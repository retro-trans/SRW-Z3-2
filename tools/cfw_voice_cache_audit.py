"""Read-only audit for the 0.5.53 hardware no-voice/all-ellipsis report.

No game, console cache, emulator registration or saved data is modified.
--apply writes only the English diagnostic JSON under work/ui/.
"""
import argparse
import hashlib
import json
from tools.common import ROOT, sha256, sha256_file, write_json
from tools import srvc as S, cfw_self as C, cfw_package as B
from tools import cfw_trophy_control as T
from tools.isoread import ISO9660

REPORT = ROOT/'work/ui/ps3_voice_audit_2026-11-22.json'


def audit():
    seal = json.loads((ROOT/'work/ui/local_release_0.5.53.json').read_text('utf8'))
    if seal['final_readback_sha256'] != sha256_file(T.PROOF):
        raise ValueError('Trophy-control proof changed')
    parent = json.loads((ROOT/'work/ui/local_release_0.5.52.json').read_text('utf8'))
    proof = json.loads(B.PROOF.read_text('utf8'))
    if parent['final_readback_sha256'] != sha256_file(B.PROOF):
        raise ValueError('Parent proof changed')
    build = json.loads((B.OUTPUT/'build.json').read_text('utf8'))
    if proof['build_sha256'] != sha256_file(B.OUTPUT/'build.json'):
        raise ValueError('Parent build changed')
    old, oldelf = S.load_prepared()
    manifest = json.loads((ROOT/'work/tengoku/source_manifest.json').read_text('utf8'))
    expected = {r['path']:r for r in manifest['files']}
    banks = []
    with ISO9660(T.IMAGE) as iso:
        files = dict(iso.walk())
        wrapped = iso.read(files['/PS3_GAME/USRDIR/EBOOT.BIN'])
        if sha256(wrapped) != build['outputs']['EBOOT.BIN']:
            raise ValueError('ISO executable differs from the sealed pair')
        elf = C.extract_debug(wrapped)
        new = iso.read(files[S.SRVC])
        if sha256(new) != build['outputs']['SRVC.BIN']:
            raise ValueError('ISO voice data differs from the sealed pair')
        for path in sorted(p for p in expected if p.startswith('/PS3_GAME/USRDIR/DATA/SOUND/')):
            digest = hashlib.sha256()
            for raw in iso.blocks(files[path]):
                digest.update(raw)
            if digest.hexdigest() != expected[path]['sha256'] or files[path]['size'] != expected[path]['size']:
                raise ValueError('Audio archive differs from original: '+path)
            banks.append(dict(path=path, bytes=files[path]['size'], sha256=digest.hexdigest(),
                              byte_identical_to_original=True))
    ot, nt = S.read_table(oldelf,len(old)), S.read_table(elf,len(new))
    ob, nb = S.parse(old,ot), S.parse(new,nt)
    if len(ob) != len(nb) or len(ob) != 368:
        raise ValueError('Voice-bank count changed')
    for before, after in zip(ob,nb):
        if old[before.base:before.offs_at] != new[after.base:after.offs_at]:
            raise ValueError('Voice selection/cue fields changed: '+str(before.i))
    invalid = [i for i in range(368) if nt[i] >= len(old) or old[nt[i]] != 3]
    text = {b.i for b in ob if b.n6}
    past_eof = [i for i in range(368) if nt[i+1] > len(old)]
    # Native install-list record: source path, installed subfolder, filename, flag.
    import struct
    at = S.va_to_offset(oldelf, 0xa1b2b4)
    pointers = struct.unpack_from('>4I',oldelf,at)
    strings = []
    for pointer in pointers[:3]:
        off = S.va_to_offset(oldelf,pointer)
        strings.append(oldelf[off:oldelf.index(b'\0',off)].decode('ascii'))
    if strings != [S.PATH_STRING.decode(), '/INSCO/', 'DATA0046.DAT'] or pointers[3] != 1:
        raise ValueError('Native voice install mapping differs')
    return dict(schema=1,date='2026-11-22',version='0.5.53',
        scope='on-disc audio and native voice-bank pairing; remote console cache not inspected',
        source_report='work/ui/ps3_voice_report_2026-11-22.json',
        image_verification_sha256=sha256_file(T.PROOF), audio_archives=banks,
        paired_voice_banks=368, voice_cue_references_preserved=sum(b.n6 for b in ob),
        selection_rules_headers_and_cues_byte_identical=True,
        native_installed_subfolder='/INSCO/',native_installed_filename='DATA0046.DAT',
        observed_rpcS3_cache_path='dev_hdd0/game/BLJS10299_DATA/USRDIR/INSCO/DATA0046.DAT',
        original_cache=dict(bytes=len(old),sha256=sha256(old)),
        required_cache=dict(bytes=len(new),sha256=sha256(new)),
        original_cache_with_new_table=dict(invalid_header_banks=len(invalid),total_banks=368,
            invalid_text_banks=len(text.intersection(invalid)),total_text_banks=len(text),
            read_windows_past_original_eof=len(past_eof)),
        suspected_cause='Old installed voice data used with the new executable table',
        remote_cache_mismatch_confirmed=False, hardware_audio_recovery_confirmed=False,
        firmware_saves_trophies_and_game_files_modified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args = parser.parse_args()
    report = audit()
    print('Original audio archives:',len(report['audio_archives']),'; cue references unchanged:',report['voice_cue_references_preserved'])
    print('Required installed DATA0046.DAT:',report['required_cache'])
    print('Old-cache/new-table simulation:',report['original_cache_with_new_table'])
    if args.apply:
        write_json(REPORT,report)
    else:
        print('DRY RUN: no files or installed data changed.')


if __name__ == '__main__':
    main()

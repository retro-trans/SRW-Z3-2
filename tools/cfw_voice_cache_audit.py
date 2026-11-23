"""Read-only audit for the 0.5.53 hardware no-voice/all-ellipsis report.

No game, console cache, emulator registration or saved data is modified.
--apply writes only the English diagnostic JSON under work/ui/.
"""
import argparse
import hashlib
import json
import struct
from tools.common import ROOT, sha256, sha256_file, write_json
from tools import srvc as S, cfw_self as C, cfw_package as B
from tools import cfw_trophy_control as T
from tools.isoread import ISO9660

REPORT = ROOT/'work/ui/ps3_voice_audit_2026-11-22.json'


def native_bank_readback(elf, data):
    """Execute packaged PPC read/parse code; streaming and audio are not emulated."""
    from tools import ppc_exec as P
    table=S.read_table(elf,len(data))
    memory=P.Memory()
    for off,va,size in S.segments(elf):
        memory.map(va,elf[off:off+size],False)
    buffer,context,stack,stop=0x10000000,0x20000000,0x30000000,0x40000000
    largest=max(b-a for a,b in zip(table,table[1:]))
    memory.map(buffer,bytes(largest))
    memory.map(context,bytes(0x100))
    memory.map(stack,bytes(0x2000))
    def machine(pc):
        m=P.Machine(memory)
        m.pc=pc
        m.r[1],m.r[2],m.r[3]=stack+0x1000,S.TOC_BASE,context
        m.lr=stop
        return m
    for bank,(base,end) in enumerate(zip(table,table[1:])):
        raw=data[base:end]
        memory.write(context,bytes(0x100))
        memory.write(context+0x28,struct.pack('>IH',S.TABLE_VA,bank))
        requests=[]
        def read(m):
            requests.append((m.r[4],m.r[5]))
            path=m.mem.read(m.r[3],len(S.PATH_STRING)+1)
            if path != S.PATH_STRING+b'\0' or m.r[6] != context:
                raise ValueError('Native voice-read path/context differs')
            m.r[3],m.pc=0,m.lr
        m=machine(S.START_READ_VA)
        m.hooks[0x22a84]=read
        m.run({stop},limit=200)
        if requests != [(base,end-base)]:
            raise ValueError('Native voice-read range differs: '+str(bank))
        memory.write(buffer,raw)
        memory.write(context,bytes(0x100))
        m=machine(S.PARSER_VA)
        m.r[4]=buffer
        m.run({stop},limit=200)
        n1,n2,n3=raw[1:4]
        n4,n6=struct.unpack_from('<HH',raw,4)
        a=buffer+8
        b=a+n1*4
        c=b+n4*8
        d=c+n2*8
        cue=d+n3*4
        offsets=cue+n6*8
        pool=offsets+n6*4
        expected=(buffer,a,b if n4 else 0,c if n2 else 0,d if n3 else 0,
                  cue if n6 else 0,offsets if n6 else 0,pool if n6 else 0)
        if struct.unpack('>8I',memory.read(context,32)) != expected:
            raise ValueError('Native parser pointers differ: '+str(bank))
        if memory.read(buffer,len(raw)) != raw:
            raise ValueError('Native parser altered a valid bank: '+str(bank))
    return dict(read_requests_verified=len(table)-1,parser_banks_verified=len(table)-1,
        largest_read_window=largest,executed_packaged_ppc_instructions=True,
        read_entry_va=hex(S.START_READ_VA),parser_entry_va=hex(S.PARSER_VA),
        mocked_streaming_boundary_va='0x22a84',
        physical_streaming_allocation_selection_and_audio_playback_verified=False)


def install_log(data, elf):
    """Bind observed 272-byte records to the native install list; no writes."""
    if len(data)<8 or (len(data)-8)%272:
        raise ValueError('Unrecognized installation-log geometry')
    records=[]
    for at in range(8,len(data),272):
        raw=data[at:at+272]
        paths=[]
        for field in (raw[:128],raw[128:256]):
            end=field.find(b'\0')
            if end<1 or any(field[end:]):
                raise ValueError('Invalid installation-log path/padding')
            paths.append(field[:end].decode('ascii'))
        records.append(dict(source=paths[0],installed_relative=paths[1],
            trailing_u64_hex=[hex(v) for v in struct.unpack_from('>QQ',raw,256)]))
    anchor=[i for i,r in enumerate(records) if r['source']==S.PATH_STRING.decode()]
    if len(anchor)!=1:
        raise ValueError('Installation log lacks a unique SRVC entry')
    base=0xa1b2b4-anchor[0]*16
    def text(va):
        at=S.va_to_offset(elf,va)
        return elf[at:elf.index(b'\0',at)].decode('ascii')
    for i,row in enumerate(records):
        source,directory,name,_=struct.unpack_from('>4I',elf,S.va_to_offset(elf,base+i*16))
        if (row['source'],row['installed_relative']) != (text(source),text(directory)+text(name)):
            raise ValueError('Log entry differs from native install mapping: '+str(i))
    return dict(bytes=len(data),sha256=sha256(data),header_hex=data[:8].hex(),
        header_semantics_unverified=True,records=len(records),native_mappings_verified=len(records),
        source_and_destination_records=records,active_executable_identity_proven=False,
        installed_audio_payload_integrity_proven=False)


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
    reverse_invalid = [i for i in range(368) if new[ot[i]] != 3]
    text = {b.i for b in ob if b.n6}
    past_eof = [i for i in range(368) if nt[i+1] > len(old)]
    # Native install-list record: source path, installed subfolder, filename, flag.
    at = S.va_to_offset(oldelf, 0xa1b2b4)
    pointers = struct.unpack_from('>4I',oldelf,at)
    strings = []
    for pointer in pointers[:3]:
        off = S.va_to_offset(oldelf,pointer)
        strings.append(oldelf[off:oldelf.index(b'\0',off)].decode('ascii'))
    if strings != [S.PATH_STRING.decode(), '/INSCO/', 'DATA0046.DAT'] or pointers[3] != 1:
        raise ValueError('Native voice install mapping differs')
    report = dict(schema=1,date='2026-11-22',version='0.5.53',
        scope='on-disc audio and native voice-bank pairing; supplied console files inspected when present',
        source_report='work/ui/ps3_voice_report_2026-11-22.json',
        image_verification_sha256=sha256_file(T.PROOF), audio_archives=banks,
        native_bank_readback=native_bank_readback(elf,new),
        paired_voice_banks=368, voice_cue_references_preserved=sum(b.n6 for b in ob),
        selection_rules_headers_and_cues_byte_identical=True,
        native_installed_subfolder='/INSCO/',native_installed_filename='DATA0046.DAT',
        observed_rpcS3_cache_path='dev_hdd0/game/BLJS10299_DATA/USRDIR/INSCO/DATA0046.DAT',
        original_cache=dict(bytes=len(old),sha256=sha256(old)),
        required_cache=dict(bytes=len(new),sha256=sha256(new)),
        required_disc_executable=dict(bytes=len(wrapped),sha256=sha256(wrapped),
            payload_sha256=sha256(elf),mounted_disc_path='/dev_bdvd/PS3_GAME/USRDIR/EBOOT.BIN'),
        original_cache_with_new_table=dict(invalid_header_banks=len(invalid),total_banks=368,
            invalid_text_banks=len(text.intersection(invalid)),total_text_banks=len(text),
            read_windows_past_original_eof=len(past_eof)),
        original_executable_with_translated_cache=dict(invalid_header_banks=len(reverse_invalid),
            total_banks=368,invalid_text_banks=len(text.intersection(reverse_invalid)),total_text_banks=len(text)),
        failure_modes_under_investigation=['Old installed data with translated executable',
            'Original executable table with translated installed data'],
        remote_cache_mismatch_confirmed=False, hardware_audio_recovery_confirmed=False,
        firmware_saves_trophies_and_game_files_modified=False)
    cache=ROOT/'incoming/DATA0046.DAT'
    log=ROOT/'incoming/UPDATE.LOG'
    if cache.is_file():
        supplied=cache.read_bytes()
        report['supplied_installed_voice_data']=dict(path=cache.relative_to(ROOT).as_posix(),
            bytes=len(supplied),sha256=sha256(supplied),byte_identical_to_verified_build=supplied==new)
        if supplied==new:
            report['supplied_cache_stale_or_corrupt']=False
    if log.is_file():
        report['supplied_installation_log']=install_log(log.read_bytes(),elf)
        report['supplied_installation_log']['path']=log.relative_to(ROOT).as_posix()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args = parser.parse_args()
    report = audit()
    print('Original audio archives:',len(report['audio_archives']),'; cue references unchanged:',report['voice_cue_references_preserved'])
    print('Required installed DATA0046.DAT:',report['required_cache'])
    print('Old-cache/new-table simulation:',report['original_cache_with_new_table'])
    if 'supplied_installed_voice_data' in report:
        print('Supplied cache:',report['supplied_installed_voice_data'])
    if 'supplied_installation_log' in report:
        print('Installation-log mappings verified:',report['supplied_installation_log']['native_mappings_verified'])
    print('Native PPC voice read/parser check:',report['native_bank_readback'])
    if args.apply:
        write_json(REPORT,report)
    else:
        print('DRY RUN: no files or installed data changed.')


if __name__ == '__main__':
    main()

"""Read back 0.5.4 startup fixes and execute their final shipped instructions."""
import argparse
import json
import re
import struct

from tools.common import ROOT, sha256, sha256_file, write_json
from tools import ui_hook, ui_catalog, eboot_text, opening_narration, ppc_exec, runtime_names
from tools.cpk import CPK


def verify(version='0.5.4'):
    folder = ROOT/'work/output/builds'/version
    build = json.loads((folder/'build.json').read_text(encoding='utf-8'))
    for name,expected in build['outputs'].items():
        if sha256_file(folder/name)!=expected:
            raise ValueError('Matched build output drift: '+name)
    elf = (folder/'EBOOT.BIN').read_bytes()
    _,_,phs,_ = ui_hook._headers(elf)
    read = ui_hook._reader(elf,phs)
    hook = build['executable']['ui_hook']
    runner = ui_hook._Runner(elf,int(hook['stub_va'],16),hook['stub_bytes'])
    translated = ui_catalog.translations()
    with CPK(folder/'AIDDATAPACK.CPK') as archive:
        entry, = [e for e in archive.files if e['id']==19]
        original = archive.read(entry)
    opening = opening_narration.sources(original)
    for row in opening:
        rid = sha256(row['text'].encode('utf-8'))[:20]
        mapping = build['mapping']
        if build.get('latin_font') and opening_narration.profile(translated[rid]['en'])[1]:
            from tools.dialogue_layout import PREFIX
            mapping = dict(mapping)
            mapping.update({token[len(PREFIX):]:code for token,code in build['mapping'].items() if token.startswith(PREFIX)})
        expected = eboot_text.encode(translated[rid]['en'],mapping)+b'\0'
        pointer,_ = runner.run(row['raw']+b'\0')
        if read(pointer,len(expected))!=expected:
            raise ValueError('Final opening dictionary execution failed')
    addresses = hook['table']['payload_vas']
    name_cases = 0
    for reader in runtime_names.READERS:
        site,_,toc,jp,en = reader
        pointer = struct.unpack('>I',read(ui_hook.TOC+toc,4))[0]
        nickname_pointer = struct.unpack('>I',read(ui_hook.TOC-0x3c68,4))[0]
        default = jp.encode('cp932')
        cases = [(value,0x400000,b'Custom') for value in (default,b'Custom',b'',b'A',default+b'X',default[:-2],None)]
        if en=='Kamishiro':
            cases += [(default,ret,b'A'*n) for ret in runtime_names.FULL_SURNAME_RETURNS for n in (20,21,24,27)]
        for value,lr,nickname in cases:
            mem = ppc_exec.Memory()
            mem.map(ui_hook.TOC+toc,struct.pack('>I',pointer if value is not None else 0),writable=False)
            if value is not None:
                mem.map(pointer,value+b'\0',writable=False)
            if pointer!=nickname_pointer:
                mem.map(nickname_pointer,nickname+b'\0',writable=False)
            for segment in phs[:2]:
                mem.map(segment[3],elf[segment[2]:segment[2]+segment[5]],writable=False)
            m = ppc_exec.Machine(mem)
            m.r = [0x100000+i for i in range(32)]
            m.r[2] = ui_hook.TOC
            before = m.r[:]
            m.cr = 0xb3c7a965
            m.lr = lr
            m.pc = site
            m.run({lr},limit=400)
            wanted = pointer if value is not None else 0
            if value==default:
                short = en=='Kamishiro' and lr in runtime_names.FULL_SURNAME_RETURNS and len(nickname)>20
                wanted = addresses['name:K.' if short else 'name:'+en]
            if m.r[3]!=wanted or m.lr!=lr or m.cr!=0xb3c7a965:
                raise ValueError('Final name getter result/register state differs')
            if any(m.r[r]!=before[r] for r in set(range(32))-{0,3,9,10,11,12}):
                raise ValueError('Final name getter changed a preserved register')
            name_cases += 1
    files = ['tools/game_build.py','tools/ui_catalog.py','tools/ui_layout_text.py',
        'tools/opening_narration.py','tools/runtime_names.py','tools/startup_layout.py',
        'tools/verify_startup_ui.py','tests/test_startup_ui.py',
        'work/translation/en/ui/expanded/opening.json','work/ui/startup_layout.json']
    font_report = None
    if build.get('latin_font'):
        import numpy as np
        from tools.ui_build import atlas,cell_xy
        from tools.ui_vwf_build import raster
        from tools.latin_font import profile
        if profile()!=build['latin_font']:
            raise ValueError('Built font profile differs from current source')
        with CPK(folder/'TPACKPS3.CPK') as archive:
            pages = {e['id']:atlas(archive.read(e)) for e in archive.files if e['id'] in (1,3)}
        if set(pages)!={1,3}:
            raise ValueError('Missing matched font page')
        for token,code in build['mapping'].items():
            glyph,width = raster(token)
            from tools.ui_build import glyph_pixels
            expected = glyph_pixels(glyph)
            x,y = cell_xy(code)
            for page in pages.values():
                if not np.array_equal(page[y:y+32,x:x+32],expected):
                    raise ValueError('Built atlas glyph differs: '+token)
            cell = y//32*128+x//32
            if read(build['executable']['table_va']+cell,1)!=bytes([width]):
                raise ValueError('Built advance table differs: '+token)
        files += ['tools/latin_font.py','tools/ui_vwf_build.py','tools/ui_build.py',
                  'tools/ui_description_layout.py','tools/dialogue_layout.py','tests/test_latin_font.py']
        font_report = dict(build['latin_font'],glyphs_verified_each_page=len(build['mapping']),
            pages_verified=sorted(pages),advance_cells_verified=len(build['mapping']),
            reference_source_sha256={name:sha256_file(ROOT.parent/'SRW Z3/tools'/name)
                for name in ('digraph.py','ttfglyph.py')})
        from tools.ui_build import FACE
        cache = FACE.parents[3]/'dev_hdd0/game/BLJS10299_DATA/USRDIR/INSCO/DATA0141.DAT'
        if cache.exists():
            cached_hash = sha256_file(cache)
            font_report['installed_font_cache'] = dict(path=str(cache),sha256=cached_hash,
                matches_build=cached_hash==build['outputs']['TPACKPS3.CPK'],modified=False)
    screenshots = {p.name:dict(sha256=sha256_file(p),bytes=p.stat().st_size)
        for p in sorted((ROOT/'work/ui/screenshots').glob('0.5.3-*.png'))}
    test_log = ROOT/('work/output/scratch/startup-%s-tests.log'%version)
    raw_log = test_log.read_bytes()
    log = raw_log.decode('utf-16' if raw_log[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
    # unittest writes status to stderr; buffered test diagnostics on stdout
    # can follow OK in a merged log. Require its complete success line.
    match = re.search(r'Ran (\d+) tests[^\r\n]*\r?\n\s*OK(?: \(skipped=(\d+)\))?[ \t]*\r?(?:\n|$)',log)
    if not match:
        raise ValueError('Regression log does not confirm success')
    run,skip = int(match[1]),int(match[2] or 0)
    image_report = ROOT/('work/output/iso/%s/Tengoku-hen-English-%s.json'%(version,version))
    iso = json.loads(image_report.read_text(encoding='utf-8')) if image_report.exists() else None
    if iso and (iso['version']!=version or iso['files_verified_each_tree']!=82):
        raise ValueError('Unexpected testing ISO verification report')
    return dict(schema=1,version=version,build_sha256=sha256_file(folder/'build.json'),
        outputs=build['outputs'],input_sha256={p:sha256_file(ROOT/p) for p in files},
        screenshots=screenshots,opening_lines_executed=len(opening),opening_member_unchanged=True,
        name_getter_cases_executed=name_cases,name_buffers_read_only=True,
        stage_cpk_sha256=sha256_file(folder/'STGZ3OF2.cpk'),iso=iso,
        latin_font=font_report,
        regression_tests=dict(run=run,passed=run-skip,skipped=skip,log_sha256=sha256_file(test_log)),
        runtime_verified=False,layout_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--version',default='0.5.4')
    args = parser.parse_args()
    result = verify(args.version)
    print('Final opening lines:',result['opening_lines_executed'])
    print('Final name-reader cases:',result['name_getter_cases_executed'])
    print('Matched files:',len(result['outputs']))
    print('Original opening member preserved; name buffers read-only; live QA pending.')
    if args.apply:
        write_json(ROOT/('work/ui/startup_%s.json'%args.version),result)
    else:
        print('DRY RUN: no report written.')


if __name__=='__main__':
    main()

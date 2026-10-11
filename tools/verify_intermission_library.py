"""Read back intermission, complete Library prose and native chart artwork."""
import argparse
import json
import re
import shutil
import struct
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import intermission_layout as I,library_runtime as L,ui_hook as H
from tools import library_text,library_build,eboot_text,ui_catalog,eff_art,chart_art
from tools.cpk import CPK
from tools.ui_description_layout import advance

SHOTS=(('intermission','04b50243-abee-4110-94c7-59e6c345773f'),
       ('options','6bed6447-142d-4cb6-807b-7525a872cfc4'),
       ('library-menu','0bc1848e-6b76-4e24-82f8-4517bc989c9e'),
       ('keyword-popup','caf613a9-eb39-4936-9b33-cfe7b7dc48cd'),
       ('scenario-chart','efcb15c6-47ee-49fb-9060-c4292453bb29'))


def verify(version):
    from tools.verify_title_screen import verify as title
    folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf8'))
    previous=title(version)
    elf=(folder/'EBOOT.BIN').read_bytes();source=H.PREPARED.read_bytes()
    read=H._reader(elf,H._headers(elf)[2]);mapping=build['mapping']
    planned=L.plan(source,mapping,advance);addresses=build['executable']['ui_hook']['table']['payload_vas']
    for key,raw in planned['payloads']:
        if key not in (L.FAST_STATE,L.FAST_TABLE) and read(addresses[key],len(raw))!=raw:
            raise ValueError('Final Library prose differs: '+key)
    for row in planned['pointers']:
        if struct.unpack_from('>I',elf,row['offset'])[0]!=addresses[row['id']]:
            raise ValueError('Native Library descriptor still points to the original prose')
    for row in planned['report']['entries']:
        at=row['record_offset'];restored=bytearray(elf[at:at+24]);restored[8:16]=source[at+8:at+16]
        if restored!=source[at:at+24]:raise ValueError('Native Library names, series, flags or IDs changed')
    conversion=L.verify_fastpath(elf,planned,addresses,build['executable']['library_runtime']['conversion'])
    table=H.unicode_table(elf);oracle=H.ConverterOracle(elf);converter_cases=0
    owned=[raw for key,raw in planned['payloads'] if key.startswith('library:keyword:') and not key.endswith(':encoded')]
    # Native conversion remains useful for copies of individual wrapped lines.
    for raw in (dict(planned['payloads'])['library:keyword:0:DSCR'],
                max(max(owned,key=len)[:-1].split(b'\n'),key=len)+b'\0'):
        expected=H.convert(raw[:-1],table)
        for model in ('A','B'):
            out,_,_=oracle.run(raw,model)
            if out[:len(expected)+1]!=expected+b'\0':raise ValueError('Final native UTF-8 carrier conversion differs')
            converter_cases+=1
    library=library_text.load_library();entries,_=library_text.load_translations()
    terms=json.loads(library_text.GLOSSARY.read_text(encoding='utf8'))['terms']
    rendered=library_build.plan(library,entries,terms)
    japanese=re.compile(r'[\u3040-\u30ff\u4e00-\u9fff]')
    fields=0;prose=0
    for kind,records in rendered.items():
        for tid,values in records.items():
            for tag,text in values.items():
                if japanese.search(text):raise ValueError('Untranslated Library display field: %s %d %s'%(kind,tid,tag))
                fields+=1;prose+=tag in ('DSCR','DSC2')
    base,_=eboot_text.hook_entries(source,mapping,lambda raw:H.utf8_key(raw,source))
    hooked,_=ui_catalog.hook_entries(source,mapping,base);by_key={e['key']:e for e in hooked}
    h=build['executable']['ui_hook'];runner=H._Runner(elf,int(h['stub_va'],16),h['stub_bytes'])
    native_rows=[r for r in eboot_text.records() if r['family']=='library' and r.get('display') and r.get('usage')in eboot_text.IN_SCOPE]
    executed=0;formats=[]
    for row in native_rows:
        raw=row['jp'].encode(row['encoding']);key=raw if row['encoding']=='cp932' else H.utf8_key(raw,source)
        if key not in by_key:
            formats.append(dict(va=row['va'],format=bool(row.get('format')),fragment=bool(row.get('fragment'))));continue
        pointer,_=runner.run(key+b'\0');english=by_key[key]['english']
        if read(pointer,len(english)+1)!=english+b'\0':raise ValueError('Library display hook differs: '+row['va'])
        if japanese.search(library_build.decode(english,mapping)):raise ValueError('Native Library display still contains Japanese')
        executed+=1
    if formats:raise ValueError('Uncovered native Library display occurrences: '+repr(formats))
    charts=[];originals=eff_art.source_members(eff_art._settings(),list(chart_art.SOURCES),chart_art.SOURCES)
    with CPK(folder/'EFFPS3.CPK')as archive:
        by_id={e['id']:e for e in archive.files}
        for mid,raw in originals.items():
            want,pixels,edits,info=chart_art.render(raw,mid);built=archive.read(by_id[mid])
            if built!=want:raise ValueError('Chart archive member differs')
            eff_art.verify_member(raw,built,pixels,edits);charts.append(info)
    shots=[]
    from PIL import Image
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dest=ROOT/'work/ui/screenshots'/('reported-'+version+'-'+label+'.png')
        if not src.exists():src=dest
        with Image.open(src)as img:size=list(img.size)
        shots.append(dict(issue=label,source=str(src),saved_path=str(dest),sha256=sha256_file(src),pixel_size=size,runtime_confirmation=False))
    layout=I.plan()
    if layout!=json.loads(I.DEST.read_text(encoding='utf8')):raise ValueError('Intermission layout plan is stale')
    return dict(schema=1,version=version,widgets=layout['edits'],native_keywords=planned['report'],
        native_conversion=dict(conversion,wrapped_converter_cases=converter_cases),
        library_audit=dict(entries={k:len(v)for k,v in rendered.items()},english_display_fields=fields,
            description_fields=prose,native_display_occurrences=len(native_rows),native_hook_cases=executed,
            untranslated_display_fields=0),charts=charts,screenshots=shots,
        source_sha256={f:sha256_file(ROOT/f)for f in ('tools/intermission_layout.py','tools/library_runtime.py',
            'tools/chart_art.py','tools/operation_layout.py','tools/game_build.py','tools/ui_layout_text.py',
            'tools/verify_intermission_library.py','tests/test_intermission_library.py')},
        prior_title_verification=previous,iso_verification=previous['iso_verification'],runtime_verified=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--version',default='0.5.11');ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    data=verify(args.version)
    print('Intermission widgets:',len(data['widgets']));print('Library audit:',data['library_audit'])
    print('Native conversion:',data['native_conversion']);print('Chart members:',len(data['charts']))
    if args.apply:
        for shot in data['screenshots']:
            dest=Path(shot['saved_path']);dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists()and sha256_file(dest)!=shot['sha256']:raise ValueError('Screenshot collision')
            if Path(shot['source'])!=dest:shutil.copyfile(shot['source'],dest)
        write_json(ROOT/'work/ui'/('intermission_library_'+args.version+'.json'),data)
    else:print('DRY RUN: no evidence or screenshots written.')


if __name__=='__main__':main()

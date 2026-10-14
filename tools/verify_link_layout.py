"""Read and execute final layout helpers; preview evidence before --apply."""
import argparse
import json
import struct
import shutil
from pathlib import Path
from PIL import Image
from tools import ui_hook, link_layout as ll, operation_layout, eboot_text, ppc_exec as p, library_build
from tools.common import ROOT, sha256_file, sha256, write_json

SCREENSHOTS = (
    ('map-menu','d94c2cb9-596c-46e8-84ac-8fe8aa098bb5'),
    ('spirit-list','c88fd4e7-394b-4458-a1c9-6fa02b9be6c8'),
    ('tactical-report','47f6593c-b0fa-4164-b339-7f1db8195cc4'),
    ('settings-tabs','0934c5a1-1094-4103-9cf7-e09773896827'),
    ('save-choices','422dc0a4-2173-4204-8fc4-c68c02509ca7'),
)
REGIONS = {
    'map-menu': [('command buttons', (2019,113,424,627))],
    'spirit-list': [('tabs', (516,44,1522,75)),('Spirit columns', (138,199,2282,810))],
    'tactical-report': [('stage heading', (338,180,828,53)),('team count', (766,949,435,71))],
    'settings-tabs': [('settings tabs', (263,124,1070,89))],
    'save-choices': [('save choices', (260,686,2049,292))],
}


def verify(version):
    folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf8'))
    for name,expected in build['outputs'].items():
        if sha256_file(folder/name)!=expected: raise ValueError('Matched output drift: '+name)
    elf=(folder/'EBOOT.BIN').read_bytes(); phs=ui_hook._headers(elf)[2]; read=ui_hook._reader(elf,phs)
    layout=build['executable']['link_layout']; rows={r['id']:r for r in layout['code']}
    state,table=layout['state_va'],layout['width_table_va']
    look,wrapper,measure=[rows[key]['va'] for key in ('exact lookup','display lookup','VWF units')]
    expected={
        'exact lookup':lambda va:ui_hook.stub(va,back=va,replay=ll.NOP)[:-4]+struct.pack('>I',ll.BLR),
        'display lookup':lambda va:ll.lookup_wrapper(va,look),
        'VWF units':lambda va:ll.units(va,table),
        'drawer origin':lambda va:ll.drawer_pen(va,state),
        'drawer advance':lambda va:ll.drawer_pen(va,state,True),
        'segment column':lambda va:ll.column(va,state),
        'segment x/y':ll.position,
        'registered width':lambda va:ll.capture(va,state),
        'selected width':lambda va:ll.secondary(va,state),
        'secondary rectangle':lambda va:ll.secondary(va,state,True),
        'primary rectangle':lambda va:ll.primary(va,state),
        'dialogue scene':ll.scene,
        'translated registration':lambda va:ll.compare(va,wrapper),
        'name width':lambda va:ll.name_width(va,wrapper,measure),
        'caption centering':lambda va:ll.center(va,wrapper,measure,layout['centering_selection_codes']),
        'formatted heading':lambda va:ll.heading(va,wrapper),
    }
    if layout.get('save_center'):
        from tools.status_layout import save_origin
        expected['drawer origin']=lambda va:save_origin(va,state,layout['save_center'])
    for key,row in rows.items():
        if read(row['va'],row['bytes'])!=expected[key](row['va']): raise ValueError('Final helper mismatch: '+key)
    for site in ll.GUARDS:
        word=struct.unpack('>I',read(site,4))[0]
        linked=site==0x21ce74
        destinations={0x141a8:'drawer origin',0x1488c:'drawer advance',0x2209e4:'segment column',
            0x21f700:'segment x/y',0x21cddc:'registered width',0x216a3c:'selected width',
            0x216ad0:'secondary rectangle',0x214b54:'primary rectangle',0x21ce04:'dialogue scene',
            0x21ce74:'translated registration',0x2aae04:'name width',0x14a24:'caption centering',
            0x1dd178:'formatted heading'}
        want=ll.NOP if site==0x2209e8 else ui_hook.branch(site,rows[destinations[site]]['va'])|int(linked)
        if word!=want: raise ValueError('Final interception differs: %#x'%site)
    widths=read(table,4480); mapping=build['mapping']
    def machine(quad=None):
        mem=p.Memory(); mem.map(0x40000000,bytes(0x3000))
        if quad is not None:
            mem.map(ui_hook.TOC-0x7f3c,struct.pack('>I',0x41001000),writable=False)
            font=bytearray(0x1200); struct.pack_into('>f',font,0x54,quad)
            mem.map(0x41001000,font)
        for seg in phs[:2]: mem.map(seg[3],elf[seg[2]:seg[2]+seg[5]],writable=False)
        m=p.Machine(mem); m.r=[0x990000+i for i in range(32)]
        m.r[1]=0x40001800; m.r[2]=ui_hook.TOC; m.lr=0xdead00; m.cr=0xb3c7a965
        return m,mem
    executions=[]
    for english,japanese in [('Sumeragi','スメラギ'),('Shikuu','尸空'),('Hibiki','ヒビキ'),
                              ('Move','移動'),('Transform','変形'),('Spirit','精神'),('Status','能力')]:
        encoded=eboot_text.encode(english,mapping)
        want=sum(widths[(a-0x81)*192+b-0x40] for a,b in zip(encoded[::2],encoded[1::2]))
        # Exact source names and pre-encoded dialogue names share the same geometry.
        for raw in (encoded,japanese.encode('cp932')):
            m,mem=machine(); mem.map(0x41000000,raw+b'\0',writable=False); m.r[3]=0x41000000
            before=m.r[:]; cr=m.cr; m.pc=wrapper; m.run({0xdead00},limit=100000)
            pointer=m.r[3]
            for reg in set(range(32))-{0,3}:
                if m.r[reg]!=before[reg]: raise ValueError('Final lookup changed r%d'%reg)
            if m.cr!=cr: raise ValueError('Final lookup changed CR')
            m.pc=measure; m.run({0xdead00},limit=100000)
            # A name also has other contextual translations; only assert the
            # expected word when the final dictionary really supplies that word.
            hit=mem.read(pointer,len(encoded))==encoded if pointer!=0x41000000 else raw==encoded
            if hit and m.r[3]!=want: raise ValueError('Final width differs: '+english)
            executions.append(dict(text=english,source='encoded' if raw==encoded else 'native key',
                                   expected_key_match=hit,units=m.r[3],steps=m.steps))
    hook=build['executable']['ui_hook']
    runner=ui_hook._Runner(elf,int(hook['stub_va'],16),hook['stub_bytes'])
    headings=[]
    for row in operation_layout.hook_entries(ui_hook.PREPARED.read_bytes(),mapping):
        pointer,steps=runner.run(row['key']+b'\0')
        if read(pointer,len(row['english'])+1)!=row['english']+b'\0': raise ValueError('Final heading mismatch')
        headings.append(dict(id=row['id'],source_sha256=sha256(row['key']),steps=steps,
                             english=eboot_text.unshow(library_build.decode(row['english'],mapping))))
        m,mem=machine(); mem.map(0x41000000,row['key']+b'\0',writable=False)
        m.r[31]=0x41000000; mem.write(m.r[1]+0xc0,struct.pack('>Q',0xdead00))
        m.pc=rows['formatted heading']['va']; m.run({0x1dd17c},limit=100000)
        if mem.read(m.r[31],len(row['english'])+1)!=row['english']+b'\0' or m.r[0]!=0xdead00:
            raise ValueError('Final formatted heading return differs')
    centers=[]
    for text in ('Attune','Strike','End Phase','Settings 1','Settings 2','Abilities',
                 'Save to Hard Disk','Upload to Network','Do Not Save'):
        raw=eboot_text.encode(text,mapping)
        units=sum(widths[(a-0x81)*192+b-0x40]for a,b in zip(raw[::2],raw[1::2]))
        for quad in (28,31):
            for alternate in (False,True):
                m,mem=machine(quad); mem.map(0x41000000,raw+b'\0',writable=False)
                m.r[31]=0x41000000; m.r[30]=1; m.f[29]=639.5
                m.cr=(m.cr&~2) if alternate else (m.cr|2)
                before=m.r[:]; lr=m.lr; m.pc=rows['caption centering']['va']
                m.run({0x14a68,0x14a2c,0x14ac4},limit=100000)
                if m.pc!=0x14a68 or abs(m.f[1]+units*quad/64-639.5)>0.0001:
                    raise ValueError('Final CP932 caption center differs: '+text)
                if m.lr!=lr or any(m.r[r]!=before[r]for r in (1,2,27,28,29,30,31)):
                    raise ValueError('Final caption preserved registers differ')
                centers.append(dict(text=text,quad=quad,alternate=alternate,left=m.f[1],center=639.5))
    from tools import menu_layout,ui_layout_text
    from tools.cpk import CPK
    from tools.ui_coverage import member
    from tools.pipeline import config,verified_source
    from tools.aid_art import ARCHIVE
    source=member(verified_source(config(ROOT/'config/tengoku.json'),ARCHIVE))
    menus=json.loads(menu_layout.DEST.read_text(encoding='utf8'))
    if menus!=menu_layout.plan(): raise ValueError('Menu plan differs from current source')
    catalog=json.loads(ui_layout_text.CATALOG.read_text(encoding='utf8'))
    startup=json.loads((ROOT/'work/ui/startup_layout.json').read_text(encoding='utf8'))
    with CPK(folder/'AIDDATAPACK.CPK') as archive:
        entry,=[e for e in archive.files if e['id']==0]; built=archive.read(entry)
    edits=catalog['edits']+startup['edits']+menus['edits']
    if build['executable'].get('status_layout'):
        from tools import status_layout
        status=json.loads(status_layout.DEST.read_text(encoding='utf8'))
        edits=status_layout.merge(edits,status['edits'])
    if build['executable'].get('battle_layout'):
        from tools import battle_layout
        battle=json.loads(battle_layout.DEST.read_text(encoding='utf8'))
        if battle!=battle_layout.plan():raise ValueError('Battle plan differs from current source')
        edits=status_layout.merge(edits,battle['edits'])
    if build['executable'].get('library_runtime'):
        from tools import intermission_layout
        intermission=json.loads(intermission_layout.DEST.read_text(encoding='utf8'))
        if intermission!=intermission_layout.plan():raise ValueError('Intermission plan differs from current source')
        edits=status_layout.merge(edits,intermission['edits'])
    if tuple(map(int,build['version'].split('.'))) >= (0,5,15):
        from tools import settings_layout
        settings_data=json.loads(settings_layout.DEST.read_text(encoding='utf8'))
        if settings_data!=settings_layout.plan():raise ValueError('Settings plan differs from current source')
        edits=status_layout.merge(edits,settings_data['edits'])
    if tuple(map(int,build['version'].split('.'))) >= (0,5,17):
        from tools import category_ui
        category=json.loads(category_ui.DEST.read_text(encoding='utf8'))
        if category!=category_ui.plan():raise ValueError('Category plan differs from current source')
        edits=status_layout.merge(edits,category['edits'])
    if tuple(map(int,build['version'].split('.'))) >= (0,5,19):
        from tools import review19_layout
        review=json.loads(review19_layout.DEST.read_text(encoding='utf8'))
        if review!=review19_layout.plan():raise ValueError('Review19 plan differs from current source')
        edits=status_layout.merge(edits,review['edits'])
    if tuple(map(int,build['version'].split('.'))) >= (0,5,20):
        from tools import upgrade_layout
        upgrade=json.loads(upgrade_layout.DEST.read_text(encoding='utf8'))
        if upgrade!=upgrade_layout.plan():raise ValueError('Upgrade layout plan differs from current source')
        edits=status_layout.merge(edits,upgrade['edits'])
    if tuple(map(int,build['version'].split('.'))) >= (0,5,21):
        from tools import review21_layout
        review21=json.loads(review21_layout.DEST.read_text(encoding='utf8'))
        if review21!=review21_layout.plan():raise ValueError('Review21 layout plan differs from current source')
        edits=status_layout.merge(edits,review21['edits'])
    if tuple(map(int,version.split('.')))>=(0,5,22):
        from tools import review22_layout
        review22=json.loads(review22_layout.DEST.read_text(encoding='utf8'))
        if review22!=review22_layout.plan():raise ValueError('Review22 layout plan differs from current source')
        edits=status_layout.merge(edits,review22['edits'])
    if tuple(map(int,version.split('.')))>=(0,5,23):
        from tools import review23_layout
        review23=json.loads(review23_layout.DEST.read_text(encoding='utf8'))
        if review23!=review23_layout.plan():raise ValueError('Review23 layout plan differs from current source')
        edits=status_layout.merge(edits,review23['edits'])
    if tuple(map(int,version.split('.')))>=(0,5,24):
        from tools import review24_layout
        review24=json.loads(review24_layout.DEST.read_text(encoding='utf8'))
        if review24!=review24_layout.plan():raise ValueError('Review24 layout plan differs from current source')
        edits=status_layout.merge(edits,review24['edits'])
    if tuple(map(int,version.split('.')))>=(0,5,25):
        from tools import review25_layout
        review25=json.loads(review25_layout.DEST.read_text(encoding='utf8'))
        if review25!=review25_layout.plan():raise ValueError('Review25 layout plan differs from current source')
        edits=status_layout.merge(edits,review25['edits'])
    if tuple(map(int,version.split('.')))>=(0,5,30):
        from tools import review30_layout
        review30=json.loads(review30_layout.DEST.read_text(encoding='utf8'))
        if review30!=review30_layout.plan():raise ValueError('Review30 layout plan differs from current source')
        edits=status_layout.merge(edits,review30['edits'])
    ui_layout_text.verify_fssa(source,built,edits,mapping,menus['element_edits'])
    command_lines=[]
    for edit in menus['edits']:
        if 'line_center' not in edit: continue
        raw=menu_layout.encode(edit,mapping).split(b'\n')
        for text,data in zip(edit['en'].split('\n'),raw):
            if not text: continue
            en=eboot_text.encode(text,mapping); pad=data[:-len(en)]
            units=lambda value:sum(widths[(a-0x81)*192+b-0x40]for a,b in zip(value[::2],value[1::2]))
            left=1030+units(pad)*31/32; width=units(en)*31/32
            if abs(left+width/2-1140)>31/64 or not (1030<left<left+width<1250):
                raise ValueError('Final command line center differs: '+text)
            command_lines.append(dict(text=text,left=left,width=width,center=left+width/2))
    shots=[]
    for label,ident in SCREENSHOTS:
        source=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        target=ROOT/'work/ui/screenshots'/('reported-'+version+'-'+label+'.png')
        if not source.exists(): source=target
        with Image.open(source) as image: size=list(image.size)
        shots.append(dict(issue=label,source=str(source),saved_path=str(target),sha256=sha256_file(source),
                          pixel_size=size,
                          observed_regions=[dict(label=name,x=box[0],y=box[1],width=box[2],height=box[3],
                              approximate=True) for name,box in REGIONS[label]],
                          fix_binding=layout['code'],runtime_confirmation=False))
    return dict(schema=1,version=version,matched_files=len(build['outputs']),
        final_elf_sha256=sha256(elf),helpers_verified=len(rows),instruction_cases=executions,
        caption_centers=centers,command_lines=command_lines,menu_widgets=menus,
        input_sha256={name:sha256_file(ROOT/name) for name in (
            'tools/link_layout.py','tools/operation_layout.py','tools/ui_hook.py',
            'tools/verify_link_layout.py','tests/test_link_layout.py',
            'tools/menu_layout.py','tools/ui_layout_text.py','tests/test_menu_layout.py',
            'work/translation/en/ui/menu_layout.json',
            'work/translation/en/ui/mission.json')},
        assembled_headings=headings,screenshots=shots,layout=layout,runtime_verified=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--version',default='0.5.7')
    ap.add_argument('--apply',action='store_true'); args=ap.parse_args()
    data=verify(args.version)
    print('Verified %d matched files, %d helpers, %d width cases and %d assembled headings.'%
          (data['matched_files'],data['helpers_verified'],len(data['instruction_cases']),len(data['assembled_headings'])))
    for row in data['instruction_cases']: print(row['text'],row['source'],row['units'],row['expected_key_match'])
    print('Caption cases:',len(data['caption_centers']),'command lines:',len(data['command_lines']))
    for row in data['command_lines']: print(row)
    for shot in data['screenshots']: print(shot['issue'],shot['pixel_size'],shot['saved_path'])
    if args.apply:
        for shot in data['screenshots']:
            dest=Path(shot['saved_path']); dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists() and sha256_file(dest)!=shot['sha256']: raise ValueError('Screenshot target collision')
            if Path(shot['source'])!=dest: shutil.copyfile(shot['source'],dest)
        write_json(ROOT/'work/ui'/('link_layout_'+args.version+'.json'),data)
    else: print('DRY RUN: no evidence or screenshots written.')


if __name__=='__main__': main()

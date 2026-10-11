"""Read back final native labels, fixed tutorial rows, and parts movement cells."""
import argparse,json,shutil,struct
from pathlib import Path
from tools.common import ROOT,sha256_file,write_json
from tools import review22_layout as L,native_labels as N,battle_layout as B,ui_catalog as U
from tools import ui_hook as H,eboot_text as E,menu_layout as M,tutorial_layout as T,parts_movement as P,library_build as R
from tools.cpk import CPK

SHOTS=(('crystal-question','be8a91b2-9c66-4150-88d7-4219b93f1991'),
       ('topic-selector','d403fdb9-a68b-449a-b4f3-49a3262ca2e8'),
       ('song-tutorial','a729329e-8d81-47e6-85f7-776a4705a459'),
       ('combat-record','b7c2620b-af10-4449-b94e-e165122d8a1c'),
       ('parts','37922106-3d55-4d19-a92f-5ffce866a5b6'))

def verify(version):
    from tools.verify_review21 import verify as previous
    prior=previous(version);folder=ROOT/'work/output/builds'/version
    build=json.loads((folder/'build.json').read_text(encoding='utf8'));mapping=build['mapping']
    source=B.source();plan=L.plan()
    if json.loads(L.DEST.read_text(encoding='utf8'))!=plan:raise ValueError('Review22 source bindings stale')
    with CPK(folder/'AIDDATAPACK.CPK')as archive:final=archive.read(next(e for e in archive.files if e['id']==0))
    grow=len(final)-len(source);widgets={a:r for r in U.fssa_strings(final,decode=lambda raw:R.decode(raw,mapping))for a in r['widget_offsets']}
    for row in plan['edits']:
        at=row['widget_offset'];target=at+grow
        if widgets[target]['raw']!=M.encode(row,mapping):raise ValueError('Final Review22 text differs')
        if (final[target+8:target+16]!=source[at+8:at+16]or final[target+21:target+23]!=source[at+21:at+23]
            or final[target+24:target+32]!=source[at+24:at+32]or final[target+23]!=row.get('mode',source[at+23])):
            raise ValueError('Native value/state/pitch changed')
        expected=struct.pack('>f',row['x'])if 'x'in row else source[at+4:at+8]
        if final[target+4:target+8]!=expected:raise ValueError('Final label origin differs')
        if final[target+16:target+21]!=bytes(row.get('font_metrics',source[at+16:at+21])):raise ValueError('Final font metrics differ')
    elf=(folder/'EBOOT.BIN').read_bytes();info=build['executable']['ui_hook']
    runner=H._Runner(elf,int(info['stub_va'],16),info['stub_bytes']);read=H._reader(elf,H._headers(elf)[2])
    grouped,translations=U.checked();report=T.report(grouped,translations,E.resolver());cases=[]
    from tools.dialogue_layout import PREFIX
    for row in report['rows']:
        active=dict(mapping)
        if row['condensed']:
            for c in set(row['text']):
                if 32<=ord(c)<127:active[c]=mapping[PREFIX+c]
        for occurrence in grouped[row['id']]:
            if not occurrence['id'].startswith('aid:6:'):continue
            key=H.utf8_key(occurrence['raw'],H.PREPARED.read_bytes());want=E.encode(row['text'],active,utf8_source=True)
            pointer,steps=runner.run(key+b'\0')
            if read(pointer,len(want)+1)!=want+b'\0':raise ValueError('Final tutorial row lookup differs')
            cases.append(dict(source=occurrence['id'],steps=steps,width=row['width'],budget=row['budget']))
    # Both neutral lookup and colored FSSA paths share the same alphabet,
    # preventing differently sized duplicate captions in the emblem footer.
    captions=[]
    for at,jp in ((0x9ba84,'獲得条件：'),(0x9baa4,'装備効果：')):
        key=jp.encode('cp932');pointer,steps=runner.run(key+b'\0');wanted=widgets[at+grow]['raw']
        if read(pointer,len(wanted)+1)!=wanted+b'\0':raise ValueError('Emblem footer uses mismatched letter masks')
        captions.append(dict(widget_offset=at,matched_neutral_colored_paths=True,steps=steps))
    original=H.PREPARED.read_bytes()
    for va,jp,en in P.CELLS:
        wanted=__import__('tools.status_layout',fromlist=['CELL']).CELL[en].encode('utf8')+b'\0'
        if read(va,4)!=wanted:raise ValueError('Final parts movement cell differs')
    for va in (0x3150e8,0x31532c):
        if read(va,4)!=original[va-0x10000:va-0x10000+4]:raise ValueError('Parts formatter instruction changed')
    from tools.ui_build import atlas,cell_xy,glyph_pixels
    checked=0
    with CPK(folder/'TPACKPS3.CPK')as font:
        for page in (1,3):
            pixels=atlas(font.read(next(e for e in font.files if e['id']==page)))
            for token,code in mapping.items():
                if not token.startswith(N.PREFIX):continue
                import numpy as np
                x,y=cell_xy(code);want=glyph_pixels(N.raster(token[len(N.PREFIX):])[0])
                if not np.array_equal(pixels[y:y+32,x:x+32],want):raise ValueError('Final native fill/outline masks differ')
                checked+=1
    shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dst=ROOT/'work/ui/screenshots'/('reported-0.5.18-review22-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(issue=label,source=str(src),saved_path=str(dst),source_version='0.5.18',sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=version,prior_verification=prior,iso_verification=prior['iso_verification'],
        layout=plan,tutorial_layout=report,tutorial_lookup_cases=cases,emblem_captions=captions,
        native_font_cells_checked=checked,parts_movement=build['executable']['parts_movement'],
        screenshots=shots,runtime_verified=False,proofreading=dict(reviewer='review22_help_wording',assigned_items=15,source_rows_examined=146))

def main():
    from tools.game_build import VERSION
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--version',default=VERSION);ap.add_argument('--apply',action='store_true');a=ap.parse_args();result=verify(a.version)
    print('Widgets:',len(result['layout']['edits']),'Help lookups:',len(result['tutorial_lookup_cases']),'Native cells:',result['native_font_cells_checked'])
    print('ISO:',result['iso_verification']['sha256'])
    if not a.apply:print('DRY RUN: no evidence written.');return
    for shot in result['screenshots']:
        dst=Path(shot['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists()and sha256_file(dst)!=shot['sha256']:raise ValueError('Screenshot collision')
        if Path(shot['source'])!=dst:shutil.copyfile(shot['source'],dst)
    write_json(ROOT/'work/ui'/('review22_verified_'+a.version+'.json'),result)

if __name__=='__main__':main()

"""Read the shipped deployment, news, glossary dialogue and keyword data."""
import argparse,json,shutil,struct
from pathlib import Path
from tools.common import ROOT,sha256,sha256_file,write_json
from tools.pipeline import config
from tools.cpk import CPK
from tools import review42_layout as D,review42_news as N,keyword_popup as K
from tools import ui_catalog as U,menu_layout as M,ui_hook as H,dialogue_build as DB,dialogue as DL

VERSION='0.5.42'
SHOTS=(('deployment','bff0c740-bd6a-4cef-a9b1-930052ccb507'),
       ('Psyco-Waves','6e38f109-e63d-4530-a8dc-5aea74a874a6'),
       ('northern-Europe','61a4753b-2cb0-4916-ae18-e6c6b44f15b8'),
       ('South-America-Pacific','f626ed27-b98b-4fc5-b43c-4ae95370af5d'))

def verify():
    folder=ROOT/'work/output/builds'/VERSION;b=json.loads((folder/'build.json').read_text('utf8'))
    parent=json.loads((ROOT/'work/output/builds/0.5.40/build.json').read_text('utf8'))
    for name,digest in b['outputs'].items():
        if sha256_file(folder/name)!=digest:raise ValueError('Compiled output differs: '+name)
    if b['version']!=VERSION or b['mapping']!=parent['mapping'] or b['widths']!=parent['widths']:
        raise ValueError('Font codes or advances changed')
    for name in ('TPACKPS3.CPK','RPW_DATA.CPK','MTZKN_KW.CPK','MTZKN_PT.CPK','MTZKN_RT.CPK','SRVC.BIN','CMN.CPK','OP.CPK','TROPHY.TRP'):
        if b['outputs'][name]!=parent['outputs'][name]:raise ValueError('Unrelated asset changed: '+name)
    mapping=b['mapping'];elf=(folder/'EBOOT.BIN').read_bytes()
    news=N.verify(elf,mapping,b['executable']['ui_hook'],b['executable']['link_layout'])
    print('Compiled news: 22 paragraphs / 38 scenario bindings / native row copy, lookup and centering passed.',flush=True)
    with CPK(folder/'AIDDATAPACK.CPK')as arc:ui=arc.read(next(r for r in arc.files if r['id']==0))
    source=D.B.source();grow=len(ui)-len(source)
    widgets={a-grow:r for r in U.fssa_strings(ui,decode=lambda x:x.hex())for a in r['widget_offsets']}
    dp=D.plan()
    for edit in dp['edits']:
        if widgets[edit['widget_offset']]['raw']!=M.encode(edit,mapping):raise ValueError('Deployment widget differs')
        for field,delta in (('x',4),('y',8)):
            if field in edit and ui[edit['widget_offset']+grow+delta:edit['widget_offset']+grow+delta+4]!=struct.pack('>f',edit[field]):
                raise ValueError('Deployment coordinate differs')
    with CPK(ROOT/'work/output/builds/0.5.40/AIDDATAPACK.CPK')as arc:
        before=arc.read(next(r for r in arc.files if r['id']==0))
    old_grow=len(before)-len(source)
    old_widgets={a-old_grow:r for r in U.fssa_strings(before,decode=lambda x:x.hex())for a in r['widget_offsets']}
    edits={e['widget_offset']:e for e in dp['edits']}
    if widgets.keys()!=old_widgets.keys():raise ValueError('Widget identities changed')
    for at,row in old_widgets.items():
        edit=edits.get(at,{})
        if not edit and widgets[at]['raw']!=row['raw']:raise ValueError('Unrelated widget text changed: '+hex(at))
        original_state=bytearray(before[at+old_grow+4:at+old_grow+32])
        final_state=bytearray(ui[at+grow+4:at+grow+32])
        if 'x'in edit:final_state[:4]=original_state[:4]
        if final_state!=original_state:raise ValueError('Unrelated widget geometry/style/state changed: '+hex(at))
    # Retain both preloaded Search states and both map selector states too.
    from tools import review40_tabs as T,review39_selector as SELECT
    for edit in T.plan()['edits']+SELECT.plan()['edits']:
        if widgets[edit['widget_offset']]['raw']!=M.encode(edit,mapping):raise ValueError('Earlier selection fix regressed')
    texts={a:widgets[a]['raw']for pair in T.PAIRS.values()for a in pair}
    texts.update({a:widgets[a]['raw']for a in T.ABILITIES})
    tabs=T.native_cases(elf,mapping,b['executable']['table_va'],texts)
    print('Deployment: all 45 terrain rows and 6 compact labels read back; earlier tab states retained.',flush=True)
    from tools import eboot_text as E,dialogue_layout as A
    active=DB.translations();affected={rid:e for rid,e in active.items()if any('$$'+t+'$$'in e['en']for t in ('サイコ・ウェーブ','精神感応波'))}
    mids={int(rid.split(':')[0])for rid in affected};originals={r['id']:r for mid in mids for r in DL.records(mid)}
    resolver=E.resolver();width=lambda c:b['widths'].get(c,32);dialogues=[]
    with CPK(folder/'STGZ3OF2.cpk')as arc:
        members={mid:arc.read(next(r for r in arc.files if r['id']==mid))for mid in mids}
    for rid,entry in affected.items():
        rendered=DB.render(entry,originals[rid],resolver,width)
        if 'Psyco Waves'not in rendered:raise ValueError('Canonical term differs')
        encoded=DB.encode(rendered,A.mapping_for(rid,mapping))
        if encoded not in members[int(rid.split(':')[0])]:raise ValueError('Compiled dialogue is stale: '+rid)
        dialogues.append(dict(id=rid,english=rendered))
    if len(dialogues)!=8:raise ValueError('Psyco Waves reference count changed')
    if sha256_file(folder/'STGZ3OF2.cpk')!=b['stage_archive']['cpk_sha256'] or not b['stage_archive']['roundtrip_verified']:
        raise ValueError('Encrypted stage round trip lacks evidence')
    from tools.verify_review34 import members_equal
    isolation={}
    for name,changed in (('AIDDATAPACK.CPK',{0}),('EFFPS3.CPK',{229}),('STGZ3OF2.cpk',mids)):
        unchanged=members_equal(ROOT/'work/output/builds/0.5.40'/name,folder/name,changed)
        isolation[name]=dict(unchanged_members=len(unchanged),proof_sha256=sha256(json.dumps(unchanged,sort_keys=True).encode('utf8')))
    keywords=K.verify_archive(folder/'MTV_ALL_KEYWORD_DEF.CPK',K.plan(config(ROOT/'config/tengoku.json'),mapping))
    image=json.loads((ROOT/'work/output/iso'/VERSION/('Tengoku-hen-English-'+VERSION+'.json')).read_text('utf8'))
    if image['version']!=VERSION or image['files_verified_each_tree']!=82 or image['replaced'].get(K.DISC)!='MTV_ALL_KEYWORD_DEF.CPK':
        raise ValueError('Final ISO inventory differs')
    if sha256_file(Path(image['image']))!=image['sha256']:raise ValueError('Final ISO changed')
    shots=[]
    for label,ident in SHOTS:
        src=Path('C:/Users/Binh/AppData/Local/Temp')/('codex-clipboard-'+ident+'.png')
        dst=ROOT/'work/ui/screenshots'/('reported-review42-'+label+'.png')
        if not src.exists():src=dst
        shots.append(dict(source=str(src),saved_path=str(dst),sha256=sha256_file(src),runtime_confirmation=False))
    return dict(schema=1,version=VERSION,previous_public_version='0.5.40',news=news,deployment=dp,
        psyco_waves=dialogues,keyword_popup=keywords,search_tab_cases=tabs,
        archive_isolation=isolation,unchanged_widget_geometry_and_styles=len(widgets),
        font_codes_advances_and_archive_unchanged=True,iso_verification=image,screenshots=shots,runtime_verified=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--apply',action='store_true');a=p.parse_args()
    if a.preview:print('DRY RUN: compiled report sources, native row copy/draw/origins, deployment widgets, eight term references, actual popup archive and final ISO.');return
    data=verify();print('Final ISO:',data['iso_verification']['sha256'])
    if a.apply:
        for row in data['screenshots']:
            src,dst=Path(row['source']),Path(row['saved_path']);dst.parent.mkdir(parents=True,exist_ok=True)
            if dst.exists()and sha256_file(dst)!=row['sha256']:raise ValueError('Screenshot collision')
            if src!=dst:shutil.copyfile(src,dst)
        write_json(ROOT/'work/ui'/('review42_verified_'+VERSION+'.json'),data)
    else:print('DRY RUN: no evidence written.')

if __name__=='__main__':main()

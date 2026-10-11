"""Preview source-bound caption fixes from the user's latest UI review."""
import argparse
import json
from tools.common import ROOT,sha256,write_json
from tools import ui_catalog as U


def wording(jp,en):
    if jp=='格闘':return 'CQB'
    if '・音声設定' in jp:
        en=en.replace('・Voice Settings ( :    )','・Voice Vol.').replace('・Voice Volume','・Voice Vol.')
        en=en.replace('・SE Settings','・SE Vol.').replace('・SE Volume','・SE Vol.')
        en=en.replace('・BGM Settings','・BGM Vol.').replace('・BGM Volume','・BGM Vol.')
    if 'ソート・サブ情報の記憶' in jp:
        en=en.replace('Remember Sort / Secondary Info','Remember Sort/Info')
    return en


def plan():
    sources={sha256(r['text'].encode('utf8'))[:20]:r['text']for r in U.sources()}
    out=[]
    for p in sorted(U.DEST.glob('*.json')):
        data=json.loads(p.read_text(encoding='utf8'));changes=[]
        for rid,row in data['strings'].items():
            jp=sources[rid];before=row['en'];after=wording(jp,before)
            if after!=before:
                row['en']=after;row['layout_note']='Screenshot review 0.5.15: fit native label slots and fixed controller icons.'
                changes.append((rid,before,after))
        if changes:out.append((p,data,changes))
    p=ROOT/'work/translation/en/ui/eboot.json';data=json.loads(p.read_text(encoding='utf8'))
    before=data['strings']['格闘']['en']
    if before!='CQB':
        data['strings']['格闘']['en']='CQB';out.append((p,data,[('格闘',before,'CQB')]))
    return out


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true')
    args=ap.parse_args();pending=plan()
    for p,data,changes in pending:
        for rid,before,after in changes:print(p.name,rid,repr(before),'->',repr(after))
    if args.apply:
        for p,data,changes in pending:write_json(p,data)
    else:print('DRY RUN: no translations written.')


if __name__=='__main__':main()

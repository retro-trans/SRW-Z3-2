"""Remove lowercase overrides of the glossary's Arm Raker proper term."""
import argparse,json
from tools import dialogue as D, library_text as L
from tools.common import ROOT,sha256_file,write_json
DEST=ROOT/'work/ui/review33_names.json'

def plan():
    terms=json.loads(L.GLOSSARY.read_text('utf8'))['terms']
    matching=[t for t in terms if t.get('token')=='アームレイカー']
    if len(matching)!=1 or matching[0]['en']!='Arm Raker':raise ValueError('Arm Raker glossary changed')
    edits=[];count=0
    for path in sorted(D.TRANSLATIONS.glob('*.json')):
        for rid,row in json.loads(path.read_text('utf8')).get('rows',{}).items():
            if 'アームレイカー' in row['en']:count+=1
            new=row['en'].replace('$$アームレイカー|lc$$','$$アームレイカー$$')
            if new!=row['en']:edits.append(dict(path=str(path),id=rid,source_sha=row['sha'],before=row['en'],after=new))
    return dict(schema=1,version='0.5.33',term='Arm Raker',active_references=count,edits=edits,
                glossary_sha256=sha256_file(L.GLOSSARY))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');a=ap.parse_args();data=plan()
    for edit in data['edits']:print(edit['id'],repr(edit['before']),'->',repr(edit['after']))
    print('Active term references:',data['active_references'])
    if not a.apply:print('DRY RUN: no dialogue written.');return
    for edit in data['edits']:
        from pathlib import Path
        path=Path(edit['path']);raw=path.read_bytes();before=json.dumps(edit['before'],ensure_ascii=False).encode('utf8');after=json.dumps(edit['after'],ensure_ascii=False).encode('utf8')
        if raw.count(before)!=1:raise ValueError('Ambiguous Arm Raker row')
        path.write_bytes(raw.replace(before,after))
    write_json(DEST,data)

if __name__=='__main__':main()

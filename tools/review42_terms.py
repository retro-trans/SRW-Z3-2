"""Apply the user's exact Psyco Waves spelling to active sources only."""
import argparse,json
from tools.common import ROOT,write_json

def plan():
    p=ROOT/'work/glossary/library_terms.json';data=json.loads(p.read_text(encoding='utf8'));changed=[]
    for row in data['terms']:
        if row['token'] not in ('サイコ・ウェーブ','精神感応波'):continue
        if row['en'] not in ('Psycho-Waves','Psyco Waves'):raise ValueError('Conflicting term correction')
        row.update(en='Psyco Waves',status='confirmed',
            source='User correction 2026-10-15: Psyco Waves. Preserve this spelling and capitalization in running speech.')
        changed.append(row['token'])
    if len(changed)!=2:raise ValueError('Term alias coverage changed')
    out=[(p,data)]
    for p in sorted((ROOT/'work/translation/en/dialogue').glob('*.json')):
        data=json.loads(p.read_text(encoding='utf8'));n=0
        for row in data.get('rows',{}).values():
            text=row['en']
            for token in changed:text=text.replace('$$'+token+'|lc$$','$$'+token+'$$')
            if text!=row['en']:row['en']=text;n+=1
        if n:out.append((p,data));print(p.relative_to(ROOT),'running-speech rows:',n)
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();changes=plan()
    print('Glossary aliases: Psyco Waves; files:',len(changes))
    if a.apply:
        for path,data in changes:write_json(path,data)
    else:print('DRY RUN: no translation data written.')

if __name__=='__main__':main()

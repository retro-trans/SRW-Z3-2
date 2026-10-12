"""Measured caption alignment and the reviewed normal-font Mao explanation."""
import argparse,json
from tools.common import ROOT,sha256_file,write_json

CAPTION_SHA='36755227d4'
CAPTION_IDS={'51:t_1:57','63:t_1:266','395:t_1:3','395:t_3:38','407:t_2:3','413:t_1:3','413:t_2:3'}
CAPTION='～ $$ガルガンティア船団$$ / Fleet Commander\'s Room ～'
MAO_ID='81:t_1:64'
MAO_SHA='4e0167391c'
MAO="$$マオ$$\n「It's a term for humanity's natural enemies we can't talk to. As $$ワッ太$$ says, the $$ヒディアーズ#keyword$$ fighting the $$人類銀河同盟$$ for survival are probably a type of 《$$バアル$$》.」"

def centered(text,record,width_of):
    if record.get('id')not in CAPTION_IDS:return text
    if record['sha']!=CAPTION_SHA:raise ValueError('Gargantia caption source changed')
    from tools.dialogue import BOX_UNITS
    lines=text.split('\n')
    if len(lines)!=3 or any(line.strip('　 ')for line in lines[:2]):raise ValueError('Caption blank rows changed')
    body=lines[2].lstrip('　 ')
    if body!="～ Gargantia Fleet / Fleet Commander's Room ～":raise ValueError('Caption meaning changed')
    span=sum(map(width_of,body));space=width_of(' ')
    if span>BOX_UNITS or space<=0:raise ValueError('Caption does not fit normal font')
    padding=round((BOX_UNITS-span)/2/space)
    lines[2]=' '*padding+body
    return '\n'.join(lines)

def plan():
    from tools import dialogue as Q
    source={r['id']:r for r in Q.plan_rows()};changes=[];outputs={};seen=set()
    for path in sorted((ROOT/'work/translation/en/dialogue').glob('*.json')):
        data=json.loads(path.read_text(encoding='utf8'));local=[]
        for rid,row in data.get('rows',{}).items():
            if rid not in CAPTION_IDS|{MAO_ID}:continue
            if row['sha']!=source[rid]['sha'] or row['sha']!=(MAO_SHA if rid==MAO_ID else CAPTION_SHA):raise ValueError('Reported dialogue binding changed')
            seen.add(rid);old=row['en']
            if rid==MAO_ID:new=MAO
            else:
                lines=old.split('\n')
                if len(lines)!=3 or "Fleet Commander's Room"not in lines[2]:raise ValueError('Reported location caption changed')
                lead=lines[2][:len(lines[2])-len(lines[2].lstrip('　 '))]
                new='\n'.join(lines[:2]+[lead+CAPTION])
            if old!=new:row['en']=new;local.append(dict(id=rid,source_sha=row['sha'],old=old,new=new))
        if local:outputs[path]=data;changes.append(dict(file=path.relative_to(ROOT).as_posix(),source_sha256=sha256_file(path),changes=local))
    if seen!=CAPTION_IDS|{MAO_ID}:raise ValueError('Reported dialogue coverage incomplete')
    return dict(schema=1,version='0.5.25',caption_records=len(CAPTION_IDS),normal_font_record=MAO_ID,
                changes=changes,reviewer='review25_wording',source_rows_examined=47),outputs

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();report,outputs=plan()
    for file in report['changes']:
        for row in file['changes']:print(row['id'],repr(row['old']),'->',repr(row['new']))
    if not a.apply:print('DRY RUN: no dialogue written.');return
    for path,data in outputs.items():
        newline='\r\n'if b'\r\n'in path.read_bytes()else '\n'
        path.write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').replace('\n',newline).encode('utf8'))
    if outputs:write_json(ROOT/'work/ui/review25_dialogue_audit.json',report)

if __name__=='__main__':main()

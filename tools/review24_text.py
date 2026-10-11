"""Preview concise deployment commands and distributive PP award wording."""
import argparse,json
from tools.common import ROOT,write_json

CHANGES={
 'help':{'129fca590d7cb35d1a16':'・Select Team',
         '67dd0320f2664ba08619':'・Prep Menu',
         'e06a31e6c49aeb8f9743':'・Map Deploy'},
 'generated':{'3f1190ade1a57f98941a':'Each deployed pilot received',
              'c26131936557f8a29952':'%s PP.'}}

def plan():
    changes=[]
    for family,rows in CHANGES.items():
        path=ROOT/'work/translation/en/ui/expanded'/(family+'.json')
        data=json.loads(path.read_text(encoding='utf8'))
        for rid,en in rows.items():
            old=data['strings'][rid]['en']
            changes.append(dict(file=str(path),id=rid,before=old,after=en))
            data['strings'][rid]['en']=en
        yield path,data,changes[-len(rows):]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
    for path,data,changes in plan():
        for r in changes:print(path.name,r['id'],repr(r['before']),'->',repr(r['after']))
        if a.apply:write_json(path,data)
    if not a.apply:print('DRY RUN: no translations written.')

if __name__=='__main__':main()

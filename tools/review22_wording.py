"""Preview the reviewed short help labels and fixed-row tutorial wording."""
import argparse,json
from tools.common import write_json
from tools import ui_catalog as U

REVISIONS={
 '7260573b15752cc50444':('1. Changes to the Battle System','1. Battle Changes'),
 '174e8fa3a113eb6d222f':('2. New Feature: Z Crystal','2. Z Crystal'),
 '5c0cad2953a83cac0e51':('13. New Feature: D Commands','13. D Commands'),
 '156f82ae7af3941b9e12':('14. New Feature: Shinka','14. Shinka'),
 '2594cfd5b1480b8503cf':('1. Lecture Plates (Team Setup)','1. Team Setup Guide'),
 'cf991e543fe10d755bdb':('2. Changes to Team Setup','2. Team Setup Changes'),
 '7c5d9d783a5d36bf2567':('3. Event Sorties and Disbanding','3. Event Sortie & Disband'),
 'c56bdea92c3aa60173ec':(None,'●Wide Attack: Your main attacks their main, and your sub attacks their sub.'),
 'a875317b4a689b3b0db4':(None,'  and from combat and its results. More Song Energy strengthens song effects.'),
 '0ba4c2f203085202ecb4':('Acquisition Condition:','Need:'),
 '443fd8711641b2ab41e5':('Equipped Effect:','Effect:'),
}
CONTEXT={
 '156f82ae7af3941b9e12':'Use the established target term Shinka for the named pilot-machine fusion state. The root terminology pass owns the English name normalization. ',
 'a875317b4a689b3b0db4':'Deliberate continuation of a multi-row UI sentence; read with adjacent source IDs. ',
}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');a=ap.parse_args();seen=set()
    for path in U.DEST.glob('*.json'):
        data=json.loads(path.read_text(encoding='utf8'));changed=False
        for rid,(old,new)in REVISIONS.items():
            if rid not in data['strings']:continue
            row=data['strings'][rid];seen.add(rid)
            if old is not None and row['en']not in (old,new):raise ValueError('Reviewed source wording changed')
            print(rid,repr(row['en']),'->',repr(new));row['en']=new
            row['notes']=CONTEXT.get(rid,'')+'Review22: short caption / preserve fixed native row.'
            if path.stem=='help':row['notes']+=' Tutorial wording reviewed by review22_help_wording.'
            changed=True
        if changed and a.apply:write_json(path,data)
    if seen!=set(REVISIONS):raise ValueError('Missing reviewed wording ID')
    if not a.apply:print('DRY RUN: no translations written.')

if __name__=='__main__':main()

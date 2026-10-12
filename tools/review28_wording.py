"""Preview/apply reviewed defeat-quote wording and synchronize active copies."""
import argparse,json,copy
from tools.common import ROOT,sha256_file,write_json
from tools import rpw_text as R,eboot_text as E

REPORTS=ROOT/'work/output/scratch/review28'
DEST=ROOT/'work/ui/review28_wording_audit.json'


def plan():
    originals={};outputs={};reviews=[];edits=[]
    def load(path):
        if path not in originals:
            originals[path]=json.loads(path.read_text('utf8'));outputs[path]=copy.deepcopy(originals[path])
        return outputs[path]
    names=load(R.NAMES);quotes=names['strings']['quote'];exe=load(E.TRANSLATION)
    for n in range(3):
        path=REPORTS/('wording_%02d.json'%n);report=json.loads(path.read_text('utf8'));reviews.append(report)
        answer=R.NEW/('r_quote_%02d.json'%n);data=load(answer);keys=list(data['rows'])
        for edit in report['edits']:
            key=keys[edit['ordinal']];jp=key.removeprefix('quote:').replace('\\n','\n')
            current=quotes[jp]['en']
            if current not in(edit['before'],edit['after']):raise ValueError('Reviewed quote drift')
            if R.unusual(edit['after'])or current.count('\n')!=edit['after'].count('\n'):raise ValueError('Reviewed quote structure differs')
            quotes[jp]=dict(quotes[jp],en=edit['after'],source='review28:agent-meaning-review')
            edits.append(dict(slice=report['slice'],ordinal=edit['ordinal'],source_sha256=__import__('hashlib').sha256(jp.encode('utf8')).hexdigest(),**{k:edit[k]for k in('before','after','reason')}))
    # The two nonverbal records already have approved executable translations.
    rows=[r for r in R.slots(R.load_rpw())if r['family']=='quote']
    for row in rows:
        jp=row['jp']
        if jp not in quotes:
            en=exe['strings'].get(jp,{}).get('en')
            if not en:raise ValueError('Missing nonverbal defeat quote')
            quotes[jp]=dict(en=en,source='review28:existing-executable-punctuation')
    # Use current active wording, including earlier reviews, in all export
    # copies. An old answer merge must not reintroduce stale translations.
    for path in sorted(R.NEW.glob('r_quote_*.json')):
        data=load(path)
        for key,row in data['rows'].items():
            jp=key.removeprefix('quote:').replace('\\n','\n');row['en']=quotes[jp]['en']
    for jp,row in quotes.items():
        exe['strings'][jp]=dict(exe['strings'].get(jp,{}),en=row['en'],source='review28:complete-defeat-quotes')
    for path in sorted(E.NEW.glob('e_defeat_quotes_*.json')):
        data=load(path)
        for key,row in data['rows'].items():
            jp=key.replace('\\n','\n')
            if jp in quotes:row['en']=quotes[jp]['en']
    files=[dict(file=str(p.relative_to(ROOT)).replace('\\','/'),source_sha256=sha256_file(p))for p in outputs if outputs[p]!=originals[p]]
    report=dict(schema=1,version='0.5.28',meaning_edits=edits,reviews=reviews,files=files,
        distinct_quotes=len(quotes),source_scripts_changed=False)
    return report,{p:d for p,d in outputs.items()if d!=originals[p]}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();report,outputs=plan()
    print('Reviewed edits:',len(report['meaning_edits']),'distinct quotes:',report['distinct_quotes'],'files:',len(outputs))
    for edit in report['meaning_edits']:print(edit['slice'],edit['ordinal'],repr(edit['before']),'->',repr(edit['after']))
    if a.apply:
        for path,data in outputs.items():write_json(path,data)
        write_json(DEST,report)
    else:print('DRY RUN: no files changed.')

if __name__=='__main__':main()

"""Isolated dialogue retranslation batches, with source-bound six-agent assignments."""
import argparse
import contextlib
import io
import json
import shutil
from pathlib import Path
from tools import dialogue as d
from tools.common import ROOT, sha256_file, write_json

RUN = ROOT/'work/translation/en/retranslation_2026-10-07'
STAGES = d.PLAN[:15]  # Existing batch 1: two prologues, stages 1-8, Green choice.
SCOPE = 'first ten in play order, including two prologues and Green route choice'
BATCH = 1


def configure(batch):
    global RUN, STAGES, SCOPE, BATCH
    BATCH = batch
    if batch == 1:
        RUN = ROOT/'work/translation/en/retranslation_2026-10-07'
        STAGES = d.PLAN[:15]
        SCOPE = 'first ten in play order, including two prologues and Green route choice'
    elif batch == 2:
        RUN = ROOT/'work/translation/en/retranslation_2026-10-07_batch2'
        STAGES = d.PLAN[15:29]
        SCOPE = 'stages 9-18 on route A: Green Earth 9-11, common 12-16, Macross Quarter 17-18, and 2210/2211 choice scenes'
    elif batch == 3:
        RUN = ROOT/'work/translation/en/retranslation_2026-10-07_batch3'
        STAGES = d.PLAN[29:43]
        SCOPE = 'stages 19-28 on route A: Macross Quarter 19-20, joined MQ/Hive 21-22, common 23-25, continent 26-28, and 2220/2221 choice scenes'
    elif batch == 4:
        RUN = ROOT/'work/translation/en/retranslation_2026-10-07_batch4'
        STAGES = d.PLAN[43:55]
        SCOPE = 'stages 29-38 on route A: continent 29, common 30-35, Japan Defense 36-38, and 2230/2231 choice scenes'
    elif batch == 5:
        RUN = ROOT/'work/translation/en/retranslation_2026-10-09_batch5'
        STAGES = d.PLAN[55:69]
        SCOPE = 'stages 39-48 on route A: Japan Defense 39-40, common 41-42, Shinji 43, common 44-48, and 2240/2241 choice scenes'
    elif batch == 6:
        RUN = ROOT/'work/translation/en/retranslation_2026-10-09_batch6'
        STAGES = d.PLAN[69:82]
        SCOPE = 'stages 49-58 on route A: common 49-51, Getter 52-54, common 55-56, hope 57, common 58, and 2250/2251 choice scenes'
    elif batch in range(7,13):
        start,end,scope = {
            7:(82,89,'stages 59 through the final stage and all ending scenes (2103-2106d)'),
            8:(89,111,'alternate routes: Blue Earth stages 4-11, Dragons Hive stages 17-20, and associated choices'),
            9:(111,131,'alternate routes: Sousuke rescue stages 17-22, Left-Behind Sea stages 26-29, and remaining choice D-Traders'),
            10:(131,141,'alternate routes: Neo Zeon stages 36-40 and Amalgam stages 36-40'),
            11:(141,149,'alternate routes: Crowe and Char stage 43, Macross Quarter stages 52-54, despair stage 57'),
            12:(149,152,'remaining dialogue: ace pilot talks, guidance scenario, and next-episode previews'),
        }[batch]
        RUN = ROOT/('work/translation/en/retranslation_2026-10-09_batch%d'%batch)
        STAGES = d.PLAN[start:end]
        SCOPE = scope
    else:
        raise ValueError('unsupported batch')


def groups():
    return d.slices([r for r in d.plan_rows() if r['stage'] in STAGES])


def prepare(apply=False):
    slices=groups()
    batches=[]
    pending=list(slices)
    for n in range(6):
        target=sum(len(rows) for _,rows in pending)/(6-n)
        batch=[]; count=0
        while pending:
            name,rows=pending[0]
            if batch and n<5 and abs(count-target)<abs(count+len(rows)-target):break
            pending.pop(0);batch.append((name,rows));count+=len(rows)
        batches.append({'agent':n+1,'rows':count,'slices':[name for name,_ in batch]})
    print(json.dumps(batches,indent=2))
    if not apply:
        print('DRY RUN: preserve %d existing files; prepare isolated drafts and assignments.' % len(slices))
        return
    RUN.mkdir(parents=True,exist_ok=False)
    (RUN/'prior').mkdir();(RUN/'drafts').mkdir()
    fingerprints={}
    for name,rows in slices:
        source=d.TRANSLATIONS/(name+'.json')
        shutil.copy2(source,RUN/'prior'/source.name)
        fingerprints[name]={'prior_sha256':sha256_file(source),
                            'rows':{r['id']:r['sha'] for r in rows}}
    manifest={'schema':1,'run':'2026-10-09' if BATCH >= 5 else '2026-10-07','batch':BATCH,'state':'prepared','model':'gpt-6.1-sol',
              'reasoning':'medium','agents':batches,'stages':STAGES,
              'scope':SCOPE,
              'total_rows':sum(len(rows) for _,rows in slices),'slices':fingerprints}
    write_json(RUN/'manifest.json',manifest)


def source(name):
    group=dict(groups())[name]
    all_rows=d.plan_rows();by_id={r['id']:i for i,r in enumerate(all_rows)}
    terms=json.loads(d.GLOSSARY.read_text(encoding='utf-8'))['terms']
    resolver=d.Resolver(terms)
    start=by_id[group[0]['id']];end=by_id[group[-1]['id']]+1
    for r in all_rows[max(0,start-8):min(len(all_rows),end+8)]:
        options,status=d.speaker_options(r['jp'],resolver)
        print(json.dumps({'id':r['id'],'sha':r['sha'],'stage':r['stage'],
              'assigned':r['id'] in {x['id'] for x in group},'speaker_options':options,
              'speaker_status':status,'pid':r['pid'],'jp':r['jp']},ensure_ascii=False))


def check(name=None):
    manifest=json.loads((RUN/'manifest.json').read_text(encoding='utf-8'))
    expected=manifest['slices']
    names=[name] if name else list(expected)
    valid=True; rows=0
    if name is None:
        extra={p.stem for p in (RUN/'drafts').glob('*.json')}-set(expected)
        if extra:
            print('ERROR unassigned files: '+', '.join(sorted(extra)));valid=False
    for key in names:
        path=RUN/'drafts'/(key+'.json')
        if not path.exists():
            print('MISSING '+key);valid=False;continue
        data=json.loads(path.read_text(encoding='utf-8'))
        actual={rid:r.get('sha') for rid,r in data.get('rows',{}).items()}
        if actual!=expected[key]['rows']:
            print('ERROR row scope/fingerprint '+key);valid=False
        if data.get('slice')!=key or data.get('schema')!=1:
            print('ERROR schema/slice '+key);valid=False
        report=data.get('report',{})
        if report.get('rows_in_slice')!=len(actual) or report.get('rows_examined')!=len(actual):
            print('ERROR examination counts '+key);valid=False
        if report.get('left_untranslated'):
            print('ERROR untranslated rows '+key);valid=False
        rows+=len(actual)
    original=d.TRANSLATIONS
    try:
        d.TRANSLATIONS=RUN/'drafts'
        with contextlib.redirect_stdout(io.StringIO()) as output:
            checked=d.check(name+'.json' if name else None)
        details=output.getvalue()
        print(details,end='')
        # The older checker reports these as warnings, but an isolated draft
        # must not claim readiness with unresolved tokens or overflowing text.
        warnings='TOO LONG ' in details or 'names not in the glossary (' in details
        valid=checked and not warnings and valid
    finally:d.TRANSLATIONS=original
    print('RETRANSLATION: %d rows; %s'%(rows,'PASS' if valid else 'INCOMPLETE/ERROR'))
    return valid


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=('prepare','source','check'))
    p.add_argument('--slice');p.add_argument('--apply',action='store_true')
    p.add_argument('--batch',type=int,choices=range(1,13),default=1)
    a=p.parse_args()
    configure(a.batch)
    if a.command=='prepare':prepare(a.apply)
    elif a.command=='source':source(a.slice)
    else:raise SystemExit(0 if check(a.slice) else 1)

if __name__=='__main__':main()

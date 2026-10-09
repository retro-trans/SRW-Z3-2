"""Read-only candidates for homonymous glossary tokens contradicting source names."""
import argparse,json,re
from collections import defaultdict
from tools import dialogue as d
from tools import dialogue_retranslate as r

def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',type=int,required=True);a=p.parse_args();r.configure(a.batch)
    source={x['id']:x['jp'].partition('\n')[2] for x in d.plan_rows()}
    terms=json.loads(d.GLOSSARY.read_text(encoding='utf-8'))['terms'];by_token={t['token']:t for t in terms};by_en=defaultdict(list)
    for t in terms:
        if t.get('en'):by_en[t['en'].casefold()].append(t)
    count=0
    for path in sorted((r.RUN/'drafts').glob('*.json')):
        data=json.loads(path.read_text(encoding='utf-8'))
        for rid,row in data['rows'].items():
            for match in re.finditer(r'\$\$([^$]+)\$\$',row['en'].partition('\n')[2]):
                tk=match[1].split('|')[0];term=by_token.get(tk)
                if not term or term['jp'] in source[rid]:continue
                candidates=[t['token'] for t in by_en[term['en'].casefold()] if t['jp'] in source[rid] and t['jp']!=term['jp']]
                if candidates:
                    count+=1;print(json.dumps(dict(file=path.name,id=rid,token=tk,candidates=candidates,jp=source[rid],en=row['en']),ensure_ascii=False))
    print('Source-name collision candidates:',count,'(review required; no changes made)')

if __name__=='__main__':main()

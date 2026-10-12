"""Measure every runtime team-name dialogue row with the native full-width name."""
import argparse,json,re
from functools import lru_cache
from tools.common import ROOT,sha256,write_json
from tools import dialogue as Q,dialogue_build as D,dialogue_layout as A,eboot_text as E,ui_hook as H

DEST=ROOT/'work/ui/review27_dialogue_audit.json'
TEAM_OFFSET=0x8cc1c0
TARGET='194:t_1:82'
TARGET_SHA='a87061d96e'

def guard(elf):
    raw=Q.TEAM_NAME.encode('utf8')+b'\0'
    if elf[TEAM_OFFSET:TEAM_OFFSET+len(raw)]!=raw:raise ValueError('Native team name source changed')
    return sha256(raw)

def plan(width=None):
    from tools.ui_vwf_build import raster
    if width is None:
        @lru_cache(None)
        def width(c):return raster(c)[1]if 32<=ord(c)<127 else 32
    team_sha=guard(H.PREPARED.read_bytes());source={r['id']:r for r in Q.plan_rows()};active=D.translations();res=E.resolver();rows=[]
    for rid,entry in active.items():
        if '$c'not in entry['en']:continue
        record=source[rid]
        if entry['sha']!=record['sha']:raise ValueError('Runtime name row source changed')
        rendered=D.render(entry,record,res,width)
        w=lambda c:0 if c in D.LINK_MARKS else A.advance(width(c),A.scale(rid))if A.condensed(rid)and ord(c)<128 else width(c)
        spans=[Q.speech_units(line,w)for line in rendered.split('\n')[1:]]
        if max(spans)>Q.BOX_UNITS:raise ValueError('Runtime team name exceeds dialogue width: '+rid)
        for part in entry['en'].partition('\n')[2].split('\n'):
            single=dict(entry,en=entry['en'].partition('\n')[0]+'\n'+part)
            if len(D.render(single,record,res,width).split('\n'))-1>Q.MAX_SPEECH_LINES:raise ValueError('Runtime name exceeds dialogue rows: '+rid)
        if sorted(Q.CODES.findall(rendered))!=sorted(Q.CODES.findall(record['jp'])):raise ValueError('Runtime control changed')
        rows.append(dict(id=rid,source_sha=entry['sha'],english_sha256=sha256(entry['en'].encode('utf8')),
                         rendered_sha256=sha256(rendered.encode('utf8')),row_widths=spans))
    if len(rows)!=800 or source[TARGET]['sha']!=TARGET_SHA:raise ValueError('Runtime team-name category changed')
    return dict(schema=1,version='0.5.27',team_name_units=Q.TEAM_UNITS,native_team_sha256=team_sha,
        records=rows,reported_id=TARGET,reported_rendered=D.render(active[TARGET],source[TARGET],res,width),
        runtime_verified=False,custom_team_names='Width reserved for the six-cell default native name.')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan()
    print('Runtime team-name records:',len(data['records']),'Reserved units:',data['team_name_units']);print(data['reported_rendered'])
    print('Maximum rendered row:',max(w for r in data['records']for w in r['row_widths']))
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no dialogue audit written.')

if __name__=='__main__':main()

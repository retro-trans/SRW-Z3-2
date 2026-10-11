"""Fit help selector columns and fixed tutorial rows without adding line breaks."""
import re
from tools.ui_description_layout import advance,condensed_advance

def budget(sources):
    rows=[int(s['id'].split(':')[-1])for s in sources if s['id'].startswith('aid:6:')]
    if any(203<=r<=216 or 403<=r<=411 for r in rows):return 320
    if any(219<=r<=401 or 414<=r<=460 for r in rows):return 980
    return None

def width(text,condensed=False):
    measure=condensed_advance if condensed else advance
    clean=re.sub(r'1[\x01-\x1f]','',text)
    return max(sum(measure(c)for c in line)*28/32 for line in clean.split('\n'))

def profile(text,sources):
    limit=budget(sources)
    if limit is None:return text,False
    if '\n' in text:raise ValueError('Tutorial native row gained a line break')
    if width(text)<=limit:return text,False
    if width(text,True)>limit:raise ValueError('Tutorial row exceeds its panel: '+text)
    return text,True

def report(grouped,rows,resolver):
    from tools import eboot_text as E,library_build as L
    out=[]
    for rid,sources in grouped.items():
        limit=budget(sources)
        if limit is None or rid not in rows:continue
        text=E.unshow(L.expand(rows[rid]['en'],resolver));text,condensed=profile(text,sources)
        out.append(dict(id=rid,text=text,budget=limit,width=width(text,condensed),condensed=condensed))
    return dict(rows=out,count=len(out),condensed=sum(r['condensed']for r in out),runtime_verified=False)

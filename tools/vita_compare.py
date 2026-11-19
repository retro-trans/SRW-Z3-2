"""Read-only source/member correspondence; reports hashes, never Japanese scripts."""
import argparse
import json
from tools.common import ROOT, sha256, write_json
from tools.cpk import CPK
from tools import vita_source as V, dialogue as D


def record_keys(raw, mid):
    try:
        text = raw.decode('cp932')
    except UnicodeDecodeError:
        return {}
    keys = {}
    for event in D.EVENT.finditer(text):
        for n, block in enumerate(D.BLOCK.finditer(event.group(2))):
            position = event.start(2)+block.start()
            head = D.HEAD.search(text, max(0,position-160), position)
            if head:
                value = block.group(1).replace('\r\n','\n')
                keys[f'{mid}:{event.group(1)}:{n}'] = (head.group(4), D.digest(value))
    return keys


def compare():
    source = ROOT/'work/tengoku/source/PS3_GAME/USRDIR'
    indexed = {p.name.lower():p for p in source.rglob('*') if p.is_file()}
    pairs = []
    for vita in sorted(V.PLAIN.rglob('*.cpk')):
        ps3 = indexed.get(vita.name.lower())
        if vita.name == 'STGZ3OF2.cpk':
            ps3 = ROOT/'work/tengoku/prepared/STGZ3OF2.dec.cpk'
        if not ps3:
            continue
        text_archive = vita.name.lower() in ('stgz3of2.cpk','rpw_data.cpk',
            'mtzkn_kw.cpk','mtzkn_pt.cpk','mtzkn_rt.cpk','mtv_all_keyword_def.cpk','luacpk.cpk')
        with CPK(vita) as a, CPK(ps3) as b:
            if text_archive:
                av = {r['id']:a.read(r) for r in a.files}
                bv = {r['id']:b.read(r) for r in b.files}
                same = [k for k,raw in av.items() if k in bv and raw == bv[k]]
            else:
                # Different platform textures require separate porting anyway.
                # Prove identical stored members without materializing gigabytes
                # of decoded artwork; differing streams remain unverified.
                av = {r['id']:r for r in a.files}
                bv = {r['id']:r for r in b.files}
                same = [k for k,r in av.items() if k in bv and
                    (r['size'],r['extract']) == (bv[k]['size'],bv[k]['extract']) and
                    a.buf[r['offset']:r['offset']+r['size']] ==
                    b.buf[bv[k]['offset']:bv[k]['offset']+bv[k]['size']]]
        row = dict(vita=vita.relative_to(V.PLAIN).as_posix(), ps3=str(ps3.relative_to(ROOT)),
                   vita_members=len(av), ps3_members=len(bv), identical_members=same,
                   unverified_or_different_members=[k for k in av if k not in same],
                   decoded_comparison=text_archive)
        if vita.name == 'STGZ3OF2.cpk':
            records = []
            for mid in sorted(set(av)&set(bv)):
                ak, bk = record_keys(av[mid],mid), record_keys(bv[mid],mid)
                if ak or bk:
                    records.append(dict(member=mid, vita_records=len(ak), ps3_records=len(bk),
                        identical_records=sum(k in bk and v==bk[k] for k,v in ak.items()),
                        mismatched_ids=[k for k,v in ak.items() if k not in bk or v!=bk[k]],
                        missing_in_vita=[k for k in bk if k not in ak]))
            row['dialogue'] = records
        pairs.append(row)
        print('Compared',row['vita'],len(same),'proven identical members.',flush=True)
    return dict(schema=1,title_id=V.TITLE, archive_pairs=pairs, runtime_verified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args()
    result=compare()
    for row in result['archive_pairs']:
        print(row['vita'],row['vita_members'],'members;',len(row['identical_members']),'byte-identical to PS3')
        if 'dialogue' in row:
            rows=row['dialogue']
            print('Dialogue:',sum(r['vita_records'] for r in rows),'Vita;',sum(r['ps3_records'] for r in rows),'PS3;',
                  sum(r['identical_records'] for r in rows),'exact identities; mismatches:',sum(len(r['mismatched_ids'])+len(r['missing_in_vita']) for r in rows))
    if a.apply:write_json(V.WORK/'source_correspondence.json',result)
    else:print('DRY RUN: no report written.')


if __name__=='__main__':main()

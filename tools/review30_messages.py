"""Bind every native skill-learning, level-raise and overwrite question."""
import argparse,json,struct
from tools.common import ROOT,sha256,write_json
from tools import rpw_text as R,source_text as T,ui_hook as H,eboot_text as E
from tools.ui_description_layout import advance
DEST=ROOT/'work/translation/en/ui/review30_messages.json'
START,END=0x319038,0x319480
FRAGMENTS={0xa088d8:'Ｌ',0xa088dc:'＋',0xa088e0:'「',0xa088e4:'」になります。',
    0xa088f4:'＋１」を新規に修得します。',0xa08910:'」を新規に修得します。',
    0xa08928:'」は上書きされて無くなります。'}

def source_rows(elf):
    read=H._reader(elf,H._headers(elf)[2])
    if struct.unpack('>I',read(H.TOC-0x1518,4))[0]!=0xa08888:raise ValueError('Learning fragment binding changed')
    if struct.unpack('>I',read(H.TOC-0x14ec,4))[0]!=0xa2f5a0:raise ValueError('Learning digit table changed')
    for va,jp in FRAGMENTS.items():
        if read(va,len(jp.encode('cp932'))+1)!=jp.encode('cp932')+b'\0':raise ValueError('Learning fragment changed')
    for n,va in enumerate(struct.unpack('>10I',read(0xa2f5a0,40))):
        if read(va,3)!=chr(0xff10+n).encode('cp932')+b'\0':raise ValueError('Learning level digit changed')
    source=R.load_rpw();chunk=next(c for c in T.rpw_chunks(source)if c['name']=='sk-pri');names=R.load_names();rows=[]
    for slot in R.slots(source):
        # The native getter returns the 52-byte record; the composer loads
        # its name pointer at +8 (RPW column 2), including Element variants.
        if slot['family']!='skill'or slot['col']!=2 or not R.needs_text(slot['jp']):continue
        raw=source[chunk['body_offset']+slot['record']*52:chunk['body_offset']+(slot['record']+1)*52]
        en=R.text_for(slot,names)
        if not en:raise ValueError('Untranslated skill base')
        rows.append(dict(record=slot['record'],jp=slot['jp'],en=en,flags=struct.unpack_from('<I',raw)[0],source_record_sha256=sha256(raw)))
    if len(rows)!=81:raise ValueError('Skill family coverage changed')
    return rows

def plan():
    elf=H.PREPARED.read_bytes();read=H._reader(elf,H._headers(elf)[2]);rows=source_rows(elf)
    return dict(schema=1,version='0.5.30',skill_records=[{k:v for k,v in row.items()if k!='jp'}for row in rows],
        composer_va=START,composer_bytes=END-START,composer_sha256=sha256(read(START,END-START)),
        fragments={hex(va):sha256(jp.encode('cp932'))for va,jp in FRAGMENTS.items()},
        categories=['learn','learn-plus-one','raise-level','raise-innate-plus-learned','overwrite'],runtime_verified=False)

def characters():return set('Learn Raise to from Lv Overwrite will be lost. "0123456789')

def hook_entries(elf,mapping):
    if json.loads(DEST.read_text('utf8'))!=plan():raise ValueError('Learning prompt bindings stale')
    out={};opening='「'.encode('cp932');suffix={va:jp.encode('cp932')for va,jp in FRAGMENTS.items()}
    def add(name,tail,en,ident):
        key=opening+name+tail
        if H.extent(key+b'\0')!=len(key):raise ValueError('Invalid learning key')
        if sum(map(advance,en))*31/32>1040:raise ValueError('Learning sentence crosses question panel')
        row=dict(id='review30:skill:'+ident,key=key,english=E.encode(en,mapping))
        if key in out and out[key]['english']!=row['english']:raise ValueError('Contradictory learning prompt')
        out[key]=row
    for row in source_rows(elf):
        en=row['en']
        for kind,name in [('source',row['jp'].encode('cp932')),('translated',E.encode(en,mapping))]:
            ident=str(row['record'])+':'+kind
            add(name,suffix[0xa08910],'Learn "'+en+'".',ident+':learn')
            add(name,suffix[0xa088f4],'Learn "'+en+' +1".',ident+':learn-one')
            add(name,suffix[0xa08928],'Overwrite "'+en+'"; this skill will be lost.',ident+':overwrite')
            if not row['flags']&2:continue
            for n in range(1,10):
                level=('＋'+chr(0xff10+n)).encode('cp932')
                add(name,level+suffix[0xa088e4],'Raise "'+en+'" to +'+str(n)+'.',ident+':raise:'+str(n))
                for innate in range(10):
                    form=('Ｌ'+chr(0xff10+innate)+'＋'+chr(0xff10+n)).encode('cp932')
                    text='Raise "'+en+'" to Lv '+str(innate)+' + '+str(n)+'.'
                    add(name,form+suffix[0xa088e4],text,ident+':raise:'+str(innate)+':'+str(n))
    return list(out.values())

def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();data=plan()
    print('Skills:',len(data['skill_records']),'Categories:',data['categories'])
    print('Examples: Learn "E-Save". / Raise "Potential" to +3. / Raise "Potential" to Lv 3 + 2. / Overwrite "Counter"; this skill will be lost.')
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no learning data written.')
if __name__=='__main__':main()

"""Translate the complete trophy UI; preserve every ID, trigger and icon."""
import argparse,hashlib,json,struct,xml.etree.ElementTree as ET
from tools.common import ROOT,sha256,write_json
from tools.pipeline import config,verified_source

DISC='/PS3_GAME/TROPDIR/NPWR07804_00/TROPHY.TRP'
DEST=ROOT/'work/translation/en/ui/trophies.json'
TEXTS=(
 ('Tengoku-hen Master','Earn every trophy.'),
 ('Scenario Complete','Complete the Scenario Chart.'),
 ('Emblem Collector','Obtain all five Emblems.'),
 ("DEM's Loyal Customer",'Buy all 24 standard Power Parts at D-Trader and upgrade the Z Crystal to Grade 5.'),
 ('SR Point Master','Earn 61 SR Points.'),
 ('Game Clear','Clear the game.'),
 ('Pilot Trainer','Train at least 30 Ace Pilots.'),
 ('Custom King','Earn Custom Bonuses for at least 30 units.'),
 ('Single Smash','Deal at least 50,000 damage to one enemy in a single battle.'),
 ('Multi Smash','Shoot down at least 10 enemies at once with a MAP weapon.'),
 ('Savvy Shopper','Meet the unlock conditions for all 24 standard Power Parts at D-Trader.'),
 ('Super Ace Pilot','Have one pilot exceed 200 kills.'),
 ('Gold Finger','Earn over 30,000,000 funds in total.'),
 ('Sweet Nail',"Reduce an enemy's HP to a single digit in battle."),
 ('High Tension','Raise Tag-Tension to two stars for at least 16 allied teams.'),
 ('Ready for Battle','Clear the Guidance Scenario.'),
 ('The Long War Begins','Clear Episode 1.'),
 ('Maximum Break','Use Maximum Break.'),
 ('Tactical Combo MAX','Max out the Tactical Combo gauge.'),
 ('Ace Pilot','Train any pilot into an Ace Pilot.'),
 ('Custom Bonus','Earn a Custom Bonus for any unit.'),
 ('Thanks for Shopping','Buy any of the 24 standard Power Parts at D-Trader.'),
 ('Time to Rest','View a quit message.'),
 ('Emblem of Battle','Obtain one Emblem.'),
 ('Beautiful Warrior','Train any female pilot into an Ace Pilot.'),
 ('Spirit Unity','Have every Spirit Command in the Search list available among your deployed allies.'),
 ('Out-of-Range Attack','Attack an enemy from at least 15 spaces away, excluding MAP weapons.'),
 ('Thousand Smash','Shoot down at least 1,000 enemies across all allies.'),
 ('Love and Courage','Have one unit under the effects of $$加速#spirit$$, $$必中#spirit$$, $$閃き#spirit$$, $$熱血#spirit$$, $$直撃#spirit$$, $$努力#spirit$$ and $$幸運#spirit$$ at once.'),
 ('Difference in Skill','Shoot down at least five enemies with critical hits in one stage.'),
 ('Two Birds, One Strike','Shoot down two enemies at once with an ALL attack.'),
 ('Lucky Day','Use $$幸運#spirit$$ and $$祝福#spirit$$ a combined total of at least 10 times in one stage.'),
 ('Five Actions','Have one team successfully use Multi Action four times in one turn. Other units may act between these actions.'),
 ('Unsung Hero','Have one allied pilot perform four Support Attacks in one turn.'),
 ('One Unit, a Thousand Foes','Have one allied pilot shoot down at least 15 enemies in one stage.'))


def unpack(blob):
    if blob[:8]!=bytes.fromhex('dca24d0000000002'):raise ValueError('Unsupported TRP header')
    size,count,stride=struct.unpack_from('>QII',blob,8)
    if size!=len(blob)or stride!=64 or count!=40:raise ValueError('Trophy container geometry changed')
    zero=bytearray(blob);zero[28:48]=bytes(20)
    if hashlib.sha1(zero).digest()!=blob[28:48]:raise ValueError('TRP checksum mismatch')
    entries=[]
    for n in range(count):
        at=64+64*n;header=blob[at:at+64];name=header[:32].split(b'\0')[0].decode('ascii')
        pos,length=struct.unpack_from('>QQ',header,32)
        if pos%16 or pos<64+64*count or pos+length>size:raise ValueError('TRP entry bounds changed')
        entries.append(dict(name=name,header=header,data=blob[pos:pos+length]))
    if len({r['name']for r in entries})!=count:raise ValueError('Duplicate TRP filenames')
    return entries


def source():
    return verified_source(config(ROOT/'config/tengoku.json'),DISC).read_bytes()


def plan():
    # Apply glossary names after proofreading; bind the same Spirit tokens
    # that the game's command-name table uses, across this entire category.
    import re
    terms=json.loads((ROOT/'work/glossary/glossary.json').read_text(encoding='utf8'))['terms']
    names={t['token']:t['en']for t in terms if t['kind']=='spirit' and t['meaning_reviewed']}
    def expand(text):return re.sub(r'\$\$([^$]+)\$\$',lambda m:names[m[1]],text)
    original=source();entries=unpack(original);by={r['name']:r['data']for r in entries}
    if by['TROP.SFM']!=by['TROP_00.SFM']:raise ValueError('Source language metadata differ')
    xml=ET.fromstring(by['TROP.SFM']);rows=xml.findall('trophy')
    if len(rows)!=35 or [r.get('id')for r in rows]!=['%03d'%n for n in range(35)]:raise ValueError('Trophy IDs changed')
    out=[]
    for row,(name,detail)in zip(rows,TEXTS):
        name,detail=expand(name),expand(detail)
        if len(name.encode('utf8'))>127 or len(detail.encode('utf8'))>1023:raise ValueError('OS trophy text limit exceeded')
        out.append(dict(id=row.get('id'),attributes=dict(row.attrib),
            source_name_sha256=sha256(row.findtext('name').encode('utf8')),
            source_detail_sha256=sha256(row.findtext('detail').encode('utf8')),name=name,detail=detail))
    return dict(schema=1,version='0.5.20',source_sha256=sha256(original),
        title_name='Super Robot Wars Z3: Tengoku-hen',
        title_detail='Trophies for Super Robot Wars Z3: Tengoku-hen.',
        trophies=out,translated_files=['TROP.SFM','TROP_00.SFM'],translated_fields_per_file=72,
        trophy_ids_changed=False,icons_changed=False,runtime_verified=False)


def translated_metadata(raw,data):
    # ElementTree removes the obsolete signature comment; no signing claim.
    xml=ET.fromstring(raw)
    xml.find('title-name').text=data['title_name'];xml.find('title-detail').text=data['title_detail']
    for row,en in zip(xml.findall('trophy'),data['trophies']):
        if dict(row.attrib)!=en['attributes']:raise ValueError('Trophy attributes changed')
        for field in ('name','detail'):
            if sha256(row.findtext(field).encode('utf8'))!=en['source_'+field+'_sha256']:raise ValueError('Trophy source text changed')
            row.find(field).text=en[field]
    return ET.tostring(xml,encoding='utf-8',xml_declaration=True)


def build():
    data=json.loads(DEST.read_text(encoding='utf8'))
    if data!=plan():raise ValueError('Trophy translations/source bindings are stale')
    original=source();entries=unpack(original);count=len(entries)
    out=bytearray(original[:64]);out[28:48]=bytes(20);out.extend(bytes(64*count))
    for n,row in enumerate(entries):
        raw=translated_metadata(row['data'],data)if row['name']in data['translated_files']else row['data']
        out.extend(bytes((-len(out))%16));pos=len(out);out.extend(raw)
        header=bytearray(row['header']);struct.pack_into('>QQ',header,32,pos,len(raw))
        out[64+64*n:128+64*n]=header
    struct.pack_into('>Q',out,8,len(out));out[28:48]=hashlib.sha1(out).digest()
    verify(original,bytes(out),data)
    return bytes(out),dict(source_sha256=sha256(original),output_sha256=sha256(out),
        trophy_count=35,translated_fields=144,translated_files=data['translated_files'],
        untouched_payloads=38,ids_types_hidden_flags_and_icons_preserved=True,container_sha1_verified=True)


def verify(original,final,data):
    before,after=unpack(original),unpack(final)
    for a,b in zip(before,after):
        if a['name']!=b['name']or a['header'][:32]+a['header'][48:]!=b['header'][:32]+b['header'][48:]:raise ValueError('Trophy entry identity changed')
        if a['name']not in data['translated_files']:
            if a['data']!=b['data']:raise ValueError('Unrelated trophy payload changed')
            continue
        src,dst=ET.fromstring(a['data']),ET.fromstring(b['data'])
        if dst.findtext('title-name')!=data['title_name']or dst.findtext('title-detail')!=data['title_detail']:raise ValueError('Trophy title readback failed')
        for row,en in zip(dst.findall('trophy'),data['trophies']):
            if row.findtext('name')!=en['name']or row.findtext('detail')!=en['detail']:raise ValueError('Trophy English readback failed')
        # Restoring only the 72 text values must recover the complete XML tree.
        for tag in ('title-name','title-detail'):dst.find(tag).text=src.findtext(tag)
        for arow,brow in zip(src.findall('trophy'),dst.findall('trophy')):
            for tag in ('name','detail'):brow.find(tag).text=arow.findtext(tag)
        if ET.tostring(src)!=ET.tostring(dst):raise ValueError('Trophy structure/trigger metadata changed')
    return True


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');a=ap.parse_args();data=plan()
    for row in data['trophies']:print(row['id'],row['name'],'/',row['detail'])
    if a.apply:write_json(DEST,data)
    else:print('DRY RUN: no trophy translations written.')

if __name__=='__main__':main()

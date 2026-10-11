"""Relocate context-bound widget labels inside Tengoku's FSSA string section."""
import json
import struct

from tools.common import ROOT, sha256
from tools import ui_catalog, eboot_text, library_build as lb, aid_art
from tools.ui_coverage import member, ui_string_table
from tools.cpk import CPK

CATALOG = ROOT/'work/translation/en/ui/expanded_fragments.json'


def fssa_patch(source, edits, mapping, element_edits=()):
    rows = ui_catalog.fssa_strings(source)
    widgets = {at:r for r in rows for at in r['widget_offsets']}
    base,end = struct.unpack_from('>II',source,0x20)
    pool_size = end-base
    appendix, offsets, seen = bytearray(), {}, set()
    changes = []
    for edit in edits:
        at = edit['widget_offset']
        if at in seen or at not in widgets:
            raise ValueError('Duplicate/foreign fragment widget')
        seen.add(at)
        row = widgets[at]
        if sha256(row['raw'])!=edit['source_sha256'] or sha256(source[at:at+32])!=edit['source_widget_sha256']:
            raise ValueError('Fragment widget fingerprint changed')
        pointer = struct.unpack_from('>I', source, at)[0]
        if 'en' in edit:
            from tools.menu_layout import encode
            english = encode(edit,mapping)
            if english not in offsets:
                offsets[english] = pool_size+len(appendix)
                appendix += english+b'\0'
            pointer = offsets[english]
        changes.append((at,pointer,edit))
    appendix += bytes(-len(appendix)%4)
    grow = len(appendix)
    header = bytearray(source[:end])
    for at in range(0x10,0x7c,4):
        old = struct.unpack_from('>I',source,at)[0]
        if old>=end:
            struct.pack_into('>I',header,at,old+grow)
    out = header+appendix+source[end:]
    for at,pointer,edit in changes:
        struct.pack_into('>I',out,at+grow,pointer)
        for field,delta in (('x',4),('y',8)):
            if field in edit:
                import math
                value = float(edit[field])
                if not math.isfinite(value) or not -2<=value<=2:
                    raise ValueError('Invalid bound widget coordinate')
                struct.pack_into('>f',out,at+grow+delta,value)
        if 'font_metrics' in edit:
            metrics=edit['font_metrics']
            if len(metrics)!=5 or any(type(v)!=int or not 1<=v<=64 for v in metrics):
                raise ValueError('Invalid bound font metrics')
            out[at+grow+16:at+grow+21]=bytes(metrics)
        if 'mode' in edit:
            if edit['mode'] != source[at+23]&~0x40:
                raise ValueError('Only native count-centering may be cleared')
            out[at+grow+23]=edit['mode']
    element_start,element_end=struct.unpack_from('>II',source,0x50)
    for edit in element_edits:
        at=edit['element_offset']
        if at in seen or not element_start<=at<element_end or (at-element_start)%12:
            raise ValueError('Duplicate/foreign FSSA element')
        seen.add(at)
        if sha256(source[at:at+12])!=edit['source_element_sha256']:
            raise ValueError('FSSA element fingerprint changed')
        value=float(edit['x'])
        import math
        if not math.isfinite(value) or not -2<=value<=2:
            raise ValueError('Invalid bound element coordinate')
        struct.pack_into('>f',out,at+grow,value)
    verify_fssa(source,bytes(out),edits,mapping,element_edits)
    return bytes(out),dict(widgets=len(changes),appended_pool_bytes=grow,original_pool_preserved=True,
        positioned_elements=len(element_edits),
        header_sections_relocated=True,runtime_verified=False,layout_verified=False)


def verify_fssa(source,out,edits,mapping,element_edits=()):
    base,end = struct.unpack_from('>II',source,0x20)
    grow = len(out)-len(source)
    restored = bytearray(out[:end]+out[end+grow:])
    for at in range(0x10,0x7c,4):
        old = struct.unpack_from('>I',source,at)[0]
        wanted = old+grow if old>=end else old
        if struct.unpack_from('>I',out,at)[0]!=wanted:
            raise ValueError('FSSA section relocation mismatch')
        restored[at:at+4] = source[at:at+4]
    decoded = ui_catalog.fssa_strings(out,decode=lambda raw:lb.decode(raw,mapping))
    by_widget = {at:r for r in decoded for at in r['widget_offsets']}
    for edit in edits:
        at = edit['widget_offset']
        row = by_widget[at+grow]
        original_pointer = struct.unpack_from('>I',source,at)[0]
        original_raw = source[base+original_pointer:source.index(0,base+original_pointer)]
        from tools.menu_layout import encode
        wanted = encode(edit,mapping) if 'en' in edit else original_raw
        if row['raw']!=wanted or ('en' in edit and row['offset']<end):
            raise ValueError('FSSA English widget readback failed')
        restored[at:at+4] = source[at:at+4]
        for field,delta in (('x',4),('y',8)):
            if field in edit:
                if out[at+grow+delta:at+grow+delta+4]!=struct.pack('>f',edit[field]):
                    raise ValueError('FSSA bound coordinate readback failed')
                restored[at+delta:at+delta+4] = source[at+delta:at+delta+4]
        if 'font_metrics' in edit:
            if out[at+grow+16:at+grow+21]!=bytes(edit['font_metrics']):
                raise ValueError('FSSA bound font metrics readback failed')
            restored[at+16:at+21]=source[at+16:at+21]
        if 'mode' in edit:
            if out[at+grow+23]!=edit['mode']:raise ValueError('FSSA mode readback failed')
            restored[at+23]=source[at+23]
    for edit in element_edits:
        at=edit['element_offset']
        if out[at+grow:at+grow+4]!=struct.pack('>f',edit['x']):
            raise ValueError('FSSA bound element coordinate readback failed')
        restored[at:at+4]=source[at:at+4]
    if restored!=source or out[base:end]!=source[base:end]:
        raise ValueError('FSSA bytes changed outside appended text, headers and bound pointers/coordinates')


def table_patch(source, edits, mapping):
    rows = ui_string_table(source)
    text_at = 32+struct.unpack_from('>I',source,24)[0]
    pool_at = text_at+16
    out = bytearray(source)
    changed = set()
    for edit in edits:
        rid = edit['table_row_id']
        if rid in changed or not 0<=rid<len(rows):
            raise ValueError('Duplicate/foreign SB2T row')
        changed.add(rid)
        row = rows[rid]
        if sha256(row['raw'])!=edit['source_sha256']:
            raise ValueError('SB2T fragment fingerprint changed')
        pos = len(out)-pool_at
        out += eboot_text.encode(edit['en'],mapping)+b'\0'
        struct.pack_into('>I',out,row['pointer_offset'],pos)
    struct.pack_into('>I',out,text_at+8,len(out)-pool_at)
    restored = bytearray(out[:len(source)])
    restored[text_at+8:text_at+12] = source[text_at+8:text_at+12]
    for edit in edits:
        row = rows[edit['table_row_id']]
        ptr = struct.unpack_from('>I',out,row['pointer_offset'])[0]
        raw = out[pool_at+ptr:out.index(0,pool_at+ptr)]
        if raw != eboot_text.encode(edit['en'],mapping):
            raise ValueError('SB2T English readback failed')
        restored[row['pointer_offset']:row['pointer_offset']+4]=source[row['pointer_offset']:row['pointer_offset']+4]
    if restored!=source:
        raise ValueError('SB2T unrelated bytes changed')
    return bytes(out)


def plan(settings,mapping):
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    fixes = json.loads((ROOT/'work/ui/startup_layout.json').read_text(encoding='utf-8'))
    catalog['edits'] += fixes['edits']
    from tools.menu_layout import DEST
    menu = json.loads(DEST.read_text(encoding='utf-8'))
    catalog['edits'] += menu['edits']
    from tools import status_layout
    status=json.loads(status_layout.DEST.read_text(encoding='utf-8'))
    if status!=status_layout.plan():raise ValueError('Status plan differs from source/geometry')
    catalog['edits']=status_layout.merge(catalog['edits'],status['edits'])
    from tools import battle_layout
    battle=json.loads(battle_layout.DEST.read_text(encoding='utf8'))
    if battle!=battle_layout.plan():raise ValueError('Battle plan differs from source/geometry')
    catalog['edits']=status_layout.merge(catalog['edits'],battle['edits'])
    from tools import intermission_layout
    intermission=json.loads(intermission_layout.DEST.read_text(encoding='utf8'))
    if intermission!=intermission_layout.plan():raise ValueError('Intermission plan differs from source')
    catalog['edits']=status_layout.merge(catalog['edits'],intermission['edits'])
    from tools import settings_layout
    settings_data=json.loads(settings_layout.DEST.read_text(encoding='utf8'))
    if settings_data!=settings_layout.plan():raise ValueError('Settings layout plan is stale')
    catalog['edits']=status_layout.merge(catalog['edits'],settings_data['edits'])
    from tools import category_ui
    category=json.loads(category_ui.DEST.read_text(encoding='utf8'))
    if category!=category_ui.plan():raise ValueError('Category layout plan is stale')
    catalog['edits']=status_layout.merge(catalog['edits'],category['edits'])
    from tools import review19_layout
    review19=json.loads(review19_layout.DEST.read_text(encoding='utf8'))
    if review19!=review19_layout.plan():raise ValueError('Review 19 layout plan is stale')
    catalog['edits']=status_layout.merge(catalog['edits'],review19['edits'])
    from tools import upgrade_layout
    upgrade=json.loads(upgrade_layout.DEST.read_text(encoding='utf8'))
    if upgrade!=upgrade_layout.plan():raise ValueError('Upgrade layout plan is stale')
    catalog['edits']=status_layout.merge(catalog['edits'],upgrade['edits'])
    from tools import review21_layout
    review21=json.loads(review21_layout.DEST.read_text(encoding='utf8'))
    if review21!=review21_layout.plan():raise ValueError('Review21 layout plan is stale')
    catalog['edits']=status_layout.merge(catalog['edits'],review21['edits'])
    from tools import review22_layout
    review22=json.loads(review22_layout.DEST.read_text(encoding='utf8'))
    if review22!=review22_layout.plan():raise ValueError('Review22 layout plan is stale')
    catalog['edits']=status_layout.merge(catalog['edits'],review22['edits'])
    from tools import review23_layout
    review23=json.loads(review23_layout.DEST.read_text(encoding='utf8'))
    if review23!=review23_layout.plan():raise ValueError('Review 23 layout plan is stale')
    catalog['edits']=status_layout.merge(catalog['edits'],review23['edits'])
    from tools import review24_layout
    review24=json.loads(review24_layout.DEST.read_text(encoding='utf8'))
    if review24!=review24_layout.plan():raise ValueError('Review 24 layout plan is stale')
    catalog['edits']=status_layout.merge(catalog['edits'],review24['edits'])
    art = aid_art.plan(settings)
    original = member(art['source_path'])
    if sha256(original)!=catalog['source_member_sha256']:
        raise ValueError('Context-bound menu source changed')
    if sha256(original)!=fixes['source_member_sha256']:
        raise ValueError('Screenshot-bound startup UI source changed')
    if sha256(original)!=menu['source_member_sha256']:
        raise ValueError('Screenshot-bound menu UI source changed')
    if sha256(original)!=status['source_member_sha256']:
        raise ValueError('Screenshot-bound status UI source changed')
    catalog['element_edits']=menu['element_edits']
    data, report = fssa_patch(original,catalog['edits'],mapping,catalog['element_edits'])
    art['members'][0] = data
    art['sources'][0] = original
    table_edits = catalog['table_fragments']
    sb2t = member(art['source_path'],5)
    art['members'][5] = table_patch(sb2t,table_edits,mapping)
    art['sources'][5] = sb2t
    art['text_catalog'] = catalog
    art['mapping'] = mapping
    art['report']['context_text'] = dict(report,sb2t_fragments=len(table_edits))
    return art


def verify_archive(path,planned):
    with CPK(path) as built:
        for entry in built.files:
            mid = entry['id']
            if mid in planned['members'] and built.read(entry)!=planned['members'][mid]:
                raise ValueError('UI archive member differs from plan')
    # The normal art gate is still applied to member 1. The enclosing build's
    # archive comparison validates stored bytes for all untouched members.
    aid_art.verify_member(planned['sources'][1],planned['members'][1],planned['intended'][1],planned['rects'][1])
    verify_fssa(planned['sources'][0],planned['members'][0],planned['text_catalog']['edits'],planned['mapping'],
                planned['text_catalog']['element_edits'])
    if table_patch(planned['sources'][5],planned['text_catalog']['table_fragments'],planned['mapping'])!=planned['members'][5]:
        raise ValueError('SB2T archive fragment verification failed')
    return dict(art_members_verified=1,text_members_verified=2)

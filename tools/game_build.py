"""Build Tengoku: matched VWF executable, UI, library, dialogue and battle voice.

Dry run by default. One font allocation serves the Spirit UI and all three
library archives. Source-bound long dialogue uses a separate condensed alphabet.
Every output is read back and decoded before the build is accepted.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from tools.common import ROOT, contained, sha256, sha256_file, write_json
from tools.cpk import CPK
from tools.cpkpatch import build as build_cpk
from tools.inventory import RPW, FONT
from tools.pipeline import config, verified_source
from tools.ui_spirits import load_and_validate
from tools.ui_build import FACE, allocate, atlas, cell_xy, patch_font
from tools.ui_build import encode as ui_encode, decode as ui_decode
from tools.ui_vwf_build import raster
from tools.verify_archives import compare
from tools.self_elf import decrypt, EBOOT
from tools.vwf import patch
from tools import library_build as lb
from tools import library_compare as lc
from tools.library_text import GLOSSARY, load_library, load_translations, check
from tools.source_text import library_fields
from tools.dialogue import stage_members as dlg_stage_members

VERSION = '0.5.42'
LIBRARY = {kind: lc.MTDATA + 'MTZKN_%s.CPK' % code for kind, (code, _) in lc.KINDS.items()}


def plan(settings):
    if not check():
        raise ValueError('library translations do not pass `library_text check`')
    rows = load_and_validate(settings)['entries']
    font_path, rpw_path = verified_source(settings, FONT), verified_source(settings, RPW)
    font = CPK(font_path)
    pages = {e['id']: font.read(e) for e in font.files if e['id'] in (1, 3)}
    if set(pages) != {1, 3}:
        raise ValueError('missing font page')

    library = load_library()
    entries, _ = load_translations()
    terms = json.loads(GLOSSARY.read_text(encoding='utf-8'))['terms']
    rendered = lb.plan(library, entries, terms)

    tokens = set(lb.characters(rendered))
    # Dialogue: characters from the expanded English, before wrapping.
    from tools import dialogue_build as dbuild
    from tools.library_text import Resolver
    resolver = Resolver(terms)
    dialogue_rows = dbuild.translations()
    from tools import dialogue_layout as layout
    for rid, entry in dialogue_rows.items():
        chars = dbuild.characters([lb.expand(entry['en'], resolver)])
        tokens |= chars
        if layout.condensed(rid, entry):
            tokens.update(layout.prefix(rid) + ch for ch in chars)
    # Battle voice: same expanded-English rule, breaks are the literal two-character \n.
    from tools import srvc, voice_build
    voice_rows = voice_build.translations()
    voice_texts = voice_build.expanded(voice_rows, resolver)
    tokens |= voice_build.characters(voice_texts.values())
    # Mission conditions (docs/UI_MISSION.md): expanded English; wrapped once widths are known.
    from tools import mission_text
    tokens |= mission_text.characters(lb.expand(e['en'], resolver)
                                      for e in mission_text.load()['strings'].values() if e.get('en'))
    # Team / squad names in the stage scripts (tools/squad_text.py): plain English.
    from tools import squad_text
    squad = squad_text.plan()
    tokens |= squad_text.characters(squad.values())
    # Executable UI text (docs/UI_EBOOT.md), drawn through the hook (docs/UI_HOOK.md).
    from tools import eboot_text
    tokens |= eboot_text.characters()
    from tools import review32_content,review32_layout
    tokens |= review32_content.characters()
    from tools import review42_layout,native_labels
    for edit in review42_layout.plan()['edits']:
        chars=set(edit['en'].replace('\n','').replace('\u3000',''));tokens.update(chars)
        if edit.get('font_style')=='native-label':tokens.update(native_labels.PREFIX+c for c in chars)
    from tools import review38_fonts
    for edit in review38_fonts.plan()['edits']:
        tokens.update(native_labels.PREFIX+c for c in edit['en'])
    from tools import native_labels
    for edit in review32_layout.plan()['edits']:
        tokens.update(c for c in edit['en'] if c != '\n')
        if edit.get('font_style')=='native-label':tokens.update(native_labels.PREFIX+c for c in edit['en'] if c != '\n')
    from tools import ui_catalog
    tokens |= ui_catalog.characters()
    from tools import upgrade_messages
    tokens |= upgrade_messages.characters()
    from tools import review26_messages
    tokens |= review26_messages.characters()
    from tools import review30_messages,review30_layout,review30_movement,native_labels
    tokens |= review30_messages.characters()
    for edit in review30_layout.plan()['edits']:
        chars=set(edit['en'].replace('\n',''));tokens.update(chars)
        tokens.update(native_labels.PREFIX+c for c in chars)
    from tools import review28_quotes
    defeat_quotes_plan=review28_quotes.plan()
    for row in defeat_quotes_plan['rows']:
        tokens.update(c for c in row['english']if 32<=ord(c)<127)
    tokens.update(' Lv 0123456789')
    from tools import review21_layout
    for edit in review21_layout.plan()['edits']:tokens.update(edit['en'].replace('\n',''))
    from tools import review22_layout,native_labels
    for edit in review22_layout.plan()['edits']:
        chars=set(edit['en'].replace('\n',''));tokens.update(chars)
        if edit.get('font_style')=='native-label':tokens.update(native_labels.PREFIX+c for c in chars)
    from tools import review23_layout
    for edit in review23_layout.plan()['edits']:
        # Existing fullwidth spaces retain their native converter/font cell.
        chars=set(edit['en'].replace('\n','').replace('\u3000',''));tokens.update(chars)
        if edit.get('font_style')=='native-label':tokens.update(native_labels.PREFIX+c for c in chars)
    from tools import review24_layout
    for edit in review24_layout.plan()['edits']:
        chars=set(edit['en'].replace('\n',''));tokens.update(chars)
        if edit.get('font_style')=='native-label':tokens.update(native_labels.PREFIX+c for c in chars)
    from tools import review25_layout
    for edit in review25_layout.plan()['edits']:
        tokens.update(edit.get('en','').replace('\n',''))
    tokens.update('HibikiKamishiroK.')
    from tools.menu_layout import PADS
    tokens.update(PADS)
    from tools import status_layout
    tokens.update(status_layout.TINY)
    tokens.update(status_layout.MARKERS.values())
    from tools import category_ui
    for text in category_ui.terrain_rows().values():tokens.update(text)
    tokens.update('Self SingleAreaAllTeamOwnOneAllyEnemyAlliesEnemiesFoeUnitTrainCQBRNGSKLDEFEVDHITEff.')
    from tools import battle_layout
    tokens.update(battle_layout.TINY)
    for edit in battle_layout.plan()['edits']:tokens.update(edit['en'].replace('\n',''))
    for text in list(battle_layout.HOOKS.values())+['Debris Field']:tokens.update(text)
    # RPW name tables (docs/UI_RPW.md): English letters; other symbols stay cp932.
    from tools import rpw_text
    rpw_names = rpw_text.load_names()
    for table in list(rpw_names['strings'].values()) + [rpw_names['slots']]:
        for e in table.values():
            tokens.update(c for c in e.get('en') or '' if 32 <= ord(c) < 127)
    for row in rows:
        if row['occurrence_id'].endswith(':abbreviation'):
            tokens.add('@badge:' + row['rendered_en'])
        else:
            tokens.update(row['rendered_en'].replace('\n', ''))
    mapping, free = allocate(list(pages.values()), tokens, lambda t: [t])
    drawn = {t: raster(t) for t in mapping}
    widths = {}
    for token, code in mapping.items():
        x, y = cell_xy(code)
        if drawn[token][1] != 32:
            widths[y // 32 * 128 + x // 32] = drawn[token][1]
    width_of = lambda ch: drawn[ch][1] if ch in drawn else lb.FULLWIDTH

    members, expected, longest = {}, {}, 0
    for kind, path in LIBRARY.items():
        archive = CPK(verified_source(settings, path))
        members[kind] = {}
        for entry in archive.files:
            fields = dict(rendered[kind][entry['id']])
            for tag in ('DSCR', 'DSC2'):
                fields[tag] = lb.wrap(fields[tag], width_of)
                longest = max(longest, max(sum(width_of(c) for c in line) for line in fields[tag].split('\n')))
            payloads = {tag: lb.encode(text, mapping) for tag, text in fields.items()}
            members[kind][entry['id']] = lb.rebuild(archive.read(entry), payloads)
            expected[(kind, entry['id'])] = fields
    if longest > lb.LINE_UNITS:
        raise ValueError('a wrapped line exceeds the panel width')

    stage_members = {}
    if dialogue_rows:
        dialogue = dbuild.plan(width_of)
        for mids in dlg_stage_members().values():
            for mid in mids:
                data = dbuild.rebuild_member(mid, dialogue, mapping)
                if data is not None:
                    stage_members[mid] = data
    mission = mission_text.plan(width_of)
    from tools import mission_display
    mission_stage=mission_display.stage_text(mission)
    mission_members = 0
    for mid in squad_text.stage_members():
        data = squad_text.rebuild_member(mid, mission_stage, squad, mapping)
        if data is None:
            continue
        if mid in stage_members:
            raise ValueError('member %d holds both dialogue and mission/squad text' % mid)
        stage_members[mid] = data
        mission_members += 1

    r = CPK(rpw_path)
    rpw_source = r.read(r.files[0])
    edits = []
    for row in rows:
        raw = ui_encode(row['rendered_en'], mapping, 'vwf', row['occurrence_id'].endswith(':abbreviation'))
        if ui_decode(raw, mapping, 'vwf') != row['rendered_en']:
            raise ValueError('Spirit English encoding changed text: ' + row['occurrence_id'])
        edits.append({'id': row['occurrence_id'], 'pointer_offset': row['pointer_offset'],
                      'old': row['string_body_offset'], 'raw': raw, 'english': row['rendered_en']})
    if {e['pointer_offset'] for e in edits} != rpw_text.spirit_cells(rpw_source):
        raise ValueError('patch scope is not the complete reviewed Spirit occurrence set')
    name_cells, names_skipped = rpw_text.name_cells(rpw_source, rpw_names, lambda t: lb.encode(t, mapping))
    rpw, grow = rpw_text.patch(rpw_source, edits + name_cells)
    rpw_report = {'cells': len(name_cells), 'left_japanese_over_limits': names_skipped,
                  'families': dict(Counter(c['id'].split(':')[0] for c in name_cells))}
    elf, source_report = decrypt(verified_source(settings, EBOOT).read_bytes())
    executable, exec_report = patch(elf, widths)
    exec_report.update(source_report)
    exec_report['vwf_output_sha256'] = exec_report['output_sha256']
    from tools import ui_hook
    hook_entries, hook_skipped = eboot_text.hook_entries(elf, mapping, lambda raw: ui_hook.utf8_key(raw, elf))
    hook_entries, expanded_report = ui_catalog.hook_entries(elf,mapping,hook_entries)
    from tools import operation_layout, link_layout
    hook_entries += operation_layout.hook_entries(elf,mapping)
    upgrade_entries=upgrade_messages.hook_entries(elf,mapping)
    mission_entries=mission_display.hook_entries(elf,mission,mapping)
    review26_entries=review26_messages.hook_entries(elf,mapping)
    from tools import review27_messages
    review27_entries=review27_messages.hook_entries(elf,mapping)
    review30_entries=review30_messages.hook_entries(elf,mapping)+review30_movement.hook_entries(elf,mapping)
    review32_entries=review32_content.hook_entries(elf,mapping)
    from tools import review33_reports
    review33_entries=review33_reports.hook_entries(elf,mapping)
    from tools import review35_news,review42_news
    review35_entries=review35_news.hook_entries(elf,mapping)
    hook_entries = list({e['key']:e for e in hook_entries+status_layout.hook_entries(elf,mapping)+battle_layout.hook_entries(elf,mapping)+category_ui.hook_entries(elf,mapping)+upgrade_entries+mission_entries+review26_entries+review27_entries+review30_entries+review32_entries+review33_entries+review35_entries}.values())
    hook_entries=list({e['key']:e for e in hook_entries+review42_news.hook_entries(elf,mapping)}.values())
    from tools import ui_description_layout
    grouped_ui, translated_ui = ui_catalog.checked()
    expanded_report['description_layout'] = ui_description_layout.report(grouped_ui,translated_ui,resolver)
    from tools import tutorial_layout
    expanded_report['tutorial_layout']=tutorial_layout.report(grouped_ui,translated_ui,resolver)
    from tools import ui_runtime
    runtime_plan = ui_runtime.plan(elf,mapping)
    news42_plan=review42_news.runtime_plan(mapping)
    from tools import review24_report
    report24_plan=review24_report.plan(elf,mapping)
    from tools import runtime_names
    names_plan = runtime_names.plan(elf,mapping)
    from tools import mission_names
    names_plan['payloads'] += mission_names.payloads(mapping)
    from tools import library_runtime
    library_runtime_plan=library_runtime.plan(elf,mapping,width_of)
    from tools import review32_save
    save32_plan=review32_save.plan(elf,mapping);save32_plan['mapping']=mapping
    executable, hook_report = ui_hook.apply(executable, hook_entries,
        runtime_plan['payloads']+news42_plan['payloads']+report24_plan['payloads']+names_plan['payloads']+library_runtime_plan['payloads']+save32_plan['payloads']+review28_quotes.payloads(defeat_quotes_plan,mapping)+[(link_layout.STATE,link_layout.PAYLOAD)])
    executable,defeat_quotes_report=review28_quotes.apply(executable,defeat_quotes_plan,hook_report['table']['payload_vas'])
    defeat_quotes_report['execution']=review28_quotes.verify(executable,defeat_quotes_plan,mapping)
    exec_report['defeat_quotes']=defeat_quotes_report
    executable, runtime_report = ui_runtime.apply(executable,runtime_plan,hook_report['table']['payload_vas'])
    executable,news42_report=ui_runtime.apply(executable,news42_plan,hook_report['table']['payload_vas'])
    exec_report['news_paragraphs']=news42_report
    executable,report24_report=review24_report.apply(executable,elf,report24_plan,hook_report['table']['payload_vas'])
    runtime_report['clear_report']=report24_report
    executable, names_report = runtime_names.apply(executable,names_plan,hook_report['table']['payload_vas'])
    executable,mission_names_report=mission_names.apply(executable,hook_report['table']['payload_vas'])
    names_report['mission_substitutions']=mission_names_report
    names_report['mission_execution_cases']=mission_names.verify(executable,mapping,hook_report['table']['payload_vas'])
    executable, library_runtime_report=ui_runtime.apply(executable,library_runtime_plan,hook_report['table']['payload_vas'])
    executable, library_converter_report=library_runtime.native_patch(executable,elf,mapping)
    executable,save32_report=review32_save.apply(executable,elf,save32_plan,hook_report['table']['payload_vas'])
    exec_report['save_questions']=save32_report
    executable, library_conversion_report=library_runtime.apply_fastpath(executable,elf,library_runtime_plan,hook_report['table']['payload_vas'])
    executable, link_report = link_layout.apply(executable,elf,
        hook_report['table']['payload_vas'][link_layout.STATE],exec_report['table_va'],mapping,
        status_layout.save_specs(mapping))
    executable,status_report=status_layout.native_patch(executable,elf,mapping)
    exec_report['status_layout']=status_report
    from tools import parts_movement
    executable,parts_report=parts_movement.apply(executable,elf)
    exec_report['parts_movement']=parts_report
    executable,battle_report=battle_layout.native_patch(executable,elf,mapping)
    exec_report['battle_layout']=battle_report
    exec_report['mission_composition']=dict(
        static_cases=len(mission_display.composition_cases(executable,mission,mapping)),
        live_cases=len(mission_display.live_cases(executable,mission,mapping)),runtime_verified=False)
    from tools import mission_panel
    exec_report['mission_composition']['sr_panel_cases'] = len(mission_panel.sr_cases(executable, mission, mapping))
    exec_report['ui_hook'] = dict(hook_report if isinstance(hook_report, dict) else {'report': str(hook_report)},
                                  entries=len(hook_entries), skipped=dict(hook_skipped))
    exec_report['expanded_ui'] = expanded_report
    exec_report['runtime_ui'] = runtime_report
    exec_report['runtime_names'] = names_report
    exec_report['library_runtime']=dict(library_runtime_report,converter=library_converter_report,conversion=library_conversion_report)
    exec_report['link_layout'] = link_report
    exec_report['output_sha256'] = sha256(executable)
    voice, voice_report = None, None
    if voice_rows:
        from tools.voice_write import build as build_voice
        voice_source = verified_source(settings, srvc.SRVC).read_bytes()
        voice_edits = voice_build.edits(voice_source, srvc.read_table(executable, len(voice_source)),
                                        voice_rows, voice_texts)
        voice, executable, voice_report = build_voice(voice_source, executable, voice_edits,
                                                      lambda t: voice_build.encode(t, mapping))
        voice_report['voice_strings'] = len(voice_rows)
        exec_report['output_sha256'] = sha256(executable)   # VWF patch + hook + rewritten SRVC block table
    from tools import backlog_storage
    executable, backlog_report = backlog_storage.apply(executable)
    exec_report['backlog_storage'] = backlog_report
    exec_report['output_sha256'] = sha256(executable)
    # Texture art (docs/TEXTURES.md): title cards and map badges, never the font pages.
    from tools import texture_art
    art = texture_art.plan(pages, settings)
    # Art in other archives: (output name, disc path, plan, module, compress). Raw members, as Jigoku shipped.
    from tools import aid_art, cmn_art, op_art, ui_layout_text
    extra_art = [('CMN.CPK', cmn_art.CMN, cmn_art.plan(settings), cmn_art, False),
                 ('OP.CPK', op_art.DISC, op_art.plan(settings), op_art, False),
                 ('AIDDATAPACK.CPK', aid_art.ARCHIVE, ui_layout_text.plan(settings,mapping), ui_layout_text, False)]
    # EFFPS3: members the original stores compressed stay compressed (eff_plan['compress']).
    from tools import eff_art
    eff_plan = eff_art.plan(settings, title_version=VERSION)
    extra_art.append(('EFFPS3.CPK', eff_art.ARCHIVE, eff_plan, eff_art, eff_plan['compress']))
    from tools import keyword_popup
    extra_art.append(('MTV_ALL_KEYWORD_DEF.CPK', keyword_popup.DISC,
                      keyword_popup.plan(settings,mapping),keyword_popup,True))
    from tools import trophy_text
    trophy,trophy_report=trophy_text.build()
    summary = {'schema': 3, 'version': VERSION, 'title_id': 'BLJS10299', 'encoding': 'vwf',
               'review30':dict(learning_prompt_keys=len(review30_entries)-review30_movement.report()['draw_keys'],movement=review30_movement.report()),
               'review27':dict(save_line_keys=len(review27_entries),runtime_team_units=dbuild.dlg.TEAM_UNITS),
               'review26_messages':dict(report_strings=24,report_occurrences=99,hook_keys=len(review26_entries)),
               'upgrade_messages':dict(conditions=23,item_announcements=24,bonus_choices=9,hook_keys=len(upgrade_entries)),
               'trophies':trophy_report,
               'spirit_occurrences': len(edits), 'library_entries': {k: len(v) for k, v in members.items()},
               'dialogue_records': len(dialogue_rows), 'stage_members_rebuilt': len(stage_members),
               'dialogue_layout': {'condensed_records': sorted(set(dialogue_rows) & set(layout.CONDENSED)),
                                   'horizontal_scale': layout.SCALE,
                                   'tight_records': sorted(set(dialogue_rows)&layout.TIGHT_IDS),
                                   'tight_horizontal_scale': layout.TIGHT_SCALE},
               'rpw_names': rpw_report,
               'mission_strings': len(mission), 'squad_names': len(squad),
               'mission_display_keys': len(mission_entries),
               'mission_squad_members_rebuilt': mission_members,
               'battle_voice': voice_report,
               'allocated_cells': len(mapping), 'letter_cells': len(widths),
               'available_blank_cells': free, 'new_rpw_pool_bytes': grow,
               'library_line_units': lb.LINE_UNITS, 'longest_library_line_units': longest,
               'face_sha256': sha256_file(FACE), 'executable': exec_report,
               'texture_art': {k: v for k, v in art['report'].items() if k != 'title_cards'},
               'title_cards_rendered': sorted(art['report'].get('title_cards', [])),
               'extra_art': {name: {k: v for k, v in plan_['report'].items() if not isinstance(v, (list, dict))}
                             for name, _d, plan_, _m, _c in extra_art},
               'ui_context_text': next(plan_['report']['context_text'] for name,_d,plan_,_m,_c in extra_art if name=='AIDDATAPACK.CPK'),
               'runtime_verified': False, 'layout_verified': False}
    from tools.latin_font import profile
    summary['latin_font'] = profile()
    summary['title_screen'] = eff_plan['report']['title_screen']
    summary['scenario_chart'] = eff_plan['report']['scenario_chart']
    return dict(summary=summary, mapping=mapping, drawn=drawn, pages=pages, rpw=rpw, edits=edits,
                executable=executable, font_path=font_path, rpw_path=rpw_path, members=members,
                expected=expected, settings=settings, stage_members=stage_members,
                voice=voice, art=art, extra_art=extra_art,trophy=trophy)


def verify_library(p, output):
    """Decode every rebuilt record; untouched fields must keep their original bytes."""
    report = {}
    for kind, path in LIBRARY.items():
        source = verified_source(p['settings'], path)
        original = CPK(source)
        built = CPK(output / Path(path).name)
        for entry in built.files:
            data = built.read(entry)
            if data != p['members'][kind][entry['id']]:
                raise ValueError('library member readback mismatch: %s %d' % (kind, entry['id']))
            plain = bytes(x if x in (0, 0x5e) else x ^ 0x5e for x in data)
            want = p['expected'][(kind, entry['id'])]
            orig_raw = original.read(original.files[[e['id'] for e in original.files].index(entry['id'])])
            orig_plain = bytes(x if x in (0, 0x5e) else x ^ 0x5e for x in orig_raw)
            orig_fields = {f['tag']: orig_plain[f['offset']:f['offset'] + f['bytes']] for f in library_fields(orig_raw)[1]}
            for f in library_fields(data)[1]:
                payload = plain[f['offset']:f['offset'] + f['bytes']]
                if f['tag'] in want:
                    if lb.decode(payload, p['mapping']) != want[f['tag']]:
                        raise ValueError('decoded text mismatch: %s %d %s' % (kind, entry['id'], f['tag']))
                elif payload != orig_fields[f['tag']]:
                    raise ValueError('untouched field changed: %s %d %s' % (kind, entry['id'], f['tag']))
        report[kind] = compare(source, output / Path(path).name, p['members'][kind])
    return report


def build(p, output):
    from PIL import Image, ImageDraw
    output = contained(ROOT / 'work', output)
    output.mkdir(parents=True, exist_ok=False)
    glyphs = {t: g for t, (g, w) in p['drawn'].items()}
    font_members = {}
    for fid, raw in p['pages'].items():
        modified = patch_font(raw, p['mapping'], glyphs)
        restored = atlas(modified).copy()
        for code in p['mapping'].values():
            x, y = cell_xy(code)
            restored[y:y + 32, x:x + 32] = atlas(raw)[y:y + 32, x:x + 32]
        if raw[:128] + restored.tobytes() != raw:
            raise ValueError('unallocated font changed')
        font_members[fid] = output / ('font_%d.bin' % fid)
        font_members[fid].write_bytes(modified)
    (output / 'rpw.bin').write_bytes(p['rpw'])
    build_cpk(p['rpw_path'], output / 'RPW_DATA.CPK', {0: output / 'rpw.bin'})
    tpack_members = dict(font_members)
    if set(tpack_members) & set(p['art']['members']):
        raise ValueError('font and art members overlap')
    tpack_members.update(p['art']['members'])
    # Art members are stored CRILAYLA-compressed (round-trip checked); font pages stay as before.
    build_cpk(p['font_path'], output / 'TPACKPS3.CPK', tpack_members, compress=set(p['art']['members']))
    from tools import texture_art
    texture_report = texture_art.verify_archive(output / 'TPACKPS3.CPK', p['art'])
    (output / 'EBOOT.BIN').write_bytes(p['executable'])
    if sha256_file(output / 'EBOOT.BIN') != p['summary']['executable']['output_sha256']:
        raise ValueError('executable readback mismatch')
    staging = output / 'library_members'
    for kind, path in LIBRARY.items():
        folder = staging / kind
        folder.mkdir(parents=True)
        files = {}
        for mid, data in p['members'][kind].items():
            files[mid] = folder / ('%04d.bin' % mid)
            files[mid].write_bytes(data)
        build_cpk(verified_source(p['settings'], path), output / Path(path).name, files)
    library_report = verify_library(p, output)
    stage_report = None
    if p['stage_members']:
        from tools import dialogue_build as dbuild
        stage_report = dbuild.build_archive(p['stage_members'], output, Path(p['settings']['offline_sdat_tool']))
    outputs = ['EBOOT.BIN', 'RPW_DATA.CPK', 'TPACKPS3.CPK'] + [Path(p_).name for p_ in LIBRARY.values()]
    if stage_report:
        outputs.append('STGZ3OF2.SDAT')
    if p['voice'] is not None:
        with open(str(output / 'SRVC.BIN'), 'xb') as stream:
            stream.write(p['voice'])
        if (output / 'SRVC.BIN').read_bytes() != p['voice']:
            raise ValueError('SRVC.BIN readback mismatch')
        outputs.append('SRVC.BIN')
    disc_files, extra_reports = {}, {}
    for name, disc, art_plan, module, compress in p['extra_art']:
        if not art_plan['members']:
            continue
        source = verified_source(p['settings'], disc)
        build_cpk(source, output / name, art_plan['members'], compress=compress)
        extra_reports[name] = {'archive': compare(source, output / name, art_plan['members']),
                               'members_verified': module.verify_archive(output / name, art_plan)}
        disc_files[disc] = name
    from tools import trophy_text
    (output/'TROPHY.TRP').write_bytes(p['trophy'])
    trophy_text.verify(trophy_text.source(),(output/'TROPHY.TRP').read_bytes(),trophy_text.plan())
    disc_files[trophy_text.DISC]='TROPHY.TRP'
    outputs += sorted(disc_files.values())
    report = dict(p['summary'], mapping=p['mapping'], stage_archive=stage_report,
                  widths={t: w for t, (g, w) in p['drawn'].items()},
                  rpw_archive=compare(p['rpw_path'], output / 'RPW_DATA.CPK', {0: p['rpw']}),
                  font_archive=compare(p['font_path'], output / 'TPACKPS3.CPK',
                                       {f: (v.read_bytes() if isinstance(v, Path) else v)
                                        for f, v in tpack_members.items()}),
                  texture_art=dict(p['art']['report'], archive_members_verified=texture_report),
                  library_archives=library_report, extra_art=extra_reports, disc_files=disc_files,
                  outputs={name: sha256_file(output / name) for name in outputs})
    write_json(output / 'build.json', report)
    # Preview: a few library entries drawn with the allocated glyphs at atlas scale.
    samples = [('pilot', 0), ('keyword', 14), ('robot', 3)]
    preview = Image.new('RGB', (1300, 40 * 34), '#18202c')
    draw, y = ImageDraw.Draw(preview), 4
    for kind, mid in samples:
        draw.text((4, y), '%s %d' % (kind, mid), fill='#9fc'); y += 16
        for line in p['expected'][(kind, mid)]['DSCR'].split('\n')[:10]:
            x = 8
            for ch in line:
                if ch in glyphs:
                    preview.paste('white', (x, y, x + 32, y + 32), glyphs[ch]); x += p['drawn'][ch][1]
                else:
                    x += 32
            y += 30
        y += 10
    preview.save(output / 'library_preview.png')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='work/output/builds/' + VERSION)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    p = plan(config(ROOT / 'config/tengoku.json'))
    print(json.dumps({k: v for k, v in p['summary'].items() if k != 'executable'}, indent=2))
    sample = p['expected'][('pilot', 0)]
    print('sample pilot 0:', json.dumps({k: v[:160] for k, v in sample.items()}, ensure_ascii=False))
    if args.apply:
        build(p, ROOT / args.output)
        print('Built and verified %s: EBOOT, RPW, font, library, stage and battle voice files. Runtime pending.' % VERSION)
    else:
        print('DRY RUN: no outputs written')


if __name__ == '__main__':
    main()

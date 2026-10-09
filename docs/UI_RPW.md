# RPW name tables (pilot, robot, weapon, skill, part, series, quote)

`COMMONDATA/MTDATA/RPW_DATA.CPK` member 0 holds the game's core name tables:
record arrays whose name columns are u32 offsets into one pool of cp932
strings (`j-string`). The build appends the English to the pool and repoints
only the reviewed cells; the Japanese pool bytes never move (Jigoku crashed
when strings moved). Tool: `tools/rpw_text.py`. Spirit Commands are a
separate, earlier family (`docs/UI_SPIRITS.md`).

## Verified schema (2026-10-02)

Every value in these columns is a string start in the pristine file; the tool
rechecks it on every load.

| chunk | stride (words) | columns | family |
|---|---|---|---|
| pilot-nw | 8 | 0 display name, 1 family name, 2 given name | pilot |
| robot | 24 | 2 short name, 3 full name | robot_short / robot |
| weapon | 13 | 3 short name, 4 full name | weapon_short / weapon |
| sk-pri | 13 | 1-3 skill name | skill |
| boost-p | 21 | 1-2 part name | part |
| pro-name | 2 | 0 series title | series |
| deadmsg | 3 | 0 shoot-down quote (column 1 = pilot code) | quote |

Out of scope on purpose:
- Skill descriptions (sk-pri 4-5) and part descriptions (boost-p 3-8). In Jigoku,
  swapped part descriptions corrupted memory at boot, and skill descriptions
  went through a draw-time EBOOT hook instead.
- `p-debug` / `r-debug` and the `パ・` / `ロ・` labels (2,415 strings). These are
  internal and never drawn.
- The index tables (`pidividx`, `ridwpidx`...), which hold no string pointers.

Coverage: 3,041 distinct Japanese strings (11,472 cells).
Status 2026-10-02: all cells have English and ship in build 0.4.2; runtime fit is untested.

## Limits

Each English letter is one 2-byte font cell, as each Japanese character is.

- **Display name (pilot-nw 0): at most 15 characters.** It is the battle speaker
  name, copied into a 31-byte field (Jigoku traced the overflow).
- **Skill names: at most 13 characters.** Level-up copies them into 32-byte slots
  and appends a level suffix.
- **Part names:** the record's two names plus its six Japanese descriptions must
  stay within the largest original record. The brief gives each part's
  `max_chars`.
- **Robot short name: at most 15 characters. Weapon short name: at most 18.**
  This fits them on screen; the full name has its own column.
- Family and given names, full robot and weapon names, series titles and quotes
  have no hard limit. Jigoku shipped them at full length.

## Workflow

```
python -m tools.rpw_text slots              # schema, counts, caps
python -m tools.rpw_text reuse --apply      # glossary + Jigoku tables -> rpw_names.json
python -m tools.rpw_text check              # whole-table check
python -m tools.rpw_text export --apply     # briefs for what is left: work/tengoku/rpw_briefs/
python -m tools.rpw_text check --file r_weapon_00.json
python -m tools.rpw_text merge --apply      # rpw_new/*.json -> rpw_names.json
```

The reuse step takes:
- pilot, robot and series names from the library glossary (pilot family and
  given names are split from the glossary's full name, record by record);
- weapon, skill and part names from Jigoku's `translation/weapons.json`,
  `skills.json` and `parts.json`;
- generic grunt names and unambiguous name pieces from Jigoku's
  `enemy_names.json` and `name_pieces.json`.

## Answer file

`work/translation/en/ui/rpw_new/<brief>.json`:

```json
{
  "schema": 1,
  "rows": {
    "weapon:ザンボット・バスター": {"en": "Zambot Buster", "short": null},
    "robot:超銀河グレンラガン": {"en": "Super Galaxy Gurren Lagann", "short": "SG Gurren Lagann"},
    "pilot:ガイゾック|コンピュータードール|-": {"en": {"display": "Gaizok", "family": "Computer Doll"}},
    "skill:野性化": {"en": "Wild Instinct"},
    "quote:「くそぉぉっ！\\n　脱出するぞ、宇宙太、恵子！！」": {"en": "「Dammit!\n Bail out, Uchuta, Keiko!!」"}
  },
  "report": {"uncertain": [], "notes": ""}
}
```

- The keys are copied exactly from the brief's `## ` headings. A quote key
  shows each line break as the two characters `\n`, so in JSON it is written
  `\\n`. In `en` a line break is a real newline (`\n` in JSON).
- Robot and weapon rows:
  - `en` is the full name.
  - `short` is needed only when `en` is longer than `short_max_chars`; otherwise
    use `null`.
  - When the brief's `current` is set, keep that English as `en` unless it is
    wrong, and supply only the short form.
- Pilot rows: `en` is an object with `display`, `family` and `given`. Fill only
  the parts whose Japanese is real text (`-` means empty). `current` shows the
  pieces that already have English.

## Style

- **ASCII only.** Keep the Japanese corner brackets 「」 in quotes. Symbols that
  are already in the glossary, such as the ∀ of ∀ Gundam or Greek letters,
  may stay.
- **Names follow the glossary.** Use `work/tengoku/library_briefs/GLOSSARY.md`
  and the story English. Write out the English, never a `$$token$$`.
- **Weapons and attacks:**
  - Use Title Case and the official or common English name.
  - Match how the attack is called out in the finished battle voice: grep the
    Japanese in `work/translation/en/voice/*.json` and in
    `E:\Projects\SRW Z3\translation\weapons.json` (Jigoku, read only).
  - Generic arms: Beam Rifle, Vulcan, Missile, Beam Saber...
- **Robots:**
  - Use the official name.
  - Variant suffixes in the brief's `variant` (`（２）`, `（敵）`) are internal;
    do not translate them into the name.
  - Mode names follow the official form, e.g. "Fighter Mode".
- **Short forms:**
  - Use natural abbreviations that fans recognize, such as "SG Gurren Lagann",
    "Gundam Exia R2" or "Fed. Soldier".
  - Every variant of the same thing gets the same short form.
- **Generic people:** "<Faction> Soldier", "<Faction> Pilot", "<Faction>
  Captain". Shorten the faction when the 15-character display limit needs it
  (for example "Fed. Soldier").
- **Shoot-down quotes:**
  - Write a short battle bark in the speaker's voice.
  - Keep exactly the Japanese line breaks; the full-width indent `　` becomes
    one ASCII space.
  - Keep 「...」, and keep each line at about 36 characters or fewer.
- **`？？？`** (an unknown name) becomes `???`.

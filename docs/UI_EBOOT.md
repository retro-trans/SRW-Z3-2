# Executable UI text (EBOOT)

The Japanese UI text compiled into the program covers menus, system messages,
help, reward notices, D-Trader text, BGM titles, date and location cards, stage
titles, default team names and more. That is 3,535 distinct strings, drawn
from the research inventory `work/tengoku/research/eboot_strings.json` (method in
`eboot_strings.md`). English is stored in `work/translation/en/ui/eboot.json`.
It reaches the screen through the draw-time hook (`tools/ui_hook.py`,
`docs/UI_HOOK.md`).

The executable's own strings are never changed, so name strings that the program
also uses as keys stay intact. A given Japanese string gets one English
everywhere it is drawn.

Tool: `tools/eboot_text.py` (`inventory`, `reuse`, `export`, `check [--file]`,
`merge`).

Reuse order:
1. Tengoku English already in the project (glossary, library, RPW names,
   squad names).
2. Jigoku's exact English.

Reuse filled 2,195 strings; 1,340 went to 26 briefs in `work/tengoku/eboot_briefs/`.

Out of scope for now:
- About 104 OS-dialog strings (install, save data, trophies, PSN). They do not
  go through the game's text drawer and would need an in-place change.
- Internal keys, debug text, input palettes and pure placeholders.

## Answer file

`work/translation/en/ui/eboot_new/<brief>.json`:

```json
{"schema": 1,
 "rows": {"行け！ザンボット３": {"en": "Go! Zambot 3"},
          "南ヨーロッパ": {"en": "Southern Europe"}},
 "report": {"uncertain": [], "names": {}}}
```

- **Keys:** copy each key exactly from the brief's `## ` heading. A line break
  appears there as `\n`, written `\\n` in the JSON.
- **Control bytes:** written `{XX}`, two hex digits, for example the colour
  markup `1{0B}...1{01}`. Keep them all, in the same order.
- **printf specifiers** (`%s`, `%d`, `%2d`...): keep them all, in the same order.
- **Line breaks:** each is a real newline in `en` (`\n` in JSON). Use at most as
  many as the Japanese has. The text is not re-wrapped, so a long line overflows
  its box. Keep each English line about as long as its Japanese line: roughly
  1.8 English letters per Japanese character.

## Style

- **Characters:** ASCII. Japanese symbols such as 「」, ・ and ※ may stay where
  the layout clearly uses them, for example the 「」 around a quoted line.
  Otherwise use ASCII quotes.
- **Names:** use glossary `$$tokens$$` from
  `work/tengoku/library_briefs/GLOSSARY.md`, or the English already used in
  `work/translation/en/ui/rpw_names.json` (pilots, robots, weapons, skills,
  parts) and `squad_names.json` (teams). Spirit Commands follow
  `work/translation/en/ui/spirit_commands.json`.
- **Menus and commands:** short, Title Case labels, matching the terms already
  used:
  - Spirit Commands, Skills, Parts
  - Upgrade, Equip, Sortie, Intermission
  - Tactical Combo, Maximum Break, Z Chips, SR Point, Player Phase / Enemy Phase
- **System messages, help and rewards:** plain, clear sentences. Keep every number,
  percentage and condition exactly. 気力 = "Morale", as in the Spirit table already
  in game. Never "Focus", which is the 集中 Spirit Command. Spirit Command names
  are the project's (`work/glossary/glossary.json`: 不屈 = Persist, 鉄壁 = Wall,
  闘志 = Fighting Spirit, 直撃 = Fury), not Jigoku's. Reused Jigoku strings were
  converted on 2026-10-02. The terms used in mission
  text (`work/translation/en/ui/mission.json`) and Jigoku's catalog are the
  references.
- **Stage titles:** episode titles in Title Case. They also appear on the
  title-card images, so keep them reasonably short. Check how the story refers
  to the event if unsure.
- **BGM titles:** the official English or romanized title of the song where one
  exists. Most are anime theme songs, for example 行け！ザンボット３ =
  "Go! Zambot 3". Otherwise translate the Japanese title.
- **Date and location cards:** place names use the standard English names, such
  as 南ヨーロッパ = "Southern Europe" and 中央アジア = "Central Asia". Calendar
  and era terms follow the story's English; grep
  `work\translation\en\dialogue\*.json`.
- **Default team names** (勝平隊, 万丈隊...): "<Name> Team", consistent with
  `squad_names.json` (for example スカル小隊 = "Skull Squadron").
- **Library entries:** follow `work/translation/en/library/`.

# Battle voice translation style

Battle voice lines are the short lines a pilot says during a battle animation
(attacking, being hit, dodging, being shot down, calling a weapon...). They are
stored in `DATA/BTLC/SRVC.BIN`; see `docs/BATTLE_VOICE.md` for the format.
Read `BASE_RULES.md` and the "Settled renderings" in `docs/DIALOGUE_STYLE.md`
first: names, ranks, terms and honorific rules are the same as in the story.

## The work

- One brief = up to 80 Japanese lines of one voice set (one pilot's voice bank),
  or several small voice sets packed together. Each row id is `block:offset`.
- `python -m tools.voice export` writes the briefs to
  `work/tengoku/voice_briefs/`. Each voice-set section lists Jigoku's speaker
  identification (often right, sometimes wrong), names spoken in the lines,
  weapon leads, and lines of the same voice set that are already translated
  (reused from Jigoku-hen): match their voice, names and attack-name English.
- The same Japanese line may be used in several situations (e.g. attack and
  counterattack); write English that works for all of them.

## Answer file

`work/translation/en/voice_new/<brief>.json`:

```json
{
  "schema": 1,
  "rows": {
    "10:0": {"jp": "「...」", "en": "「I'll become like Big Sis...!」"}
  },
  "speakers": {
    "g010": {"token": "$$ノノ$$", "basis": "Calls Noriko Big Sis, Buster Machine 7 lines"}
  },
  "report": {"uncertain": [], "names": {}}
}
```

- `jp` is copied exactly from the brief (the checker compares it with the game file).
- `speakers`: for every voice set in your brief, the glossary token of the
  speaker you identified from the lines (or `null` for a generic grunt /
  unknown), with a one-line basis. Correct Jigoku's identification when the
  lines say otherwise.
- `report.names`: any name you needed that is not in the glossary (token form
  you used, proposed English, evidence).

## Text rules

- Mirror the Japanese brackets: 「...」 stays 「...」; a thought （...） becomes `(...)`.
- Line breaks: the game uses the two characters `\n` (backslash + n) inside the
  line. Keep exactly as many as the Japanese has (in the JSON that is written
  `\\n`). Do not add or remove breaks.
- Length: each segment between breaks should be at most 36 characters, names
  counted at their English length. The real battle-window limit is not measured
  yet; `check` lists longer segments as LONG. Shorten wording before meaning;
  never drop the point of the line.
- ASCII only (plus 「」). Ellipsis `...`, no em dashes, straight quotes.
- Names: glossary tokens `$$...$$` as in the story (`$$ノノ$$`, `$$宗介$$`...).
  `$n` / `$c` style codes do not occur here. Generic grunts stay generic.
- Attack and weapon names that the pilot shouts: use the English already used
  in this voice set's translated lines, else the official/common English name.
  Keep them in Title Case, without tokens unless the glossary has the exact term.
- Battle barks are short and punchy. Screams and grunts: write them as English
  interjections ("Raaaagh!", "Guh...!"), matching nearby translated ones.
- Keep each character's voice (Nono's polite "desu" quirk is dropped as in the
  story; a rough speaker stays rough). Pronouns follow the glossary gender.
- Never translate the developer placeholder line (it is not in the briefs).

## Check

```
python -m tools.voice check --file <brief>.json
```

Fix every ERROR. LONG segments are warnings; fix them where a shorter wording
keeps the full meaning.

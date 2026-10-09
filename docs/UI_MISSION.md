# Stage mission conditions

The victory, defeat and SR Point conditions are display strings in each map
script's `OPERATE_TBL={str_tbl={...}; id_tbl={...};}`. There are 287 distinct
Japanese strings across 110 stage members. `id_tbl` decides each string's role: it is
read in groups of 8, one per phase of the map:

| slot | meaning |
|---|---|
| 0 | final-condition flag |
| 1-3 | victory conditions |
| 4-6 | defeat conditions |
| 7 | SR Point condition and help text |

Tool: `tools/mission_text.py`. English goes in `work/translation/en/ui/mission.json`.

Team and squad names (`TOUROKU`, `ENEMY_TBL`, `SC_*` calls) are a separate family in
`tools/squad_text.py`. They are display text only (`work/tengoku/research/squad_names.md`),
and one combined rebuild writes both families into each member.

## Workflow

```
python -m tools.mission_text inventory
python -m tools.mission_text reuse --apply      # Jigoku's mission_conditions_hook.json (2 lines resolve)
python -m tools.mission_text export --apply     # briefs: work/tengoku/mission_briefs/
python -m tools.mission_text check --file m_00.json
python -m tools.mission_text merge --apply
python -m tools.mission_text check
```

Build:
- `game_build` expands tokens and word-wraps each paragraph to 38 full-width
  cells (the longest Japanese line is 39).
- It encodes the result with the font mapping and writes the Lua literal with
  `\n` for each break and `\\` for each 0x5C byte. Lua reads the strings byte by
  byte; the scripts already store ソ as 83 5C 5C.
- Each rebuilt member is read back byte for byte, and its `id_tbl` must not change.

## Answer file

`work/translation/en/ui/mission_new/<brief>.json`:

```json
{"schema": 1,
 "rows": {"敵の全滅。": {"en": "Defeat all enemies."},
          "このシナリオはＳＲポイントは存在しません。\\n青い文字で...": {"en": "This scenario has no SR Point.\nThe victory condition in blue is the final victory condition.\nAchieving it clears the map."}},
 "report": {"uncertain": [], "names": {}}}
```

- **Keys:** copy each key exactly from the brief's `## ` heading. A Japanese
  line break shows there as `\n`, written `\\n` in the JSON.
- **Line breaks in `en`:** a real newline (`\n` in JSON) starts a new paragraph,
  and you may use at most as many as the Japanese has. Do not break lines for
  width; the build wraps.

## Style

- **Runtime placeholders stay verbatim, with the same count as the Japanese:**
  `主人公フルネーム`, `ヒビキＡ`, `ヒビキＮ`, `カミシロＮ`, `ローカルワーク０`,
  `ローカルワーク１` and `ローカルワーク２`. The EBOOT substitutes them at run
  time, using its table at 0x9E1198. The first four become the protagonist's
  name, which the player can change, like `$n` in the story; the last three
  become per-map counter numbers. Examples: "ヒビキＡ is shot down.",
  "Reach turn ローカルワーク１." The checker enforces this.
- **Names:** use glossary `$$tokens$$` as in the story (`$$シンジ$$`,
  `$$宗介$$`...). For a unit that has no token, use the English from
  `work/translation/en/ui/rpw_names.json` (robot / pilot strings) or the
  glossary sheet.
- **Victory lines state an action to achieve**, in the imperative:
  - 〇〇の撃墜。 = "Shoot down X."
  - 敵の全滅。 = "Defeat all enemies."
  - 〇〇のＨＰを５０００以下にする。 = "Reduce X's HP to 5000 or less."
  - 〇〇に到達する。 = "Reach X." / "Move X to Y."
- **Defeat lines state a failure event:**
  - 〇〇の撃墜。 = "X is shot down."
  - 味方戦艦の撃墜。 = "An allied battleship is shot down."
  - いずれかの味方ユニットの撃墜。 = "Any allied unit is shot down."
  - 〇〇ターン目を迎える。 = "Turn N begins."
  - 敵ユニットの〇〇侵入。 = "An enemy unit enters X."
- **Never infer the role from the Japanese wording.** The same 〇〇の撃墜。 is a
  victory line for an enemy and a defeat line for an ally. A string listed with
  both roles must read correctly as both, for example "X is shot down." versus
  "Shoot down X." Pick the reading that works for both, or report it.
- **SR Point lines are conditions to achieve**, written like victory lines.
  Keep every number exactly: turn limits, unit counts, HP thresholds, phases
  (味方フェイズ = Player Phase, 敵フェイズ = Enemy Phase). The longer SR help
  paragraphs explain the rule. Keep them complete; you may tighten the wording.
- **Fixed terms:**
  - ＳＲポイント = "SR Point"
  - マップクリア = "map clear" ("clear the map")
  - 最終勝利条件 = "final victory condition"
  - タクティカルコンボ = "Tactical Combo"
  - マキシマムブレイク = "Maximum Break"
  - ＳＥＬＥＣＴボタン = "SELECT button"
  - コンバットレコード = "Combat Record"
  - レクチャープレート = "Lecture Plate"
  - なし = "None"
  - ？？？ = "???"
- **Characters:** ASCII only. 「...」 around a quoted command or menu name becomes
  double quotes.

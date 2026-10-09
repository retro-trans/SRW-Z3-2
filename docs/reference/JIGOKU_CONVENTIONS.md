# Settled conventions -- every slice reads this

These were decided while translating stages 1-30 and the intermissions. They
are not suggestions: a slice that re-decides one of them makes the shipped
text inconsistent, and someone then has to sweep it project-wide.

## Glossary terms are tokens, never literal English

Write a glossary term as `$$japanese$$` -- `$$スフィア$$`, not `Sphere`. The
build expands it, so renaming a term later updates every line at once. This
is the single most important rule after the structural ones:

* suffixes go OUTSIDE the token: `$$スフィア$$s`, `$$ジェニオン$$'s`
* `|lc` lower-cases it mid-sentence: `a $$スフィア|lc$$ bearer`
* a `#` discriminator separates two terms sharing one Japanese string:
  `$$レイ#333$$` is Rei Ayanami, `$$レイ#233$$` is Ray Lovelock; `#pilot` vs
  `#robot` where a pilot and its machine share a name
* speaker names on line 1 are terms too -- `$$スズネ$$`, not `Suzune`
* ordinary words are NOT terms. If it is not in the brief's glossary table,
  write plain English.
* find the right token with
  `python tools/terms.py list analysis/glossary.json <japanese or english>`

## Known gap: a machine whose short name has no entry

`アクエリオンゲパルト` and `アクエリオンスパーダ` are glossary terms. The bare
`ゲパルト` / `スパーダ` that the dialogue actually uses are not, and the bare
form is the common one: 231 occurrences against 68 inside the compound, across
27 stages. So write them plain -- "Gepard", "Spada" -- matching the shipped
corpus, and do NOT invent a token for them; `$$ゲパルト$$` is a build error.

This is a gap to close at the project level, not per slice. Adding the bare
entries is safe (`tokenise_stage.py` takes the longest match, so the compounds
still win) but it means sweeping the literal instances already shipped, which
is one change with its own verification, not something a slice does.

## Ranks: `中佐` is always "Lt. Colonel", never "Colonel"

`大佐` is "Colonel" (96 shipped records) or, for a ship's captain, "Captain"
(15). So a bare "Colonel" for `中佐` names the wrong rank, and the two share
scenes -- Otto (`大佐`) refers to Daguza (`中佐`) in one line of stage 14.

Write "Lt. Colonel" for `中佐` everywhere: with the name (`ダグザ中佐` ->
"Lt. Colonel $$ダグザ$$") and bare, in address or reference (「同感ですよ、中佐」
-> "Agreed, Lt. Colonel."). Real English would address a lieutenant colonel as
"Colonel"; we do not, because it erases the distinction the script relies on.
Not "Lieutenant Colonel" and not "Lt. Col." -- one spelling, 17 records already
use it.

## Text

* a bare `「………」` is `「.........」` -- nine dots, always
* a thought line whose Japanese uses `（ ）` and no `「 」` keeps that shape:
  do not add `「 」`, and keep the brackets FULLWIDTH `（ ）`, not ASCII. They
  are drawable and the corpus uses them 1076 times against 164 ASCII, which
  have now been normalised. The brief's drawable-character list used to omit
  them, which is what caused the split
* location banners read `　\n　　\n　　　　　　～ Macross Quarter Hangar ～`
  (no comma between ship and room unless the Japanese separates them)
* `姐さん` addressed to Mao is "Boss"; `先生` for Suzune is "Miss Suzune"
  or "Miss"
* the shop AI ＡＧ speaks in NORMAL SENTENCE CASE, never all capitals
  (stage 1 is the only place caps were used and it is the odd one out)
* NEVER use an em dash or a double hyphen `--`. Use a comma, a full stop
  or `...`
* write `...` not `…`; use `'` and never `"`
* an unidentified speaker is ASCII `???`, NOT fullwidth `？？？`.
  Both encode and both fit, so this is consistency only: ASCII was the
  shipped majority (122 to 76), it is in the documented drawable set
  where fullwidth `？` is not, and it matches the ASCII preference the
  rules apply elsewhere (`...` not `…`, `'` not a double quote). All 198
  records now use ASCII

## Reuse before you invent

Any recurring name, unit, location caption or banner has almost certainly
shipped already. Grep `translation/stage*.json` for the Japanese string
before choosing a new rendering. The same goes for a character's register:
their library entry is quoted in your brief's cast section.

## What to report

Records examined vs records in the slice, the final `check_stage.py` line,
every term you had to choose a rendering for, and anything you could not
verify. Do not report a slice clean that you have not run the checker on.

## Known traps: a name that matches is not a term that fits

The Japanese matching is evidence, not proof. These have all bitten someone:

* **`ドロシー`** is two people. `$$ドロシー#240$$` is R. Dorothy Waynewright
  (The Big O -- Roger, Norman, Beck, Paradigm City); `$$ドロシー#86$$` is
  Dorothy Catalonia (Gundam Wing -- Relena, Treize, Romefeller). The cast
  section gets this wrong the same way it does レイ. `check_names.py` now
  checks it in both directions.
* **`レイ`** is two people. `$$レイ#333$$` is Rei Ayanami; `$$レイ#168$$` is
  Ray Lovelock (Macross 7). The brief's auto-generated cast section attaches
  the wrong bio here regularly, because it goes by portrait id -- EVERY
  `pid_RAY`/`pid_RAY_S` line gets Ray's Macross 7 bio, Rei's included. The
  portrait is NOT evidence. Read the surrounding records: 碇/綾波/使徒/ＥＶＡ
  means Rei, バサラ/ミレーヌ/ガムリン means Ray. A bare `「………」` carries no
  evidence of its own -- it hashes identically for both -- so resolve it from
  its neighbours, never from the cast section. `python tools/check_names.py`
  flags a token whose scene says the other character, and four shipped
  records had to be corrected because nobody ran that check earlier.
* **`ゼロ`** is Lelouch (`$$ゼロ$$`). Gundam Wing's **Wing Gundam Zero** is
  NOT that term. "Board Zero", "your Zero" spoken to Heero or by Duo is the
  machine: write plain `Zero`. A shipped line that got this wrong was
  corrected, so do not cite it as precedent.
* **`姫`** is the SRW-original keyword, the Firebug's Princess. Unicorn's
  `姫様` (Mineva) and Klan's `『姫』` are NOT it: write plain `Princess`.
* **`レディ`** is Lady Une. A generic `レディ` ("a pout doesn't suit a lady")
  is not.
* **`ボス`** is the Mazinger pilot. Mao's `姐さん` renders as "Boss" but is
  not that term: write plain `Boss`.
* **`安`**, **`ＡＧ`**, **`ＰＳ`**, **`ファ`**, **`ＵＮ`** ARE terms despite
  being one or two letters in English.

When a name matches but the term does not fit, write plain English. A literal
is honest; a wrong token is a rename waiting to corrupt a line.

## Working files

Many translators run at once and share one scratchpad directory. Two rules:

* **Never write a scratch file into the project tree.** Grep output, probe
  scripts and intermediate JSON go in the session scratchpad directory, not
  in `E:/Projects/SRW Z3/`. 46 stray `scratch_*.txt` and `out*.txt` files had
  to be swept out of the repository root in one run.
* **Give it a name unique to your slice** (`build_STG0033B_m3_0_120.py`),
  never a generic one like `build_answer.py`: two slices have already had a
  generic scratch file overwritten mid-run by another translator.

Your answer file path is already unique -- keep everything else beside it.

## First-instance renderings settled by this run

**Everything in this list is PLAIN ENGLISH, not a token**, unless it is
written with `$$`. A translator tokenised `ジェミニス` because the arrow
notation looked like a token mapping; the checker caught it. If you are not
sure, `python tools/terms.py list analysis/glossary.json <word>` is the
authority -- 0 matches means plain English.

A name with no glossary entry and no shipped precedent gets decided by
whichever slice reaches it first. These are settled -- reuse them rather than
re-deciding, and grep the corpus before adding to the list:

* `ソウセイの書` -> `'Book of Genesis'` (recurs in stages 41, 45, 83)
* `アクバルジン・バドバヤール` -> `Akbarjin Badbayar` (Jin's birth name)
* `ロンデニオン` -> `Londenion`;  `ルオ商会` -> `Luio & Co.`
* `天子様` -> `the Tianzi` (Code Geass R2's Chinese Federation Empress)
* `クェス・エア` -> `$$クェス$$ Air` -- she uses her mother's surname; the
  glossary's `クェス・パラヤ` is her father's and does NOT belong on that line
* `角割れ` -> `Split-Horn`;  `四枚羽` -> `four-winged`
* `パラオ` -> `Palau`;  `ア・バオア・クー` -> `A Baoa Qu`
* `サイコ・フレーム` -> `Psycoframe` (the project's existing spelling)
* `マリーメイア兵` -> `Mariemaia Soldier`;  `市民` -> `Citizen`
* `Zero System` is plain English, never `$$ゼロ$$ System`
* `ナナヒカリ` -> `Daddy's Boy`;  `エコヒイキ` -> `Teacher's Pet` (Asuka's
  taunts for Shinji and Rei)
* `愛・おぼえていますか` -> `Do You Remember Love` (the film's English title)
* `運命の赤い糸` -> `fate's red thread`;  `運命の環` -> `the ring of fate`
* a `『 』` title becomes `'...'` -- corner brackets are not drawable
* `第３新東京市` -> `Tokyo-3`;  `第２新東京市` -> `$$第２新東京市$$` ("Neo
  Tokyo-2"). These are DIFFERENT cities and one stage confused them
* `墓穴特訓` -> `the Grave Pit Drill` (Fudou names it on screen)
* `Ｇの誇り` -> `the pride of G`;  `墓地` -> `Graveyard`;  `アイアンシー` ->
  `Iron-C`;  `アルテア` -> `Altair` (never "Altea")
* `銀河の妖精` -> `the Galactic Fairy` (Sheryl -- her own library entry, not
  the keyword entry's "galaxy's fairy");  `超時空シンデレラ` -> `the Super
  Dimension Cinderella` (Ranka -- `超時空` is "Super Dimension" by Macross
  convention, as in Super Dimension Fortress Macross)
* `スズネ先生` -> `Miss $$スズネ$$`. NEVER `$$先生$$` -- that term is Sensei,
  a named Shin Mazinger pilot, an unrelated character. 10 shipped records had
  to be corrected
* `ドーリアン外務次官` -> `Vice Minister Darlian` (never "Dorian")
* `マリナ様` -> `Lady $$マリナ$$` (12-1 in shipped text; she is a princess and
  the corpus already says Lady for ミネバ and マリーメイア). `$n様` ->
  `Master $n`, gender-neutral, because `$n` is the player-named protagonist.
  AG says `Master X` to everyone regardless -- that is his own idiolect
* `ジェミニス` -> `Geminis` (never "Geminiss");  coordinates take the house
  form `N23-32, E161-22` -- the degree sign is not drawable
* `プトレマイオス２改` hangar banner -> `～ $$プトレマイオス２改$$ Hangar ～`;
  `ムッツリ５` -> `the Silent Five`;  `パラダイムシティ` -> `Paradigm City`;
  `パラダイム社` -> `Paradigm Corp.`;  `ライル／ニール・ディランディ` ->
  `Lyle / Neil Dylandy`;  `おキツネ博士` -> `Doctor Fox`
* `ジェミニス` -> `Geminis`;  `惑星ジェミナイ` -> `Geminai`;  `ジェミナイド` ->
  `Geminaid`;  `ウズミ・ナラ・アスハ` -> `Uzumi Nara Athha`;  `アスハ代表` ->
  `Representative Athha`;  `ミネルバ` -> `Minerva`;  `アークエンジェル` ->
  `Archangel`;  `アカツキ` -> `Akatsuki`;  `ソレスタルビーイング` ->
  `Celestial Being`;  `サバーニャ` -> `Zanbanya`
* `風呂んてぃあ` -> `Bathrontier` (the 風呂/Frontier pun, kept visible in
  English);  `アルテア人` -> `Altairan`;  `ガイコツ` -> `skeleton`;
  `アトランディア` -> `Atlandia`;  `ロンド・ベル` -> `Londo Bell`;
  `アイランド１` -> `Island 1`;  `補佐官` -> `Secretary`;  `私室` ->
  `'s Quarters` (vs `個室` -> `Private Room`)
* `無限拳` -> `Mugen Attack`, per `translation/weapons.json` -- an attack
  name is whatever the weapon list ships, never re-decided in dialogue
* `桂様` -> `Master $$桂$$` (16-1);  `お姉様` (Noriko's mentor) -> `Big Sis`
* `テスタロッサ大佐` -> `Captain Testarossa` (she commands the submarine and
  that is the official English; the corpus was split 7-6 and is now settled)
* `無機質な部屋` -> `A Featureless Room`;  `タロス` -> `TAROS`;
  `艦長室` -> `Captain's Cabin`;  `フライトハッチ` -> `Flight Hatch`;
  `オーブ連合首長国` -> `Union of Orb Emirates`;  `キミツ` -> `Sealed`
* `インベーダー` -> `$$インベーダー#keyword$$` always. The robot sense renders
  identically and only differs in which encyclopedia entry it links; the enemy
  is spoken of as a species, never as a named deployable unit
* `パラダイムシティ` -> `Paradigm City`;  `メガデウス` -> `Megadeus`;
  `ドミュナス` -> `Dominus`;  `ザ・ビッグ` -> `the Big`;  `ゴードンの畑` ->
  `Gordon's Farm`;  `ランド・トラビス` -> `Land Travis` (the library already
  ships it that way -- do not "correct" it to Rand without deciding first)
* `螺旋王` -> `Spiral King`;  `ゲッター線` -> `Getter rays`;  `真ゲッター`
  (bare) -> `Shin Getter`;  `クロノ` -> `Chrono`;  `時の牢獄` ->
  `the Prison of Time`;  `ゲッター空間` -> `Getter Space`
* `研究室` -> `Laboratory`;  `トゥアハー・デ・ダナン食堂` ->
  `$$トゥアハー・デ・ダナン$$ Mess Hall`;  `レディチャペル` -> `the Lady
  Chapel` (NOT the `$$レディ$$` token -- different referent)

## Open question: how `様` renders (do NOT re-decide it per slice)

Shipped text is split. `様` comes out as "Master X" 100+ times including for
women (`Master $$オードリー$$` x9, `Master $$カレン$$` x6, `Master $$Ｃ．Ｃ．$$`
x7) and as "Lady X"/"Miss X" elsewhere (`Lady $$ミネバ$$` x7, `Lady
$$マリーメイア$$` x4). Audrey and Mineva are the same character, so the corpus
currently calls one person both.

Until this is settled: **match whatever that specific character already has
in the shipped corpus** -- grep for their name before writing a title. Do not
switch a character's title, and do not introduce a gendered title for a
character who does not already have one; `様` itself is gender-neutral and the
brief forbids inferring gender.

## Open question: `総帥` has no English of its own

The rank words are otherwise settled -- `司令` is "Commander" (59:1) and
`総司令` is "Supreme Commander" (16:2), and the three outliers were fixed --
but `総帥` (Char/Frontal's Neo Zeon title) is split 13 "Commander" to 14
"Supreme Commander", so it collides with BOTH of the settled ranks and has no
dominant form of its own to fall back on.

One translator rendered it "the Sovereign", which is what the official Gundam
UC English localisation uses and would be collision-free. Adopting it means
renaming a title across ~27 shipped lines, so it is the user's call, not a
sweep. Until it is decided: **match whatever that specific line's neighbours
already use** and flag it, do not re-decide per slice.

## Placeholders

* `$c` is the player-named SQUAD (the ZEUTH/ZEXIS slot: 「$cとして行動を
  開始します」). A runtime placeholder exactly like `$n`: keep it, never
  translate it, and do not repeat it where the Japanese has it once.
  Four translators flagged it as undocumented before it was written down.
  `check_stage.py` verifies its count now, and found a shipped line that
  used it twice against one in the source.

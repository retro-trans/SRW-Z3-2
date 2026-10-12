# Dialogue translation style

For translators of Tengoku stage dialogue. Read `BASE_RULES.md` in full (the
dialogue section applies to you), then your brief in
`work/tengoku/dialogue_briefs/<slice>.md`. Names: search the glossary sheet
`work/tengoku/library_briefs/GLOSSARY.md` (token, English, status, gender).

## Output

Write `work/translation/en/dialogue/<slice>.json`, UTF-8, and nothing else:

```json
{
  "schema": 1,
  "slice": "dlg_2001_00",
  "rows": {
    "4:t_003:2": {"sha": "455328beab",
                  "en": "$$アルト$$\n「And that guy $$尸空#pilot$$ from earlier is here too.」"}
  },
  "names": {"<Japanese>": {"kind": "pilot", "en": "...", "evidence": "..."}},
  "report": {"rows_in_slice": 80, "rows_examined": 80, "left_untranslated": [],
             "kept_omissions": ["4:t_003:5: ..."], "uncertain": ["..."]}
}
```

- Row ids and `sha` are copied from the brief exactly.
- `en` is the **speaker line**, a newline, then the **speech on ONE line**.
  The builder wraps it to the dialogue box and indents continuation lines.
- The speaker line is copied from the brief. When the brief offers options
  (`X OR Y`), pick the one the pid and the scene settle.
- Rare records hold several separate 「...」 blocks (e.g. one per route branch):
  write one 「...」 per line, same count as the Japanese; each wraps on its own.
- Keep the speech's own brackets: 「...」 when the Japanese has them (almost
  always), nothing extra when it does not. Thoughts in （...） are written with
  ASCII parentheses `(...)`.
- **Captions** (speaker line is a fullwidth space, e.g. a location card
  centred with fullwidth spaces and ～): keep the Japanese line layout and
  spacing; translate only the words (`～ D-Trader ～`).
- Save the file after every ~20 rows; if it exists when you start, continue.
- Check your file: `python -m tools.dialogue check --file <slice>.json`
  (run from `E:\Projects\SRW Z3 2`). Fix every ERROR. `TOO LONG` means the
  speech needs more than 3 lines in the box: first write it in full, then
  compress or abbreviate, never drop the end of a sentence. If it still does not
  fit, leave it long and list it in `report.uncertain`.

## Text rules

1. ASCII only outside tokens, American spelling, straight quotes; `'` for
   quotes inside speech, `...` for ellipses, `-` for dashes. Keep 「」 and 《》.
   Source-only exception: retain U+0431 exactly where it appears in the original
   (five decorative uses in the corpus). Its game-font appearance is unverified;
   do not substitute a heart or remove it. The checker requires its source count.
2. **Control codes** stay, same count: `$n` is the protagonist's name (the
   player can rename him), `$l`, `$F`, `$f`, `$c` are game codes; keep each where
   the Japanese has it.
3. **Keyword links 《》**: the same number and order as the Japanese; they bind
   to the game's keyword list by position. Inside, write the term's token:
   `《$$時の牢獄$$》`. You may move a link within the sentence, never drop or add one.
4. **Names are tokens** (`$$token$$`, `$$token|lc$$`, suffixes outside), exactly
   as in the library; never literal English. A name not in the sheet:
   `$$<exact Japanese>$$` plus an entry in `names` with evidence.
5. **No honorifics** (-san, -kun, -sama...), as in the Jigoku release; keep
   titles and ranks ('Captain', 'Commander', 'Sis', 'Big Bro' where the
   relation matters). A nickname that includes -chan may keep it.

## Meaning (BASE_RULES, dialogue)

- Read the rows before and after before deciding who a line is aimed at; the
  reply two rows later usually settles it. Neighbouring slices are in the same
  folder.
- **Pro-drop is grammar**: where the scene settles who, English states the
  subject; check a verb survived. Keep ambiguity only where the scene genuinely
  does not settle it, and list each such row in `report.kept_omissions`.
- **Direction**: 頼む / よろしく is the speaker asking the listener. Name who is
  asking whom before choosing the form.
- **Gender**: he/she only when the glossary gender or the scene settles it;
  never from a name. Unknown people: gender-neutral.
- Write each line in full first. Match the speaker's voice (a hothead talks
  like one; a formal officer does not use slang), but do not add meaning.
- **Jigoku English**: when the brief shows Jigoku English for identical
  Japanese, keep it if it fits this scene (the two games must read the same),
  adapting only the speaker line and tokens to this glossary.
- Report `rows_examined` against `rows_in_slice` honestly; a row you cannot
  verify even with the neighbouring slices goes in `left_untranslated` with the
  reason. List every call you were unsure of in `uncertain`.

## Settled renderings (keep consistent across slices)

- スズネ先生 = "Miss $$スズネ$$" (Jigoku shipped English); Mari's 先生チャン = "Teach".
- ソースケ (katakana) uses the `$$宗介$$` token; 皇帝陛下 = "His Majesty the Emperor".
- Unnamed voice (speaker ？？？) = ASCII `???`.
- 皇国 alone = "the Empire"; the full 新地球皇国 uses its token.
- `$c` is the player-named squad; keep it where the Japanese has it.
- Surname or given-name-only forms have their own tokens (千鳥, カナメ, カナ,
  相良, 碇, 綾波, テレサ, テスタロッサ, 神楽坂, 西条, ベン, ウェーバー, 式波, 真希波, 葛城, 三条, 破嵐); search the sheet before
  proposing a new one.
- 先輩 is dropped like other honorifics (plain name, not "Senior X").
- ナースさん as a plain word = "Nurse"; Lambda Driver is the token `$$ラムダ・ドライバ$$`.
- Evangelion short forms are plain English matching the library's official
  names: 初号機/零号機/２号機 = Unit-01/Unit-00/Unit-02, ＥＶＡ/エヴァ = EVA,
  使徒 = Angel, ダミープラグ = Dummy Plug; Rei Ayanami = `$$レイ#pt394$$`;
  Mari's ワンコ君 = "Puppy"; 父さん (Shinji to Gendo) = "Father".
- Ranks (until the rank table is settled): 軍曹 = Sergeant, 中尉 = Lieutenant,
  曹長 = Master Sergeant (Mao), 司令 = Commander, 総司令 = Supreme Commander.
- モビルスーツ in running speech = plain "mobile suit(s)".
- Captions use tokens for names too (`～ $$Ｄトレーダー$$ ～`); 中佐 = Lieutenant
  Colonel, 艦長 = Captain; 嬢 = "Miss"; plural outside the token (`$$X$$s`).
- 【...】 (Ledo/Chamber cockpit voice) = ASCII `[...]`; Chamber's speaker line
  is `$$チェインバー#pilot$$`; 少尉 = Ensign; 同盟 alone = "the Alliance".
- Ledo's broken, accented speech while he learns the language (katakana mixed
  into hiragana, e.g. コう撃をカイ始すル) = hyphen-split English ("Be-gin
  at-tack."); no misspellings or random capitals.
- 大佐殿 / テスタロッサ大佐 (Tessa) = "Captain" (Jigoku: "Captain $$テッサ$$"); Jeffrey and Misato keep "Colonel".
- Gargantia: 船団長 = Fleet Commander; 女帝 = Empress; 海の女帝 = Empress of
  the Sea (Lukkage).
- 社長 = "President" (Watta, head of Takeo General Company).
- Diebuster: Nicola's 姫 for Lal'C = plain "Princess"; Nono's お姉さま =
  "Big Sis"; Nono refers to herself by name where the Japanese does.
- 宇宙怪獣: `$$宇宙怪獣$$` ("Space Monsters") where the plural fits; a single
  one is plain "space monster". Kappei's 姉ちゃん/兄ちゃん = "Sis X" / "Big Bro X".
- Bare クォーター / ダナン = `$$クォーター$$` ("Quarter") / `$$ダナン$$` ("Danaan");
  the full names keep their full tokens. Kappei: おっちゃん = "Uncle X".
- Turn A: アメリア = `$$アメリア$$` ("Ameria", user-selected canonical spelling), アメリア大陸 = "the $$アメリア$$ Continent".
- 月の女王 = "the Moon Queen" (Dianna).
- Aquarion EVOL: 翅無し = "Wingless", 翅犬 = "winged dog", 無限拳 = "Infinity Punch".
- ランカちゃん = "$$ランカ$$-chan" (Jigoku shipped English; affectionate nickname).
- Gurren Lagann: Simon's アニキ (Kamina) = "Bro"; street 兄さん/姐さん = "bro"/"sis".
- 皇帝宮 = "Imperial Palace"; 皇国の中枢 = "the heart of the Empire".
- Jindai student council: 会長閣下 = "Council President, sir"; 補佐官 = "Aide".
- 「………」 alone = "........." (nine dots, Jigoku); normalise six-dot rows in the mechanical pass.
- Macross 7: Exsedol 参謀 = "Chief of Staff", 記録参謀 = "records officer".
- シンカ = `$$シンカ$$` ("Shinka"), as 真化融合 = Shinka Fusion.
- Mileina's です tic is not rendered (plain English).
- Gavil's ～美 puns = "X-beauty" (生命美 = "life-beauty", 新生美 = "rebirth-beauty"); Sivil speaks halting English ("Sivil... like Basara's song!").
- 根源的災厄 = "fundamental calamity" (lowercase).
- 人類敵対種 = "species hostile to humanity"; 副長 = "XO".
- ムッツリ (the running joke about Hibiki) = "the quiet type"; ムッツリスケベ =
  "closet pervert"; 脱ムッツリ = "stop being the quiet type". 太陽炉 = "GN Drive".
- ＥＬＳ in speech = `$$ＥＬＳ#keyword$$`; bare クアンタ = `$$クアンタ$$` ("Qan[T]").
- Mari's 姫 for Asuka = "Princess"; ガキシンジ = "Brat $$シンジ$$".
- Asuka's コネメガネ for Mari = "Four-Eyes"; Mari's ニャ～ = "nya~".
- リリン = "Lilin" (Evangelion official English).
- 超時空物理学 = "super-dimensional physics" (Orguss); 貧乏くじ同盟 = "Short Straw Alliance".
- Bare ザンボット / ダイターン = `$$ザンボット$$` / `$$ダイターン$$` (no "3").
- Company titles: 社長 = "President", 専務 = "Executive Director", 常務 = "Managing Director".
- Zuul's 分身 = "avatar"; 魔獣王子 = "Demon Beast Prince". Preserve the user's canonical Zuul spelling.
- 暗黒の軍団 = "army of darkness".
- 真戦 = "the True War" (capitalised).
- エルーナ様 = "Lady $$エルーナ$$" (she insists on the title; the honorific is the point).
- `$n` is Hibiki (male): he/him is fine when the scene needs a pronoun. サロン = "salon".
- Hibiki's childhood with Megumi: her 母 (to young Hibiki) = "Mommy", his お母さん = "Mom", adult 母さん = "Mom". `$f` / `$F` are name codes; keep them in place, never replace with `$n`.
- 最後の一人 (the last of the twelve Sidereal) = "the last one".
- いがみ合う双子 is always the token `$$いがみ合う双子$$` ("Quarreling Twins"), never literal "feuding twins".
- D.O.M.E. the being (speaker, addressed, talked about) = `$$Ｄ．Ｏ．Ｍ．Ｅ．#pilot$$`; the facility and 《》 links = `$$Ｄ．Ｏ．Ｍ．Ｅ．#keyword$$`.
- 黒歴史 = `$$黒歴史$$` ("Black History"). Harry's ディアナ様 = "Her Majesty"; 女王サマ (mocking) = "the Queen".
- Bare ターンエー (spoken) = $$ターンエー$$ 'Turn A'.
- Route-choice teams (2230): 'the Japan Defense Force' / 'the $$ネオ・ジオン$$ containment force' / 'the $$アマルガム$$ pursuit force'.
- Bare トライダー = $$トライダー$$ ('Trider'); ガバール星 = $$ガバール星$$; シグマ = $$シグマ$$.
- 光の魔神 = "the Demon God of Light"; ハーデス様 = "Lord $$ハーデス$$"; 光子力 = "Photon Power"; 科学要塞研究所 = "Science Fortress Research Institute"; 女将 (Tsubasa) = "the proprietress".
- ゲッター炉 = "Getter Reactor"; ゲッタービーム = "Getter Beam"; 太虚 = "the Great Void".
- 断空剣 = "Dankuuken" (Jigoku weapon list); split shout "Dan-kuu-ken!!".
- Aoi's bare センパイ/先輩 with no name available = "Senpai" (address); センパイ達 = "my seniors".
- レインボーウェーブ = "Rainbow Wave".
- クロノ保守派 = "the $$クロノ$$ Conservatives"; 改革派 = "Reformists" (capitalised).
- FMP terms: ブラック・テクノロジー = "Black Technology"; マーティアル教団 = "the $$マーティアル$$ Church"; イオタ波/タウ波 plain English ("Iota wave", "Tau wave"); 時空震動 always its token.
- Kalinin's last word イキナサイ = romanized 'Ikinasai' (go/live ambiguity; Sousuke comments on it later).
- 感応波 = "psychic waves".
- 宇宙世紀憲章 = "$$宇宙世紀$$ Charter"; bare 箱 = "the Box"; Gael's 様 dropped (no "Master").
- Four-phrase refrain: 獣の血 / 水の交わり / 風の行き先 / 火の文明 = "blood of the beast / mingling of waters / destination of the wind / civilization of fire".
- Shinji's 逃げちゃ駄目だ = "I mustn't run away".
- 事象の制御 = "event control" / "control over events" (never "phenomenon control").
- 宇宙の心 = "the Heart of Space"; bare ウイングゼロ = $$ウイングゼロ$$ ("Wing Zero").
- 蠢く金属 = "the writhing metal".
- 銀河殴り込み艦隊 = "Galactic Raid Fleet"; 新バスターマシン３号 = "the new Buster Machine No. 3".
- Garadoublas (ガラダブラ) is male ("he"), although the glossary gender says unknown.
- 真シャインスパーク = "Shin Shine Spark".
- 存在しようとする力 / 消滅しようとする力 = "the force that seeks to exist" / "the force that seeks to vanish".
- 螺旋の男 = "Spiral Man".
- 使者 = "emissary/emissaries" (never "envoy"); 飢える破壊魔 = "ravenous destroyers".
- 大崩壊 = "great collapse" (lowercase); 虚無 = "the void" or "nothingness" by context (never "the Great Void", which is 太虚).
- 天柱 = token $$天柱$$ ("Heavenly Pillar").
- 縮退炉 = "degeneracy reactor".
- The Edel's sentence-final にゃ = light "nya~" (like Mari). Hope/despair choice: "There is still hope." / "There is only despair."
- True Disciples (真徒): their あの方(達) for the Angels = "the Exalted Ones" (provisional); their chant サルース = "Salus".
- True Disciples' アドヴェント様 = "Lord $$アドヴェント#pilot$$" (worship); White's = "Captain". 神の使い = "emissary of God".
- 機械化融合 = "machine fusion"; ドルイドシステム = plain "Druid System".
- 神を殺す力 / 神殺し = "god-killing power" / "god-killer"; 闘気 "fighting aura", 闘志 "fighting spirit"; 機械天使 plain "Mechanical Angel".
- 先駆者 = "forerunner" (Newtype / Innovator / Vildark lines).
- 太陽の使者 (Tetsujin) = "Messenger of the Sun" (series title; exception to 使者 = "emissary"). 鋼の勇者 = "Steel Hero" (singular prophecy) / "heroes of steel" (praise of the team).
- 無限力 = "infinite power" (lowercase, as used so far); 贄 = "offering(s)" (avoid clashing with Sacrifice).
- Rand/Mel's 親方 = "the Boss" (capitalized; Rand's missing mentor).
- Hibiki's 父さん / 母さん / 姉さん = "Dad" / "Mom" / "Sis".


### Endgame renderings (stages 57-final)

- 黒い太陽 = token `$$黒い太陽$$` (`#sol` variant where it is Sol's Black Sun, as earlier slices did)
- 黒き罪翼 = "black wings of sin"; 無限獄 = token `$$無限獄$$`; 天の獄 = "Heavenly Prison"; 業 = "karma"; 理 = "the natural order"; 因果地平 = "causal horizon"
- 天柱 = token `$$天柱$$`; 真化 = token `$$シンカ$$` (also as a noun: "attain $$シンカ$$"); 真化融合 = token `$$真化融合$$`; 天元突破 = "Tengen Toppa"
- 超グレン団 / ザ・ビッグ / メガデウス / ルクバト星系 = tokens; 翅犬 = "winged dog"; 神話の果て = "the end of myth"
- Rand's 親方 = "the Boss"; Hibiki's 父さん/母さん/姉さん = "Dad"/"Mom"/"Sis"
- 宿命 = "destiny", 運命 = "fate"; 因果 = "causality"; 因縁 = "tie(s)"; 先駆者 = "forerunner"; 同位体 = "isotope(s)"; 無限力 = "infinite power"; 贄 = "offering(s)"; 多元世界 = "multiverse"; 車輪銀河 = "Cartwheel Galaxy"
- 天罪 = "Heaven's sin"; 大崩壊 = "great collapse"; 虚無 = "the void"/"nothingness"; 存在しようとする力 / 消滅しようとする力 = "the force that seeks to exist" / "the force that seeks to vanish"; 太虚 = "the Great Void"
- 御使い = token `$$御使い$$` (plural `$$御使い$$s`); 使者 = "emissary/emissaries" (Tetsujin's 太陽の使者 = "Messenger of the Sun"); 神の使い = "emissary of God"; 至高神の使い = "emissary of the Supreme God"; しもべ = "servants"
- 神を殺す力 / 神殺し = "god-killing power" / "god-killer"; 邪神 = "evil god(s)"; 烙印 = token `$$烙印$$`
- 真徒 = token `$$真徒$$`; their あの方(達) = "the Exalted Ones"; their アドヴェント様 = "Lord $$アドヴェント#pilot$$"; chant サルース = "Salus"; White's アドヴェント様 = "Captain $$アドヴェント#pilot$$"
- 至高神ソル = token; bare 至高神 = "the Supreme God"; bare ソル = token `$$ソル$$`; 至高神Ｚ = token
- ネオ・ angels have tokens ("Neo Hamaliel" …); 貧乏くじ同盟 = "Short Straw Alliance"
- ドロシー: choose by the surrounding cast (Gundam Wing = `#pt101`, Big O = `#bigo`)
- Advent's speaker line: use what the brief gives (`$$聖アドヴェント$$` for Holy Advent in the finale, else `$$アドヴェント#pilot$$`); in speech use `$$アドヴェント#pilot$$`
- Translate idioms by meaning, not literally.
- The brief's pid is often offset by one row from the speaker line — follow the speaker line.
- 超次元世界 = "hyperdimensional world" (lowercase)
- 総帥 (Neo Zeon: Frontal, Char) = "leader" / "the Leader" as a title; 総司令 = "Supreme Commander".
- Takeru's 兄さん (Marg) = "Brother" (as address) / "my brother".
- Kurz's 姐さん (Mao) = "Sis".

# Stage order and routes (Tengoku-hen)

Script files are named by scene group (`2001` … `2106d`, `22x0` choice scenes,
`22x1`… their D-Trader variants). Story order comes from the published
flowchart (akurasu `Super_Robot_Wars/Z3.2/Flow_Chart` and SRW Wiki
全話一覧/第3次Z天獄篇, cross-checked 2026-09-30) matched to the files by cast,
locations and the choice texts found in the scripts.

**Route A** = the first option at every choice. `tools/dialogue.py` `PLAN`
lists the files in play order.

| Play order | Stage | File(s) | Route |
|---|---|---|---|
| 1-2 | Prologue 1-2 | 2001, 2002 | common |
| 3-5 | 1-3 | 2003a/b, 2004, 2005 | common |
| choice | Green / Blue Earth | 2200 + 2201 (Green D-Trader) / 2202 (Blue) | |
| 6-13 | 4-11 Green | 2006-2013 | 翠 (route A) |
| | 4-11 Blue | 2014-2025 (splits NA / Japan at 5-8) | 蒼 |
| 14 | 12 | 2026a/b (hangar choice inside 2026a) | common |
| 15-18 | 13-16 | 2027-2030 | common |
| choice | spacequake split | 2030 end + 2210 (choice) + 2211/2212/2213 (D-Trader) | |
| 19-22 | 17-20 MQ | 2031a/b, 2032, 2033, 2034a/b | Macross Quarter (route A) |
| | 17-20 Hive | 2035a/b-2038a/b | Dragon's Hive |
| 23-24 | 21-22 MQ+Hive | 2039, 2040a/b | |
| | 17-22 Rescue | 2041a/b/c-2046 | Sousuke rescue |
| 25-27 | 23-25 | 2047, 2048, 2049 | common (all rejoin at 23) |
| choice | continent / Left-Behind Sea | 2220 + 2221 (continent D-Trader) / 2222 | |
| 28-31 | 26-29 continent | 2050, 2051, 2052, 2053 | 大陸 (route A) |
| | 26-29 sea | 2054a/b, 2055, 2056, 2057 | 海 |
| 32-37 | 30-35 | 2058, 2059, 2060, 2061, 2062, 2063 | common |
| choice | Japan / Neo Zeon / Amalgam | 2230 (3-block choice) + 2231 (Japan D-Trader) / 2232 / 2233 | |
| 38-40 | 36-38 Japan | 2064, 2065, 2066 | 日本 (route A) |
| 41 | 39 受け継がれる牙 | 2067 | 日本 (route A) |
| 42 | 40 光と闇の向こうに | 2068a (stage), 2068b (Dragon's Hive briefing: Ra Cailum's Amalgam alert, lead-in to the rejoin) | 日本 (route A) |
| | 36-40 Neo Zeon: 宇宙の神 / 暗闇のリディ / ハマーンのためらい / 想いと力の向かう先 / 赤い彗星の未来 | 2069, 2070, 2071, 2072, 2073 | ネオ・ジオン牽制 |
| | 36-40 Amalgam: 世界への挑戦 / 神への誘い / 幻影 / 歪む因果 / 迫るクロス・オブ・ワールド | 2074, 2075, 2076, 2077, 2078 | アマルガム追跡 |
| 43 | 41 ずっと、スタンド・バイ・ミー | 2079 | common (all rejoin at 41) |
| 44 | 42 炎 | 2080 | common |
| choice | Shinji / Crowe / Char | 2240 (Sidereal scene + the choice in its map event) + 2241 (Shinji D-Trader) / 2242 / 2243 | |
| 45 | 43 閉じた世界 | 2081 | シンジ (route A) |
| | 43 永遠の聖王国 | 2082a, 2082b (Crowe-route after-scene) | クロウ |
| | 43 BEYOND THE DIMENSION | 2083 | シャア |
| 46-49 | 44 宿命を越えて, 45 虹の彼方に, 46 守るべき未来, 47 決戦の地へ | 2084, 2085, 2086, 2087 | common (all rejoin at 44) |
| 50 | 48 燃える地球 | 2088a, 2088b (D-Trader + ELS/STMC tag) | common |
| 51-53 | 49 宇宙に響く声, 50 星の向こうに, 51 運命への出航 | 2089, 2090, 2091 | common |
| choice | Shin Getter Dragon / Macross Quarter | 2250 (choice in its map event) + 2251 (Getter D-Trader) / 2252 | |
| 54-56 | 52 神に導かれし者, 53 歪んだ進化, 54 閃光！！次元の果て！ | 2092, 2093, 2094 | ゲッター / Invaders (route A) |
| | 52 崩壊へのスタンピード, 53 愛憎のラビリンス, 54 愛する翼 | 2095, 2096, 2097 | マクロス / Vajra |
| 57-58 | 55 死闘の銀河, 56 覚醒 | 2098, 2099 (hope / despair choice inside 2099) | common |
| 59 | 57 真化、その意味 | 2100a/b | 希望 (route A) |
| | 57 終焉の宇宙 | 2101a/b | 絶望 |
| 60-63 | 58 哀しき墓守, 59 邪神降臨, 60 永遠へ, 61 黒い太陽 | 2102, 2103, 2104, 2105 | common |
| 64 | 最終話 果てなき世界 | 2106a-d (2106d = ending) | common |

Later choices (from the scripts): 2220 central continent / Left-Behind Sea
(after 25), 2230-2233 Japan / Neo Zeon / Amalgam (after 35), 2240 Shinji /
Crowe / Char (after 42), 2250 Shin Getter Dragon / Macross Quarter (after 51),
2099 hope / despair (after 56). 2500 (ace pilot talks), 2600 (guidance
scenario), 2700 (next-episode previews) and 2902 (test map) are outside the
story.

Stages 39-61 (added 2026-09-30): titles and branch layout from the akurasu
flowchart (the 3-way split after 35 runs for five stages, 36-40, and rejoins
at 41; the 2240 split is one stage, 43; the 2250 split is 52-54; the 2099
split is 57). Files matched by content: 2067 Dancouga Nova 「受け継いだ…牙」,
2068a Takeru/Marg on light and dark + Angels (SR point), 2079 Laevatein /
Leonard finale (FMP's last novel title), 2080 STMC + Vajra (SR point), 2081 /
2082a / 2083 end with the protagonist asking whether Shinji's / Crowe's /
Char's wish caused the transfer, 2084 Ambriel, 2085 Neo Zeong + 虹, 2086
Geminia, 2092 and 2095 share the same opening (the two 52s), 2094 Invaders,
2097 Vajra, 2103 Zuul / Hades / Uchuu Maou (59 SR point). Within a route the
files run in numeric order. The D-Trader variants 2241-2243 (and 2251/2252)
are textually identical; 2241 / 2251 are taken as the route-A ones by the
same numbering as 2201/2211/2221/2231.

Correction (2026-09-30): play order past stage 29 was off by one (a
duplicate "32 | 29 continent | 2053" row); stages 30-35 are play 32-37 and
Japan 36-38 are play 38-40 (prologues add 2 to every stage number).

Sources: akurasu wiki `Super_Robot_Wars/Z3.2/Flow_Chart`
(https://www.akurasu.net/wiki/Super_Robot_Wars/Z3.2/Flow_Chart, rev. 34166,
stage titles JP/EN, choice texts, SR points); the choice texts in the scripts
(2240 「シンジの所へ向かう」…, 2250 「本隊を真ゲッタードラゴンの救援に回す」…,
2099 「希望は残っている」…).

Translated: batch 1 = play order 1-10 (2001-2010); batch 2 = stages 9-18 on
route A (2011-2013, 2026-2030, 2210/2211, 2031-2032); batch 3 = stages
19-28 (2033, 2034a/b, 2039, 2040a/b, 2047-2049, 2220/2221, 2050-2052); batch 4 = stages 29-38 (2053, 2058-2063,
2230/2231, 2064-2066). Batch 5 = stages 39-48: 2067, 2068a/b, 2079, 2080,
2240/2241, 2081, 2084-2087, 2088a/b (7,096 records, 95 slices). Batch 6 = stages 49-58: 2089-2091, 2250/2251, 2092-2094, 2098, 2099, 2100a/b, 2102 (6,828 records, 91 slices). Batch 7 = stages 59-61 and the final stage: 2103, 2104, 2105, 2106a-d (5,515 records, 70 slices). Route A is now translated end to end (39,381 records); other branches (Neo Zeon / Amalgam 36-40, the 2240/2241 and 2250/2251 alternatives, the despair branch 2101a/b) remain. Batch 8 = branches Blue Earth 4-11 (2202, 2014-2025, which itself splits North America / Japan) and Dragon's Hive 17-20 (2212/2213, 2035a/b-2038a/b): 7,116 records in 96 slices (+19 D-Trader rows filled by reuse). Remaining branches: Sousuke rescue 2041-2046, Left-Behind Sea 2054-2057 (+2222), Neo Zeon 2069-2073 and Amalgam 2074-2078 (+2232/2233), Crowe 2082a/b and Char 2083 (+2242/2243), Macross Quarter 2095-2097 (+2252), despair 2101a/b; plus 2500 ace talks and 2700 previews. Batch 9 = Sousuke rescue 2041a/b/c-2046 and Left-Behind Sea 2054a/b-2057: 5,535 records, 75 slices (+48 choice D-Trader rows 2222/2232/2233/2242/2243/2252 filled by reuse); total 52,080 records. Remaining: Neo Zeon 2069-2073, Amalgam 2074-2078, Crowe 2082a/b, Char 2083, Macross Quarter 2095-2097, despair 2101a/b; then 2500 ace talks and 2700 previews. Batch 10 = Neo Zeon 2069-2073 and Amalgam 2074-2078: 6,085 records, 80 slices; total 58,165 records. Batch 11 = Crowe 2082a/b, Char 2083, Macross Quarter 2095-2097, despair 2101a/b: 3,019 records, 43 slices; total 61,184 records — every story stage file is translated. Batch 12 = 2500 ace talks, 2600 guidance scenario, 2700 previews: 2,369 records, 31 slices. All stage dialogue is translated: 63,553 records. Only 2902 (test map, not player-facing) is left out.

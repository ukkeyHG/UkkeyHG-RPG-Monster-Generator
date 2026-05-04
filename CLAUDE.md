# CLAUDE.md

このファイルは Claude Code がこのリポジトリで作業する際のガイドです。

## プロジェクト概要

ComfyUI 用のカスタムノード `RPG Monster Generator`。
ユーザーが選択した「スタイル / 種族 / 属性 / ランク / シーン」から、ダークファンタジー RPG 向けのポジティブ／ネガティブプロンプトを合成し、CLIP エンコード結果と KSampler 推奨値（steps / cfg / sampler / scheduler）も併せて出力する。

ノード単体で完結するシンプルな構成（外部 DB やネットワーク呼び出しなし）。改造時はほぼ常に「データ追加・調整」か「合成ロジック変更」のどちらか。

## ファイル構成と役割

```
__init__.py                              # ノード登録のエントリポイント
rpg_monster_generator.py                 # ノード本体・スタイル定義・プロンプト合成ロジック
rpg_character_data/
  __init__.py
  rpg_monster_species_data.py            # 種族データ（28種）
  rpg_monster_element_data.py            # 属性データ（None含む8種）
  rpg_monster_rank_data.py               # ランク（6種、値が文字列のみ。Common/Elite/Boss/Legendary + Ancient/Mutated）
  rpg_scene_data.py                      # 背景シーン（6種）
README.md                                # ユーザー向け導入手順
REFERENCE_GUIDE.md                       # 各設定値の詳細解説（ユーザー向け）
```

> **Variant 廃止について（Plan B 統合）**
> 元々あった `rpg_monster_variant_data.py`（Normal/Enraged/Ancient/Mutated）は、Rank と概念が重複していたため廃止し、`Ancient` と `Mutated` を Rank に統合した。`Enraged` は種族プロンプト側のランダム pose に既に内包されていたため捨てた。

`STYLE_DATA` だけは `rpg_monster_generator.py` に直書き（Oil Painting / Cinematic Realistic / Anime Cel Shaded の3種）。スタイルの追加・変更時はここを編集する。

> 過去には `Pixel Art`（廃止）や `Ancient Sketch`（廃止）も存在したが、Element と概念衝突しやすい / 専用 LoRA 必須 / 使用頻度低 のため整理済み。

## データスキーマ

データファイルごとに辞書の値の形式が混在している:

- **辞書形式（カテゴリ付き）**: `{"category": "...", "prompt": "...", "negative_prompt": "..."}` … species
- **辞書形式（カテゴリなし）**: `{"prompt": "...", "negative_prompt": "..."}` … element / scene
- **文字列形式**: `"..."`（プロンプト文字列のみ） … rank の Common / Elite / Ancient / Mutated
- **カテゴリ別 dict**: `{"default": "...", "by_category": {...}}` … rank の Boss / Legendary

### Species カテゴリ（全 14 種）

各種族には `category` フィールドが必須。Boss / Legendary プロンプトはこのカテゴリ別に最適化されている:

| カテゴリ | 該当種族 | サイズ語 OK? |
| :--- | :--- | :--- |
| `humanoid_small` | Goblin / Kobold / Ghoul / Harpy | ❌ |
| `humanoid_large` | Skeleton / Orc / Ogre / Vampire / Demon / Lich / Flesh Golem / Medusa | ✅ |
| `quadruped_small` | Rat | ❌ |
| `quadruped_large` | Wolf / Cerberus | ✅ |
| `winged_mammal` | Bat | ❌ |
| `winged_reptilian` | Dragon / Manticore / Chimera | ✅ |
| `serpentine` | Hydra | ✅ |
| `arthropod` | Spider | ❌ |
| `amphibian` | Frog | ❌ |
| `amorphous` | Slime | ❌ |
| `incorporeal` | Ghost / Wraith | ❌ |
| `construct_stone` | Gargoyle | ❌ |
| `construct_object` | Mimic | ❌ |
| `tubular` | Giant Worm | ✅ |

### Species と Rank の責任分離（重要）

種族プロンプトと Rank プロンプトの**役割を明確に分離**することで、ランク間の進化が AI に伝わりやすくなる:

| 層 | 含めるべき要素 | 含めてはいけない要素 |
| :--- | :--- | :--- |
| **Species** | 解剖学（体型・部位・体表）、基本ポーズ、絶対不変のアイデンティティ | **装備バリアント（武器・防具・盾）** |
| **Rank** | 装備（武器・防具・盾・装飾）、威圧感、装飾レベル | 種族識別（"skeleton" などは入っていてOK） |
| **Element** | 体色・属性エフェクト | 装備や種族の上書き |
| **Scene** | 背景 | モンスター本体への干渉 |

**逆の例（やってはいけない）**:
種族プロンプトに `{rusted iron breastplate|completely bare bones|...}` のような装備バリアントを置くと、Rank が `no armor`（Common）や `heavy plate armor`（Boss）と指定しても**ランダムに鎧が抽選されて衝突**する。結果、Common と Elite の見た目が同じになる、Boss でも装備が貧弱、といった現象が起きる。

**正しい設計**:
種族は**剥き出しの骨格** / **裸のコウモリ** / **裸のスライム本体** だけを描写し、Rank が「Common = ほぼ素 / Elite = 部分鎧 / Boss = 重装鎧 / Legendary = 黄金聖鎧」のように装備を進化させる。これにより**ランクによる視覚的進化階段**が成立する。

Skeleton で実装済み。他の humanoid 系（Vampire / Lich / Demon 等）も同じパターンで進化階段を作ると見栄えが良くなる。

### 強調するとクロップされる現象（注意）

種族プロンプトで特定の体の部位（`rib cage` / `horns` / `wings` 等）を**多重に強調**すると、AI がその部位に視覚的見どころが集中していると判断し、**カメラがそこに寄ってクロップされる**（脚が切れる、頭が切れる等）。

**回避策**:
1. **全身ショット指定を強ウェイトで明示**: `(full body shot showing the entire creature from head to feet:1.4)` を先頭に置く
2. 強調部位を**分散**させる（頭・胴・脚にバランス良く要素を持たせる）
3. ビューバリアントに `full body` を含める: `{full body front view|full body three-quarter view|full body side profile}`
4. 接地ワード追加: `standing on the ground`, `feet visible at the bottom of the frame` 等
5. ネガティブに `cropped, knee-up shot, half body` を入れる手もある

Skeleton で実例: `rib cage` を 4 箇所で強調した結果、Boss では膝上クロップが頻発。`(full body shot ...:1.4)` を先頭に追加して解消。

### Boss / Legendary で起こりがちな腰上クロップ・正面化

豪華な装備（兜・肩甲・胸甲・大武器・盾・マント・後光・王冠等）が**画面上半分に集中**するため、AI のカメラが**胸より上**に寄って腰上クロップになりがち。Legendary は**左右対称な要素（王冠・後光・戦旗）**が多いため、**正面視点**ばかり選ばれがち。

**回避策**:
1. **`full body shot ... visible:1.6` まで重みを上げる**（1.5 では足りない時がある）
2. **`sabatons / boots on the feet:1.4` を脚にも追加**して、視覚的見どころを脚にも分散
3. **視点バリアントを Boss/Legendary でも変える**: `{dynamic three-quarter angle|side profile stance|action pose with one leg forward|low-angle view}`
4. **正面化対策**: `(NOT directly front facing the viewer, dynamic angled composition:1.3)` を別ウェイトで主張
5. **ネガティブ的に末尾追加**: `NOT a waist-up shot, NOT a bust shot, NOT a half body shot, NOT a directly frontal portrait, entire figure including legs and feet clearly visible at the bottom of the frame`

### CLIP トークンチャンク分布と framing 失敗の関係（重要）

CLIPTextEncode は ~75 トークンごとにチャンク分割し、**第 1 チャンクが最強の影響力**を持つ。プロンプト構成順は `Style → Species → Element → Rank → Scene` なので:
- Style(50) + Species(50-100) で第 1 チャンク埋まる
- Rank(200-400 トークン) は第 2 チャンク以降に押し出される
- Rank 内に書いた framing 指示（`full body shot:1.6` 等）も第 2 チャンク以降になり、影響力が弱まる

**Legendary が膝上クロップ・正面化しやすい本質的理由**:
- Legendary は装備・後光・王冠・banner で **400 トークン超**になりがち
- framing 指示が 4 〜 5 チャンク目に入ると、AI のカメラ位置決定にほぼ届かない

**確実な解決策**:
1. **framing 指示を Species プロンプトの先頭に置く**（CLIP 第 1 チャンクに入る）
   ```
   "(full body wide cinematic shot of the entire skeleton from skull to feet visible at all times, feet planted on the ground at the bottom of the frame:1.6), ..."
   ```
2. **Species の view variant から「frontal view」を削除** → 三クォーター・横・低アングルのみ
3. **Species の negative_prompt に framing 除外語を追加**（CLIP は negative も別途処理するため独立して効く）
   ```
   "..., waist-up shot, bust shot, knee-up shot, half body shot, cropped at the waist, head-only portrait, headshot, directly frontal mugshot, symmetrical centered front-facing portrait, feet not visible, legs cut off the frame"
   ```

**Rank プロンプト側に書く framing 指示はあくまで補強**として機能させる。本丸は Species（第 1 チャンク）と Negative。

### CLIP reverse-prompt effect（重要・反直感的）

**「描いてほしくないもの」を執拗に書くと、AI はそれを意識して逆に描いてしまう**現象がある。これは CLIP の attention 機構の特性で、Positive/Negative 関係なく**言及した概念が活性化**される。

**典型的な失敗例（Dragon の 5 本足）**:
- 5 本足を防ごうとして positive に `(exactly four legs total, no fifth leg, no middle leg:1.7)` と書いた
- negative に `five legs, six legs, extra legs, fifth leg, third front leg, middle leg, leg growing from the chest, hexapod, octopod, supernumerary legs, ...` と 30 ワード並べた
- 結果: **5 本足発生率が 50% 超まで悪化** — 「leg / legs」を連呼したことで AI が脚要素を過剰に重要視した

**正しい対処**:
- 脚カウントには言及しない（positive にも negative にも書かない）
- 種族識別 (`a massive winged classic western dragon, body shaped like a lion or tiger`) だけで AI に四足獣を理解させる
- 脚以外の問題（二足立ち、wyvern 化、正面化、クロップ）は引き続き negative で対処（これらは leg-count とは別概念なので reverse-prompt effect が起きにくい）

**判断基準**:
- ✅ Negative に書いて効くもの: 完全に別カテゴリの概念（`bipedal stance` `wyvern` `humanoid` `headshot` 等）
- ❌ Negative に書くと逆効果: 描いてほしいものと**同じカテゴリの概念の数違い**（`five legs` は `four legs` と同じ脚カテゴリ → 脚要素を活性化）

### 意図しない属性カラー誘発ワード（要注意リスト）

特定のワードは AI の学習データで強い属性連想を持っており、「**None 属性**」のはずなのに勝手に Fire/Poison/Light 等の色合いを発動させる。Boss/Legendary/Mutated のような長文 override で**気付かずに大量採用**してしまうので要注意。

#### 🔥 Fire / 赤を呼ぶワード（None 属性が炎化する）

| ワード | 連想 | 安全な代替 |
| :--- | :--- | :--- |
| `infernal` | hellfire（特に強力） | `dark divine` `shadow` `abyssal` `dread` |
| `blazing` | 燃え盛る炎 | `shimmering` `radiating` `glowing` |
| `burning` | 燃焼 | `filled with` `shining` `glowing` |
| `embers` | 火の粉 → 赤い床散乱 | `dust` `stone debris` |
| `red eyes` | 赤色が体外に漏出 | `amber eyes` `glowing eyes` |
| `crimson aura` | 赤いオーラ | `dark aura` `menacing haze` |
| `wounds` (生傷) | 出血イメージ → 赤い床 | `healed scar lines` `old scars` |

実例: Cerberus Legendary で `infernal` を 5 回使ったら全身炎化。`divine` `dark` に置換で解決。

#### 🟢 Poison / 緑紫を呼ぶワード（None 属性が毒化する）

| ワード | 連想 | 安全な代替 |
| :--- | :--- | :--- |
| `toxic` | 直接「毒」 | `unnatural` |
| `sickly` | 病的＝緑紫 | `wrong` `eerie` |
| `necrotic` | 壊死＝緑紫 | `eldritch` `wrong` |
| `putrid` | 腐敗＝緑 | `raw exposed` |
| `rotted` | 腐る | `torn` `damaged` |
| `corrupted` | 腐敗（多用注意） | `warped` `twisted` |
| `ichor` `slime` | 毒液 | `dark fluid` |
| `green or purple eyes` | 直接 緑紫 色指定 | `milky pale + burning unnatural light`（mismatched 表現） |

実例: Cerberus Mutated に上記ワード多数 → None なのに緑紫の体色になった。`wrong eldritch` 系に置換で解決。

#### 👤 二足化を誘発するワード（四足獣が立ち上がる）

| ワード | 連想 | 安全な代替 |
| :--- | :--- | :--- |
| `king` `lord` `overlord` | 人型君主 | `alpha` `predator` |
| `royal` `regal` `throne` | 人型王族 | （avoid） |
| `crown` (of fur) | 直立姿勢の連想 | `mane` `shaggy mane spreading wide` |
| `iron-spiked collar` `armor` `cape` | 二足キャラ装備 | （avoid for quadrupeds） |
| `bone trophies dangling` | ぶら下がる＝直立 | （avoid） |
| `towering` | 縦の威厳 | `oversized` `massive scale` `body lowered close to ground` |
| `standing tall` `proud upright` | 直立 | `low predator stance` `horizontal body` |

実例: Wolf Boss で `dire wolf overlord, crown of fur, iron-spiked collar` で二足化。`dire wolf alpha predator, shaggy mane spreading wide, healed scar lines` に置換で解決。

#### 🦵 5 本足を誘発するワード

| ワード | 連想 | 安全な代替 |
| :--- | :--- | :--- |
| `legs` (positive 内のあらゆる言及) | 脚要素を CLIP attention で活性化 | 部位指定を避ける |
| `paws` `claws on the ground` | 上記同様 | 「horizontal stance like a stalking lion」など姿勢の比喩 |
| `bands on the legs` (装飾) | Legendary でよく入れがち | `golden plating across the chest` `bands along the spinal ridge` |
| `four legs` `four paws` `exactly four` | 数値カウント | 種族識別だけで足数は AI に任せる |

実例: Wolf/Cerberus Legendary で `golden bands on the legs` → 5 本足発生率上昇。`golden plating across the chest` に置換で解決。

#### 設計原則: 同じ語でも weight 1.5+ でリスク激増

弱重みなら影響軽微でも、`(:1.5)` `(:1.6)` のような強重みブロックに含めると CLIP attention を強く支配する。**長い override を書く時は危険ワードのスキャンを必ず実施**。

### 多頭/多体生物の SDXL 限界（重要）

3 頭以上の多頭生物（Cerberus / Hydra / Chimera 等）は SDXL の弱点:
- 学習データに「3 匹の動物が並んでる」画像の方が圧倒的に多い
- 「three heads」と書くと**「3 匹の動物」と解釈**される傾向
- 「one body, three heads」をいくら強調しても安定しない

**戦略的選択**:
1. **単頭化（戦略的撤退）** — 多頭性を諦め、単頭の強い個体として描画（Cerberus 採用）
2. **ControlNet で骨格テンプレ強制** — 参考画像必須で手間
3. **専用 LoRA** — 別途学習が必要で手間

ファンタジー RPG では多くの作品が単頭ヘルハウンド系として描いてる前例があるので、**単頭化は妥当な選択**。「Cerberus」「Hydra」の名前は使うが描画は単頭化する。

将来の Hydra / Chimera も同じ判断を検討すべき。

### ControlNet 参照画像と体型のミスマッチ（重要）

ControlNet 使用時の参照画像は **体型カテゴリで選び分ける**必要がある。Scene 別ではなく**体型別**が正解:

| 体型 | 該当カテゴリ | 推奨参照画像タイプ |
| :--- | :--- | :--- |
| 縦長ヒューマノイド | `humanoid_small` / `humanoid_large` / `incorporeal` | 縦コリドー型 OK / フラット壁 OK |
| 水平四足獣 | `quadruped_small` / `quadruped_large` / `winged_reptilian` / `serpentine` / `tubular` | **フラット壁必須**（縦コリドーは NG） |
| 翼付き哺乳類・節足・両生・不定形 | `winged_mammal` / `arthropod` / `amphibian` / `amorphous` / `construct_*` | フラット壁推奨 |

**典型的な失敗ケース**: Dragon × 縦コリドー型参照
- ControlNet が「縦長空間」を強制 → 水平に長い 4 足ドラゴンが空間に収まらない
- AI の妥協策として **後ろ脚だけで立ち上がる二足ポーズ**で縦に詰める
- 結果: T-Rex 風 / Dragonborn 風 / 翼を腕のように上げる立ちポーズ

**フラット壁（`dungeon_ref_04.png` 系）なら**:
- ControlNet が深度・縦長制約を出さない
- AI が自由なサイズ・姿勢で被写体を描ける
- 4 足獣はちゃんと低い水平プロウル姿勢になる

### Rank プロンプトの解決ロジック（4 段階優先）

`generate_prompt` 内で `resolve_rank_prompt()` が呼ばれ、以下の順で解決:

1. **種族固有 `rank_overrides[rank]`**（最優先・脱出ハッチ）
2. Rank データの `by_category[species.category]`
3. Rank データの `default`
4. プレーン文字列はそのまま

これにより、例えば **Bat × Boss** は `winged_mammal` 用の「翼開長を強調する Boss プロンプト」を選び、**Dragon × Boss** は `winged_reptilian` 用の「colossal towering scale」プロンプトを選ぶ。

### `rank_overrides` を使うべきケース

カテゴリ共通プロンプトと種族の主張がコンフリクトしている場合に、種族側で個別 Rank プロンプトを定義する:

```python
"Skeleton": {
    "category": "humanoid_large",
    "prompt": "...(骨むき出しを強く主張)...",
    "rank_overrides": {
        "Boss": "...(骨格系 Boss = 巨大な骨王、骨の王冠)...",
        "Legendary": "...(骨格系 Legendary = 黄金紋様の骨ソブリン)..."
    }
}
```

**典型的な該当ケース**:
- `humanoid_large` カテゴリの Boss プロンプトは "regal ornate armor" を含むが、Skeleton (骨むき出し) / Lich (ローブ) / Flesh Golem (継ぎ接ぎ肉体) では鎧記述が衝突する
- `winged_reptilian` の Boss は "colossal scaled beast" だが、Manticore (ライオン体) では scaled が変
- 種族の独自性が category 共通記述と矛盾する場合

すべての種族に override を書く必要はない。**コンフリクトが視覚的に出てから個別対応**で十分。

合成ロジック (`generate_prompt`) は `isinstance(entry, dict)` で両方を吸収しているので、新規エントリ追加時はどちらの形式でも動く。ただし**そのファイル内で形式を統一する**こと。

### プロンプト中のバリアント記法

`{a|b|c}` 形式を `resolve_prompt_variants_with_trace` がランダム選択する。Python の標準 random を使用（seed 固定なし）。ネスト不可（パターンは `[^{}]+`）。

例: `"{front view|three-quarter view|side profile}"` → どれか1つに置換。

> **キャッシュ無効化（IS_CHANGED）**: `RPGMonsterGenerator.IS_CHANGED` が毎回 `random.random()` を返すように設定されているため、Queue Prompt のたびにノードが再実行され、バリアントが毎回新しく抽選される。これにより同じ入力（Style/Species/Element/Rank/Scene）でも、Queue ごとに **武器・ポーズ・装備が変わる** ガチャ的挙動になる。
> 
> もし「同じ入力なら同じ結果」にしたい場合は、`IS_CHANGED` を削除するか定数を返すようにすればキャッシュが効くようになる。

## プロンプト合成順序（重要）

`generate_prompt` での連結順は意図的に決まっている：

1. **スタイル**（先頭・絶対優先）— 画風キーワードは強い側に置く
2. 種族（本体）
3. 属性（装飾）
4. ランク（威圧感・装飾レベル・個性）
5. シーン（背景）

ポジティブは `"{style_positive} {content_prompt}"`（スタイルとコンテンツの間はスペース、コンテンツ内はカンマ）。ネガティブは全部カンマ連結で、共通ネガティブ（frame / text / watermark など）が先頭に固定で入る。

`steps` / `cfg` はスタイル既定値に `steps_offset` / `cfg_offset` を加算。`sampler_name` / `scheduler` はスタイル既定値そのまま（オフセット非対応）。

## ComfyUI との連携で注意すべき点

- **CLIP エンコード**は ComfyUI の `nodes.CLIPTextEncode` を直接 import して使用。ノード内部で `encoder.encode(clip, text)[0]` の戻り値を CONDITIONING として返す。
- **sampler_name / scheduler の型**は `nodes.KSampler.INPUT_TYPES()` から動的に取得して `RETURN_TYPES` に流用している。これにより KSampler 側が更新されても型ミスマッチを起こさない。import 失敗時のハードコードフォールバックあり。
- ノード登録名は `RPG-Monster-Generator`、表示名は `RPG Monster Generator`、カテゴリは `RPG`。

## 改造時のチェックリスト

### 種族／属性／シーンを追加する
1. 該当データファイルの辞書に新規キーを追加（`prompt` / `negative_prompt`）。
2. `prompt` には `{a|b|c}` バリアントを2〜3個以上入れて画一化を避ける。
3. `negative_prompt` には他の種族・属性に化けるのを防ぐワード（例: 種族なら `humanoid, person, static pose` など）を入れる。
4. 既存エントリの命名規則・粒度に揃える。データ追加時は `REFERENCE_GUIDE.md` の対応表も更新する。

### ランクを追加する
- 値は**文字列のみ**（辞書形式にしない方針で運用中）。
- 追加先は `rpg_character_data/rpg_monster_rank_data.py`。
- 「強さ・希少度」軸と「特殊個性」軸（Ancient/Mutated 系）を混ぜているので、命名は方向性が一目で分かるものに。

### スタイルを追加する
- `rpg_monster_generator.py` の `STYLE_DATA` に1エントリ追加。`positive` / `negative` / `steps` / `cfg` / `sampler_name` / `scheduler` の6キーを必ず埋める。
- `sampler_name` は ComfyUI 側で実在するものを指定（フォールバックリストや KSampler の入力候補を参照）。

### 出力ピンを増やす／変える
- `RETURN_TYPES` と `RETURN_NAMES` の順序・要素数を必ず一致させる。
- `generate_prompt` の戻り値タプルも同じ順序で更新する。

### 共通ネガティブを変える
- `generate_prompt` 内 `resolved_negatives` の初期リストを編集。
- **意図的に外している語**（再追加すると層を跨いで打ち消し合いが起きる）:
  - `woman` … 性別は種族側で制御
  - `photo` … Cinematic Realistic スタイルの `RAW photo, hyperrealistic` を殺さないため。代わりに非写実スタイル（Oil Painting / Anime Cel Shaded）の各 negative 側で `photo` を持たせている
  - `pedestal, platform, table, desk, display stand` … Gargoyle `perched on a gothic pedestal` や Vampire `seated on a gothic throne` を殺さないため。台座に乗ってはいけない種族（Slime 等）の `negative_prompt` 側で個別に抑制する方針

### 属性プロンプトを書くときの注意（最重要）

**ポジティブ側は 3 層のウェイト構成**で書く:

```
(:1.5) 体色の塗り替え     ← 例: "(crimson red and burning orange colored creature:1.5)"
(:1.4) 体全体の染色詳細   ← 例: "(entire body and fur deeply tinted in fiery red:1.4)"
(:1.3) 体表エフェクト     ← 例: "(creature's body engulfed in flames:1.3)"
(:1.0) 補助記述           ← グロー・霧・粒子など
```

なぜ 3 層必要か:
- 体表エフェクトだけ書くと、AI が「炎を体の周りに置く」だけで**体色は種族デフォルト**（コウモリ=茶色、狼=灰色）のまま残してしまう
- 体色塗り替えを最強ウェイトで先頭に置くことで、種族の学習バイアスを上書きできる

**やってはいけないこと**:
- ❌ `surroundings filled with intense heat` / `surrounded by storm clouds` などの**環境記述**
  - AI が属性を背景に逃がして「炎の上を飛ぶコウモリ」になる
- ❌ 種族の体表に依存する語（`hide` / `scales` 固有）
  - Bat の毛皮、Slime の半透明など分岐があるので、`body` / `skin` / `fur` の汎用語で書く
- ❌ 汎用的な色名/材質名をネガティブに入れる（`red, blue, green, light, flesh, translucent` 等）
  - シーン/種族のポジティブを巻き添えで殺す（例: Metal の `green` がゴブリンの緑肌を消す、Fire の `blue` が Ice Vault の青氷壁を消す）

**ネガティブの正しい書き方**: 「**対義属性のエフェクトがモンスター本体に乗ったらおかしいもの**」を narrow に列挙する（例: Fire なら `icicles, frost coating, snow on creature, natural brown fur`）。

### Scene プロンプトを書くときの注意

Scene はプロンプト末尾に置かれるため、重みなしでは Species/Element/Rank に必ず負ける。**3 層ウェイト構造**を必須:

```
(:1.4) 背景の本質宣言       ← "set in a ... background"
(:1.3) 視覚要素を背景固定   ← "in the background" を明示してモンスター本体に乗らないように
(:1.0) 補助記述             ← 雰囲気・小道具
```

**ネガティブには「他シーンへの汚染防止」を明示**:
- Dungeon の場合、Fire 属性の Bat を出したときに AI が `Lava Cave` 化させないよう、`lava, magma, volcanic cavern, natural cave` を明示的に拒否
- 同様に Ice Vault は `lava, fire, magma` を、Throne Room は `natural cave, lava, dungeon prison bars` を拒否

### 属性のシーン汚染とその対策（重要）

属性プロンプトを `(:1.5)` 強重みで **本体バインド**しても、AI は学習バイアスから**属性を背景にも適用**しがち。具体例:
- Skeleton × Ice × Dungeon → 屋外の雪村風景が出てしまう（Ice の "frost" "icicles" "frozen" が「冬の屋外」を呼ぶ）
- Bat × Fire × Dungeon → 床に焚火・溶岩風景が出る（過去対応済み）
- Wolf × Lightning × Dungeon → 雷雲・嵐の屋外が出る可能性

**前提（重要）**:
SDXL モデルの学習バイアスにより、属性 Element が「**Element Domain 効果**」として周囲環境に汚染することは**完全には抑制できない**。
- プロンプト + ControlNet で 80〜85% の seed では問題ない結果が出る
- 残り 15〜20% で床に氷塊・焚火・電光が残る → これは**仕様**として REFERENCE_GUIDE.md にも記載
- 完全クリーンな背景が必要な場合は **Inpainting workflow** または **2-pass composite** が必要（プロンプト工夫の限界）

**対策（4 段階）**:
1. **Element の negative に屋外シーン汚染ワードを追加**:
   - Fire neg: `outdoor volcanic landscape, lava field background, scene replaced by lava environment`
   - Ice neg: `outdoor snowy landscape, snowy village houses, scene replaced by snowy environment`
   - Lightning neg: `outdoor stormy sky, outdoor thunderstorm landscape, scene replaced by stormy environment`
   - Light neg: `outdoor heavenly cloud landscape, scene replaced by celestial heaven`
   - Dark neg: `outdoor void abyss landscape, scene replaced by void environment`
   - Poison neg: `outdoor toxic swamp, poison forest landscape`
   - Metal neg: `industrial factory background, sci-fi metal environment`
2. **Scene のウェイトを `(:1.4)` → `(:1.5)` に底上げ**して Element と互角に競合させる
3. **Scene の prompt に `indoor` を明示**（Dungeon / Ice Vault / Graveyard / Throne Room は屋内系なので）
4. **Scene の negative に屋外気象キーワードを追加**: `snow on the ground, blizzard, outdoor stormy weather, outdoor lightning, falling snow outdoors, sunny outdoor day, trees, grass, mountains in the background`

### 床への element 汚染（更に subtle な汚染パターン）

属性のシーン汚染を屋外まで防いだ後、**床への element 散乱**という二次汚染が発生しやすい:
- Skeleton × Ice × Dungeon → 床に氷柱・氷の結晶が散らばる
- Bat × Fire × Dungeon → 床に焚火・燃え滓
- Wolf × Lightning × Dungeon → 床にスパーク・電光跡

行き場を失った element エフェクトが**床に逃げる**現象。Element の `(:1.5)` ウェイトが強すぎて、本体に乗りきらない分が床に出てしまう。

**対策**:
1. **Element の prompt の曖昧な表現を「体限定」に書き換え**:
   - ❌ `ice crystals encrusting every part of the body` → 「散らばる結晶」と読まれやすい
   - ✅ `ice crystals growing only on the body, icicles attached only to the creature's limbs`
   - ❌ `embers radiating from the creature's flesh` → 「散る粒子」と読まれやすい
   - ✅ `embers emitting directly from the creature's flesh only`
   - 各表現に `only` `tightly` `directly` を加えて散逸を防ぐ
2. **Element の negative に床/地面散乱を追加**:
   - Fire neg: `embers scattered on the floor, lava puddles on the ground, fire pits on the floor, flames coming from the ground`
   - Ice neg: `ice crystals on the ground, ice spikes growing from the floor, icicles on the dungeon floor, frost patches on the floor`
   - Lightning neg: `sparks on the floor, lightning bolts on the ground, electrical arcs on the floor`
   - Dark neg: `shadow puddles on the floor, void cracks on the floor`
   - Light neg: `light spots on the floor, glowing patches on the ground`
   - Poison neg: `poison puddles on the ground, toxic spills on the floor`
   - Metal neg: `metal shards on the floor, metallic scraps on the ground`
3. **Scene の negative にも element 床散乱拒否を追加**（特に Dungeon）:
   - `embers on the dungeon floor, ice crystals on the dungeon floor, ice spikes growing from the stone floor, sparks on the floor, plants growing on the floor, glowing patches on the floor, decorative element effects scattered on the dungeon floor`
4. **Scene の prompt に `clean dry indoor stone floor with no element decorations on the floor` を追加**して床の状態を明示

### Rank プロンプトを書くときの注意

属性・シーンと同じ 3 層ウェイト構造を採用:

```
(:1.4) ランクの本質宣言   ← "legendary mythical creature with divine majesty" 等
(:1.3) 視覚フレーバー       ← 後光・粒子・紋様等の具体描写
(:1.0) 補助記述             ← 補強
```

**サイズ語（`colossal` / `massive scale`）は避ける** — 小型種族（Bat / Slime / Spider 等）と衝突するため。代わりに「装飾・後光・粒子・紋様」のサイズ非依存な要素で威厳を表現する。

## Git 運用

- ブランチは `main` 単一運用。直近のコミットを見ると、種族プロンプトの細かい調整（武器配分、ポーズ多様化、スタイル互換）が積み重なる形で進んでいる。
- 改造後は `git status` / `git diff` で意図しない範囲（特に `__pycache__/`）が混ざっていないか確認する。`.gitignore` で除外済みだが念のため。

## 開発環境

- **OS**: Windows 11
- **Shell**: PowerShell 7 (pwsh) ※ユーザーのデフォルト
- **ComfyUI**: `C:\Project\ComfyUI\` 配下にインストール済み
- **このカスタムノード**: `C:\Project\ComfyUI\custom_nodes\RPG-Monster-Generator\`

### ★ 基準モデル（プロンプト最適化の前提）

本ノードのプロンプトとパラメータ既定値は下記モデルでチューニング・検証されている:

- **DreamShaper XL Lightning DPM++ SDE** (`dreamshaperXL_lightningDPMSDE.safetensors`)
- ファミリー: SDXL Lightning 系（少ステップ高品質）
- **`STYLE_DATA` の既定値が Lightning 前提**で固定されている:
  - Oil Painting: 8 steps / 2.0 cfg / dpmpp_sde / karras
  - Cinematic Realistic: 8 steps / 1.8 cfg / dpmpp_sde / karras
  - Anime Cel Shaded: 8 steps / 2.5 cfg / dpmpp_sde / karras
- 標準 SDXL モデルを使う場合は `steps_offset` / `cfg_offset` で +20〜+27 / +4〜+6 を加算

**プロンプト改造時の注意**:
- 重み構文 `(text:1.5)` を多用しているため、ウェイトを正しく解釈する SDXL ベースモデル前提
- `{a|b|c}` variant 構文も同様に SDXL 系で動作確認済み
- FLUX / SD3.5 / Pony 系では構文・解釈が違うため動作未保証
- プロンプト変更時は基準モデルで再テストし、Tier 1 で挙動確認してから commit する

### コマンド実行時の使い分け

| 用途 | 推奨ツール | 理由 |
| :--- | :--- | :--- |
| ファイル一覧・git・gh・python など普通のコマンド | **PowerShell tool** | PowerShell 7 はパイプ・`&&`/`\|\|` チェーン演算子・三項演算子に対応。ネイティブで動く |
| POSIX 専用構文が必要な時 (`{a,b,c}` 展開、複雑な `awk`/`sed` パイプ等) | **Bash tool** | Git Bash 経由で動作 |
| ファイル検索・grep | **Glob / Grep ツール** | 専用ツールが最適化されている |
| ファイル読み書き | **Read / Write / Edit ツール** | 専用ツールを使う |

### PowerShell 7 で気をつける構文

- `null` の参照は `$null`（`/dev/null` ではない）
- 環境変数は `$env:VAR`（`$VAR` でも `%VAR%` でもない）
- 行継続はバッククォート `` ` ``（`\` ではない）
- ファイル削除は `Remove-Item`（`rm` はエイリアス、`-Recurse -Force` が必要なケースあり）
- 単一引用符ヒアストリング: `@'...'@`、ダブルなら `@"..."@`

### このプロジェクト特有のコマンド例

```powershell
# ComfyUI 再起動（コード変更を反映するため必須）
# - Windows Terminal 上の ComfyUI を Ctrl+C で止めて再起動
# - もしくは ComfyUI Manager の "Restart" ボタン

# キャッシュ削除（プロンプト変更が反映されない時）
Remove-Item rpg_character_data\__pycache__\*.pyc -Force

# 全カテゴリの存在を検証
python -c "from rpg_character_data.rpg_monster_species_data import MONSTER_SPECIES_DATA; print(set(v['category'] for v in MONSTER_SPECIES_DATA.values()))"
```

## 動作確認

ComfyUI 内でノードとして動かすしか確認手段がない（単体テストなし）。Python としては `from nodes import CLIPTextEncode` が ComfyUI ランタイム前提なので、リポジトリ単体で `python rpg_monster_generator.py` してもエラーになる点に注意。

改造後は ComfyUI を**再起動**しないと変更が反映されない（custom_nodes は起動時 import）。

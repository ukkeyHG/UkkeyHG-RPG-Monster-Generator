# RPG Monster Generator 設定リファレンス

このガイドでは、`RPG Monster Generator` ノードで選択可能な各項目の意味と、生成される画像への影響について解説します。

---

## 1. Style (画風・技法)
画像全体の描き方を決定します。

| スタイル名 | 概要 | 推奨設定 (自動出力) |
| :--- | :--- | :--- |
| **Oil Painting** | 重厚な油彩画 | Steps: 8, CFG: 2.0, Sampler: dpmpp_sde, Scheduler: karras |
| **Cinematic Realistic** | 写実的なリアル | Steps: 8, CFG: 1.8, Sampler: dpmpp_sde, Scheduler: karras |
| **Anime Cel Shaded** | アニメ風（セル画） | Steps: 8, CFG: 2.5, Sampler: dpmpp_sde, Scheduler: karras |

> [!IMPORTANT]
> 既定値は **DreamShaper XL Lightning DPM++ SDE** 前提でチューニング済みです。Lightning ユーザーは Offset を 0 のまま使えます。標準 SDXL モデルを使う場合は下記の Offset 適用が必要です。

> [!TIP]
> **アニメ風スタイルをさらに高品質にするには**
> `Juggernaut XL` などの実写・汎用系モデルでも動作しますが、アニメ専用モデル（例：`Animagine XL`, `Pony Diffusion V6 XL` など）に切り替えると、より本物のアニメに近い、鮮やかな塗りや綺麗な線画が得られます。

---

## 1.5. 推奨モデル（Checkpoint）

このノードのプロンプトは特定のモデルでチューニング・検証されています。下記の Tier 制を参考に選んでください。

> [!IMPORTANT]
> ### ★ Tier 1: 第一推奨（このノードの基準モデル）
>
> | モデル | ファイル名 | 備考 |
> | :--- | :--- | :--- |
> | **DreamShaper XL Lightning DPM++ SDE** | `dreamshaperXL_lightningDPMSDE.safetensors` | **本ノードの全プロンプト・全テストの基準モデル**。プロンプトが想定通りに反応する、油彩・スケッチ・写実・アニメすべてに無難に適応 |
>
> Civitai: https://civitai.com/models/112902/dreamshaper-xl
> ファイル配置: `ComfyUI/models/checkpoints/`

### Tier 1 推奨設定（KSampler Offset）

**既定値が Lightning 前提**でチューニング済みなので、Lightning モデル使用時は **`steps_offset = 0` / `cfg_offset = 0`** のままで OK です。

| Style | 既定 Steps | 既定 CFG | 既定 Sampler | 既定 Scheduler |
| :--- | :---: | :---: | :--- | :--- |
| Oil Painting | 8 | 2.0 | `dpmpp_sde` | `karras` |
| Cinematic Realistic | 8 | 1.8 | `dpmpp_sde` | `karras` |
| Anime Cel Shaded | 8 | 2.5 | `dpmpp_sde` | `karras` |

> [!TIP]
> 微調整したい場合は `steps_offset` で ±2〜4、`cfg_offset` で ±0.3〜0.5 程度の調整がおすすめです。CFG を 3.0 以上に上げると焼け付きが起きやすくなります。

### ○ Tier 2: 動作確認済みの代替

スタイル特化で Tier 1 を上回る品質が欲しい場合の代替候補。プロンプトはほぼそのまま動きますが、若干のチューニングが必要なことがあります。

| モデル | 得意なスタイル | 備考 |
| :--- | :--- | :--- |
| **AlbedoBase XL v3.1** | 全般 | 中立で癖が少ない。ファンタジー絵画 + 写実のハイブリッド。Lightning 不要なら標準ステップ（25〜35）で動作 |
| **Copax TimeLessXL v13** | Oil Painting | 古典絵画調・濃密な色彩・伝説級ボスの重厚感。標準ステップ（25〜35）必須 |
| **RealVisXL V5.0** | Cinematic Realistic | 写実モンスター画の最高峰、subsurface scattering が綺麗。NPC ポートレート（人間キャラ）にも最適 |
| **Illustrious XL v1.0** | Anime Cel Shaded | アニメ調モンスター。プロンプト先頭に `masterpiece, best quality` 追加推奨 |

### ⚠ Tier 3: 動作するが要注意（学習バイアス強）

これらのモデルは動作しますが、本ノードのプロンプトと**衝突するバイアス**を持っています。

| モデル | バイアス傾向 | 顕在化する問題 |
| :--- | :--- | :--- |
| `Juggernaut XL` 系 | 悪魔・暗黒方面に強い | コウモリ→悪魔・骸骨→Death Knight・狼→人狼 |
| `NightVision XL` | ダーク方面に強い | Light / 神聖系の表現が出にくい |

回避策: Tier 1（DreamShaper XL Lightning）に切り替える。プロンプトのウェイトを上げても完全には抑制できない。

### × Tier 4: 非推奨（動作未保証）

下記モデル系統は本ノードのプロンプト構造と噛み合わないため、動作保証外:

| モデル系統 | 理由 |
| :--- | :--- |
| **SD 1.5 系**（Realistic Vision など） | プロンプト長と重み構文が SDXL 前提のため、品質低下・崩壊しやすい |
| **Pony Diffusion V6 XL** | プロンプト先頭に `score_9, score_8_up, score_7_up...` が必須で、本ノードと共存させるには大幅改造が必要 |
| **FLUX.1 / SD 3.5 / HiDream** | プロンプトの解釈方式が違う（自然言語寄り）。本ノードの `(...:1.5)` ウェイトや variant 構文 `{a|b|c}` が正しく解釈されない可能性 |

### VRAM 別の現実解（参考）

| VRAM | 推奨セットアップ |
| :--- | :--- |
| **8GB** | Tier 1（DreamShaper XL Lightning、Steps 8〜12） ※ 本ノードの想定環境 |
| **12GB** | Tier 1 または Tier 2（標準ステップ 25〜35） |
| **16GB+** | Tier 1/2 + ControlNet / IP-Adapter 併用可 |

> [!TIP]
> **動物系種族（Bat / Rat / Wolf など）が悪魔化する場合**
> Tier 3 の `Juggernaut XL` 系を使っていないか確認。Tier 1（DreamShaper XL Lightning）に切り替えると改善します。

### 用途別おすすめ（ウィザードリィ風 RPG・古典 D&D 風 RPG 制作向け）

ゲーム素材としてキャラ・モンスター・NPC・装備を一貫して作る場合の組み合わせ:

| 用途 | おすすめモデル | 本ノード style | 理由 |
| :--- | :--- | :--- | :--- |
| **モンスター全般（推奨）** | DreamShaper XL Lightning | Oil Painting / Cinematic | 悪魔化バイアスなし、絵画寄りでウィザードリィの雰囲気と相性◎、Lightning で量産しやすい |
| **重厚ボス・伝説級モンスター** | Copax TimeLessXL v13 | Oil Painting | 古典絵画の濃密な色彩、Boss/Legendary ランクの威厳がより出る |
| **人間 NPC（仲間・酒場主・商人など）** | RealVisXL V5.0 | Cinematic Realistic | 人間ポートレートの写実度が圧倒的、肌・布・金属の質感が綺麗 |

**統一感を最優先する場合**: DreamShaper XL Lightning **単体**で十分な仕上がりになります（本ノードはこれ前提でチューニング済み）。

**ウィザードリィ向きとして避けるべきモデル**:
- ❌ Pony Diffusion / Animagine XL — アニメ偏向で硬派なウィザードリィのトーンが消える
- ❌ Juggernaut XL Ragnarok — モンスターが悪魔化（Skeleton → Death Knight、Bat → 悪魔コウモリ）
- ⚠️ EpicRealism XL — 過度に写実的でゲームアート感がない

> [!NOTE]
> **モデル切替時の注意**:
> - SDXL 系モデル間では本ノードのプロンプト構文（`(text:1.5)` ウェイト、`{a|b|c}` バリアント）はそのまま動作
> - ただしバイアスが違うため、Common/Boss の見え方が微妙に変わる
> - Lightning 以外は `steps_offset` / `cfg_offset` を Tier 1 表通りに加算する

---

## 7. KSampler との連携方法
このノードは、選択したスタイルに最適な KSampler の設定値（steps, cfg, sampler_name, scheduler）を自動的に出力します。

### 設定手順
1.  **KSampler ノードを用意する**: 通常の `KSampler` ノードを配置します。
2.  **入力をピンに変換する**: `KSampler` ノードの上で **右クリック** し、以下を選択して各項目を入力ピンに変換します：
    - `convert steps to input`
    - `convert cfg to input`
    - `convert sampler_name to input`
    - `convert scheduler to input`
3.  **線を繋ぐ**: `RPG Monster Generator` ノードの各出力ピンから、`KSampler` の対応する入力ピンへ線を繋ぎます。

### 推奨値の微調整（Offset機能）
`KSampler` に設定値を繋ぐと、サンプラー側での直接操作ができなくなります。その代わりに、当ノードの **`steps_offset`** と **`cfg_offset`** を操作することで、推奨値を基準に数値を微調整できます。
- **steps_offset**: スタイルの基本ステップに追加・削減する値（範囲: `-30 〜 +30`、例：`-5` で 5 ステップ減らす）。
- **cfg_offset**: 基本 CFG に加算・減算する値（範囲: `-10.0 〜 +10.0`、例：`1.5` で 1.5 上げる）。

> [!NOTE]
> **本ノードの既定値は Lightning モデル (DreamShaper XL Lightning DPM++ SDE) 前提です。**
> Lightning ユーザーは Offset 不要、`steps_offset = 0 / cfg_offset = 0` のまま使えます。

> [!IMPORTANT]
> **標準 SDXL モデル（非 Lightning）を使う場合の Offset 設定**
> Lightning ではない通常の SDXL モデル（`SDXL Base`, `Juggernaut XL` 通常版等）は、Lightning より多くの Steps と高い CFG が必要です。以下の Offset を加算してください:
>
> | Style | 既定 Steps | 既定 CFG | 推奨 steps_offset | 推奨 cfg_offset | 結果 (Steps / CFG) |
> | :--- | :---: | :---: | :---: | :---: | :--- |
> | Oil Painting | 8 | 2.0 | `+22` | `+6.0` | 30 / 8.0 |
> | Cinematic Realistic | 8 | 1.8 | `+27` | `+4.7` | 35 / 6.5 |
> | Anime Cel Shaded | 8 | 2.5 | `+20` | `+5.0` | 28 / 7.5 |
>
> Sampler / Scheduler は本ノードからの出力を使うか、KSampler 側で `dpmpp_2m / karras` を直接指定してください（Lightning 用 `dpmpp_sde` は標準モデルでも動作はしますが最適ではありません）。

## 2. Species (種族)
モンスターの基本的な外見を決定します。現在、以下の全28種族が選択可能です。

- **Slime**: 半透明、粘液質、核が見える。
- **Skeleton**: 露出した骨、暗い眼窩、崩れかけた質感。
- **Orc**: 筋骨逞しく、牙があり、荒々しい戦士。
- **Dragon**: 鱗、巨大な翼、鋭い爪、爬虫類的な瞳。
- **Bat**: 巨大な翼を持つ蝙蝠、鋭い牙、毛深い体。
- **Rat**: 突然変異した巨大ネズミ、光る目、鋭い爪。
- **Frog**: 湿った肌、大きな口、突き出た目。
- **Spider**: 八本の脚、複数の目、毛深い体質。
- **Kobold**: Reptilian（爬虫類）の特徴を持つ、小さな戦士。
- **Goblin**: 緑色の肌、尖った耳、邪悪な表情。
- **Ogre**: 巨大な体、厚い皮膚、単角。
- **Vampire**: 青白い肌、鋭い牙、貴族的な装束。
- **Demon**: 角、翼、筋肉質な体、威圧感。
- **Ghost**: 半透明、幽霊のような実体のない姿。
- **Hydra**: 複数の蛇のような首を持つ大蛇。
- **Manticore**: ライオンの体、蝙蝠の翼、蠍の尾。
- **Medusa**: 蛇の髪を持つ女性。魅惑的な美しさと石化の視線、しなやかな曲線美。
- **Gargoyle**: 石造りの翼を持つ怪物、ひび割れた石の肌。
- **Lich**: 古代の骨格、魔術師のローブ、腐敗した布。
- **Mimic**: 宝箱に擬態した怪物、鋭い牙、長い舌。
- **Wolf**: 獰猛な巨大狼、逆立った毛並み、捕食者の構え。
- **Ghoul**: 飢えたアンデッド、青白い皮膚、壊死したオーラ。
- **Giant Worm**: 巨大な環形動物、幾重にも重なる鋭い歯。
- **Chimera**: ライオン・山羊・蛇が融合した異形の獣。
- **Flesh Golem**: 繋ぎ合わされた筋肉と皮膚の構築物。
- **Harpy**: 女性の半身と鳥の翼・爪を持つ怪鳥。蠱惑的な雰囲気と優雅なシルエット。
- **Wraith**: 黒いボロを纏った死神のような影。
- **Cerberus**: 三つの頭を持つ巨大な魔犬、鋭い牙と黒い毛並。

### 主な種族の定義例

| 種族名 | 特徴・プロンプトの狙い |
| :--- | :--- |
| **Dragon** | 4 本足の古典西洋ドラゴン。Common（無装飾・地味色）→ Elite（戦傷・隻眼）→ Boss（角の王冠・背骨スパイク・胸ブレス）→ Legendary（金鱗全身・後光・神聖ルーン）→ Ancient（全身苔・色褪せ）→ Mutated（双頭・余分翼・腫瘍）の進化階段が明確。**ControlNet 使用時はフラット壁参照画像を必ず使う**（縦コリドー参照だと二足立ち化する）。5 本足が稀に出るが SDXL の四足獣描画限界として許容、batch 複数生成で当たりを選ぶ運用。 |
| **Giant Worm** | 床の上でミミズのようにグルグルと巻いた「とぐろ（spiral mound）」の造形を重視。 |
| **Harpy** | 優美な人面・しなやかなS字ポーズ・女性の上半身と鳥の翼・足を両立。体にフィットする装甲（form-fitting armor）で色香と安全性を維持。 |
| **Medusa** | 魅惑的な美貌と威圧感を両立。S字の曲線美を強調した構図と、露出を抑えた豪華な装甲デザインを採用。 |
| **Cerberus** | 3つの独立した頭部と、低い姿勢での全身描写を安定化。 |
| **Demon** | ポーズのバリエーション（翼を広げる、屈む等）と斜め構図を導入し、正面固定を回避。 |
| **Slime** | 球体を避け、雫型や床に広がった不定形、内部の核（Nucleus）を強調。 |

---

## 3. Element (属性)
モンスターが纏うエネルギーや視覚的なエフェクトを決定します。

- **None**: 属性なし。
- **Fire**: 炎の粒子、煙、灼熱のマグマのような赤。
- **Ice**: 氷の結晶、冷気、青白く澄んだ輝き。
- **Poison**: 紫や緑の霧、毒々しい泡、腐食感。
- **Lightning**: 青い電光、シアンの閃光、激しい放電エフェクト。
- **Dark**: 黒い影のオーラ、光を吸収する紫の虚無感。
- **Light**: 聖なる黄金の輝き、神々しい光の粒。
- **Metal**: 鏡面仕上げのメタリックな質感、クローム。

> [!NOTE]
> ### 属性エフェクトの「領域汚染」について
>
> SDXL モデルの学習データには「**属性付きクリーチャーは周囲環境も影響を受ける**」というバイアスが含まれています。そのため、Element を強く適用すると **モンスター本体だけでなく床や壁にも属性エフェクトが広がる**ことがあります。
>
> 例:
> - **Ice**: 床に氷塊・霜の patches が散らばる
> - **Fire**: 床に焚火・燃え滓が散らばる
> - **Lightning**: 床にスパーク・電光跡が残る
> - **Dark**: 床に影の水たまりが広がる
> - **Light**: 床に光のパッチが現れる
>
> これは ComfyUI の ControlNet を使っても完全には抑えきれない**仕様**です。
>
> **RPG 的な解釈としてはむしろ自然**で、「Ice 属性のボスの周囲は凍りつく」「Fire 属性のクリーチャーが立つ場所は焼け焦げる」といった **Element Domain（属性領域効果）** として捉えると、ゲームのアートワークとして違和感ありません。
>
> 完全に背景をクリーンにしたい場合は、生成後に画像編集ソフトで該当部分を消すか、Inpainting ワークフローで再描画してください。

---

## 4. Rank (強さ・希少度・個性)
モンスターの迫力・装飾・特殊な個性を一括で決定します。
旧 `Variant` から `Ancient` / `Mutated` を統合しました。

### 強さ・希少度（4 段階）
- **Common**: 一般的な個体。標準的な外見で装飾も控えめ。
- **Elite**: 強力な個体。歴戦の凄みと鉄・青銅の装飾、わずかに大型化。
- **Boss**: 強大で威厳のある個体。圧倒的巨体と周囲に漂うオーラ、地響きを感じる存在感。
- **Legendary**: 神話の如き最高位。黄金に輝く装飾、神々しい粒子を纏った究極の造形。

### 特殊個性（2 種）
- **Ancient**: 長い年月を経た古代個体。体表に苔や塵、風化した質感、古の威厳。
- **Mutated**: 異常変異した個体。不規則な結晶・棘・腫瘍状の異形、膨らんだ血管、対称性の崩れ。

> [!TIP]
> **Rank: Ancient の使い所**
> 風化した古代個体を表現したい場合に選択。Scene を `Graveyard` などにすると「古代の墓守」的な雰囲気が出ます。

---

## 5. Scene (背景・場所)
モンスターが出現する場所（背景）を決定します。

- **Dungeon**: 暗い石造りの地下牢。鉄格子のある冷たい部屋。
- **Lava Cave**: 溶岩が流れる灼熱の洞窟。
- **Ice Vault**: 氷に閉ざされた古代の宝物庫。
- **Graveyard**: 地下の墓地、カタコンベ。
- **Throne Room**: 廃墟となった玉座の間、ひび割れた大理石。
- **Transparent (White)**: 純白の背景。素材の切り抜き（透過処理）に最適。

> [!TIP]
> **「背景透過」を実現するには**
> AIは直接透明な画像を出力するのが苦手なため、この `Transparent (White)` を選んで「白い背景の画像」を作り、ComfyUI の **`Rembg`** や **`LayerMask`** といった背景削除ノードを繋ぐことで、綺麗な透過PNG素材を作成できます。

---

## 組み合わせのコツ
- **リアルにしたい**: `Cinematic Realistic` を選び、KSampler の CFG を少し下げてください。
- **古代の威厳**: `Rank: Ancient` と `Scene: Graveyard` を組み合わせると、忘れ去られた古代モンスターの雰囲気が出ます。
- **属性の視認性を高める**: `Element: Fire` や `Lightning` を選んだ際は、少し暗い `Scene` を選ぶと光が映えます。

# Workflows

このディレクトリには `RPG Monster Generator` ノードを使った ComfyUI ワークフローのサンプルが入っています。

## ファイル一覧

| ファイル | 用途 |
| :--- | :--- |
| **`dungeon_reference_generator.json`** | ControlNet 用の **モンスターなしダンジョン背景画像** を生成 |
| **`controlnet_dungeon.json`** | ControlNet + HiRes Fix 2 段サンプリングで高解像度モンスター画像を生成（メイン） |
| **`inpaint_partial_fix.json`** | 部分修正（手書きプロンプト版）— 自由なプロンプトで細かい指示が可能 |
| **`inpaint_with_rpg_node.json`** | 部分修正（RPG Generator 自動版）— 元画像と同じ Species/Element/Rank を選ぶだけ |

### 使う順序
1. `dungeon_reference_generator.json` で気に入ったダンジョン画像を数枚生成
2. 一番良いのを `ComfyUI/input/dungeon_ref_NN.png` として保存
3. `controlnet_dungeon.json` を読み込んで ControlNet 経由でモンスター生成
4. （任意）変な部分があれば `inpaint_partial_fix.json` で部分修正

---

## dungeon_reference_generator.json — 参照用ダンジョン背景の生成

ControlNet の参照画像として使う「**モンスターのいない**ダンジョン画像」を生成するための簡易ワークフロー。

### 使い方
1. ComfyUI 画面に `dungeon_reference_generator.json` をドラッグ&ドロップ
2. KSampler の `seed` を `randomize` に設定（既定値）
3. `Queue Prompt` を数回実行 → 4〜8 枚生成
4. 中央が空いていてゴシック調の暗い構図のものを選ぶ
5. 選んだ画像を **右クリック → Save Image** で保存
6. ファイル名を `dungeon_ref_01.png` 等にリネームして `C:\Project\ComfyUI\input\` へ配置

### 中央が空いた構図にするコツ

良い参照画像の条件は「**画面中央にモンスターを配置できる空間がある**」こと:
- 廊下の遠近構図
- アーチ越しの構図
- 中央に何もない部屋

### ★ 強くおすすめ: フラット壁テクスチャ（推奨）

**奥行きのない石壁テクスチャ**を参照画像にするとモンスターが**手前に大きく**配置されます。理由: ControlNet が「奥行き構造」を見つけられないため、AI が空間内で自由なサイズで被写体を描く。

フラット壁参照用プロンプト例（Positive 抜粋）:
```
(frontal flat view of a dark medieval dungeon stone wall facing the camera directly:1.6),
(flat orthographic composition with no depth perspective, no vanishing point:1.5),
(gothic stone block wall surface filling the entire frame:1.4),
grimy stone bricks covered in moss and damp, dark cracks running across the stones,
weathered ancient masonry texture, wall-mounted rusted iron torches on the left and right sides,
dim light only from side torches, (upper portion of the image fading into deep pitch black darkness:1.4),
no ceiling visible, just a small strip of dark stone floor at the very bottom of the image
```

ネガティブには `deep corridor, perspective view, vanishing point, ceiling visible, vaulted ceiling, deep depth of field` を必ず入れる。

このタイプの参照画像（例: `dungeon_ref_04.png`）を使うと、ControlNet 適用時にモンスターが **画面の 70-90% を占有** するようになり、「奥に小さく置かれる」現象が解消されます。

### ★ 四足獣（Dragon / Wolf / Cerberus / Hydra / Manticore / Chimera）には特に必須

**縦長コリドー型の参照画像を使うと、四足獣が二足立ちポーズに変換されやすい**:

- ControlNet が「縦長空間」を強制 → 水平に長い四足獣が空間に収まらない
- AI の妥協策として **後ろ脚だけで立ち上がる二足ポーズ**で縦に詰める
- 結果: ドラゴンが T-Rex 風 / Dragonborn 風になる

**フラット壁テクスチャ参照画像なら、ControlNet が「縦長制約」を強制しないため、四足獣が自然な水平ポーズで描かれる**。Dragon / Wolf / Cerberus 等を生成する時は必ずフラット壁参照を使う。

縦コリドー型の参照画像はヒューマノイド（Skeleton / Goblin / Vampire / Lich など）には適しているが、四足獣には不適。Scene 別というより**体型別**で参照画像を使い分けるのが正解。

### 異なるシーンの参照画像を作りたい場合

Positive プロンプトを書き換えれば他の Scene 用の参照画像も作れます:

| Scene | Positive 例 |
| :--- | :--- |
| Lava Cave | `dark volcanic cavern interior, basalt rock walls, glowing lava rivers, no creatures` |
| Ice Vault | `ancient frozen burial chamber interior, blue ice walls, frost-covered pillars, no creatures` |
| Graveyard | `underground catacomb interior, walls of skulls, dusty stone, candlelight, no creatures` |
| Throne Room | `ruined gothic throne hall interior, stone throne, tattered tapestries, cracked marble, no creatures` |

それぞれ生成して `dungeon_ref_lava.png` `dungeon_ref_ice.png` 等の名前で保存しておくと、`controlnet_dungeon.json` 側の `LoadImage` を切り替えて使えます。

---

## controlnet_dungeon.json — ControlNet + HiRes Fix（2 段サンプリング）

プロンプトのみでは難しい「背景の完全固定」を ControlNet で実現し、さらに **4 倍アップスケール + 第 2 サンプリング**で高解像度ディテール強化までを 1 ワークフローでこなします。

### 使う前のセットアップ（4 つ）

#### 1. ControlNet モデルをダウンロード

xinsir の SDXL ControlNet が推奨。**Depth** か **Canny** どちらでも動作します:

- **Depth 版**（既定）: https://huggingface.co/xinsir/controlnet-depth-sdxl-1.0 → `diffusion_pytorch_model.safetensors`
- **Canny 版**: https://huggingface.co/xinsir/controlnet-canny-sdxl-1.0 → `diffusion_pytorch_model_V2.safetensors`

配置先: `C:\Project\ComfyUI\models\controlnet\`

> 既定ワークフローでは Depth 版を `SDXL\controlnet-depth-sdxl-1.0\diffusion_pytorch_model.safetensors` パスで指定しています。Canny 版を使う場合は `ControlNetLoader` のファイル選択を切り替え、プリプロセッサも MiDaS Depth → Canny Edge に変更してください。

#### 2. アップスケールモデルをダウンロード

`4x-UltraSharp.pth` を入手（HuggingFace 等で配布）:

配置先: `C:\Project\ComfyUI\models\upscale_models\4x-UltraSharp.pth`

#### 3. 必要なカスタムノードパックをインストール

ComfyUI Manager から:
- **`ComfyUI's ControlNet Auxiliary Preprocessors`**（作者: Fannovel16）— MiDaS Depth プリプロセッサ用
- **`rgthree-comfy`** — Seed ノードと Image Comparer ノード用

#### 4. 参考ダンジョン画像を配置

`C:\Project\ComfyUI\input\dungeon_ref_NN.png` に好みのダンジョン画像を保存（既定ワークフローは `dungeon_ref_06.png` を参照）。

良い参考画像の条件:
- **フラット壁テクスチャ**（奥行きなし）が最強推奨 — 四足獣の二足立ち化を防げる
- 中央が空いた構図（縦長コリドー型はヒューマノイド向け）
- 暗いゴシック調の照明
- 1024×1024 または近い縦横比

入手方法:
- 同梱の `dungeon_reference_generator.json` で生成（フラット壁プロンプト推奨）
- Civitai で `dark dungeon background` 検索

### ワークフローの読み込み

1. ComfyUI を起動
2. `controlnet_dungeon.json` を **画面にドラッグ＆ドロップ**
3. すべてのノードが配置されて接続される
4. `Queue Prompt` で実行

### 構成ノード（HiRes Fix 2 段サンプリング）

```
                  ┌────────── Pass 1 (1024×1024) ──────────┐
[1] Checkpoint ──→ [5] RPG Monster Gen ──→ [6] ControlNet ──→ [8] KSampler ──→ [9] VAEDecode ──┐
                       (clip)                  ↑                  (denoise=1.0)                 │
[2] LoadImage ──→ [3] MiDaS Depth ─────────────┤                                                │
[4] ControlNet Loader ─────────────────────────┘                                                │
[15] Seed (rgthree) ─────────────────────────────────→ (両 KSampler の seed)                   │
                                                                                                │
                                                                          ┌─────────────────────┘
                                                                          │
                  ┌────────── Pass 2 (HiRes Fix) ──────────┐               │
                  ↓                                                        ↓
[17] UpscaleLoader ──→ [16] ImageUpscale ──→ [18] ResizeAndPad ──→ [19] VAEEncode ──→ [20] KSampler ──→ [21] VAEDecode ──→ [22] SaveImage
     (4x-UltraSharp)                       (1536×1536)                            (denoise=0.45)                          (filename=yyyyMMdd)

[23] Image Comparer (rgthree) ←──── Pass 1 image / Pass 2 image (スライダー比較)
[24] PreviewImage ←──── Pass 1 image (リアルタイム確認)
```

### 各パスの役割

| パス | 役割 | 設定 |
| :--- | :--- | :--- |
| **Pass 1 (Node 8)** | ControlNet で背景を緩く誘導しつつ初期生成 | 1024×1024 / 8 steps / cfg 2.0 / **denoise 1.0** |
| **Pass 2 (Node 20)** | アップスケール後にディテール強化 | 1536×1536 / 1 step / cfg 2.0 / **denoise 0.4** |

Pass 2 は denoise 低めで「線・質感の補強」に徹するので、**Pass 1 の構図・キャラクターを維持しつつ高解像度化**できます。

### パラメータ調整のコツ

#### ノード 6 (Apply ControlNet Advanced)

| パラメータ | 既定値 | 推奨範囲 | 効果 |
| :--- | :---: | :---: | :--- |
| `strength` | `0.3` | `0.2 〜 0.85` | 強い: 背景固定が確実 / 弱い: モンスターの自由度が高い |
| `start_percent` | `0.0` | `0.0` | 最初から効かせる |
| `end_percent` | `0.3` | `0.3 〜 0.85` | 早く切るほどモンスター本体の自由度が増す |

> 既定値 `0.3 / 0.3` は本ノードの強い framing/identity プロンプトを最大活用するチューニング。背景固定を強めたい場合は両方とも `0.6 〜 0.8` に上げる（ただし四足獣の二足立ち化リスクが上がる）。

#### ノード 20 (Pass 2 KSampler) - HiRes Fix

| パラメータ | 既定値 | 推奨範囲 | 効果 |
| :--- | :---: | :---: | :--- |
| `denoise` | `0.4` | `0.35 〜 0.55` | 高い: ディテール強化が強い / 低い: Pass 1 の構図に忠実 |
| `steps` | `1` | `1 〜 4` | Lightning は少 step で OK。多すぎるとディテールが過剰に |
| `cfg` | `2.0` | `1.5 〜 2.5` | Lightning 推奨範囲 |

#### ノード 5 (RPG Monster Generator)

`steps_offset = 0 / cfg_offset = 0`（既定）のまま使用。`STYLE_DATA` の既定値が Lightning に最適化されています。

#### ノード 15 (Seed rgthree)

`-1` を設定すると毎回ランダム seed。両方の KSampler が同じ seed を使うので、Pass 1 と Pass 2 の整合性が取れます。

### 比較・確認ノード

- **Node 24 (PreviewImage)**: Pass 1 の出力をリアルタイム確認
- **Node 23 (Image Comparer rgthree)**: Pass 1 と Pass 2 をスライダーで比較（HiRes Fix の効果を可視化）
- **Node 22 (SaveImage)**: 最終出力（Pass 2 結果）を `yyyyMMdd_filename_prefix` 形式で保存

### ControlNet 一括 ON/OFF スイッチ（Subgraph 方式）

ワークフローには ControlNet 関連 3 ノード（ControlNetLoader / MiDaS Depth / ControlNetApply）を **1 つの Subgraph ノード**にまとめてあります。

四足獣（Dragon / Wolf / Cerberus 等）のように ControlNet なしで生成したい場合に **1 クリックで一括バイパス**できます。

#### Subgraph とは

ComfyUI 0.14+ の機能。複数のノードを 1 つの「super ノード」として扱える機能で:
- 視覚的に**1 つのノード**として表示される
- 入出力ピンが定義されている（このワークフローでは positive/negative/image 入力 → positive/negative 出力）
- **Subgraph 自体をバイパスすると、内部の全ノードが一括バイパスされる**

#### 使い方

1. ワークフロー上部に表示される **ControlNet Subgraph ノード**（中サイズの 1 ノード）を右クリック
2. **「Bypass」** を選択（または `Ctrl+B`）
3. Subgraph 内の 3 ノード全てが一括バイパス状態に
4. もう一度同じ操作で解除

ComfyUI 標準機能なので追加パッケージ不要。

#### Subgraph の中身を編集したい場合

Subgraph ノードを **ダブルクリック**すると内部が展開され、ControlNetLoader / MiDaS Depth / ControlNetApply の 3 ノードが見える。パラメータ調整（strength や end_percent 等）はここで行う。

#### 体型別おすすめ設定

| 体型 | 該当種族 | ControlNet 推奨 |
| :--- | :--- | :--- |
| ヒューマノイド | Skeleton / Goblin / Vampire / Lich など | ☑ ON（縦コリドー型 ref OK） |
| 四足獣 | Dragon / Wolf / Cerberus / Hydra など | ☑ ON（フラット壁 ref のみ）or ☐ OFF |
| 大型ボス | Boss/Legendary 全般 | ☐ OFF（プロンプトに任せる方が威厳出る） |

### 複数の参考背景を使い分ける場合

**シンプル**: `LoadImage` ノードのファイル名を変えるだけ
- `dungeon_ref_01.png` → `dungeon_ref_03.png` 等

**自動切替**: `rgthree-comfy` の `Image Switch (rgthree)` で複数の `LoadImage` を切替可能に

### トラブルシューティング

| 症状 | 原因 | 対処 |
| :--- | :--- | :--- |
| 「Node not found: MiDaS-DepthMapPreprocessor」 | `comfyui_controlnet_aux` 未インストール | セットアップ #3 を実行 |
| 「Node not found: Seed (rgthree)」 / 「Image Comparer (rgthree)」 | `rgthree-comfy` 未インストール | セットアップ #3 を実行 |
| 「Node not found: ResizeAndPadImage」 | ComfyUI 0.14.1+ が必要 | ComfyUI 本体を更新 |
| 「ControlNet model not found」 | モデルファイル未配置 / パスミス | セットアップ #1 のファイルパスを確認 |
| 「Upscale model not found: 4x-UltraSharp.pth」 | アップスケールモデル未配置 | セットアップ #2 を実行 |
| 「No image found: dungeon_ref_NN.png」 | 参考画像未配置 | セットアップ #4 を実行 |
| 背景が固定されない | ControlNet strength が低い | strength を `0.6 〜 0.8` まで上げる |
| 四足獣（Dragon等）が二足立ちになる | 縦長コリドー型の参照画像 | フラット壁テクスチャの参照画像（`dungeon_ref_06.png` 等）に切替 |
| モンスターが歪む | ControlNet strength が高すぎ | strength を `0.3 〜 0.4` に下げる、または `end_percent` を `0.3` に下げる |
| Pass 2 でディテールが過剰 / 元と違う | denoise が高すぎ | Pass 2 KSampler の denoise を `0.35` 程度に下げる |
| 全体的にボヤける | Pass 1 / Pass 2 の cfg が低すぎ | RPG Generator のスタイル選択を見直す。Anime Cel Shaded は cfg 2.5 |
| しっぽ・脚など特定部位だけ変 | 単一画像生成では完全制御困難 | `inpaint_partial_fix.json` で部分修正（後述） |

---

## inpaint_partial_fix.json — 部分修正（インペイント）

`controlnet_dungeon.json` で生成した画像のうち、**特定部分だけが変な場合**（しっぽ分岐・脚の本数違反・顔の崩れ等）に、その部分だけを書き直すワークフロー。

### 使い方

1. ComfyUI 画面に `inpaint_partial_fix.json` をドラッグ&ドロップ
2. **`LoadImage` ノードに修正したい画像をドロップ**（例: `dragon_metal_legendary_00002_.png`）
3. **`LoadImage` 上で右クリック → 「Open in MaskEditor」**
4. ブラシで**修正したい部分を白く塗る**（白い部分だけが再描画される）
5. 「Save to node」 → MaskEditor を閉じる
6. **`Positive` ノード**に修正後の理想的な描写を記述
   - 例: しっぽ修正なら `(natural single draconic tail tapering smoothly to a single sharp tip:1.5), single uninterrupted tail line, golden scales`
7. **`Negative` ノード**に避けたい要素を記述
   - 例: `branching tail, split tail, multiple tails, malformed tail`
8. **`KSampler` の `denoise` を調整**（次節）
9. `Queue Prompt` 実行 → SaveImage に修正版が出力

### denoise 値の選び方

| 値 | 効果 |
| :---: | :--- |
| `0.5 〜 0.6` | 元の形を残しつつ控えめに修正（軽微な不具合修正） |
| **`0.7`**（既定） | バランス型（推奨デフォルト） |
| `0.8 〜 0.9` | 大胆に書き直し（大きな崩壊修正） |
| `1.0` | マスク部分を完全新規描画（最後の手段） |

### マスク境界を自然に馴染ませるコツ

`VAEEncodeForInpaint` ノードの `grow_mask_by` パラメータ:

| 値 | 効果 |
| :---: | :--- |
| `0` | マスクそのまま（境界がくっきり見える可能性） |
| `4 〜 6` | 軽くぼかし |
| **`8`**（既定） | 自然な馴染み（推奨） |
| `12 〜 16` | 強くぼかし（境界周辺も再描画される） |

### 推奨追加ノードパック（精度向上）

| パック | 効果 |
| :--- | :--- |
| `ComfyUI-Inpaint-CropAndStitch` | マスク部分だけ切り出して再描画→ステッチ。**SDXL での精度が大幅向上** |
| `ComfyUI-Impact-Pack` | `MaskDetailer` で部位特化のディテール強化 |

### トラブルシューティング

| 症状 | 原因 | 対処 |
| :--- | :--- | :--- |
| マスク部分が描画されない | MaskEditor で塗っていない / Save し忘れ | LoadImage 右クリック → MaskEditor で再度塗って Save |
| 修正部分の色味が周辺と合わない | `grow_mask_by` が小さすぎ | `12 〜 16` に上げて境界周辺も再描画 |
| 修正部分が元の形そのままで変わらない | `denoise` が低すぎ | `0.8` 以上に上げる |
| 修正部分が全く違う絵になる | `denoise` が高すぎ | `0.6` 以下に下げる |
| プロンプトと違うものが出る | マスクが小さすぎて影響範囲不足 | マスク範囲を広めに塗る |

---

## inpaint_with_rpg_node.json — 部分修正（RPG Generator 自動版）

`inpaint_partial_fix.json` の **プロンプト自動生成版**。RPG Monster Generator ノードが元画像と同じ条件で自動的にプロンプトを生成するので、**毎回プロンプトを手書きしなくて済む**。さらに必要なら追加プロンプトをハイブリッド合成可能。

### inpaint_partial_fix.json との違い

| 観点 | partial_fix（手書き版） | with_rpg_node（自動版） |
| :--- | :--- | :--- |
| プロンプト | 毎回 Positive/Negative を手で書く | Style/Species/Element/Rank/Scene 選ぶだけで自動 |
| 整合性 | 手書きの精度に依存 | 元画像と同じ条件 → **完全整合** |
| 追加指示 | プロンプトに直接書く | 別ノードで追加（任意） |
| ノード数 | 10 | 13（ConditioningCombine 追加） |
| 適している場面 | プロンプト力ある人、特殊な修正、汎用画像のインペイント | RPG Monster Generator で生成した画像の修正全般 |

### 使い方

1. ComfyUI 画面に `inpaint_with_rpg_node.json` をドラッグ&ドロップ
2. **`LoadImage` ノードに修正したい画像をドロップ**
3. **`LoadImage` 上で右クリック → 「Open in MaskEditor」**
4. ブラシで修正したい部分を白く塗る → Save to node → 閉じる
5. **`RPG Monster Generator` ノードで元画像と同じ選択肢を設定**
   - 例: 元画像が「Dragon × Metal × Legendary × Dungeon」なら同じ選択
   - これだけで元画像と整合する Positive/Negative プロンプトが自動生成される
6. （任意）**「追加 Positive」**ノードに部位特化の指示を書く
   - 既定値: `(clean smooth anatomy, single uninterrupted form:1.4)` が入っている（汎用的に効く）
   - しっぽ修正なら `(natural single tail tapering smoothly, no branching:1.5)` 等を追記
   - 空でも動作する（RPG Generator のプロンプトだけで動く）
7. （任意）**「追加 Negative」**ノードも同様
   - 既定値: `branching, split, duplicate, malformed, deformed` が入っている
8. **`KSampler` の `denoise` を調整**（partial_fix と同じく 0.6〜0.9）
9. `Queue Prompt` 実行

### ハイブリッド合成の仕組み

```
RPG Generator → 自動 Positive ─┐
                                ├→ ConditioningCombine → KSampler.positive
追加 Positive ─────────────────┘                              ↓
                                                          (両方の指示を合成)
RPG Generator → 自動 Negative ─┐
                                ├→ ConditioningCombine → KSampler.negative
追加 Negative ─────────────────┘
```

`ConditioningCombine` は 2 つのプロンプトを**両方とも適用**する効果があり、AI が両方を満たそうとする。`ConditioningConcat`（連結）と違って独立したプロンプトとして処理される。

### KSampler の自動連携

| パラメータ | 接続元 | 役割 |
| :--- | :--- | :--- |
| `model` | Checkpoint | モデル |
| `positive` | ConditioningCombine | RPG + 追加の合成プロンプト |
| `negative` | ConditioningCombine | RPG + 追加の合成プロンプト |
| `latent_image` | VAEEncodeForInpaint | マスク済み画像 |
| `steps` | RPG Generator | スタイル既定値 |
| `cfg` | RPG Generator | スタイル既定値 |
| `sampler_name` | RPG Generator | スタイル既定値 |
| `scheduler` | RPG Generator | スタイル既定値 |
| `denoise` | （手動設定） | **0.7 推奨**（部分修正用） |

**denoise だけ手動**: RPG Generator は 1.0 想定だが、インペイントは 0.7 が適切なため接続しない。

### SaveImage のファイル名

`RPG Generator` の `filename_prefix` 出力（`{species}_{element}_{rank}` 形式）が自動で SaveImage に渡るので、**修正版も元画像と同じネーミングルール**で保存される（プレフィックスに `_inpaint` 付加）。

例: `dragon_metal_legendary_inpaint_00001_.png`

### よくある使い方（パターン別）

| 修正したい部位 | 追加 Positive 例 | 追加 Negative 例 |
| :--- | :--- | :--- |
| しっぽが分岐 | `(natural single tail tapering smoothly to a sharp tip:1.5)` | `branching tail, split tail, multiple tails` |
| 脚が 5 本 | （空でも OK、Negative だけでも効く） | `extra leg, fifth leg, three front legs` |
| 顔が崩壊 | `(clean reptilian dragon face with two glowing eyes:1.5)` | `extra eyes, malformed face, distorted face` |
| 翼が変 | `(natural symmetrical bat-like dragon wing:1.5)` | `broken wing, deformed wing, three wings` |
| 装備が変 | `(clean ornate golden plate armor:1.4)` | `broken armor, twisted armor, asymmetric armor` |

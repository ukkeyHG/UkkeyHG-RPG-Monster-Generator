# Workflows

このディレクトリには `RPG Monster Generator` ノードを使った ComfyUI ワークフローのサンプルが入っています。

## ファイル一覧

| ファイル | 用途 |
| :--- | :--- |
| **`dungeon_reference_generator.json`** | ControlNet 用の **モンスターなしダンジョン背景画像** を生成 |
| **`controlnet_dungeon.json`** | ControlNet + HiRes Fix 2 段サンプリングで高解像度モンスター画像を生成（メイン） |

### 使う順序
1. `dungeon_reference_generator.json` で気に入ったダンジョン画像を数枚生成
2. 一番良いのを `ComfyUI/input/dungeon_ref_NN.png` として保存
3. `controlnet_dungeon.json` を読み込んで ControlNet 経由でモンスター生成

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

xinsir の SDXL ControlNet が推奨。**Canny** か **Depth** どちらでも動作します:

- **Canny 版**（既定）: https://huggingface.co/xinsir/controlnet-canny-sdxl-1.0 → `diffusion_pytorch_model_V2.safetensors`
- **Depth 版**: https://huggingface.co/xinsir/controlnet-depth-sdxl-1.0 → `diffusion_pytorch_model.safetensors`

配置先: `C:\Project\ComfyUI\models\controlnet\`

> 既定ワークフローでは Canny 版を `SDXL\controlnet-canny-sdxl-1.0\diffusion_pytorch_model_V2.safetensors` パスで指定しています。Depth 版を使う場合は `ControlNetLoader` のファイル選択を切り替えてください（プリプロセッサは MiDaS Depth のままで OK）。

#### 2. アップスケールモデルをダウンロード

`4x-UltraSharp.pth` を入手（HuggingFace 等で配布）:

配置先: `C:\Project\ComfyUI\models\upscale_models\4x-UltraSharp.pth`

#### 3. 必要なカスタムノードパックをインストール

ComfyUI Manager から:
- **`ComfyUI's ControlNet Auxiliary Preprocessors`**（作者: Fannovel16）— MiDaS Depth プリプロセッサ用
- **`rgthree-comfy`** — Seed ノードと Image Comparer ノード用

#### 4. 参考ダンジョン画像を配置

`C:\Project\ComfyUI\input\dungeon_ref_NN.png` に好みのダンジョン画像を保存（例: `dungeon_ref_03.png`）。

良い参考画像の条件:
- 中央が空いた構図
- 暗いゴシック調の照明
- 1024×1024 または近い縦横比

入手方法:
- 同梱の `dungeon_reference_generator.json` で生成
- 既存の `RPG Monster Generator × Scene: Dungeon` で当たりを引いた画像を使う
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
| **Pass 1 (Node 8)** | ControlNet で背景を固定しつつ初期生成 | 1024×1024 / 8 steps / cfg 2.0 / **denoise 1.0** |
| **Pass 2 (Node 20)** | アップスケール後にディテール強化 | 1536×1536 / 1 step / cfg 2.0 / **denoise 0.45** |

Pass 2 は denoise 低めで「線・質感の補強」に徹するので、**Pass 1 の構図・キャラクターを維持しつつ高解像度化**できます。

### パラメータ調整のコツ

#### ノード 6 (Apply ControlNet Advanced)

| パラメータ | 既定値 | 推奨範囲 | 効果 |
| :--- | :---: | :---: | :--- |
| `strength` | `0.6` | `0.45 〜 0.85` | 強い: 背景固定が確実 / 弱い: モンスターの自由度が高い |
| `start_percent` | `0.0` | `0.0` | 最初から効かせる |
| `end_percent` | `0.65` | `0.5 〜 0.85` | 後半は ControlNet 切ってモンスターの細部に集中 |

#### ノード 20 (Pass 2 KSampler) - HiRes Fix

| パラメータ | 既定値 | 推奨範囲 | 効果 |
| :--- | :---: | :---: | :--- |
| `denoise` | `0.45` | `0.35 〜 0.55` | 高い: ディテール強化が強い / 低い: Pass 1 の構図に忠実 |
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
| 背景が固定されない | ControlNet strength が低い | strength を `0.85` まで上げる |
| モンスターが歪む | ControlNet strength が高すぎ | strength を `0.45-0.6` に下げる、または `end_percent` を `0.5` に下げる |
| Pass 2 でディテールが過剰 / 元と違う | denoise が高すぎ | Pass 2 KSampler の denoise を `0.35` 程度に下げる |
| 全体的にボヤける | Pass 1 / Pass 2 の cfg が低すぎ | RPG Generator のスタイル選択を見直す。Anime Cel Shaded は cfg 2.5 |

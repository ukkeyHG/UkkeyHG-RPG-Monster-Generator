# RPG Monster Generator

RPG用のモンスター画像を生成するための ComfyUI カスタムノードです。

## 概要

このツールは、クラシックなダークファンタジーの世界観にマッチした RPG モンスター画像を生成するためのプロンプトを自動構成します。
スタイル・種族・属性・ランク・シーンを選択することで、最適なポジティブ/ネガティブプロンプト + KSampler 推奨値（steps / cfg / sampler / scheduler）を出力します。

## 推奨モデル

> [!IMPORTANT]
> **本ノードは下記モデルでチューニング・検証されています**:
>
> ★ **DreamShaper XL Lightning DPM++ SDE** (`dreamshaperXL_lightningDPMSDE.safetensors`)
>
> - 入手先: https://civitai.com/models/112902/dreamshaper-xl
> - 配置: `ComfyUI/models/checkpoints/`
> - Tier 別の代替候補・非推奨モデル・必要な KSampler Offset 設定は [`REFERENCE_GUIDE.md`](./REFERENCE_GUIDE.md#15-推奨モデルcheckpoint) 参照
>
> 他モデルでも動作はしますが、特に `Juggernaut XL` 系は学習バイアスにより動物→悪魔・骸骨→Death Knight 化が起きやすいので推奨外です。

## 構成

- `rpg_monster_generator.py`: ComfyUI 用のカスタムノード本体。
- `rpg_character_data/`: 種族・属性・ランク・シーンの定義データ。
- `workflows/`: サンプルワークフロー JSON（ControlNet で背景を固定する例など）。
- `REFERENCE_GUIDE.md`: 各設定項目（推奨モデル含む）の詳細解説。
- `CLAUDE.md`: 開発・改造時の設計方針メモ。

## 導入方法

1.  ComfyUI の `custom_nodes` ディレクトリに移動します。
2.  このリポジトリをクローンするか、ファイルを配置します。
    ```bash
    git clone https://github.com/ukkeyHG/UkkeyHG-RPG-Monster-Generator.git
    ```
3.  ComfyUI を再起動すると、`UkkeyHG/RPG` カテゴリに `RPG Monster Generator (UkkeyHG)` ノードが追加されます。
4.  推奨モデル（DreamShaper XL Lightning DPM++ SDE）を `ComfyUI/models/checkpoints/` に配置します。

## 使い方の概要

1.  `Load Checkpoint` ノードで推奨モデルをロード
2.  `RPG Monster Generator (UkkeyHG)` ノードに `clip` を接続
3.  Style / Species / Element / Rank / Scene を選択
4.  Lightning モデル使用時は `steps_offset` / `cfg_offset` を REFERENCE_GUIDE の早見表通りに調整
5.  `KSampler` ノードに各出力を接続して生成

詳細は [`REFERENCE_GUIDE.md`](./REFERENCE_GUIDE.md) 参照。

## 高度な使い方: 背景固定 + HiRes Fix（ControlNet ワークフロー）

属性 (Fire / Ice / Lightning) が背景や床を汚染する問題は、プロンプトのみでは完全には解決できません。確実に背景を固定し、さらに高解像度ディテール強化までを 1 ワークフローでこなすサンプルを用意しています:

- [`workflows/controlnet_dungeon.json`](./workflows/controlnet_dungeon.json) — ControlNet + 4x アップスケール + 2 段サンプリング HiRes Fix
- [`workflows/dungeon_reference_generator.json`](./workflows/dungeon_reference_generator.json) — 上記用の参照ダンジョン背景を生成
- [`workflows/README.md`](./workflows/README.md) — セットアップ手順・依存パッケージ・パラメータ調整方法

### 主な機能
- **ControlNet 背景固定** — 参照画像と同じダンジョン構造でモンスター生成
- **4x アップスケール** — `4x-UltraSharp.pth` で高解像度化
- **HiRes Fix Pass 2** — denoise 0.45 で Pass 1 構図を維持しつつディテール強化
- **Image Comparer** — Pass 1 / Pass 2 をスライダー比較で効果を可視化
- **日付付き自動保存** — `yyyyMMdd_filename_prefix` 形式で出力ファイル管理

### 必要な追加依存（ワークフロー使用時のみ）
- ComfyUI Manager 経由で `comfyui_controlnet_aux` (Fannovel16) と `rgthree-comfy`
- ControlNet モデル（Canny または Depth SDXL）
- アップスケールモデル `4x-UltraSharp.pth`

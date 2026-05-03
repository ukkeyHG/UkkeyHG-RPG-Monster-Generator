import random
import re
from nodes import CLIPTextEncode
from .rpg_character_data.rpg_monster_species_data import MONSTER_SPECIES_DATA
from .rpg_character_data.rpg_monster_element_data import MONSTER_ELEMENT_DATA
from .rpg_character_data.rpg_monster_rank_data import MONSTER_RANK_DATA
from .rpg_character_data.rpg_scene_data import SCENE_DATA


# ComfyUI の KSampler から直接型定義を取得して型ミスマッチを回避する
try:
    import nodes
    # KSampler の入力型定義（リスト）をそのまま取得して「自分の出力型」として利用する
    _ks_input = nodes.KSampler.INPUT_TYPES()["required"]
    SAMPLER_TYPE = _ks_input["sampler_name"][0]
    SCHEDULER_TYPE = _ks_input["scheduler"][0]
except Exception as e:
    # 失敗した場合のフォールバック
    SAMPLER_TYPE = ["euler", "euler_ancestral", "heun", "dpm_2", "dpm_2_ancestral", "lms", "dpm_fast", "dpm_adaptive", "dpmpp_2s_ancestral", "dpmpp_sde", "dpmpp_sde_gpu", "dpmpp_2m", "dpmpp_2m_sde", "dpmpp_2m_sde_gpu", "ddpm", "lcm"]
    SCHEDULER_TYPE = ["normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform"]

# 高品質なスタイルプリセット
# 既定値は推奨モデル `DreamShaper XL Lightning DPM++ SDE` 前提でチューニング:
#   Steps 8 / CFG 1.8〜2.5 / Sampler: dpmpp_sde / Scheduler: karras
# 通常の SDXL モデル（非 Lightning）を使う場合はノードの steps_offset / cfg_offset で
# それぞれ +20〜+27 / +4〜+6 を加算して標準値（30 steps / 6.5〜8 CFG）に戻す。
STYLE_DATA = {
    "Oil Painting": {
        "positive": (
            "Masterpiece dark fantasy oil painting, heavy impasto brushstrokes, realistic paint texture, "
            "moody chiaroscuro lighting, deep shadows, rich dramatic colors, "
            "90s classic high-fantasy RPG manual illustration aesthetic, "
            "extremely detailed, fine art, professional oil on canvas. NO UI, NO TEXT."
        ),
        "negative": "anime, digital, 3d, photo, futuristic, minimalist, bright colors, flat lighting, clean lines",
        "steps": 8,
        "cfg": 2.0,
        "sampler_name": "dpmpp_sde",
        "scheduler": "karras"
    },
    "Cinematic Realistic": {
        "positive": (
            "Cinematic dark fantasy photography, highly detailed monster textures, subsurface scattering, "
            "moody chiaroscuro lighting, volumetric fog, realistic skin, 8k UHD, RAW photo, "
            "hyperrealistic, extremely detailed. NO UI, NO TEXT."
        ),
        "negative": "anime, painting, drawing, illustration, sketch",
        "steps": 8,
        "cfg": 1.8,
        "sampler_name": "dpmpp_sde",
        "scheduler": "karras"
    },
    "Anime Cel Shaded": {
        "positive": (
            "Stylized 2D anime style, clean lineart, flat cel shading, vibrant colors, "
            "vivid high-quality anime illustration, character design sheet aesthetic, crisp edges, "
            "bold colors, simple shading. NO 3D, NO REALISTIC, NO OIL PAINTING, NO TEXTURE, NO TEXT."
        ),
        "negative": (
            "realistic, 3d, photo, oil painting, sketch, messy lines, blurry, distorted, grainy, "
            "detailed texture, realistic skin, noise, canvas texture, heavy brushstrokes"
        ),
        "steps": 8,
        "cfg": 2.5,
        "sampler_name": "dpmpp_sde",
        "scheduler": "karras"
    }
}

def resolve_prompt_variants_with_trace(text):
    if not text: return "", []
    pattern = r"\{([^{}]+)\}"
    selections = []
    def replacer(match):
        choice = random.choice(match.group(1).split("|"))
        selections.append(choice)
        return choice
    return re.sub(pattern, replacer, text), selections


def resolve_categorized_entry(entry, category):
    """
    Rank などのカテゴリ別プロンプトを解決する。
    entry が dict で 'by_category' キーを持つ場合、種族カテゴリで引いて該当プロンプトを返す。
    該当カテゴリが無ければ 'default' にフォールバック。
    それ以外（プレーン文字列、または通常の dict）はそのまま返す。
    """
    if isinstance(entry, dict) and "by_category" in entry:
        return entry["by_category"].get(category, entry.get("default", ""))
    return entry


def resolve_rank_prompt(species_entry, rank_name, rank_entry, category):
    """
    Rank プロンプトを優先順位付きで解決する:
      1. 種族固有 rank_overrides[rank_name]  ← 最優先（特殊種族の脱出ハッチ）
      2. カテゴリ別 by_category[category]    ← 通常
      3. default                              ← フォールバック
      4. プレーン文字列はそのまま
    """
    # 1. species-level override (highest priority)
    if isinstance(species_entry, dict):
        overrides = species_entry.get("rank_overrides", {})
        if rank_name in overrides:
            return overrides[rank_name]
    # 2-4. fall through to category resolution
    return resolve_categorized_entry(rank_entry, category)

class RPGMonsterGenerator:
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # 毎回違う値を返して ComfyUI のノードキャッシュを無効化する。
        # これにより Queue Prompt のたびに generate_prompt が再実行され、
        # プロンプト中の {a|b|c} バリアント（武器・ポーズ・装備等）が毎回新しく抽選される。
        return random.random()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP",),
                "style": (list(STYLE_DATA.keys()),),
                "species": (list(MONSTER_SPECIES_DATA.keys()),),
                "element": (list(MONSTER_ELEMENT_DATA.keys()),),
                "rank": (list(MONSTER_RANK_DATA.keys()),),
                "scene": (list(SCENE_DATA.keys()),),
                "steps_offset": ("INT", {"default": 0, "min": -30, "max": 30, "step": 1}),
                "cfg_offset": ("FLOAT", {"default": 0.0, "min": -10.0, "max": 10.0, "step": 0.1}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "CONDITIONING", "CONDITIONING", "INT", "FLOAT", SAMPLER_TYPE, SCHEDULER_TYPE, "STRING")
    RETURN_NAMES = (
        "positive_text", 
        "negative_text", 
        "conditioning_positive", 
        "conditioning_negative",
        "steps",
        "cfg",
        "sampler_name",
        "scheduler",
        "filename_prefix"
    )
    FUNCTION = "generate_prompt"
    CATEGORY = "UkkeyHG/RPG"

    def generate_prompt(self, clip, style, species, element, rank, scene, steps_offset, cfg_offset):
        # 種族のカテゴリを引いて Rank をカテゴリ別プロンプトに解決
        # 優先順位: species.rank_overrides > Rank.by_category > Rank.default > 文字列素通し
        species_entry = MONSTER_SPECIES_DATA[species]
        species_category = species_entry.get("category", "default") if isinstance(species_entry, dict) else "default"
        rank_entry = resolve_rank_prompt(species_entry, rank, MONSTER_RANK_DATA[rank], species_category)

        # データの役割に応じた順序付け
        order = [
            species_entry,                 # 本体
            MONSTER_ELEMENT_DATA[element], # 属性装飾
            rank_entry,                    # 格付け/威圧感/個性（カテゴリ別解決済み）
            SCENE_DATA[scene]              # 背景舞台
        ]

        resolved_positives = []
        # 基本的なネガティブセット（枠線・文字・署名抑制）
        # 意図的に外しているもの:
        #   - woman: 性別は種族プロンプトで制御
        #   - photo: Cinematic Realistic スタイルの "RAW photo" を殺さないため。各非写実スタイルの negative 側に photo を持たせている
        #   - pedestal/platform/table 等: Gargoyle "perched on a gothic pedestal" や Vampire "seated on a gothic throne" を殺さないため。台座に乗らないべき種族（Slime 等）の側で個別に抑制
        resolved_negatives = [
            "modern, sci-fi, "
            "closeup, portrait, headshot, bust, macro, cropped face, "
            "frame, border, boxed, picture frame, cropping, margins, bleed, canvas frame, "
            "text, watermark, signature, letters, artist name, logo, words, digits"
        ]
        all_selections = []

        for entry in order:
            p, n = ("", "")
            if isinstance(entry, dict):
                p, n = entry.get("prompt", ""), entry.get("negative_prompt", "")
            else:
                p = str(entry)
            
            if p:
                res, sel = resolve_prompt_variants_with_trace(p)
                resolved_positives.append(res)
                all_selections.extend(sel)
            if n:
                res_n, _ = resolve_prompt_variants_with_trace(n)
                resolved_negatives.append(res_n)

        # 選択されたスタイル設定を取得
        style_config = STYLE_DATA.get(style, STYLE_DATA["Oil Painting"])
        style_positive = style_config["positive"]
        style_negative = style_config["negative"]
        
        # KSampler 推奨値 + オフセット適用
        steps = max(1, style_config["steps"] + steps_offset)
        cfg = max(0.0, style_config["cfg"] + cfg_offset)
        sampler_name = style_config["sampler_name"]
        scheduler = style_config["scheduler"]

        # パラメータ設計の再構築：
        # 1. スタイル(画風)を最優先(先頭)にする
        # 2. 種族以下をカンマで結合
        # 3. 画風と内容をピリオドで区切る
        content_prompt = ", ".join(filter(None, resolved_positives))
        final_positive = f"{style_positive} {content_prompt}"
        
        # スタイル固有のネガティブがある場合は追加
        if style_negative:
            resolved_negatives.insert(0, style_negative)

        final_negative = ", ".join(filter(None, resolved_negatives))

        # Encode prompts
        encoder = CLIPTextEncode()
        encoded_positive = encoder.encode(clip, final_positive)[0]
        encoded_negative = encoder.encode(clip, final_negative)[0]

        # filename_prefix: 全小文字・スペースは _ に置換（例: bat_dark_elite, giant_worm_fire_boss）
        prefix = "_".join(s.lower().replace(" ", "_") for s in (species, element, rank))

        return (
            final_positive, 
            final_negative, 
            encoded_positive, 
            encoded_negative,
            steps,
            cfg,
            sampler_name,
            scheduler,
            prefix
        )

NODE_CLASS_MAPPINGS = {"UkkeyHG-RPG-Monster-Generator": RPGMonsterGenerator}
NODE_DISPLAY_NAME_MAPPINGS = {"UkkeyHG-RPG-Monster-Generator": "RPG Monster Generator (UkkeyHG)"}




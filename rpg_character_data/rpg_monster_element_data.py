# rpg_monster_element_data.py
#
# === prompt の方針（最重要） ===
# 属性は「モンスター本体に乗っているもの」 + 「体全体（体毛・皮膚を含む）の色を属性色に塗り替える」
# の2層を最強ウェイトで主張する。何もしないと AI は種族のデフォルト色（コウモリ=茶色、狼=灰色 等）
# を優先し、塗りやすい部位（翼膜など）だけ部分塗布で済ませてしまう。
#
# 4 層ウェイト構造:
#   (:1.5) 体毛・皮膚を含む全身の色塗り替え   ← "fur, skin, and body deeply colored ..."
#   (:1.5) 体本体への完全エフェクト被覆       ← "body completely engulfed/wrapped in ..."
#   (:1.4) 体全体の染色詳細
#   (:1.3) 体表エフェクト
#   (:1.0) 補助記述                            ← グロー・霧・粒子など
#
# 環境記述（"surroundings filled with..." / "surrounded by..."）は使わない。
# 周囲記述は AI が属性を背景に逃がす原因になる（例: 炎の上を飛ぶコウモリ、床の焚火）。
# 動詞は「wrapped/covering/engulfed/blanket/every inch」など本体を完全包囲する語を使う。
#
# === negative_prompt の方針 ===
# 汎用的な色名/材質名（red, blue, green, light, flesh 等）はシーンや種族のポジティブを
# 打ち消してしまうので使わない。「対義属性のエフェクトがモンスター本体に乗ると
# おかしいもの」を narrow に列挙する（例: Fire なら "icicles, frost coating"）。

MONSTER_ELEMENT_DATA = {
    "None": {
        "prompt": "",
        "negative_prompt": ""
    },
    "Fire": {
        "prompt": "(creature's entire fur, skin, and body tinted with crimson red and ember orange highlights:1.2), (the creature's body wrapped in burning flames on the body only:1.3), (surfaces of the body tinted with fiery red and ember orange:1.2), glowing red-hot accents with molten cracks across the body, heat haze rising from the body itself",
        "negative_prompt": "icicles, frost coating, snow on creature, freezing breath, natural brown fur, natural gray fur, fire on the ground only, campfire on floor, embers scattered on the floor, lava puddles on the ground, fire pits on the floor, flames coming from the ground, fire spreading from the body to the floor, flame trails on the dungeon floor, fire growing on the walls, outdoor volcanic landscape, lava field background, burning forest outside, outdoor wildfire scene, scene replaced by lava environment"
    },
    "Ice": {
        "prompt": "(creature's entire fur, skin, and body deeply colored pale ice blue and frosty white:1.4), (smooth thick ice glaze coating only the body surface:1.4), (every surface of the body deeply tinted icy pale blue and white:1.3), frozen blue glow across the skin, smooth icy coating on the body, frosty breath puffing from the mouth, frozen aura clinging tightly to the body",
        "negative_prompt": "flames on body, scorched skin, smoldering embers, lava splashes on creature, natural warm fur tones, ice crystals on the ground, ice spikes growing from the floor, icicles on the dungeon floor, frost patches on the floor, ice formations on the ground around the creature, frozen patches on the dungeon floor, ice scattered around the creature, ice growths spreading from the body, frost grass growing from the floor, ice tendrils, ice vines, frost vines, ice plants, frozen growths on the walls, ice spreading across the dungeon, white feathery ice growths around the creature, outdoor snowy landscape, snowy forest, snowy village houses, snow-covered houses, winter wonderland, snowy mountains outdoors, blizzard outdoors, frozen lake outdoors, snow falling on the ground, outdoor winter scene, scene replaced by snowy environment"
    },
    "Poison": {
        "prompt": "(creature's entire fur, skin, and body deeply colored sickly green and necrotic purple:1.5), (the creature's body completely oozing and dripping with toxic sludge on the body surface only:1.5), (every surface of the body deeply tinted toxic green and bruised purple:1.4), sickly neon green glow across the skin, necrotic purple veins visible on the body, dripping poison from the body only, toxic mist clinging tightly to the body",
        "negative_prompt": "holy radiance, divine purification, sterile blessed aura, healthy natural skin tone, poison puddles on the ground, toxic spills on the floor, poison clouds on the floor, outdoor toxic swamp, poison forest landscape, outdoor green poisonous field, scene replaced by swamp"
    },
    "Lightning": {
        "prompt": "(creature's entire fur, skin, and body deeply colored electric blue and crackling cyan:1.5), (the creature's body completely covered in arcing electric currents on the body surface only:1.5), (every surface of the body deeply tinted vivid electric blue and crackling cyan:1.4), cyan lightning streaks across the skin, sparks emitting from the body only, glowing blue veins of lightning on the creature, electrified aura clinging tightly to the form",
        "negative_prompt": "flame burst on body, watery surface, completely calm still atmosphere, natural matte fur, sparks on the floor, lightning bolts on the ground, electrical arcs on the floor, lightning patterns on the dungeon floor, outdoor stormy sky, lightning strikes filling the sky, outdoor thunderstorm landscape, scene replaced by stormy environment"
    },
    "Dark": {
        "prompt": "(creature's entire fur, skin, and body deeply colored pitch black and shadow purple:1.5), (the creature's body completely wrapped in shadowy black aura on the body surface only:1.5), (every surface of the body deeply tinted deep void black and dark violet:1.4), dark mist clinging tightly to the skin, swirling purple void energy on the body only, abyssal silhouette, glowing dark eyes, shadow tendrils emanating from the body only",
        "negative_prompt": "holy halo, divine angelic aura, shining sun rays on creature, bright natural fur, shadow puddles on the floor, dark patches on the ground, void cracks on the floor, outdoor void abyss landscape, abyssal cosmic background, scene replaced by void environment"
    },
    "Light": {
        "prompt": "(creature's entire fur, skin, and body deeply colored radiant gold and pearlescent white:1.5), (the creature's body completely radiating golden divine light on the body surface only:1.5), (every surface of the body deeply tinted shining golden and luminous white:1.4), glowing white highlights on the skin, halo of holy light around the creature only, celestial luminescence emanating from the body within, sacred glow on the body",
        "negative_prompt": "demonic shadow tendrils, void corruption marks, abyssal mist on creature, dull dark fur, light spots on the floor, glowing patches on the ground, light beams on the dungeon floor, outdoor heavenly cloud landscape, divine sky outdoors, scene replaced by celestial heaven, bright sky background"
    },
    "Metal": {
        "prompt": "(creature's entire fur, skin, and body replaced with polished chrome silver on the body surface only:1.5), (the creature's body completely covered in shiny liquid metal surface:1.5), (every surface of the body replaced with reflective metallic plating:1.4), mirror-like reflective skin, chrome metallic sheen on the entire body, cold steel texture covering the creature, hardened plating fused to the form",
        "negative_prompt": "cloth fabric robes, paper texture, rotting flesh wounds, soft organic fur, metal shards on the floor, metallic scraps on the ground, metal plating on the dungeon floor, industrial factory background, sci-fi metal environment, scene replaced by metallic facility"
    }
}

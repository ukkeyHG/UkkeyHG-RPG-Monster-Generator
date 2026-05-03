# rpg_scene_data.py
#
# === Scene プロンプトの方針 ===
# Scene はプロンプトの末尾に置かれるので、重みなしでは Element/Rank に押し負ける。
# 種族 (:1.5) や属性 (:1.5) と渡り合うために 3 層ウェイト構造を採用:
#   (:1.4) 背景の本質宣言       ← "set in a ... background"
#   (:1.3) 視覚要素を背景固定   ← "in the background" を明示してモンスター本体に乗らないように
#   (:1.0) 補助記述             ← 雰囲気・小道具
#
# negative_prompt は「他シーンに化けるのを防ぐ」役割。属性とのクロス汚染も意識する
# （例: Dungeon に Fire 属性が乗ったとき、AI が "Lava Cave" 化させないよう
# `lava, natural cave, volcanic cavern` を明示的に拒否）。

SCENE_DATA = {
    "Dungeon": {
        "prompt": "(set in a dark medieval stone dungeon indoor environment as the background:1.5), (gothic stone block walls and rusty iron prison bars in the background:1.4), grimy stone bricks covered in moss and damp, (clean dry indoor stone floor with deep cracks and no element decorations on the floor:1.3), wall-mounted torches on stone walls in the distant background, chains hanging from the walls, ancient gothic prison indoor atmosphere",
        "negative_prompt": "outdoor scene, outside, open sky, forest, bright sunlit room, lava, magma, volcanic cavern, natural cave, beach, desert, campfire on floor, fire pit on the ground, bonfire, embers on the dungeon floor, snow on the ground, snowy outdoor scene, winter outdoor village, snowy houses, frozen outdoor lake, blizzard, falling snow, ice crystals on the dungeon floor, ice spikes growing from the stone floor, icicles on the floor, frost patches on the floor, outdoor stormy weather, lightning strikes in the sky, sparks on the floor, sunny outdoor day, trees, grass, mountains in the background, plants growing on the floor, glowing patches on the floor, decorative element effects scattered on the dungeon floor"
    },
    "Lava Cave": {
        "prompt": "(set in a subterranean volcanic cavern as the background:1.5), (flowing rivers of molten lava and glowing cracks in the background:1.4), dark basalt rock walls, ambient red heat glow, cracked volcanic stone floor, ember particles drifting in the air",
        "negative_prompt": "forest, ocean, winter, ice, snow, snowy outdoor village, dungeon prison bars, throne room, open sky, outdoor stormy weather"
    },
    "Ice Vault": {
        "prompt": "(set in an ancient frozen indoor burial chamber as the background:1.5), (blue ice walls and frost-covered stone pillars in the background:1.4), crystalline ice surface indoors, frozen mist hovering on the floor, ornate frozen sarcophagi visible behind, pale blue ambient light, indoor frozen tomb atmosphere",
        "negative_prompt": "outdoor snowy landscape, snowy outdoor village, snowy outdoor mountains, blizzard outdoors, desert, sun, fire, lava, dungeon prison bars, forest, throne room, magma, open sky, falling snow outdoors"
    },
    "Graveyard": {
        "prompt": "(set in an underground catacomb indoor environment as the background:1.5), (rows of ancient skulls in stone niches and dusty sarcophagi in the background:1.4), dusty stone walls with bone alcoves, dim flickering candlelight, cobwebs hanging from the ceiling, indoor sacred burial atmosphere",
        "negative_prompt": "outdoor cemetery, outdoor graveyard with grass, town, bright daytime, modern building, lava, ice, throne room, forest, open sky, snowy outdoor scene, outdoor stormy weather"
    },
    "Throne Room": {
        "prompt": "(set in a ruined gothic indoor throne hall as the background:1.5), (massive ornate stone throne and tattered royal tapestries in the background:1.4), cracked marble floor with debris, dim shafts of light from broken stained glass windows, faded royal banners, abandoned regal indoor atmosphere",
        "negative_prompt": "simple room, kitchen, lava, natural cave, forest, dungeon prison bars, ice, outdoor scene, snowy outdoor, outdoor stormy weather, open sky, outdoor castle exterior"
    },
    "Transparent (White)": {
        "prompt": "(isolated on a pure solid white background:1.5), (clean studio product photography lighting:1.4), plain white backdrop with no environment, centered composition, high contrast clean edges, no ground, no horizon",
        "negative_prompt": "shadows on background, ground, floor, landscape, horizon, outdoors, messy, blurry background, depth of field, cave wall, stone wall, dungeon, sky, forest, lava, snow, ice, weather effects"
    }
}

import random


NEGATIVE_WATERMARK_BLOCKERS = [
    "watermark",
    "logo",
    "text",
    "signature",
    "letters",
    "trademark",
    "copyright",
    "stamp",
    "URL",
    "website",
    "username",
]


def merge_negative_prompt_tags(base_prompt=None, *tag_groups):
    watermark_keys = {tag.lower() for tag in NEGATIVE_WATERMARK_BLOCKERS}
    merged_tags = []
    seen_keys = set()

    def add_group(group):
        if not group:
            return
        items = group.split(",") if isinstance(group, str) else group
        for item in items:
            text = str(item).strip()
            if not text or text == "-":
                continue
            key = text.lower()
            if key in watermark_keys or key in seen_keys:
                continue
            seen_keys.add(key)
            merged_tags.append(text)

    add_group(base_prompt)
    for tag_group in tag_groups:
        add_group(tag_group)

    merged_tags.extend(NEGATIVE_WATERMARK_BLOCKERS)
    return ", ".join(merged_tags) if merged_tags else ", ".join(NEGATIVE_WATERMARK_BLOCKERS)


def get_sorted_list(original_list):
    if original_list is None:
        return []
    values = list(original_list)
    specials = [x for x in values if x in ["None", "Random"]]
    rest = [x for x in values if x not in ["None", "Random"]]
    return specials + sorted(rest, key=lambda item: str(item).lower())


# --- DATA CONSTANTS (Ported from the Web App) ---

Anatomie_Liste = [
    "None", "alraune", "amorphous", "amphibian", "anthro", "anthropomorphic", "arachnid",
    "arthropod", "centaur", "centauroid", "cervitaur", "cyborg", "deer taur", "dragon taur",
    "elemental", "feral", "flora", "gelatinous", "horse taur", "human", "humanoid",
    "insect girl", "insectoid", "lamia", "lion taur", "mechanical", "mermaid", "merfolk",
    "merman", "naga", "partially anthro", "plant", "quadruped", "robot", "semi-anthro",
    "skeleton", "slime", "snake lower body", "spider girl", "taur", "tiger taur", "undead", "zombie"
]

Spezies_Liste = [
    "None", "alligator anthro", "angel", "ant girl", "anthro bear", "anthro cat", "anthro fox",
    "anthro horse", "anthro hyena", "anthro lion", "anthro rabbit", "anthro tiger", "anthro wolf",
    "avian", "bat anthro", "bee girl", "bipedal wolf", "bird anthro", "bull anthro", "bunnygirl",
    "catgirl", "celestial", "cephalopod", "crocodile anthro", "demon", "draconic anthro",
    "dragon anthro", "dragonkin", "drake", "equine anthro", "fallen angel", "faun", "fish anthro",
    "goat anthro", "goblin", "griffin anthro", "gryphon", "harpy", "hobgoblin", "incubus",
    "inari", "infernal", "kappa", "kitsune", "lizardman", "lycanthrope", "minotaur", "nekomata",
    "octopus", "oni", "orc", "reptilian anthro", "satyr", "serpent", "shark anthro", "snake anthro",
    "sphinx", "succubus", "tanuki", "tengu", "tentacle anthro", "tiefling", "tiger taur", "troll",
    "vampire", "werebear", "werecat", "werefox", "werehorse", "werehyena", "werelion", "wererabbit",
    "weretiger", "werewolf"
]

# Erst eine echte Liste für das Geschlecht erstellen:
Echtes_Geschlecht_Liste = ["None", "male", "female", "hermaphrodite", "androgynous"]

# Jetzt die Variablen richtig an das Interface übergeben:
GENDERS = Echtes_Geschlecht_Liste
ALL_BODY_TYPES = Spezies_Liste + Anatomie_Liste


RATINGS = ["rating_safe", "rating_questionable", "rating_explicit"]

PHOTO_BOOST_POTION = (
    "masterpiece, highly detailed, award-winning illustration, vibrant colors, "
    "realistic heavy muscle shading, cinematic lighting, masterfully integrated, "
    "sharp focus, volumetric lighting, rich textures"
)

SCORE_SCHEMES = [
    "default high",          # score_9, score_8_up, score_7_up, score_6_up
    "score_9 only",          # score_9
    "score_7_plus",          # score_9, score_8_up, score_7_up
]

SOURCE_TAGS = [
    "None",
    "source_photography",
    "source_pony",
    "source_furry",
    "source_anime",
    "source_cartoon",
]

STYLE_PRESETS = [
    "None",
    "photorealistic",
    "anime_leaning",
    "sketch",
    "studio_glamour",
]

AGES = ["18", "20", "25", "30", "35", "40", "45", "50", "60", "MILF", "mature", "Random"]

ETHNICITIES = [
    "Caucasian", "Japanese", "Korean", "Chinese", "African American", "Nubian",
    "Latino", "Scandinavian", "Italian", "Russian", "Middle Eastern", "South Asian",
    "Native American", "Pacific Islander", "Mixed Race", "Pale-skinned", "Dark-skinned",
    "None", "Random"
]

SKIN_TYPES = [
    "None",
    "smooth skin",
    "soft skin",
    "shiny skin",
    "wet skin",
    "pale skin",
    "fair skin",
    "tan skin",
    "dark skin",
    "olive skin",
    "freckled skin",
    "textured skin with pores",
    "oily skin",
    "sweaty skin",
    "goosebumps",
    "sun-damaged skin",
    "wrinkled skin",
    "light skin",
    "brown skin",
    "black skin",
]

SPECIAL_SKIN_TYPES = [
    "None",
    "fluffy fur",
    "thick fur",
    "short fur",
    "rough fur",
    "wet fur",
    "shaggy fur",
    "spotted fur",
    "striped fur",
    "smooth scales",
    "reptilian scales",
    "dragon scales",
    "soft feathers",
    "glossy feathers",
]

HAIR_COLORS = [
    "Random",
    "blonde", "platinum_blonde", "platinum blonde", "dirty blonde", "brunette", "brown_hair",
    "black", "black_hair", "raven black", "red", "red_hair", "ginger", "auburn",
    "white", "white_hair", "silver", "silver_hair", "grey", "grey_hair",
    "blue_hair", "green_hair", "pink_hair", "pastel pink", "neon blue", "purple",
    "azure_hair", "aqua_hair", "ruby_hair", "rainbow_hair", "rainbow",
    "multicolored_hair", "two-tone_hair", "two-tone", "ombre", "gradient_hair",
    "streaked_hair", "dyed_hair"
]

EYE_COLORS = [
    "Random",
    "blue", "blue_eyes", "ice blue", "green", "green_eyes", "emerald", "brown", "brown_eyes",
    "hazel", "grey", "grey_eyes", "amber", "red", "red_eyes", "purple", "purple_eyes",
    "heterochromia", "glowing eyes", "closed eyes", "half-closed eyes",
    "aqua_eyes", "gold_eyes", "yellow_eyes", "pink_eyes", "black_eyes"
]

# Pony/Danbooru tag lists (male + female) for ComfyUI dropdowns — SDXL Pony recognized
ALL_HAIRSTYLES = [
    "Random",
    "straight_hair", "curly_hair", "wavy_hair", "long straight", "long wavy",
    "messy_hair", "messy bun", "bob cut", "inverted_bob", "princess_cut", "princess_head", "bowl_cut",
    "hime cut", "hime_cut", "hair_flaps", "bangs", "air_bangs", "blunt_bangs", "side_blunt_bangs",
    "centre parting bangs", "swept bangs", "swept_bangs", "asymmetric bangs", "braided_bangs",
    "ponytail", "twintails", "twin tails", "short_ponytail", "side_ponytail", "high_ponytail",
    "low_twintails", "short_twintails", "uneven_twintails", "tri_tails", "quad_tails", "quin_tails",
    "tied_hair", "low_tied_hair", "multi-tied_hair", "braid", "french_braid", "braiding_hair",
    "braided ponytail", "twin_braids", "short_braid", "long_braid", "braided_bun", "braided_ponytail",
    "crown_braid", "multiple_braids", "side_braid", "hair_bun", "double_bun", "single_hair_bun",
    "ballet_hair_bun", "doughnut_hair_bun", "heart_hair_bun", "triple_bun", "cone_hair_bun",
    "half_updo", "half_up_braid", "half_up_half_down_braid", "pointy_hair", "feather_hair",
    "bow-shaped_hair", "lone_nape_hair", "shag haircut", "ahoge", "heart_shaped_ahoge",
    "star_shaped_ahoge", "antenna_hair", "sideburns", "long_sideburns", "sidelocks",
    "hair_over_one_eye", "hair_over_eyes", "shaved side", "undercut", "afro", "huge_afro",
    "spiked_hair", "dreadlocks", "cornrows", "boxing_braids", "mullet", "pompadour", "quiff",
    "messy quiff", "short curly", "ringlets", "crew cut", "buzz cut", "flattop", "fade",
    "man bun", "bald", "hair_slicked_back", "slicked back", "side part", "hair_pulled_back",
    "hair_comb_over", "very_short_hair", "very_long_hair", "absurdly_long_hair", "wolf cut",
    "wolf_cut", "mohawk", "chonmage", "okappa", "front_braid", "front_ponytail", "low_twin_braids",
    "tri_braids", "quad_braids", "japari_bun", "arched_bangs", "asymmetrical_bangs",
    "bangs_pinned_back", "crossed_bangs", "choppy_bangs", "diagonal_bangs", "dyed_bangs",
    "fanged_bangs", "long_bangs", "parted_bangs", "curtained_hair", "wispy_bangs", "short_bangs",
    "hair_between_eyes", "sidelocks_tied_back", "single_sidelock", "widow's peak", "huge_ahoge",
    "hair_intakes", "single_hair_intake", "asymmetrical_sidelocks", "drill_sidelocks",
    "low-tied_sidelocks", "drill_hair", "twin_drills", "tri_drills", "beehive_hairdo",
    "flower_shaped_hair", "twisted_hair", "ooseledets", "hair_scarf", "one_side_up",
    "two_side_up", "low_braided_long_hair", "low_tied_long_hair", "mizura", "nihongami",
    "folded_ponytail", "split_ponytail", "star-shaped_hair", "shiny_hair", "glowing_hair",
    "liquid_hair", "crystal_hair", "translucent_hair", "polka_dot_hair", "tentacle_hair",
    "hair_vines", "split-color_hair", "hair_half_undone", "ruffling_hair", "expressive_hair",
    "bouncing_hair", "flipped_hair", "hair_rings", "single_hair_ring", "long flowing", "updo",
    "short textured"
]

# Simple gendered views over ALL_HAIRSTYLES.
FEMALE_HAIRSTYLES = [
    "Random",
    "long straight", "long wavy", "messy_hair", "messy bun", "bob cut", "inverted_bob",
    "princess_cut", "princess_head", "hime cut", "hime_cut",
    "ponytail", "twintails", "twin tails", "short_ponytail", "side_ponytail", "high_ponytail",
    "low_twintails", "short_twintails", "uneven_twintails",
    "braid", "french_braid", "braiding_hair", "braided ponytail", "twin_braids",
    "long_braid", "braided_bun", "braided_ponytail", "crown_braid", "multiple_braids",
    "side_braid", "hair_bun", "double_bun", "single_hair_bun", "ballet_hair_bun",
    "doughnut_hair_bun", "heart_hair_bun", "triple_bun", "cone_hair_bun",
    "half_updo", "half_up_braid", "half_up_half_down_braid",
    "arched_bangs", "asymmetrical_bangs", "bangs_pinned_back", "choppy_bangs",
    "curtained_hair", "wispy_bangs", "long_bangs", "short_bangs",
    "hair_between_eyes", "sidelocks_tied_back", "single_sidelock",
    "long flowing", "updo", "short textured", "shag haircut",
]

MALE_HAIRSTYLES = [
    "Random",
    "short textured", "short curly", "crew cut", "buzz cut", "flattop", "fade",
    "mullet", "pompadour", "quiff", "messy quiff",
    "man bun", "bald", "hair_slicked_back", "slicked back", "side part",
    "undercut", "shaved side", "spiked_hair",
]

FULL_OUTFITS = [
    "Random", "None",
    "nude", "lingerie", "lace underwear", "bikini", "micro bikini", "one-piece swimsuit",
    "shell_bikini", "frilled_swimsuit", "front_zipper_swimsuit", "bikesuit", "wrestling_outfit",
    "evening_gown", "evening gown", "cocktail_dress", "cocktail dress", "gown", "wedding_dress",
    "canonicals", "sundress", "summer dress", "sleeveless_dress", "strapless_dress", "backless_dress",
    "halter_dress", "sailor_dress", "pinafore_dress", "frilled_dress", "sweater_dress",
    "pleated_dress", "pencil_dress", "cheongsam", "china_dress", "off-shoulder_dress",
    "armored_dress", "fur-trimmed_dress", "lace-trimmed_dress", "collared_dress", "layered_dress",
    "multicolored_dress", "striped_dress", "polka_dot_dress", "plaid_dress",
    "print_dress", "ribbed_dress", "short_jumpsuit", "maid", "miko", "school_uniform", "sailor",
    "serafuku", "sailor_senshi_uniform", "summer_uniform", "naval_uniform", "military_uniform",
    "business_suit", "business suit", "nurse", "chef_uniform", "labcoat", "cheerleader",
    "band_uniform", "space_suit", "leotard", "hanbok", "japanese_clothes",
    "chinese_style", "traditional_clothes", "uchikake", "sleeveless_kimono", "print_kimono",
    "hanten_(clothes)", "korean_clothes", "gothic", "lolita", "gothic_lolita", "byzantine_fashion",
    "tropical cloth", "indian_style", "Ao_Dai", "ainu_clothes", "arabian_clothes", "egyptian_clothes",
    "hawaii costume", "furisode", "animal_costume", "bunny_costume", "cat_costume", "santa_costume",
    "yukata", "hanfu", "Taoist robe", "robe", "cloak", "hooded_cloak", "winter_clothes",
    "down jacket", "halloween_costume", "loungewear", "harem_outfit", "gym_uniform",
    "athletic_leotard", "volleyball_uniform", "tennis_uniform", "baseball_uniform",
    "letterman_jacket", "biker_clothes", "tuxedo", "tailored suit", "latex bodysuit",
    "mechanic jumpsuit", "streetwear", "casual", "cyberpunk techwear"
]

TOP_CLOTHING = [
    "Random", "None",
    "t-shirt", "blouse", "off-shoulder_shirt", "collared_shirt", "collared shirt", "dress_shirt",
    "sailor_shirt", "cropped_shirt", "criss-cross_halter", "frilled_shirt", "sweatshirt",
    "hawaiian_shirt", "kappougi", "polo_shirt", "polo shirt", "print_shirt", "sleeveless_hoodie",
    "sleeveless_shirt", "striped_shirt", "tank_top", "tank top", "vest", "waistcoat", "cardigan",
    "sweater", "virgin killer sweater", "hooded_sweater", "striped_sweater", "pullover_sweaters",
    "ribbed_sweater", "sweater_vest", "backless_sweater", "blazer", "overcoat", "double-breasted",
    "long_coat", "winter_coat", "hooded_coat", "fur_coat", "fur-trimmed_coat", "duffel_coat",
    "parka", "cropped_jacket", "track_jacket", "hooded_track_jacket", "military_jacket",
    "camouflage_jacket", "leather_jacket", "leather jacket", "trench_coat", "windbreaker",
    "raincoat", "tunic", "cape", "capelet", "hagoromo", "lab coat", "biker vest",
    "crop_top", "sports_bra", "tube_top", "halter_top", "bustier", "corset", "hoodie",
    "zipper_jacket", "denim_jacket", "puffer_jacket", "sleeveless_turtleneck", "turtleneck_sweater",
    "off_shoulder_sweater", "graphic_tshirt", "logo_tshirt",
    # Additional common Danbooru-style tops
    "open_shirt", "unbuttoned_shirt", "see-through_shirt", "wet_shirt",
    "white_shirt", "black_shirt", "striped_t-shirt", "graphic_t-shirt",
    "off_shoulder_top", "cropped_hoodie", "hood_down", "hood_up",
    "sleeveless_sweater", "ribbed_tank_top", "sports_jacket", "jersey"
]

FEMALE_TOP_CLOTHING = [
    "Random", "None",
    "blouse", "off-shoulder_shirt", "cropped_shirt", "criss-cross_halter",
    "frilled_shirt", "virgin killer sweater", "backless_sweater",
    "crop_top", "sports_bra", "tube_top", "halter_top", "bustier", "corset",
    "off_shoulder_sweater", "sleeveless_sweater", "ribbed_tank_top",
]

MALE_TOP_CLOTHING = [
    "Random", "None",
    "t-shirt", "dress_shirt", "collared_shirt", "collared shirt", "sailor_shirt",
    "polo_shirt", "polo shirt", "sweatshirt", "hawaiian_shirt",
    "track_jacket", "hooded_track_jacket", "military_jacket",
    "letterman_jacket", "sports_jacket", "jersey",
]

BOTTOM_CLOTHING = [
    "Random", "None",
    "skirt", "miniskirt", "mini_skirt", "skirt_suit", "bikini_skirt",
    "pleated_skirt", "pencil_skirt", "bubble_skirt", "tutu", "ballgown", "denim_skirt",
    "suspender_skirt", "long_skirt", "high-waist_skirt", "chiffon_skirt", "lace_skirt",
    "layered_skirt", "print_skirt", "flared_skirt", "floral_skirt", "jumpsuit", "hot_pants",
    "striped_shorts", "suspender_shorts", "denim_shorts", "puffy_shorts", "dolphin_shorts",
    "tight pants", "yoga pants", "track_pants", "bike_shorts", "gym_shorts", "pants",
    "puffy_pants", "pumpkin_pants", "hakama", "hakama_pants", "harem_pants", "bloomers", "buruma",
    "jeans", "cargo_pants", "camouflage_pants", "capri_pants", "chaps", "plaid_pants",
    "striped_pants", "torn_jeans", "boxers", "briefs", "swim trunks", "loincloth",
    "leggings", "fishnet_pantyhose", "ripped_jeans", "short_shorts", "yoga_shorts",
    "denim_cutoffs", "thigh_straps", "garter_straps",
    # Additional Danbooru-style bottoms and legwear
    "booty_shorts", "low_rise_shorts", "high-waist_shorts", "tight_shorts",
    "striped_thighhighs", "vertical-striped_thighhighs", "polka_dot_thighhighs",
    "ripped_leggings", "sheer_pantyhose", "patterned_pantyhose",
    "striped_panties", "lacy_panties", "thong", "g-string"
]

HEADWEAR = [
    "Random", "None",
    "helmet", "kabuto", "hat", "beret", "baseball cap", "sun hat", "headband",
    "hairband", "tiara", "crown", "veil", "hood", "hood_up", "headphones",
    "beanie", "newsboy_cap", "cowboy_hat", "straw_hat", "witch_hat", "wizard_hat",
    "ribbon_in_hair", "hair_ribbon",
    # Additional common head items
    "hair_ornament", "hair_flower", "flower_crown", "laurel_wreath",
    "nurse_cap", "maid_headdress", "military_hat", "police_hat",
    "beret_with_badge", "animal_ears_hat", "cat_ears_hood", "bunny_ears_hood"
]

FOOTWEAR = [
    "Random", "None",
    "barefoot", "sandals", "flip_flops", "sneakers", "running shoes", "boots", "thigh_boots",
    "knee_high_boots", "ankle_boots", "loafers", "high_heels", "stilettos", "platform_shoes",
    "mary_janes", "combat_boots", "lace_up_boots", "thighhigh_boots", "wedge_heels",
    # Additional footwear / legwear tags
    "geta", "zori", "school_shoes", "heels", "platform_boots",
    "open_toe_sandals", "ankle_strap_heels", "knee_socks", "thighhigh_socks",
    "mismatched_socks", "striped_socks"
]

ACCESSORIES = [
    "Random", "None",
    "fishnets", "thighhighs", "stockings", "pantyhose", "garter_belt",
    "arm warmers", "fingerless gloves", "gloves", "scarf", "necktie", "bowtie",
    "choker", "necklace", "bracelet", "ring", "earrings", "sunglasses",
    "goggles", "backpack", "messenger bag", "belt", "harness", "rigging",
    "waist_apron", "maid_apron", "clothes_around_waist", "jacket_around_waist",
    "sweater_around_waist", "towel", "apron",
    "suspenders", "necklace_choker", "locket", "pierced_ears", "nose_ring",
    "belly_chain", "anklet", "armlet", "wristband", "watch", "hairclip",
    "hair_flower", "cat_ears_headband", "bunny_ears_headband",
    # Additional accessories and fetish-leaning details
    "hair_ornament", "hair_ribbon", "neck_ribbon", "leg_garter",
    "collar", "leash", "handcuffs", "wrist_cuffs", "ankle_cuffs",
    "blindfold", "ball_gag", "ring_gag", "rope_bondage", "shibari",
    "bandage", "eyepatch", "monocle", "mask", "face_mask",
    "cross_necklace", "rosary", "ear_cuffs", "toe_ring"
]

ALL_BODY_TYPES = [
    "Random",
    "slim body", "curvy body", "voluptuous body", "hourglass figure", "hourglass",
    "athletic body", "fit body", "petite body", "tall body", "plus size body",
    "thick thighs", "wide hips", "soft body", "pregnant", "wide hips",
    "muscular body", "lean body", "broad shoulders", "muscular",
    "dad bod", "slim fit", "bodybuilder", "average build",
    "hairy chest", "abs", "bear", "flat_chest", "large_breasts", "huge_breasts",
    "long neck", "broad shoulders", "navel", "cleavage", "ass",
    "medium build", "skinny", "stocky", "obese", "toned",
    "pear-shaped_body", "apple-shaped_body", "hourglass_figure", "thicc",
    "lean_muscular", "soft_thick", "petite_curvy",
    # Additional nuanced body descriptors
    "muscular_female", "muscular_male", "slim_thick", "curvy_thick",
    "flat_figured", "plump", "chubby", "soft_body", "skinny_fat",
    "hourglass_waist", "broad_hips", "narrow_waist", "pear_shaped",
    "apple_shaped", "athletic_female", "athletic_male",
    # Fantasy / creature morphs used in monster prompt examples
    "centaur", "lycanthrope", "werewolf", "monster", "anthro griffin", "anthro dragon",
    "anthro shark", "minotaur", "satyr", "faun", "naga", "mermaid", "merman",
    "anthro bear", "anthro panther", "anthro equine", "anthro stallion", "anthro mare",
    "jackalfolk", "ursine", "anubis", "draconic humanoid",
    # Full categorized species / anatomy taxonomy
    "human", "humanoid", "anthro", "anthropomorphic", "feral", "quadruped", "semi-anthro",
    "partially anthro", "taur", "centauroid", "naga", "lamia", "snake lower body", "merfolk",
    "insectoid", "arachnid", "arthropod", "slime", "gelatinous", "amorphous", "skeleton",
    "undead", "zombie", "mechanical", "cyborg", "robot", "plant", "flora", "alraune",
    "elemental", "werefox", "anthro fox", "kitsune", "werecat", "anthro cat", "nekomata",
    "catgirl", "werebear", "weretiger", "anthro tiger", "werelion", "anthro lion",
    "werehyena", "anthro hyena", "wererabbit", "anthro rabbit", "bunnygirl", "werehorse",
    "anthro horse", "equine anthro", "dragonkin", "drake", "draconic anthro", "dragon anthro",
    "lizardman", "reptilian anthro", "bull anthro", "goat anthro", "harpy", "bird anthro",
    "avian", "gryphon", "griffin anthro", "sphinx", "demon", "infernal", "tiefling", "angel",
    "celestial", "fallen angel", "succubus", "incubus", "vampire", "bat anthro", "orc",
    "goblin", "hobgoblin", "troll", "oni", "tengu", "kappa", "tanuki", "inari", "serpent",
    "snake anthro", "crocodile anthro", "alligator anthro", "shark anthro", "fish anthro",
    "octopus", "cephalopod", "tentacle anthro", "insect girl", "bee girl", "spider girl",
    "ant girl", "horse taur", "deer taur", "cervitaur", "lion taur", "tiger taur", "dragon taur"
]

FEMALE_BODY_TYPES = [
    "Random",
    "slim body", "curvy body", "voluptuous body", "hourglass figure", "hourglass",
    "athletic_female", "petite body", "plus size body",
    "thick thighs", "wide hips", "soft body", "pregnant",
    "medium build", "skinny", "toned", "thicc", "soft_thick", "petite_curvy",
    "curvy_thick", "hourglass_waist", "broad_hips", "narrow_waist",
]

MALE_BODY_TYPES = [
    "Random",
    "athletic_male", "muscular body", "lean body", "broad shoulders", "muscular",
    "dad bod", "slim fit", "bodybuilder", "average build",
    "hairy chest", "abs", "bear",
    "medium build", "skinny", "stocky", "obese", "toned",
]

ALL_POSES = [
    "Random",
    "standing", "standing elegantly", "sitting", "sitting on chair", "kneeling", "all fours",
    "lying on back", "lying on stomach", "walking", "looking back", "looking at viewer",
    "hands on hips", "peace sign", "selfie angle", "twirling hair",
    "leaning against wall", "legs spread", "bent over", "squatting", "stretching",
    "presenting", "lifting skirt", "spread legs",
    "standing confidently", "sitting manspreading", "arms crossed",
    "adjusting tie", "hands in pockets", "hand on hip",
    "fighting stance", "flexing muscles", "dynamic action", "floating",
    "dancing", "running", "jumping", "yawning", "leg crossed", "arms up",
    "on back", "on stomach", "cowboy shot", "from below", "from above",
    "profile", "back to viewer", "reclining", "standing on one leg",
    "sitting_crosslegged", "knees_together_feet_apart", "on_tiptoes",
    "arched_back", "hip_thrust", "lying_on_side", "pinup_pose"
]

BREAST_SIZES = [
    "Random", "None", "flat chest", "small breasts", "medium breasts", "large breasts",
    "huge breasts", "gigantic breasts", "massive breasts",
    # Alternate/common boob size phrasings
    "tiny breasts", "petite breasts", "big breasts", "enormous breasts", "colossal breasts"
]

BREAST_SHAPES = [
    "Random", "None", "natural breasts", "perky breasts", "saggy breasts", "asymmetrical breasts",
    "perfect breasts", "heavy breasts",
    # Additional shape/behavior descriptors
    "round breasts", "teardrop breasts", "firm breasts", "bouncy breasts",
    "compressed_breasts", "squeezed_breasts", "hanging_breasts"
]

LEG_FEATURES = [
    "Random", "None",
    "long legs", "thick thighs", "slim legs", "muscular legs", "crossed legs",
    "legs together", "legs apart", "one leg up", "kneeling", "squatting",
    "thigh_gap", "spread_legs", "pressed_thighs", "stocking_clad_legs",
    # Additional leg focus tags
    "bare_legs", "closed_legs", "bent_legs", "leg_lift", "legs_over_edge",
    "knees_up", "leg_wrap", "leg_lock", "one_leg_on_table"
]

BUTT_FEATURES = [
    "Random", "None",
    "bubble butt", "big ass", "round butt", "tight butt", "wide hips", "plump butt",
    "perky_butt", "thong_visible", "ass_focus",
    # Additional butt / hip focus tags
    "ass_cheeks", "ass_visible_through_clothes", "panties_around_one_leg",
    "panties_around_thigh", "panties_half_off", "butt_up", "hips_out",
    "booty_focus", "ass_grab"
]

FACE_SHAPES = [
    "Random", "None",
    "round face", "oval face", "heart-shaped face", "square jaw", "sharp jawline",
    "soft features"
]

EXPRESSIONS = [
    "Random", "None",
    "neutral expression", "gentle smile", "big smile", "smirk", "serious",
    "blushing", "shy", "seductive smile", "open mouth", "tongue out",
    "ahegao", "half-lidded eyes", "closed eyes", "crying", "pouting",
    "wink", "smug", "embarrassed", "teary_eyes", "biting_lip",
    "bedroom_eyes", "sleepy", "surprised", "angry",
    # Additional Danbooru-style facial expressions
    "orgasm_face", "ecstatic", "grin", "evil_grin", "nervous_smile",
    "flustered", "scared", "terrified", "bored", "disgusted",
    "sweatdrop", "determined", "focused", "daydreaming"
]

HAIR_LENGTHS = [
    "Random", "None",
    "very_short_hair", "short hair", "medium hair", "long hair",
    "very_long_hair", "absurdly_long_hair"
]

LOCATIONS = [
    "Random",
    "simple white background", "white_background", "simple black background", "black_background",
    "grey background", "grey_background", "blue_background", "gradient_background", "simple_background",
    "photography studio", "bustling city street", "cyberpunk city at night", "luxury penthouse",
    "cozy bedroom", "bedroom", "messy bedroom", "modern kitchen", "kitchen", "bathroom", "shower stall",
    "locker room", "neon-lit club", "bar counter", "library", "cafe terrace", "classroom",
    "office cubicle", "office", "hospital room", "garage", "dungeon", "gym", "gymnasium",
    "sci-fi spaceship interior", "space station corridor", "beach", "beach sunset", "dense forest",
    "forest", "flower garden", "garden", "abandoned warehouse", "rainy street", "street",
    "snowy mountain", "mountain", "desert dunes", "desert", "tropical jungle", "meadow with flowers",
    "onsen", "in a pool", "pool", "rooftop", "rooftop at night", "balcony", "autumn park",
    "cherry blossom grove", "love hotel", "tatami room", "public train", "outdoors", "indoors",
    "castle", "temple", "church", "dojo", "cave", "underwater", "stadium", "concert", "bar", "club",
    "rooftop_pool", "hotel_room", "luxury_bathroom", "sauna", "locker_room_shower",
    "night_cityscape", "alleyway", "parking_garage", "abandoned_building", "bridge_over_river",
    # Additional common Danbooru / SDXL environments
    "city_at_night", "city_skyline", "tokyo_street", "shibuya_crossing",
    "train_platform", "subway_car", "amusement_park", "ferris_wheel",
    "arcade", "shopping_mall", "market_street", "festival", "fireworks_view",
    "cliffside", "lakeside", "riverbank", "waterfall", "snowy_forest",
    "blossom_park", "school_hallway", "school_rooftop", "locker_corridor",
    # Fantasy / creature scene examples
    "jungle temple ruins background", "coral reef background", "deep ocean environment",
    "volcanic background", "ancient forest background", "egyptian god aesthetics",
    "gold ornaments", "snowy mountain background", "desert ruins", "moonlit cave"
]

LIGHTING = [
    "Random",
    "natural sunlight", "golden hour", "soft overcast", "cinematic lighting",
    "studio softbox", "studio_lighting", "hard rim lighting", "rim_lighting", "backlighting",
    "neon lights", "volumetric fog", "dark moody lighting", "dramatic_lighting",
    "moonlight", "bioluminescent glow", "camera flash", "dimly lit", "candlelight",
    "god rays", "lens flare", "soft_lighting", "harsh_lighting", "outdoor_lighting",
    "indoor_lighting", "overcast", "night", "day", "sunset", "sunrise", "silhouette",
    "spotlight", "rimlit_silhouette", "colored_gel_lighting", "club_neon_lighting",
    "hdr_lighting", "dramatic_shadows",
    # Additional nuanced lighting tags
    "soft_shadow", "strong_shadow", "backlit", "front_lighting",
    "side_lighting", "top_lighting", "underlighting", "colored_lighting",
    "pink_neon_lighting", "blue_neon_lighting", "studio_backdrop_lighting",
    # Fantasy / creature lighting examples
    "bright_rim_lighting", "cinematic_lighting", "volumetric lighting",
    "warm rim lighting", "dramatic lighting", "underwater lighting",
    "dark cinematic lighting", "golden rim light", "bioluminescent markings"
]

CAMERAS = [
    "Random",
    "85mm portrait lens", "35mm street lens", "24mm wide angle", "50mm standard lens",
    "200mm telephoto", "macro lens", "fisheye lens", "wide_shot", "wide angle view",
    "CCTV footage", "Polaroid style", "GoPro view", "drone shot",
    "from below", "from above", "dutch angle", "close-up", "extreme close-up",
    "cowboy shot", "full body", "full body shot", "upper body", "medium shot",
    "long shot", "bird's eye view", "low angle", "high angle", "over_shoulder",
    "pov", "looking at viewer",
    "closeup_face", "bust_shot", "three_quarter_view", "profile_view",
    "dolly_zoom_feel", "cinematic_framing",
    # Additional composition / camera-angle tags
    "wide_angle_lens", "telephoto_lens", "overhead_shot", "worm's_eye_view",
    "extreme_low_angle", "extreme_high_angle", "shoulder_level_shot",
    "hip_level_shot", "intimate_closeup", "face_focus", "body_focus"
]

SEX_ACTS = [
    "None", "Random",
    "sex", "vaginal sex", "anal sex", "oral sex", "fellatio", "cunnilingus", "sixty-nine",
    "fingering", "handjob", "paizuri", "titfuck", "rimming", "footjob", "thigh job",
    "frottage", "tribadism", "deepthroat", "face fucking", "irrumatio",
    "double penetration", "gangbang", "bukkake", "creampie", "facial", "internal ejaculation",
    "masturbation", "spitroast", "group sex",
    "cum_on_breasts", "cum_on_stomach", "cum_on_thighs", "hand_on_thigh",
    "teasing", "groping_breasts", "groping_butt", "public_sex", "bath_sex",
    "deep coupling", "explicit deep coupling", "intimate coupling", "creature coupling",
    "equine coupling", "wolf coupling", "werewolf coupling", "horse coupling",
    "centaur coupling", "canine coupling", "anthro coupling", "monster coupling"
]

SEX_POSITIONS = [
    "None", "Random",
    "missionary", "doggy style", "cowgirl position", "reverse cowgirl", "mating press",
    "standing sex", "spooning sex", "piledriver", "amazon position", "carried sex",
    "against wall", "on desk", "suspended", "facesitting", "prone bone",
    "legs over shoulders", "lotus position", "bridge position", "bent over",
    "cowgirl_on_chair", "reverse_cowgirl_on_sofa", "standing_doggy", "table_edge_sex",
    "side-by-side_position", "intimate position", "intimate positions",
    "body to body", "close-quarters coupling", "passionate embrace",
    "pointing_downwards", "fully_erect", "pointing_upwards", "standing_doggy_style",
    "alpha female stance", "battle stance", "powerful stance"
]

NSFW_MODIFIER_SECTIONS = {
    "core_nsfw_modifiers": [
        "nude", "naked", "topless", "bottomless", "nipples", "areolae", "pussy juice",
        "sweat", "tears", "blush", "ahegao", "rolling eyes", "tongue out", "drooling",
        "hard nipples", "detailed genitals", "uncensored", "cum on body", "cum on face",
        "messy hair", "heavy breathing", "wet_skin", "oil_on_skin", "body_glitter",
        "thigh_squeeze", "panty_pull_aside", "visible_panty_line", "cameltoe",
        "underboob", "sideboob", "nip_slip"
    ],
    "additional_explicit_and_fetish_modifiers": [
        "cum_in_mouth", "cum_on_hair", "semen", "dripping_cum", "multiple_cumshots",
        "saliva", "string_of_saliva", "spitstring", "glistening_skin",
        "sweaty_skin", "spread_pussy", "gaping", "pussy_juice_trail",
        "handprint_on_ass", "red_marks_on_skin", "explicit deep coupling",
        "dynamic muscle tension", "intense passion", "thick shaggy dark fur",
        "sleek white horse lower body", "thick leather skin", "heavy muscular chest",
        "glowing amber eyes", "smoky fur texture", "sleek glossy coat texture"
    ],
    "anatomy_and_genital_detail_modifiers": [
        "flared_knot_at_base", "thick_glans_ridge", "large testicles",
        "prominent pulsing veins", "detailed equine anatomy", "detailed canine anatomy",
        "equine_genitalia", "horse_penis", "dog_penis", "canine_genitalia",
        "male_genitalia", "female_genitalia", "horse_genitalia", "wolf_genitalia",
        "human_penis", "human_vagina", "human_anus", "big_testicles", "thick_corona_glandis",
        "large_testicles", "detailed_veins", "prominent_glans_ridge", "wide open pussy",
        "spreading pussy lips", "pink interior texture", "labia minora", "clitoris",
        "breasts", "small breasts", "medium breasts", "large breasts", "huge breasts",
        "hyper breasts", "multi-breast", "nipples", "puffy nipples", "inverted nipples",
        "areola", "pussy", "vagina", "labia", "detailed pussy", "wet pussy",
        "anus", "ass", "uterus", "womb", "penis", "large penis", "huge penis",
        "hyper penis", "human penis", "canine penis", "equine penis", "tapered penis",
        "ridged penis", "barbed penis", "flared tip", "knot", "knotted penis",
        "sheath", "sheath bulge", "balls", "scrotum", "large balls", "heavy balls",
        "cum-filled balls", "glans", "tip", "erection", "flaccid", "semi-erect",
        "dripping precum", "futanari", "hermaphrodite", "intersex", "dickgirl",
        "penis and vagina", "balls and pussy", "knotted futanari", "equine futanari",
        "multiple genitals", "cloaca", "ovipositor", "tentacle genitals",
        "internal genitals", "hemipenes", "multiple penises", "multi-cock",
        "pseudopenis", "genital slit", "gaping", "creampie overflow",
        "pussy juice trailing", "hyper", "hyper breasts", "hyper penis",
        "hyper muscles", "hyper proportions", "pregnancy", "pregnant",
        "heavily pregnant", "inflation", "expansion", "muscle growth",
        "hyper muscular", "soft body", "plush", "plush body", "chubby",
        "thick", "thick thighs", "wide hips", "narrow waist", "skinny",
        "emaciated", "amputee", "prosthetic limbs", "body horror", "mutated",
        "transformation", "partial transformation", "mid transformation",
        "transforming", "werewolf transformation", "anthro transformation",
        "cum", "semen", "pussy juice", "vaginal fluids", "saliva", "sweat",
        "wet", "dripping", "overflow", "cum dripping", "cum string",
        "cum pool", "messy", "sex", "intercourse", "vaginal", "anal", "oral",
        "fellatio", "cunnilingus", "paizuri", "titjob", "handjob", "footjob",
        "thighjob", "grinding", "tribadism", "penetration", "deep penetration",
        "knotting", "knotted", "knot locked", "knot swelling", "breeding",
        "impregnation", "creampie", "cum inside", "cum on body", "cum on face",
        "facial", "bukkake", "double penetration", "triple penetration",
        "spitroast", "reverse spitroast", "cowgirl", "reverse cowgirl",
        "missionary", "doggy style", "from behind", "standing sex", "against wall",
        "on top", "riding", "facesitting", "69", "sixty-nine", "oral sex",
        "deepthroat", "gagging", "kissing", "french kissing", "neck kissing",
        "licking", "biting", "scratching", "holding hands", "hugging",
        "embracing", "restraining", "pinning down", "dominant", "submissive",
        "rough sex", "gentle sex", "passionate"
    ],
    "anthro_fur_and_anatomy_modifiers": [
        "fur", "fluffy fur", "soft fur", "thick fur", "short fur", "long fur",
        "underfur", "mane", "feathered", "feathers", "plumage", "scales",
        "scaly", "smooth scales", "rough scales", "chitin", "exoskeleton",
        "bark", "wooden", "slimy", "wet", "glossy", "translucent",
        "see-through", "patterned fur", "spots", "stripes", "markings",
        "two-tone fur", "multicolored fur",
        "breasts", "small breasts", "medium breasts", "large breasts", "huge breasts",
        "hyper breasts", "multi-breast", "nipples", "puffy nipples", "inverted nipples",
        "areola", "pussy", "vagina", "labia", "clitoris", "detailed pussy",
        "wet pussy", "anus", "ass", "uterus", "womb",
        "penis", "large penis", "huge penis", "hyper penis", "human penis",
        "canine penis", "equine penis", "tapered penis", "ridged penis",
        "barbed penis", "flared tip", "knot", "knotted penis", "sheath",
        "sheath bulge", "balls", "scrotum", "large balls", "heavy balls",
        "cum-filled balls", "glans", "tip", "erection", "flaccid",
        "semi-erect", "dripping precum"
    ],
    "bondage_and_restraint_modifiers": [
        "bound", "tied up", "restrained", "handcuffs", "rope", "bondage",
        "collar", "leash", "gag", "blindfold", "spread legs", "arms behind back",
        "legs spread"
    ],
    "quality_and_anatomy_tags": [
        "detailed anatomy", "accurate anatomy", "correct anatomy", "realistic anatomy",
        "stylized anatomy", "anatomically correct", "detailed genitals", "realistic genitals",
        "soft shading", "detailed shading", "muscular definition", "muscular chest",
        "defined abs", "soft belly", "plush thighs", "score_9", "score_8_up",
        "score_7_up", "masterpiece", "best quality", "highly detailed", "intricate details"
    ],
    "creature_and_fantasy_surface_modifiers": [
        "greenish scales", "iridescent snake scales", "bioluminescent markings"
    ],
}


def _flatten_nsfw_sections(section_map):
    flattened = []
    for entries in section_map.values():
        flattened.extend(entries)
    seen = set()
    ordered = []
    for tag in flattened:
        if tag in seen:
            continue
        seen.add(tag)
        ordered.append(tag)
    return ordered


NSFW_MODIFIERS = _flatten_nsfw_sections(NSFW_MODIFIER_SECTIONS)


# --- HELPER FUNCTIONS ---

def get_smart_random(category_list, seed, exclude_none=True):
    # Filters out 'Random' and 'None' for the selection pool
    pool = [x for x in category_list if x != "Random" and (not exclude_none or x != "None")]
    if not pool:
        return ""
    random.seed(seed)
    return random.choice(pool)


def _normalize_prompt_value(value):
    if value is None:
        return ""
    value = str(value).strip()
    if value in {"", "None", "Random"}:
        return ""
    return value


def _is_ignored_value(value):
    if value is None:
        return True
    return str(value).strip() in {"", "None", "Random"}


def _format_eye_value(value):
    value = _normalize_prompt_value(value)
    if not value:
        return ""
    lowered = value.lower()
    if lowered.endswith("_eyes") or lowered.endswith(" eyes"):
        return value
    return f"{value} eyes"


def _clean_tag_list(items):
    cleaned = []
    seen = set()
    for item in items:
        value = _normalize_prompt_value(item)
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(value)
    return cleaned


def build_subject_prompt_from_ui(values):
    values = values or {}

    def pick(key):
        value = values.get(key, "")
        if value is None:
            return ""
        text = str(value).strip()
        if text in {"", "None", "Random"}:
            return ""
        return text

    is_ignored = _is_ignored_value

    lead_token = pick("lead_token") or pick("gender") or "person"
    setup_group = pick("setup_group") or pick("group_setup") or pick("person_setup")

    parts = [lead_token]
    if setup_group and setup_group not in {"solo", "1girl", "1boy", "1other", "duo"}:
        parts.append(setup_group)

    age = pick("age")
    if age:
        parts.append(f"{age} years old:1.1")

    body = pick("body_type")
    if body:
        parts.append(body)

    skin = pick("skin_texture")
    if skin:
        parts.append(skin)

    special_skin = pick("special_skin_type")
    if not special_skin:
        person_index = str(values.get("person_index", "")).strip()
        if person_index:
            dynamic_key = f"person_{person_index}_special_skin"
            dynamic_value = values.get(dynamic_key, "")
            if not is_ignored(dynamic_value):
                special_skin = str(dynamic_value).strip()
    if special_skin:
        parts.append(special_skin)

    hair_color = pick("hair_color")
    hair_style = pick("hair_style")
    if hair_color and hair_style:
        parts.append(f"{hair_color} {hair_style}")
    elif hair_color:
        parts.append(hair_color)
    elif hair_style:
        parts.append(hair_style)

    full_outfit = pick("full_outfit")
    if full_outfit:
        parts.append(full_outfit)

    for key in ["top_clothing", "bottom_clothing", "headwear", "shoes", "accessories"]:
        value = pick(key)
        if value:
            parts.append(value)

    for key in ["breast_size", "breast_shape", "expression", "pose"]:
        value = pick(key)
        if value:
            parts.append(value)

    nsfw_modifier = values.get("nsfw_modifier", "")
    if not is_ignored(nsfw_modifier):
        parts.append(nsfw_modifier)

    bondage = values.get("bondage_restraint", "")
    if not is_ignored(bondage):
        parts.append(bondage)

    custom_tags = pick("custom_tags")
    if custom_tags:
        parts.append(custom_tags)

    prompt = "(" + ", ".join(parts) + ")"
    return prompt


# --- NODES ---

class CR_Pony_Subject:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "gender": (GENDERS, {"default": "female"}),
                "age": (AGES, {"default": "25"}),
                "ethnicity": (ETHNICITIES, {"default": "Caucasian"}),
                "body_type": (ALL_BODY_TYPES, {"default": "slim body"}),
                "skin_texture": (SKIN_TYPES, {"default": "pale skin"}),
                "hair_color": (HAIR_COLORS, {"default": "platinum blonde"}),
                "hair_style": (ALL_HAIRSTYLES, {"default": "messy bun"}),
                "eye_color": (EYE_COLORS, {"default": "blue"}),
                "full_outfit": (FULL_OUTFITS, {"default": "Random"}),
                "top_clothing": (TOP_CLOTHING, {"default": "t-shirt"}),
                "bottom_clothing": (BOTTOM_CLOTHING, {"default": "jeans"}),
                "headwear": (HEADWEAR, {"default": "None"}),
                "shoes": (FOOTWEAR, {"default": "None"}),
                "accessories": (ACCESSORIES, {"default": "None"}),
                "pose": (ALL_POSES, {"default": "standing elegantly"}),
                "breast_size": (BREAST_SIZES, {"default": "medium breasts"}),
                "breast_shape": (BREAST_SHAPES, {"default": "natural breasts"}),
            },
            "optional": {
                "custom_tags": ("STRING", {"multiline": True, "default": ""}),
                "nsfw_modifiers": ("BOOLEAN", {"default": False}),
                "leg_feature": (LEG_FEATURES, {"default": "Random"}),
                "butt_feature": (BUTT_FEATURES, {"default": "Random"}),
                "face_shape": (FACE_SHAPES, {"default": "Random"}),
                "expression": (EXPRESSIONS, {"default": "Random"}),
                "hair_length": (HAIR_LENGTHS, {"default": "Random"}),
                "extra_clothing_tags": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text_output",)
    FUNCTION = "generate_subject"
    CATEGORY = "CyberRealistic Pony"

    def generate_subject(self, seed, gender, age, ethnicity, body_type, skin_texture,
                        hair_color, hair_style, eye_color, full_outfit,
                        top_clothing, bottom_clothing, headwear, shoes, accessories,
                        pose, breast_size, breast_shape, custom_tags="", nsfw_modifiers=False,
                        leg_feature="Random", butt_feature="Random",
                        face_shape="Random", expression="Random", hair_length="Random",
                        extra_clothing_tags="", lead_token=None):

        # Seed the RNG
        random.seed(seed)

        # Resolve Randoms - but ignore Random/None completely; never inject defaults for them.
        r_gender = gender if not _is_ignored_value(gender) else ""
        r_age = age if not _is_ignored_value(age) else ""
        r_ethnicity = ethnicity if not _is_ignored_value(ethnicity) else ""
        r_body = body_type if not _is_ignored_value(body_type) else ""
        r_skin = skin_texture if not _is_ignored_value(skin_texture) else ""
        r_h_color = hair_color if not _is_ignored_value(hair_color) else ""
        r_h_style = hair_style if not _is_ignored_value(hair_style) else ""
        r_eyes = eye_color if not _is_ignored_value(eye_color) else ""
        r_pose = pose if not _is_ignored_value(pose) else ""

        explicit_lead = (lead_token or "").strip()
        if explicit_lead and explicit_lead != "Random":
            noun = explicit_lead
        else:
            noun = "woman" if r_gender == "female" else "man" if r_gender == "male" else str(r_gender or "person").strip() or "person"

        r_gender_clean = _normalize_prompt_value(r_gender)
        r_age_clean = _normalize_prompt_value(r_age)
        r_ethnicity_clean = _normalize_prompt_value(r_ethnicity)
        r_body_clean = _normalize_prompt_value(r_body)
        r_skin_clean = _normalize_prompt_value(r_skin)
        r_h_color_clean = _normalize_prompt_value(r_h_color)
        r_h_style_clean = _normalize_prompt_value(r_h_style)
        r_eyes_clean = _format_eye_value(r_eyes)
        r_pose_clean = _normalize_prompt_value(r_pose)

        # Construct String (avoid "hair hair" when tag already contains hair, e.g. straight_hair)
        eth_str = noun if not r_ethnicity_clean or r_ethnicity_clean in {"Caucasian"} else f"{r_ethnicity_clean} {noun}"
        hair_part = "" if r_h_style_clean and "hair" in r_h_style_clean.lower() else " hair" if r_h_style_clean else ""
        prompt_parts = [eth_str]
        if r_age_clean:
            prompt_parts.append(f"{r_age_clean} years old:1.1")
        if r_body_clean:
            prompt_parts.append(r_body_clean)
        if r_skin_clean:
            prompt_parts.append(r_skin_clean)
        if r_h_color_clean and r_h_style_clean:
            prompt_parts.append(f"{r_h_color_clean} {r_h_style_clean}{hair_part}")
        elif r_h_style_clean:
            prompt_parts.append(r_h_style_clean)
        elif r_h_color_clean:
            prompt_parts.append(r_h_color_clean)
        if r_eyes_clean:
            prompt_parts.append(r_eyes_clean)
        prompt = "(" + ", ".join(part for part in prompt_parts if part and part != "()") + ")"

        # Clothing selection
        clothing_tags = []
        r_full_outfit = full_outfit if not _is_ignored_value(full_outfit) else ""
        if r_full_outfit:
            clothing_tags.append(r_full_outfit)

        def _resolve_choice(choice, data=None, offset=None):
            if _is_ignored_value(choice):
                return ""
            return str(choice).strip()

        r_top = _resolve_choice(top_clothing)
        r_bottom = _resolve_choice(bottom_clothing)
        r_head = _resolve_choice(headwear)
        r_shoes = _resolve_choice(shoes)
        r_acc = _resolve_choice(accessories)

        for item in [r_top, r_bottom, r_head, r_shoes, r_acc]:
            if item:
                clothing_tags.append(item)

        if clothing_tags:
            prompt += f", wearing {', '.join(clothing_tags)}"

        feature_parts = []
        if r_pose and r_pose not in ["Random", "None"]:
            feature_parts.append(r_pose)

        # Breasts (Only if not male)
        if r_gender != "male":
            r_b_size = get_smart_random(BREAST_SIZES, seed + 10) if breast_size == "Random" else breast_size
            r_b_shape = get_smart_random(BREAST_SHAPES, seed + 11) if breast_shape == "Random" else breast_shape
            if r_b_size and r_b_size != "None":
                feature_parts.append(r_b_size)
            if r_b_shape and r_b_shape != "None":
                feature_parts.append(r_b_shape)

        # Extra body-part controls
        def _resolve_feature(choice, data, offset):
            if not choice:
                return None
            if choice == "Random":
                return get_smart_random(data, seed + offset)
            return choice

        r_leg = _resolve_feature(leg_feature, LEG_FEATURES, 17)
        r_butt = _resolve_feature(butt_feature, BUTT_FEATURES, 18)
        r_face = _resolve_feature(face_shape, FACE_SHAPES, 19)
        r_expr = _resolve_feature(expression, EXPRESSIONS, 20)
        r_hlen = _resolve_feature(hair_length, HAIR_LENGTHS, 21)

        for feat in [r_leg, r_butt, r_face, r_expr, r_hlen]:
            if feat and feat not in ["Random", "None"]:
                feature_parts.append(feat)

        extra_custom_parts = []
        if custom_tags.strip():
            for raw in [part.strip() for part in custom_tags.split(',')]:
                if not raw:
                    continue
                lowered = raw.lower()
                if raw in NSFW_MODIFIERS or lowered in {"pussy", "vagina", "anus", "ass", "penis", "balls", "nipple", "nipples", "genitals", "genitalia", "clitoris", "labia"}:
                    feature_parts.append(raw)
                else:
                    extra_custom_parts.append(raw)

        # NSFW Auto-Modifiers
        if nsfw_modifiers:
            # Do not inject hardcoded anatomy/default tags when the UI values are None/Random.
            # The selected modifier and custom tags are the only allowed source for NSFW content.
            pass

        if feature_parts:
            clean_parts = _clean_tag_list(feature_parts)
            if clean_parts:
                prompt += f", ({', '.join(clean_parts)})"

        # Extra Clothing & Custom Tags at the end
        if extra_clothing_tags.strip():
            cleaned_extra = ", ".join(_clean_tag_list([tag.strip() for tag in extra_clothing_tags.split(',')]))
            if cleaned_extra:
                prompt += f", {cleaned_extra}"
        if extra_custom_parts:
            clean_custom = _clean_tag_list(extra_custom_parts)
            if clean_custom:
                prompt += f", {', '.join(clean_custom)}"

        print(f"[CyberRealistic Pony Subject] {prompt}")
        return (prompt,)


class CR_Pony_Subject_Female:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "age": (AGES, {"default": "25"}),
                "ethnicity": (ETHNICITIES, {"default": "Caucasian"}),
                "body_type": (FEMALE_BODY_TYPES, {"default": "slim body"}),
                "skin_texture": (SKIN_TYPES, {"default": "pale skin"}),
                "hair_color": (HAIR_COLORS, {"default": "platinum blonde"}),
                "hair_style": (FEMALE_HAIRSTYLES, {"default": "messy bun"}),
                "eye_color": (EYE_COLORS, {"default": "blue"}),
                "full_outfit": (FULL_OUTFITS, {"default": "Random"}),
                "top_clothing": (FEMALE_TOP_CLOTHING, {"default": "t-shirt"}),
                "bottom_clothing": (BOTTOM_CLOTHING, {"default": "jeans"}),
                "headwear": (HEADWEAR, {"default": "None"}),
                "shoes": (FOOTWEAR, {"default": "None"}),
                "accessories": (ACCESSORIES, {"default": "None"}),
                "pose": (ALL_POSES, {"default": "standing elegantly"}),
                "breast_size": (BREAST_SIZES, {"default": "medium breasts"}),
                "breast_shape": (BREAST_SHAPES, {"default": "natural breasts"}),
            },
            "optional": {
                "custom_tags": ("STRING", {"multiline": True, "default": ""}),
                "nsfw_modifiers": ("BOOLEAN", {"default": False}),
                "leg_feature": (LEG_FEATURES, {"default": "Random"}),
                "butt_feature": (BUTT_FEATURES, {"default": "Random"}),
                "face_shape": (FACE_SHAPES, {"default": "Random"}),
                "expression": (EXPRESSIONS, {"default": "Random"}),
                "hair_length": (HAIR_LENGTHS, {"default": "Random"}),
                "extra_clothing_tags": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "generate_subject"
    CATEGORY = "CyberRealistic Pony"

    def generate_subject(self, seed, age, ethnicity, body_type, skin_texture,
                        hair_color, hair_style, eye_color, full_outfit,
                        top_clothing, bottom_clothing, headwear, shoes, accessories,
                        pose, breast_size, breast_shape, custom_tags="", nsfw_modifiers=False,
                        leg_feature="Random", butt_feature="Random",
                        face_shape="Random", expression="Random", hair_length="Random",
                        extra_clothing_tags=""):

        # Seed the RNG
        random.seed(seed)

        r_gender = "female"
        r_age = get_smart_random(AGES, seed + 1) if age == "Random" else age
        r_ethnicity = get_smart_random(ETHNICITIES, seed + 2) if ethnicity == "Random" else ethnicity
        r_body = get_smart_random(FEMALE_BODY_TYPES, seed + 3) if body_type == "Random" else body_type
        r_skin = get_smart_random(SKIN_TYPES, seed + 4) if skin_texture == "Random" else skin_texture
        r_h_color = get_smart_random(HAIR_COLORS, seed + 5) if hair_color == "Random" else hair_color
        r_h_style = get_smart_random(FEMALE_HAIRSTYLES, seed + 6) if hair_style == "Random" else hair_style
        r_eyes = get_smart_random(EYE_COLORS, seed + 7) if eye_color == "Random" else eye_color
        r_pose = get_smart_random(ALL_POSES, seed + 9) if pose == "Random" else pose

        r_age_clean = _normalize_prompt_value(r_age)
        r_ethnicity_clean = _normalize_prompt_value(r_ethnicity)
        r_body_clean = _normalize_prompt_value(r_body)
        r_skin_clean = _normalize_prompt_value(r_skin)
        r_h_color_clean = _normalize_prompt_value(r_h_color)
        r_h_style_clean = _normalize_prompt_value(r_h_style)
        r_eyes_clean = _format_eye_value(r_eyes)

        noun = "woman"
        eth_str = noun if not r_ethnicity_clean or r_ethnicity_clean in {"Caucasian"} else f"{r_ethnicity_clean} {noun}"
        hair_part = "" if r_h_style_clean and "hair" in r_h_style_clean.lower() else " hair" if r_h_style_clean else ""
        prompt_parts = [eth_str]
        if r_age_clean:
            prompt_parts.append(f"{r_age_clean} years old:1.1")
        if r_body_clean:
            prompt_parts.append(r_body_clean)
        if r_skin_clean:
            prompt_parts.append(r_skin_clean)
        if r_h_color_clean and r_h_style_clean:
            prompt_parts.append(f"{r_h_color_clean} {r_h_style_clean}{hair_part}")
        elif r_h_style_clean:
            prompt_parts.append(r_h_style_clean)
        elif r_h_color_clean:
            prompt_parts.append(r_h_color_clean)
        if r_eyes_clean:
            prompt_parts.append(r_eyes_clean)
        prompt = "(" + ", ".join(part for part in prompt_parts if part and part != "()") + ")"

        clothing_tags = []
        r_full_outfit = get_smart_random(FULL_OUTFITS, seed + 8) if full_outfit == "Random" else full_outfit
        if r_full_outfit and r_full_outfit not in ["Random", "None"]:
            clothing_tags.append(r_full_outfit)

        def _resolve_choice(choice, data, offset):
            if choice is None:
                return None
            if choice == "Random":
                return get_smart_random(data, seed + offset)
            return choice

        r_top = _resolve_choice(top_clothing, FEMALE_TOP_CLOTHING, 12)
        r_bottom = _resolve_choice(bottom_clothing, BOTTOM_CLOTHING, 13)
        r_head = _resolve_choice(headwear, HEADWEAR, 14)
        r_shoes = _resolve_choice(shoes, FOOTWEAR, 15)
        r_acc = _resolve_choice(accessories, ACCESSORIES, 16)

        for item in [r_top, r_bottom, r_head, r_shoes, r_acc]:
            if item and item not in ["Random", "None"]:
                clothing_tags.append(item)

        if clothing_tags:
            prompt += f", wearing {', '.join(clothing_tags)}"

        feature_parts = []
        if r_pose and r_pose not in ["Random", "None"]:
            feature_parts.append(r_pose)

        # Breasts (always applicable here)
        r_b_size = get_smart_random(BREAST_SIZES, seed + 10) if breast_size == "Random" else breast_size
        r_b_shape = get_smart_random(BREAST_SHAPES, seed + 11) if breast_shape == "Random" else breast_shape
        if r_b_size and r_b_size != "None":
            feature_parts.append(r_b_size)
        if r_b_shape and r_b_shape != "None":
            feature_parts.append(r_b_shape)

        def _resolve_feature(choice, data, offset):
            if not choice:
                return None
            if choice == "Random":
                return get_smart_random(data, seed + offset)
            return choice

        r_leg = _resolve_feature(leg_feature, LEG_FEATURES, 17)
        r_butt = _resolve_feature(butt_feature, BUTT_FEATURES, 18)
        r_face = _resolve_feature(face_shape, FACE_SHAPES, 19)
        r_expr = _resolve_feature(expression, EXPRESSIONS, 20)
        r_hlen = _resolve_feature(hair_length, HAIR_LENGTHS, 21)

        for feat in [r_leg, r_butt, r_face, r_expr, r_hlen]:
            if feat and feat not in ["Random", "None"]:
                feature_parts.append(feat)

        extra_custom_parts = []
        if custom_tags.strip():
            for raw in [part.strip() for part in custom_tags.split(',')]:
                if not raw:
                    continue
                lowered = raw.lower()
                if raw in NSFW_MODIFIERS or lowered in {"pussy", "vagina", "anus", "ass", "penis", "balls", "nipple", "nipples", "genitals", "genitalia", "clitoris", "labia"}:
                    feature_parts.append(raw)
                else:
                    extra_custom_parts.append(raw)

        if nsfw_modifiers:
            mods = random.sample(NSFW_MODIFIERS, 2)
            for mod in mods:
                feature_parts.append(mod)
            feature_parts.append("pussy")

        if feature_parts:
            clean_parts = _clean_tag_list(feature_parts)
            if clean_parts:
                prompt += f", ({', '.join(clean_parts)})"

        if extra_clothing_tags.strip():
            cleaned_extra = ", ".join(_clean_tag_list([tag.strip() for tag in extra_clothing_tags.split(',')]))
            if cleaned_extra:
                prompt += f", {cleaned_extra}"
        if extra_custom_parts:
            clean_custom = _clean_tag_list(extra_custom_parts)
            if clean_custom:
                prompt += f", {', '.join(clean_custom)}"

        print(f"[CyberRealistic Pony Female Subject] {prompt}")
        return (prompt,)


class CR_Pony_Subject_Male:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "age": (AGES, {"default": "25"}),
                "ethnicity": (ETHNICITIES, {"default": "Caucasian"}),
                "body_type": (MALE_BODY_TYPES, {"default": "athletic_male"}),
                "skin_texture": (SKIN_TYPES, {"default": "pale skin"}),
                "hair_color": (HAIR_COLORS, {"default": "black"}),
                "hair_style": (MALE_HAIRSTYLES, {"default": "fade"}),
                "eye_color": (EYE_COLORS, {"default": "blue"}),
                "full_outfit": (FULL_OUTFITS, {"default": "Random"}),
                "top_clothing": (MALE_TOP_CLOTHING, {"default": "t-shirt"}),
                "bottom_clothing": (BOTTOM_CLOTHING, {"default": "jeans"}),
                "headwear": (HEADWEAR, {"default": "None"}),
                "shoes": (FOOTWEAR, {"default": "None"}),
                "accessories": (ACCESSORIES, {"default": "None"}),
                "pose": (ALL_POSES, {"default": "standing confidently"}),
            },
            "optional": {
                "custom_tags": ("STRING", {"multiline": True, "default": ""}),
                "nsfw_modifiers": ("BOOLEAN", {"default": False}),
                "leg_feature": (LEG_FEATURES, {"default": "Random"}),
                "butt_feature": (BUTT_FEATURES, {"default": "Random"}),
                "face_shape": (FACE_SHAPES, {"default": "Random"}),
                "expression": (EXPRESSIONS, {"default": "Random"}),
                "hair_length": (HAIR_LENGTHS, {"default": "Random"}),
                "extra_clothing_tags": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "generate_subject"
    CATEGORY = "CyberRealistic Pony"

    def generate_subject(self, seed, age, ethnicity, body_type, skin_texture,
                        hair_color, hair_style, eye_color, full_outfit,
                        top_clothing, bottom_clothing, headwear, shoes, accessories,
                        pose, custom_tags="", nsfw_modifiers=False,
                        leg_feature="Random", butt_feature="Random",
                        face_shape="Random", expression="Random", hair_length="Random",
                        extra_clothing_tags=""):

        random.seed(seed)

        r_gender = "male"
        r_age = get_smart_random(AGES, seed + 1) if age == "Random" else age
        r_ethnicity = get_smart_random(ETHNICITIES, seed + 2) if ethnicity == "Random" else ethnicity
        r_body = get_smart_random(MALE_BODY_TYPES, seed + 3) if body_type == "Random" else body_type
        r_skin = get_smart_random(SKIN_TYPES, seed + 4) if skin_texture == "Random" else skin_texture
        r_h_color = get_smart_random(HAIR_COLORS, seed + 5) if hair_color == "Random" else hair_color
        r_h_style = get_smart_random(MALE_HAIRSTYLES, seed + 6) if hair_style == "Random" else hair_style
        r_eyes = get_smart_random(EYE_COLORS, seed + 7) if eye_color == "Random" else eye_color
        r_pose = get_smart_random(ALL_POSES, seed + 9) if pose == "Random" else pose

        r_age_clean = _normalize_prompt_value(r_age)
        r_ethnicity_clean = _normalize_prompt_value(r_ethnicity)
        r_body_clean = _normalize_prompt_value(r_body)
        r_skin_clean = _normalize_prompt_value(r_skin)
        r_h_color_clean = _normalize_prompt_value(r_h_color)
        r_h_style_clean = _normalize_prompt_value(r_h_style)
        r_eyes_clean = _format_eye_value(r_eyes)

        noun = "man"
        eth_str = noun if not r_ethnicity_clean or r_ethnicity_clean in {"Caucasian"} else f"{r_ethnicity_clean} {noun}"
        hair_part = "" if r_h_style_clean and "hair" in r_h_style_clean.lower() else " hair" if r_h_style_clean else ""
        prompt_parts = [eth_str]
        if r_age_clean:
            prompt_parts.append(f"{r_age_clean} years old:1.1")
        if r_body_clean:
            prompt_parts.append(r_body_clean)
        if r_skin_clean:
            prompt_parts.append(r_skin_clean)
        if r_h_color_clean and r_h_style_clean:
            prompt_parts.append(f"{r_h_color_clean} {r_h_style_clean}{hair_part}")
        elif r_h_style_clean:
            prompt_parts.append(r_h_style_clean)
        elif r_h_color_clean:
            prompt_parts.append(r_h_color_clean)
        if r_eyes_clean:
            prompt_parts.append(r_eyes_clean)
        prompt = "(" + ", ".join(part for part in prompt_parts if part and part != "()") + ")"

        clothing_tags = []
        r_full_outfit = get_smart_random(FULL_OUTFITS, seed + 8) if full_outfit == "Random" else full_outfit
        if r_full_outfit and r_full_outfit not in ["Random", "None"]:
            clothing_tags.append(r_full_outfit)

        def _resolve_choice(choice, data, offset):
            if choice is None:
                return None
            if choice == "Random":
                return get_smart_random(data, seed + offset)
            return choice

        r_top = _resolve_choice(top_clothing, MALE_TOP_CLOTHING, 12)
        r_bottom = _resolve_choice(bottom_clothing, BOTTOM_CLOTHING, 13)
        r_head = _resolve_choice(headwear, HEADWEAR, 14)
        r_shoes = _resolve_choice(shoes, FOOTWEAR, 15)
        r_acc = _resolve_choice(accessories, ACCESSORIES, 16)

        for item in [r_top, r_bottom, r_head, r_shoes, r_acc]:
            if item and item not in ["Random", "None"]:
                clothing_tags.append(item)

        if clothing_tags:
            prompt += f", wearing {', '.join(clothing_tags)}"

        feature_parts = []
        if r_pose and r_pose not in ["Random", "None"]:
            feature_parts.append(r_pose)

        def _resolve_feature(choice, data, offset):
            if not choice:
                return None
            if choice == "Random":
                return get_smart_random(data, seed + offset)
            return choice

        r_leg = _resolve_feature(leg_feature, LEG_FEATURES, 17)
        r_butt = _resolve_feature(butt_feature, BUTT_FEATURES, 18)
        r_face = _resolve_feature(face_shape, FACE_SHAPES, 19)
        r_expr = _resolve_feature(expression, EXPRESSIONS, 20)
        r_hlen = _resolve_feature(hair_length, HAIR_LENGTHS, 21)

        for feat in [r_leg, r_butt, r_face, r_expr, r_hlen]:
            if feat and feat not in ["Random", "None"]:
                feature_parts.append(feat)

        extra_custom_parts = []
        if custom_tags.strip():
            for raw in [part.strip() for part in custom_tags.split(',')]:
                if not raw:
                    continue
                lowered = raw.lower()
                if raw in NSFW_MODIFIERS or lowered in {"pussy", "vagina", "anus", "ass", "penis", "balls", "nipple", "nipples", "genitals", "genitalia", "clitoris", "labia"}:
                    feature_parts.append(raw)
                else:
                    extra_custom_parts.append(raw)

        if nsfw_modifiers:
            mods = random.sample(NSFW_MODIFIERS, 2)
            for mod in mods:
                feature_parts.append(mod)
            feature_parts.extend(["penis", "balls"])

        if feature_parts:
            clean_parts = _clean_tag_list(feature_parts)
            if clean_parts:
                prompt += f", ({', '.join(clean_parts)})"

        if extra_clothing_tags.strip():
            cleaned_extra = ", ".join(_clean_tag_list([tag.strip() for tag in extra_clothing_tags.split(',')]))
            if cleaned_extra:
                prompt += f", {cleaned_extra}"
        if extra_custom_parts:
            clean_custom = _clean_tag_list(extra_custom_parts)
            if clean_custom:
                prompt += f", {', '.join(clean_custom)}"

        print(f"[CyberRealistic Pony Male Subject] {prompt}")
        return (prompt,)

class CR_Pony_Master:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "rating": (RATINGS, {"default": "rating_safe"}),
                "location": (LOCATIONS, {"default": "luxury penthouse"}),
                "lighting": (LIGHTING, {"default": "cinematic lighting"}),
                "camera": (CAMERAS, {"default": "85mm portrait lens"}),
                "use_break": ("BOOLEAN", {"default": True}),
                "nsfw_mode": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "sex_act": (SEX_ACTS, {"default": "None"}),
                "sex_position": (SEX_POSITIONS, {"default": "None"}),
                "score_scheme": (SCORE_SCHEMES, {"default": "default high"}),
                "source_bias": (SOURCE_TAGS, {"default": "None"}),
                "strong_anime_bias": ("BOOLEAN", {"default": False}),
                "style_preset": (STYLE_PRESETS, {"default": "None"}),
                "subject_1": ("STRING", {"forceInput": True}),
                "subject_2": ("STRING", {"forceInput": True}),
                "subject_3": ("STRING", {"forceInput": True}),
                "subject_4": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text_output",)
    FUNCTION = "generate_master"
    CATEGORY = "CyberRealistic Pony"

    def generate_master(self, seed, rating, location, lighting, camera, use_break, nsfw_mode,
                       sex_act="None", sex_position="None",
                       score_scheme="default high", source_bias="None", strong_anime_bias=False,
                       style_preset="None",
                       subject_1=None, subject_2=None, subject_3=None, subject_4=None,
                       photo_boost=False):

        random.seed(seed)

        # 1. Header
        if score_scheme == "score_9 only":
            base_score = "score_9"
        elif score_scheme == "score_7_plus":
            base_score = "score_9, score_8_up, score_7_up"
        else:
            base_score = "score_9, score_8_up, score_7_up, score_6_up"

        # Quality/source handling
        # Default photography bias; source_bias can override or add to this.
        quality = "raw photo, hyperrealistic, 8k uhd, film grain, masterpiece, highly detailed"
        source_tags = []
        if source_bias and source_bias != "None":
            source_tags.append(source_bias)
        else:
            source_tags.append("source_photography")

        # Style presets inject small curated bundles
        style_tags = []
        if style_preset == "photorealistic":
            style_tags.append("photo-realistic")
        elif style_preset == "anime_leaning":
            style_tags.append("anime style, soft shading")
        elif style_preset == "sketch":
            style_tags.append("pencil sketch, lineart emphasis")
        elif style_preset == "studio_glamour":
            style_tags.append("studio glamour, beauty lighting")

        header_parts = [base_score, rating]
        if photo_boost:
            header_parts.append(PHOTO_BOOST_POTION)
        header_parts.extend([", ".join(source_tags), quality])
        if style_tags:
            header_parts.append(", ".join(style_tags))
        pos = f"{', '.join(header_parts)}, "

        # 2. Count Logic & Subject Collection (only add count tags that match actual subjects)
        subjects = [s for s in [subject_1, subject_2, subject_3, subject_4] if s and str(s).strip()]
        count = len(subjects)

        creature_terms = [
            "centaur", "lycanthrope", "werewolf", "monster", "griffin", "dragon",
            "shark", "minotaur", "satyr", "faun", "naga", "mermaid", "merman",
            "bear", "panther", "stallion", "mare", "jackalfolk", "ursine", "anubis",
            "equine", "canine", "wolf", "horse"
        ]
        combined_subject_text = " ".join(subjects).lower()
        duo_creature_mode = count >= 2 and any(term.lower() in combined_subject_text for term in creature_terms)

        # 3. Sex Acts (NSFW) — appear early in prompt, weighted by scheme
        if nsfw_mode:
            r_act = get_smart_random(SEX_ACTS, seed + 3, exclude_none=True) if sex_act == "Random" else sex_act
            r_pos = get_smart_random(SEX_POSITIONS, seed + 4, exclude_none=True) if sex_position == "Random" else sex_position
            if score_scheme == "default high":
                act_weight = "3"
                pos_weight = "3"
            else:
                act_weight = "1.2"
                pos_weight = "1.15"
            if r_act and r_act != "None":
                pos += f"({r_act}:{act_weight}), "
            if r_pos and r_pos != "None":
                pos += f"({r_pos}:{pos_weight}), "

            if duo_creature_mode or count >= 2:
                pos += "2creatures, duo, explicit deep coupling, intimate positions, intense passion, dynamic muscle tension, detailed equine and canine anatomy, "
                pos += "flared_knot_at_base, thick_glans_ridge, large testicles, prominent pulsing veins, "


        # Count by gender: avoid "man" matching inside "woman"
        def _is_girl(s):
            return "woman" in s or "girl" in s
        def _is_boy(s):
            return "boy" in s or ("man" in s and "woman" not in s)
        girl_count = sum(1 for s in subjects if _is_girl(s))
        boy_count = sum(1 for s in subjects if _is_boy(s))

        if count == 0:
            pass  # no count tags when no subjects
        elif count == 1:
            if girl_count == 1:
                pos += "1girl, "
            elif boy_count == 1:
                pos += "1boy, "
            else:
                pos += "1person, "
        elif count == 2:
            if girl_count == 2:
                pos += "2girls, "
            elif boy_count == 2:
                pos += "2boys, "
            elif girl_count == 1 and boy_count == 1:
                pos += "1girl, 1boy, "
            else:
                pos += "2people, "
        else:
            pos += f"{count}people, "

        # 4. Scene — before subject strings
        r_loc = get_smart_random(LOCATIONS, seed) if location == "Random" else location
        r_light = get_smart_random(LIGHTING, seed + 1) if lighting == "Random" else lighting
        r_cam = get_smart_random(CAMERAS, seed + 2) if camera == "Random" else camera
        pos += f"{r_loc}, {r_light}, {r_cam}"

        # 5. Subject Assembly
        if count > 0:
            pos += ", "
        for i, subj in enumerate(subjects):
            pos += subj
            if use_break and i < count - 1:
                pos += " BREAK "
            elif i < count - 1:
                pos += ", "
        # 6. Negative Prompt
        neg_sources = ["source_furry", "source_cartoon"]
        # strong_anime_bias: flip anime-ish tags toward positive look, relax them in negative
        if strong_anime_bias:
            # Drop explicit anime/cartoon negatives
            neg_sources = ["source_furry"]

        neg = (
            "canine_face, dog_face, wolf_face, snout, muzzle, animal_face, anthro_face, furry_face, "
            "human_penis, human_genitalia, uncut_penis, circumcised_penis, human_pussy, human_vagina, human_anus, "
            "score_6, score_5, score_4, rating_source_anime, rating_source_cartoon, anime, cartoon, comic, manga, "
            "vector art, 2d drawing, 3d render, cgi, digital painting, illustration, drawing, sketch, blurry, low quality, "
            "deformed, mutated"
        )
        if not nsfw_mode:
            neg += ", nude, nipples, pussy, penis, sex, nsfw"

        neg = merge_negative_prompt_tags(neg)

        print(f"[CyberRealistic Pony Master Prompt] {pos}")
        return (pos, neg)

# --- MAPPINGS ---

NODE_CLASS_MAPPINGS = {
    "CR_Pony_Master": CR_Pony_Master,
    "CR_Pony_Subject": CR_Pony_Subject,
    "CR_Pony_Subject_Female": CR_Pony_Subject_Female,
    "CR_Pony_Subject_Male": CR_Pony_Subject_Male,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CR_Pony_Master": "CyberRealistic Master Prompt",
    "CR_Pony_Subject": "CyberRealistic Subject",
    "CR_Pony_Subject_Female": "CyberRealistic Female Subject",
    "CR_Pony_Subject_Male": "CyberRealistic Male Subject",
}

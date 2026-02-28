"""
Structure & Interaction Terminology Constants (格局 & 合化 术语)
================================================================

Comprehensive bilingual terminology for Chart Structures (Cách Cục),
Heavenly Stem Combinations (Thiên Can Ngũ Hợp), Earthly Branch
Interactions (Địa Chi Hợp Hoá), and related classical concepts.

Each entry is a tuple: (chinese, pinyin, english, vietnamese).
Lookup tables map Chinese keys → full terminology tuples.
"""

from typing import Dict, List, Tuple

# Format: (chinese, pinyin, english, vietnamese)
Term = Tuple[str, str, str, str]

# ============================================================
# I. BÁT CHÍNH CÁCH — Eight Regular Structures (八正格)
# ============================================================

DIRECT_OFFICER_STRUCTURE: Term = (
    "正官格", "Zhèng Guān Gé", "Direct Officer Structure", "Chính Quan Cách",
)
SEVEN_KILLINGS_STRUCTURE: Term = (
    "七杀格", "Qī Shā Gé", "Seven Killings Structure", "Thất Sát Cách",
)
DIRECT_RESOURCE_STRUCTURE: Term = (
    "正印格", "Zhèng Yìn Gé", "Direct Resource Structure", "Chính Ấn Cách",
)
INDIRECT_RESOURCE_STRUCTURE: Term = (
    "偏印格", "Piān Yìn Gé", "Indirect Resource Structure", "Thiên Ấn Cách",
)
DIRECT_WEALTH_STRUCTURE: Term = (
    "正财格", "Zhèng Cái Gé", "Direct Wealth Structure", "Chính Tài Cách",
)
INDIRECT_WEALTH_STRUCTURE: Term = (
    "偏财格", "Piān Cái Gé", "Indirect Wealth Structure", "Thiên Tài Cách",
)
EATING_GOD_STRUCTURE: Term = (
    "食神格", "Shí Shén Gé", "Eating God Structure", "Thực Thần Cách",
)
HURTING_OFFICER_STRUCTURE: Term = (
    "伤官格", "Shāng Guān Gé", "Hurting Officer Structure", "Thương Quan Cách",
)

EIGHT_REGULAR_STRUCTURES: List[Term] = [
    DIRECT_OFFICER_STRUCTURE,
    SEVEN_KILLINGS_STRUCTURE,
    DIRECT_RESOURCE_STRUCTURE,
    INDIRECT_RESOURCE_STRUCTURE,
    DIRECT_WEALTH_STRUCTURE,
    INDIRECT_WEALTH_STRUCTURE,
    EATING_GOD_STRUCTURE,
    HURTING_OFFICER_STRUCTURE,
]

# Ten-God → Bát Chính Cách mapping (比肩 & 劫财 excluded — they cannot
# serve as Useful God in the Eight Regular Structures)
TEN_GOD_TO_REGULAR_STRUCTURE: Dict[str, Term] = {
    "正官": DIRECT_OFFICER_STRUCTURE,
    "七杀": SEVEN_KILLINGS_STRUCTURE,
    "正印": DIRECT_RESOURCE_STRUCTURE,
    "偏印": INDIRECT_RESOURCE_STRUCTURE,
    "正财": DIRECT_WEALTH_STRUCTURE,
    "偏财": INDIRECT_WEALTH_STRUCTURE,
    "食神": EATING_GOD_STRUCTURE,
    "伤官": HURTING_OFFICER_STRUCTURE,
}

# ============================================================
# II-A. NGOẠI CÁCH — Vượng Cực Group (Extreme Prosperous)
# ============================================================

ESTABLISH_FORTUNE_STRUCTURE: Term = (
    "建禄格", "Jiàn Lù Gé", "Establish Fortune Structure", "Kiến Lộc Cách",
)
GOAT_BLADE_STRUCTURE: Term = (
    "羊刃格", "Yáng Rèn Gé", "Goat Blade Structure", "Dương Nhẫn Cách",
)

# --- Ngũ Hành Chuyên Vượng Cách (Five-Element Dominance Structures) ---

WOOD_DOMINANCE_STRUCTURE: Term = (
    "曲直格", "Qū Zhí Gé", "Bent & Straight Structure", "Khúc Trực Cách",
)
FIRE_DOMINANCE_STRUCTURE: Term = (
    "炎上格", "Yán Shàng Gé", "Blazing Upward Structure", "Viêm Thượng Cách",
)
EARTH_DOMINANCE_STRUCTURE: Term = (
    "稼穡格", "Jià Sè Gé", "Sowing & Reaping Structure", "Giá Sắc Cách",
)
METAL_DOMINANCE_STRUCTURE: Term = (
    "从革格", "Cóng Gé Gé", "Following Reform Structure", "Tòng Cách Cách",
)
WATER_DOMINANCE_STRUCTURE: Term = (
    "润下格", "Rùn Xià Gé", "Moistening Downward Structure", "Nhuận Hạ Cách",
)

FIVE_ELEMENT_DOMINANCE_STRUCTURES: List[Term] = [
    WOOD_DOMINANCE_STRUCTURE,
    FIRE_DOMINANCE_STRUCTURE,
    EARTH_DOMINANCE_STRUCTURE,
    METAL_DOMINANCE_STRUCTURE,
    WATER_DOMINANCE_STRUCTURE,
]

# Element key → dominance structure
ELEMENT_TO_DOMINANCE_STRUCTURE: Dict[str, Term] = {
    "Wood": WOOD_DOMINANCE_STRUCTURE,
    "Fire": FIRE_DOMINANCE_STRUCTURE,
    "Earth": EARTH_DOMINANCE_STRUCTURE,
    "Metal": METAL_DOMINANCE_STRUCTURE,
    "Water": WATER_DOMINANCE_STRUCTURE,
}

EXTREME_PROSPEROUS_STRUCTURES: List[Term] = [
    ESTABLISH_FORTUNE_STRUCTURE,
    GOAT_BLADE_STRUCTURE,
    *FIVE_ELEMENT_DOMINANCE_STRUCTURES,
]

# ============================================================
# II-B. NGOẠI CÁCH — Tòng Group (Following / Submission)
# ============================================================

FOLLOW_WEALTH_STRUCTURE: Term = (
    "从财格", "Cóng Cái Gé", "Follow Wealth Structure", "Tòng Tài Cách",
)
FOLLOW_OFFICER_STRUCTURE: Term = (
    "从官杀格", "Cóng Guān Shā Gé", "Follow Officer-Killings Structure",
    "Tòng Quan Sát Cách",
)
FOLLOW_OUTPUT_STRUCTURE: Term = (
    "从食伤格", "Cóng Shí Shāng Gé", "Follow Output Structure",
    "Tòng Thực Thương Cách",
)
FOLLOW_STRENGTH_STRUCTURE: Term = (
    "从强格", "Cóng Qiáng Gé", "Follow Strength Structure", "Tòng Cường Cách",
)
FOLLOW_MOMENTUM_STRUCTURE: Term = (
    "从势格", "Cóng Shì Gé", "Follow Momentum Structure", "Tòng Thế Cách",
)

FOLLOW_STRUCTURES: List[Term] = [
    FOLLOW_WEALTH_STRUCTURE,
    FOLLOW_OFFICER_STRUCTURE,
    FOLLOW_OUTPUT_STRUCTURE,
    FOLLOW_STRENGTH_STRUCTURE,
    FOLLOW_MOMENTUM_STRUCTURE,
]

# ============================================================
# II-C. NGOẠI CÁCH — Hóa Group (Transformation)
# ============================================================

TRANSFORM_EARTH_STRUCTURE: Term = (
    "化土格", "Huà Tǔ Gé", "Transform to Earth Structure", "Hóa Thổ Cách",
)
TRANSFORM_METAL_STRUCTURE: Term = (
    "化金格", "Huà Jīn Gé", "Transform to Metal Structure", "Hóa Kim Cách",
)
TRANSFORM_WATER_STRUCTURE: Term = (
    "化水格", "Huà Shuǐ Gé", "Transform to Water Structure", "Hóa Thủy Cách",
)
TRANSFORM_WOOD_STRUCTURE: Term = (
    "化木格", "Huà Mù Gé", "Transform to Wood Structure", "Hóa Mộc Cách",
)
TRANSFORM_FIRE_STRUCTURE: Term = (
    "化火格", "Huà Huǒ Gé", "Transform to Fire Structure", "Hóa Hỏa Cách",
)

TRANSFORM_STRUCTURES: List[Term] = [
    TRANSFORM_EARTH_STRUCTURE,
    TRANSFORM_METAL_STRUCTURE,
    TRANSFORM_WATER_STRUCTURE,
    TRANSFORM_WOOD_STRUCTURE,
    TRANSFORM_FIRE_STRUCTURE,
]

# Element key → transformation structure
ELEMENT_TO_TRANSFORM_STRUCTURE: Dict[str, Term] = {
    "Earth": TRANSFORM_EARTH_STRUCTURE,
    "Metal": TRANSFORM_METAL_STRUCTURE,
    "Water": TRANSFORM_WATER_STRUCTURE,
    "Wood": TRANSFORM_WOOD_STRUCTURE,
    "Fire": TRANSFORM_FIRE_STRUCTURE,
}

# ============================================================
# II-D. NGOẠI CÁCH — Special Composite Structures
# ============================================================

EATING_GOD_CONTROLS_KILLINGS: Term = (
    "食神制杀格", "Shí Shén Zhì Shā Gé",
    "Eating God Controls Killings Structure", "Thực Thần Chế Sát Cách",
)
HURTING_OFFICER_WITH_RESOURCE: Term = (
    "伤官配印格", "Shāng Guān Pèi Yìn Gé",
    "Hurting Officer Paired with Resource Structure", "Thương Quan Phối Ấn Cách",
)
HURTING_OFFICER_MEETS_OFFICER: Term = (
    "伤官见官格", "Shāng Guān Jiàn Guān Gé",
    "Hurting Officer Meets Officer Structure", "Thương Quan Kiến Quan Cách",
)
WEALTH_NOURISHES_BOTH: Term = (
    "财滋两旺格", "Cái Zī Liǎng Wàng Gé",
    "Wealth Nourishes Both Prosperous Structure", "Tài Tư Lưỡng Vượng Cách",
)
WEALTH_AND_RESOURCE_COMPLETE: Term = (
    "财印双全格", "Cái Yìn Shuāng Quán Gé",
    "Wealth & Resource Complete Structure", "Tài Ấn Song Toàn Cách",
)
KILLINGS_AND_RESOURCE_MUTUAL: Term = (
    "杀印相生格", "Shā Yìn Xiāng Shēng Gé",
    "Killings & Resource Mutually Generating Structure", "Sát Ấn Tương Sinh Cách",
)
FLYING_FORTUNE_HORSE: Term = (
    "飞天禄马格", "Fēi Tiān Lù Mǎ Gé",
    "Flying Heaven Fortune Horse Structure", "Phi Thiên Lộc Mã Cách",
)
WELL_RAILING_CROSS: Term = (
    "井栏叉甲格", "Jǐng Lán Chā Jiǎ Gé",
    "Well Railing Cross Structure", "Tỉnh Lan Thoa Giáp Cách",
)

SPECIAL_COMPOSITE_STRUCTURES: List[Term] = [
    EATING_GOD_CONTROLS_KILLINGS,
    HURTING_OFFICER_WITH_RESOURCE,
    HURTING_OFFICER_MEETS_OFFICER,
    WEALTH_NOURISHES_BOTH,
    WEALTH_AND_RESOURCE_COMPLETE,
    KILLINGS_AND_RESOURCE_MUTUAL,
    FLYING_FORTUNE_HORSE,
    WELL_RAILING_CROSS,
]

# ============================================================
# Master lookup: Chinese structure name → Term
# ============================================================

ALL_STRUCTURES: List[Term] = [
    *EIGHT_REGULAR_STRUCTURES,
    *EXTREME_PROSPEROUS_STRUCTURES,
    *FOLLOW_STRUCTURES,
    *TRANSFORM_STRUCTURES,
    *SPECIAL_COMPOSITE_STRUCTURES,
]

STRUCTURE_LOOKUP: Dict[str, Term] = {t[0]: t for t in ALL_STRUCTURES}

# ============================================================
# III. Structure Category terms
# ============================================================

CATEGORY_REGULAR: Term = (
    "八正格", "Bā Zhèng Gé", "Eight Regular Structures", "Bát Chính Cách",
)
CATEGORY_OUTER: Term = (
    "外格", "Wài Gé", "Outer Structures", "Ngoại Cách",
)
CATEGORY_SPECIAL: Term = (
    "特殊格局", "Tè Shū Gé Jú", "Special Structures", "Đặc Biệt Cách",
)
CATEGORY_EXTREME_PROSPEROUS: Term = (
    "旺极格", "Wàng Jí Gé", "Extreme Prosperous", "Vượng Cực Cách",
)
CATEGORY_FOLLOW: Term = (
    "从格", "Cóng Gé", "Follow Structures", "Tòng Cách",
)
CATEGORY_TRANSFORM: Term = (
    "化格", "Huà Gé", "Transform Structures", "Hóa Cách",
)
CATEGORY_FIVE_DOMINANCE: Term = (
    "五行专旺格", "Wǔ Xíng Zhuān Wàng Gé",
    "Five-Element Dominance Structures", "Ngũ Hành Chuyên Vượng Cách",
)

STRUCTURE_CATEGORIES: List[Term] = [
    CATEGORY_REGULAR,
    CATEGORY_OUTER,
    CATEGORY_SPECIAL,
    CATEGORY_EXTREME_PROSPEROUS,
    CATEGORY_FOLLOW,
    CATEGORY_TRANSFORM,
    CATEGORY_FIVE_DOMINANCE,
]

# ============================================================
# IV. Structure Quality / Outcome terms
# ============================================================

QUALITY_ESTABLISHED: Term = (
    "成格", "Chéng Gé", "Structure Established", "Thành Cách",
)
QUALITY_BROKEN: Term = (
    "破格", "Pò Gé", "Structure Broken", "Phá Cách",
)
QUALITY_PURE: Term = (
    "格局清纯", "Gé Jú Qīng Chún", "Pure Structure", "Cách Cục Thanh Thuần",
)
QUALITY_TURBID: Term = (
    "格局混浊", "Gé Jú Hùn Zhuó", "Turbid Structure", "Cách Cục Hỗn Trọc",
)

STRUCTURE_QUALITY_TERMS: List[Term] = [
    QUALITY_ESTABLISHED,
    QUALITY_BROKEN,
    QUALITY_PURE,
    QUALITY_TURBID,
]

# ============================================================
# V. THIÊN CAN NGŨ HỢP — Heavenly Stem Five Combinations (天干五合)
#
# These are *pair instances* — they define WHICH stems can combine
# and WHAT element they transform into.  Whether the transformation
# actually succeeds depends on the four conditions evaluated at
# runtime (see §V-B below).
# ============================================================

# --- V-A. Pair Instances (Cặp hợp — dữ liệu tĩnh) ---

STEM_COMBINE_JIA_JI: Term = (
    "甲己合", "Jiǎ Jǐ Hé",
    "Jia-Ji Combination (→ Earth)", "Giáp Kỷ hợp (→ Thổ)",
)
STEM_COMBINE_YI_GENG: Term = (
    "乙庚合", "Yǐ Gēng Hé",
    "Yi-Geng Combination (→ Metal)", "Ất Canh hợp (→ Kim)",
)
STEM_COMBINE_BING_XIN: Term = (
    "丙辛合", "Bǐng Xīn Hé",
    "Bing-Xin Combination (→ Water)", "Bính Tân hợp (→ Thủy)",
)
STEM_COMBINE_DING_REN: Term = (
    "丁壬合", "Dīng Rén Hé",
    "Ding-Ren Combination (→ Wood)", "Đinh Nhâm hợp (→ Mộc)",
)
STEM_COMBINE_WU_GUI: Term = (
    "戊癸合", "Wù Guǐ Hé",
    "Wu-Gui Combination (→ Fire)", "Mậu Quý hợp (→ Hỏa)",
)

HEAVENLY_STEM_FIVE_COMBINATIONS: List[Term] = [
    STEM_COMBINE_JIA_JI,
    STEM_COMBINE_YI_GENG,
    STEM_COMBINE_BING_XIN,
    STEM_COMBINE_DING_REN,
    STEM_COMBINE_WU_GUI,
]

# Stem pair → combination term (instance)
STEM_PAIR_TO_COMBINATION: Dict[frozenset, Term] = {
    frozenset({"甲", "己"}): STEM_COMBINE_JIA_JI,
    frozenset({"乙", "庚"}): STEM_COMBINE_YI_GENG,
    frozenset({"丙", "辛"}): STEM_COMBINE_BING_XIN,
    frozenset({"丁", "壬"}): STEM_COMBINE_DING_REN,
    frozenset({"戊", "癸"}): STEM_COMBINE_WU_GUI,
}

# Stem pair → target element (Hóa Thần 化神)
STEM_PAIR_TO_ELEMENT: Dict[frozenset, str] = {
    frozenset({"甲", "己"}): "Earth",
    frozenset({"乙", "庚"}): "Metal",
    frozenset({"丙", "辛"}): "Water",
    frozenset({"丁", "壬"}): "Wood",
    frozenset({"戊", "癸"}): "Fire",
}

# --- V-B. Transformation Conditions (Điều kiện Hợp Hóa) ---
#
# All four conditions must be met for a stem pair to successfully
# transform (Hóa).  If any condition fails, the pair remains in
# the "bound" state (Hợp Nhi Bất Hóa / Hợp Trú).

CONDITION_ADJACENCY: Term = (
    "紧贴", "Jǐn Tiē",
    "Adjacency (pillars must be next to each other)",
    "Kề Sát (hai trụ phải kề nhau)",
)
CONDITION_REMOTE_COMBINE: Term = (
    "遥合", "Yáo Hé",
    "Remote Combination (non-adjacent; affinity only, cannot transform)",
    "Diệu Hợp (hợp xa; chỉ có tình, không hóa được)",
)
CONDITION_MONTH_ORDER: Term = (
    "月令得气", "Yuè Lìng Dé Qì",
    "Month Order Support (month must prosper or generate the transformed element)",
    "Nguyệt Lệnh Đắc Khí (tháng sinh phải vượng hoặc sinh Hóa Thần)",
)
CONDITION_LEADING_STEM: Term = (
    "引化", "Yǐn Huà",
    "Leading Stem (transformed element exposed on other Heavenly Stems)",
    "Dẫn Hóa (hành Hóa Thần lộ trên Thiên Can khác)",
)
CONDITION_NO_OBSTRUCTION: Term = (
    "无阻碍", "Wú Zǔ Ài",
    "No Obstruction (no clash/jealousy breaking the combination)",
    "Không Bị Ngăn Trở (không xung, không tranh hợp)",
)

TRANSFORMATION_GOD: Term = (
    "化神", "Huà Shén",
    "Transformation God (the resulting element of a successful combination)",
    "Hóa Thần (ngũ hành kết quả khi hợp hóa thành công)",
)

TRANSFORMATION_CONDITIONS: List[Term] = [
    CONDITION_ADJACENCY,
    CONDITION_MONTH_ORDER,
    CONDITION_LEADING_STEM,
    CONDITION_NO_OBSTRUCTION,
]

TRANSFORMATION_RELATED_TERMS: List[Term] = [
    *TRANSFORMATION_CONDITIONS,
    CONDITION_REMOTE_COMBINE,
    TRANSFORMATION_GOD,
]

# ============================================================
# VI. Combination Classification (合化分类)
#
# Three-level hierarchy:
#   Level 1 — Structure (input pattern — how many stems contest)
#   Level 2 — Outcome  (resulting state after evaluating §V-B conditions)
#   Level 3 — Modifier (external events that change the outcome)
# ============================================================

# --- Level 1: Structure (Cấu trúc đầu vào) ---

COMBINE_STRUCTURE_SINGLE: Term = (
    "单合", "Dān Hé", "Single Combination (1-to-1)", "Đơn Hợp",
)
COMBINE_STRUCTURE_JEALOUSY: Term = (
    "争合", "Zhēng Hé", "Jealous Combination (N-to-1)", "Tranh Hợp",
)

COMBINE_STRUCTURE_TERMS: List[Term] = [
    COMBINE_STRUCTURE_SINGLE,
    COMBINE_STRUCTURE_JEALOUSY,
]

# --- Level 2: Outcome (Kết quả) ---

COMBINE_OUTCOME_TRANSFORMED: Term = (
    "合化", "Hé Huà", "Combined & Transformed", "Hợp Hóa",
)
COMBINE_OUTCOME_BLOCKED: Term = (
    "合而不化", "Hé Ér Bù Huà",
    "Combined but Not Transformed (bound/locked)", "Hợp Nhi Bất Hóa",
)
# 合住 (Hợp Trú) is a consequence of 合而不化: when stems/branches
# combine but fail to transform, they "lock" each other and lose
# their original function.  Modeled as an attribute, not a separate state.
COMBINE_OUTCOME_BLOCKED_NOTE = (
    "合住 (Hợp Trú / Bound) is the practical effect of 合而不化. "
    "The combined elements are neutralized and cannot act independently."
)

COMBINE_OUTCOME_TERMS: List[Term] = [
    COMBINE_OUTCOME_TRANSFORMED,
    COMBINE_OUTCOME_BLOCKED,
]

# --- Level 3: Modifiers (Biến động / External interference) ---

COMBINE_MODIFIER_CLASHED: Term = (
    "冲破合", "Chōng Pò Hé",
    "Combination Broken by Clash", "Xung Phá Hợp",
)
COMBINE_MODIFIER_RESOLVED: Term = (
    "解合", "Jiě Hé", "Combination Resolved / Dissolved", "Giải Hợp",
)

COMBINE_MODIFIER_TERMS: List[Term] = [
    COMBINE_MODIFIER_CLASHED,
    COMBINE_MODIFIER_RESOLVED,
]

# --- Flat list (all combination classification terms) ---

COMBINATION_STATUS_TERMS: List[Term] = [
    *COMBINE_STRUCTURE_TERMS,
    *COMBINE_OUTCOME_TERMS,
    *COMBINE_MODIFIER_TERMS,
]

# ============================================================
# VII. THIÊN CAN TƯƠNG XUNG — Heavenly Stem Clashes (天干相冲)
# ============================================================

STEM_CLASH_JIA_GENG: Term = (
    "甲庚冲", "Jiǎ Gēng Chōng", "Jia-Geng Clash", "Giáp Canh xung",
)
STEM_CLASH_YI_XIN: Term = (
    "乙辛冲", "Yǐ Xīn Chōng", "Yi-Xin Clash", "Ất Tân xung",
)
STEM_CLASH_BING_REN: Term = (
    "丙壬冲", "Bǐng Rén Chōng", "Bing-Ren Clash", "Bính Nhâm xung",
)
STEM_CLASH_DING_GUI: Term = (
    "丁癸冲", "Dīng Guǐ Chōng", "Ding-Gui Clash", "Đinh Quý xung",
)

HEAVENLY_STEM_CLASHES: List[Term] = [
    STEM_CLASH_JIA_GENG,
    STEM_CLASH_YI_XIN,
    STEM_CLASH_BING_REN,
    STEM_CLASH_DING_GUI,
]

STEM_CLASH_PAIR_TO_TERM: Dict[frozenset, Term] = {
    frozenset({"甲", "庚"}): STEM_CLASH_JIA_GENG,
    frozenset({"乙", "辛"}): STEM_CLASH_YI_XIN,
    frozenset({"丙", "壬"}): STEM_CLASH_BING_REN,
    frozenset({"丁", "癸"}): STEM_CLASH_DING_GUI,
}

# ============================================================
# VIII. LỤC HỢP — Six Earthly Branch Combinations (地支六合)
# ============================================================

LIU_HE_ZI_CHOU: Term = (
    "子丑合化土", "Zǐ Chǒu Hé Huà Tǔ",
    "Zi-Chou combine, transform to Earth", "Tí Sửu hợp hóa Thổ",
)
LIU_HE_YIN_HAI: Term = (
    "寅亥合化木", "Yín Hài Hé Huà Mù",
    "Yin-Hai combine, transform to Wood", "Dần Hợi hợp hóa Mộc",
)
LIU_HE_MAO_XU: Term = (
    "卯戌合化火", "Mǎo Xū Hé Huà Huǒ",
    "Mao-Xu combine, transform to Fire", "Mão Tuất hợp hóa Hỏa",
)
LIU_HE_CHEN_YOU: Term = (
    "辰酉合化金", "Chén Yǒu Hé Huà Jīn",
    "Chen-You combine, transform to Metal", "Thìn Dậu hợp hóa Kim",
)
LIU_HE_SI_SHEN: Term = (
    "巳申合化水", "Sì Shēn Hé Huà Shuǐ",
    "Si-Shen combine, transform to Water", "Tỵ Thân hợp hóa Thủy",
)
LIU_HE_WU_WEI: Term = (
    "午未合化火", "Wǔ Wèi Hé Huà Huǒ",
    "Wu-Wei combine, transform to Fire", "Ngọ Mùi hợp hóa Hỏa",
)

SIX_BRANCH_COMBINATIONS: List[Term] = [
    LIU_HE_ZI_CHOU,
    LIU_HE_YIN_HAI,
    LIU_HE_MAO_XU,
    LIU_HE_CHEN_YOU,
    LIU_HE_SI_SHEN,
    LIU_HE_WU_WEI,
]

BRANCH_PAIR_TO_LIU_HE: Dict[frozenset, Term] = {
    frozenset({"子", "丑"}): LIU_HE_ZI_CHOU,
    frozenset({"寅", "亥"}): LIU_HE_YIN_HAI,
    frozenset({"卯", "戌"}): LIU_HE_MAO_XU,
    frozenset({"辰", "酉"}): LIU_HE_CHEN_YOU,
    frozenset({"巳", "申"}): LIU_HE_SI_SHEN,
    frozenset({"午", "未"}): LIU_HE_WU_WEI,
}

# Lục Hợp → transformed element
LIU_HE_PAIR_TO_ELEMENT: Dict[frozenset, str] = {
    frozenset({"子", "丑"}): "Earth",
    frozenset({"寅", "亥"}): "Wood",
    frozenset({"卯", "戌"}): "Fire",
    frozenset({"辰", "酉"}): "Metal",
    frozenset({"巳", "申"}): "Water",
    frozenset({"午", "未"}): "Fire",
}

# ============================================================
# IX. TAM HỢP CỤC — Three Combination Frames (地支三合)
# ============================================================

SAN_HE_WATER: Term = (
    "申子辰合水局", "Shēn Zǐ Chén Hé Shuǐ Jú",
    "Shen-Zi-Chen Water Frame", "Thân Tí Thìn hợp Thủy cục",
)
SAN_HE_FIRE: Term = (
    "寅午戌合火局", "Yín Wǔ Xū Hé Huǒ Jú",
    "Yin-Wu-Xu Fire Frame", "Dần Ngọ Tuất hợp Hỏa cục",
)
SAN_HE_WOOD: Term = (
    "亥卯未合木局", "Hài Mǎo Wèi Hé Mù Jú",
    "Hai-Mao-Wei Wood Frame", "Hợi Mão Mùi hợp Mộc cục",
)
SAN_HE_METAL: Term = (
    "巳酉丑合金局", "Sì Yǒu Chǒu Hé Jīn Jú",
    "Si-You-Chou Metal Frame", "Tỵ Dậu Sửu hợp Kim cục",
)

THREE_COMBINATION_FRAMES: List[Term] = [
    SAN_HE_WATER,
    SAN_HE_FIRE,
    SAN_HE_WOOD,
    SAN_HE_METAL,
]

SAN_HE_SET_TO_TERM: Dict[frozenset, Term] = {
    frozenset({"申", "子", "辰"}): SAN_HE_WATER,
    frozenset({"寅", "午", "戌"}): SAN_HE_FIRE,
    frozenset({"亥", "卯", "未"}): SAN_HE_WOOD,
    frozenset({"巳", "酉", "丑"}): SAN_HE_METAL,
}

SAN_HE_SET_TO_ELEMENT: Dict[frozenset, str] = {
    frozenset({"申", "子", "辰"}): "Water",
    frozenset({"寅", "午", "戌"}): "Fire",
    frozenset({"亥", "卯", "未"}): "Wood",
    frozenset({"巳", "酉", "丑"}): "Metal",
}

# ============================================================
# X. BÁN TAM HỢP — Half Three Combinations (半三合)
# ============================================================

HALF_THREE_COMBINATION: Term = (
    "半三合", "Bàn Sān Hé", "Half Three Combination", "Bán Tam Hợp",
)

BAN_SAN_HE_SHENG: Term = (
    "生地半合", "Shēng Dì Bàn Hé",
    "Birth-Phase Half Combination", "Sinh Địa Bán Hợp",
)
BAN_SAN_HE_MU: Term = (
    "墓地半合", "Mù Dì Bàn Hé",
    "Grave-Phase Half Combination", "Mộ Địa Bán Hợp",
)

# Birth-phase half combos (long sinh + đế vượng)
BAN_SAN_HE_BIRTH_PAIRS: Dict[frozenset, str] = {
    frozenset({"申", "子"}): "Water",
    frozenset({"寅", "午"}): "Fire",
    frozenset({"亥", "卯"}): "Wood",
    frozenset({"巳", "酉"}): "Metal",
}

# Grave-phase half combos (đế vượng + mộ)
BAN_SAN_HE_GRAVE_PAIRS: Dict[frozenset, str] = {
    frozenset({"子", "辰"}): "Water",
    frozenset({"午", "戌"}): "Fire",
    frozenset({"卯", "未"}): "Wood",
    frozenset({"酉", "丑"}): "Metal",
}

# ============================================================
# XI. TAM HỘI CỤC — Directional Combination Frames (三会局)
# ============================================================

SAN_HUI_WOOD: Term = (
    "寅卯辰会木局", "Yín Mǎo Chén Huì Mù Jú",
    "Yin-Mao-Chen Wood Directional Frame", "Dần Mão Thìn hội Mộc cục",
)
SAN_HUI_FIRE: Term = (
    "巳午未会火局", "Sì Wǔ Wèi Huì Huǒ Jú",
    "Si-Wu-Wei Fire Directional Frame", "Tỵ Ngọ Mùi hội Hỏa cục",
)
SAN_HUI_METAL: Term = (
    "申酉戌会金局", "Shēn Yǒu Xū Huì Jīn Jú",
    "Shen-You-Xu Metal Directional Frame", "Thân Dậu Tuất hội Kim cục",
)
SAN_HUI_WATER: Term = (
    "亥子丑会水局", "Hài Zǐ Chǒu Huì Shuǐ Jú",
    "Hai-Zi-Chou Water Directional Frame", "Hợi Tí Sửu hội Thủy cục",
)

DIRECTIONAL_COMBINATION_FRAMES: List[Term] = [
    SAN_HUI_WOOD,
    SAN_HUI_FIRE,
    SAN_HUI_METAL,
    SAN_HUI_WATER,
]

SAN_HUI_SET_TO_TERM: Dict[frozenset, Term] = {
    frozenset({"寅", "卯", "辰"}): SAN_HUI_WOOD,
    frozenset({"巳", "午", "未"}): SAN_HUI_FIRE,
    frozenset({"申", "酉", "戌"}): SAN_HUI_METAL,
    frozenset({"亥", "子", "丑"}): SAN_HUI_WATER,
}

SAN_HUI_SET_TO_ELEMENT: Dict[frozenset, str] = {
    frozenset({"寅", "卯", "辰"}): "Wood",
    frozenset({"巳", "午", "未"}): "Fire",
    frozenset({"申", "酉", "戌"}): "Metal",
    frozenset({"亥", "子", "丑"}): "Water",
}

# ============================================================
# XII. LỤC XUNG — Six Clashes (六冲)
# ============================================================

LIU_CHONG_ZI_WU: Term = (
    "子午冲", "Zǐ Wǔ Chōng", "Zi-Wu Clash", "Tí Ngọ xung",
)
LIU_CHONG_CHOU_WEI: Term = (
    "丑未冲", "Chǒu Wèi Chōng", "Chou-Wei Clash", "Sửu Mùi xung",
)
LIU_CHONG_YIN_SHEN: Term = (
    "寅申冲", "Yín Shēn Chōng", "Yin-Shen Clash", "Dần Thân xung",
)
LIU_CHONG_MAO_YOU: Term = (
    "卯酉冲", "Mǎo Yǒu Chōng", "Mao-You Clash", "Mão Dậu xung",
)
LIU_CHONG_CHEN_XU: Term = (
    "辰戌冲", "Chén Xū Chōng", "Chen-Xu Clash", "Thìn Tuất xung",
)
LIU_CHONG_SI_HAI: Term = (
    "巳亥冲", "Sì Hài Chōng", "Si-Hai Clash", "Tỵ Hợi xung",
)

SIX_CLASHES: List[Term] = [
    LIU_CHONG_ZI_WU,
    LIU_CHONG_CHOU_WEI,
    LIU_CHONG_YIN_SHEN,
    LIU_CHONG_MAO_YOU,
    LIU_CHONG_CHEN_XU,
    LIU_CHONG_SI_HAI,
]

BRANCH_PAIR_TO_LIU_CHONG: Dict[frozenset, Term] = {
    frozenset({"子", "午"}): LIU_CHONG_ZI_WU,
    frozenset({"丑", "未"}): LIU_CHONG_CHOU_WEI,
    frozenset({"寅", "申"}): LIU_CHONG_YIN_SHEN,
    frozenset({"卯", "酉"}): LIU_CHONG_MAO_YOU,
    frozenset({"辰", "戌"}): LIU_CHONG_CHEN_XU,
    frozenset({"巳", "亥"}): LIU_CHONG_SI_HAI,
}

# ============================================================
# XIII. LỤC HẠI — Six Harms (六害)
# ============================================================

LIU_HAI_ZI_WEI: Term = (
    "子未害", "Zǐ Wèi Hài", "Zi-Wei Harm", "Tí Mùi hại",
)
LIU_HAI_CHOU_WU: Term = (
    "丑午害", "Chǒu Wǔ Hài", "Chou-Wu Harm", "Sửu Ngọ hại",
)
LIU_HAI_YIN_SI: Term = (
    "寅巳害", "Yín Sì Hài", "Yin-Si Harm", "Dần Tỵ hại",
)
LIU_HAI_MAO_CHEN: Term = (
    "卯辰害", "Mǎo Chén Hài", "Mao-Chen Harm", "Mão Thìn hại",
)
LIU_HAI_SHEN_HAI: Term = (
    "申亥害", "Shēn Hài Hài", "Shen-Hai Harm", "Thân Hợi hại",
)
LIU_HAI_YOU_XU: Term = (
    "酉戌害", "Yǒu Xū Hài", "You-Xu Harm", "Dậu Tuất hại",
)

SIX_HARMS: List[Term] = [
    LIU_HAI_ZI_WEI,
    LIU_HAI_CHOU_WU,
    LIU_HAI_YIN_SI,
    LIU_HAI_MAO_CHEN,
    LIU_HAI_SHEN_HAI,
    LIU_HAI_YOU_XU,
]

BRANCH_PAIR_TO_LIU_HAI: Dict[frozenset, Term] = {
    frozenset({"子", "未"}): LIU_HAI_ZI_WEI,
    frozenset({"丑", "午"}): LIU_HAI_CHOU_WU,
    frozenset({"寅", "巳"}): LIU_HAI_YIN_SI,
    frozenset({"卯", "辰"}): LIU_HAI_MAO_CHEN,
    frozenset({"申", "亥"}): LIU_HAI_SHEN_HAI,
    frozenset({"酉", "戌"}): LIU_HAI_YOU_XU,
}

# ============================================================
# XIV. LỤC PHÁ — Six Destructions (六破)
# ============================================================

LIU_PO_ZI_YOU: Term = (
    "子酉破", "Zǐ Yǒu Pò", "Zi-You Destruction", "Tí Dậu phá",
)
LIU_PO_CHOU_CHEN: Term = (
    "丑辰破", "Chǒu Chén Pò", "Chou-Chen Destruction", "Sửu Thìn phá",
)
LIU_PO_YIN_HAI: Term = (
    "寅亥破", "Yín Hài Pò", "Yin-Hai Destruction", "Dần Hợi phá",
)
LIU_PO_MAO_WU: Term = (
    "卯午破", "Mǎo Wǔ Pò", "Mao-Wu Destruction", "Mão Ngọ phá",
)
LIU_PO_SI_SHEN: Term = (
    "巳申破", "Sì Shēn Pò", "Si-Shen Destruction", "Tỵ Thân phá",
)
LIU_PO_WEI_XU: Term = (
    "未戌破", "Wèi Xū Pò", "Wei-Xu Destruction", "Mùi Tuất phá",
)

SIX_DESTRUCTIONS: List[Term] = [
    LIU_PO_ZI_YOU,
    LIU_PO_CHOU_CHEN,
    LIU_PO_YIN_HAI,
    LIU_PO_MAO_WU,
    LIU_PO_SI_SHEN,
    LIU_PO_WEI_XU,
]

BRANCH_PAIR_TO_LIU_PO: Dict[frozenset, Term] = {
    frozenset({"子", "酉"}): LIU_PO_ZI_YOU,
    frozenset({"丑", "辰"}): LIU_PO_CHOU_CHEN,
    frozenset({"寅", "亥"}): LIU_PO_YIN_HAI,
    frozenset({"卯", "午"}): LIU_PO_MAO_WU,
    frozenset({"巳", "申"}): LIU_PO_SI_SHEN,
    frozenset({"未", "戌"}): LIU_PO_WEI_XU,
}

# ============================================================
# XV. HÌNH — Punishments (刑)
# ============================================================

# --- Tam Hình (三刑) — Three Punishments ---

GRACELESS_PUNISHMENT: Term = (
    "无恩之刑", "Wú Ēn Zhī Xíng",
    "Graceless Punishment", "Vô Ân Chi Hình",
)
BULLY_PUNISHMENT: Term = (
    "恃势之刑", "Shì Shì Zhī Xíng",
    "Bullying Punishment", "Ỷ Thế Chi Hình",
)
UNCIVIL_PUNISHMENT: Term = (
    "无礼之刑", "Wú Lǐ Zhī Xíng",
    "Uncivil Punishment", "Vô Lễ Chi Hình",
)
SELF_PUNISHMENT: Term = (
    "自刑", "Zì Xíng", "Self-Punishment", "Tự Hình",
)

PUNISHMENT_TYPES: List[Term] = [
    GRACELESS_PUNISHMENT,
    BULLY_PUNISHMENT,
    UNCIVIL_PUNISHMENT,
    SELF_PUNISHMENT,
]

# Graceless: 寅巳申 (Dần Tỵ Thân) — mutually ungrateful
GRACELESS_PUNISHMENT_SET: frozenset = frozenset({"寅", "巳", "申"})

GRACELESS_PUNISHMENT_PAIRS: List[Term] = [
    ("寅巳刑", "Yín Sì Xíng", "Yin-Si Punishment", "Dần Tỵ hình"),
    ("巳申刑", "Sì Shēn Xíng", "Si-Shen Punishment", "Tỵ Thân hình"),
    ("寅申刑", "Yín Shēn Xíng", "Yin-Shen Punishment", "Dần Thân hình"),
]

# Bully: 丑戌未 (Sửu Tuất Mùi) — relying on power
BULLY_PUNISHMENT_SET: frozenset = frozenset({"丑", "戌", "未"})

BULLY_PUNISHMENT_PAIRS: List[Term] = [
    ("丑戌刑", "Chǒu Xū Xíng", "Chou-Xu Punishment", "Sửu Tuất hình"),
    ("戌未刑", "Xū Wèi Xíng", "Xu-Wei Punishment", "Tuất Mùi hình"),
    ("丑未刑", "Chǒu Wèi Xíng", "Chou-Wei Punishment", "Sửu Mùi hình"),
]

# Uncivil: 子卯 (Tí Mão) — lacking propriety
UNCIVIL_PUNISHMENT_SET: frozenset = frozenset({"子", "卯"})

UNCIVIL_PUNISHMENT_PAIR: Term = (
    "子卯刑", "Zǐ Mǎo Xíng", "Zi-Mao Punishment", "Tí Mão hình",
)

# Self-Punishment: 辰午酉亥 (Thìn Ngọ Dậu Hợi)
SELF_PUNISHMENT_BRANCHES: frozenset = frozenset({"辰", "午", "酉", "亥"})

SELF_PUNISHMENT_TERMS: List[Term] = [
    ("辰辰自刑", "Chén Chén Zì Xíng", "Chen-Chen Self-Punishment",
     "Thìn Thìn tự hình"),
    ("午午自刑", "Wǔ Wǔ Zì Xíng", "Wu-Wu Self-Punishment",
     "Ngọ Ngọ tự hình"),
    ("酉酉自刑", "Yǒu Yǒu Zì Xíng", "You-You Self-Punishment",
     "Dậu Dậu tự hình"),
    ("亥亥自刑", "Hài Hài Zì Xíng", "Hai-Hai Self-Punishment",
     "Hợi Hợi tự hình"),
]

# ============================================================
# XVI. General Interaction Category terms
# ============================================================

INTERACTION_COMBINE: Term = ("合", "Hé", "Combination", "Hợp")
INTERACTION_CLASH: Term = ("冲", "Chōng", "Clash", "Xung")
INTERACTION_PUNISHMENT: Term = ("刑", "Xíng", "Punishment", "Hình")
INTERACTION_HARM: Term = ("害", "Hài", "Harm", "Hại")
INTERACTION_DESTRUCTION: Term = ("破", "Pò", "Destruction", "Phá")

INTERACTION_CATEGORY_TERMS: List[Term] = [
    INTERACTION_COMBINE,
    INTERACTION_CLASH,
    INTERACTION_PUNISHMENT,
    INTERACTION_HARM,
    INTERACTION_DESTRUCTION,
]

# ============================================================
# XVII. Thấu Xuất & Tàng Can terms (Protrusion & Hidden Stems)
# ============================================================

PROTRUSION: Term = (
    "透出", "Tòu Chū", "Protrusion (exposed stem)", "Thấu Xuất",
)
HIDDEN_STEM: Term = (
    "藏干", "Cáng Gān", "Hidden Stem", "Tàng Can",
)
MONTH_ORDER: Term = (
    "月令", "Yuè Lìng", "Month Order (month branch)", "Nguyệt Lệnh",
)
USEFUL_GOD: Term = (
    "用神", "Yòng Shén", "Useful God", "Dụng Thần",
)
JOYFUL_GOD: Term = (
    "喜神", "Xǐ Shén", "Joyful God", "Hỉ Thần",
)
TABOO_GOD: Term = (
    "忌神", "Jì Shén", "Taboo God", "Kỵ Thần",
)
ENMITY_GOD: Term = (
    "仇神", "Chóu Shén", "Enmity God", "Cừu Thần",
)
IDLE_GOD: Term = (
    "闲神", "Xián Shén", "Idle God", "Nhàn Thần",
)

SIX_GOD_TERMS: List[Term] = [
    USEFUL_GOD,
    JOYFUL_GOD,
    TABOO_GOD,
    ENMITY_GOD,
    IDLE_GOD,
]

MAIN_HIDDEN: Term = ("本气", "Běn Qì", "Main Qi (primary hidden stem)", "Bản Khí")
MIDDLE_HIDDEN: Term = ("中气", "Zhōng Qì", "Middle Qi", "Trung Khí")
RESIDUAL_HIDDEN: Term = ("余气", "Yú Qì", "Residual Qi", "Dư Khí")

HIDDEN_STEM_ROLE_TERMS: List[Term] = [MAIN_HIDDEN, MIDDLE_HIDDEN, RESIDUAL_HIDDEN]

# ============================================================
# XVIII. Day Master Strength terms (日主强弱)
# ============================================================

STRENGTH_STRONG: Term = ("身强", "Shēn Qiáng", "Strong Day Master", "Thân Vượng")
STRENGTH_WEAK: Term = ("身弱", "Shēn Ruò", "Weak Day Master", "Thân Nhược")
STRENGTH_BALANCED: Term = ("中和", "Zhōng Hé", "Balanced", "Trung Hòa")
STRENGTH_EXTREME_STRONG: Term = (
    "极旺", "Jí Wàng", "Extremely Strong", "Cực Vượng",
)
STRENGTH_EXTREME_WEAK: Term = (
    "极弱", "Jí Ruò", "Extremely Weak", "Cực Nhược",
)

STRENGTH_TERMS: List[Term] = [
    STRENGTH_STRONG,
    STRENGTH_WEAK,
    STRENGTH_BALANCED,
    STRENGTH_EXTREME_STRONG,
    STRENGTH_EXTREME_WEAK,
]

# ============================================================
# XIX. Seasonal Strength (旺相休囚死)
# ============================================================

SEASONAL_PROSPEROUS: Term = ("旺", "Wàng", "Prosperous", "Vượng")
SEASONAL_PRIME: Term = ("相", "Xiàng", "Prime", "Tướng")
SEASONAL_RESTING: Term = ("休", "Xiū", "Resting", "Hưu")
SEASONAL_IMPRISONED: Term = ("囚", "Qiú", "Imprisoned", "Tù")
SEASONAL_DEAD: Term = ("死", "Sǐ", "Dead", "Tử")

SEASONAL_STRENGTH_TERMS: List[Term] = [
    SEASONAL_PROSPEROUS,
    SEASONAL_PRIME,
    SEASONAL_RESTING,
    SEASONAL_IMPRISONED,
    SEASONAL_DEAD,
]

# ============================================================
# XX. Fu Yin & Fan Yin (伏吟 & 反吟)
# ============================================================

FU_YIN: Term = (
    "伏吟", "Fú Yín", "Hidden Sobbing (repeated pillar)", "Phục Ngâm",
)
FAN_YIN: Term = (
    "反吟", "Fǎn Yín", "Counter Sobbing (clashed pillar)", "Phản Ngâm",
)

DUPLICATION_TERMS: List[Term] = [FU_YIN, FAN_YIN]

# ============================================================
# Composite lookup: all terminology in this module
# ============================================================

ALL_TERMINOLOGY: List[Term] = [
    *ALL_STRUCTURES,
    *STRUCTURE_CATEGORIES,
    *STRUCTURE_QUALITY_TERMS,
    *HEAVENLY_STEM_FIVE_COMBINATIONS,
    *TRANSFORMATION_RELATED_TERMS,
    *HEAVENLY_STEM_CLASHES,
    *COMBINATION_STATUS_TERMS,
    *SIX_BRANCH_COMBINATIONS,
    *THREE_COMBINATION_FRAMES,
    *DIRECTIONAL_COMBINATION_FRAMES,
    *SIX_CLASHES,
    *SIX_HARMS,
    *SIX_DESTRUCTIONS,
    *PUNISHMENT_TYPES,
    *INTERACTION_CATEGORY_TERMS,
    PROTRUSION, HIDDEN_STEM, MONTH_ORDER,
    *SIX_GOD_TERMS,
    *HIDDEN_STEM_ROLE_TERMS,
    *STRENGTH_TERMS,
    *SEASONAL_STRENGTH_TERMS,
    *DUPLICATION_TERMS,
]

# Chinese → full Term tuple (for any term in this module)
TERMINOLOGY_LOOKUP: Dict[str, Term] = {t[0]: t for t in ALL_TERMINOLOGY}

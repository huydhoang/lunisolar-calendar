"""
Bazi Constants (八字常量)
========================

All data constants, lookup tables, and interaction sets used by the Bazi
analysis subsystems.
"""

from itertools import combinations as _combs
from typing import Dict, List, Tuple

from shared.constants import STEM_CHARS, BRANCH_CHARS

from .glossary import (
    STEM_PAIR_TO_ELEMENT,
    BRANCH_PAIR_TO_LIU_HE,
    BRANCH_PAIR_TO_LIU_CHONG,
    BRANCH_PAIR_TO_LIU_HAI,
    BRANCH_PAIR_TO_LIU_PO,
    STEM_CLASH_PAIR_TO_TERM,
    SAN_HE_SET_TO_TERM,
    SAN_HUI_SET_TO_TERM,
    BAN_SAN_HE_BIRTH_PAIRS,
    BAN_SAN_HE_GRAVE_PAIRS,
    SELF_PUNISHMENT_BRANCHES,
    GRACELESS_PUNISHMENT_SET,
    BULLY_PUNISHMENT_SET,
    UNCIVIL_PUNISHMENT_SET,
)

# Core Lists — from shared canonical constants
HEAVENLY_STEMS: List[str] = STEM_CHARS
EARTHLY_BRANCHES: List[str] = BRANCH_CHARS

# ============================================================
# Element & Polarity Mappings
# ============================================================

STEM_ELEMENT: Dict[str, str] = {
    "甲": "Wood", "乙": "Wood",
    "丙": "Fire", "丁": "Fire",
    "戊": "Earth", "己": "Earth",
    "庚": "Metal", "辛": "Metal",
    "壬": "Water", "癸": "Water",
}

STEM_POLARITY: Dict[str, str] = {
    "甲": "Yang", "乙": "Yin",
    "丙": "Yang", "丁": "Yin",
    "戊": "Yang", "己": "Yin",
    "庚": "Yang", "辛": "Yin",
    "壬": "Yang", "癸": "Yin",
}

# Five-Element production cycle: A produces B
GEN_MAP: Dict[str, str] = {
    "Wood": "Fire", "Fire": "Earth", "Earth": "Metal",
    "Metal": "Water", "Water": "Wood",
}

# Five-Element control cycle: A controls B
CONTROL_MAP: Dict[str, str] = {
    "Wood": "Earth", "Fire": "Metal", "Earth": "Water",
    "Metal": "Wood", "Water": "Fire",
}

# ============================================================
# Hidden Stems — spec §2.2  (main, middle, residual)
# ============================================================

BRANCH_HIDDEN_STEMS: Dict[str, List[str]] = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "戊", "庚"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

HIDDEN_ROLES = ("main", "middle", "residual")

# ============================================================
# Twelve Longevity Stages — spec §3
# ============================================================

LONGEVITY_STAGES: List[str] = [
    "长生", "沐浴", "冠带", "临官", "帝旺", "衰",
    "病", "死", "墓", "绝", "胎", "养",
]

# Starting branch for 长生 of each stem — spec §3.3
LONGEVITY_START: Dict[str, str] = {
    "甲": "亥", "乙": "午", "丙": "寅", "丁": "酉",
    "戊": "寅", "己": "酉", "庚": "巳", "辛": "子",
    "壬": "申", "癸": "卯",
}

LONGEVITY_STAGES_EN: List[str] = [
    "Growth", "Bath", "Crown Belt", "Coming of Age",
    "Prosperity Peak", "Decline", "Sickness", "Death",
    "Grave", "Termination", "Conception", "Nurture",
]

LONGEVITY_STAGES_VI: List[str] = [
    "Trường Sinh", "Mộc Dục", "Quan Đới", "Lâm Quan",
    "Đế Vượng", "Suy", "Bệnh", "Tử",
    "Mộ", "Tuyệt", "Thai", "Dưỡng",
]

# ============================================================
# Branch Interactions — spec §8
# Derived from glossary (single source of truth)
# ============================================================

# §8.1 Six Combinations (六合)
LIU_HE = frozenset(BRANCH_PAIR_TO_LIU_HE.keys())

# §8.4 Six Clashes (六冲)
LIU_CHONG = frozenset(BRANCH_PAIR_TO_LIU_CHONG.keys())

# §8.6 Six Harms (六害)
LIU_HAI = frozenset(BRANCH_PAIR_TO_LIU_HAI.keys())

# §8.2 Three Combinations (三合)
SAN_HE: List[frozenset] = list(SAN_HE_SET_TO_TERM.keys())

# §8.2b Half Three Combinations (半三合)
BAN_SAN_HE: List[frozenset] = [
    pair for bp, gp in zip(BAN_SAN_HE_BIRTH_PAIRS, BAN_SAN_HE_GRAVE_PAIRS)
    for pair in (bp, gp)
]

# §8.3 Directional Combinations (三会 / 方局)
SAN_HUI: List[frozenset] = list(SAN_HUI_SET_TO_TERM.keys())

# §8.5 Three Punishments (三刑)
XING: List[frozenset] = [
    GRACELESS_PUNISHMENT_SET,   # 无恩之刑 (Graceless)
    BULLY_PUNISHMENT_SET,       # 恃势之刑 (Bullying)
    UNCIVIL_PUNISHMENT_SET,     # 无礼之刑 (Rude)
]

# §8.5 Self-punishment (自刑)
ZI_XING_BRANCHES = SELF_PUNISHMENT_BRANCHES

# ============================================================
# Branch → native element mapping
# ============================================================

BRANCH_ELEMENT: Dict[str, str] = {
    "子": "Water", "丑": "Earth", "寅": "Wood", "卯": "Wood",
    "辰": "Earth", "巳": "Fire", "午": "Fire", "未": "Earth",
    "申": "Metal", "酉": "Metal", "戌": "Earth", "亥": "Water",
}

# ============================================================
# Heavenly Stem Combinations & Transformations (天干合化)
# ============================================================

STEM_TRANSFORMATIONS: Dict[frozenset, str] = dict(STEM_PAIR_TO_ELEMENT)

ADJACENT_PAIRS: List[Tuple[str, str]] = [
    ("year", "month"), ("month", "day"), ("day", "hour"),
]

# ============================================================
# Punishments & Harms — derived from glossary
# ============================================================

SELF_PUNISH_BRANCHES = SELF_PUNISHMENT_BRANCHES

UNCIVIL_PUNISH_PAIRS = frozenset(
    frozenset(pair) for pair in _combs(UNCIVIL_PUNISHMENT_SET, 2)
)

GRACELESS_PUNISH_PAIRS = frozenset(
    frozenset(pair) for pair in _combs(GRACELESS_PUNISHMENT_SET, 2)
)

BULLY_PUNISH_PAIRS = frozenset(
    frozenset(pair) for pair in _combs(BULLY_PUNISHMENT_SET, 2)
)

HARM_PAIRS = LIU_HAI

LIU_PO = frozenset(BRANCH_PAIR_TO_LIU_PO.keys())

STEM_CLASH_PAIRS = frozenset(STEM_CLASH_PAIR_TO_TERM.keys())

# ============================================================
# Void Branches (空亡) — spec §IX
# ============================================================

VOID_BRANCH_TABLE: Dict[int, Tuple[str, str]] = {
    0: ("戌", "亥"),  1: ("申", "酉"),  2: ("午", "未"),
    3: ("辰", "巳"),  4: ("寅", "卯"),  5: ("子", "丑"),
}

XUN_NAMES: Dict[int, str] = {
    0: "甲子旬", 1: "甲戌旬", 2: "甲申旬",
    3: "甲午旬", 4: "甲辰旬", 5: "甲寅旬",
}

# ============================================================
# Symbolic Stars (神煞) — spec §X
# ============================================================

NOBLEMAN_TABLE: Dict[str, List[str]] = {
    "甲": ["丑", "未"], "乙": ["子", "申"],
    "丙": ["亥", "酉"], "丁": ["亥", "酉"],
    "戊": ["丑", "未"], "己": ["子", "申"],
    "庚": ["丑", "未"], "辛": ["午", "寅"],
    "壬": ["卯", "巳"], "癸": ["卯", "巳"],
}

ACADEMIC_STAR_TABLE: Dict[str, str] = {
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉",
    "戊": "申", "己": "酉", "庚": "亥", "辛": "子",
    "壬": "寅", "癸": "卯",
}

PEACH_BLOSSOM_TABLE: Dict[str, str] = {
    "子": "酉", "丑": "午", "寅": "卯", "卯": "子",
    "辰": "酉", "巳": "午", "午": "卯", "未": "子",
    "申": "酉", "酉": "午", "戌": "卯", "亥": "子",
}

TRAVEL_HORSE_TABLE: Dict[str, str] = {
    "子": "寅", "丑": "亥", "寅": "申", "卯": "巳",
    "辰": "寅", "巳": "亥", "午": "申", "未": "巳",
    "申": "寅", "酉": "亥", "戌": "申", "亥": "巳",
}

GENERAL_STAR_TABLE: Dict[str, str] = {
    "子": "子", "丑": "酉", "寅": "午", "卯": "卯",
    "辰": "子", "巳": "酉", "午": "午", "未": "卯",
    "申": "子", "酉": "酉", "戌": "午", "亥": "卯",
}

CANOPY_STAR_TABLE: Dict[str, str] = {
    "子": "辰", "丑": "丑", "寅": "戌", "卯": "未",
    "辰": "辰", "巳": "丑", "午": "戌", "未": "未",
    "申": "辰", "酉": "丑", "戌": "戌", "亥": "未",
}

GOAT_BLADE_TABLE: Dict[str, str] = {
    "甲": "卯", "乙": "辰", "丙": "午", "丁": "未",
    "戊": "午", "己": "未", "庚": "酉", "辛": "戌",
    "壬": "子", "癸": "丑",
}

PROSPERITY_STAR_TABLE: Dict[str, str] = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午",
    "戊": "巳", "己": "午", "庚": "申", "辛": "酉",
    "壬": "亥", "癸": "子",
}

RED_CLOUD_TABLE: Dict[str, str] = {
    "子": "卯", "丑": "寅", "寅": "丑", "卯": "子",
    "辰": "亥", "巳": "戌", "午": "酉", "未": "申",
    "申": "未", "酉": "午", "戌": "巳", "亥": "辰",
}

BLOOD_KNIFE_TABLE: Dict[str, str] = {
    "子": "戌", "丑": "酉", "寅": "申", "卯": "未",
    "辰": "午", "巳": "巳", "午": "辰", "未": "卯",
    "申": "寅", "酉": "丑", "戌": "子", "亥": "亥",
}

# ============================================================
# Scoring weights
# ============================================================

PILLAR_WEIGHTS = {
    "year": 1.0,
    "month": 3.0,
    "day": 1.5,
    "hour": 1.0,
}

LU_MAP = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午",
    "戊": "巳", "己": "午", "庚": "申", "辛": "酉",
    "壬": "亥", "癸": "子",
}

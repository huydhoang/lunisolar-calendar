"""
Canonical Stem / Branch Constants
=================================

Single source of truth for Heavenly Stems, Earthly Branches,
and derived lookups used across lunisolar, huangdao, and bazi.
"""

from typing import Dict, List

# Rich tuples — canonical definition
HEAVENLY_STEMS = [
    ('甲', 'jiǎ', 'Wood Yang', 1),
    ('乙', 'yǐ', 'Wood Yin', 2),
    ('丙', 'bǐng', 'Fire Yang', 3),
    ('丁', 'dīng', 'Fire Yin', 4),
    ('戊', 'wù', 'Earth Yang', 5),
    ('己', 'jǐ', 'Earth Yin', 6),
    ('庚', 'gēng', 'Metal Yang', 7),
    ('辛', 'xīn', 'Metal Yin', 8),
    ('壬', 'rén', 'Water Yang', 9),
    ('癸', 'guǐ', 'Water Yin', 10)
]

EARTHLY_BRANCHES = [
    ('子', 'zǐ', 'Rat', 1, 23, 1),      # 23:00-01:00
    ('丑', 'chǒu', 'Ox', 2, 1, 3),      # 01:00-03:00
    ('寅', 'yín', 'Tiger', 3, 3, 5),     # 03:00-05:00
    ('卯', 'mǎo', 'Rabbit', 4, 5, 7),   # 05:00-07:00
    ('辰', 'chén', 'Dragon', 5, 7, 9),   # 07:00-09:00
    ('巳', 'sì', 'Snake', 6, 9, 11),     # 09:00-11:00
    ('午', 'wǔ', 'Horse', 7, 11, 13),    # 11:00-13:00
    ('未', 'wèi', 'Goat', 8, 13, 15),    # 13:00-15:00
    ('申', 'shēn', 'Monkey', 9, 15, 17), # 15:00-17:00
    ('酉', 'yǒu', 'Rooster', 10, 17, 19), # 17:00-19:00
    ('戌', 'xū', 'Dog', 11, 19, 21),     # 19:00-21:00
    ('亥', 'hài', 'Pig', 12, 21, 23)     # 21:00-23:00
]

# Derived lookups (convenience, computed once at import)
STEM_CHARS: List[str] = [s[0] for s in HEAVENLY_STEMS]
BRANCH_CHARS: List[str] = [b[0] for b in EARTHLY_BRANCHES]
BRANCH_INDEX: Dict[str, int] = {ch: i for i, ch in enumerate(BRANCH_CHARS)}
BRANCH_ANIMALS: Dict[str, str] = {b[0]: b[2] for b in EARTHLY_BRANCHES}

# Pinyin lookups
EARTHLY_BRANCH_PINYIN: Dict[str, str] = {
    "子": "Zǐ", "丑": "Chǒu", "寅": "Yín", "卯": "Mǎo",
    "辰": "Chén", "巳": "Sì", "午": "Wǔ", "未": "Wèi",
    "申": "Shēn", "酉": "Yǒu", "戌": "Xū", "亥": "Hài"
}

# Principal Solar Terms (Z1-Z12) for leap month determination
PRINCIPAL_TERMS = {
    1: 330,   # Z1 雨水 Rain Water
    2: 0,     # Z2 春分 Spring Equinox
    3: 30,    # Z3 穀雨 Grain Rain
    4: 60,    # Z4 小滿 Grain Full
    5: 90,    # Z5 夏至 Summer Solstice
    6: 120,   # Z6 大暑 Great Heat
    7: 150,   # Z7 處暑 Limit of Heat
    8: 180,   # Z8 秋分 Autumnal Equinox
    9: 210,   # Z9 霜降 Descent of Frost
    10: 240,  # Z10 小雪 Slight Snow
    11: 270,  # Z11 冬至 Winter Solstice
    12: 300   # Z12 大寒 Great Cold
}

# Principal solar term names (節氣) — used by huangdao for repeat rule
PRINCIPAL_TERM_NAMES = {
    "立春", "驚蟄", "清明", "立夏", "芒種", "小暑",
    "立秋", "白露", "寒露", "立冬", "大雪", "小寒",
    "惊蛰", "芒种"  # Simplified variants
}

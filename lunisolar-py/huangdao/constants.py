"""Domain-specific constants for Huangdao systems."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List

from shared.constants import BRANCH_INDEX as _SHARED_BRANCH_INDEX


# =====================================================================================
# Enums
# =====================================================================================

class EarthlyBranch(Enum):
    """Twelve Earthly Branches (十二地支)"""
    ZI = (0, "子", "Rat")
    CHOU = (1, "丑", "Ox")
    YIN = (2, "寅", "Tiger")
    MAO = (3, "卯", "Rabbit")
    CHEN = (4, "辰", "Dragon")
    SI = (5, "巳", "Snake")
    WU = (6, "午", "Horse")
    WEI = (7, "未", "Goat")
    SHEN = (8, "申", "Monkey")
    YOU = (9, "酉", "Rooster")
    XU = (10, "戌", "Dog")
    HAI = (11, "亥", "Pig")

    def __init__(self, index: int, chinese: str, animal: str):
        self.index = index
        self.chinese = chinese
        self.animal = animal


class GreatYellowPathSpirit(Enum):
    """Twelve Spirits of Great Yellow Path"""
    QINGLONG = ("青龙", "Azure Dragon", True)
    MINGTANG = ("明堂", "Bright Hall", True)
    TIANXING = ("天刑", "Heavenly Punishment", False)
    ZHUQUE = ("朱雀", "Vermillion Bird", False)
    JINKUI = ("金匮", "Golden Coffer", True)
    TIANDE = ("天德", "Heavenly Virtue", True)
    BAIHU = ("白虎", "White Tiger", False)
    YUTANG = ("玉堂", "Jade Hall", True)
    TIANLAO = ("天牢", "Heavenly Prison", False)
    XUANWU = ("玄武", "Black Tortoise", False)
    SIMING = ("司命", "Life Controller", True)
    GOUCHEN = ("勾陈", "Coiling Snake", False)

    def __init__(self, chinese: str, english: str, is_auspicious: bool):
        self.chinese = chinese
        self.english = english
        self.is_auspicious = is_auspicious


# =====================================================================================
# Lookup tables
# =====================================================================================

BRANCH_ORDER: List[str] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
BRANCH_INDEX: Dict[str, int] = _SHARED_BRANCH_INDEX

# Building branch for each lunar month (1..12)
BUILDING_BRANCH_BY_MONTH: Dict[int, str] = {
    1: "寅", 2: "卯", 3: "辰", 4: "巳", 5: "午", 6: "未",
    7: "申", 8: "酉", 9: "戌", 10: "亥", 11: "子", 12: "丑",
}

# Great Yellow Path Azure Dragon monthly start positions
AZURE_DRAGON_MONTHLY_START: Dict[int, EarthlyBranch] = {
    1: EarthlyBranch.ZI, 2: EarthlyBranch.YIN, 3: EarthlyBranch.CHEN,
    4: EarthlyBranch.WU, 5: EarthlyBranch.SHEN, 6: EarthlyBranch.XU,
    7: EarthlyBranch.ZI, 8: EarthlyBranch.YIN, 9: EarthlyBranch.CHEN,
    10: EarthlyBranch.WU, 11: EarthlyBranch.SHEN, 12: EarthlyBranch.XU,
}

MNEMONIC_FORMULAS: Dict[int, str] = {
    1: "寅申需加子", 2: "卯酉却在寅", 3: "辰戍龙位上",
    4: "巳亥午上存", 5: "子午临申地", 6: "丑未戍上行",
    7: "寅申需加子", 8: "卯酉却在寅", 9: "辰戍龙位上",
    10: "巳亥午上存", 11: "子午临申地", 12: "丑未戍上行",
}

SPIRIT_SEQUENCE: List[GreatYellowPathSpirit] = [
    GreatYellowPathSpirit.QINGLONG, GreatYellowPathSpirit.MINGTANG,
    GreatYellowPathSpirit.TIANXING, GreatYellowPathSpirit.ZHUQUE,
    GreatYellowPathSpirit.JINKUI, GreatYellowPathSpirit.TIANDE,
    GreatYellowPathSpirit.BAIHU, GreatYellowPathSpirit.YUTANG,
    GreatYellowPathSpirit.TIANLAO, GreatYellowPathSpirit.XUANWU,
    GreatYellowPathSpirit.SIMING, GreatYellowPathSpirit.GOUCHEN,
]

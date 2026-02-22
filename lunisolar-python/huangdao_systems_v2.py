#!/usr/bin/env python3
"""
Efficient Huangdao Systems Calculator (十二建星与大黄道) - Optimized for Monthly Output
Uses lunisolar_v2 for fast, accurate calendar conversion

Usage:
  python huangdao_systems_v3.py --year 2025 --month 10
  python huangdao_systems_v3.py -y 2025 -m 10 --timezone Asia/Shanghai
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Tuple

import argparse
import calendar
import pytz

# External engine and helpers
from lunisolar_v2 import solar_to_lunisolar, solar_to_lunisolar_batch, LunisolarDateDTO
from solar_terms import calculate_solar_terms
from skyfield.api import utc

# =====================================================================================
# Constants and Enums
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


BRANCH_ORDER: List[str] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
BRANCH_INDEX: Dict[str, int] = {ch: i for i, ch in enumerate(BRANCH_ORDER)}

EARTHLY_BRANCH_PINYIN = {
    "子": "Zǐ", "丑": "Chǒu", "寅": "Yín", "卯": "Mǎo",
    "辰": "Chén", "巳": "Sì", "午": "Wǔ", "未": "Wèi",
    "申": "Shēn", "酉": "Yǒu", "戌": "Xū", "亥": "Hài"
}

# Building branch for each lunar month (1..12)
BUILDING_BRANCH_BY_MONTH: Dict[int, str] = {
    1: "寅", 2: "卯", 3: "辰", 4: "巳", 5: "午", 6: "未",
    7: "申", 8: "酉", 9: "戌", 10: "亥", 11: "子", 12: "丑"
}

# Great Yellow Path Azure Dragon monthly start positions
AZURE_DRAGON_MONTHLY_START: Dict[int, EarthlyBranch] = {
    1: EarthlyBranch.ZI, 2: EarthlyBranch.YIN, 3: EarthlyBranch.CHEN,
    4: EarthlyBranch.WU, 5: EarthlyBranch.SHEN, 6: EarthlyBranch.XU,
    7: EarthlyBranch.ZI, 8: EarthlyBranch.YIN, 9: EarthlyBranch.CHEN,
    10: EarthlyBranch.WU, 11: EarthlyBranch.SHEN, 12: EarthlyBranch.XU
}

MNEMONIC_FORMULAS: Dict[int, str] = {
    1: "寅申需加子", 2: "卯酉却在寅", 3: "辰戍龙位上",
    4: "巳亥午上存", 5: "子午临申地", 6: "丑未戍上行",
    7: "寅申需加子", 8: "卯酉却在寅", 9: "辰戍龙位上",
    10: "巳亥午上存", 11: "子午临申地", 12: "丑未戍上行"
}

# Principal solar terms (节气) - these trigger the repeat rule
PRINCIPAL_TERM_NAMES = {
    "立春", "驚蟄", "清明", "立夏", "芒種", "小暑",
    "立秋", "白露", "寒露", "立冬", "大雪", "小寒",
    "惊蛰", "芒种"  # Simplified variants
}


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


SPIRIT_SEQUENCE: List[GreatYellowPathSpirit] = [
    GreatYellowPathSpirit.QINGLONG, GreatYellowPathSpirit.MINGTANG,
    GreatYellowPathSpirit.TIANXING, GreatYellowPathSpirit.ZHUQUE,
    GreatYellowPathSpirit.JINKUI, GreatYellowPathSpirit.TIANDE,
    GreatYellowPathSpirit.BAIHU, GreatYellowPathSpirit.YUTANG,
    GreatYellowPathSpirit.TIANLAO, GreatYellowPathSpirit.XUANWU,
    GreatYellowPathSpirit.SIMING, GreatYellowPathSpirit.GOUCHEN
]


# =====================================================================================
# Construction Stars System
# =====================================================================================

class ConstructionStars:
    """Twelve Construction Stars (十二建星) Calculator"""
    
    CONSTRUCTION_STARS = ["建", "除", "满", "平", "定", "执", "破", "危", "成", "收", "开", "闭"]
    
    STAR_TRANSLATIONS = {
        "建": "Jiàn (Establish)", "除": "Chú (Remove)", "满": "Mǎn (Full)",
        "平": "Píng (Balanced)", "定": "Dìng (Set)", "执": "Zhí (Hold)",
        "破": "Pò (Break)", "危": "Wēi (Danger)", "成": "Chéng (Accomplish)",
        "收": "Shōu (Harvest)", "开": "Kāi (Open)", "闭": "Bì (Close)"
    }
    
    # "建满平收黑，除危定执黄，成开皆可用，破闭不可当"
    # Updated scoring: 4 (auspicious), 3 (moderate), 2 (inauspicious), 1 (very inauspicious)
    AUSPICIOUSNESS = {
        "建": {"level": "inauspicious", "score": 2},
        "除": {"level": "auspicious", "score": 4},
        "满": {"level": "moderate", "score": 3},
        "平": {"level": "inauspicious", "score": 2},
        "定": {"level": "auspicious", "score": 4},
        "执": {"level": "moderate", "score": 3},
        "破": {"level": "very_inauspicious", "score": 1},
        "危": {"level": "inauspicious", "score": 2},
        "成": {"level": "moderate", "score": 3},
        "收": {"level": "inauspicious", "score": 2},
        "开": {"level": "moderate", "score": 3},
        "闭": {"level": "very_inauspicious", "score": 1}
    }

    def __init__(self, timezone_name: str):
        self.timezone_name = timezone_name
        self.tz = pytz.timezone(timezone_name)
        self._solar_term_cache: Dict[str, bool] = {}

    def _is_principal_solar_term_day(self, date_obj: datetime) -> bool:
        """Check if date is a principal solar term day (with caching)"""
        date_key = date_obj.strftime("%Y-%m-%d")
        if date_key in self._solar_term_cache:
            return self._solar_term_cache[date_key]
        
        start_local = self.tz.localize(datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0))
        end_local = start_local + timedelta(days=1, seconds=-1)
        start_utc = start_local.astimezone(pytz.utc)
        end_utc = end_local.astimezone(pytz.utc)
        
        results = calculate_solar_terms(start_utc, end_utc)
        is_term = False
        for unix_ts, idx, zht, zhs, _vn in results:
            utc_dt = datetime.fromtimestamp(unix_ts, tz=utc)
            local_dt = utc_dt.astimezone(self.tz)
            if local_dt.date() == date_obj.date():
                if (zht and zht in PRINCIPAL_TERM_NAMES) or (zhs and zhs in PRINCIPAL_TERM_NAMES):
                    is_term = True
                    break
        
        self._solar_term_cache[date_key] = is_term
        return is_term

    def _star_index_from_branches(self, building_branch: str, day_branch: str) -> int:
        """Calculate star index: (day_branch_index - building_branch_index) mod 12"""
        b_idx = BRANCH_INDEX[building_branch]
        d_idx = BRANCH_INDEX[day_branch]
        return (d_idx - b_idx) % 12

    def get_construction_star(self, date_obj: datetime, dto: LunisolarDateDTO,
                              prev_star: str = None) -> str:
        """Get construction star for date (with solar term repeat rule)
        
        Args:
            date_obj: Target date
            dto: Lunisolar date data for target
            prev_star: Star from previous day (for sequential tracking)
        """
        date_str = date_obj.strftime("%Y-%m-%d")
        is_solar_term = self._is_principal_solar_term_day(date_obj)
        
        building_branch = BUILDING_BRANCH_BY_MONTH[dto.month]

        # The base calculation is what the star *would* be without sequential logic.
        # We can use it for comparison and for the first day.
        base_star_index = self._star_index_from_branches(building_branch, dto.day_branch)
        base_star = self.CONSTRUCTION_STARS[base_star_index]

        if prev_star is None:
            # First day of a sequence, use the base calculation.
            actual_star = base_star
            # print(f"\n  📅 Date: {date_str} (Sequence Start)")
            # print(f"     Lunar month: {dto.month} ({'閏' if dto.is_leap_month else ''})")
            # print(f"     Building branch: {building_branch} (index {BRANCH_INDEX[building_branch]})")
            # print(f"     Day branch: {dto.day_branch} (index {BRANCH_INDEX[dto.day_branch]})")
            # print(f"     Star calculation: ({BRANCH_INDEX[dto.day_branch]} - {BRANCH_INDEX[building_branch]}) % 12 = {base_star_index}")
            # print(f"     Star: {actual_star}")
        elif is_solar_term:
            # Solar term day: repeat previous day's star
            actual_star = prev_star
            # print(f"\n  🔄 SOLAR TERM DAY: {date_str}")
            # print(f"     Repeating previous day's star: {prev_star}")
            # print(f"     (Base calculation would be: {base_star})")
        else:
            # Normal day: increment from the previous day's star
            prev_star_index = self.CONSTRUCTION_STARS.index(prev_star)
            actual_star_index = (prev_star_index + 1) % 12
            actual_star = self.CONSTRUCTION_STARS[actual_star_index]
            # print(f"\n  ➡️  Date: {date_str} (Sequential)")
            # print(f"     Previous star: {prev_star} (index {prev_star_index})")
            # print(f"     Continuing sequence: ({prev_star_index} + 1) % 12 = {actual_star_index}")
            # print(f"     Star: {actual_star}")
            # if actual_star != base_star:
            #     print(f"     (Base calculation would be: {base_star})")

        return actual_star


# =====================================================================================
# Great Yellow Path System
# =====================================================================================

class GreatYellowPath:
    """Great Yellow Path (大黄道) Calculator"""

    def calculate_spirit(self, lunar_month: int, day_branch_char: str) -> GreatYellowPathSpirit:
        """Calculate spirit for the day"""
        day_branch_idx = BRANCH_INDEX[day_branch_char]
        azure_start = AZURE_DRAGON_MONTHLY_START[lunar_month]
        spirit_index = (day_branch_idx - azure_start.index) % 12
        return SPIRIT_SEQUENCE[spirit_index]


# =====================================================================================
# Unified Calculator
# =====================================================================================

class HuangdaoCalculator:
    """Unified calculator for Construction Stars and Great Yellow Path"""

    def __init__(self, timezone_name: str = 'Asia/Ho_Chi_Minh'):
        self.timezone_name = timezone_name
        self.construction_stars = ConstructionStars(timezone_name)
        self.great_yellow_path = GreatYellowPath()

    def calculate_day_info(self, date_obj: datetime, dto: LunisolarDateDTO = None,
                          prev_star: str = None) -> Dict:
        """Calculate complete information for a single day
        
        Args:
            date_obj: Target date
            dto: Lunisolar data (optional, will fetch if not provided)
            prev_star: Star from previous day for sequential tracking
        """
        # Get lunisolar data (use provided DTO if available, otherwise fetch)
        if dto is None:
            dto = solar_to_lunisolar(date_obj.strftime("%Y-%m-%d"), "12:00", self.timezone_name, quiet=True)
        
        # Check if this is a solar term day
        is_solar_term = self.construction_stars._is_principal_solar_term_day(date_obj)
        
        # Construction Star with sequential tracking
        star = self.construction_stars.get_construction_star(date_obj, dto, prev_star)
        ausp = self.construction_stars.AUSPICIOUSNESS[star]
        
        # Great Yellow Path
        spirit = self.great_yellow_path.calculate_spirit(dto.month, dto.day_branch)
        
        return {
            "date": date_obj.strftime("%Y-%m-%d"),
            "star": star,
            "translation": self.construction_stars.STAR_TRANSLATIONS[star],
            "level": ausp["level"],
            "score": ausp["score"],
            "day_branch": dto.day_branch,
            "lunar_month": dto.month,
            "lunar_month_display": f"{'閏' if dto.is_leap_month else ''}{dto.month}",
            "building_branch": BUILDING_BRANCH_BY_MONTH[dto.month],
            "is_leap_month": dto.is_leap_month,
            "is_solar_term": is_solar_term,
            "gyp_spirit": spirit.chinese,
            "gyp_spirit_eng": spirit.english,
            "gyp_is_auspicious": spirit.is_auspicious,
            "gyp_auspiciousness": "吉" if spirit.is_auspicious else "凶",
            "gyp_path_type": "黄道" if spirit.is_auspicious else "黑道"
        }

    def print_month_calendar(self, year: int, month: int) -> None:
        """Print formatted calendar table for a specific month"""
        # Build date range for entire month
        days_in_month = calendar.monthrange(year, month)[1]
        date_range = [(datetime(year, month, day).strftime("%Y-%m-%d"), "12:00")
                      for day in range(1, days_in_month + 1)]
        
        # Batch convert all dates to lunisolar (much faster!)
        lunisolar_results = solar_to_lunisolar_batch(date_range, self.timezone_name, quiet=True)
        
        # Get mid-month data for header info
        mid_idx = 14  # 15th day (0-indexed)
        mid_dto = lunisolar_results[mid_idx]
        
        month_branch = BUILDING_BRANCH_BY_MONTH[mid_dto.month]
        month_pinyin = EARTHLY_BRANCH_PINYIN.get(month_branch, "")
        azure_start = AZURE_DRAGON_MONTHLY_START[mid_dto.month]
        mnemonic = MNEMONIC_FORMULAS[mid_dto.month]
        
        # Print header
        month_name = calendar.month_name[month]
        print(f"\n{'='*150}")
        print(f"{month_name} {year} - Construction Stars & Great Yellow Path Calendar")
        print(f"{'='*150}")
        print(f"Lunar Month: {mid_dto.month} ({month_branch} - {month_pinyin})")
        print(f"Azure Dragon Start: {azure_start.chinese} ({EARTHLY_BRANCH_PINYIN[azure_start.chinese]}) | Mnemonic: {mnemonic}")
        print(f"{'='*150}")
        print(f"{'Date':<6} {'Star':<4} {'Translation':<15} {'Level':<16} {'Score':<5} {'Spirit':<8} {'Path':<6} {'Day Branch':<12} {'Icons':<6}")
        print(f"{'-'*150}")
        
        # Calculate and print each day using batched results with sequential tracking
        prev_star = None
        
        for day, dto in enumerate(lunisolar_results, start=1):
            date_obj = datetime(year, month, day)
            info = self.calculate_day_info(date_obj, dto, prev_star)
            
            # Update tracking variables for next iteration
            prev_star = info["star"]
            
            date_str = f"{day:02d}"
            star = info["star"]
            translation = info["translation"][:13]
            level = info["level"][:14]
            score = info["score"]
            
            gyp_spirit = info["gyp_spirit"][:6]
            gyp_path = info["gyp_path_type"][:4]
            
            day_branch = info["day_branch"]
            day_pinyin = EARTHLY_BRANCH_PINYIN.get(day_branch, "")
            day_branch_display = f"{day_branch}({day_pinyin})"
            
            # Color coding
            if score >= 4:
                cs_icon = "🟨"  # Yellow - auspicious
            elif score == 3:
                cs_icon = "🟩"  # Green - moderate
            elif score == 2:
                cs_icon = "⬛"  # Black - inauspicious
            else:
                cs_icon = "🟥"  # Red - very inauspicious
            
            gyp_icon = "🟡" if info["gyp_is_auspicious"] else "⚫"
            
            print(f"{date_str:<6} {star:<4} {translation:<15} {level:<16} {score:<5} {gyp_spirit:<8} {gyp_path:<6} {day_branch_display:<12} {cs_icon}{gyp_icon}")
        
        print(f"{'='*150}\n")


# =====================================================================================
# CLI Main
# =====================================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Efficient Huangdao Systems Calculator - Print monthly calendar tables',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --year 2025 --month 10
  %(prog)s -y 2025 -m 1 --timezone Asia/Shanghai
  %(prog)s -y 2024 -m 12 -tz Asia/Tokyo

Legend:
  Construction Stars (十二建星):
    🟨 Yellow: Auspicious (除危定执) - Score 4
    🟩 Green: Moderate (成开) - Score 3
    ⬛ Black: Inauspicious (建满平收) - Score 2
    🟥 Red: Very Inauspicious (破闭) - Score 1
  
  Great Yellow Path (大黄道):
    🟡 Yellow Path (黄道): Auspicious days
    ⚫ Black Path (黑道): Inauspicious days
        """
    )
    parser.add_argument('--year', '-y', type=int, required=True,
                        help='Gregorian year (e.g., 2025)')
    parser.add_argument('--month', '-m', type=int, required=True,
                        help='Month number (1-12)')
    parser.add_argument('--timezone', '-tz', default='Asia/Ho_Chi_Minh',
                        help='Timezone (IANA format, default: Asia/Ho_Chi_Minh)')
    
    args = parser.parse_args()
    
    # Validate month
    if not 1 <= args.month <= 12:
        parser.error("Month must be between 1 and 12")
    
    # Create calculator and print calendar
    calculator = HuangdaoCalculator(args.timezone)
    calculator.print_month_calendar(args.year, args.month)


if __name__ == "__main__":
    main()
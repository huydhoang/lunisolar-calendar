"""HuangdaoCalculator — unified facade for Construction Stars and Great Yellow Path."""

from __future__ import annotations

import calendar
from datetime import datetime
from typing import Dict

from lunisolar.api import solar_to_lunisolar, solar_to_lunisolar_batch
from shared.constants import EARTHLY_BRANCH_PINYIN
from shared.models import LunisolarDateDTO

from .constants import (
    BRANCH_INDEX,
    BUILDING_BRANCH_BY_MONTH,
    AZURE_DRAGON_MONTHLY_START,
    MNEMONIC_FORMULAS,
)
from .construction_stars import ConstructionStars
from .great_yellow_path import GreatYellowPath


class HuangdaoCalculator:
    """Unified calculator for Construction Stars and Great Yellow Path"""

    def __init__(self, timezone_name: str = 'Asia/Ho_Chi_Minh'):
        self.timezone_name = timezone_name
        self.construction_stars = ConstructionStars(timezone_name)
        self.great_yellow_path = GreatYellowPath()

    def calculate_day_info(self, date_obj: datetime, dto: LunisolarDateDTO = None,
                           prev_star_index: int = None) -> Dict:
        """Calculate complete information for a single day.

        Args:
            date_obj: Target date
            dto: Lunisolar data (optional, will fetch if not provided)
            prev_star_index: 0-based index of the previous day's star for sequential tracking
        """
        if dto is None:
            dto = solar_to_lunisolar(date_obj.strftime("%Y-%m-%d"), "12:00", self.timezone_name, quiet=True)

        is_solar_term = self.construction_stars._is_principal_solar_term_day(date_obj)

        star = self.construction_stars.get_construction_star(date_obj, dto, prev_star_index)
        ausp = self.construction_stars.AUSPICIOUSNESS[star]

        spirit = self.great_yellow_path.calculate_spirit(dto.month, BRANCH_INDEX[dto.day_branch])

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
            "gyp_path_type": "黄道" if spirit.is_auspicious else "黑道",
        }

    def print_month_calendar(self, year: int, month: int) -> None:
        """Print formatted calendar table for a specific month."""
        days_in_month = calendar.monthrange(year, month)[1]
        date_range = [
            (datetime(year, month, day).strftime("%Y-%m-%d"), "12:00")
            for day in range(1, days_in_month + 1)
        ]

        lunisolar_results = solar_to_lunisolar_batch(date_range, self.timezone_name, quiet=True)

        mid_idx = 14  # 15th day (0-indexed)
        mid_dto = lunisolar_results[mid_idx]

        month_branch = BUILDING_BRANCH_BY_MONTH[mid_dto.month]
        month_pinyin = EARTHLY_BRANCH_PINYIN.get(month_branch, "")
        azure_start = AZURE_DRAGON_MONTHLY_START[mid_dto.month]
        mnemonic = MNEMONIC_FORMULAS[mid_dto.month]

        month_name = calendar.month_name[month]
        print(f"\n{'='*150}")
        print(f"{month_name} {year} - Construction Stars & Great Yellow Path Calendar")
        print(f"{'='*150}")
        print(f"Lunar Month: {mid_dto.month} ({month_branch} - {month_pinyin})")
        print(f"Azure Dragon Start: {azure_start.chinese} ({EARTHLY_BRANCH_PINYIN[azure_start.chinese]}) | Mnemonic: {mnemonic}")
        print(f"{'='*150}")
        print(f"{'Date':<6} {'Star':<4} {'Translation':<15} {'Level':<16} {'Score':<5} {'Spirit':<8} {'Path':<6} {'Day Branch':<12} {'Icons':<6}")
        print(f"{'-'*150}")

        prev_star_index = None

        for day, dto in enumerate(lunisolar_results, start=1):
            date_obj = datetime(year, month, day)
            info = self.calculate_day_info(date_obj, dto, prev_star_index)

            prev_star_index = self.construction_stars.CONSTRUCTION_STARS.index(info["star"])

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

            if score >= 4:
                cs_icon = "🟨"
            elif score == 3:
                cs_icon = "🟩"
            elif score == 2:
                cs_icon = "⬛"
            else:
                cs_icon = "🟥"

            gyp_icon = "🟡" if info["gyp_is_auspicious"] else "⚫"

            print(f"{date_str:<6} {star:<4} {translation:<15} {level:<16} {score:<5} {gyp_spirit:<8} {gyp_path:<6} {day_branch_display:<12} {cs_icon}{gyp_icon}")

        print(f"{'='*150}\n")

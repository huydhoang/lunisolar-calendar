"""ConstructionStars — Twelve Construction Stars (十二建星) Calculator."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict

import pytz
from skyfield.api import utc

from solar_terms import calculate_solar_terms
from shared.constants import PRINCIPAL_TERM_NAMES
from shared.models import LunisolarDateDTO
from .constants import BRANCH_INDEX, BUILDING_BRANCH_BY_MONTH


class ConstructionStars:
    """Twelve Construction Stars (十二建星) Calculator"""

    CONSTRUCTION_STARS = ["建", "除", "满", "平", "定", "执", "破", "危", "成", "收", "开", "闭"]

    STAR_TRANSLATIONS = {
        "建": "Jiàn (Establish)", "除": "Chú (Remove)", "满": "Mǎn (Full)",
        "平": "Píng (Balanced)", "定": "Dìng (Set)", "执": "Zhí (Hold)",
        "破": "Pò (Break)", "危": "Wēi (Danger)", "成": "Chéng (Accomplish)",
        "收": "Shōu (Harvest)", "开": "Kāi (Open)", "闭": "Bì (Close)",
    }

    # "建满平收黑，除危定执黄，成开皆可用，破闭不可当"
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
        "闭": {"level": "very_inauspicious", "score": 1},
    }

    def __init__(self, timezone_name: str):
        self.timezone_name = timezone_name
        self.tz = pytz.timezone(timezone_name)
        self._solar_term_cache: Dict[str, bool] = {}

    def _is_principal_solar_term_day(self, date_obj: datetime) -> bool:
        """Check if date is a principal solar term day (with caching)."""
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

    def _star_index_from_branches(self, building_branch_index: int, day_branch_index: int) -> int:
        """Calculate star index: (day_branch_index - building_branch_index) mod 12"""
        return (day_branch_index - building_branch_index) % 12

    def get_construction_star(self, date_obj: datetime, dto: LunisolarDateDTO,
                              prev_star_index: int = None) -> str:
        """Get construction star for date (with solar term repeat rule).

        Args:
            date_obj: Target date
            dto: Lunisolar date data for target
            prev_star_index: 0-based index of the previous day's star (for sequential tracking)
        """
        is_solar_term = self._is_principal_solar_term_day(date_obj)

        building_branch = BUILDING_BRANCH_BY_MONTH[dto.month]
        base_star_index = self._star_index_from_branches(BRANCH_INDEX[building_branch], BRANCH_INDEX[dto.day_branch])
        base_star = self.CONSTRUCTION_STARS[base_star_index]

        if prev_star_index is None:
            actual_star = base_star
        elif is_solar_term:
            actual_star = self.CONSTRUCTION_STARS[prev_star_index]
        else:
            actual_star_index = (prev_star_index + 1) % 12
            actual_star = self.CONSTRUCTION_STARS[actual_star_index]

        return actual_star

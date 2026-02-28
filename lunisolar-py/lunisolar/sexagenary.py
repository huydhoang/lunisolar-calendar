"""SexagenaryEngine — calculates sexagenary cycles for year, month, day, and hour."""

from datetime import datetime, timedelta, timezone
from typing import Tuple

from utils import setup_logging
from shared.constants import HEAVENLY_STEMS, EARTHLY_BRANCHES
from .timezone_service import TimezoneService


class SexagenaryEngine:
    """Calculates sexagenary cycles for year, month, day, and hour."""

    def __init__(self, timezone_service: TimezoneService):
        self.logger = setup_logging()
        self.tz_service = timezone_service

    def ganzhi_year(self, lunar_year: int) -> Tuple[str, str, int]:
        """Use 4 AD as authoritative Jiazi anchor; return (stem, branch, cycleIndex 1..60)."""
        year_cycle = (lunar_year - 4) % 60 + 1
        if year_cycle <= 0:
            year_cycle += 60

        stem_char, branch_char, _, _ = self._get_stem_branch(year_cycle)
        return stem_char, branch_char, year_cycle

    def ganzhi_month(self, lunar_year: int, lunar_month: int) -> Tuple[str, str, int]:
        """Calculate month stem and branch using traditional rules based on year stem."""
        year_stem, _, _ = self.ganzhi_year(lunar_year)
        year_stem_idx = next(
            (i for i, (char, _, _, _) in enumerate(HEAVENLY_STEMS) if char == year_stem), 0
        ) + 1

        # Traditional month stem calculation mapping
        mapping_first_month_stem = {
            1: 3, 6: 3,    # 甲/己 -> 丙 (index 3)
            2: 5, 7: 5,    # 乙/庚 -> 戊 (index 5)
            3: 7, 8: 7,    # 丙/辛 -> 庚 (index 7)
            4: 9, 9: 9,    # 丁/壬 -> 壬 (index 9)
            5: 1, 10: 1,   # 戊/癸 -> 甲 (index 1)
        }

        first_month_stem_idx = mapping_first_month_stem[year_stem_idx]
        month_stem_idx = ((first_month_stem_idx - 1 + (lunar_month - 1)) % 10) + 1

        # Month branch calculation
        month_branch_idx = (lunar_month + 2) % 12
        if month_branch_idx == 0:
            month_branch_idx = 12

        month_stem_char = HEAVENLY_STEMS[month_stem_idx - 1][0]
        month_branch_char = EARTHLY_BRANCHES[month_branch_idx - 1][0]

        month_cycle = self._calculate_cycle_from_stem_branch(month_stem_idx, month_branch_idx)
        return month_stem_char, month_branch_char, month_cycle

    def ganzhi_day(self, target_local: datetime) -> Tuple[str, str, int]:
        """Day cycle using continuous count and documented historical anchors."""
        reference_date_utc = datetime(4, 1, 31, tzinfo=timezone.utc)

        days_diff = (target_local.date() - reference_date_utc.date()).days
        day_cycle = (days_diff % 60) + 1

        stem_char, branch_char, _, _ = self._get_stem_branch(day_cycle)
        return stem_char, branch_char, day_cycle

    def ganzhi_hour(self, target_local: datetime, base_day_stem: str) -> Tuple[str, str, int]:
        """Apply Wu Shu Dun; for 23:00-23:59, advance day before computing hour stem/branch."""
        hour = target_local.hour
        minute = target_local.minute

        hour_branch_char, hour_branch_name, hour_branch_index = self._get_hour_branch(hour, minute)

        # Handle 23:00-23:59 boundary (belongs to next day's Zi hour)
        if hour >= 23:
            next_day_local = target_local + timedelta(days=1)
            next_day_stem, _, _ = self.ganzhi_day(next_day_local)
            base_day_stem = next_day_stem

        hour_stem_char = self._calculate_hour_stem(base_day_stem, hour_branch_index)

        stem_index = next(
            (i for i, (char, _, _, _) in enumerate(HEAVENLY_STEMS) if char == hour_stem_char), 0
        )
        hour_cycle = self._calculate_cycle_from_stem_branch(stem_index + 1, hour_branch_index)

        return hour_stem_char, hour_branch_char, hour_cycle

    def _get_stem_branch(self, cycle_number: int) -> Tuple[str, str, int, int]:
        """Get Heavenly Stem and Earthly Branch for a given cycle number."""
        stem_index = (cycle_number - 1) % 10
        branch_index = (cycle_number - 1) % 12

        stem_char = HEAVENLY_STEMS[stem_index][0]
        branch_char = EARTHLY_BRANCHES[branch_index][0]

        return stem_char, branch_char, stem_index + 1, branch_index + 1

    def _get_hour_branch(self, hour: int, minute: int = 0) -> Tuple[str, str, int]:
        """Get the Earthly Branch for a given hour."""
        decimal_hour = hour + minute / 60.0

        if decimal_hour >= 23.0 or decimal_hour < 1.0:
            branch_index = 0  # 子 (Zi)
        else:
            branch_index = int((decimal_hour - 1.0) // 2.0) + 1
            if branch_index >= 12:
                branch_index = 11

        branch_char = EARTHLY_BRANCHES[branch_index][0]
        branch_name = EARTHLY_BRANCHES[branch_index][2]

        return branch_char, branch_name, branch_index + 1

    def _calculate_hour_stem(self, day_stem: str, hour_branch_index: int) -> str:
        """Calculate hour stem using Wu Shu Dun (五鼠遁) rule."""
        wu_shu_dun = {
            '甲': 0, '己': 0,
            '乙': 2, '庚': 2,
            '丙': 4, '辛': 4,
            '丁': 6, '壬': 6,
            '戊': 8, '癸': 8,
        }

        zi_hour_stem_index = wu_shu_dun.get(day_stem, 0)
        hour_stem_index = (zi_hour_stem_index + hour_branch_index - 1) % 10

        return HEAVENLY_STEMS[hour_stem_index][0]

    def _calculate_cycle_from_stem_branch(self, stem_idx: int, branch_idx: int) -> int:
        """Calculate 60-cycle position from stem and branch indices."""
        stem_0 = stem_idx - 1
        branch_0 = branch_idx - 1

        for cycle in range(1, 61):
            cycle_stem = (cycle - 1) % 10
            cycle_branch = (cycle - 1) % 12
            if cycle_stem == stem_0 and cycle_branch == branch_0:
                return cycle

        return 1

"""LunarMonthResolver, ResultAssembler — resolve target month and assemble result."""

from datetime import datetime
from typing import List, Tuple

from utils import setup_logging
from shared.models import MonthPeriod, LunisolarDateDTO
from .timezone_service import TimezoneService


class LunarMonthResolver:
    """Resolves target month information from periods."""

    def __init__(self, timezone_service: TimezoneService):
        self.logger = setup_logging()
        self.tz_service = timezone_service

    def find_period_for_datetime(self, periods: List[MonthPeriod], target_utc: datetime) -> MonthPeriod:
        """Match by CST date-only boundaries: startCstDate <= targetCstDate < endCstDate."""
        if target_utc.tzinfo is not None:
            target_naive = target_utc.replace(tzinfo=None)
        else:
            target_naive = target_utc

        target_cst_date = self.tz_service.utc_to_cst_date(target_naive)

        for period in periods:
            if period.start_cst_date <= target_cst_date < period.end_cst_date:
                return period

        raise ValueError(f"No period found for date {target_cst_date}")

    def calculate_lunar_day(self, target_utc: datetime, period: MonthPeriod) -> int:
        """Return day-in-month using CST date-only difference from period.startCstDate, bounded 1..30."""
        if target_utc.tzinfo is not None:
            target_naive = target_utc.replace(tzinfo=None)
        else:
            target_naive = target_utc

        target_cst_date = self.tz_service.utc_to_cst_date(target_naive)
        days_diff = (target_cst_date - period.start_cst_date).days + 1
        return max(1, min(30, days_diff))

    def calculate_lunar_year(self, target_period: MonthPeriod) -> int:
        """Calculate the correct lunar year based on the target period.

        The lunar year follows this logic:
        - Month 1 (Lunar New Year) starts a new lunar year
        - The lunar year number is the Gregorian year when Month 1 occurs
        - Months 1-10 belong to the lunar year that started with the current Month 1
        - Months 11-12 belong to the SAME lunar year (not the next one)

        For months 11-12, the lunar year equals the Gregorian year in which
        Month 1 of that year occurred:
        - Month 11 always starts in Nov/Dec -> period_start.year is correct
        - Month 12 may start in Dec (same year) or Jan (next Gregorian year),
          so we check and subtract 1 when the period starts in Jan/Feb
        """
        period_start = target_period.start_utc
        if period_start.tzinfo:
            period_start = period_start.replace(tzinfo=None)

        if target_period.month_number <= 11:
            return period_start.year
        else:  # month 12
            if period_start.month <= 2:
                return period_start.year - 1
            return period_start.year


class ResultAssembler:
    """Assembles the final LunisolarDateDTO."""

    def __init__(self):
        self.logger = setup_logging()

    def assemble_result(
        self,
        lunar_year: int,
        target_period: MonthPeriod,
        lunar_day: int,
        local_hour: int,
        year_ganzhi: Tuple[str, str, int],
        month_ganzhi: Tuple[str, str, int],
        day_ganzhi: Tuple[str, str, int],
        hour_ganzhi: Tuple[str, str, int],
    ) -> LunisolarDateDTO:
        """Assemble complete LunisolarDateDTO from components."""
        year_stem, year_branch, year_cycle = year_ganzhi
        month_stem, month_branch, month_cycle = month_ganzhi
        day_stem, day_branch, day_cycle = day_ganzhi
        hour_stem, hour_branch, hour_cycle = hour_ganzhi

        return LunisolarDateDTO(
            year=lunar_year,
            month=target_period.month_number,
            day=lunar_day,
            hour=local_hour,
            is_leap_month=target_period.is_leap,
            year_stem=year_stem,
            year_branch=year_branch,
            month_stem=month_stem,
            month_branch=month_branch,
            day_stem=day_stem,
            day_branch=day_branch,
            hour_stem=hour_stem,
            hour_branch=hour_branch,
            year_cycle=year_cycle,
            month_cycle=month_cycle,
            day_cycle=day_cycle,
            hour_cycle=hour_cycle,
        )

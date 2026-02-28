"""Public API — solar_to_lunisolar, solar_to_lunisolar_batch, pinyin helpers."""

import logging
from typing import List, Tuple

from utils import setup_logging
from timezone_handler import TimezoneHandler
from shared.constants import HEAVENLY_STEMS, EARTHLY_BRANCHES
from shared.models import LunisolarDateDTO

from .timezone_service import TimezoneService
from .window_planner import WindowPlanner
from .ephemeris_service import EphemerisService
from .month_builder import MonthBuilder, TermIndexer, LeapMonthAssigner
from .sexagenary import SexagenaryEngine
from .resolver import LunarMonthResolver, ResultAssembler


def solar_to_lunisolar_batch(
    date_range: List[Tuple[str, str]],
    timezone_name: str = 'Asia/Shanghai',
    quiet: bool = True,
) -> List[LunisolarDateDTO]:
    """Efficiently convert multiple solar dates to lunisolar dates in batch.

    Processes multiple dates using a single ephemeris window calculation,
    making it much more efficient than calling solar_to_lunisolar repeatedly.

    Args:
        date_range: List of (date_str, time_str) tuples in format [("YYYY-MM-DD", "HH:MM"), ...]
        timezone_name: IANA timezone name (default: 'Asia/Shanghai' for CST)
        quiet: If True, suppresses info-level logging (default: True)

    Returns:
        List of LunisolarDateDTO objects in the same order as input
    """
    if not date_range:
        return []

    logger = setup_logging()
    if quiet:
        logger.setLevel(logging.WARNING)

    try:
        tz_handler = TimezoneHandler(timezone_name)
        tz_service = TimezoneService(tz_handler)
        window_planner = WindowPlanner()
        ephemeris_service = EphemerisService()
        month_builder = MonthBuilder(tz_service)
        term_indexer = TermIndexer()
        leap_assigner = LeapMonthAssigner()
        sexagenary_engine = SexagenaryEngine(tz_service)
        month_resolver = LunarMonthResolver(tz_service)
        result_assembler = ResultAssembler()

        # Parse all dates and find the window that covers all of them
        parsed_dates = []
        for solar_date, solar_time in date_range:
            local_dt = tz_service.parse_local_datetime(solar_date, solar_time)
            target_utc = tz_service.local_to_utc(local_dt)
            parsed_dates.append((local_dt, target_utc))

        all_utc_dates = [utc for _, utc in parsed_dates]
        min_date = min(all_utc_dates)
        max_date = max(all_utc_dates)

        window_start_min, _ = window_planner.compute_window(min_date)
        _, window_end_max = window_planner.compute_window(max_date)

        new_moons = ephemeris_service.compute_new_moons(window_start_min, window_end_max)
        principal_terms = ephemeris_service.compute_principal_terms(window_start_min, window_end_max)

        if not new_moons:
            raise ValueError("No new moons found in calculation window")

        periods = month_builder.build_month_periods(new_moons)
        term_indexer.tag_principal_terms(periods, principal_terms)

        # Find Winter Solstice anchors for the years involved
        years = set(utc_dt.year for _, utc_dt in parsed_dates)
        solstices = {}
        for year in years:
            solstices[year] = window_planner._find_winter_solstice(year)
            solstices[year - 1] = window_planner._find_winter_solstice(year - 1)

        results = []
        for local_datetime, target_utc in parsed_dates:
            target_naive = target_utc.replace(tzinfo=None) if target_utc.tzinfo else target_utc
            current_year_solstice = solstices[target_utc.year]

            if target_naive >= current_year_solstice:
                anchor_solstice = current_year_solstice
            else:
                anchor_solstice = solstices[target_utc.year - 1]

            leap_assigner.assign_month_numbers(periods, anchor_solstice)

            target_period = month_resolver.find_period_for_datetime(periods, target_utc)
            lunar_day = month_resolver.calculate_lunar_day(target_utc, target_period)
            lunar_year = month_resolver.calculate_lunar_year(target_period)

            year_ganzhi = sexagenary_engine.ganzhi_year(lunar_year)
            month_ganzhi = sexagenary_engine.ganzhi_month(lunar_year, target_period.month_number)
            day_ganzhi = sexagenary_engine.ganzhi_day(local_datetime)
            hour_ganzhi = sexagenary_engine.ganzhi_hour(local_datetime, day_ganzhi[0])

            result = result_assembler.assemble_result(
                lunar_year=lunar_year,
                target_period=target_period,
                lunar_day=lunar_day,
                local_hour=local_datetime.hour,
                year_ganzhi=year_ganzhi,
                month_ganzhi=month_ganzhi,
                day_ganzhi=day_ganzhi,
                hour_ganzhi=hour_ganzhi,
            )
            results.append(result)

        return results

    except Exception as e:
        logger.error(f"Error in solar_to_lunisolar_batch conversion: {e}")
        raise
    finally:
        if quiet:
            logger.setLevel(logging.INFO)


def solar_to_lunisolar(
    solar_date: str,
    solar_time: str = "12:00",
    timezone_name: str = 'Asia/Shanghai',
    quiet: bool = False,
) -> LunisolarDateDTO:
    """Convert solar date and time to lunisolar date with stems and branches.

    This is the main entry point that orchestrates the entire conversion pipeline.

    Args:
        solar_date: Solar date in YYYY-MM-DD format
        solar_time: Solar time in HH:MM format (default: 12:00)
        timezone_name: IANA timezone name (default: 'Asia/Shanghai' for CST)
        quiet: If True, suppresses info-level logging (default: False)

    Returns:
        LunisolarDateDTO object with complete lunisolar information
    """
    logger = setup_logging()
    original_level = logger.level

    if quiet:
        logger.setLevel(logging.WARNING)

    try:
        tz_handler = TimezoneHandler(timezone_name)
        tz_service = TimezoneService(tz_handler)
        window_planner = WindowPlanner()
        ephemeris_service = EphemerisService()
        month_builder = MonthBuilder(tz_service)
        term_indexer = TermIndexer()
        leap_assigner = LeapMonthAssigner()
        sexagenary_engine = SexagenaryEngine(tz_service)
        month_resolver = LunarMonthResolver(tz_service)
        result_assembler = ResultAssembler()

        local_datetime = tz_service.parse_local_datetime(solar_date, solar_time)
        target_utc = tz_service.local_to_utc(local_datetime)

        logger.info(f"Converting {solar_date} {solar_time} to lunisolar")

        window_start, window_end = window_planner.compute_window(target_utc)

        new_moons = ephemeris_service.compute_new_moons(window_start, window_end)
        principal_terms = ephemeris_service.compute_principal_terms(window_start, window_end)

        if not new_moons:
            raise ValueError("No new moons found in calculation window")

        periods = month_builder.build_month_periods(new_moons)
        term_indexer.tag_principal_terms(periods, principal_terms)

        target_naive = target_utc.replace(tzinfo=None) if target_utc.tzinfo else target_utc
        current_year_solstice = window_planner._find_winter_solstice(target_utc.year)

        if target_naive >= current_year_solstice:
            anchor_solstice = current_year_solstice
        else:
            anchor_solstice = window_planner._find_winter_solstice(target_utc.year - 1)

        leap_assigner.assign_month_numbers(periods, anchor_solstice)

        target_period = month_resolver.find_period_for_datetime(periods, target_utc)
        lunar_day = month_resolver.calculate_lunar_day(target_utc, target_period)
        lunar_year = month_resolver.calculate_lunar_year(target_period)

        year_ganzhi = sexagenary_engine.ganzhi_year(lunar_year)
        month_ganzhi = sexagenary_engine.ganzhi_month(lunar_year, target_period.month_number)
        day_ganzhi = sexagenary_engine.ganzhi_day(local_datetime)
        hour_ganzhi = sexagenary_engine.ganzhi_hour(local_datetime, day_ganzhi[0])

        result = result_assembler.assemble_result(
            lunar_year=lunar_year,
            target_period=target_period,
            lunar_day=lunar_day,
            local_hour=local_datetime.hour,
            year_ganzhi=year_ganzhi,
            month_ganzhi=month_ganzhi,
            day_ganzhi=day_ganzhi,
            hour_ganzhi=hour_ganzhi,
        )

        logger.info(f"Conversion completed: {result.year}-{result.month}-{result.day}")
        return result

    except Exception as e:
        logger.error(f"Error in solar_to_lunisolar conversion: {e}")
        raise
    finally:
        if quiet:
            logger.setLevel(original_level)


def get_stem_pinyin(stem_index: int) -> str:
    """Get pinyin for a heavenly stem by 0-based index (0=甲 ... 9=癸)."""
    if 0 <= stem_index < len(HEAVENLY_STEMS):
        return HEAVENLY_STEMS[stem_index][1]
    return ""


def get_branch_pinyin(branch_index: int) -> str:
    """Get pinyin for an earthly branch by 0-based index (0=子 ... 11=亥)."""
    if 0 <= branch_index < len(EARTHLY_BRANCHES):
        return EARTHLY_BRANCHES[branch_index][1]
    return ""

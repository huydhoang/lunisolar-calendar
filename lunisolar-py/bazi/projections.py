"""
Time Projection Functions (Year / Month / Day)
===============================================
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

from .constants import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES, STEM_ELEMENT, BRANCH_ELEMENT,
    GEN_MAP, CONTROL_MAP, LIU_CHONG, LIU_HE, LIU_HAI,
)
from .core import ganzhi_from_cycle
from .ten_gods import ten_god
from .longevity import life_stage_detail
from .nayin import nayin_for_cycle, _nayin_pure_element
from .punishments import detect_fu_yin_duplication

try:
    from datetime import UTC as utc
except ImportError:
    from datetime import timezone
    utc = timezone.utc

from shared.models import LunisolarDateDTO
from lunisolar.api import solar_to_lunisolar, solar_to_lunisolar_batch
from ephemeris.moon_phases import calculate_moon_phases


def get_year_cycle_for_gregorian(year: int) -> int:
    """Get the sexagenary cycle number for a Gregorian year (立春 based)."""
    base_year = 1984
    base_cycle = 1
    offset = (year - base_year) % 60
    return base_cycle + offset


def get_month_cycle_for_date(solar_date: str, solar_time: str = "12:00") -> int:
    """Get the month pillar cycle number for a given solar date."""
    dto = solar_to_lunisolar(solar_date, solar_time, quiet=True)
    return dto.month_cycle


def get_day_cycle_for_date(solar_date: str, solar_time: str = "12:00") -> int:
    """Get the day pillar cycle number for a given solar date."""
    dto = solar_to_lunisolar(solar_date, solar_time, quiet=True)
    return dto.day_cycle


def get_new_moon_dates(start_date: date, count: int = 36) -> List[date]:
    """Return the next *count* new moon solar dates on or after *start_date*."""
    results: List[date] = []
    window_start = datetime(
        start_date.year, start_date.month, start_date.day, tzinfo=utc
    )
    while len(results) < count:
        window_end = window_start + timedelta(days=365 * 3)
        phases = calculate_moon_phases(window_start, window_end)
        for ts, phase_idx, _name in phases:
            if phase_idx == 0:  # New Moon
                nm_date = datetime.fromtimestamp(ts, tz=utc).date()
                if nm_date >= start_date:
                    results.append(nm_date)
        if results:
            last = results[-1]
            window_start = datetime(
                last.year, last.month, last.day, tzinfo=utc
            ) + timedelta(days=1)
        else:
            window_start = window_end
    return results[:count]


def _strength_delta(dm_elem: str, stem: str, branch: str) -> int:
    """Compute approximate Day-Master strength delta from a pillar."""
    delta = 0
    elem_stem = STEM_ELEMENT[stem]
    elem_branch = BRANCH_ELEMENT[branch]

    if GEN_MAP.get(elem_stem) == dm_elem or elem_stem == dm_elem:
        delta += 1
    elif CONTROL_MAP.get(elem_stem) == dm_elem or GEN_MAP.get(dm_elem) == elem_stem:
        delta -= 1

    if GEN_MAP.get(elem_branch) == dm_elem or elem_branch == dm_elem:
        delta += 2
    elif CONTROL_MAP.get(elem_branch) == dm_elem or GEN_MAP.get(dm_elem) == elem_branch:
        delta -= 2

    return delta


def generate_year_projections(
    chart: Dict, start_year: int, end_year: int
) -> List[Dict]:
    """Generate year-by-year projections from start_year up to end_year."""
    projections: List[Dict] = []
    dm_idx = HEAVENLY_STEMS.index(chart["day_master"]["stem"])
    dm_elem = chart["day_master"]["element"]

    natal_branches = [p["branch"] for p in chart["pillars"].values()]

    for year in range(start_year, end_year + 1):
        cycle = get_year_cycle_for_gregorian(year)
        if cycle < 1 or cycle > 60:
            cycle = ((cycle - 1) % 60) + 1

        stem, branch = ganzhi_from_cycle(cycle)
        b_idx = EARTHLY_BRANCHES.index(branch)

        interactions: List[str] = []
        for b in natal_branches:
            pair = frozenset({b, branch})
            if pair in LIU_CHONG:
                interactions.append("冲")
            if pair in LIU_HE:
                interactions.append("合")
            if pair in LIU_HAI:
                interactions.append("害")

        life_stage = life_stage_detail(dm_idx, b_idx)
        tg = ten_god(dm_idx, HEAVENLY_STEMS.index(stem))
        nayin = nayin_for_cycle(cycle)

        delta = _strength_delta(dm_elem, stem, branch)

        entry: Dict = {
            "year": year,
            "cycle": cycle,
            "stem": stem,
            "branch": branch,
            "ganzhi": stem + branch,
            "ten_god": tg,
            "life_stage": life_stage,
            "interactions": interactions,
            "strength_delta": delta,
        }
        if nayin:
            entry["nayin"] = {
                "element": _nayin_pure_element(nayin["nayin_element"]),
                "chinese": nayin["nayin_chinese"],
            }

        fu_yin_duplication = detect_fu_yin_duplication(
            chart, {"stem": stem, "branch": branch}
        )
        if fu_yin_duplication:
            entry["fu_yin_duplication"] = fu_yin_duplication

        projections.append(entry)

    return projections


def generate_month_projections(
    chart: Dict,
    start_date: date,
    end_date: Optional[date],
    use_new_moons: bool = True,
) -> List[Dict]:
    """Generate month-by-month projections."""
    projections: List[Dict] = []
    dm_idx = HEAVENLY_STEMS.index(chart["day_master"]["stem"])
    dm_elem = chart["day_master"]["element"]

    if use_new_moons:
        target_dates = get_new_moon_dates(start_date, 36)
        date_tuples = [(dt.strftime("%Y-%m-%d"), "00:00") for dt in target_dates]
        lunisolar_infos = solar_to_lunisolar_batch(date_tuples, quiet=True) if date_tuples else []
    else:
        target_dates = []
        current = start_date
        max_entries = 1200
        count = 0
        while count < max_entries:
            target_dates.append(current)
            if end_date and current >= end_date:
                break
            current = current + timedelta(days=30)
            count += 1
        date_tuples = [(dt.strftime("%Y-%m-%d"), "12:00") for dt in target_dates]
        lunisolar_infos = solar_to_lunisolar_batch(date_tuples, quiet=True) if date_tuples else []

    if not target_dates:
        return []

    natal_branches = [p["branch"] for p in chart["pillars"].values()]

    for i, (dt, dto) in enumerate(zip(target_dates, lunisolar_infos)):
        try:
            month_cycle = dto.month_cycle
            stem, branch = ganzhi_from_cycle(month_cycle)
            b_idx = EARTHLY_BRANCHES.index(branch)

            interactions: List[str] = []
            for b in natal_branches:
                pair = frozenset({b, branch})
                if pair in LIU_CHONG:
                    interactions.append("冲")
                if pair in LIU_HE:
                    interactions.append("合")
                if pair in LIU_HAI:
                    interactions.append("害")

            life_stage = life_stage_detail(dm_idx, b_idx)
            tg = ten_god(dm_idx, HEAVENLY_STEMS.index(stem))
            delta = _strength_delta(dm_elem, stem, branch)

            entry: Dict = {
                "month_num": i + 1,
                "solar_date": dt.strftime("%Y-%m-%d"),
                "date": dt.strftime("%Y-%m-%d"),
                "year": dt.year,
                "month": dt.month,
                "cycle": month_cycle,
                "stem": stem,
                "branch": branch,
                "ganzhi": stem + branch,
                "ten_god": tg,
                "life_stage": life_stage,
                "interactions": interactions,
                "strength_delta": delta,
            }
            if use_new_moons:
                leap_tag = "*" if dto.is_leap_month else ""
                entry["lunisolar_date"] = (
                    dto.year, dto.month, dto.day, dto.is_leap_month, leap_tag,
                )
            projections.append(entry)
        except Exception:
            pass

    return projections


def generate_day_projections(
    chart: Dict, start_date: date, end_date: Optional[date]
) -> List[Dict]:
    """Generate day-by-day projections up to end_date (or a default of 100 days)."""
    projections: List[Dict] = []
    dm_idx = HEAVENLY_STEMS.index(chart["day_master"]["stem"])
    dm_elem = chart["day_master"]["element"]

    target_dates: List[date] = []
    current = start_date
    max_days = 100 if not end_date else 4000
    count = 0

    while count < max_days:
        target_dates.append(current)
        if end_date and current >= end_date:
            break
        current += timedelta(days=1)
        count += 1

    date_tuples = [(dt.strftime("%Y-%m-%d"), "12:00") for dt in target_dates]
    if not date_tuples:
        return []

    dtos = solar_to_lunisolar_batch(date_tuples, quiet=True)
    natal_branches = [p["branch"] for p in chart["pillars"].values()]

    for i, (dt, dto) in enumerate(zip(target_dates, dtos)):
        try:
            day_cycle = dto.day_cycle
            stem, branch = ganzhi_from_cycle(day_cycle)
            b_idx = EARTHLY_BRANCHES.index(branch)

            interactions: List[str] = []
            for b in natal_branches:
                pair = frozenset({b, branch})
                if pair in LIU_CHONG:
                    interactions.append("冲")
                if pair in LIU_HE:
                    interactions.append("合")
                if pair in LIU_HAI:
                    interactions.append("害")

            life_stage = life_stage_detail(dm_idx, b_idx)
            tg = ten_god(dm_idx, HEAVENLY_STEMS.index(stem))
            delta = _strength_delta(dm_elem, stem, branch)

            entry: Dict = {
                "day_num": i + 1,
                "date": dt.strftime("%Y-%m-%d"),
                "weekday": dt.strftime("%a"),
                "cycle": day_cycle,
                "stem": stem,
                "branch": branch,
                "ganzhi": stem + branch,
                "ten_god": tg,
                "life_stage": life_stage,
                "interactions": interactions,
                "strength_delta": delta,
            }
            projections.append(entry)
        except Exception:
            pass

    return projections

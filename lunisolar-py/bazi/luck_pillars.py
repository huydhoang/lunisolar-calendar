"""
Luck Pillar Calculation (大运) — spec §5
=========================================
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .constants import HEAVENLY_STEMS, EARTHLY_BRANCHES, STEM_POLARITY
from .core import normalize_gender, ganzhi_from_cycle, _cycle_from_stem_branch
from .longevity import changsheng_stage, life_stage_detail
from .ten_gods import ten_god
from .nayin import nayin_for_cycle, _nayin_pure_element

try:
    from datetime import UTC as utc
except ImportError:
    from datetime import timezone
    utc = timezone.utc

from ephemeris.solar_terms import calculate_solar_terms


def _next_ganzhi(stem: str, branch: str, forward: bool = True) -> Tuple[str, str]:
    """Advance (or retreat) one position in the sexagenary cycle."""
    s_idx = HEAVENLY_STEMS.index(stem)
    b_idx = EARTHLY_BRANCHES.index(branch)
    delta = 1 if forward else -1
    return (
        HEAVENLY_STEMS[(s_idx + delta) % 10],
        EARTHLY_BRANCHES[(b_idx + delta) % 12],
    )


def _luck_direction(chart: Dict) -> bool:
    """Return *True* if luck pillars advance forward (clockwise)."""
    year_stem = chart["pillars"]["year"]["stem"]
    gender = normalize_gender(chart.get("gender", "male"))
    is_yang = STEM_POLARITY[year_stem] == "Yang"
    return (is_yang and gender == "male") or (not is_yang and gender == "female")


def find_governing_jie_term(birth_dt: datetime, forward: bool) -> Optional[datetime]:
    """Find the governing Jie (Nodal) solar term date for luck pillar calculation."""
    if forward:
        search_start = birth_dt
        search_end = birth_dt + timedelta(days=35)
    else:
        search_start = birth_dt - timedelta(days=35)
        search_end = birth_dt

    terms = calculate_solar_terms(search_start, search_end)
    jie_terms = [t for t in terms if t[1] % 2 != 0]

    if not jie_terms:
        return None

    jie_terms.sort(key=lambda x: x[0], reverse=not forward)
    return datetime.fromtimestamp(jie_terms[0][0], tz=utc)


def calculate_luck_start_age(
    birth_date: date,
    solar_term_date: date,
    forward: bool,
) -> Tuple[int, int]:
    """Calculate the starting age of the first Luck Pillar (大运).

    Implements the traditional **3-Day Rule**: 3 days from birth to the
    governing solar term equals 1 year of life, and 1 day equals 4 months.
    """
    delta_days = abs((solar_term_date - birth_date).days)
    total_months = delta_days * 4
    years = total_months // 12
    months = total_months % 12
    return int(years), int(months)


def generate_luck_pillars(
    chart: Dict,
    count: int = 8,
    birth_date: Optional[date] = None,
    solar_term_date: Optional[date] = None,
    birth_year: Optional[int] = None,
) -> List[Dict]:
    """Generate *count* Luck Pillars (大运) from the month pillar."""
    forward = _luck_direction(chart)
    dm_idx = HEAVENLY_STEMS.index(chart["day_master"]["stem"])

    start_years: Optional[int] = None
    start_months: int = 0

    if birth_date is not None and solar_term_date is not None:
        start_years, start_months = calculate_luck_start_age(
            birth_date, solar_term_date, forward,
        )
    elif birth_year is not None:
        start_years = 1
        start_months = 0

    effective_birth_year: Optional[int] = None
    if birth_date is not None:
        effective_birth_year = birth_date.year
    elif birth_year is not None:
        effective_birth_year = birth_year

    stem = chart["pillars"]["month"]["stem"]
    branch = chart["pillars"]["month"]["branch"]
    pillars: List[Dict] = []
    for i in range(count):
        stem, branch = _next_ganzhi(stem, branch, forward)
        b_idx = EARTHLY_BRANCHES.index(branch)
        s_idx = HEAVENLY_STEMS.index(stem)
        entry: Dict = {
            "stem": stem,
            "branch": branch,
            "longevity_stage": changsheng_stage(dm_idx, b_idx),
            "ten_god": ten_god(dm_idx, s_idx),
            "life_stage_detail": life_stage_detail(dm_idx, b_idx),
        }
        lp_cycle = _cycle_from_stem_branch(stem, branch)
        lp_nayin = nayin_for_cycle(lp_cycle)
        if lp_nayin:
            entry["nayin"] = {
                "element": _nayin_pure_element(lp_nayin["nayin_element"]),
                "chinese": lp_nayin["nayin_chinese"],
                "vietnamese": lp_nayin["nayin_vietnamese"],
                "english": lp_nayin["nayin_english"],
            }
        if start_years is not None:
            cycle_start_months = (start_years * 12 + start_months) + i * 120
            age_years = cycle_start_months // 12
            age_months = cycle_start_months % 12
            entry["start_age"] = (age_years, age_months)
            if effective_birth_year is not None:
                entry["start_gregorian_year"] = effective_birth_year + age_years
        pillars.append(entry)
    return pillars

"""
Core Chart Construction
=======================

normalize_gender, ganzhi_from_cycle, _cycle_from_stem_branch, build_chart,
from_lunisolar_dto, from_solar_date.
"""

from typing import Dict, Tuple, Union

from lunisolar_v2 import LunisolarDateDTO, solar_to_lunisolar

from .constants import HEAVENLY_STEMS, EARTHLY_BRANCHES, STEM_ELEMENT
from .ten_gods import ten_god
from .hidden_stems import branch_hidden_with_roles
from .nayin import nayin_for_cycle, _nayin_pure_element


def normalize_gender(gender: Union[str, None]) -> str:
    """Normalize and validate gender string. Returns ``'male'`` or ``'female'``."""
    if gender is None:
        raise ValueError("gender must be provided as 'male' or 'female'")
    g = str(gender).strip().lower()
    if g in ("m", "male", "man", "男"):
        return "male"
    if g in ("f", "female", "woman", "女"):
        return "female"
    raise ValueError("gender must be 'male' or 'female' (or common aliases)")


def ganzhi_from_cycle(cycle: int) -> Tuple[str, str]:
    """Convert a 1-60 sexagenary cycle number to (stem, branch) characters."""
    if not (1 <= cycle <= 60):
        raise ValueError(f"Cycle must be between 1 and 60, got {cycle}")
    stem = HEAVENLY_STEMS[(cycle - 1) % 10]
    branch = EARTHLY_BRANCHES[(cycle - 1) % 12]
    return stem, branch


def _cycle_from_stem_branch(stem: str, branch: str) -> int:
    """Compute sexagenary cycle number (1-60) from stem and branch characters."""
    s_idx = HEAVENLY_STEMS.index(stem)
    b_idx = EARTHLY_BRANCHES.index(branch)
    for c in range(1, 61):
        if (c - 1) % 10 == s_idx and (c - 1) % 12 == b_idx:
            return c
    raise ValueError(f"Invalid stem-branch pair: {stem}{branch}")


def build_chart(
    year_cycle: int,
    month_cycle: int,
    day_cycle: int,
    hour_cycle: int,
    gender: str,
) -> Dict:
    """Build a structured natal chart from four sexagenary cycle numbers."""
    gender = normalize_gender(gender)

    pillar_cycles = {
        "year": year_cycle, "month": month_cycle,
        "day": day_cycle, "hour": hour_cycle,
    }
    pillars = {name: ganzhi_from_cycle(c) for name, c in pillar_cycles.items()}

    dm_stem = pillars["day"][0]
    dm_elem = STEM_ELEMENT[dm_stem]

    chart: Dict = {
        "pillars": {},
        "day_master": {"stem": dm_stem, "element": dm_elem},
        "gender": gender,
    }

    for name, (stem, branch) in pillars.items():
        pillar_data: Dict = {
            "stem": stem,
            "branch": branch,
            "hidden": branch_hidden_with_roles(EARTHLY_BRANCHES.index(branch)),
            "ten_god": ten_god(
                HEAVENLY_STEMS.index(dm_stem), HEAVENLY_STEMS.index(stem)
            ),
        }
        p_cycle = pillar_cycles[name]
        ny = nayin_for_cycle(p_cycle)
        if ny:
            pillar_data["nayin"] = {
                "element": _nayin_pure_element(ny["nayin_element"]),
                "chinese": ny["nayin_chinese"],
                "vietnamese": ny["nayin_vietnamese"],
                "english": ny["nayin_english"],
            }
        chart["pillars"][name] = pillar_data

    return chart


def from_lunisolar_dto(dto: LunisolarDateDTO, gender: str) -> Dict:
    """Build a Bazi chart from a :class:`LunisolarDateDTO`."""
    gender = normalize_gender(gender)
    return build_chart(
        dto.year_cycle, dto.month_cycle,
        dto.day_cycle, dto.hour_cycle, gender,
    )


def from_solar_date(
    solar_date: str,
    solar_time: str = "12:00",
    gender: str = "male",
    timezone_name: str = "Asia/Shanghai",
) -> Dict:
    """Build a Bazi chart from a Gregorian date using the lunisolar engine."""
    gender = normalize_gender(gender)
    dto = solar_to_lunisolar(solar_date, solar_time, timezone_name, quiet=True)
    return from_lunisolar_dto(dto, gender)

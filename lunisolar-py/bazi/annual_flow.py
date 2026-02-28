"""
Annual Flow Engine (流年) — spec §6
====================================
"""

from typing import Dict, List

from .constants import (
    HEAVENLY_STEMS, STEM_ELEMENT, GEN_MAP, CONTROL_MAP,
    LIU_CHONG, LIU_HE, LIU_HAI,
)
from .core import ganzhi_from_cycle
from .ten_gods import ten_god


def annual_analysis(chart: Dict, year_pillar_cycle: int) -> Dict:
    """Analyse a flowing-year pillar against the natal chart."""
    year_stem, year_branch = ganzhi_from_cycle(year_pillar_cycle)
    dm = chart["day_master"]["stem"]
    dm_elem = STEM_ELEMENT[dm]
    natal_branches = [p["branch"] for p in chart["pillars"].values()]

    result: Dict = {}
    result["year_ten_god"] = ten_god(
        HEAVENLY_STEMS.index(dm), HEAVENLY_STEMS.index(year_stem)
    )

    interactions: List[str] = []
    for b in natal_branches:
        pair = frozenset({b, year_branch})
        if pair in LIU_CHONG:
            interactions.append("冲")
        if pair in LIU_HE:
            interactions.append("合")
        if pair in LIU_HAI:
            interactions.append("害")
    result["interactions"] = interactions

    yr_elem = STEM_ELEMENT[year_stem]
    delta = 0
    if GEN_MAP[yr_elem] == dm_elem:
        delta += 1
    if CONTROL_MAP[yr_elem] == dm_elem:
        delta -= 1
    result["strength_delta"] = delta

    return result

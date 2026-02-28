"""
Twelve Longevity Stages (十二长生) — spec §3
=============================================
"""

from typing import Dict, Tuple

from .constants import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES, STEM_POLARITY,
    LONGEVITY_STAGES, LONGEVITY_START,
    LONGEVITY_STAGES_EN, LONGEVITY_STAGES_VI,
)


def changsheng_stage(stem_idx: int, branch_idx: int) -> Tuple[int, str]:
    """Return (1-based stage index, stage name) for the stem at branch."""
    stem = HEAVENLY_STEMS[stem_idx]
    start = LONGEVITY_START[stem]
    i_start = EARTHLY_BRANCHES.index(start)

    if STEM_POLARITY[stem] == "Yang":
        offset = (branch_idx - i_start) % 12
    else:
        offset = (i_start - branch_idx) % 12

    idx = offset + 1
    return idx, LONGEVITY_STAGES[idx - 1]


def longevity_map(chart: Dict) -> Dict[str, Tuple[int, str]]:
    """Map the Day Master's 12 Longevity Stage across all four natal pillars."""
    dm_idx = HEAVENLY_STEMS.index(chart["day_master"]["stem"])
    result: Dict[str, Tuple[int, str]] = {}
    for name, p in chart["pillars"].items():
        b_idx = EARTHLY_BRANCHES.index(p["branch"])
        result[name] = changsheng_stage(dm_idx, b_idx)
    return result


def life_stage_detail(stem_idx: int, branch_idx: int) -> Dict:
    """Return full life-stage detail (Chinese, English, Vietnamese, strength)."""
    idx, cn_name = changsheng_stage(stem_idx, branch_idx)
    return {
        "index": idx,
        "chinese": cn_name,
        "english": LONGEVITY_STAGES_EN[idx - 1],
        "vietnamese": LONGEVITY_STAGES_VI[idx - 1],
        "strength_class": "strong" if idx <= 5 else "weak",
    }


def life_stages_for_chart(chart: Dict) -> Dict[str, Dict]:
    """Return the Day Master's life stage at each natal pillar."""
    dm_idx = HEAVENLY_STEMS.index(chart["day_master"]["stem"])
    result: Dict[str, Dict] = {}
    for pname, p in chart["pillars"].items():
        b_idx = EARTHLY_BRANCHES.index(p["branch"])
        result[pname] = life_stage_detail(dm_idx, b_idx)
    return result


def life_stage_for_luck_pillar(chart: Dict, luck_pillar: Dict) -> Dict:
    """Return the Day Master's life stage at a luck pillar."""
    dm_idx = HEAVENLY_STEMS.index(chart["day_master"]["stem"])
    b_idx = EARTHLY_BRANCHES.index(luck_pillar["branch"])
    return life_stage_detail(dm_idx, b_idx)

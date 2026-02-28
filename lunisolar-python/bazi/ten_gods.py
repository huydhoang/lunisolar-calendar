"""
Ten Gods (十神) — spec §1
=========================
"""

from typing import Dict

from .constants import (
    HEAVENLY_STEMS, STEM_ELEMENT, STEM_POLARITY, GEN_MAP, CONTROL_MAP,
)


def _element_relation(dm_elem: str, other_elem: str) -> str:
    """Classify the Five-Element relationship of *other_elem* to *dm_elem*."""
    if other_elem == dm_elem:
        return "same"
    if GEN_MAP[other_elem] == dm_elem:
        return "sheng"
    if GEN_MAP[dm_elem] == other_elem:
        return "wo_sheng"
    if CONTROL_MAP[dm_elem] == other_elem:
        return "wo_ke"
    if CONTROL_MAP[other_elem] == dm_elem:
        return "ke"
    raise ValueError(f"Unexpected element pair: {dm_elem}, {other_elem}")


def ten_god(dm_stem_idx: int, target_stem_idx: int) -> str:
    """Return the Ten-God name of the stem at *target_stem_idx* relative to Day Master."""
    dm_stem = HEAVENLY_STEMS[dm_stem_idx]
    target_stem = HEAVENLY_STEMS[target_stem_idx]
    dm_elem = STEM_ELEMENT[dm_stem]
    t_elem = STEM_ELEMENT[target_stem]
    rel = _element_relation(dm_elem, t_elem)
    same_polarity = STEM_POLARITY[dm_stem] == STEM_POLARITY[target_stem]

    mapping = {
        "same": ("比肩", "劫财"),
        "sheng": ("偏印", "正印"),
        "wo_sheng": ("食神", "伤官"),
        "wo_ke": ("偏财", "正财"),
        "ke": ("七杀", "正官"),
    }
    same_pol_name, diff_pol_name = mapping[rel]
    return same_pol_name if same_polarity else diff_pol_name


def weighted_ten_god_distribution(chart: Dict) -> Dict[str, float]:
    """Weighted Ten-God distribution (month pillar stem weighs most)."""
    dm = chart["day_master"]["stem"]
    dist: Dict[str, float] = {}
    weight_map = {"month": 3}

    for pname, p in chart["pillars"].items():
        w_stem = weight_map.get(pname, 2)
        tg = ten_god(HEAVENLY_STEMS.index(dm), HEAVENLY_STEMS.index(p["stem"]))
        dist[tg] = dist.get(tg, 0) + w_stem

        for role, stem in p["hidden"]:
            tg_h = ten_god(HEAVENLY_STEMS.index(dm), HEAVENLY_STEMS.index(stem))
            w_hidden = {"main": 2, "middle": 1}.get(role, 0.5)
            dist[tg_h] = dist.get(tg_h, 0) + w_hidden

    return dist

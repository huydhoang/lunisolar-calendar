"""
Na Yin (納音) System
====================
"""

import csv
import os
from typing import Dict, List, Optional

from .constants import HEAVENLY_STEMS, EARTHLY_BRANCHES, STEM_ELEMENT
from .ten_gods import _element_relation

_NAYIN_CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "nayin.csv")
_NAYIN_DATA: Dict[int, Dict] = {}


def _load_nayin() -> Dict[int, Dict]:
    """Load Na Yin data from ``nayin.csv`` (cached after first call)."""
    global _NAYIN_DATA
    if _NAYIN_DATA:
        return _NAYIN_DATA
    with open(_NAYIN_CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            idx = int(row["cycle_index"])
            _NAYIN_DATA[idx] = {
                "cycle_index": idx,
                "chinese": row["chinese"],
                "pinyin": row["pinyin"],
                "vietnamese": row["vietnamese"],
                "nayin_element": row["nayin_element"],
                "nayin_chinese": row["nayin_chinese"],
                "nayin_vietnamese": row["nayin_vietnamese"],
                "nayin_english": row["nayin_english"],
                "nayin_song": row["nayin_song"],
                "stem_polarity": row["stem_polarity"],
                "stem_element": row["stem_element"],
                "branch_polarity": row["branch_polarity"],
                "branch_element": row["branch_element"],
                "stem_life_stage": row["stem_life_stage"],
            }
    return _NAYIN_DATA


def nayin_for_cycle(cycle: int) -> Optional[Dict]:
    """Return Na Yin data dict for the given 1-60 sexagenary cycle number."""
    if not (1 <= cycle <= 60):
        return None
    data = _load_nayin()
    return data.get(cycle)


def _nayin_pure_element(nayin_element_str: str) -> str:
    """Extract pure element name from nayin_element field like 'Metal (金)'."""
    return (
        nayin_element_str.split("(")[0].strip()
        if "(" in nayin_element_str
        else nayin_element_str.strip()
    )


def nayin_for_pillar(pillar: Dict) -> Optional[Dict]:
    """Return Na Yin data for a pillar dict with ``'stem'`` and ``'branch'`` keys."""
    from .core import _cycle_from_stem_branch
    cycle = _cycle_from_stem_branch(pillar["stem"], pillar["branch"])
    return nayin_for_cycle(cycle)


def analyze_nayin_interactions(chart: Dict) -> Dict:
    """Analyze Na Yin element interactions between pillars and with Day Master."""
    dm_elem = chart["day_master"]["element"]
    pillar_order = ["year", "month", "day", "hour"]
    pillar_nayins: Dict[str, Dict] = {}

    for pname in pillar_order:
        p = chart["pillars"][pname]
        ny = nayin_for_pillar(p)
        if ny:
            pillar_nayins[pname] = {
                "nayin_element": _nayin_pure_element(ny["nayin_element"]),
                "nayin_chinese": ny["nayin_chinese"],
                "nayin_vietnamese": ny["nayin_vietnamese"],
                "nayin_english": ny["nayin_english"],
            }

    # Flow interactions: Year→Month→Day→Hour
    flow: List[Dict] = []
    for i in range(len(pillar_order) - 1):
        p1_name, p2_name = pillar_order[i], pillar_order[i + 1]
        if p1_name in pillar_nayins and p2_name in pillar_nayins:
            e1 = pillar_nayins[p1_name]["nayin_element"]
            e2 = pillar_nayins[p2_name]["nayin_element"]
            rel = _element_relation(e1, e2)
            flow.append({
                "from": p1_name, "to": p2_name,
                "from_element": e1, "to_element": e2,
                "relation": rel,
            })

    # Relation to Day Master
    vs_dm: Dict[str, Dict] = {}
    for pname, ny_data in pillar_nayins.items():
        ny_elem = ny_data["nayin_element"]
        rel = _element_relation(dm_elem, ny_elem)
        vs_dm[pname] = {
            "nayin_element": ny_elem,
            "relation_to_dm": rel,
            "nayin_name": ny_data["nayin_chinese"],
        }

    return {
        "pillar_nayins": pillar_nayins,
        "flow": flow,
        "vs_day_master": vs_dm,
    }

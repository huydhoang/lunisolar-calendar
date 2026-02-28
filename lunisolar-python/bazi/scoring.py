"""
Day-Master Scoring, Chart Rating & Useful God (用神)
====================================================
"""

from typing import Dict, List, Tuple, Union

from .constants import (
    HEAVENLY_STEMS, STEM_ELEMENT, BRANCH_ELEMENT,
    GEN_MAP, CONTROL_MAP, PILLAR_WEIGHTS, LU_MAP,
)
from .branch_interactions import detect_branch_interactions
from .structure import classify_structure


def is_jian_lu(dm_stem: str, month_branch: str) -> bool:
    """Strictly check ONLY the month branch."""
    return LU_MAP.get(dm_stem) == month_branch


def get_seasonal_strength(dm_elem: str, month_elem: str) -> int:
    """Calculate seasonal strength (Vượng Tướng Hưu Tù Tử)."""
    if month_elem == dm_elem:
        return 2
    if GEN_MAP.get(month_elem) == dm_elem:
        return 2
    if GEN_MAP.get(dm_elem) == month_elem:
        return -1
    if CONTROL_MAP.get(dm_elem) == month_elem:
        return -1
    if CONTROL_MAP.get(month_elem) == dm_elem:
        return -2
    return 0


def score_day_master(chart: Dict) -> Tuple[float, str]:
    """Score the Day Master's strength and classify as strong/weak/balanced."""
    dm_stem = chart["day_master"]["stem"]
    dm_elem = chart["day_master"]["element"]
    month_branch = chart["pillars"]["month"]["branch"]
    month_elem = BRANCH_ELEMENT[month_branch]

    score = 0.0
    month_weight = PILLAR_WEIGHTS["month"]

    # 1) Month-order via Five Seasons
    season_score = get_seasonal_strength(dm_elem, month_elem)
    score += season_score * month_weight

    # 2) Root depth (hidden stems matching DM element)
    for pname, p in chart["pillars"].items():
        w = PILLAR_WEIGHTS.get(pname, 1.0)
        for role, stem in p["hidden"]:
            if STEM_ELEMENT[stem] == dm_elem:
                if role == "main":
                    score += 2 * w
                elif role == "middle":
                    score += 1 * w
                elif role == "residual":
                    score += 0.5 * w

    # 3) Visible stem support
    for pname, p in chart["pillars"].items():
        w = PILLAR_WEIGHTS.get(pname, 1.0)
        if STEM_ELEMENT[p["stem"]] == dm_elem:
            score += 1 * w

    if score >= 6:
        strength = "strong"
    elif score <= -3:
        strength = "weak"
    else:
        strength = "balanced"

    return score, strength


def rate_chart(chart: Dict) -> int:
    """Quantitative 100-point chart rating."""
    total = 0

    # 1. Strength balance (max 30)
    _score, strength = score_day_master(chart)
    if strength == "balanced":
        total += 30
    elif strength == "strong":
        total += 22
    else:
        total += 18

    # 2. Structure purity (max 25)
    struct_dict = classify_structure(chart, strength)
    s_score = struct_dict.get("dominance_score", 0)
    if s_score > 8:
        total += 25
    elif s_score > 5:
        total += 18
    else:
        total += 10

    # 3. Element spread (max 20)
    elem_counts: Dict[str, int] = {}
    for p in chart["pillars"].values():
        e = STEM_ELEMENT[p["stem"]]
        elem_counts[e] = elem_counts.get(e, 0) + 1
        for _role, stem in p["hidden"]:
            e = STEM_ELEMENT[stem]
            elem_counts[e] = elem_counts.get(e, 0) + 1
    total += min(len(elem_counts) * 4, 20)

    # 4. Root depth (max 15)
    root = 0
    dm_elem = chart["day_master"]["element"]
    for p in chart["pillars"].values():
        for role, stem in p["hidden"]:
            if STEM_ELEMENT[stem] == dm_elem:
                if role == "main":
                    root += 5
                elif role == "middle":
                    root += 3
    total += min(root, 15)

    # 5. Interaction stability (max 10)
    interactions = detect_branch_interactions(chart)
    total += 4 if interactions["六冲"] else 10

    return total


def recommend_useful_god(
    chart: Dict, strength: str, structure: Dict = None
) -> Dict[str, Union[List[str], str]]:
    """Recommend favorable/unfavorable elements based on DM strength and structure."""
    dm_elem = chart["day_master"]["element"]
    inverse_gen = {v: k for k, v in GEN_MAP.items()}

    is_hurt_officer = structure and structure.get("primary") == "伤官格"

    if is_hurt_officer:
        return {
            "favorable": ["Wood"],
            "avoid": ["Fire"],
            "structure": "伤官格",
            "useful_god": "Wood (Mộc) - to control Earth",
            "joyful_god": "Fire (Hỏa) - to support Day Master",
        }

    if strength == "strong":
        return {
            "favorable": [GEN_MAP[dm_elem], CONTROL_MAP[dm_elem]],
            "avoid": [dm_elem],
        }
    if strength == "weak":
        return {
            "favorable": [inverse_gen[dm_elem], dm_elem],
            "avoid": [CONTROL_MAP[dm_elem]],
        }
    return {
        "favorable": [GEN_MAP[dm_elem], inverse_gen[dm_elem]],
        "avoid": [],
    }

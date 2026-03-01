"""
Day-Master Scoring, Chart Rating & Useful God (用神)
====================================================
"""

from typing import Dict, List, Optional, Tuple, Union

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


def score_day_master(
    chart: Dict,
    interactions: Optional[Dict] = None,
    rooting: Optional[Dict] = None,
) -> Tuple[float, str]:
    """Score the Day Master's strength and classify.

    Classifications: extreme_strong / strong / balanced / weak / extreme_weak.
    Optionally integrates interaction and rooting data for more accurate scoring.
    """
    dm_stem = chart["day_master"]["stem"]
    dm_elem = chart["day_master"]["element"]
    inverse_gen = {v: k for k, v in GEN_MAP.items()}
    resource_elem = inverse_gen[dm_elem]
    month_branch = chart["pillars"]["month"]["branch"]
    month_elem = BRANCH_ELEMENT[month_branch]

    score = 0.0
    month_weight = PILLAR_WEIGHTS["month"]

    # 1) Month-order via Five Seasons
    season_score = get_seasonal_strength(dm_elem, month_elem)
    score += season_score * month_weight

    # 2) Root depth (hidden stems matching DM element)
    if rooting:
        # Use pre-computed rooting strength
        score += rooting.get("total_strength", 0)
    else:
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

    # 2b) Resource element support (印星 — element that generates DM)
    for pname, p in chart["pillars"].items():
        w = PILLAR_WEIGHTS.get(pname, 1.0)
        for role, stem in p["hidden"]:
            if STEM_ELEMENT[stem] == resource_elem:
                if role == "main":
                    score += 1.2 * w
                elif role == "middle":
                    score += 0.6 * w
                elif role == "residual":
                    score += 0.3 * w

    # 3) Visible stem support (peers + resource)
    for pname, p in chart["pillars"].items():
        w = PILLAR_WEIGHTS.get(pname, 1.0)
        s_elem = STEM_ELEMENT[p["stem"]]
        if s_elem == dm_elem:
            score += 1 * w
        elif s_elem == resource_elem:
            score += 0.6 * w

    # 4) Interaction adjustments (if provided)
    if interactions:
        # 三合/三会 frame matching DM element → boost
        for entry in interactions.get("三合", []):
            target = entry.get("target_element") if isinstance(entry, dict) else None
            if target == dm_elem:
                score += 3.0
            elif target and GEN_MAP.get(target) == dm_elem:
                score += 1.5

        for entry in interactions.get("三会", []):
            from .constants import SAN_HUI_ELEMENT
            if isinstance(entry, frozenset):
                target = SAN_HUI_ELEMENT.get(entry)
                if target == dm_elem:
                    score += 3.0
                elif target == resource_elem:
                    score += 1.5

        # 六冲 on month branch → weakens seasonal support
        for clash in interactions.get("六冲", []):
            if isinstance(clash, tuple) and month_branch in clash:
                score -= 2.0

    # Classify with five tiers
    if score >= 10:
        strength = "extreme_strong"
    elif score >= 6:
        strength = "strong"
    elif score <= -6:
        strength = "extreme_weak"
    elif score <= -3:
        strength = "weak"
    else:
        strength = "balanced"

    return score, strength


def rate_chart(chart: Dict) -> int:
    """Quantitative 100-point chart rating."""
    total = 0

    # 1. Strength balance (max 30, 5 tiers)
    _score, strength = score_day_master(chart)
    strength_points = {
        "balanced": 30,
        "strong": 22,
        "weak": 18,
        "extreme_strong": 12,
        "extreme_weak": 10,
    }
    total += strength_points.get(strength, 15)

    # 2. Structure purity (max 25)
    struct_dict = classify_structure(chart, strength)
    s_score = struct_dict.get("dominance_score", 0)
    is_broken = struct_dict.get("is_broken", False)
    composite = struct_dict.get("composite")

    if is_broken:
        total += 5
    elif s_score > 8:
        total += 25
    elif s_score > 5:
        total += 18
    else:
        total += 10
    if composite and not is_broken:
        total += 3  # Composite structure bonus (capped by max)

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
    stability = 10
    if interactions.get("六冲"):
        stability -= 3 * len(interactions["六冲"])
    if interactions.get("刑"):
        stability -= 2
    if interactions.get("害"):
        stability -= 1
    if interactions.get("六破"):
        stability -= 1
    # Combinations are positive
    if interactions.get("六合"):
        stability += 1
    if interactions.get("三合"):
        stability += 2
    total += max(0, min(stability, 10))

    return min(total, 100)


def _assess_chart_temperature(
    chart: Dict, interactions: Optional[Dict] = None,
) -> str:
    """Assess chart temperature (Điều Hầu): 'hot', 'cold', or 'neutral'.

    Examines elemental composition and branch frames to determine whether
    the chart is overheated (Fire/Wood dominant) or overcooled (Water/Metal).
    """
    hot_score = 0.0
    cold_score = 0.0
    role_weights = {"main": 1.0, "middle": 0.6, "residual": 0.3}

    for p in chart.get("pillars", {}).values():
        s_elem = STEM_ELEMENT.get(p.get("stem", ""), "")
        if s_elem in ("Fire", "Wood"):
            hot_score += 1
        elif s_elem in ("Water", "Metal"):
            cold_score += 1
        for role, stem in p.get("hidden", []):
            h_elem = STEM_ELEMENT.get(stem, "")
            w = role_weights.get(role, 0.3)
            if h_elem in ("Fire", "Wood"):
                hot_score += w
            elif h_elem in ("Water", "Metal"):
                cold_score += w

    if interactions:
        from .constants import SAN_HUI_ELEMENT as _SHE
        for entry in interactions.get("三会", []):
            if isinstance(entry, frozenset):
                target = _SHE.get(entry)
                if target == "Fire":
                    hot_score += 3
                elif target == "Water":
                    cold_score += 3
        for entry in interactions.get("三合", []):
            target = entry.get("target_element") if isinstance(entry, dict) else None
            if target == "Fire":
                hot_score += 2
            elif target == "Water":
                cold_score += 2

    if hot_score >= cold_score + 3:
        return "hot"
    elif cold_score >= hot_score + 3:
        return "cold"
    return "neutral"


def recommend_useful_god(
    chart: Dict, strength: str, structure: Dict = None,
    interactions: Optional[Dict] = None,
) -> Dict[str, Union[List[str], str]]:
    """Structure-aware Useful God recommendation with temperature balancing."""
    dm_elem = chart["day_master"]["element"]
    inverse_gen = {v: k for k, v in GEN_MAP.items()}

    # Special structure handling
    if structure:
        primary = structure.get("primary", "")
        category = structure.get("category", "")

        # Follow structures → favor the dominant element category
        if category == "从格":
            if "从财" in primary:
                wealth_elem = CONTROL_MAP[dm_elem]
                return {
                    "favorable": [wealth_elem, GEN_MAP[dm_elem]],
                    "avoid": [dm_elem, inverse_gen[dm_elem]],
                    "structure": primary,
                    "useful_god": f"{wealth_elem} — follow wealth",
                }
            elif "从官" in primary:
                officer_elem = CONTROL_MAP.get(
                    {v: k for k, v in CONTROL_MAP.items()}.get(dm_elem, ""), ""
                )
                controlling_elem = [e for e, t in CONTROL_MAP.items() if t == dm_elem]
                ctrl = controlling_elem[0] if controlling_elem else ""
                return {
                    "favorable": [ctrl, GEN_MAP.get(ctrl, "")],
                    "avoid": [dm_elem],
                    "structure": primary,
                    "useful_god": f"{ctrl} — follow officer/killings",
                }

        # Transform structures → favor the transformed element
        if category == "化格":
            target = structure.get("target_element", "")
            if target:
                return {
                    "favorable": [target, inverse_gen.get(target, "")],
                    "avoid": [CONTROL_MAP.get(target, "")],
                    "structure": primary,
                    "useful_god": f"{target} — transformation god",
                }

        # 伤官格 special handling
        if primary == "伤官格":
            return {
                "favorable": ["Wood"],
                "avoid": ["Fire"],
                "structure": "伤官格",
                "useful_god": "Wood (Mộc) - to control Earth",
                "joyful_god": "Fire (Hỏa) - to support Day Master",
            }

    # Derive the five relational elements
    officer_elem = [e for e, t in CONTROL_MAP.items() if t == dm_elem]
    officer = officer_elem[0] if officer_elem else ""
    resource = inverse_gen.get(dm_elem, "")
    output = GEN_MAP.get(dm_elem, "")
    wealth = CONTROL_MAP.get(dm_elem, "")

    # Default strength-based recommendations
    if strength in ("strong", "extreme_strong"):
        # Strong DM: restrain with Officer, exhaust with Output/Wealth; avoid Peers + Resource
        return {
            "favorable": [officer, output, wealth],
            "avoid": [dm_elem, resource],
            "useful_god": f"{officer} — restrain strong DM",
            "joyful_god": f"{output} — exhaust DM energy",
        }
    if strength in ("weak", "extreme_weak"):
        # Weak DM: support with Resource + Peers; avoid Officer (primary threat) + Wealth
        return {
            "favorable": [resource, dm_elem],
            "avoid": [officer, wealth],
            "useful_god": f"{resource} — support weak DM",
            "joyful_god": f"{dm_elem} — peer support",
        }
    # Balanced: assess chart temperature (Điều Hầu) for proper recommendation
    temperature = _assess_chart_temperature(chart, interactions)

    if temperature == "hot":
        return {
            "favorable": [officer, output],
            "avoid": [resource, dm_elem],
            "useful_god": f"{officer} — cool overheated chart",
            "joyful_god": f"{output} — vent excess energy",
        }
    elif temperature == "cold":
        return {
            "favorable": [resource, dm_elem],
            "avoid": [officer, wealth],
            "useful_god": f"{resource} — warm cold chart",
            "joyful_god": f"{dm_elem} — peer support for warmth",
        }
    # Neutral balanced: favor moderate drainage + support
    return {
        "favorable": [output, resource],
        "avoid": [],
        "useful_god": f"{output} — maintain balance via output",
        "joyful_god": f"{resource} — gentle support",
    }

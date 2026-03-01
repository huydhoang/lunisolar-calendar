"""
Rooting & Tomb/Treasury Analysis (通根 & 墓库)
===============================================

Provides structured rooting depth analysis for every Heavenly Stem in a chart,
focused DM rooting, and Tomb/Treasury mechanics for the four 墓库 branches.
"""

from typing import Dict, List

from .constants import (
    STEM_ELEMENT, BRANCH_ELEMENT, BRANCH_HIDDEN_STEMS, HIDDEN_ROLES,
    ELEMENT_TO_TOMB, TOMB_BRANCHES, LU_MAP, PILLAR_WEIGHTS,
    LIU_CHONG, GOAT_BLADE_TABLE,
)


# Weights for root quality: main qi > middle qi > residual qi
ROOT_WEIGHTS = {"main": 1.0, "middle": 0.6, "residual": 0.3}


def analyze_stem_roots(chart: Dict) -> Dict[str, Dict]:
    """Analyze rooting depth of every Heavenly Stem in the chart.

    Returns a dict keyed by pillar name → rooting info for that pillar's stem.
    Each entry contains:
    - roots: list of {branch, pillar, role, weight}
    - total_strength: sum of weighted root values
    - is_rooted: whether the stem has any root
    - classification: "strong_root" / "moderate_root" / "weak_root" / "unrooted"
    """
    result: Dict[str, Dict] = {}

    for pname, p in chart["pillars"].items():
        stem = p["stem"]
        stem_elem = STEM_ELEMENT[stem]
        roots: List[Dict] = []

        for bname, bp in chart["pillars"].items():
            branch = bp["branch"]
            hidden_list = BRANCH_HIDDEN_STEMS[branch]
            for i, hstem in enumerate(hidden_list):
                if STEM_ELEMENT[hstem] == stem_elem:
                    role = HIDDEN_ROLES[i] if i < len(HIDDEN_ROLES) else "residual"
                    same_stem = (hstem == stem)
                    weight = ROOT_WEIGHTS.get(role, 0.3)
                    # Exact stem match (same polarity) is a stronger root
                    if same_stem and role == "main":
                        weight = 1.0
                    roots.append({
                        "branch": branch,
                        "pillar": bname,
                        "hidden_stem": hstem,
                        "role": role,
                        "same_stem": same_stem,
                        "weight": weight * PILLAR_WEIGHTS.get(bname, 1.0),
                    })

        total = sum(r["weight"] for r in roots)
        is_rooted = len(roots) > 0

        if total >= 4.0:
            classification = "strong_root"
        elif total >= 2.0:
            classification = "moderate_root"
        elif total > 0:
            classification = "weak_root"
        else:
            classification = "unrooted"

        result[pname] = {
            "stem": stem,
            "element": stem_elem,
            "roots": roots,
            "total_strength": round(total, 2),
            "is_rooted": is_rooted,
            "classification": classification,
        }

    return result


def analyze_dm_rooting(chart: Dict) -> Dict:
    """Focused rooting analysis for the Day Master only.

    Returns:
    - roots, total_strength, is_rooted, classification (as above)
    - is_jian_lu: whether month branch is DM's 禄 (Lộc)
    - is_yang_ren: whether month branch is DM's 羊刃
    - main_qi_roots: count of main-qi roots
    - residual_roots: count of residual/middle-qi roots
    """
    dm_stem = chart["day_master"]["stem"]
    dm_elem = chart["day_master"]["element"]
    month_branch = chart["pillars"]["month"]["branch"]

    roots: List[Dict] = []
    main_qi_count = 0
    residual_count = 0

    for bname, bp in chart["pillars"].items():
        branch = bp["branch"]
        hidden_list = BRANCH_HIDDEN_STEMS[branch]
        for i, hstem in enumerate(hidden_list):
            if STEM_ELEMENT[hstem] == dm_elem:
                role = HIDDEN_ROLES[i] if i < len(HIDDEN_ROLES) else "residual"
                same_stem = (hstem == dm_stem)
                weight = ROOT_WEIGHTS.get(role, 0.3)
                if same_stem and role == "main":
                    weight = 1.0
                roots.append({
                    "branch": branch,
                    "pillar": bname,
                    "hidden_stem": hstem,
                    "role": role,
                    "same_stem": same_stem,
                    "weight": weight * PILLAR_WEIGHTS.get(bname, 1.0),
                })
                if role == "main":
                    main_qi_count += 1
                else:
                    residual_count += 1

    total = sum(r["weight"] for r in roots)
    is_rooted = len(roots) > 0

    if total >= 4.0:
        classification = "strong_root"
    elif total >= 2.0:
        classification = "moderate_root"
    elif total > 0:
        classification = "weak_root"
    else:
        classification = "unrooted"

    is_jian_lu = LU_MAP.get(dm_stem) == month_branch
    is_yang_ren = GOAT_BLADE_TABLE.get(dm_stem) == month_branch

    return {
        "stem": dm_stem,
        "element": dm_elem,
        "roots": roots,
        "total_strength": round(total, 2),
        "is_rooted": is_rooted,
        "classification": classification,
        "main_qi_roots": main_qi_count,
        "residual_roots": residual_count,
        "is_jian_lu": is_jian_lu,
        "is_yang_ren": is_yang_ren,
    }


def analyze_tomb_treasury(chart: Dict) -> List[Dict]:
    """Analyze Tomb/Treasury (墓库) relationships for all elements in the chart.

    For each Tomb/Treasury branch present (辰戌丑未), determines:
    - Which elements it entombs
    - Whether the tomb is opened (by 冲 from another natal branch)
    - Whether the DM enters tomb (入墓) — relevant for weak DMs
    """
    dm_elem = chart["day_master"]["element"]
    results: List[Dict] = []

    # Collect all natal branches
    natal_branches = {
        pname: p["branch"] for pname, p in chart["pillars"].items()
    }

    for pname, branch in natal_branches.items():
        if branch not in TOMB_BRANCHES:
            continue

        # Which elements does this tomb branch store?
        entombed_elements = [
            elem for elem, tomb in ELEMENT_TO_TOMB.items() if tomb == branch
        ]

        # Is the tomb opened by a clash?
        is_opened = False
        opened_by = None
        for other_name, other_branch in natal_branches.items():
            if other_name == pname:
                continue
            if frozenset({branch, other_branch}) in LIU_CHONG:
                is_opened = True
                opened_by = f"冲 ({other_branch} from {other_name})"
                break

        # Does the DM enter this tomb?
        dm_enters = (
            ELEMENT_TO_TOMB.get(dm_elem) == branch
            and not is_opened
        )

        results.append({
            "pillar": pname,
            "branch": branch,
            "entombed_elements": entombed_elements,
            "is_opened": is_opened,
            "opened_by": opened_by,
            "dm_enters_tomb": dm_enters,
        })

    return results

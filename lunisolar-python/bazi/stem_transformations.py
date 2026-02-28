"""
Stem Combination & Transformation Detection (天干合化)
=====================================================
"""

from typing import Dict, List

from .constants import (
    HEAVENLY_STEMS, STEM_ELEMENT, STEM_POLARITY,
    CONTROL_MAP, GEN_MAP, BRANCH_ELEMENT,
    STEM_TRANSFORMATIONS, ADJACENT_PAIRS,
)


def check_obstruction(chart: Dict, p1: str, p2: str) -> bool:
    """Check if a third stem between *p1* and *p2* obstructs their combination."""
    order = ["year", "month", "day", "hour"]
    i1, i2 = order.index(p1), order.index(p2)
    lo, hi = min(i1, i2), max(i1, i2)
    if hi - lo <= 1:
        return False
    s1 = chart["pillars"][p1]["stem"]
    s2 = chart["pillars"][p2]["stem"]
    e1, e2 = STEM_ELEMENT[s1], STEM_ELEMENT[s2]
    for mid_idx in range(lo + 1, hi):
        mid_pillar = order[mid_idx]
        mid_stem = chart["pillars"][mid_pillar]["stem"]
        mid_elem = STEM_ELEMENT[mid_stem]
        if CONTROL_MAP.get(mid_elem) in (e1, e2):
            return True
    return False


def check_severe_clash(chart: Dict, target_element: str) -> bool:
    """Return True if *target_element* is severely clashed by natal pillars."""
    dm_pol = STEM_POLARITY[chart["day_master"]["stem"]]
    for pname, p in chart["pillars"].items():
        elem = STEM_ELEMENT[p["stem"]]
        if CONTROL_MAP.get(elem) == target_element:
            if pname == "month" or STEM_POLARITY[p["stem"]] != dm_pol:
                return True
    return False


def detect_stem_combinations(chart: Dict) -> List[Dict]:
    """Detect Heavenly Stem Combination pairs (天干合) in the natal chart."""
    results: List[Dict] = []
    pillar_names = ["year", "month", "day", "hour"]
    for i, p1 in enumerate(pillar_names):
        for j in range(i + 1, len(pillar_names)):
            p2 = pillar_names[j]
            s1 = chart["pillars"][p1]["stem"]
            s2 = chart["pillars"][p2]["stem"]
            pair_key = frozenset([s1, s2])
            if pair_key in STEM_TRANSFORMATIONS:
                results.append({
                    "pair": (p1, p2),
                    "stems": (s1, s2),
                    "target_element": STEM_TRANSFORMATIONS[pair_key],
                })
    return results


def detect_transformations(chart: Dict) -> List[Dict]:
    """Detect stem transformations (合化) with full condition checking."""
    results: List[Dict] = []
    month_branch = chart["pillars"]["month"]["branch"]
    month_elem = BRANCH_ELEMENT[month_branch]
    pillar_names = ["year", "month", "day", "hour"]
    adjacent_set = {(a, b) for a, b in ADJACENT_PAIRS}

    for i, p1 in enumerate(pillar_names):
        for j in range(i + 1, len(pillar_names)):
            p2 = pillar_names[j]
            s1 = chart["pillars"][p1]["stem"]
            s2 = chart["pillars"][p2]["stem"]
            pair_key = frozenset([s1, s2])
            if pair_key not in STEM_TRANSFORMATIONS:
                continue
            target = STEM_TRANSFORMATIONS[pair_key]

            is_adjacent = (p1, p2) in adjacent_set or (p2, p1) in adjacent_set
            proximity_score = 2 if is_adjacent else 1

            blocked = check_obstruction(chart, p1, p2)

            month_support = (month_elem == target)

            other_pillars = [k for k in pillar_names if k not in (p1, p2)]
            leading = False
            for k in other_pillars:
                if STEM_ELEMENT.get(chart["pillars"][k]["stem"]) == target:
                    leading = True
                    break
            if not leading:
                for p in chart["pillars"].values():
                    for _role, hstem in p["hidden"]:
                        if STEM_ELEMENT.get(hstem) == target:
                            leading = True
                            break
                    if leading:
                        break

            severely_clashed = check_severe_clash(chart, target)

            if (
                proximity_score == 2
                and month_support
                and (leading or not severely_clashed)
                and not blocked
            ):
                status = "Hóa (successful)"
                confidence = 95 if leading else 85
            elif proximity_score >= 1 and (month_support or leading) and not blocked:
                status = "Hợp (bound)"
                confidence = 65
            elif blocked:
                status = "Blocked"
                confidence = 10
            else:
                status = "Hợp (bound)"
                confidence = 40

            if status == "Hóa (successful)" and severely_clashed:
                status = "Hóa (suppressed by clash)"
                confidence = max(confidence - 30, 20)

            results.append({
                "pair": (p1, p2),
                "stems": (s1, s2),
                "target_element": target,
                "month_support": month_support,
                "leading_present": leading,
                "blocked": blocked,
                "severely_clashed": severely_clashed,
                "proximity_score": proximity_score,
                "status": status,
                "confidence": confidence,
            })
    return results

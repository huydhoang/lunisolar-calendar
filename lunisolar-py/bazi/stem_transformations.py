"""
Stem Combination & Transformation Detection (天干合化)
=====================================================
"""

from typing import Dict, List

from .constants import (
    HEAVENLY_STEMS, STEM_ELEMENT, STEM_POLARITY,
    CONTROL_MAP, GEN_MAP, BRANCH_ELEMENT,
    STEM_TRANSFORMATIONS, ADJACENT_PAIRS,
    STEM_CLASH_PAIRS, STEM_RESTRAINT_PAIRS,
)
from .glossary import STEM_RESTRAIN_PAIR_TO_TERM, STEM_CLASH_PAIR_TO_TERM


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

    # Count stem occurrences for jealous combination detection (争合)
    _stem_counts: Dict[str, int] = {}
    for pn in pillar_names:
        s = chart["pillars"][pn]["stem"]
        _stem_counts[s] = _stem_counts.get(s, 0) + 1

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

            # Remote combination — affinity only, cannot transform
            if not is_adjacent:
                results.append({
                    "pair": (p1, p2),
                    "stems": (s1, s2),
                    "target_element": target,
                    "month_support": False,
                    "leading_present": False,
                    "blocked": False,
                    "severely_clashed": False,
                    "proximity_score": proximity_score,
                    "status": "遥合 (remote)",
                    "confidence": 30,
                })
                continue

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

            # Jealous combination penalty (争合): when either stem appears
            # in multiple pillars, the contest prevents transformation
            if _stem_counts.get(s1, 1) > 1 or _stem_counts.get(s2, 1) > 1:
                if status.startswith("Hóa"):
                    status = "Hợp (bound — jealous)"
                    confidence = min(confidence, 30)

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


def detect_jealous_combinations(chart: Dict) -> List[Dict]:
    """Detect Jealous Combinations (争合) where a stem has multiple potential partners.

    When the same stem value appears in multiple pillars competing to combine
    with a single partner, neither combination can transform successfully.
    """
    pillar_names = ["year", "month", "day", "hour"]
    results: List[Dict] = []

    # Map each stem value → list of pillar names containing it
    stem_positions: Dict[str, List[str]] = {}
    for pn in pillar_names:
        s = chart["pillars"][pn]["stem"]
        stem_positions.setdefault(s, []).append(pn)

    # For each valid combination pair, see if one side has multiple occurrences
    seen_pairs = set()
    for i, p1 in enumerate(pillar_names):
        for j in range(i + 1, len(pillar_names)):
            p2 = pillar_names[j]
            s1 = chart["pillars"][p1]["stem"]
            s2 = chart["pillars"][p2]["stem"]
            pair_key = frozenset([s1, s2])
            if pair_key not in STEM_TRANSFORMATIONS or pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            # Check if either stem has multiple pillar positions
            s1_count = len(stem_positions.get(s1, []))
            s2_count = len(stem_positions.get(s2, []))
            if s1_count > 1 or s2_count > 1:
                contested = s1 if s1_count > 1 else s2
                results.append({
                    "contested_stem": contested,
                    "partner_stem": s2 if contested == s1 else s1,
                    "contested_count": max(s1_count, s2_count),
                    "target_element": STEM_TRANSFORMATIONS[pair_key],
                    "note": "争合 — multiple stems contest; transformation weakened",
                })
    return results


def detect_stem_restraints(chart: Dict) -> List[Dict]:
    """Detect Heavenly Stem Restraints (天干相克) between natal pillars."""
    pillar_names = ["year", "month", "day", "hour"]
    adjacent_set = {(a, b) for a, b in ADJACENT_PAIRS} | {(b, a) for a, b in ADJACENT_PAIRS}
    results: List[Dict] = []

    for i, p1 in enumerate(pillar_names):
        for j in range(i + 1, len(pillar_names)):
            p2 = pillar_names[j]
            s1 = chart["pillars"][p1]["stem"]
            s2 = chart["pillars"][p2]["stem"]

            for attacker, target_pillar, a_stem, t_stem in [
                (p1, p2, s1, s2), (p2, p1, s2, s1)
            ]:
                pair_key = (a_stem, t_stem)
                if pair_key in STEM_RESTRAIN_PAIR_TO_TERM:
                    is_adjacent = (attacker, target_pillar) in adjacent_set
                    involves_day = "day" in (attacker, target_pillar)
                    involves_month = "month" in (attacker, target_pillar)
                    severity = 80 if (is_adjacent and involves_day) else (
                        70 if (is_adjacent and involves_month) else (
                            60 if is_adjacent else 40
                        )
                    )
                    results.append({
                        "attacker_pillar": attacker,
                        "target_pillar": target_pillar,
                        "attacker_stem": a_stem,
                        "target_stem": t_stem,
                        "attacker_element": STEM_ELEMENT[a_stem],
                        "target_element": STEM_ELEMENT[t_stem],
                        "is_adjacent": is_adjacent,
                        "severity": severity,
                    })
    return results


def detect_stem_clashes(chart: Dict) -> List[Dict]:
    """Detect the four Heavenly Stem Clashes (天干相冲): 甲庚, 乙辛, 丙壬, 丁癸."""
    pillar_names = ["year", "month", "day", "hour"]
    adjacent_set = {(a, b) for a, b in ADJACENT_PAIRS} | {(b, a) for a, b in ADJACENT_PAIRS}
    results: List[Dict] = []

    for i, p1 in enumerate(pillar_names):
        for j in range(i + 1, len(pillar_names)):
            p2 = pillar_names[j]
            s1 = chart["pillars"][p1]["stem"]
            s2 = chart["pillars"][p2]["stem"]
            pair_key = frozenset({s1, s2})
            if pair_key in STEM_CLASH_PAIRS:
                is_adjacent = (p1, p2) in adjacent_set
                term = STEM_CLASH_PAIR_TO_TERM.get(pair_key)
                results.append({
                    "pair": (p1, p2),
                    "stems": (s1, s2),
                    "is_adjacent": is_adjacent,
                    "term": term[0] if term else None,
                    "severity": 80 if is_adjacent else 50,
                })
    return results

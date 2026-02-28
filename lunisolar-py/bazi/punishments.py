"""
Punishments, Harms & Fu Yin Detection (刑害伏吟)
=================================================
"""

from typing import Dict, List

from .constants import (
    SELF_PUNISH_BRANCHES, UNCIVIL_PUNISH_PAIRS,
    GRACELESS_PUNISH_PAIRS, BULLY_PUNISH_PAIRS, HARM_PAIRS,
)


def detect_punishments(chart: Dict) -> List[Dict]:
    """Detect punishments (刑) and harms (害) with life-area tagging."""
    results: List[Dict] = []
    names = ["year", "month", "day", "hour"]
    branches = [chart["pillars"][k]["branch"] for k in names]

    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            bi, bj = branches[i], branches[j]
            pair = frozenset({bi, bj})

            involves_day = "day" in (names[i], names[j])
            involves_month = "month" in (names[i], names[j])
            severity = 80 if involves_day else (70 if involves_month else 50)

            if bi == bj and bi in SELF_PUNISH_BRANCHES:
                results.append({
                    "type": "Tự hình (Self-punish)",
                    "pair": (names[i], names[j]),
                    "branches": (bi, bj),
                    "severity": severity,
                    "life_areas": ["health", "self-sabotage"],
                })

            if pair in UNCIVIL_PUNISH_PAIRS:
                results.append({
                    "type": "Vô lễ chi hình (Uncivil)",
                    "pair": (names[i], names[j]),
                    "branches": (bi, bj),
                    "severity": severity,
                    "life_areas": ["relationship", "secrets"],
                })

            if pair in GRACELESS_PUNISH_PAIRS:
                results.append({
                    "type": "Vô ân chi hình (Graceless)",
                    "pair": (names[i], names[j]),
                    "branches": (bi, bj),
                    "severity": severity,
                    "life_areas": ["betrayal", "ingratitude"],
                })

            if pair in BULLY_PUNISH_PAIRS:
                results.append({
                    "type": "Ỷ thế chi hình (Bully)",
                    "pair": (names[i], names[j]),
                    "branches": (bi, bj),
                    "severity": severity,
                    "life_areas": ["career", "power struggles"],
                })

            if pair in HARM_PAIRS:
                results.append({
                    "type": "Hại (Harm)",
                    "pair": (names[i], names[j]),
                    "branches": (bi, bj),
                    "severity": severity,
                    "life_areas": ["health", "relationship"],
                })

    return results


def detect_fu_yin_duplication(chart: Dict, dynamic_pillar: Dict) -> List[Dict]:
    """Detect Fu Yin (伏吟) / Duplication between a dynamic pillar and natal chart."""
    results: List[Dict] = []
    dyn_stem = dynamic_pillar["stem"]
    dyn_branch = dynamic_pillar["branch"]

    for p_name, natal in chart["pillars"].items():
        if natal["stem"] == dyn_stem and natal["branch"] == dyn_branch:
            confidence = 95 if p_name == "month" else 90
            results.append({
                "type": "Phục Ngâm",
                "match": "exact",
                "natal_pillar": p_name,
                "dynamic_stem": dyn_stem,
                "dynamic_branch": dyn_branch,
                "confidence": confidence,
                "message": (
                    f"{p_name} pillar identical to dynamic pillar "
                    f"({dyn_stem}{dyn_branch}) — overload/stagnation risk."
                ),
            })
        elif natal["branch"] == dyn_branch:
            confidence = 70 if p_name == "month" else 60
            results.append({
                "type": "Phục Ngâm",
                "match": "branch",
                "natal_pillar": p_name,
                "dynamic_stem": dyn_stem,
                "dynamic_branch": dyn_branch,
                "confidence": confidence,
                "message": (
                    f"{p_name} branch equals dynamic branch ({dyn_branch}) "
                    f"— elemental overbalance."
                ),
            })
    return results

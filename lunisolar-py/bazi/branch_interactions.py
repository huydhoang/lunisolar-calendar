"""
Branch Interaction Detection — spec §8
=======================================
"""

from typing import Dict, List

from .constants import (
    ZI_XING_BRANCHES, BRANCH_HIDDEN_STEMS,
    LIU_HE, LIU_CHONG, LIU_HAI,
    SAN_HE, BAN_SAN_HE, SAN_HUI, XING,
)


def detect_self_punishment(
    chart: Dict,
    require_exposed_main: bool = False,
    require_adjacent: bool = False,
) -> List[Dict]:
    """Detect 自刑 (self-punishment) patterns among natal branches."""
    pillar_names = list(chart["pillars"].keys())
    branches = [chart["pillars"][n]["branch"] for n in pillar_names]
    positions: Dict[str, List[int]] = {}
    for idx, b in enumerate(branches):
        positions.setdefault(b, []).append(idx)

    results: List[Dict] = []
    for b, inds in positions.items():
        if b in ZI_XING_BRANCHES and len(inds) >= 2:
            adjacent_ok = True
            if require_adjacent:
                adjacent_ok = any(abs(i - j) == 1 for i in inds for j in inds if i != j)

            exposed_ok = True
            if require_exposed_main:
                main_hidden = BRANCH_HIDDEN_STEMS[b][0]
                exposed_ok = any(
                    chart["pillars"][pillar_names[i]]["stem"] == main_hidden
                    for i in inds
                )

            if adjacent_ok and exposed_ok:
                mode = "complete" if len(inds) >= 3 else "partial"
                results.append({
                    "branch": b,
                    "count": len(inds),
                    "positions": inds,
                    "mode": mode,
                    "notes": f"adjacent_ok={adjacent_ok}, exposed_ok={exposed_ok}",
                })
    return results


def detect_xing(chart: Dict, strict: bool = False) -> List[Dict]:
    """Detect 刑 (punishment) patterns among natal branches."""
    branches = [p["branch"] for p in chart["pillars"].values()]
    bset = set(branches)
    results: List[Dict] = []
    for trio in XING:
        found = len(trio & bset)
        if strict:
            if found == len(trio):
                results.append({"pattern": trio, "found": found, "mode": "complete"})
        else:
            if found >= 2:
                mode = "complete" if found == len(trio) else "partial"
                results.append({"pattern": trio, "found": found, "mode": mode})
    return results


def detect_branch_interactions(chart: Dict) -> Dict[str, list]:
    """Detect 六合, 六冲, 六害, 三合, 三会, 刑, and 自刑 among natal branches."""
    branches = [p["branch"] for p in chart["pillars"].values()]
    results: Dict[str, list] = {
        "六合": [], "六冲": [], "害": [],
        "三合": [], "半三合": [], "三会": [],
        "刑": [], "自刑": [],
    }

    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            pair = frozenset({branches[i], branches[j]})
            if pair in LIU_HE:
                results["六合"].append((branches[i], branches[j]))
            if pair in LIU_CHONG:
                results["六冲"].append((branches[i], branches[j]))
            if pair in LIU_HAI:
                results["害"].append((branches[i], branches[j]))

    bset = set(branches)
    for trio in SAN_HE:
        if trio.issubset(bset):
            results["三合"].append(trio)

    for pair in BAN_SAN_HE:
        if pair.issubset(bset):
            already_full = any(pair.issubset(trio) for trio in results["三合"])
            if not already_full:
                results["半三合"].append(pair)

    for trio in SAN_HUI:
        if trio.issubset(bset):
            results["三会"].append(trio)

    for entry in detect_xing(chart, strict=False):
        results["刑"].append(entry)

    for entry in detect_self_punishment(chart):
        results["自刑"].append(entry)

    return results

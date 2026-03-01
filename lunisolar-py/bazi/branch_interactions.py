"""
Branch Interaction Detection — spec §8
=======================================
"""

from typing import Dict, List, Optional

from .constants import (
    ZI_XING_BRANCHES, BRANCH_HIDDEN_STEMS, BRANCH_ELEMENT,
    STEM_ELEMENT, GEN_MAP,
    LIU_HE, LIU_CHONG, LIU_HAI, LIU_PO, AN_HE, GONG_HE,
    SAN_HE, BAN_SAN_HE, SAN_HUI,
    XING,
    LIU_HE_TRANSFORM_ELEMENT, LIU_HE_WU_WEI_PAIR, LIU_HE_WU_WEI_ELEMENTS,
    SAN_HE_ELEMENT,
    GONG_HE_MISSING_MIDDLE, GONG_HE_ELEMENT,
    ADJACENT_PAIRS,
)
from .glossary import (
    BAN_SAN_HE_BIRTH_PAIRS,
    BAN_SAN_HE_GRAVE_PAIRS,
)


# ── Pillar ordering utilities ──────────────────────────────

PILLAR_ORDER = ["year", "month", "day", "hour"]
_ADJACENT_SET = {(a, b) for a, b in ADJACENT_PAIRS} | {(b, a) for a, b in ADJACENT_PAIRS}


def _pillar_names_for_branch(chart: Dict, branch: str) -> List[str]:
    """Return pillar names that contain *branch*."""
    return [n for n in PILLAR_ORDER if chart["pillars"][n]["branch"] == branch]


def _are_adjacent(p1: str, p2: str) -> bool:
    return (p1, p2) in _ADJACENT_SET


# ── Self-punishment ─────────────────────────────────────────

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


# ── Punishment patterns ─────────────────────────────────────

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


# ── Lục Hợp transformation ─────────────────────────────────

def evaluate_liu_he_transformation(
    chart: Dict,
    branch1: str,
    branch2: str,
    pillar1: str,
    pillar2: str,
) -> Dict:
    """Evaluate whether a Six Combination (六合) transforms.

    Checks four classical conditions:
    1. Adjacency — pillars must be next to each other
    2. Month order support — month branch element matches or generates target
    3. Leading element — target element exposed on other stems or main hidden stems
    4. No obstruction — no clash on either combining branch from a third natal branch
    """
    pair = frozenset({branch1, branch2})
    target = LIU_HE_TRANSFORM_ELEMENT.get(pair)
    if target is None:
        return {"status": "invalid", "pair": (branch1, branch2)}

    # Wu-Wei dual transform logic
    if pair == LIU_HE_WU_WEI_PAIR:
        target = _resolve_wu_wei_target(chart)

    # Condition 1: Adjacency
    is_adjacent = _are_adjacent(pillar1, pillar2)

    # Condition 2: Month order support
    month_branch = chart["pillars"]["month"]["branch"]
    month_elem = BRANCH_ELEMENT[month_branch]
    month_support = (month_elem == target) or (GEN_MAP.get(month_elem) == target)

    # Condition 3: Leading element
    leading = _has_leading_element(chart, target, exclude_pillars={pillar1, pillar2})

    # Condition 4: No obstruction (no clash on either combining branch)
    obstructed = _branch_clashed_by_third(chart, branch1, branch2)

    # Determine outcome
    if is_adjacent and month_support and leading and not obstructed:
        status = "合化 (transformed)"
        confidence = 95
    elif is_adjacent and month_support and not obstructed:
        status = "合化 (transformed)"
        confidence = 80
    elif is_adjacent and (month_support or leading) and not obstructed:
        status = "合而不化 (bound)"
        confidence = 60
    else:
        status = "合而不化 (bound)"
        confidence = 40
        if not is_adjacent:
            confidence -= 10

    return {
        "pair": (branch1, branch2),
        "pillars": (pillar1, pillar2),
        "target_element": target,
        "is_adjacent": is_adjacent,
        "month_support": month_support,
        "leading_present": leading,
        "obstructed": obstructed,
        "status": status,
        "confidence": confidence,
    }


def _resolve_wu_wei_target(chart: Dict) -> str:
    """Resolve Wu-Wei (午未) dual transform: Fire (default) or Earth."""
    month_branch = chart["pillars"]["month"]["branch"]
    month_elem = BRANCH_ELEMENT[month_branch]

    earth_support = (month_elem == "Earth") or (GEN_MAP.get(month_elem) == "Earth")
    fire_support = (month_elem == "Fire") or (GEN_MAP.get(month_elem) == "Fire")

    if earth_support and not fire_support:
        return "Earth"

    # Check leading stems for Earth vs Fire
    earth_leading = 0
    fire_leading = 0
    for p in chart["pillars"].values():
        se = STEM_ELEMENT[p["stem"]]
        if se == "Earth":
            earth_leading += 1
        elif se == "Fire":
            fire_leading += 1

    if earth_leading > fire_leading and earth_support:
        return "Earth"
    return "Fire"  # Traditional default


def _has_leading_element(chart: Dict, target: str, exclude_pillars: set) -> bool:
    """Check if target element is exposed on stems or as main hidden stem."""
    for pname, p in chart["pillars"].items():
        if pname in exclude_pillars:
            continue
        if STEM_ELEMENT[p["stem"]] == target:
            return True
    # Also check main hidden stems
    for pname, p in chart["pillars"].items():
        if pname in exclude_pillars:
            continue
        hidden = BRANCH_HIDDEN_STEMS[p["branch"]]
        if hidden and STEM_ELEMENT[hidden[0]] == target:
            return True
    return False


def _branch_clashed_by_third(chart: Dict, b1: str, b2: str) -> bool:
    """Check if a third natal branch clashes either b1 or b2."""
    for p in chart["pillars"].values():
        b = p["branch"]
        if b == b1 or b == b2:
            continue
        if frozenset({b, b1}) in LIU_CHONG or frozenset({b, b2}) in LIU_CHONG:
            return True
    return False


# ── San He transformation ──────────────────────────────────

def evaluate_san_he_transformation(chart: Dict, trio: frozenset) -> Dict:
    """Evaluate whether a Three Combination (三合) successfully forms an elemental frame."""
    target = SAN_HE_ELEMENT.get(trio)
    if target is None:
        return {"status": "invalid", "trio": trio}

    month_branch = chart["pillars"]["month"]["branch"]
    month_elem = BRANCH_ELEMENT[month_branch]
    month_support = (month_elem == target) or (GEN_MAP.get(month_elem) == target)

    # Check if any branch in trio is clashed by an external branch
    branches_in_trio = set(trio)
    obstructed = False
    for p in chart["pillars"].values():
        b = p["branch"]
        if b in branches_in_trio:
            continue
        for tb in branches_in_trio:
            if frozenset({b, tb}) in LIU_CHONG:
                obstructed = True
                break
        if obstructed:
            break

    # Full trio present → strong formation
    if month_support and not obstructed:
        status = "合化 (frame formed)"
        confidence = 95
    elif month_support or not obstructed:
        status = "合化 (frame formed)"
        confidence = 75
    else:
        status = "合局受阻 (frame obstructed)"
        confidence = 40

    return {
        "trio": trio,
        "target_element": target,
        "month_support": month_support,
        "obstructed": obstructed,
        "status": status,
        "confidence": confidence,
    }


# ── Half Three Combination classification ──────────────────

def classify_ban_san_he(pair: frozenset) -> Dict:
    """Classify a half-trio as birth-phase or grave-phase."""
    if pair in BAN_SAN_HE_BIRTH_PAIRS:
        return {
            "pair": pair,
            "phase": "生地半合 (birth-phase)",
            "target_element": BAN_SAN_HE_BIRTH_PAIRS[pair],
            "strength": "stronger",
        }
    if pair in BAN_SAN_HE_GRAVE_PAIRS:
        return {
            "pair": pair,
            "phase": "墓地半合 (grave-phase)",
            "target_element": BAN_SAN_HE_GRAVE_PAIRS[pair],
            "strength": "weaker",
        }
    return {"pair": pair, "phase": "unknown", "target_element": None, "strength": "none"}


# ── Interaction conflict resolution ────────────────────────

def resolve_interaction_conflicts(interactions: Dict[str, list]) -> Dict[str, list]:
    """Apply classical priority rules to resolve conflicting interactions.

    Rules:
    1. 合 resolves 冲 when same branch is in both (adjacent 合 wins)
    2. 三合/三会 takes priority over 六合 for same branch
    3. 刑 coexists with other interactions (no resolution needed)
    """
    resolved = {k: list(v) for k, v in interactions.items()}

    # Collect branches involved in 六合
    he_branches = set()
    for item in resolved.get("六合", []):
        if isinstance(item, dict):
            he_branches.update(item.get("pair", ()))
        elif isinstance(item, tuple):
            he_branches.update(item)

    # Collect branches in san_he / san_hui
    frame_branches = set()
    for trio in resolved.get("三合", []):
        if isinstance(trio, dict):
            frame_branches.update(trio.get("trio", set()))
        elif isinstance(trio, frozenset):
            frame_branches.update(trio)
    for trio in resolved.get("三会", []):
        if isinstance(trio, frozenset):
            frame_branches.update(trio)

    # Rule 1: Adjacent 合 resolves 冲 on the same branch
    if resolved.get("六合") and resolved.get("六冲"):
        he_set = set()
        for item in resolved["六合"]:
            if isinstance(item, dict) and item.get("status", "").startswith("合化"):
                he_set.update(item.get("pair", ()))
            elif isinstance(item, tuple):
                he_set.update(item)
        new_chong = []
        for item in resolved["六冲"]:
            clash_branches = set(item) if isinstance(item, tuple) else set()
            if clash_branches & he_set:
                continue  # Resolved by combination
            new_chong.append(item)
        resolved["六冲"] = new_chong

    return resolved


# ── Main detection function ─────────────────────────────────

def detect_branch_interactions(chart: Dict) -> Dict[str, list]:
    """Detect all branch interactions among natal branches.

    Detects: 六合, 六冲, 害, 六破, 暗合, 拱合, 三合, 半三合, 三会, 刑, 自刑.
    Also evaluates transformation outcomes for 六合 and 三合.
    """
    pillar_names = list(chart["pillars"].keys())
    branches = [chart["pillars"][n]["branch"] for n in pillar_names]
    bset = set(branches)

    results: Dict[str, list] = {
        "六合": [], "六冲": [], "害": [], "六破": [],
        "暗合": [], "拱合": [],
        "三合": [], "半三合": [], "三会": [],
        "刑": [], "自刑": [],
    }

    # Pairwise interactions
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            pair = frozenset({branches[i], branches[j]})
            p1, p2 = pillar_names[i], pillar_names[j]

            if pair in LIU_HE:
                transform = evaluate_liu_he_transformation(
                    chart, branches[i], branches[j], p1, p2,
                )
                results["六合"].append(transform)

            if pair in LIU_CHONG:
                results["六冲"].append((branches[i], branches[j]))

            if pair in LIU_HAI:
                results["害"].append((branches[i], branches[j]))

            if pair in LIU_PO:
                results["六破"].append((branches[i], branches[j]))

            if pair in AN_HE:
                results["暗合"].append((branches[i], branches[j]))

    # Arching combinations (拱合): pair present, middle branch ABSENT
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            pair = frozenset({branches[i], branches[j]})
            if pair in GONG_HE:
                missing = GONG_HE_MISSING_MIDDLE.get(pair)
                if missing and missing not in bset:
                    results["拱合"].append({
                        "pair": (branches[i], branches[j]),
                        "missing_middle": missing,
                        "target_element": GONG_HE_ELEMENT.get(pair),
                    })

    # Three Combinations (三合) with transformation evaluation
    for trio in SAN_HE:
        if trio.issubset(bset):
            transform = evaluate_san_he_transformation(chart, trio)
            results["三合"].append(transform)

    # Half Three Combinations (半三合) — only if not part of a full 三合
    full_trio_branches = set()
    for entry in results["三合"]:
        if isinstance(entry, dict):
            full_trio_branches.update(entry.get("trio", set()))
    for pair in BAN_SAN_HE:
        if pair.issubset(bset):
            already_full = any(pair.issubset(entry.get("trio", set()) if isinstance(entry, dict) else entry) for entry in results["三合"])
            if not already_full:
                classification = classify_ban_san_he(pair)
                results["半三合"].append(classification)

    # Directional Combinations (三会)
    for trio in SAN_HUI:
        if trio.issubset(bset):
            results["三会"].append(trio)

    # Punishments
    for entry in detect_xing(chart, strict=False):
        results["刑"].append(entry)

    for entry in detect_self_punishment(chart):
        results["自刑"].append(entry)

    # Resolve conflicts
    results = resolve_interaction_conflicts(results)

    return results

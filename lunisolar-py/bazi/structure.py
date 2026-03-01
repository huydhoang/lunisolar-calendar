"""
Chart Structure Classification (格局) — spec §7
=================================================

Three-tier classification:
  Tier 1: Special Structures (Transform, Follow, Five-Element Dominance)
  Tier 2: Extreme Prosperous (建禄格, 羊刃格)
  Tier 3: Eight Regular Structures (八正格)
"""

from typing import Dict, List, Optional, Tuple, Union

from .constants import (
    HEAVENLY_STEMS, STEM_ELEMENT, BRANCH_ELEMENT,
    STEM_TRANSFORMATIONS, LU_MAP, GOAT_BLADE_TABLE,
    GEN_MAP, CONTROL_MAP, SAN_HE_ELEMENT, SAN_HUI_ELEMENT,
)
from .ten_gods import ten_god, weighted_ten_god_distribution
from .glossary import (
    TEN_GOD_TO_REGULAR_STRUCTURE,
    ELEMENT_TO_DOMINANCE_STRUCTURE,
    ELEMENT_TO_TRANSFORM_STRUCTURE,
)


def detect_month_pillar_structure(chart: Dict) -> Optional[str]:
    """Detect structure based on month pillar Ten-God using Protrusion (透出)."""
    month_hidden = chart["pillars"]["month"]["hidden"]
    if not month_hidden:
        return None

    dm_idx = HEAVENLY_STEMS.index(chart["day_master"]["stem"])

    protruding_stems = [
        chart["pillars"]["year"]["stem"],
        chart["pillars"]["month"]["stem"],
        chart["pillars"]["hour"]["stem"],
    ]

    for _role, hidden_stem in month_hidden:
        if hidden_stem in protruding_stems:
            hidden_idx = HEAVENLY_STEMS.index(hidden_stem)
            return ten_god(dm_idx, hidden_idx)

    main_hidden_stem = month_hidden[0][1]
    main_hidden_idx = HEAVENLY_STEMS.index(main_hidden_stem)
    return ten_god(dm_idx, main_hidden_idx)


# ── Tier 1: Special Structures ──────────────────────────────

def detect_transform_structure(
    chart: Dict,
    transformations: Optional[List[Dict]] = None,
) -> Optional[Dict]:
    """Detect Transform Structure (化格).

    The DM must be part of a successful stem transformation.
    """
    if not transformations:
        return None

    dm_stem = chart["day_master"]["stem"]
    for t in transformations:
        if t.get("status", "").startswith("Hóa") and "suppressed" not in t.get("status", ""):
            stems = t.get("stems", ())
            if dm_stem in stems:
                target = t["target_element"]
                term = ELEMENT_TO_TRANSFORM_STRUCTURE.get(target)
                return {
                    "primary": term[0] if term else f"化{target}格",
                    "category": "化格",
                    "target_element": target,
                    "transformation": t,
                    "term": term,
                }
    return None


def detect_follow_structure(
    chart: Dict,
    strength: str,
    score: float = 0.0,
    rooting: Optional[Dict] = None,
    dist: Optional[Dict[str, float]] = None,
) -> Optional[Dict]:
    """Detect Follow Structures (从格).

    Requires the DM to be extremely weak (unrooted or nearly so) and one
    category of Ten Gods to dominate.
    """
    # DM must be unrooted or extremely weak
    dm_rooted = True
    if rooting:
        dm_rooted = rooting.get("is_rooted", True)
    elif strength not in ("weak",):
        return None

    if dm_rooted and strength != "weak":
        return None

    if not dist:
        dist = weighted_ten_god_distribution(chart)

    # Calculate category totals
    wealth_total = dist.get("正财", 0) + dist.get("偏财", 0)
    officer_total = dist.get("正官", 0) + dist.get("七杀", 0)
    output_total = dist.get("食神", 0) + dist.get("伤官", 0)
    resource_total = dist.get("正印", 0) + dist.get("偏印", 0)
    peer_total = dist.get("比肩", 0) + dist.get("劫财", 0)

    total_non_peer = wealth_total + officer_total + output_total + resource_total
    if total_non_peer == 0:
        return None

    # DM resource + peer support must be minimal
    support_ratio = (resource_total + peer_total) / (total_non_peer + resource_total + peer_total)
    if support_ratio > 0.25:
        return None

    # Determine which category dominates
    categories = [
        (wealth_total, "从财格", "Tòng Tài Cách"),
        (officer_total, "从官杀格", "Tòng Quan Sát Cách"),
        (output_total, "从食伤格", "Tòng Thực Thương Cách"),
    ]
    categories.sort(key=lambda x: x[0], reverse=True)
    top_val, top_name, top_vi = categories[0]

    if top_val < 5:
        return None

    # If no clear winner → 从势格 (Follow Momentum)
    second_val = categories[1][0]
    if second_val > 0 and top_val / second_val < 1.5:
        return {
            "primary": "从势格",
            "category": "从格",
            "note": "No single category dominates → Follow Momentum",
        }

    return {
        "primary": top_name,
        "category": "从格",
        "note": f"DM unrooted/weak, {top_name} dominates",
    }


def detect_five_element_dominance(
    chart: Dict,
    interactions: Optional[Dict] = None,
) -> Optional[Dict]:
    """Detect Five-Element Dominance Structures (五行专旺格).

    Requires one element to dominate via season + branch frames (三合/三会).
    """
    dm_elem = chart["day_master"]["element"]
    month_branch = chart["pillars"]["month"]["branch"]
    month_elem = BRANCH_ELEMENT[month_branch]

    # DM element must match the month's seasonal element
    if month_elem != dm_elem and GEN_MAP.get(month_elem) != dm_elem:
        return None

    # Check for supporting 三合 or 三会 frames
    if not interactions:
        return None

    frame_elements = set()
    for entry in interactions.get("三合", []):
        if isinstance(entry, dict):
            fe = entry.get("target_element")
        else:
            fe = SAN_HE_ELEMENT.get(entry)
        if fe:
            frame_elements.add(fe)
    for entry in interactions.get("三会", []):
        if isinstance(entry, frozenset):
            fe = SAN_HUI_ELEMENT.get(entry)
            if fe:
                frame_elements.add(fe)

    if dm_elem in frame_elements:
        term = ELEMENT_TO_DOMINANCE_STRUCTURE.get(dm_elem)
        return {
            "primary": term[0] if term else f"{dm_elem}专旺格",
            "category": "五行专旺格",
            "dominant_element": dm_elem,
            "term": term,
        }

    return None


def detect_special_structures(
    chart: Dict,
    strength: str,
    score: float = 0.0,
    rooting: Optional[Dict] = None,
    interactions: Optional[Dict] = None,
    transformations: Optional[List[Dict]] = None,
) -> Optional[Dict]:
    """Detect special structures (Tier 1) with full context.

    Checks in priority order:
    1. Transform Structures (化格)
    2. Follow Structures (从格)
    3. Five-Element Dominance (专旺格)
    """
    dist = weighted_ten_god_distribution(chart)

    # 1. Transform structures
    result = detect_transform_structure(chart, transformations)
    if result:
        return result

    # 2. Follow structures
    result = detect_follow_structure(chart, strength, score, rooting, dist)
    if result:
        return result

    # 3. Five-Element Dominance
    result = detect_five_element_dominance(chart, interactions)
    if result:
        return result

    return None


# ── Tier 2: Extreme Prosperous ──────────────────────────────

def detect_extreme_prosperous(
    chart: Dict,
    strength: str,
    rooting: Optional[Dict] = None,
) -> Optional[Dict]:
    """Detect Tier 2: 建禄格 or 羊刃格."""
    dm_stem = chart["day_master"]["stem"]
    month_branch = chart["pillars"]["month"]["branch"]

    lu_branch = LU_MAP.get(dm_stem)
    if lu_branch == month_branch:
        return {
            "primary": "建禄格",
            "category": "旺极格",
            "note": f"DM 禄 ({lu_branch}) in month branch",
        }

    yr_branch = GOAT_BLADE_TABLE.get(dm_stem)
    if yr_branch == month_branch:
        return {
            "primary": "羊刃格",
            "category": "旺极格",
            "note": f"DM 羊刃 ({yr_branch}) in month branch",
        }

    return None


# ── Composite Structures ────────────────────────────────────

def detect_composite_structures(
    chart: Dict,
    strength: str,
    dist: Dict[str, float],
) -> Optional[str]:
    """Detect special composite structures that refine the primary."""
    shi_shen = dist.get("食神", 0)
    shang_guan = dist.get("伤官", 0)
    qi_sha = dist.get("七杀", 0)
    zheng_guan = dist.get("正官", 0)
    zheng_yin = dist.get("正印", 0)
    pian_yin = dist.get("偏印", 0)

    # 食神制杀: 食神 + 七杀 both present, 食 >= 杀
    if shi_shen >= 2 and qi_sha >= 2 and shi_shen >= qi_sha:
        return "食神制杀格"

    # 伤官配印: 伤官 + 正印/偏印 both present
    if shang_guan >= 2 and (zheng_yin + pian_yin) >= 2:
        return "伤官配印格"

    # 伤官见官: 伤官 + 正官 both present (usually broken structure)
    if shang_guan >= 2 and zheng_guan >= 2:
        return "伤官见官格"

    # 杀印相生: 七杀 + 正印 both present
    if qi_sha >= 2 and zheng_yin >= 2:
        return "杀印相生格"

    return None


# ── Quality Assessment ──────────────────────────────────────

def _get_structure_category(ten_god_val: str) -> str:
    category_map = {
        ("正官", "七杀"): "官杀格",
        ("食神", "伤官"): "食伤格",
        ("正财", "偏财"): "财格",
        ("正印", "偏印"): "印格",
        ("比肩", "劫财"): "比劫格",
    }
    for gods, category in category_map.items():
        if ten_god_val in gods:
            return category
    return "普通格局"


def _assess_structure_quality(
    chart: Dict,
    primary_tg: str,
    strength: str,
    dist: Dict[str, float],
    interactions: Optional[Dict] = None,
    transformations: Optional[List[Dict]] = None,
) -> Tuple[str, bool]:
    """Assess structure quality (成格 vs 破格) using interaction data."""

    # Check for clash disruption if interactions provided
    has_month_clash = False
    if interactions:
        month_branch = chart["pillars"]["month"]["branch"]
        for clash in interactions.get("六冲", []):
            if isinstance(clash, tuple) and month_branch in clash:
                has_month_clash = True
                break

    if primary_tg in ("正官", "七杀"):
        has_control = dist.get("食神", 0) > 0 or dist.get("伤官", 0) > 0
        if primary_tg == "七杀" and has_control:
            quality = "七杀有制, 格局清纯"
            broken = has_month_clash
        elif strength in ("strong", "balanced"):
            quality = "身杀两停"
            broken = has_month_clash
        else:
            quality = "杀重身轻 (破格)"
            broken = True
        return quality, broken

    elif primary_tg in ("食神", "伤官"):
        has_officer = dist.get("正官", 0) > 2
        if strength == "strong" and not has_officer:
            quality = "食伤生财格"
            broken = has_month_clash
        elif has_officer:
            quality = "伤官见官, 为祸百端 (破格)"
            broken = True
        else:
            quality = "食伤格成, 但身弱"
            broken = False
        return quality, broken

    elif primary_tg in ("正财", "偏财"):
        if strength == "strong":
            quality = "身财两停, 格局纯正"
            broken = has_month_clash
        else:
            quality = "财多身弱 (破格)"
            broken = True
        return quality, broken

    elif primary_tg in ("正印", "偏印"):
        if strength in ("weak", "balanced"):
            return "印绶格成", has_month_clash
        else:
            return "印多压身", False

    elif primary_tg in ("比肩", "劫财"):
        has_food = dist.get("食神", 0) + dist.get("伤官", 0) > 3
        if strength == "strong" and has_food:
            return "建禄格/羊刃格成", has_month_clash
        else:
            return "比劫夺财风险", False

    return "格局一般", False


# ── Main Classifier ─────────────────────────────────────────

def classify_structure(
    chart: Dict,
    strength: str,
    score: float = None,
    rooting: Optional[Dict] = None,
    interactions: Optional[Dict] = None,
    transformations: Optional[List[Dict]] = None,
) -> Dict[str, Union[str, float, bool]]:
    """Unified structure classifier using traditional Bazi theory.

    Three-tier classification:
      Tier 1: Special (化格, 从格, 专旺格) — highest priority
      Tier 2: Extreme Prosperous (建禄格, 羊刃格)
      Tier 3: Eight Regular Structures (八正格)

    Backward compatible: (chart, strength) still works; new params are optional.
    """
    # Tier 1: Special structures
    special = detect_special_structures(
        chart, strength,
        score=score or 0.0,
        rooting=rooting,
        interactions=interactions,
        transformations=transformations,
    )
    if special:
        return {
            "primary": special["primary"],
            "category": special.get("category", "特殊格局"),
            "quality": "特殊",
            "dominance_score": 0.0,
            "is_special": True,
            "is_broken": False,
            "notes": special.get("note", "Special structure takes precedence"),
        }

    dist = weighted_ten_god_distribution(chart)
    if not dist:
        dist = {"比肩": 1.0}

    # Tier 2: Extreme Prosperous
    extreme = detect_extreme_prosperous(chart, strength, rooting)

    # Tier 3: Eight Regular Structures
    month_tg = detect_month_pillar_structure(chart)
    dominant_tg = max(dist, key=lambda k: dist[k])
    dominance_score = dist[dominant_tg]

    month_score = dist.get(month_tg, 0) if month_tg else 0
    if month_tg and month_score >= dominance_score * 0.7:
        primary_tg = month_tg
    else:
        primary_tg = dominant_tg

    # Check for composite structures
    composite = detect_composite_structures(chart, strength, dist)

    structure_map = {
        "正官": "正官格", "七杀": "七杀格",
        "食神": "食神格", "伤官": "伤官格",
        "正财": "正财格", "偏财": "偏财格",
        "正印": "正印格", "偏印": "偏印格",
        "比肩": "建禄格", "劫财": "羊刃格",
    }

    # Decide primary structure
    if extreme and primary_tg in ("比肩", "劫财"):
        primary_structure = extreme["primary"]
        category = extreme["category"]
    else:
        primary_structure = structure_map.get(primary_tg, "普通格局")
        category = _get_structure_category(primary_tg)

    quality, is_broken = _assess_structure_quality(
        chart, primary_tg, strength, dist, interactions, transformations
    )

    notes = f"Based on {primary_tg} dominance"
    if composite:
        notes += f"; composite: {composite}"

    return {
        "primary": primary_structure,
        "category": category,
        "quality": quality,
        "dominance_score": dominance_score,
        "is_special": False,
        "is_broken": is_broken,
        "composite": composite,
        "notes": notes,
    }

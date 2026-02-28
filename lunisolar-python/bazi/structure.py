"""
Chart Structure Classification (格局) — spec §7
=================================================
"""

from typing import Dict, Optional, Tuple, Union

from .constants import HEAVENLY_STEMS
from .ten_gods import ten_god, weighted_ten_god_distribution


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


def detect_special_structures(chart: Dict, strength: str) -> Optional[str]:
    """Detect special structures (从格, 化格, etc.)."""
    return None


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
    chart: Dict, primary_tg: str, strength: str, dist: Dict[str, float]
) -> Tuple[str, bool]:
    if primary_tg in ("正官", "七杀"):
        has_control = dist.get("食神", 0) > 0 or dist.get("伤官", 0) > 0
        if primary_tg == "七杀" and has_control:
            return "七杀有制, 格局清纯", False
        elif strength in ("strong", "balanced"):
            return "身杀两停", False
        else:
            return "杀重身轻 (破格)", True
    elif primary_tg in ("食神", "伤官"):
        has_officer = dist.get("正官", 0) > 2
        if strength == "strong" and not has_officer:
            return "食伤生财格", False
        elif has_officer:
            return "伤官见官, 为祸百端 (破格)", True
        else:
            return "食伤格成, 但身弱", False
    elif primary_tg in ("正财", "偏财"):
        if strength == "strong":
            return "身财两停, 格局纯正", False
        else:
            return "财多身弱 (破格)", True
    elif primary_tg in ("正印", "偏印"):
        if strength in ("weak", "balanced"):
            return "印绶格成", False
        else:
            return "印多压身", False
    elif primary_tg in ("比肩", "劫财"):
        has_food = dist.get("食神", 0) + dist.get("伤官", 0) > 3
        if strength == "strong" and has_food:
            return "建禄格/羊刃格成", False
        else:
            return "比劫夺财风险", False
    return "格局一般", False


def classify_structure(
    chart: Dict, strength: str
) -> Dict[str, Union[str, float, bool]]:
    """Unified structure classifier using traditional Bazi theory."""
    special = detect_special_structures(chart, strength)
    if special:
        return {
            "primary": special,
            "category": "特殊格局",
            "quality": "特殊",
            "dominance_score": 0.0,
            "is_special": True,
            "is_broken": False,
            "notes": "Special structure takes precedence",
        }

    month_tg = detect_month_pillar_structure(chart)
    dist = weighted_ten_god_distribution(chart)

    if not dist:
        dist = {month_tg: 1.0} if month_tg else {"比肩": 1.0}

    dominant_tg = max(dist, key=lambda k: dist[k])
    dominance_score = dist[dominant_tg]

    month_score = dist.get(month_tg, 0) if month_tg else 0
    if month_tg and month_score >= dominance_score * 0.7:
        primary_tg = month_tg
    else:
        primary_tg = dominant_tg

    structure_map = {
        "正官": "正官格", "七杀": "七杀格",
        "食神": "食神格", "伤官": "伤官格",
        "正财": "正财格", "偏财": "偏财格",
        "正印": "正印格", "偏印": "偏印格",
        "比肩": "建禄格", "劫财": "羊刃格",
    }

    primary_structure = structure_map.get(primary_tg, "普通格局")
    category = _get_structure_category(primary_tg)
    quality, is_broken = _assess_structure_quality(chart, primary_tg, strength, dist)

    return {
        "primary": primary_structure,
        "category": category,
        "quality": quality,
        "dominance_score": dominance_score,
        "is_special": False,
        "is_broken": is_broken,
        "notes": f"Based on {primary_tg} dominance",
    }

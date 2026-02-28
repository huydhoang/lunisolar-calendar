"""
Comprehensive Interaction Analysis & Custom Time Range Analysis
===============================================================
"""

from typing import Dict, List, Optional

from .constants import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES, STEM_ELEMENT, STEM_POLARITY,
    BRANCH_ELEMENT, GEN_MAP, CONTROL_MAP,
    LIU_CHONG, LIU_HE, LIU_HAI, STEM_TRANSFORMATIONS,
)
from .core import ganzhi_from_cycle
from .ten_gods import ten_god, _element_relation
from .longevity import life_stage_detail, life_stages_for_chart
from .nayin import nayin_for_cycle, _nayin_pure_element, analyze_nayin_interactions
from .scoring import score_day_master
from .branch_interactions import detect_branch_interactions
from .stem_transformations import detect_stem_combinations, detect_transformations
from .punishments import detect_punishments, detect_fu_yin_duplication


def analyze_time_range(
    chart: Dict,
    year_cycle: int,
    month_cycle: Optional[int] = None,
    day_cycle: Optional[int] = None,
    luck_pillar: Optional[Dict] = None,
) -> Dict:
    """Analyze a custom time range against the natal chart.

    Supports three levels of detail:
    - **Year Level**: only ``year_cycle`` provided
    - **Year-Month Level**: ``year_cycle`` + ``month_cycle``
    - **Year-Month-Day Level**: all three
    """
    dm_idx = HEAVENLY_STEMS.index(chart["day_master"]["stem"])
    dm_elem = chart["day_master"]["element"]

    result: Dict = {"level": "year", "pillars": {}}

    # --- Year pillar ---
    yr_stem, yr_branch = ganzhi_from_cycle(year_cycle)
    yr_b_idx = EARTHLY_BRANCHES.index(yr_branch)
    yr_life_stage = life_stage_detail(dm_idx, yr_b_idx)
    yr_ten_god = ten_god(dm_idx, HEAVENLY_STEMS.index(yr_stem))
    yr_nayin = nayin_for_cycle(year_cycle)

    yr_entry: Dict = {
        "stem": yr_stem,
        "branch": yr_branch,
        "ten_god": yr_ten_god,
        "life_stage": yr_life_stage,
    }
    if yr_nayin:
        yr_entry["nayin"] = {
            "element": _nayin_pure_element(yr_nayin["nayin_element"]),
            "chinese": yr_nayin["nayin_chinese"],
            "vietnamese": yr_nayin["nayin_vietnamese"],
            "english": yr_nayin["nayin_english"],
        }
    result["pillars"]["year"] = yr_entry

    # Interactions with natal branches
    yr_pillar = {"stem": yr_stem, "branch": yr_branch}
    natal_branches = [p["branch"] for p in chart["pillars"].values()]
    yr_interactions: List[str] = []
    for b in natal_branches:
        pair = frozenset({b, yr_branch})
        if pair in LIU_CHONG:
            yr_interactions.append("冲")
        if pair in LIU_HE:
            yr_interactions.append("合")
        if pair in LIU_HAI:
            yr_interactions.append("害")
    result["year_interactions"] = yr_interactions

    result["fu_yin_duplication"] = detect_fu_yin_duplication(chart, yr_pillar)

    # Stem transformation check
    yr_stem_combos: List[Dict] = []
    for pname, p in chart["pillars"].items():
        pair_key = frozenset([yr_stem, p["stem"]])
        if pair_key in STEM_TRANSFORMATIONS:
            yr_stem_combos.append({
                "natal_pillar": pname,
                "stems": (yr_stem, p["stem"]),
                "target_element": STEM_TRANSFORMATIONS[pair_key],
            })
    result["year_stem_combinations"] = yr_stem_combos

    # NaYin relation to Day Master
    if yr_nayin:
        ny_elem = _nayin_pure_element(yr_nayin["nayin_element"])
        result["year_nayin_vs_dm"] = {
            "nayin_element": ny_elem,
            "relation": _element_relation(dm_elem, ny_elem),
        }

    # --- Month pillar (if provided) ---
    if month_cycle is not None:
        result["level"] = "year-month"
        mo_stem, mo_branch = ganzhi_from_cycle(month_cycle)
        mo_b_idx = EARTHLY_BRANCHES.index(mo_branch)
        mo_life_stage = life_stage_detail(dm_idx, mo_b_idx)
        mo_ten_god = ten_god(dm_idx, HEAVENLY_STEMS.index(mo_stem))
        mo_nayin = nayin_for_cycle(month_cycle)

        mo_entry: Dict = {
            "stem": mo_stem,
            "branch": mo_branch,
            "ten_god": mo_ten_god,
            "life_stage": mo_life_stage,
        }
        if mo_nayin:
            mo_entry["nayin"] = {
                "element": _nayin_pure_element(mo_nayin["nayin_element"]),
                "chinese": mo_nayin["nayin_chinese"],
                "vietnamese": mo_nayin["nayin_vietnamese"],
                "english": mo_nayin["nayin_english"],
            }
        result["pillars"]["month"] = mo_entry

    # --- Day pillar (if provided) ---
    if day_cycle is not None:
        result["level"] = "year-month-day"
        dy_stem, dy_branch = ganzhi_from_cycle(day_cycle)
        dy_b_idx = EARTHLY_BRANCHES.index(dy_branch)
        dy_life_stage = life_stage_detail(dm_idx, dy_b_idx)
        dy_ten_god = ten_god(dm_idx, HEAVENLY_STEMS.index(dy_stem))
        dy_nayin = nayin_for_cycle(day_cycle)

        dy_entry: Dict = {
            "stem": dy_stem,
            "branch": dy_branch,
            "ten_god": dy_ten_god,
            "life_stage": dy_life_stage,
        }
        if dy_nayin:
            dy_entry["nayin"] = {
                "element": _nayin_pure_element(dy_nayin["nayin_element"]),
                "chinese": dy_nayin["nayin_chinese"],
                "vietnamese": dy_nayin["nayin_vietnamese"],
                "english": dy_nayin["nayin_english"],
            }
        result["pillars"]["day"] = dy_entry

    # Luck pillar context
    if luck_pillar is not None:
        lp_interactions: List[str] = []
        lp_branch = luck_pillar["branch"]
        for b in natal_branches:
            pair = frozenset({b, lp_branch})
            if pair in LIU_CHONG:
                lp_interactions.append("冲")
            if pair in LIU_HE:
                lp_interactions.append("合")
            if pair in LIU_HAI:
                lp_interactions.append("害")
        result["luck_pillar_interactions"] = lp_interactions
        result["luck_fu_yin_duplication"] = detect_fu_yin_duplication(
            chart, luck_pillar
        )

    return result


def comprehensive_analysis(chart: Dict) -> Dict:
    """Produce a comprehensive interaction and transformation analysis."""
    dm = chart["day_master"]
    dm_stem = dm["stem"]
    dm_elem = dm["element"]
    score, strength = score_day_master(chart)

    month_branch = chart["pillars"]["month"]["branch"]
    month_elem = BRANCH_ELEMENT[month_branch]

    interactions = detect_branch_interactions(chart)
    stem_combos = detect_stem_combinations(chart)
    transformations = detect_transformations(chart)
    punishments = detect_punishments(chart)
    life_stages = life_stages_for_chart(chart)
    nayin_analysis = analyze_nayin_interactions(chart)

    summary_parts = [
        f"Day Master {dm_stem} {dm_elem}; strength: {strength} ({score} pts).",
        f"Born in {month_branch} ({month_elem} month).",
    ]
    for t in transformations:
        if t["status"].startswith("Hóa"):
            summary_parts.append(
                f"Transformation: {t['stems'][0]}+{t['stems'][1]} → "
                f"{t['target_element']} ({t['status']}, confidence {t['confidence']})."
            )
    if interactions.get("六冲"):
        summary_parts.append("Clashes detected — watch for conflicts.")
    if punishments:
        p_types = {p["type"] for p in punishments}
        summary_parts.append(f"Punishments: {', '.join(p_types)}.")

    return {
        "day_master": {
            "stem": dm_stem,
            "element": dm_elem,
            "polarity": STEM_POLARITY[dm_stem],
            "strength": strength,
            "strength_score": score,
            "born_in": f"{month_branch} ({month_elem} month)",
        },
        "natal_interactions": {
            "clashes": interactions.get("六冲", []),
            "combinations": interactions.get("六合", []),
            "san_he": interactions.get("三合", []),
            "san_hui": interactions.get("三会", []),
            "stem_combinations": stem_combos,
            "transformations": transformations,
            "punishments": punishments,
            "harms": interactions.get("害", []),
            "xing": interactions.get("刑", []),
            "self_punishment": interactions.get("自刑", []),
        },
        "life_stages": life_stages,
        "nayin_analysis": nayin_analysis,
        "summary": " ".join(summary_parts),
    }

"""
Comprehensive Interaction Analysis & Custom Time Range Analysis
===============================================================
"""

from typing import Dict, List, Optional

from .constants import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES, STEM_ELEMENT, STEM_POLARITY,
    BRANCH_ELEMENT, GEN_MAP, CONTROL_MAP,
    LIU_CHONG, LIU_HE, LIU_HAI, STEM_TRANSFORMATIONS,
    SAN_HUI_ELEMENT,
)
from .core import ganzhi_from_cycle
from .ten_gods import ten_god, _element_relation
from .longevity import life_stage_detail, life_stages_for_chart
from .nayin import nayin_for_cycle, _nayin_pure_element, analyze_nayin_interactions
from .scoring import score_day_master
from .branch_interactions import detect_branch_interactions
from .stem_transformations import (
    detect_stem_combinations, detect_transformations,
    detect_jealous_combinations, detect_stem_restraints, detect_stem_clashes,
)
from .punishments import detect_punishments, detect_fu_yin_duplication
from .rooting import analyze_dm_rooting, analyze_tomb_treasury
from .symbolic_stars import apply_void_effects
from .structure import classify_structure


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


def detect_missing_elements(chart: Dict) -> List[Dict]:
    """Detect elements completely absent from stems and main/middle hidden stems.

    Missing elements reveal structural gaps in a chart — particularly significant
    when the missing element corresponds to Officer/Power (官殺) or Wealth (財星).
    """
    ALL_ELEMENTS = {"Wood", "Fire", "Earth", "Metal", "Water"}
    present = set()

    for p in chart["pillars"].values():
        present.add(STEM_ELEMENT[p["stem"]])
        for role, stem in p["hidden"]:
            if role in ("main", "middle"):
                present.add(STEM_ELEMENT[stem])

    missing = ALL_ELEMENTS - present
    if not missing:
        return []

    dm_elem = chart["day_master"]["element"]
    result = []
    for elem in sorted(missing):
        rel = _element_relation(dm_elem, elem)
        tg_category = {
            "same": "比劫 (Peers)",
            "sheng": "印星 (Resource/Seal)",
            "wo_sheng": "食伤 (Output)",
            "wo_ke": "财星 (Wealth)",
            "ke": "官杀 (Officer/Power)",
        }.get(rel, "Unknown")

        result.append({
            "element": elem,
            "ten_god_category": tg_category,
            "relation": rel,
        })

    return result


def detect_competing_frames(chart: Dict, interactions: Dict) -> List[Dict]:
    """Detect branches torn between competing combination frames.

    Identifies scenarios like '群比争财' (Companions fighting for Wealth)
    where a branch participates in both a peer frame (Bi-Jie) and a
    wealth combination simultaneously.
    """
    dm_elem = chart["day_master"]["element"]

    # Collect all frame affiliations per branch
    branch_frames: Dict[str, List[Dict]] = {}

    for entry in interactions.get("三合", []):
        if isinstance(entry, dict):
            trio = entry.get("trio", frozenset())
            target = entry.get("target_element")
            for b in trio:
                branch_frames.setdefault(b, []).append({
                    "type": "三合", "target": target, "branches": trio,
                })

    for entry in interactions.get("三会", []):
        if isinstance(entry, frozenset):
            target = SAN_HUI_ELEMENT.get(entry)
            for b in entry:
                branch_frames.setdefault(b, []).append({
                    "type": "三会", "target": target, "branches": entry,
                })

    for entry in interactions.get("半三合", []):
        if isinstance(entry, dict):
            pair = entry.get("pair", frozenset())
            target = entry.get("target_element")
            for b in pair:
                branch_frames.setdefault(b, []).append({
                    "type": "半三合", "target": target, "branches": pair,
                })

    results = []
    for branch, frames in branch_frames.items():
        if len(frames) < 2:
            continue

        targets = {f["target"] for f in frames if f["target"]}
        if len(targets) < 2:
            continue

        # Check for peer-vs-wealth conflict (群比争财)
        has_peer_frame = any(t == dm_elem for t in targets)
        wealth_elem = CONTROL_MAP.get(dm_elem)
        has_wealth_frame = any(t == wealth_elem for t in targets)

        if has_peer_frame and has_wealth_frame:
            conflict_type = "群比争财 (Companions fighting for Wealth)"
        else:
            conflict_type = "多局争支 (Competing frames on branch)"

        results.append({
            "branch": branch,
            "frames": frames,
            "targets": list(targets),
            "conflict_type": conflict_type,
        })

    return results


def comprehensive_analysis(chart: Dict) -> Dict:
    """Produce a comprehensive interaction and transformation analysis.

    Integrates all subsystems: branch interactions, stem transformations,
    rooting, tomb/treasury, void effects, structure classification, and scoring.
    """
    dm = chart["day_master"]
    dm_stem = dm["stem"]
    dm_elem = dm["element"]

    month_branch = chart["pillars"]["month"]["branch"]
    month_elem = BRANCH_ELEMENT[month_branch]

    # Core subsystem outputs
    interactions = detect_branch_interactions(chart)
    stem_combos = detect_stem_combinations(chart)
    transformations = detect_transformations(chart)
    punishments = detect_punishments(chart)
    life_stages = life_stages_for_chart(chart)
    nayin_analysis = analyze_nayin_interactions(chart)

    # New subsystem outputs
    dm_rooting = analyze_dm_rooting(chart)
    tomb_analysis = analyze_tomb_treasury(chart)
    jealous_combos = detect_jealous_combinations(chart)
    stem_restraints = detect_stem_restraints(chart)
    stem_clashes = detect_stem_clashes(chart)

    # Apply void effects to interactions
    interactions = apply_void_effects(chart, interactions)

    # Score with interaction and rooting awareness
    score, strength = score_day_master(chart, interactions=interactions, rooting=dm_rooting)

    # Structure classification with full context
    structure = classify_structure(
        chart, strength,
        score=score,
        rooting=dm_rooting,
        interactions=interactions,
        transformations=transformations,
    )

    # Build summary
    summary_parts = [
        f"Day Master {dm_stem} {dm_elem}; strength: {strength} ({score:.1f} pts).",
        f"Born in {month_branch} ({month_elem} month).",
        f"Rooting: {dm_rooting['classification']} (strength {dm_rooting['total_strength']}).",
        f"Structure: {structure['primary']} ({structure['quality']}).",
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
    if tomb_analysis:
        for tomb in tomb_analysis:
            if tomb["dm_enters_tomb"]:
                summary_parts.append(f"DM enters tomb at {tomb['branch']} ({tomb['pillar']}).")

    # Missing elements and competing frames
    missing_elements = detect_missing_elements(chart)
    competing_frames = detect_competing_frames(chart, interactions)

    if missing_elements:
        missing_names = [f"{m['element']} ({m['ten_god_category']})" for m in missing_elements]
        summary_parts.append(f"Missing elements: {', '.join(missing_names)}.")
    if competing_frames:
        for cf in competing_frames:
            summary_parts.append(f"Branch conflict: {cf['branch']} — {cf['conflict_type']}.")

    return {
        "day_master": {
            "stem": dm_stem,
            "element": dm_elem,
            "polarity": STEM_POLARITY[dm_stem],
            "strength": strength,
            "strength_score": score,
            "born_in": f"{month_branch} ({month_elem} month)",
        },
        "rooting": dm_rooting,
        "structure": structure,
        "natal_interactions": {
            "combinations": interactions.get("六合", []),
            "clashes": interactions.get("六冲", []),
            "san_he": interactions.get("三合", []),
            "ban_san_he": interactions.get("半三合", []),
            "san_hui": interactions.get("三会", []),
            "harms": interactions.get("害", []),
            "destructions": interactions.get("六破", []),
            "hidden_combinations": interactions.get("暗合", []),
            "arching_combinations": interactions.get("拱合", []),
            "xing": interactions.get("刑", []),
            "self_punishment": interactions.get("自刑", []),
        },
        "stem_interactions": {
            "combinations": stem_combos,
            "transformations": transformations,
            "jealous_combinations": jealous_combos,
            "restraints": stem_restraints,
            "clashes": stem_clashes,
        },
        "tomb_treasury": tomb_analysis,
        "punishments": punishments,
        "life_stages": life_stages,
        "nayin_analysis": nayin_analysis,
        "missing_elements": missing_elements,
        "competing_frames": competing_frames,
        "summary": " ".join(summary_parts),
    }

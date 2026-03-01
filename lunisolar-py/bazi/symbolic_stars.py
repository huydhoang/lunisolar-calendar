"""
Symbolic Stars (神煞) & Void Branches (空亡) — spec §IX, §X
============================================================
"""

from typing import Dict, List, Tuple

from .constants import (
    NOBLEMAN_TABLE, ACADEMIC_STAR_TABLE, PEACH_BLOSSOM_TABLE,
    TRAVEL_HORSE_TABLE, GENERAL_STAR_TABLE, CANOPY_STAR_TABLE,
    GOAT_BLADE_TABLE, PROSPERITY_STAR_TABLE, RED_CLOUD_TABLE,
    BLOOD_KNIFE_TABLE, VOID_BRANCH_TABLE, XUN_NAMES,
)
from .core import _cycle_from_stem_branch


def void_branches(day_cycle: int) -> Tuple[str, str]:
    """Return the two void branches for a given day pillar cycle number."""
    xun_index = (day_cycle - 1) // 10
    return VOID_BRANCH_TABLE.get(xun_index, ("", ""))


def xun_name(day_cycle: int) -> str:
    """Return the Xun (旬) name for a given day pillar cycle number."""
    xun_index = (day_cycle - 1) // 10
    return XUN_NAMES.get(xun_index, "")


def void_in_pillars(chart: Dict) -> Dict[str, bool]:
    """Check which natal pillars have void branches."""
    day_cycle = _cycle_from_stem_branch(
        chart["pillars"]["day"]["stem"], chart["pillars"]["day"]["branch"]
    )
    void1, void2 = void_branches(day_cycle)
    result: Dict[str, bool] = {}
    for pname, p in chart["pillars"].items():
        result[pname] = p["branch"] in (void1, void2)
    return result


def detect_symbolic_stars(chart: Dict) -> List[Dict]:
    """Detect all symbolic stars in the natal chart."""
    results: List[Dict] = []
    dm_stem = chart["day_master"]["stem"]
    year_branch = chart["pillars"]["year"]["branch"]
    day_branch = chart["pillars"]["day"]["branch"]

    for pname, p in chart["pillars"].items():
        branch = p["branch"]

        if branch in NOBLEMAN_TABLE.get(dm_stem, []):
            results.append({
                "star": "天乙贵人 (Nobleman)", "star_en": "Nobleman",
                "location": pname, "nature": "auspicious",
                "description": "Help from influential people, success in endeavors.",
            })

        if branch == ACADEMIC_STAR_TABLE.get(dm_stem):
            results.append({
                "star": "文昌 (Academic Star)", "star_en": "Academic",
                "location": pname, "nature": "auspicious",
                "description": "Intelligence, exam success, literary talent.",
            })

        pb_year = PEACH_BLOSSOM_TABLE.get(year_branch, "")
        pb_day = PEACH_BLOSSOM_TABLE.get(day_branch, "")
        if branch == pb_year:
            results.append({
                "star": "桃花 (Peach Blossom)", "star_en": "Peach Blossom",
                "location": pname, "nature": "mixed", "source": "year branch",
                "description": "Romance, charm, social popularity. Also risk of romantic entanglements.",
            })
        if branch == pb_day:
            results.append({
                "star": "桃花 (Peach Blossom)", "star_en": "Peach Blossom",
                "location": pname, "nature": "mixed", "source": "day branch",
                "description": "Romance, charm, social popularity (from day branch).",
            })

        th_year = TRAVEL_HORSE_TABLE.get(year_branch, "")
        th_day = TRAVEL_HORSE_TABLE.get(day_branch, "")
        if branch == th_year or branch == th_day:
            results.append({
                "star": "驿马 (Travel Horse)", "star_en": "Travel Horse",
                "location": pname, "nature": "neutral",
                "description": "Movement, travel, relocation, career changes.",
            })

        gen_year = GENERAL_STAR_TABLE.get(year_branch, "")
        gen_day = GENERAL_STAR_TABLE.get(day_branch, "")
        if branch == gen_year or branch == gen_day:
            results.append({
                "star": "将星 (General Star)", "star_en": "General",
                "location": pname, "nature": "auspicious",
                "description": "Leadership ability, authority, power.",
            })

        cap_year = CANOPY_STAR_TABLE.get(year_branch, "")
        cap_day = CANOPY_STAR_TABLE.get(day_branch, "")
        if branch == cap_year or branch == cap_day:
            results.append({
                "star": "华盖 (Canopy Star)", "star_en": "Canopy",
                "location": pname, "nature": "mixed",
                "description": "Spirituality, artistic talent, solitude, introspection.",
            })

        if branch == GOAT_BLADE_TABLE.get(dm_stem):
            results.append({
                "star": "羊刃 (Goat Blade)", "star_en": "Goat Blade",
                "location": pname, "nature": "inauspicious",
                "description": "Courage but risk of violence, accidents, or surgery.",
            })

        if branch == PROSPERITY_STAR_TABLE.get(dm_stem):
            results.append({
                "star": "禄神 (Prosperity Star)", "star_en": "Prosperity",
                "location": pname, "nature": "auspicious",
                "description": "Wealth, salary, career advancement.",
            })

        rc_year = RED_CLOUD_TABLE.get(year_branch, "")
        if branch == rc_year:
            results.append({
                "star": "红鸾 (Red Cloud)", "star_en": "Red Cloud",
                "location": pname, "nature": "mixed",
                "description": "Romance, marriage prospects, emotional intensity.",
            })

        bk_day = BLOOD_KNIFE_TABLE.get(day_branch, "")
        if branch == bk_day:
            results.append({
                "star": "血刃 (Blood Knife)", "star_en": "Blood Knife",
                "location": pname, "nature": "inauspicious",
                "description": "Risk of injury, surgery, or blood-related issues.",
            })

    # Void stars
    void1, void2 = void_branches(
        _cycle_from_stem_branch(
            chart["pillars"]["day"]["stem"], chart["pillars"]["day"]["branch"]
        )
    )
    for pname, p in chart["pillars"].items():
        if p["branch"] == void1 or p["branch"] == void2:
            results.append({
                "star": "空亡 (Void)", "star_en": "Void",
                "location": pname, "nature": "inauspicious",
                "description": "Reduced influence, plans may not materialize easily.",
            })

    # Deduplicate
    unique_results = []
    seen = set()
    for r in results:
        key = (r["star"], r["location"])
        if key not in seen:
            seen.add(key)
            unique_results.append(r)

    return unique_results


def get_void_branches_for_chart(chart: Dict) -> set:
    """Return the set of void branches for this chart's day pillar."""
    day_cycle = _cycle_from_stem_branch(
        chart["pillars"]["day"]["stem"], chart["pillars"]["day"]["branch"]
    )
    v1, v2 = void_branches(day_cycle)
    return {v1, v2} - {""}


def apply_void_effects(chart: Dict, interactions: Dict) -> Dict:
    """Apply Void Branch (空亡) effects to interaction results.

    Void branches weaken combinations and clashes:
    - 六合 involving a void branch → tagged as weakened
    - 六冲 involving a void branch → tagged as weakened
    - 三合 with a void branch → frame weakened
    Non-void interactions are left unchanged.
    """
    void_set = get_void_branches_for_chart(chart)
    if not void_set:
        return interactions

    result = {}
    for key, items in interactions.items():
        new_items = []
        for item in items:
            if key in ("六合",) and isinstance(item, dict):
                pair = item.get("pair", ())
                if set(pair) & void_set:
                    item = dict(item)
                    item["void_weakened"] = True
                    if item.get("confidence"):
                        item["confidence"] = max(item["confidence"] - 20, 10)
                new_items.append(item)
            elif key in ("六冲", "害", "六破", "暗合") and isinstance(item, tuple):
                if set(item) & void_set:
                    new_items.append({"pair": item, "void_weakened": True})
                else:
                    new_items.append(item)
            elif key in ("三合",) and isinstance(item, dict):
                trio = item.get("trio", frozenset())
                if set(trio) & void_set:
                    item = dict(item)
                    item["void_weakened"] = True
                    if item.get("confidence"):
                        item["confidence"] = max(item["confidence"] - 15, 10)
                new_items.append(item)
            else:
                new_items.append(item)
        result[key] = new_items

    return result

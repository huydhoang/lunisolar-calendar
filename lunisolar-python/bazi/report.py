"""
Markdown Report Builder (NEW — plan §3)
========================================
Generates a complete Bazi chart analysis as a Markdown document.
"""

from typing import Dict, List, Optional

from .terminology import format_term
from .constants import HEAVENLY_STEMS, STEM_POLARITY
from .ten_gods import ten_god


def generate_report_markdown(
    chart: Dict,
    dto,
    *,
    score: float,
    strength: str,
    structure_dict: Dict,
    useful: Dict,
    tg_dist: Dict[str, float],
    interactions: Dict,
    stem_combos: List[Dict],
    transformations: List[Dict],
    punishments: List[Dict],
    symbolic_stars: List[Dict],
    nayin_analysis: Dict,
    life_stages: Dict,
    void_status: Dict,
    luck: List[Dict],
    rating: int,
    narrative: str,
    year_projections: Optional[List[Dict]] = None,
    month_projections: Optional[List[Dict]] = None,
    day_projections: Optional[List[Dict]] = None,
    use_new_moons: bool = False,
    solar_date: Optional[str] = None,
    solar_time: Optional[str] = None,
) -> str:
    """Build a complete Markdown report string."""
    dm = chart["day_master"]
    gender = chart.get("gender", "male")
    pillar_order = ["year", "month", "day", "hour"]
    pillar_labels = {
        "year": "年 Year",
        "month": "月 Month",
        "day": "日 Day",
        "hour": "时 Hour",
    }

    lines: List[str] = []
    _a = lines.append

    birth_label = solar_date or getattr(dto, 'solar_date', None) or 'N/A'
    if solar_time:
        birth_label = f"{birth_label} {solar_time}"
    _a("# BAZI (四柱八字) COMPREHENSIVE CHART REPORT\n")
    _a(f"**Birth Data:** {birth_label} | Gender: {gender}  ")
    if hasattr(dto, "year"):
        leap = " (leap)" if dto.is_leap_month else ""
        _a(f"**Lunar:** Year {dto.year} | Month {dto.month}{leap} | Day {dto.day}\n")

    # Day Master
    _a("## Day Master (日元)\n")
    _a(f"| Property | Value |")
    _a(f"|----------|-------|")
    _a(f"| Stem | {format_term(dm['stem'])} ({STEM_POLARITY[dm['stem']]}) |")
    _a(f"| Element | {dm['element']} |")
    _a(f"| Strength | {score} pts → **{strength.upper()}** |")
    _a("")

    # Four Pillars
    _a("## Four Pillars (四柱)\n")
    _a("| Pillar | GanZhi | Ten-God | Life Stage | Na Yin | Void |")
    _a("|--------|--------|---------|------------|--------|------|")
    dm_idx = HEAVENLY_STEMS.index(dm["stem"])
    for pname in pillar_order:
        p = chart["pillars"][pname]
        ls = life_stages[pname]
        ganzhi = format_term(p["stem"] + p["branch"])
        tg_fmt = format_term(p["ten_god"])
        ls_fmt = format_term(ls["chinese"])
        nayin_str = p.get("nayin", {}).get("chinese", "-") if "nayin" in p else "-"
        void_mark = "VOID" if void_status.get(pname) else ""
        _a(f"| {pillar_labels[pname]} | {ganzhi} | {tg_fmt} | {ls_fmt} | {nayin_str} | {void_mark} |")
    _a("")

    # Hidden Stems
    _a("### Hidden Stems (藏干)\n")
    for pname in pillar_order:
        p = chart["pillars"][pname]
        hidden_strs = []
        for role, hstem in p["hidden"]:
            tg_val = ten_god(dm_idx, HEAVENLY_STEMS.index(hstem))
            hidden_strs.append(f"{role}:{format_term(hstem)} ({format_term(tg_val)})")
        _a(f"- **{pillar_labels[pname]}**: {', '.join(hidden_strs)}")
    _a("")

    # Structure
    _a("## Chart Structure (格局)\n")
    structure_primary = structure_dict.get("primary", "Unknown")
    structure_quality = structure_dict.get("quality", "Unknown")
    dominance = float(structure_dict.get("dominance_score", 0.0))
    _a(f"- **Basic**: {structure_primary}")
    _a(f"- **Quality**: {structure_quality} (dominance = {dominance:.1f})")
    useful_str = ", ".join(useful.get("favorable", [])) or "None"
    avoid_str = ", ".join(useful.get("avoid", [])) or "None"
    _a(f"- **Favorable**: {useful_str}")
    _a(f"- **Avoid**: {avoid_str}")
    if "useful_god" in useful:
        _a(f"- **Useful God**: {useful.get('useful_god', 'N/A')}")
        _a(f"- **Joyful God**: {useful.get('joyful_god', 'N/A')}")
    _a("")

    # Ten-God Distribution
    _a("## Ten-God Distribution (十神分布)\n")
    _a("| Ten-God | Score |")
    _a("|---------|-------|")
    for tg_name, tg_score in sorted(tg_dist.items(), key=lambda x: x[1], reverse=True):
        _a(f"| {format_term(tg_name)} | {tg_score:.1f} |")
    _a("")

    # Branch Interactions
    _a("## Branch Interactions (地支关系)\n")
    active = {k: v for k, v in interactions.items() if v}
    if active:
        for kind, entries in active.items():
            formatted = []
            for e in entries:
                if isinstance(e, dict):
                    formatted.append(str(e))
                elif isinstance(e, (tuple, frozenset, set)):
                    formatted.append(f"({', '.join(format_term(b) for b in e)})")
                else:
                    formatted.append(format_term(str(e)))
            _a(f"- **{format_term(kind)}**: {', '.join(formatted)}")
    else:
        _a("None detected.")

    if stem_combos:
        _a("\n### Stem Combinations (天干合)\n")
        for sc in stem_combos:
            _a(f"- {sc['stems'][0]}+{sc['stems'][1]} → {sc['target_element']}")

    if transformations:
        _a("\n### Transformations (合化)\n")
        for t in transformations:
            _a(f"- {t['stems'][0]}+{t['stems'][1]} → {t['target_element']}: {t['status']} ({t['confidence']}%)")

    if punishments:
        _a("\n### Punishments & Harms (刑害)\n")
        for p in punishments:
            _a(f"- {p['type']}: {p['branches']} ({p['life_areas']})")
    _a("")

    # Symbolic Stars
    _a("## Symbolic Stars (神煞)\n")
    if symbolic_stars:
        for star in symbolic_stars:
            nature_icon = {"auspicious": "✦", "inauspicious": "⚠"}.get(star["nature"], "◆")
            star_fmt = format_term(star["star"].split(" ")[0])
            _a(f"- {nature_icon} **{star_fmt}** @ {star['location']}: {star['description']}")
    else:
        _a("None detected.")
    _a("")

    # Na Yin
    _a("## Na Yin Interactions (納音)\n")
    if nayin_analysis.get("pillar_nayins"):
        for pname in pillar_order:
            if pname in nayin_analysis["pillar_nayins"]:
                ny = nayin_analysis["pillar_nayins"][pname]
                _a(f"- **{pillar_labels[pname]}**: {ny['nayin_chinese']} ({ny['nayin_element']})")
    _a("")

    # Life Stages
    _a("## Life Stages (十二长生)\n")
    _a("| Pillar | Stage | Class |")
    _a("|--------|-------|-------|")
    for pname in pillar_order:
        ls = life_stages[pname]
        _a(f"| {pillar_labels[pname]} | {format_term(ls['chinese'])} | {ls['strength_class']} |")
    _a("")

    # Luck Pillars
    _a("## Luck Pillars (大运)\n")
    _a("| # | GanZhi | Ten-God | Life Stage | Na Yin | Age |")
    _a("|---|--------|---------|------------|--------|-----|")
    for i, lp in enumerate(luck, 1):
        ganzhi = format_term(lp["stem"] + lp["branch"])
        lsd = lp.get("life_stage_detail", {})
        ls_name = format_term(lsd.get("chinese", "")) if lsd.get("chinese") else ""
        tg_fmt = format_term(lp.get("ten_god", "")) if lp.get("ten_god") else ""
        ny = lp.get("nayin", {})
        ny_str = ny.get("chinese", "") if ny else ""
        age_info = ""
        if "start_age" in lp:
            ay, am = lp["start_age"]
            age_info = f"{ay}y {am}m"
            if "start_gregorian_year" in lp:
                age_info += f" (~{lp['start_gregorian_year']})"
        _a(f"| {i} | {ganzhi} | {tg_fmt} | {ls_name} | {ny_str} | {age_info} |")
    _a("")

    # Rating
    _a("## Chart Rating (综合评分)\n")
    _a(f"**{rating} / 100**\n")

    # Narrative
    _a("## Narrative Interpretation (命理解读)\n")
    for line in narrative.splitlines():
        _a(line)
    _a("")

    # Projections
    if year_projections:
        _a("## 10-Year Lookahead (十年展望)\n")
        _a("| Year | GanZhi | Ten-God | Life Stage | Interactions | Δ |")
        _a("|------|--------|---------|------------|-------------|---|")
        for yp in year_projections:
            inter_str = ", ".join(format_term(x) for x in yp["interactions"]) if yp["interactions"] else "-"
            delta = yp["strength_delta"]
            delta_str = f"+{delta}" if delta > 0 else str(delta)
            ls = yp["life_stage"]
            _a(f"| {yp['year']} | {format_term(yp['ganzhi'])} | {format_term(yp['ten_god'])} | {format_term(ls.get('chinese', ''))} | {inter_str} | {delta_str} |")
        _a("")

    if month_projections:
        title = "36 New Moons Lookahead" if use_new_moons else "Month Lookahead"
        _a(f"## {title}\n")
        _a("| # | Date | GanZhi | Ten-God | Interactions | Δ |")
        _a("|---|------|--------|---------|-------------|---|")
        for mp in month_projections:
            inter_str = ", ".join(format_term(x) for x in mp["interactions"]) if mp["interactions"] else "-"
            delta = mp["strength_delta"]
            delta_str = f"+{delta}" if delta > 0 else str(delta)
            _a(f"| {mp['month_num']} | {mp['solar_date']} | {format_term(mp['ganzhi'])} | {format_term(mp['ten_god'])} | {inter_str} | {delta_str} |")
        _a("")

    if day_projections:
        notable = [dp for dp in day_projections if dp["interactions"] or dp["strength_delta"] != 0]
        if notable:
            _a("## Notable Days\n")
            _a("| Date | Day | GanZhi | Ten-God | Interactions | Δ |")
            _a("|------|-----|--------|---------|-------------|---|")
            for dp in notable[:30]:
                inter_str = ", ".join(format_term(x) for x in dp["interactions"]) if dp["interactions"] else "-"
                delta = dp["strength_delta"]
                delta_str = f"+{delta}" if delta > 0 else str(delta)
                _a(f"| {dp['date']} | {dp['weekday']} | {format_term(dp['ganzhi'])} | {format_term(dp['ten_god'])} | {inter_str} | {delta_str} |")
            _a("")

    return "\n".join(lines)

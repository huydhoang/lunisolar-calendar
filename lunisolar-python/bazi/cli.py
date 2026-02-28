"""
CLI entry point for ``python -m bazi``
=======================================
"""

import argparse
from datetime import date, datetime, timedelta
from typing import Optional

try:
    from datetime import UTC as utc
except ImportError:
    from datetime import timezone
    utc = timezone.utc

from lunisolar_v2 import solar_to_lunisolar

from . import terminology
from .constants import HEAVENLY_STEMS, STEM_POLARITY
from .core import build_chart
from .ten_gods import ten_god, weighted_ten_god_distribution
from .longevity import longevity_map, life_stages_for_chart
from .nayin import analyze_nayin_interactions
from .scoring import score_day_master, rate_chart, recommend_useful_god
from .branch_interactions import detect_branch_interactions
from .stem_transformations import detect_stem_combinations, detect_transformations
from .punishments import detect_punishments
from .symbolic_stars import detect_symbolic_stars, void_in_pillars, void_branches, xun_name
from .structure import classify_structure
from .luck_pillars import (
    _luck_direction, find_governing_jie_term, generate_luck_pillars,
)
from .analysis import comprehensive_analysis
from .narrative import generate_narrative
from .projections import generate_year_projections, generate_month_projections, generate_day_projections
from .report import generate_report_markdown
from .terminology import format_term


def main() -> None:
    parser = argparse.ArgumentParser(description="Bazi (Four Pillars) chart analysis")
    parser.add_argument("-d", "--date", required=True, help="Solar date (YYYY-MM-DD)")
    parser.add_argument(
        "-t", "--time", default="12:00", help="Solar time (HH:MM, default 12:00)"
    )
    parser.add_argument("-g", "--gender", required=True, help="Gender (male/female)")
    parser.add_argument("--proj-start", help="Start date for projections (YYYY-MM-DD).")
    parser.add_argument("--proj-end", help="End date for projections (YYYY-MM-DD).")
    parser.add_argument(
        "-f", "--format", default="cn/py",
        help="Format string for Chinese terminology.",
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Write Markdown report to this file path.",
    )
    args = parser.parse_args()

    # Update global formatting preference
    terminology.FORMAT_STRING = args.format

    solar_date = args.date
    solar_time = args.time
    gender = args.gender

    dto = solar_to_lunisolar(solar_date, solar_time, quiet=True)
    chart = build_chart(
        dto.year_cycle, dto.month_cycle, dto.day_cycle, dto.hour_cycle, gender
    )

    score, strength = score_day_master(chart)
    interactions = detect_branch_interactions(chart)
    structure_dict = classify_structure(chart, strength)
    useful = recommend_useful_god(chart, strength, structure_dict)
    rating = rate_chart(chart)
    narrative = generate_narrative(chart, strength, structure_dict, interactions)
    lmap = longevity_map(chart)
    tg_dist = weighted_ten_god_distribution(chart)
    comprehensive = comprehensive_analysis(chart)
    symbolic_stars = detect_symbolic_stars(chart)
    void_status = void_in_pillars(chart)
    stem_combos = detect_stem_combinations(chart)
    transformations = detect_transformations(chart)
    punishments = detect_punishments(chart)
    nayin_data = analyze_nayin_interactions(chart)
    life_stages = life_stages_for_chart(chart)

    # Luck pillars
    try:
        birth_dt = datetime.strptime(
            f"{solar_date} {solar_time}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=utc)
        forward = _luck_direction(chart)
        target_term_dt = find_governing_jie_term(birth_dt, forward)

        if target_term_dt:
            luck = generate_luck_pillars(
                chart,
                birth_year=birth_dt.year,
                birth_date=birth_dt.date(),
                solar_term_date=target_term_dt.date(),
            )
        else:
            luck = generate_luck_pillars(chart, birth_year=dto.year)
    except Exception:
        luck = generate_luck_pillars(chart, birth_year=dto.year)

    # Projections
    try:
        proj_start = (
            datetime.strptime(args.proj_start, "%Y-%m-%d").date()
            if args.proj_start else date.today()
        )
    except Exception:
        proj_start = date.today()

    try:
        proj_end = (
            datetime.strptime(args.proj_end, "%Y-%m-%d").date()
            if args.proj_end else None
        )
    except Exception:
        proj_end = None

    end_year = proj_end.year if proj_end else proj_start.year + 9
    year_projections = generate_year_projections(chart, proj_start.year, end_year)
    use_new_moons = proj_end is None
    month_projections = generate_month_projections(
        chart, proj_start, proj_end, use_new_moons=use_new_moons
    )
    day_projections = generate_day_projections(chart, proj_start, proj_end)

    # Generate Markdown report if output requested
    if args.output:
        md = generate_report_markdown(
            chart, dto,
            score=score,
            strength=strength,
            structure_dict=structure_dict,
            useful=useful,
            tg_dist=tg_dist,
            interactions=interactions,
            stem_combos=stem_combos,
            transformations=transformations,
            punishments=punishments,
            symbolic_stars=symbolic_stars,
            nayin_analysis=nayin_data,
            life_stages=life_stages,
            void_status=void_status,
            luck=luck,
            rating=rating,
            narrative=narrative,
            year_projections=year_projections,
            month_projections=month_projections,
            day_projections=day_projections,
            use_new_moons=use_new_moons,
            solar_date=solar_date,
            solar_time=solar_time,
        )
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Report written to {args.output}")
        return

    # Console output (preserves original terminal report)
    _print_console_report(
        chart, dto,
        score=score, strength=strength,
        structure_dict=structure_dict, useful=useful,
        tg_dist=tg_dist, interactions=interactions,
        stem_combos=stem_combos, transformations=transformations,
        punishments=punishments, symbolic_stars=symbolic_stars,
        nayin_analysis=nayin_data, life_stages=life_stages,
        void_status=void_status, luck=luck, rating=rating,
        narrative=narrative,
        year_projections=year_projections,
        month_projections=month_projections,
        day_projections=day_projections,
        proj_start=proj_start, proj_end=proj_end,
        use_new_moons=use_new_moons,
    )


def _print_console_report(
    chart, dto, *, score, strength, structure_dict, useful, tg_dist,
    interactions, stem_combos, transformations, punishments,
    symbolic_stars, nayin_analysis, life_stages, void_status, luck,
    rating, narrative, year_projections, month_projections,
    day_projections, proj_start, proj_end, use_new_moons,
):
    """Print the original-style terminal report."""
    dm = chart["day_master"]
    gender = chart.get("gender", "male")
    pillar_order = ["year", "month", "day", "hour"]
    pillar_labels = {
        "year": "年 Year", "month": "月 Month",
        "day": "日 Day", "hour": "时 Hour",
    }
    dm_idx = HEAVENLY_STEMS.index(dm["stem"])

    SEP = "=" * 70
    print(SEP)
    print("  BAZI (四柱八字) COMPREHENSIVE CHART REPORT")
    print(SEP)
    print(f"\n  Birth Data: {dto.solar_date if hasattr(dto, 'solar_date') else 'N/A'} | Gender: {gender}")
    if hasattr(dto, "year"):
        print(
            f"  Lunar Year: {dto.year} | Month: {dto.month}"
            f"{' (leap)' if dto.is_leap_month else ''} | Day: {dto.day} | Hour: {dto.hour}"
        )

    print(f"\n{'─' * 70}")
    print("[ Day Master (日元) ]")
    print(f"  Stem    : {format_term(dm['stem'])} ({STEM_POLARITY[dm['stem']]})")
    print(f"  Element : {dm['element']}")
    print(f"  Strength: {score} pts → {strength.upper()}")

    from .symbolic_stars import void_branches, xun_name
    from .core import _cycle_from_stem_branch
    day_cycle = _cycle_from_stem_branch(
        chart["pillars"]["day"]["stem"], chart["pillars"]["day"]["branch"]
    )
    void1, void2 = void_branches(day_cycle)
    print(f"  Xun     : {xun_name(day_cycle)}")
    print(f"  Void    : {format_term(void1)}, {format_term(void2)}")

    print(f"\n{'─' * 70}")
    print("[ Four Pillars (四柱) ]")
    header = f"  {'Pillar':<12} {'GanZhi':<6} {'Ten-God':<8} {'Life Stage':<16} {'Na Yin':<16}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for pname in pillar_order:
        p = chart["pillars"][pname]
        ls = life_stages[pname]
        nayin_str = p.get("nayin", {}).get("chinese", "-") if "nayin" in p else "-"
        void_mark = " [VOID]" if void_status.get(pname) else ""
        ganzhi_fmt = format_term(p["stem"] + p["branch"])
        print(
            f"  {pillar_labels[pname]:<12} {ganzhi_fmt:<35} {format_term(p['ten_god']):<30} "
            f"{format_term(ls['chinese']):<35} {nayin_str}{void_mark}"
        )

    print("\n  Hidden Stems (藏干) with Ten-Gods:")
    for pname in pillar_order:
        p = chart["pillars"][pname]
        hidden_strs = []
        for role, hstem in p["hidden"]:
            tg = ten_god(dm_idx, HEAVENLY_STEMS.index(hstem))
            hidden_strs.append(f"{role}:{format_term(hstem)} ({format_term(tg)})")
        print(f"    {pillar_labels[pname]:<10}: {', '.join(hidden_strs)}")

    print(f"\n{'─' * 70}")
    print("[ Chart Structure (格局) ]")
    print(f"  Basic        : {structure_dict.get('primary', 'Unknown')}")
    print(f"  Quality      : {structure_dict.get('quality', 'Unknown')}  (dominance score = {float(structure_dict.get('dominance_score', 0)):.1f})")
    useful_str = ", ".join(useful["favorable"]) if useful["favorable"] else "None"
    avoid_str = ", ".join(useful["avoid"]) if useful["avoid"] else "None"
    print(f"  Favorable    : {useful_str}")
    print(f"  Avoid        : {avoid_str}")
    if "useful_god" in useful:
        print(f"  Useful God   : {useful.get('useful_god', 'N/A')}")
        print(f"  Joyful God   : {useful.get('joyful_god', 'N/A')}")

    print(f"\n{'─' * 70}")
    print("[ Ten-God Distribution (十神分布, weighted) ]")
    for tg_name, tg_score in sorted(tg_dist.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(tg_score)
        print(f"  {format_term(tg_name):<35} {tg_score:>5.1f}  {bar}")

    print(f"\n{'─' * 70}")
    print("[ Branch Interactions (地支关系) ]")
    active = {k: v for k, v in interactions.items() if v}
    if active:
        for kind, entries in active.items():
            formatted_entries = []
            for e in entries:
                if isinstance(e, dict):
                    if "pattern" in e:
                        formatted_entries.append(f"{list(e['pattern'])} (match: {e['found']})")
                    elif "branch" in e:
                        formatted_entries.append(f"{e['branch']} (count: {e['count']})")
                    else:
                        formatted_entries.append(str(e))
                elif isinstance(e, (tuple, frozenset, set)):
                    formatted_entries.append(f"({', '.join(format_term(b) for b in e)})")
                else:
                    formatted_entries.append(format_term(str(e)))
            print(f"  {format_term(kind)}: {formatted_entries}")
    else:
        print("  None detected.")

    if stem_combos:
        print("\n  Stem Combinations (天干合):")
        for sc in stem_combos:
            print(f"    {sc['stems'][0]}+{sc['stems'][1]} → {sc['target_element']} ({sc['pair'][0]}-{sc['pair'][1]})")

    if transformations:
        print("\n  Transformations (合化):")
        for t in transformations:
            print(f"    {t['stems'][0]}+{t['stems'][1]} → {t['target_element']}: {t['status']} ({t['confidence']}%)")

    if punishments:
        print("\n  Punishments & Harms (刑害):")
        for p in punishments:
            print(f"    {p['type']}: {p['branches']} ({p['life_areas']})")

    print(f"\n{'─' * 70}")
    print("[ Symbolic Stars (神煞) ]")
    if symbolic_stars:
        for star in symbolic_stars:
            nature_icon = "✦" if star["nature"] == "auspicious" else ("⚠" if star["nature"] == "inauspicious" else "◆")
            star_fmt = format_term(star["star"].split(" ")[0])
            print(f"  {nature_icon} {star_fmt} @ {star['location']}: {star['description']}")
    else:
        print("  None detected.")

    print(f"\n{'─' * 70}")
    print("[ Na Yin Interactions (納音) ]")
    if nayin_analysis.get("pillar_nayins"):
        print("  Pillar Na Yin:")
        for pname in pillar_order:
            if pname in nayin_analysis["pillar_nayins"]:
                ny = nayin_analysis["pillar_nayins"][pname]
                print(f"    {pillar_labels[pname]:<10}: {ny['nayin_chinese']} ({ny['nayin_element']})")
    if nayin_analysis.get("vs_day_master"):
        print("  vs Day Master:")
        for pname, vs in nayin_analysis["vs_day_master"].items():
            print(f"    {pillar_labels[pname]:<10}: {vs['nayin_element']} ({vs['relation_to_dm']})")

    print(f"\n{'─' * 70}")
    print("[ Life Stages Detail (十二长生) ]")
    for pname in pillar_order:
        ls = life_stages[pname]
        print(f"  {pillar_labels[pname]:<10}: ({ls['index']:>2}) {format_term(ls['chinese'])} [{ls['strength_class']}]")

    print(f"\n{'─' * 70}")
    print("[ Luck Pillars (大运) ]")
    from .luck_pillars import _luck_direction
    direction = "forward ▶" if _luck_direction(chart) else "backward ◀"
    print(f"  Direction: {direction} | Count: {len(luck)}")
    for i, lp in enumerate(luck, 1):
        ganzhi_fmt = format_term(lp["stem"] + lp["branch"])
        lsd = lp.get("life_stage_detail", {})
        ls_name = lsd.get("chinese", "")
        tg = lp.get("ten_god", "")
        ny = lp.get("nayin", {})
        ny_str = ny.get("chinese", "") if ny else ""
        age_info = ""
        if "start_age" in lp:
            ay, am = lp["start_age"]
            age_info = f"  age {ay}y {am}m"
            if "start_gregorian_year" in lp:
                age_info += f" (~{lp['start_gregorian_year']})"
        ls_fmt = format_term(ls_name) if ls_name else ""
        tg_fmt = format_term(tg) if tg else ""
        print(f"  {i:2}. {ganzhi_fmt:<30} | Ten-God: {tg_fmt:<30} | Life: {ls_fmt:<30} | Na Yin: {ny_str:<12}{age_info}")

    print(f"\n{'─' * 70}")
    print("[ Chart Rating (综合评分) ]")
    bar_filled = "█" * (rating // 5)
    bar_empty = "░" * (20 - rating // 5)
    print(f"  {rating} / 100  [{bar_filled}{bar_empty}]")

    print(f"\n{'─' * 70}")
    print("[ Narrative Interpretation (命理解读) ]")
    for line in narrative.splitlines():
        print(f"  {line}")

    # Projections
    print(f"\n{'=' * 70}")
    print("  PROJECTION VIEWS (运程展望)")
    print(f"  Start: {proj_start}  |  End: {proj_end if proj_end else 'Default'}")
    print(f"{'=' * 70}")

    print(f"\n{'─' * 70}")
    print("[ 10-Year Lookahead (十年展望) ]")
    hdr_yr = f"  {'Year':<6} {'GanZhi':<20} {'Ten-God':<20} {'Life Stage':<20} {'Int':<15} {'Δ':<3}"
    print(hdr_yr)
    print("  " + "-" * (len(hdr_yr) - 2))
    for yp in year_projections:
        interactions_str = ", ".join(format_term(x) for x in yp["interactions"]) if yp["interactions"] else "-"
        delta = yp["strength_delta"]
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        ls = yp["life_stage"]
        ls_fmt = format_term(ls.get("chinese", ""))
        ls_strength = ls.get("strength_class", "")
        ganzhi_fmt = format_term(yp["ganzhi"])
        tg_fmt = format_term(yp["ten_god"])
        print(f"  {yp['year']:<6} {ganzhi_fmt:<20} {tg_fmt:<20} {ls_fmt:<15} [{ls_strength:<5}]  {interactions_str:<15} {delta_str:<3}")

    print(f"\n{'─' * 70}")
    title = "[ 36 New Moons Lookahead (三十六朔展望) ]" if use_new_moons else "[ Month Lookahead (月展望) ]"
    print(title)
    _lunar_hdr = f" {'Lunar Date':<22}" if use_new_moons else ""
    hdr_mo = (
        f"  {'#':>2}  {'Solar Date':<13}" + _lunar_hdr
        + f" {'GanZhi':<20} {'Ten-God':<20} {'Life Stage':<20} {'Int':<15} {'Δ':<3}"
    )
    print(hdr_mo)
    print("  " + "-" * (len(hdr_mo) - 2))
    for mp in month_projections:
        interactions_str = ", ".join(format_term(x) for x in mp["interactions"]) if mp["interactions"] else "-"
        delta = mp["strength_delta"]
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        ls = mp["life_stage"]
        ls_fmt = format_term(ls.get("chinese", ""))
        ls_strength = ls.get("strength_class", "")
        ganzhi_fmt = format_term(mp["ganzhi"])
        tg_fmt = format_term(mp["ten_god"])
        lunar_col = ""
        if use_new_moons and "lunisolar_date" in mp:
            ly, lm, ld, _is_leap, leap_tag = mp["lunisolar_date"]
            lunar_col = f"(Lunar {ly}/{lm}{leap_tag} d{ld:<2}) "
        print(
            f"  {mp['month_num']:>2}.  {mp['solar_date']:<13}"
            + (f" {lunar_col:<23}" if use_new_moons else "")
            + f" {ganzhi_fmt:<20} {tg_fmt:<20} {ls_fmt:<15} [{ls_strength:<5}]  {interactions_str:<15} {delta_str:<3}"
        )

    print(f"\n{'─' * 70}")
    title = "[ Day Lookahead (日展望) ]" if proj_end else "[ 100-Day Lookahead (百日展望) ]"
    print(title)
    notable_days = [dp for dp in day_projections if dp["interactions"] or dp["strength_delta"] != 0]
    print("  Showing days with interactions or strength impact (filtered):")
    hdr_dy = f"  {'Date':<12} {'Day':<5} {'GanZhi':<20} {'Ten-God':<20} {'Life Stage':<15} {'Int':<15} {'Δ':<3}"
    print(hdr_dy)
    print("  " + "-" * (len(hdr_dy) - 2))
    if notable_days:
        for dp in notable_days[:30]:
            interactions_str = ", ".join(format_term(x) for x in dp["interactions"]) if dp["interactions"] else "-"
            delta = dp["strength_delta"]
            delta_str = f"+{delta}" if delta > 0 else str(delta)
            ls = dp["life_stage"]
            ls_fmt = format_term(ls.get("chinese", ""))
            ls_strength = ls.get("strength_class", "")
            ganzhi_fmt = format_term(dp["ganzhi"])
            tg_fmt = format_term(dp["ten_god"])
            print(f"  {dp['date']:<12} ({dp['weekday']:<3}) {ganzhi_fmt:<20} {tg_fmt:<20} {ls_fmt:<15} [{ls_strength:<5}]  {interactions_str:<15} {delta_str:<3}")
        if len(notable_days) > 30:
            print(f"  ... and {len(notable_days) - 30} more notable days (use --full for all 100)")
    else:
        print("  No notable interactions in the next 100 days.")

    print(f"\n{SEP}")

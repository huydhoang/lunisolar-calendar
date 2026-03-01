"""
Markdown Report Builder (NEW — plan §3)
========================================
Generates a complete Bazi chart analysis as a Markdown document.
"""

from typing import Dict, List, Optional

from .terminology import format_term
from .constants import HEAVENLY_STEMS, STEM_POLARITY, BRANCH_ELEMENT
from .ten_gods import ten_god


# ── Formatting helpers ──────────────────────────────────────

def _fmt_branch_pair(pair) -> str:
    """Format a branch pair (tuple or frozenset) as readable."""
    if isinstance(pair, (tuple, list)):
        return f"{format_term(pair[0])}–{format_term(pair[1])}"
    if isinstance(pair, frozenset):
        items = sorted(pair)
        return f"{format_term(items[0])}–{format_term(items[1])}"
    return format_term(str(pair))


def _fmt_liu_he(item: Dict) -> str:
    """Format a 六合 rich-dict entry."""
    pair_str = _fmt_branch_pair(item.get("pair", ()))
    target = item.get("target_element", "?")
    status = item.get("status", "?")
    conf = item.get("confidence", 0)
    pillars = item.get("pillars", ())
    loc = f"{pillars[0]}↔{pillars[1]}" if len(pillars) == 2 else ""
    void = " `[VOID-weakened]`" if item.get("void_weakened") else ""
    return f"{pair_str} → {target} | {status} ({conf}%){void} [{loc}]"


def _fmt_san_he(item: Dict) -> str:
    """Format a 三合 rich-dict entry."""
    trio = item.get("trio", frozenset())
    branches = ", ".join(format_term(b) for b in sorted(trio))
    target = item.get("target_element", "?")
    status = item.get("status", "?")
    conf = item.get("confidence", 0)
    void = " `[VOID-weakened]`" if item.get("void_weakened") else ""
    return f"({branches}) → {target} | {status} ({conf}%){void}"


def _fmt_ban_san_he(item: Dict) -> str:
    """Format a 半三合 entry."""
    pair = item.get("pair", frozenset())
    branches = ", ".join(format_term(b) for b in sorted(pair))
    phase = item.get("phase", "?")
    target = item.get("target_element", "?")
    strength = item.get("strength", "")
    return f"({branches}) → {target} | {phase} ({strength})"


def _fmt_gong_he(item: Dict) -> str:
    """Format a 拱合 entry."""
    pair = item.get("pair", ())
    pair_str = _fmt_branch_pair(pair)
    missing = format_term(item.get("missing_middle", "?"))
    target = item.get("target_element", "?")
    return f"{pair_str} (missing {missing}) → {target}"


def _fmt_xing(item: Dict) -> str:
    """Format a 刑 punishment entry."""
    pattern = item.get("pattern", frozenset())
    branches = ", ".join(format_term(b) for b in sorted(pattern))
    mode = item.get("mode", "?")
    found = item.get("found", 0)
    return f"({branches}) — {mode} ({found} of {len(pattern)} found)"


def _fmt_self_xing(item: Dict) -> str:
    """Format a 自刑 entry."""
    branch = format_term(item.get("branch", "?"))
    count = item.get("count", 0)
    mode = item.get("mode", "?")
    return f"{branch} ×{count} — {mode}"


def _fmt_basic_pair(item, void_set=None) -> str:
    """Format a basic tuple/dict interaction entry, checking void."""
    if isinstance(item, dict):
        pair = item.get("pair", ())
        void = " `[VOID-weakened]`" if item.get("void_weakened") else ""
        return f"{_fmt_branch_pair(pair)}{void}"
    if isinstance(item, (tuple, frozenset)):
        return _fmt_branch_pair(item)
    return format_term(str(item))


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
    comprehensive: Optional[Dict] = None,
) -> str:
    """Build a complete Markdown report string.

    The *comprehensive* parameter accepts the output of ``comprehensive_analysis()``,
    enabling display of rooting, tomb/treasury, and stem interaction data.
    """
    dm = chart["day_master"]
    gender = chart.get("gender", "male")
    pillar_order = ["year", "month", "day", "hour"]
    pillar_labels = {
        "year": "年 Year",
        "month": "月 Month",
        "day": "日 Day",
        "hour": "时 Hour",
    }

    # Extract sub-dicts from comprehensive analysis if provided
    comp = comprehensive or {}
    rooting = comp.get("rooting", {})
    tomb_treasury = comp.get("tomb_treasury", [])
    stem_interactions = comp.get("stem_interactions", {})
    comp_structure = comp.get("structure", {})

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

    month_branch = chart["pillars"]["month"]["branch"]
    month_elem = BRANCH_ELEMENT[month_branch]
    _a(f"**Month Order:** {format_term(month_branch)} ({month_elem} season)\n")

    # ── Day Master ──────────────────────────────────────────
    _a("## Day Master (日元)\n")
    _a("| Property | Value |")
    _a("|----------|-------|")
    _a(f"| Stem | {format_term(dm['stem'])} ({STEM_POLARITY[dm['stem']]}) |")
    _a(f"| Element | {dm['element']} |")
    _a(f"| Strength | {score} pts → **{strength.upper()}** |")
    if rooting:
        root_cls = rooting.get("classification", "N/A")
        root_str = rooting.get("total_strength", 0)
        main_count = rooting.get("main_qi_roots", 0)
        _a(f"| Rooting | {root_cls} (strength {root_str}, {main_count} main-qi roots) |")
        if rooting.get("is_jian_lu"):
            _a("| 建禄 Jiàn Lù | ✦ Month branch is DM's Prosperity (禄) |")
        if rooting.get("is_yang_ren"):
            _a("| 羊刃 Yáng Rèn | ⚠ Month branch is DM's Goat Blade |")
    _a("")

    # ── Four Pillars ────────────────────────────────────────
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
        void_mark = "**VOID**" if void_status.get(pname) else ""
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

    # ── Structure ───────────────────────────────────────────
    _a("## Chart Structure (格局)\n")
    # Use comprehensive structure if available, fall back to passed dict
    sd = comp_structure if comp_structure else structure_dict
    structure_primary = sd.get("primary", structure_dict.get("primary", "Unknown"))
    structure_quality = sd.get("quality", structure_dict.get("quality", "Unknown"))
    dominance = float(sd.get("dominance_score", structure_dict.get("dominance_score", 0.0)))
    category = sd.get("category", structure_dict.get("category", ""))
    is_special = sd.get("is_special", structure_dict.get("is_special", False))
    is_broken = sd.get("is_broken", structure_dict.get("is_broken", False))
    composite = sd.get("composite", structure_dict.get("composite"))
    notes = sd.get("notes", structure_dict.get("notes", ""))

    _a(f"- **Primary**: {structure_primary}")
    if category:
        _a(f"- **Category**: {category}")
    _a(f"- **Quality**: {structure_quality} (dominance = {dominance:.1f})")
    if is_special:
        _a("- **Special structure** — takes precedence over regular structures")
    if is_broken:
        _a("- ⚠ **BROKEN structure** — structural integrity compromised")
    if composite:
        _a(f"- **Composite**: {composite}")
    if notes:
        _a(f"- *{notes}*")
    _a("")

    # ── Useful God (用神) ───────────────────────────────────
    _a("## Useful God Recommendation (用神)\n")
    useful_str = ", ".join(useful.get("favorable", [])) or "None"
    avoid_str = ", ".join(useful.get("avoid", [])) or "None"
    _a(f"- **Favorable elements**: {useful_str}")
    _a(f"- **Avoid elements**: {avoid_str}")
    if "useful_god" in useful:
        _a(f"- **用神 Useful God**: {useful['useful_god']}")
    if "joyful_god" in useful:
        _a(f"- **喜神 Joyful God**: {useful['joyful_god']}")
    if "structure" in useful:
        _a(f"- *Structure-aware: based on {useful['structure']}*")
    _a("")

    # ── Ten-God Distribution ────────────────────────────────
    _a("## Ten-God Distribution (十神分布)\n")
    _a("| Ten-God | Score |")
    _a("|---------|-------|")
    for tg_name, tg_score in sorted(tg_dist.items(), key=lambda x: x[1], reverse=True):
        _a(f"| {format_term(tg_name)} | {tg_score:.1f} |")
    _a("")

    # ── Branch Interactions ─────────────────────────────────
    _a("## Branch Interactions (地支关系)\n")

    # Ordered list of interaction types with labels and formatters
    INTERACTION_SPEC = [
        ("六合", "Six Combinations (六合)", _fmt_liu_he),
        ("六冲", "Six Clashes (六冲)", _fmt_basic_pair),
        ("三合", "Three Combinations (三合)", _fmt_san_he),
        ("半三合", "Half Three Combinations (半三合)", _fmt_ban_san_he),
        ("三会", "Directional Trinities (三会)", None),  # special handling
        ("害", "Six Harms (六害)", _fmt_basic_pair),
        ("六破", "Six Destructions (六破)", _fmt_basic_pair),
        ("暗合", "Hidden Combinations (暗合)", _fmt_basic_pair),
        ("拱合", "Arching Combinations (拱合)", _fmt_gong_he),
        ("刑", "Punishments (刑)", _fmt_xing),
        ("自刑", "Self-Punishment (自刑)", _fmt_self_xing),
    ]

    has_any = False
    for key, label, formatter in INTERACTION_SPEC:
        entries = interactions.get(key, [])
        if not entries:
            continue
        has_any = True
        _a(f"### {label}\n")
        for e in entries:
            if key == "三会":
                # frozenset of branches
                branches = ", ".join(format_term(b) for b in sorted(e))
                from .constants import SAN_HUI_ELEMENT
                elem = SAN_HUI_ELEMENT.get(e, "?") if isinstance(e, frozenset) else "?"
                _a(f"- ({branches}) → {elem}")
            elif formatter and isinstance(e, dict):
                _a(f"- {formatter(e)}")
            elif formatter:
                _a(f"- {formatter(e)}")
            elif isinstance(e, (tuple, frozenset)):
                _a(f"- {_fmt_branch_pair(e)}")
            else:
                _a(f"- {e}")
        _a("")
    if not has_any:
        _a("None detected.\n")

    # ── Stem Interactions ───────────────────────────────────
    _a("## Stem Interactions (天干关系)\n")

    # Combinations
    if stem_combos:
        _a("### Stem Combinations (天干合)\n")
        for sc in stem_combos:
            s1, s2 = sc["stems"]
            target = sc["target_element"]
            loc = f"{sc['pair'][0]}↔{sc['pair'][1]}" if "pair" in sc else ""
            _a(f"- {format_term(s1)}+{format_term(s2)} → {target} [{loc}]")
        _a("")

    # Transformations
    if transformations:
        _a("### Transformations (合化)\n")
        for t in transformations:
            s1, s2 = t["stems"]
            target = t["target_element"]
            status = t["status"]
            conf = t["confidence"]
            loc = f"{t['pair'][0]}↔{t['pair'][1]}" if "pair" in t else ""
            adj = "adjacent" if t.get("proximity_score", 0) >= 2 else "remote"
            month = "✓" if t.get("month_support") else "✗"
            leading = "✓" if t.get("leading_present") else "✗"
            blocked = "⚠ blocked" if t.get("blocked") else ""
            clashed = "⚠ severely clashed" if t.get("severely_clashed") else ""
            _a(f"- **{format_term(s1)}+{format_term(s2)} → {target}**: {status} ({conf}%) [{loc}]")
            flags = f"  {adj} | month-support: {month} | leading: {leading}"
            if blocked:
                flags += f" | {blocked}"
            if clashed:
                flags += f" | {clashed}"
            _a(f"  {flags}")
        _a("")

    # Jealous Combinations (from comprehensive)
    jealous = stem_interactions.get("jealous_combinations", [])
    if jealous:
        _a("### Jealous Combinations (争合)\n")
        for jc in jealous:
            contested = format_term(jc["contested_stem"])
            partner = format_term(jc["partner_stem"])
            target = jc["target_element"]
            count = jc["contested_count"]
            _a(f"- {contested} ×{count} contests with {partner} → {target}")
            _a(f"  *{jc.get('note', '')}*")
        _a("")

    # Stem Restraints (from comprehensive)
    restraints = stem_interactions.get("restraints", [])
    if restraints:
        _a("### Stem Restraints (天干相克)\n")
        _a("| Attacker | Target | Severity | Adjacent | Pillars |")
        _a("|----------|--------|----------|----------|---------|")
        for r in restraints:
            a_stem = format_term(r["attacker_stem"])
            t_stem = format_term(r["target_stem"])
            a_elem = r["attacker_element"]
            t_elem = r["target_element"]
            adj_mark = "✓" if r["is_adjacent"] else ""
            severity = r["severity"]
            loc = f"{r['attacker_pillar']}→{r['target_pillar']}"
            _a(f"| {a_stem} ({a_elem}) | {t_stem} ({t_elem}) | {severity} | {adj_mark} | {loc} |")
        _a("")

    # Stem Clashes (from comprehensive)
    stem_clash_list = stem_interactions.get("clashes", [])
    if stem_clash_list:
        _a("### Stem Clashes (天干相冲)\n")
        for sc in stem_clash_list:
            s1, s2 = sc["stems"]
            adj = "adjacent" if sc["is_adjacent"] else "remote"
            severity = sc["severity"]
            term = sc.get("term", "")
            loc = f"{sc['pair'][0]}↔{sc['pair'][1]}" if "pair" in sc else ""
            term_str = f" ({term})" if term else ""
            _a(f"- {format_term(s1)}↔{format_term(s2)}{term_str} — severity {severity}, {adj} [{loc}]")
        _a("")

    # ── Punishments ─────────────────────────────────────────
    if punishments:
        _a("## Punishments & Harms (刑害)\n")
        for p in punishments:
            _a(f"- **{p['type']}**: {p['branches']} ({p['life_areas']})")
        _a("")

    # ── Rooting Analysis ────────────────────────────────────
    if rooting and rooting.get("roots"):
        _a("## Day Master Rooting Analysis (通根)\n")
        root_cls = rooting.get("classification", "N/A")
        total = rooting.get("total_strength", 0)
        _a(f"**Classification**: {root_cls} (strength {total})\n")
        _a("| Branch (Pillar) | Hidden Stem | Role | Weight | Same Stem |")
        _a("|-----------------|-------------|------|--------|-----------|")
        for r in rooting["roots"]:
            branch = format_term(r["branch"])
            pillar = r["pillar"]
            hstem = format_term(r["hidden_stem"])
            role = r["role"]
            weight = f"{r['weight']:.2f}"
            same = "✓" if r.get("same_stem") else ""
            _a(f"| {branch} ({pillar}) | {hstem} | {role} | {weight} | {same} |")
        _a("")

    # ── Tomb/Treasury ───────────────────────────────────────
    if tomb_treasury:
        _a("## Tomb & Treasury Analysis (墓库)\n")
        for tomb in tomb_treasury:
            branch = format_term(tomb["branch"])
            pillar = tomb["pillar"]
            entombed = ", ".join(tomb.get("entombed_elements", []))
            opened = tomb.get("is_opened", False)
            dm_enters = tomb.get("dm_enters_tomb", False)
            _a(f"### {branch} ({pillar})\n")
            _a(f"- **Entombed elements**: {entombed}")
            if opened:
                _a(f"- **Status**: 开库 OPENED — {tomb.get('opened_by', 'clash')}")
            else:
                _a(f"- **Status**: 闭库 CLOSED")
            if dm_enters:
                _a("- ⚠ **DM enters tomb** (入墓) — DM energy locked, weakened")
            _a("")

    # ── Symbolic Stars ──────────────────────────────────────
    _a("## Symbolic Stars (神煞)\n")
    # Build set of void branches for cross-referencing
    void_branches_set = set()
    for pname, is_void in void_status.items():
        if is_void:
            void_branches_set.add(chart["pillars"][pname]["branch"])

    if symbolic_stars:
        for star in symbolic_stars:
            nature_icon = {"auspicious": "✦", "inauspicious": "⚠"}.get(star["nature"], "◆")
            star_fmt = format_term(star["star"].split(" ")[0])
            location = star["location"]
            # Cross-reference with void
            star_branch = chart["pillars"].get(location, {}).get("branch", "")
            void_tag = ""
            if star_branch in void_branches_set and star["star_en"] != "Void":
                if star["nature"] == "auspicious":
                    void_tag = " `[VOID — efficacy nullified]`"
                elif star["nature"] == "inauspicious":
                    void_tag = " `[VOID — harm reduced]`"
                else:
                    void_tag = " `[VOID]`"
            _a(f"- {nature_icon} **{star_fmt}** @ {location}: {star['description']}{void_tag}")
    else:
        _a("None detected.")
    _a("")

    # ── Na Yin Analysis ─────────────────────────────────────
    _a("## Na Yin Analysis (納音)\n")
    if nayin_analysis.get("pillar_nayins"):
        _a("### Pillar Na Yin\n")
        _a("| Pillar | Na Yin | Element |")
        _a("|--------|--------|---------|")
        for pname in pillar_order:
            if pname in nayin_analysis["pillar_nayins"]:
                ny = nayin_analysis["pillar_nayins"][pname]
                _a(f"| {pillar_labels[pname]} | {ny['nayin_chinese']} | {ny['nayin_element']} |")
        _a("")

    # Na Yin flow chain
    flow = nayin_analysis.get("flow", [])
    if flow:
        _RELATION_LABELS = {
            "same": ("＝", "same element"),
            "sheng": ("←生", "generated by"),
            "wo_sheng": ("→生", "generates"),
            "wo_ke": ("→克", "controls"),
            "ke": ("←克", "controlled by"),
        }
        _a("### Na Yin Flow (Adjacent Pillar Relations)\n")
        for f in flow:
            from_label = pillar_labels.get(f["from"], f["from"])
            to_label = pillar_labels.get(f["to"], f["to"])
            rel = f["relation"]
            icon, desc = _RELATION_LABELS.get(rel, (rel, rel))
            _a(f"- **{from_label}** ({f['from_element']}) {icon} **{to_label}** ({f['to_element']}) — *{desc}*")
        _a("")

    # Na Yin vs DM
    vs_dm = nayin_analysis.get("vs_day_master", {})
    if vs_dm:
        _DM_RELATION_LABELS = {
            "same": "same as DM",
            "sheng": "generates DM (supportive)",
            "wo_sheng": "DM generates (draining)",
            "wo_ke": "DM controls (wealth)",
            "ke": "controls DM (pressure)",
        }
        _a("### Na Yin vs Day Master\n")
        for pname in pillar_order:
            if pname in vs_dm:
                info = vs_dm[pname]
                rel_desc = _DM_RELATION_LABELS.get(info["relation_to_dm"], info["relation_to_dm"])
                _a(f"- **{pillar_labels[pname]}**: {info['nayin_name']} ({info['nayin_element']}) — *{rel_desc}*")
        _a("")

    # ── Life Stages ─────────────────────────────────────────
    _a("## Life Stages (十二长生)\n")
    _a("| Pillar | Stage | Class |")
    _a("|--------|-------|-------|")
    for pname in pillar_order:
        ls = life_stages[pname]
        _a(f"| {pillar_labels[pname]} | {format_term(ls['chinese'])} | {ls['strength_class']} |")
    _a("")

    # ── Luck Pillars ────────────────────────────────────────
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

    # ── Rating ──────────────────────────────────────────────
    _a("## Chart Rating (综合评分)\n")
    _a(f"**{rating} / 100**\n")

    # ── Narrative ───────────────────────────────────────────
    _a("## Narrative Interpretation (命理解读)\n")
    for line in narrative.splitlines():
        _a(line)
    _a("")

    # ── Comprehensive Summary ───────────────────────────────
    summary = comp.get("summary", "")
    if summary:
        _a("## Analysis Summary\n")
        _a(summary)
        _a("")

    # ── Projections ─────────────────────────────────────────
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

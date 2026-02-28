"""
bazi — Four Pillars (四柱八字) Analysis Package
=================================================

This package replaces the monolithic ``bazi.py`` module with a structured
sub-package.  All public symbols previously available via ``from bazi import …``
are re-exported here for full backward compatibility.
"""

# ── Constants ─────────────────────────────────────────────
from .constants import (
    HEAVENLY_STEMS,
    EARTHLY_BRANCHES,
    STEM_ELEMENT,
    STEM_POLARITY,
    GEN_MAP,
    CONTROL_MAP,
    BRANCH_HIDDEN_STEMS,
    HIDDEN_ROLES,
    LONGEVITY_STAGES,
    LONGEVITY_START,
    LONGEVITY_STAGES_EN,
    LONGEVITY_STAGES_VI,
    LIU_HE,
    LIU_CHONG,
    LIU_HAI,
    SAN_HE,
    BAN_SAN_HE,
    SAN_HUI,
    XING,
    ZI_XING_BRANCHES,
    BRANCH_ELEMENT,
    STEM_TRANSFORMATIONS,
    ADJACENT_PAIRS,
    SELF_PUNISH_BRANCHES,
    UNCIVIL_PUNISH_PAIRS,
    GRACELESS_PUNISH_PAIRS,
    BULLY_PUNISH_PAIRS,
    HARM_PAIRS,
    LIU_PO,
    STEM_CLASH_PAIRS,
    VOID_BRANCH_TABLE,
    XUN_NAMES,
    PILLAR_WEIGHTS,
    LU_MAP,
    NOBLEMAN_TABLE,
    ACADEMIC_STAR_TABLE,
    PEACH_BLOSSOM_TABLE,
    TRAVEL_HORSE_TABLE,
    GENERAL_STAR_TABLE,
    CANOPY_STAR_TABLE,
    GOAT_BLADE_TABLE,
    PROSPERITY_STAR_TABLE,
    RED_CLOUD_TABLE,
    BLOOD_KNIFE_TABLE,
)

# ── Terminology ───────────────────────────────────────────
from .terminology import format_term, FORMAT_STRING

# ── Ten Gods ──────────────────────────────────────────────
from .ten_gods import (
    _element_relation,
    ten_god,
    weighted_ten_god_distribution,
)

# ── Hidden Stems ──────────────────────────────────────────
from .hidden_stems import branch_hidden_with_roles

# ── Longevity Stages ──────────────────────────────────────
from .longevity import (
    changsheng_stage,
    longevity_map,
    life_stage_detail,
    life_stages_for_chart,
    life_stage_for_luck_pillar,
)

# ── Na Yin ────────────────────────────────────────────────
from .nayin import (
    nayin_for_cycle,
    nayin_for_pillar,
    analyze_nayin_interactions,
)

# ── Core ──────────────────────────────────────────────────
from .core import (
    normalize_gender,
    ganzhi_from_cycle,
    _cycle_from_stem_branch,
    build_chart,
    from_lunisolar_dto,
    from_solar_date,
)

# ── Branch Interactions ───────────────────────────────────
from .branch_interactions import (
    detect_self_punishment,
    detect_xing,
    detect_branch_interactions,
)

# ── Stem Transformations ─────────────────────────────────
from .stem_transformations import (
    check_obstruction,
    check_severe_clash,
    detect_stem_combinations,
    detect_transformations,
)

# ── Punishments ──────────────────────────────────────────
from .punishments import (
    detect_punishments,
    detect_fu_yin_duplication,
)

# ── Symbolic Stars ───────────────────────────────────────
from .symbolic_stars import (
    void_branches,
    xun_name,
    void_in_pillars,
    detect_symbolic_stars,
)

# ── Structure ────────────────────────────────────────────
from .structure import (
    detect_month_pillar_structure,
    detect_special_structures,
    classify_structure,
)

# ── Scoring ──────────────────────────────────────────────
from .scoring import (
    is_jian_lu,
    get_seasonal_strength,
    score_day_master,
    rate_chart,
    recommend_useful_god,
)

# ── Luck Pillars ─────────────────────────────────────────
from .luck_pillars import (
    calculate_luck_start_age,
    generate_luck_pillars,
    find_governing_jie_term,
)

# ── Annual Flow ──────────────────────────────────────────
from .annual_flow import annual_analysis

# ── Projections ──────────────────────────────────────────
from .projections import (
    get_year_cycle_for_gregorian,
    get_month_cycle_for_date,
    get_day_cycle_for_date,
    get_new_moon_dates,
    generate_year_projections,
    generate_month_projections,
    generate_day_projections,
)

# ── Analysis ─────────────────────────────────────────────
from .analysis import (
    analyze_time_range,
    comprehensive_analysis,
)

# ── Narrative ────────────────────────────────────────────
from .narrative import generate_narrative

# ── Report ───────────────────────────────────────────────
from .report import generate_report_markdown

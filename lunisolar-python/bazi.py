"""
Bazi Analysis Framework (八字分析框架)
======================================

Spec-aligned Bazi (Four Pillars of Destiny) analysis engine that builds on
top of the lunisolar calendar and GanZhi engine in ``lunisolar_v2.py``.

This module implements the subsystems defined in
``@specs/bazi-analysis-framework.md``:

- Ten Gods (十神)
- Hidden Stems (藏干)
- Twelve Longevity Stages (十二长生)
- Day-Master strength scoring
- Branch interactions (合冲刑害)
- Chart structures (格局)
- Luck Pillars (大运)
- Annual Pillar analysis (流年)
- Favorable / Unfavorable elements (用神体系)
- Quantitative chart rating
- Narrative interpretation

Usage::

    from bazi import from_solar_date, score_day_master

    chart = from_solar_date("2025-02-15", "14:30", gender="male")
    score, strength = score_day_master(chart)
"""

from collections import Counter
from typing import Dict, List, Optional, Tuple, Union

from lunisolar_v2 import (
    EARTHLY_BRANCHES as _EB_TUPLES,
    HEAVENLY_STEMS as _HS_TUPLES,
    LunisolarDateDTO,
    solar_to_lunisolar,
)

# ============================================================
# Core Constants — extracted from lunisolar_v2 tuples
# ============================================================

HEAVENLY_STEMS: List[str] = [s[0] for s in _HS_TUPLES]
EARTHLY_BRANCHES: List[str] = [b[0] for b in _EB_TUPLES]

# ============================================================
# Element & Polarity Mappings
# ============================================================

STEM_ELEMENT: Dict[str, str] = {
    '甲': 'Wood', '乙': 'Wood',
    '丙': 'Fire', '丁': 'Fire',
    '戊': 'Earth', '己': 'Earth',
    '庚': 'Metal', '辛': 'Metal',
    '壬': 'Water', '癸': 'Water',
}

STEM_POLARITY: Dict[str, str] = {
    '甲': 'Yang', '乙': 'Yin',
    '丙': 'Yang', '丁': 'Yin',
    '戊': 'Yang', '己': 'Yin',
    '庚': 'Yang', '辛': 'Yin',
    '壬': 'Yang', '癸': 'Yin',
}

# Five-Element production cycle: A produces B
GEN_MAP: Dict[str, str] = {
    'Wood': 'Fire',
    'Fire': 'Earth',
    'Earth': 'Metal',
    'Metal': 'Water',
    'Water': 'Wood',
}

# Five-Element control cycle: A controls B
CONTROL_MAP: Dict[str, str] = {
    'Wood': 'Earth',
    'Fire': 'Metal',
    'Earth': 'Water',
    'Metal': 'Wood',
    'Water': 'Fire',
}

# ============================================================
# Hidden Stems — spec §2.2  (main, middle, residual)
# ============================================================

BRANCH_HIDDEN_STEMS: Dict[str, List[str]] = {
    '子': ['癸'],
    '丑': ['己', '癸', '辛'],
    '寅': ['甲', '丙', '戊'],
    '卯': ['乙'],
    '辰': ['戊', '乙', '癸'],
    '巳': ['丙', '戊', '庚'],
    '午': ['丁', '己'],
    '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'],
    '酉': ['辛'],
    '戌': ['戊', '辛', '丁'],
    '亥': ['壬', '甲'],
}

HIDDEN_ROLES = ('main', 'middle', 'residual')


# ============================================================
# Gender Validation
# ============================================================

def normalize_gender(gender: Union[str, None]) -> str:
    """Normalize and validate gender string. Returns ``'male'`` or ``'female'``.

    Accepts common aliases such as ``'m'``, ``'f'``, ``'man'``, ``'woman'``,
    ``'男'``, ``'女'`` (case-insensitive, stripped).

    Raises :class:`ValueError` when the input cannot be mapped.
    """
    if gender is None:
        raise ValueError("gender must be provided as 'male' or 'female'")
    g = str(gender).strip().lower()
    if g in ('m', 'male', 'man', '男'):
        return 'male'
    if g in ('f', 'female', 'woman', '女'):
        return 'female'
    raise ValueError("gender must be 'male' or 'female' (or common aliases)")


# ============================================================
# Twelve Longevity Stages — spec §3
# ============================================================

LONGEVITY_STAGES: List[str] = [
    '长生', '沐浴', '冠带', '临官', '帝旺',
    '衰', '病', '死', '墓', '绝', '胎', '养',
]

# Starting branch for 长生 of each stem — spec §3.3
LONGEVITY_START: Dict[str, str] = {
    '甲': '亥', '乙': '午',
    '丙': '寅', '丁': '酉',
    '戊': '寅', '己': '酉',
    '庚': '巳', '辛': '子',
    '壬': '申', '癸': '卯',
}

# ============================================================
# Branch Interactions — spec §8
# ============================================================

# §8.1 Six Combinations (六合)
LIU_HE = frozenset({
    frozenset({'子', '丑'}),
    frozenset({'寅', '亥'}),
    frozenset({'卯', '戌'}),
    frozenset({'辰', '酉'}),
    frozenset({'巳', '申'}),
    frozenset({'午', '未'}),
})

# §8.4 Six Clashes (六冲)
LIU_CHONG = frozenset({
    frozenset({'子', '午'}),
    frozenset({'丑', '未'}),
    frozenset({'寅', '申'}),
    frozenset({'卯', '酉'}),
    frozenset({'辰', '戌'}),
    frozenset({'巳', '亥'}),
})

# §8.6 Six Harms (六害)
LIU_HAI = frozenset({
    frozenset({'子', '未'}),
    frozenset({'丑', '午'}),
    frozenset({'寅', '巳'}),
    frozenset({'卯', '辰'}),
    frozenset({'申', '亥'}),
    frozenset({'酉', '戌'}),
})

# §8.2 Three Combinations (三合)
SAN_HE: List[frozenset] = [
    frozenset({'申', '子', '辰'}),   # Water
    frozenset({'寅', '午', '戌'}),   # Fire
    frozenset({'亥', '卯', '未'}),   # Wood
    frozenset({'巳', '酉', '丑'}),   # Metal
]

# §8.3 Directional Combinations (三会 / 方局)
SAN_HUI: List[frozenset] = [
    frozenset({'寅', '卯', '辰'}),   # Wood
    frozenset({'巳', '午', '未'}),   # Fire
    frozenset({'申', '酉', '戌'}),   # Metal
    frozenset({'亥', '子', '丑'}),   # Water
]

# §8.5 Three Punishments (三刑)
XING: List[frozenset] = [
    frozenset({'寅', '巳', '申'}),   # 无恩之刑 (Graceless)
    frozenset({'丑', '戌', '未'}),   # 恃势之刑 (Bullying)
    frozenset({'子', '卯'}),          # 无礼之刑 (Rude)
]

# §8.5 Self-punishment (自刑)
ZI_XING_BRANCHES = frozenset({'辰', '午', '酉', '亥'})


# ============================================================
# Parsing helpers
# ============================================================

def ganzhi_from_cycle(cycle: int) -> Tuple[str, str]:
    """Convert a 1-60 sexagenary cycle number to (stem, branch) characters.

    Uses the same formula as ``lunisolar_v2._get_stem_branch``:
    ``stem_index = (cycle - 1) % 10``, ``branch_index = (cycle - 1) % 12``.
    """
    if not (1 <= cycle <= 60):
        raise ValueError(f"Cycle must be between 1 and 60, got {cycle}")
    stem = HEAVENLY_STEMS[(cycle - 1) % 10]
    branch = EARTHLY_BRANCHES[(cycle - 1) % 12]
    return stem, branch


def parse_ganzhi(gz: str) -> Tuple[str, str]:
    """Parse a two-character GanZhi string into (stem, branch)."""
    gz = gz.strip()
    if len(gz) != 2:
        raise ValueError(f"GanZhi must be two characters, got '{gz}'")
    stem, branch = gz[0], gz[1]
    if stem not in HEAVENLY_STEMS:
        raise ValueError(f"Invalid heavenly stem: '{stem}'")
    if branch not in EARTHLY_BRANCHES:
        raise ValueError(f"Invalid earthly branch: '{branch}'")
    return stem, branch


def branch_hidden_with_roles(branch: str) -> List[Tuple[str, str]]:
    """Return [(role, stem), …] for the hidden stems of *branch*."""
    stems = BRANCH_HIDDEN_STEMS[branch]
    return [(HIDDEN_ROLES[i], stems[i]) for i in range(len(stems))]


# ============================================================
# Twelve Longevity Stages — calculation (spec §3)
# ============================================================

def changsheng_stage(stem: str, branch: str) -> Tuple[int, str]:
    """Return (1-based stage index, stage name) for *stem* at *branch*.

    Yang stems progress forward (clockwise); Yin stems progress backward.
    """
    start = LONGEVITY_START[stem]
    i_start = EARTHLY_BRANCHES.index(start)
    i_target = EARTHLY_BRANCHES.index(branch)

    if STEM_POLARITY[stem] == 'Yang':
        offset = (i_target - i_start) % 12
    else:
        offset = (i_start - i_target) % 12

    idx = offset + 1          # 1-based
    return idx, LONGEVITY_STAGES[idx - 1]


# ============================================================
# Ten Gods (十神) — spec §1
# ============================================================

def _element_relation(dm_elem: str, other_elem: str) -> str:
    """Classify the Five-Element relationship of *other_elem* to *dm_elem*."""
    if other_elem == dm_elem:
        return 'same'
    if GEN_MAP[other_elem] == dm_elem:
        return 'sheng'       # other produces me
    if GEN_MAP[dm_elem] == other_elem:
        return 'wo_sheng'    # I produce other
    if CONTROL_MAP[dm_elem] == other_elem:
        return 'wo_ke'       # I control other
    if CONTROL_MAP[other_elem] == dm_elem:
        return 'ke'          # other controls me
    raise ValueError(f"Unexpected element pair: {dm_elem}, {other_elem}")


def ten_god(dm_stem: str, target_stem: str) -> str:
    """Return the Ten-God name of *target_stem* relative to Day Master *dm_stem*.

    Follows the convention in spec §1.1:
    - 正 (Direct) = opposite polarity to Day Master
    - 偏 (Indirect) = same polarity as Day Master
    """
    dm_elem = STEM_ELEMENT[dm_stem]
    t_elem = STEM_ELEMENT[target_stem]
    rel = _element_relation(dm_elem, t_elem)
    same_polarity = STEM_POLARITY[dm_stem] == STEM_POLARITY[target_stem]

    mapping = {
        'same':     ('比肩', '劫财'),
        'sheng':    ('偏印', '正印'),
        'wo_sheng': ('食神', '伤官'),
        'wo_ke':    ('偏财', '正财'),
        'ke':       ('七杀', '正官'),
    }
    same_pol_name, diff_pol_name = mapping[rel]
    return same_pol_name if same_polarity else diff_pol_name


# ============================================================
# Build Chart
# ============================================================

def build_chart(
    year_cycle: int,
    month_cycle: int,
    day_cycle: int,
    hour_cycle: int,
    gender: str,
) -> Dict:
    """Build a structured natal chart from four sexagenary cycle numbers.

    Parameters
    ----------
    year_cycle, month_cycle, day_cycle, hour_cycle : int
        Sexagenary cycle position (1-60) for each pillar, as produced by
        :class:`~lunisolar_v2.LunisolarDateDTO` (e.g. ``dto.year_cycle``).
    gender : str
        ``"male"`` or ``"female"``.

    Returns
    -------
    dict
        Chart dictionary with ``pillars``, ``day_master``, and ``gender``.
    """
    gender = normalize_gender(gender)

    pillar_cycles = {
        'year': year_cycle,
        'month': month_cycle,
        'day': day_cycle,
        'hour': hour_cycle,
    }
    pillars = {name: ganzhi_from_cycle(c) for name, c in pillar_cycles.items()}

    dm_stem = pillars['day'][0]
    dm_elem = STEM_ELEMENT[dm_stem]

    chart: Dict = {
        'pillars': {},
        'day_master': {'stem': dm_stem, 'element': dm_elem},
        'gender': gender,
    }

    for name, (stem, branch) in pillars.items():
        chart['pillars'][name] = {
            'stem': stem,
            'branch': branch,
            'hidden': branch_hidden_with_roles(branch),
            'ten_god': ten_god(dm_stem, stem),
        }

    return chart


def from_lunisolar_dto(dto: LunisolarDateDTO, gender: str) -> Dict:
    """Build a Bazi chart from a :class:`LunisolarDateDTO`."""
    gender = normalize_gender(gender)
    return build_chart(
        dto.year_cycle,
        dto.month_cycle,
        dto.day_cycle,
        dto.hour_cycle,
        gender,
    )


def from_solar_date(
    solar_date: str,
    solar_time: str = "12:00",
    gender: str = "male",
    timezone_name: str = "Asia/Shanghai",
) -> Dict:
    """Build a Bazi chart from a Gregorian date using the lunisolar engine.

    This is the primary high-level entry point that connects the existing
    lunisolar calendar pipeline (solar term boundaries, etc.) to the Bazi
    analysis layers.
    """
    gender = normalize_gender(gender)
    dto = solar_to_lunisolar(solar_date, solar_time, timezone_name, quiet=True)
    return from_lunisolar_dto(dto, gender)


# ============================================================
# Day-Master Strength Scoring
# ============================================================

def score_day_master(chart: Dict) -> Tuple[int, str]:
    """Score the Day Master's strength and classify as strong/weak/balanced.

    Factors
    -------
    1. Month-order (月令) via Longevity Stage of DM in month branch.
       Stages 1–5 strengthen (+2); stages 6–12 weaken (−2).  (spec §3.5)
    2. Root depth — hidden stems matching DM element.
       Main root +2, middle root +1.
    3. Visible-stem support — surface stems matching DM element (+1 each).
    """
    dm_stem = chart['day_master']['stem']
    dm_elem = chart['day_master']['element']
    month_branch = chart['pillars']['month']['branch']

    score = 0

    # 1) Month-order (月令) via longevity stage
    idx, _stage = changsheng_stage(dm_stem, month_branch)
    if idx <= 5:
        score += 2
    else:
        score -= 2

    # 2) Root depth (hidden stems matching DM element)
    for p in chart['pillars'].values():
        for role, stem in p['hidden']:
            if STEM_ELEMENT[stem] == dm_elem:
                if role == 'main':
                    score += 2
                elif role == 'middle':
                    score += 1

    # 3) Visible stem support
    for p in chart['pillars'].values():
        if STEM_ELEMENT[p['stem']] == dm_elem:
            score += 1

    # Classification
    if score >= 3:
        strength = 'strong'
    elif score <= -2:
        strength = 'weak'
    else:
        strength = 'balanced'

    return score, strength


# ============================================================
# Branch Interaction Detection — spec §8
# ============================================================

def detect_self_punishment(
    chart: Dict,
    require_exposed_main: bool = False,
    require_adjacent: bool = False,
) -> List[Dict]:
    """Detect 自刑 (self-punishment) patterns among natal branches.

    Returns a list of dicts, each describing a self-punishment event::

        {'branch': '酉', 'count': 2, 'positions': [0, 3],
         'mode': 'complete', 'notes': '...'}

    Parameters
    ----------
    chart : dict
        Natal chart built by :func:`build_chart`.
    require_exposed_main : bool
        If *True*, only flag self-punishment when at least one pillar with the
        duplicate branch has its main hidden stem (本气) appear as that
        pillar's heavenly stem (天干透出).  Reduces false positives.
    require_adjacent : bool
        If *True*, the two identical branches must occupy adjacent pillar
        positions (year-month, month-day, or day-hour).
    """
    pillar_names = list(chart['pillars'].keys())
    branches = [chart['pillars'][n]['branch'] for n in pillar_names]
    positions: Dict[str, List[int]] = {}
    for idx, b in enumerate(branches):
        positions.setdefault(b, []).append(idx)

    results: List[Dict] = []
    for b, inds in positions.items():
        if b in ZI_XING_BRANCHES and len(inds) >= 2:
            # Adjacency check
            adjacent_ok = True
            if require_adjacent:
                adjacent_ok = any(
                    abs(i - j) == 1 for i in inds for j in inds if i != j
                )

            # Main-stem exposure check
            exposed_ok = True
            if require_exposed_main:
                main_hidden = BRANCH_HIDDEN_STEMS[b][0]
                exposed_ok = any(
                    chart['pillars'][pillar_names[i]]['stem'] == main_hidden
                    for i in inds
                )

            if adjacent_ok and exposed_ok:
                mode = 'complete' if len(inds) >= 2 else 'partial'
                results.append({
                    'branch': b,
                    'count': len(inds),
                    'positions': inds,
                    'mode': mode,
                    'notes': f"adjacent_ok={adjacent_ok}, exposed_ok={exposed_ok}",
                })
    return results


def detect_xing(chart: Dict, strict: bool = False) -> List[Dict]:
    """Detect 刑 (punishment) patterns among natal branches.

    Returns a list of dicts::

        {'pattern': frozenset({'寅','巳','申'}), 'found': 2,
         'mode': 'partial'|'complete'}

    Parameters
    ----------
    chart : dict
        Natal chart built by :func:`build_chart`.
    strict : bool
        If *True*, only report **complete** patterns (all branches present).
        If *False* (default, permissive), also report partial matches (two of
        three branches present).
    """
    branches = [p['branch'] for p in chart['pillars'].values()]
    bset = set(branches)
    results: List[Dict] = []
    for trio in XING:
        found = len(trio & bset)
        if strict:
            if found == len(trio):
                results.append({'pattern': trio, 'found': found, 'mode': 'complete'})
        else:
            if found >= 2:
                mode = 'complete' if found == len(trio) else 'partial'
                results.append({'pattern': trio, 'found': found, 'mode': mode})
    return results


def detect_branch_interactions(chart: Dict) -> Dict[str, list]:
    """Detect 六合, 六冲, 六害, 三合, 三会, 刑, and 自刑 among natal branches."""
    branches = [p['branch'] for p in chart['pillars'].values()]
    results: Dict[str, list] = {
        '六合': [], '六冲': [], '害': [],
        '三合': [], '三会': [], '刑': [], '自刑': [],
    }

    # Pairwise checks
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            pair = frozenset({branches[i], branches[j]})
            if pair in LIU_HE:
                results['六合'].append((branches[i], branches[j]))
            if pair in LIU_CHONG:
                results['六冲'].append((branches[i], branches[j]))
            if pair in LIU_HAI:
                results['害'].append((branches[i], branches[j]))

    # Triple-set checks
    bset = set(branches)
    for trio in SAN_HE:
        if trio.issubset(bset):
            results['三合'].append(trio)
    for trio in SAN_HUI:
        if trio.issubset(bset):
            results['三会'].append(trio)

    # Graded 刑 detection (default: permissive / partial + complete)
    for entry in detect_xing(chart, strict=False):
        results['刑'].append(entry)

    # Robust 自刑 detection
    for entry in detect_self_punishment(chart):
        results['自刑'].append(entry)

    return results


# ============================================================
# 格局 Classification — spec §7
# ============================================================

def classify_structure(chart: Dict, strength: str) -> str:
    """Basic structure classifier using Ten-God dominance."""
    dm_stem = chart['day_master']['stem']
    tg_counts: Counter = Counter()

    for p in chart['pillars'].values():
        tg_counts[p['ten_god']] += 1
        for _role, stem in p['hidden']:
            tg_counts[ten_god(dm_stem, stem)] += 1

    dominant = tg_counts.most_common(1)[0][0]

    if dominant in ('正官', '七杀'):
        return '官杀格'
    if dominant in ('食神', '伤官'):
        return '食伤格'
    if dominant in ('正财', '偏财'):
        return '财格'
    if dominant in ('正印', '偏印'):
        return '印格'
    if strength == 'strong' and dominant in ('比肩', '劫财'):
        return '从强格'
    if strength == 'weak' and dominant not in ('比肩', '劫财'):
        return '从弱格'
    return '普通格局'


# ============================================================
# Advanced Structure Scoring
# ============================================================

def weighted_ten_god_distribution(chart: Dict) -> Dict[str, float]:
    """Weighted Ten-God distribution (month pillar stem weighs most)."""
    dm = chart['day_master']['stem']
    dist: Dict[str, float] = {}
    weight_map = {'month': 3}

    for pname, p in chart['pillars'].items():
        w_stem = weight_map.get(pname, 2)
        tg = ten_god(dm, p['stem'])
        dist[tg] = dist.get(tg, 0) + w_stem

        for role, stem in p['hidden']:
            tg_h = ten_god(dm, stem)
            w_hidden = {'main': 2, 'middle': 1}.get(role, 0.5)
            dist[tg_h] = dist.get(tg_h, 0) + w_hidden

    return dist


def classify_structure_professional(
    chart: Dict, strength: str,
) -> Tuple[str, float]:
    """Professional structure classifier with dominance score."""
    dist = weighted_ten_god_distribution(chart)
    dominant = max(dist, key=dist.get)
    score = dist[dominant]

    rules = {
        ('正官', '七杀'): {
            True: '官杀格',
            False: '杀重身轻 (破格)',
        },
        ('食神', '伤官'): {
            True: '食伤生财格',
            False: '伤官见官风险',
        },
        ('正财', '偏财'): {
            True: '财格',
            False: '财多身弱',
        },
        ('正印', '偏印'): {
            True: '印绶格',
            False: '印多压身',
        },
        ('比肩', '劫财'): {
            True: '建禄格',
            False: '比劫夺财风险',
        },
    }

    for gods, outcomes in rules.items():
        if dominant in gods:
            if dominant in ('正官', '七杀'):
                ok = strength != 'weak'
            elif dominant in ('食神', '伤官'):
                ok = strength == 'strong'
            elif dominant in ('正财', '偏财'):
                ok = strength == 'strong'
            elif dominant in ('正印', '偏印'):
                ok = strength == 'weak'
            else:
                ok = strength == 'strong'
            return outcomes[ok], score

    return '普通格局', score


# ============================================================
# Luck Pillar Calculation (大运) — spec §5
# ============================================================

def _next_ganzhi(stem: str, branch: str, forward: bool = True) -> Tuple[str, str]:
    """Advance (or retreat) one position in the sexagenary cycle."""
    s_idx = HEAVENLY_STEMS.index(stem)
    b_idx = EARTHLY_BRANCHES.index(branch)
    delta = 1 if forward else -1
    return (
        HEAVENLY_STEMS[(s_idx + delta) % 10],
        EARTHLY_BRANCHES[(b_idx + delta) % 12],
    )


def generate_luck_pillars(chart: Dict, count: int = 8) -> List[Tuple[str, str]]:
    """Generate *count* Luck Pillars from the month pillar.

    Direction follows spec §5.2 Step 1:
    - Yang year-stem + male  → forward
    - Yang year-stem + female → backward
    - Yin year-stem  + male  → backward
    - Yin year-stem  + female → forward

    .. note::
       Precise starting-age calculation (§5.2 Step 2) requires Jie solar-term
       dates and is not included here.  The pillar *sequence* is correct.
    """
    year_stem = chart['pillars']['year']['stem']
    gender = normalize_gender(chart.get('gender', 'male'))
    is_yang = STEM_POLARITY[year_stem] == 'Yang'
    forward = (is_yang and gender == 'male') or (
        not is_yang and gender == 'female'
    )

    stem = chart['pillars']['month']['stem']
    branch = chart['pillars']['month']['branch']
    pillars: List[Tuple[str, str]] = []
    for _ in range(count):
        stem, branch = _next_ganzhi(stem, branch, forward)
        pillars.append((stem, branch))
    return pillars


# ============================================================
# Annual Flow Engine (流年) — spec §6
# ============================================================

def annual_analysis(chart: Dict, year_pillar_cycle: int) -> Dict:
    """Analyse a flowing-year pillar against the natal chart.

    Parameters
    ----------
    chart : dict
        Natal chart built by :func:`build_chart`.
    year_pillar_cycle : int
        Sexagenary cycle number (1-60) for the flowing year pillar, as
        produced by :class:`~lunisolar_v2.LunisolarDateDTO`.

    Returns the year's Ten-God role, branch interactions with natal
    branches, and an approximate Day-Master strength delta.
    """
    year_stem, year_branch = ganzhi_from_cycle(year_pillar_cycle)
    dm = chart['day_master']['stem']
    dm_elem = STEM_ELEMENT[dm]
    natal_branches = [p['branch'] for p in chart['pillars'].values()]

    result: Dict = {}
    result['year_ten_god'] = ten_god(dm, year_stem)

    interactions: List[str] = []
    for b in natal_branches:
        pair = frozenset({b, year_branch})
        if pair in LIU_CHONG:
            interactions.append('冲')
        if pair in LIU_HE:
            interactions.append('合')
        if pair in LIU_HAI:
            interactions.append('害')
    result['interactions'] = interactions

    # Approximate strength delta
    yr_elem = STEM_ELEMENT[year_stem]
    delta = 0
    if GEN_MAP[yr_elem] == dm_elem:      # year element produces DM
        delta += 1
    if CONTROL_MAP[yr_elem] == dm_elem:   # year element controls DM
        delta -= 1
    result['strength_delta'] = delta

    return result


# ============================================================
# Favorable & Unfavorable Elements (用神) — spec §10
# ============================================================

def recommend_useful_god(chart: Dict, strength: str) -> Dict[str, List[str]]:
    """Recommend favorable/unfavorable elements based on DM strength.

    - Strong DM → needs Output (食伤) and Wealth (财) to release energy.
    - Weak DM → needs Resource (印) and Companion (比劫) for support.
    - Balanced → moderate recommendation.
    """
    dm_elem = chart['day_master']['element']
    inverse_gen = {v: k for k, v in GEN_MAP.items()}

    if strength == 'strong':
        return {
            'favorable': [GEN_MAP[dm_elem], CONTROL_MAP[dm_elem]],
            'avoid': [dm_elem],
        }
    if strength == 'weak':
        return {
            'favorable': [inverse_gen[dm_elem], dm_elem],
            'avoid': [CONTROL_MAP[dm_elem]],
        }
    return {
        'favorable': [GEN_MAP[dm_elem], inverse_gen[dm_elem]],
        'avoid': [],
    }


# ============================================================
# Chart Rating System (100-point scale)
# ============================================================

def rate_chart(chart: Dict) -> int:
    """Quantitative 100-point chart rating.

    Components:

    ==============================  ======
    Category                        Max
    ==============================  ======
    Day-Master strength balance      30
    Structure purity                 25
    Element balance                  20
    Root depth                       15
    Interaction stability            10
    ==============================  ======
    """
    total = 0

    # 1. Strength balance (max 30)
    _score, strength = score_day_master(chart)
    if strength == 'balanced':
        total += 30
    elif strength == 'strong':
        total += 22
    else:
        total += 18

    # 2. Structure purity (max 25)
    _struct, s_score = classify_structure_professional(chart, strength)
    if s_score > 8:
        total += 25
    elif s_score > 5:
        total += 18
    else:
        total += 10

    # 3. Element spread (max 20)
    elem_counts: Dict[str, int] = {}
    for p in chart['pillars'].values():
        e = STEM_ELEMENT[p['stem']]
        elem_counts[e] = elem_counts.get(e, 0) + 1
        for _role, stem in p['hidden']:
            e = STEM_ELEMENT[stem]
            elem_counts[e] = elem_counts.get(e, 0) + 1
    total += min(len(elem_counts) * 4, 20)

    # 4. Root depth (max 15)
    root = 0
    dm_elem = chart['day_master']['element']
    for p in chart['pillars'].values():
        for role, stem in p['hidden']:
            if STEM_ELEMENT[stem] == dm_elem:
                if role == 'main':
                    root += 5
                elif role == 'middle':
                    root += 3
    total += min(root, 15)

    # 5. Interaction stability (max 10) — clashes indicate turbulence
    interactions = detect_branch_interactions(chart)
    total += 4 if interactions['六冲'] else 10

    return total


# ============================================================
# Narrative Interpretation Generator
# ============================================================

def generate_narrative(
    chart: Dict,
    strength: str,
    structure: str,
    interactions: Dict[str, list],
) -> str:
    """Generate a human-readable interpretation of the natal chart."""
    dm = chart['day_master']['stem']
    elem = chart['day_master']['element']

    lines = [
        f"Day Master: {dm} ({elem})",
        f"Structure: {structure}",
        f"Strength: {strength}",
    ]

    personality = {
        'strong': "Self-driven, assertive, independent.",
        'weak': "Adaptive, sensitive to environment, relationship-oriented.",
        'balanced': "Balanced temperament with moderate adaptability.",
    }
    lines.append(f"Personality: {personality.get(strength, '')}")

    if interactions.get('六冲'):
        lines.append("Chart shows internal conflicts (clashes present).")
    if interactions.get('三合'):
        lines.append("Strong elemental harmony (Three Harmony formation).")
    if interactions.get('六合'):
        lines.append("Partnership tendencies indicated (Six Combination present).")
    if interactions.get('自刑'):
        lines.append("Self-punishment pattern detected — watch for self-sabotage tendencies.")

    lines.append(
        "Overall chart shows dynamic interaction between "
        "structure and elemental balance."
    )
    return "\n".join(lines)


# ============================================================
# CLI entry point
# ============================================================

if __name__ == "__main__":
    # Demo with cycle number input (甲子=1, 乙丑=2, 丙寅=3, 丁巳=54)
    chart = build_chart(1, 2, 3, 54, "male")

    score, strength = score_day_master(chart)
    interactions = detect_branch_interactions(chart)
    structure = classify_structure(chart, strength)
    structure_pro, dominance = classify_structure_professional(chart, strength)
    luck = generate_luck_pillars(chart)
    useful = recommend_useful_god(chart, strength)
    rating = rate_chart(chart)
    narrative = generate_narrative(chart, strength, structure, interactions)

    print("Day Master:", chart['day_master'])
    print("Strength Score:", score, "→", strength)
    print("Structure (basic):", structure)
    print("Structure (professional):", structure_pro, f"(dominance={dominance})")
    print("Luck Pillars:", ["".join(p) for p in luck])
    print("Useful Elements:", useful)
    print("Chart Rating:", rating, "/ 100")
    print()
    print("Branch Interactions:", {k: v for k, v in interactions.items() if v})
    print()
    print("--- Narrative ---")
    print(narrative)

    # Demo annual analysis - 丙午 = cycle 43
    print("--- Flowing Year 2026 (丙午, cycle 43) ---")
    print(annual_analysis(chart, 43))

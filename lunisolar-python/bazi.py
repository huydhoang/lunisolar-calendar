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

import argparse
import csv
import os
from collections import Counter
from datetime import date
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
# Branch → native element mapping
# ============================================================

BRANCH_ELEMENT: Dict[str, str] = {
    '子': 'Water', '丑': 'Earth', '寅': 'Wood', '卯': 'Wood',
    '辰': 'Earth', '巳': 'Fire', '午': 'Fire', '未': 'Earth',
    '申': 'Metal', '酉': 'Metal', '戌': 'Earth', '亥': 'Water',
}

# ============================================================
# Heavenly Stem Combinations & Transformations (天干合化)
# ============================================================

# Five canonical stem-combination pairs → target element
STEM_TRANSFORMATIONS: Dict[frozenset, str] = {
    frozenset(['甲', '己']): 'Earth',
    frozenset(['乙', '庚']): 'Metal',
    frozenset(['丙', '辛']): 'Water',
    frozenset(['丁', '壬']): 'Wood',
    frozenset(['戊', '癸']): 'Fire',
}

# Adjacent pillar pairs (strongest proximity for combinations)
ADJACENT_PAIRS: List[Tuple[str, str]] = [
    ('year', 'month'), ('month', 'day'), ('day', 'hour'),
]

# ============================================================
# Punishments & Harms — detailed pair sets
# ============================================================

SELF_PUNISH_BRANCHES = frozenset({'午', '酉', '辰', '亥'})

UNCIVIL_PUNISH_PAIRS = frozenset({
    frozenset({'子', '卯'}),
})

BULLY_PUNISH_PAIRS = frozenset({
    frozenset({'寅', '巳'}),
    frozenset({'巳', '申'}),
    frozenset({'寅', '申'}),
    frozenset({'丑', '戌'}),
    frozenset({'戌', '未'}),
    frozenset({'丑', '未'}),
})

HARM_PAIRS = frozenset({
    frozenset({'子', '未'}),
    frozenset({'丑', '午'}),
    frozenset({'寅', '巳'}),
    frozenset({'卯', '辰'}),
    frozenset({'申', '亥'}),
    frozenset({'酉', '戌'}),
})

# Six Destructions (六破)
LIU_PO = frozenset({
    frozenset({'子', '酉'}),
    frozenset({'丑', '辰'}),
    frozenset({'寅', '亥'}),
    frozenset({'卯', '午'}),
    frozenset({'巳', '申'}),
    frozenset({'未', '戌'}),
})

# Stem clash pairs (天干冲) — stems 6 positions apart control each other
STEM_CLASH_PAIRS = frozenset({
    frozenset({'甲', '庚'}),
    frozenset({'乙', '辛'}),
    frozenset({'丙', '壬'}),
    frozenset({'丁', '癸'}),
    frozenset({'戊', '甲'}),  # Earth–Wood (control cycle)
    frozenset({'己', '乙'}),
})

# ============================================================
# Longevity Stage Labels (English & Vietnamese)
# ============================================================

LONGEVITY_STAGES_EN: List[str] = [
    'Growth', 'Bath', 'Crown Belt', 'Coming of Age', 'Prosperity Peak',
    'Decline', 'Sickness', 'Death', 'Grave', 'Termination',
    'Conception', 'Nurture',
]

LONGEVITY_STAGES_VI: List[str] = [
    'Trường Sinh', 'Mộc Dục', 'Quan Đới', 'Lâm Quan', 'Đế Vượng',
    'Suy', 'Bệnh', 'Tử', 'Mộ', 'Tuyệt', 'Thai', 'Dưỡng',
]

# ============================================================
# Na Yin (納音) Data Loader
# ============================================================

_NAYIN_CSV_PATH = os.path.join(os.path.dirname(__file__), 'nayin.csv')
_NAYIN_DATA: Dict[int, Dict] = {}


def _load_nayin() -> Dict[int, Dict]:
    """Load Na Yin data from ``nayin.csv`` (cached after first call)."""
    global _NAYIN_DATA
    if _NAYIN_DATA:
        return _NAYIN_DATA
    with open(_NAYIN_CSV_PATH, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            idx = int(row['cycle_index'])
            _NAYIN_DATA[idx] = {
                'cycle_index': idx,
                'chinese': row['chinese'],
                'pinyin': row['pinyin'],
                'vietnamese': row['vietnamese'],
                'nayin_element': row['nayin_element'],
                'nayin_chinese': row['nayin_chinese'],
                'nayin_vietnamese': row['nayin_vietnamese'],
                'nayin_english': row['nayin_english'],
                'nayin_song': row['nayin_song'],
                'stem_polarity': row['stem_polarity'],
                'stem_element': row['stem_element'],
                'branch_polarity': row['branch_polarity'],
                'branch_element': row['branch_element'],
                'stem_life_stage': row['stem_life_stage'],
            }
    return _NAYIN_DATA


def nayin_for_cycle(cycle: int) -> Optional[Dict]:
    """Return Na Yin data dict for the given 1-60 sexagenary cycle number."""
    if not (1 <= cycle <= 60):
        return None
    data = _load_nayin()
    return data.get(cycle)


def _nayin_pure_element(nayin_element_str: str) -> str:
    """Extract pure element name from nayin_element field like 'Metal (金)'."""
    return nayin_element_str.split('(')[0].strip() if '(' in nayin_element_str else nayin_element_str.strip()


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


def branch_hidden_with_roles(branch_idx: int) -> List[Tuple[str, str]]:
    """Return [(role, stem), …] for the hidden stems of the branch at *branch_idx*.

    Parameters
    ----------
    branch_idx : int
        0-based index into :data:`EARTHLY_BRANCHES`.
    """
    branch = EARTHLY_BRANCHES[branch_idx]
    stems = BRANCH_HIDDEN_STEMS[branch]
    return [(HIDDEN_ROLES[i], stems[i]) for i in range(len(stems))]


# ============================================================
# Twelve Longevity Stages — calculation (spec §3)
# ============================================================

def changsheng_stage(stem_idx: int, branch_idx: int) -> Tuple[int, str]:
    """Return (1-based stage index, stage name) for the stem at *stem_idx* at branch *branch_idx*.

    Yang stems progress forward (clockwise); Yin stems progress backward.

    Parameters
    ----------
    stem_idx : int
        0-based index into :data:`HEAVENLY_STEMS`.
    branch_idx : int
        0-based index into :data:`EARTHLY_BRANCHES`.
    """
    stem = HEAVENLY_STEMS[stem_idx]
    start = LONGEVITY_START[stem]
    i_start = EARTHLY_BRANCHES.index(start)

    if STEM_POLARITY[stem] == 'Yang':
        offset = (branch_idx - i_start) % 12
    else:
        offset = (i_start - branch_idx) % 12

    idx = offset + 1          # 1-based
    return idx, LONGEVITY_STAGES[idx - 1]


def longevity_map(chart: Dict) -> Dict[str, Tuple[int, str]]:
    """Map the Day Master's 12 Longevity Stage across all four natal pillars.

    Returns a dictionary keyed by pillar name (``'year'``, ``'month'``,
    ``'day'``, ``'hour'``) whose values are ``(1-based stage index, stage
    name)`` tuples produced by :func:`changsheng_stage`.

    This answers the question: "How strong or healthy is the Day Master's
    energy in each of the four pillars?"

    Parameters
    ----------
    chart : dict
        Natal chart built by :func:`build_chart`.
    """
    dm_idx = HEAVENLY_STEMS.index(chart['day_master']['stem'])
    result: Dict[str, Tuple[int, str]] = {}
    for name, p in chart['pillars'].items():
        b_idx = EARTHLY_BRANCHES.index(p['branch'])
        result[name] = changsheng_stage(dm_idx, b_idx)
    return result


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


def ten_god(dm_stem_idx: int, target_stem_idx: int) -> str:
    """Return the Ten-God name of the stem at *target_stem_idx* relative to Day Master at *dm_stem_idx*.

    Follows the convention in spec §1.1:
    - 正 (Direct) = opposite polarity to Day Master
    - 偏 (Indirect) = same polarity as Day Master

    Parameters
    ----------
    dm_stem_idx : int
        0-based index into :data:`HEAVENLY_STEMS` for the Day Master stem.
    target_stem_idx : int
        0-based index into :data:`HEAVENLY_STEMS` for the target stem.
    """
    dm_stem = HEAVENLY_STEMS[dm_stem_idx]
    target_stem = HEAVENLY_STEMS[target_stem_idx]
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
        pillar_data: Dict = {
            'stem': stem,
            'branch': branch,
            'hidden': branch_hidden_with_roles(EARTHLY_BRANCHES.index(branch)),
            'ten_god': ten_god(HEAVENLY_STEMS.index(dm_stem), HEAVENLY_STEMS.index(stem)),
        }
        # Na Yin data
        p_cycle = pillar_cycles[name]
        ny = nayin_for_cycle(p_cycle)
        if ny:
            pillar_data['nayin'] = {
                'element': _nayin_pure_element(ny['nayin_element']),
                'chinese': ny['nayin_chinese'],
                'vietnamese': ny['nayin_vietnamese'],
                'english': ny['nayin_english'],
            }
        chart['pillars'][name] = pillar_data

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
    idx, _stage = changsheng_stage(HEAVENLY_STEMS.index(dm_stem), EARTHLY_BRANCHES.index(month_branch))
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
                mode = 'complete' if len(inds) >= 3 else 'partial'
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
# Stem Combination & Transformation Detection (天干合化)
# ============================================================

def check_obstruction(chart: Dict, p1: str, p2: str) -> bool:
    """Check if a third stem between *p1* and *p2* obstructs their combination.

    A pair is obstructed when a stem sitting between the two pillar positions
    has a clash or controlling relationship with either stem of the pair.
    """
    order = ['year', 'month', 'day', 'hour']
    i1, i2 = order.index(p1), order.index(p2)
    lo, hi = min(i1, i2), max(i1, i2)
    if hi - lo <= 1:
        return False  # adjacent — no room for blocker
    s1 = chart['pillars'][p1]['stem']
    s2 = chart['pillars'][p2]['stem']
    e1, e2 = STEM_ELEMENT[s1], STEM_ELEMENT[s2]
    for mid_idx in range(lo + 1, hi):
        mid_pillar = order[mid_idx]
        mid_stem = chart['pillars'][mid_pillar]['stem']
        mid_elem = STEM_ELEMENT[mid_stem]
        if CONTROL_MAP.get(mid_elem) in (e1, e2):
            return True
    return False


def check_severe_clash(chart: Dict, target_element: str) -> bool:
    """Return True if *target_element* is severely clashed by natal pillars.

    A severe clash exists when a natal pillar's stem element controls the
    target element AND that stem is in the month pillar or has opposite
    polarity to the Day Master.
    """
    dm_pol = STEM_POLARITY[chart['day_master']['stem']]
    for pname, p in chart['pillars'].items():
        elem = STEM_ELEMENT[p['stem']]
        if CONTROL_MAP.get(elem) == target_element:
            if pname == 'month' or STEM_POLARITY[p['stem']] != dm_pol:
                return True
    return False


def detect_stem_combinations(chart: Dict) -> List[Dict]:
    """Detect Heavenly Stem Combination pairs (天干合) in the natal chart.

    Returns a list of dicts with combination info, including the target
    element the combination could transform into.
    """
    results: List[Dict] = []
    pillar_names = ['year', 'month', 'day', 'hour']
    for i, p1 in enumerate(pillar_names):
        for j in range(i + 1, len(pillar_names)):
            p2 = pillar_names[j]
            s1 = chart['pillars'][p1]['stem']
            s2 = chart['pillars'][p2]['stem']
            pair_key = frozenset([s1, s2])
            if pair_key in STEM_TRANSFORMATIONS:
                results.append({
                    'pair': (p1, p2),
                    'stems': (s1, s2),
                    'target_element': STEM_TRANSFORMATIONS[pair_key],
                })
    return results


def detect_transformations(chart: Dict) -> List[Dict]:
    """Detect stem transformations (合化) with full condition checking.

    For each candidate stem-combination pair, evaluates:
    - Proximity (adjacent pillars = strong)
    - Month Command support (月令)
    - Leading/delivery stem (引化)
    - Severe clash interference
    - Obstruction by intervening stems

    Returns a list of dicts with status: 'Hóa (successful)', 'Hợp (bound)',
    or 'Blocked'.
    """
    results: List[Dict] = []
    month_branch = chart['pillars']['month']['branch']
    month_elem = BRANCH_ELEMENT[month_branch]
    pillar_names = ['year', 'month', 'day', 'hour']
    adjacent_set = {(a, b) for a, b in ADJACENT_PAIRS}

    for i, p1 in enumerate(pillar_names):
        for j in range(i + 1, len(pillar_names)):
            p2 = pillar_names[j]
            s1 = chart['pillars'][p1]['stem']
            s2 = chart['pillars'][p2]['stem']
            pair_key = frozenset([s1, s2])
            if pair_key not in STEM_TRANSFORMATIONS:
                continue
            target = STEM_TRANSFORMATIONS[pair_key]

            # Proximity score
            is_adjacent = (p1, p2) in adjacent_set or (p2, p1) in adjacent_set
            proximity_score = 2 if is_adjacent else 1

            # Obstruction check
            blocked = check_obstruction(chart, p1, p2)

            # Month Command support
            month_support = (month_elem == target)

            # Leading stem — target element appears in other pillars (visible or hidden)
            other_pillars = [k for k in pillar_names if k not in (p1, p2)]
            leading = False
            for k in other_pillars:
                if STEM_ELEMENT.get(chart['pillars'][k]['stem']) == target:
                    leading = True
                    break
            if not leading:
                # Check hidden stems across all branches
                for p in chart['pillars'].values():
                    for _role, hstem in p['hidden']:
                        if STEM_ELEMENT.get(hstem) == target:
                            leading = True
                            break
                    if leading:
                        break

            # Severe clash check
            severely_clashed = check_severe_clash(chart, target)

            # Decision rule
            if proximity_score == 2 and month_support and (leading or not severely_clashed) and not blocked:
                status = 'Hóa (successful)'
                confidence = 95 if leading else 85
            elif proximity_score >= 1 and (month_support or leading) and not blocked:
                status = 'Hợp (bound)'
                confidence = 65
            elif blocked:
                status = 'Blocked'
                confidence = 10
            else:
                status = 'Hợp (bound)'
                confidence = 40

            # Reduce confidence if severely clashed even when Hóa
            if status == 'Hóa (successful)' and severely_clashed:
                status = 'Hóa (suppressed by clash)'
                confidence = max(confidence - 30, 20)

            results.append({
                'pair': (p1, p2),
                'stems': (s1, s2),
                'target_element': target,
                'month_support': month_support,
                'leading_present': leading,
                'blocked': blocked,
                'severely_clashed': severely_clashed,
                'proximity_score': proximity_score,
                'status': status,
                'confidence': confidence,
            })
    return results


# ============================================================
# Phục Ngâm (伏吟) Detection
# ============================================================

def detect_phuc_ngam(chart: Dict, dynamic_pillar: Dict) -> List[Dict]:
    """Detect Phục Ngâm events comparing a dynamic pillar to natal pillars.

    Phục Ngâm occurs when a dynamic pillar (current year or luck pillar) is
    identical to a natal pillar (strongest) or shares the same branch (weaker).

    Parameters
    ----------
    chart : dict
        Natal chart built by :func:`build_chart`.
    dynamic_pillar : dict
        A dict with ``'stem'`` and ``'branch'`` keys (e.g. from a luck pillar
        or annual pillar).

    Returns
    -------
    list[dict]
        Each entry describes a Phục Ngâm event.
    """
    results: List[Dict] = []
    dyn_stem = dynamic_pillar['stem']
    dyn_branch = dynamic_pillar['branch']

    for p_name, natal in chart['pillars'].items():
        if natal['stem'] == dyn_stem and natal['branch'] == dyn_branch:
            confidence = 95 if p_name == 'month' else 90
            results.append({
                'type': 'Phục Ngâm',
                'match': 'exact',
                'natal_pillar': p_name,
                'dynamic_stem': dyn_stem,
                'dynamic_branch': dyn_branch,
                'confidence': confidence,
                'message': (
                    f"{p_name} pillar identical to dynamic pillar "
                    f"({dyn_stem}{dyn_branch}) — overload/stagnation risk."
                ),
            })
        elif natal['branch'] == dyn_branch:
            confidence = 70 if p_name == 'month' else 60
            results.append({
                'type': 'Phục Ngâm',
                'match': 'branch',
                'natal_pillar': p_name,
                'dynamic_stem': dyn_stem,
                'dynamic_branch': dyn_branch,
                'confidence': confidence,
                'message': (
                    f"{p_name} branch equals dynamic branch ({dyn_branch}) "
                    f"— elemental overbalance."
                ),
            })
    return results


# ============================================================
# Punishments & Harms Detection (detailed)
# ============================================================

def detect_punishments(chart: Dict) -> List[Dict]:
    """Detect punishments (刑) and harms (害) with life-area tagging.

    Classifies each detection into Self-Punishment, Uncivil-Punishment,
    Bully-Punishment, and Harm categories. Assigns severity and affected
    life-area tags.
    """
    results: List[Dict] = []
    names = ['year', 'month', 'day', 'hour']
    branches = [chart['pillars'][k]['branch'] for k in names]

    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            bi, bj = branches[i], branches[j]
            pair = frozenset({bi, bj})

            involves_day = 'day' in (names[i], names[j])
            involves_month = 'month' in (names[i], names[j])
            severity = 80 if involves_day else (70 if involves_month else 50)

            # Self-punishment (自刑)
            if bi == bj and bi in SELF_PUNISH_BRANCHES:
                results.append({
                    'type': 'Tự hình (Self-punish)',
                    'pair': (names[i], names[j]),
                    'branches': (bi, bj),
                    'severity': severity,
                    'life_areas': ['health', 'self-sabotage'],
                })

            # Uncivil punishment (无礼之刑)
            if pair in UNCIVIL_PUNISH_PAIRS:
                results.append({
                    'type': 'Vô lễ chi hình (Uncivil)',
                    'pair': (names[i], names[j]),
                    'branches': (bi, bj),
                    'severity': severity,
                    'life_areas': ['relationship', 'secrets'],
                })

            # Bully punishment (恃势之刑)
            if pair in BULLY_PUNISH_PAIRS:
                results.append({
                    'type': 'Ỷ thế chi hình (Bully)',
                    'pair': (names[i], names[j]),
                    'branches': (bi, bj),
                    'severity': severity,
                    'life_areas': ['career', 'power struggles'],
                })

            # Harm (害/六害)
            if pair in HARM_PAIRS:
                results.append({
                    'type': 'Hại (Harm)',
                    'pair': (names[i], names[j]),
                    'branches': (bi, bj),
                    'severity': severity,
                    'life_areas': ['health', 'relationship'],
                })

    return results


# ============================================================
# Na Yin Interaction Analysis (納音相互作用)
# ============================================================

def _cycle_from_stem_branch(stem: str, branch: str) -> int:
    """Compute sexagenary cycle number (1-60) from stem and branch characters."""
    s_idx = HEAVENLY_STEMS.index(stem)
    b_idx = EARTHLY_BRANCHES.index(branch)
    for c in range(1, 61):
        if (c - 1) % 10 == s_idx and (c - 1) % 12 == b_idx:
            return c
    raise ValueError(f"Invalid stem-branch pair: {stem}{branch}")


def nayin_for_pillar(pillar: Dict) -> Optional[Dict]:
    """Return Na Yin data for a pillar dict with ``'stem'`` and ``'branch'`` keys."""
    cycle = _cycle_from_stem_branch(pillar['stem'], pillar['branch'])
    return nayin_for_cycle(cycle)


def analyze_nayin_interactions(chart: Dict) -> Dict:
    """Analyze Na Yin element interactions between pillars and with Day Master.

    Returns a dict with:
    - ``pillar_nayins``: Na Yin data for each pillar
    - ``flow``: interactions along the Year→Month→Day→Hour flow
    - ``vs_day_master``: each pillar's Na Yin relation to the Day Master element
    """
    dm_elem = chart['day_master']['element']
    pillar_order = ['year', 'month', 'day', 'hour']
    pillar_nayins: Dict[str, Dict] = {}

    for pname in pillar_order:
        p = chart['pillars'][pname]
        ny = nayin_for_pillar(p)
        if ny:
            pillar_nayins[pname] = {
                'nayin_element': _nayin_pure_element(ny['nayin_element']),
                'nayin_chinese': ny['nayin_chinese'],
                'nayin_vietnamese': ny['nayin_vietnamese'],
                'nayin_english': ny['nayin_english'],
            }

    # Flow interactions: Year→Month→Day→Hour
    flow: List[Dict] = []
    for i in range(len(pillar_order) - 1):
        p1_name, p2_name = pillar_order[i], pillar_order[i + 1]
        if p1_name in pillar_nayins and p2_name in pillar_nayins:
            e1 = pillar_nayins[p1_name]['nayin_element']
            e2 = pillar_nayins[p2_name]['nayin_element']
            rel = _element_relation(e1, e2)
            flow.append({
                'from': p1_name,
                'to': p2_name,
                'from_element': e1,
                'to_element': e2,
                'relation': rel,
            })

    # Relation to Day Master
    vs_dm: Dict[str, Dict] = {}
    for pname, ny_data in pillar_nayins.items():
        ny_elem = ny_data['nayin_element']
        rel = _element_relation(dm_elem, ny_elem)
        vs_dm[pname] = {
            'nayin_element': ny_elem,
            'relation_to_dm': rel,
            'nayin_name': ny_data['nayin_chinese'],
        }

    return {
        'pillar_nayins': pillar_nayins,
        'flow': flow,
        'vs_day_master': vs_dm,
    }


# ============================================================
# Life Stage of Day Master (at each pillar and Da Yun)
# ============================================================

def life_stage_detail(stem_idx: int, branch_idx: int) -> Dict:
    """Return full life-stage detail (Chinese, English, Vietnamese, strength)."""
    idx, cn_name = changsheng_stage(stem_idx, branch_idx)
    return {
        'index': idx,
        'chinese': cn_name,
        'english': LONGEVITY_STAGES_EN[idx - 1],
        'vietnamese': LONGEVITY_STAGES_VI[idx - 1],
        'strength_class': 'strong' if idx <= 5 else 'weak',
    }


def life_stages_for_chart(chart: Dict) -> Dict[str, Dict]:
    """Return the Day Master's life stage at each natal pillar."""
    dm_idx = HEAVENLY_STEMS.index(chart['day_master']['stem'])
    result: Dict[str, Dict] = {}
    for pname, p in chart['pillars'].items():
        b_idx = EARTHLY_BRANCHES.index(p['branch'])
        result[pname] = life_stage_detail(dm_idx, b_idx)
    return result


def life_stage_for_luck_pillar(chart: Dict, luck_pillar: Dict) -> Dict:
    """Return the Day Master's life stage at a luck pillar."""
    dm_idx = HEAVENLY_STEMS.index(chart['day_master']['stem'])
    b_idx = EARTHLY_BRANCHES.index(luck_pillar['branch'])
    return life_stage_detail(dm_idx, b_idx)


# ============================================================
# Custom Time Range Analysis (Year / Year-Month / Year-Month-Day)
# ============================================================

def analyze_time_range(
    chart: Dict,
    year_cycle: int,
    month_cycle: Optional[int] = None,
    day_cycle: Optional[int] = None,
    luck_pillar: Optional[Dict] = None,
) -> Dict:
    """Analyze a custom time range against the natal chart.

    Supports three levels of detail:
    - **Year Level**: only ``year_cycle`` provided → year pillar analysis
    - **Year-Month Level**: ``year_cycle`` + ``month_cycle`` → year + month
    - **Year-Month-Day Level**: all three → year + month + day

    Each level includes: Stem-Branch, Life Stage, interactions,
    transformations, and Na Yin analysis.

    Parameters
    ----------
    chart : dict
        Natal chart from :func:`build_chart`.
    year_cycle : int
        Sexagenary cycle number for the year (1-60).
    month_cycle : int, optional
        Sexagenary cycle number for the month (1-60).
    day_cycle : int, optional
        Sexagenary cycle number for the day (1-60).
    luck_pillar : dict, optional
        Current luck pillar dict (with ``'stem'`` and ``'branch'`` keys).
    """
    dm_idx = HEAVENLY_STEMS.index(chart['day_master']['stem'])
    dm_elem = chart['day_master']['element']

    result: Dict = {'level': 'year', 'pillars': {}}

    # --- Year pillar ---
    yr_stem, yr_branch = ganzhi_from_cycle(year_cycle)
    yr_b_idx = EARTHLY_BRANCHES.index(yr_branch)
    yr_life_stage = life_stage_detail(dm_idx, yr_b_idx)
    yr_ten_god = ten_god(dm_idx, HEAVENLY_STEMS.index(yr_stem))
    yr_nayin = nayin_for_cycle(year_cycle)

    yr_entry: Dict = {
        'stem': yr_stem,
        'branch': yr_branch,
        'ten_god': yr_ten_god,
        'life_stage': yr_life_stage,
    }
    if yr_nayin:
        yr_entry['nayin'] = {
            'element': _nayin_pure_element(yr_nayin['nayin_element']),
            'chinese': yr_nayin['nayin_chinese'],
            'vietnamese': yr_nayin['nayin_vietnamese'],
            'english': yr_nayin['nayin_english'],
        }
    result['pillars']['year'] = yr_entry

    # Interactions with natal branches
    yr_pillar = {'stem': yr_stem, 'branch': yr_branch}
    natal_branches = [p['branch'] for p in chart['pillars'].values()]
    yr_interactions: List[str] = []
    for b in natal_branches:
        pair = frozenset({b, yr_branch})
        if pair in LIU_CHONG:
            yr_interactions.append('冲')
        if pair in LIU_HE:
            yr_interactions.append('合')
        if pair in LIU_HAI:
            yr_interactions.append('害')
    result['year_interactions'] = yr_interactions

    # Phục Ngâm check
    result['phuc_ngam'] = detect_phuc_ngam(chart, yr_pillar)

    # Stem transformation check (year stem vs natal stems)
    yr_stem_combos: List[Dict] = []
    for pname, p in chart['pillars'].items():
        pair_key = frozenset([yr_stem, p['stem']])
        if pair_key in STEM_TRANSFORMATIONS:
            yr_stem_combos.append({
                'natal_pillar': pname,
                'stems': (yr_stem, p['stem']),
                'target_element': STEM_TRANSFORMATIONS[pair_key],
            })
    result['year_stem_combinations'] = yr_stem_combos

    # NaYin relation to Day Master
    if yr_nayin:
        ny_elem = _nayin_pure_element(yr_nayin['nayin_element'])
        result['year_nayin_vs_dm'] = {
            'nayin_element': ny_elem,
            'relation': _element_relation(dm_elem, ny_elem),
        }

    # --- Month pillar (if provided) ---
    if month_cycle is not None:
        result['level'] = 'year-month'
        mo_stem, mo_branch = ganzhi_from_cycle(month_cycle)
        mo_b_idx = EARTHLY_BRANCHES.index(mo_branch)
        mo_life_stage = life_stage_detail(dm_idx, mo_b_idx)
        mo_ten_god = ten_god(dm_idx, HEAVENLY_STEMS.index(mo_stem))
        mo_nayin = nayin_for_cycle(month_cycle)

        mo_entry: Dict = {
            'stem': mo_stem,
            'branch': mo_branch,
            'ten_god': mo_ten_god,
            'life_stage': mo_life_stage,
        }
        if mo_nayin:
            mo_entry['nayin'] = {
                'element': _nayin_pure_element(mo_nayin['nayin_element']),
                'chinese': mo_nayin['nayin_chinese'],
                'vietnamese': mo_nayin['nayin_vietnamese'],
                'english': mo_nayin['nayin_english'],
            }
        result['pillars']['month'] = mo_entry

    # --- Day pillar (if provided) ---
    if day_cycle is not None:
        result['level'] = 'year-month-day'
        dy_stem, dy_branch = ganzhi_from_cycle(day_cycle)
        dy_b_idx = EARTHLY_BRANCHES.index(dy_branch)
        dy_life_stage = life_stage_detail(dm_idx, dy_b_idx)
        dy_ten_god = ten_god(dm_idx, HEAVENLY_STEMS.index(dy_stem))
        dy_nayin = nayin_for_cycle(day_cycle)

        dy_entry: Dict = {
            'stem': dy_stem,
            'branch': dy_branch,
            'ten_god': dy_ten_god,
            'life_stage': dy_life_stage,
        }
        if dy_nayin:
            dy_entry['nayin'] = {
                'element': _nayin_pure_element(dy_nayin['nayin_element']),
                'chinese': dy_nayin['nayin_chinese'],
                'vietnamese': dy_nayin['nayin_vietnamese'],
                'english': dy_nayin['nayin_english'],
            }
        result['pillars']['day'] = dy_entry

    # Luck pillar context
    if luck_pillar is not None:
        lp_interactions: List[str] = []
        lp_branch = luck_pillar['branch']
        for b in natal_branches:
            pair = frozenset({b, lp_branch})
            if pair in LIU_CHONG:
                lp_interactions.append('冲')
            if pair in LIU_HE:
                lp_interactions.append('合')
            if pair in LIU_HAI:
                lp_interactions.append('害')
        result['luck_pillar_interactions'] = lp_interactions
        result['luck_phuc_ngam'] = detect_phuc_ngam(chart, luck_pillar)

    return result


# ============================================================
# Comprehensive Interaction Analysis (aggregated output)
# ============================================================

def comprehensive_analysis(chart: Dict) -> Dict:
    """Produce a comprehensive interaction and transformation analysis.

    Returns a machine-friendly dict containing:
    - ``day_master``: element, polarity, strength, born-in context
    - ``natal_interactions``: clashes, combinations, transformations, punishments
    - ``nayin_analysis``: Na Yin interactions and pillar data
    - ``life_stages``: Day Master's life stage at each pillar
    - ``summary``: human-readable summary string
    """
    dm = chart['day_master']
    dm_stem = dm['stem']
    dm_elem = dm['element']
    score, strength = score_day_master(chart)

    # Month context
    month_branch = chart['pillars']['month']['branch']
    month_elem = BRANCH_ELEMENT[month_branch]

    # Branch interactions
    interactions = detect_branch_interactions(chart)

    # Stem combinations & transformations
    stem_combos = detect_stem_combinations(chart)
    transformations = detect_transformations(chart)

    # Punishments
    punishments = detect_punishments(chart)

    # Life stages
    life_stages = life_stages_for_chart(chart)

    # Na Yin
    nayin_analysis = analyze_nayin_interactions(chart)

    # Build summary
    summary_parts = [
        f"Day Master {dm_stem} {dm_elem}; strength: {strength} ({score} pts).",
        f"Born in {month_branch} ({month_elem} month).",
    ]
    for t in transformations:
        if t['status'].startswith('Hóa'):
            summary_parts.append(
                f"Transformation: {t['stems'][0]}+{t['stems'][1]} → "
                f"{t['target_element']} ({t['status']}, confidence {t['confidence']})."
            )
    if interactions.get('六冲'):
        summary_parts.append("Clashes detected — watch for conflicts.")
    if punishments:
        p_types = {p['type'] for p in punishments}
        summary_parts.append(f"Punishments: {', '.join(p_types)}.")

    return {
        'day_master': {
            'stem': dm_stem,
            'element': dm_elem,
            'polarity': STEM_POLARITY[dm_stem],
            'strength': strength,
            'strength_score': score,
            'born_in': f"{month_branch} ({month_elem} month)",
        },
        'natal_interactions': {
            'clashes': interactions.get('六冲', []),
            'combinations': interactions.get('六合', []),
            'san_he': interactions.get('三合', []),
            'san_hui': interactions.get('三会', []),
            'stem_combinations': stem_combos,
            'transformations': transformations,
            'punishments': punishments,
            'harms': interactions.get('害', []),
            'xing': interactions.get('刑', []),
            'self_punishment': interactions.get('自刑', []),
        },
        'life_stages': life_stages,
        'nayin_analysis': nayin_analysis,
        'summary': ' '.join(summary_parts),
    }


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
            tg_counts[ten_god(HEAVENLY_STEMS.index(dm_stem), HEAVENLY_STEMS.index(stem))] += 1

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
        tg = ten_god(HEAVENLY_STEMS.index(dm), HEAVENLY_STEMS.index(p['stem']))
        dist[tg] = dist.get(tg, 0) + w_stem

        for role, stem in p['hidden']:
            tg_h = ten_god(HEAVENLY_STEMS.index(dm), HEAVENLY_STEMS.index(stem))
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


def _luck_direction(chart: Dict) -> bool:
    """Return *True* if luck pillars advance forward (clockwise).

    Direction follows spec §5.2 Step 1:
    - Yang year-stem + male  → forward
    - Yang year-stem + female → backward
    - Yin year-stem  + male  → backward
    - Yin year-stem  + female → forward
    """
    year_stem = chart['pillars']['year']['stem']
    gender = normalize_gender(chart.get('gender', 'male'))
    is_yang = STEM_POLARITY[year_stem] == 'Yang'
    return (is_yang and gender == 'male') or (
        not is_yang and gender == 'female'
    )


def calculate_luck_start_age(
    birth_date: date,
    solar_term_date: date,
    forward: bool,
) -> Tuple[int, int]:
    """Calculate the starting age of the first Luck Pillar (大运).

    Implements the traditional **3-Day Rule**: 3 days from birth to the
    governing solar term equals 1 year of life, and 1 day equals 4 months.

    Parameters
    ----------
    birth_date : :class:`datetime.date`
        Gregorian date of birth.
    solar_term_date : :class:`datetime.date`
        Gregorian date of the **governing Jie solar term boundary**.
        If *forward* is True, this should be the *next* Jie (节) after birth.
        If *forward* is False, this should be the *previous* Jie before birth.
    forward : bool
        True when the luck direction is forward (Yang-male / Yin-female).

    Returns
    -------
    (start_age_years, start_age_months)
        The age (in whole years and remaining months) at which the first
        Luck Pillar takes effect.  Fractional days are rounded to the
        nearest whole month.
    """
    delta_days = abs((solar_term_date - birth_date).days)
    # 3 days = 1 year → 1 day = 4 months
    total_months = delta_days * 4
    years = total_months // 12
    months = total_months % 12
    return int(years), int(months)


def generate_luck_pillars(
    chart: Dict,
    count: int = 8,
    birth_date: Optional[date] = None,
    solar_term_date: Optional[date] = None,
    birth_year: Optional[int] = None,
) -> List[Dict]:
    """Generate *count* Luck Pillars (大运) from the month pillar.

    Direction follows spec §5.2 Step 1:
    - Yang year-stem + male  → forward
    - Yang year-stem + female → backward
    - Yin year-stem  + male  → backward
    - Yin year-stem  + female → forward

    When *birth_date* **and** *solar_term_date* are provided, the precise
    starting age is calculated using :func:`calculate_luck_start_age` (the
    traditional 3-day rule) and each pillar includes a
    ``start_gregorian_year``.  When only *birth_year* is provided without
    dates, an approximate ``start_gregorian_year`` is computed using a
    default starting age of 1 year.

    Parameters
    ----------
    chart : dict
        Natal chart built by :func:`build_chart`.
    count : int
        Number of luck pillars to generate (default 8).
    birth_date : date, optional
        Gregorian birth date for precise starting-age calculation.
    solar_term_date : date, optional
        Governing Jie solar-term date (next Jie if forward, previous Jie
        if backward).
    birth_year : int, optional
        Gregorian birth year.  Used for approximate year mapping when
        exact dates are not available.

    Returns
    -------
    list[dict]
        Each element is a dict with keys:

        * ``stem`` — Heavenly Stem character
        * ``branch`` — Earthly Branch character
        * ``longevity_stage`` — ``(index, name)`` tuple from
          :func:`changsheng_stage` for the Day Master at this branch
        * ``start_age`` — ``(years, months)`` tuple (present when dates
          are supplied or estimated when *birth_year* is given)
        * ``start_gregorian_year`` — Gregorian year at which this 10-year
          cycle begins (present when any birth info is given)

    Backward Compatibility
    ----------------------
    When called **without** any date parameters and the return value is
    iterated for ``(stem, branch)`` tuples (the old API), each dict
    supports tuple unpacking via ``__iter__``.  However callers are
    encouraged to migrate to the dict-based API.
    """
    forward = _luck_direction(chart)
    dm_idx = HEAVENLY_STEMS.index(chart['day_master']['stem'])

    # Starting age calculation
    start_years: Optional[int] = None
    start_months: int = 0

    if birth_date is not None and solar_term_date is not None:
        start_years, start_months = calculate_luck_start_age(
            birth_date, solar_term_date, forward,
        )
    elif birth_year is not None:
        # Approximate: default starting age of 1 year when no solar-term
        # date is available.
        start_years = 1
        start_months = 0

    # Resolve birth year for Gregorian year mapping
    effective_birth_year: Optional[int] = None
    if birth_date is not None:
        effective_birth_year = birth_date.year
    elif birth_year is not None:
        effective_birth_year = birth_year

    stem = chart['pillars']['month']['stem']
    branch = chart['pillars']['month']['branch']
    pillars: List[Dict] = []
    for i in range(count):
        stem, branch = _next_ganzhi(stem, branch, forward)
        b_idx = EARTHLY_BRANCHES.index(branch)
        s_idx = HEAVENLY_STEMS.index(stem)
        entry: Dict = {
            'stem': stem,
            'branch': branch,
            'longevity_stage': changsheng_stage(dm_idx, b_idx),
            'ten_god': ten_god(dm_idx, s_idx),
            'life_stage_detail': life_stage_detail(dm_idx, b_idx),
        }
        # Na Yin for luck pillar
        lp_cycle = _cycle_from_stem_branch(stem, branch)
        lp_nayin = nayin_for_cycle(lp_cycle)
        if lp_nayin:
            entry['nayin'] = {
                'element': _nayin_pure_element(lp_nayin['nayin_element']),
                'chinese': lp_nayin['nayin_chinese'],
                'vietnamese': lp_nayin['nayin_vietnamese'],
                'english': lp_nayin['nayin_english'],
            }
        if start_years is not None:
            cycle_start_months = (start_years * 12 + start_months) + i * 120
            age_years = cycle_start_months // 12
            age_months = cycle_start_months % 12
            entry['start_age'] = (age_years, age_months)
            if effective_birth_year is not None:
                entry['start_gregorian_year'] = effective_birth_year + age_years
        pillars.append(entry)
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
    result['year_ten_god'] = ten_god(HEAVENLY_STEMS.index(dm), HEAVENLY_STEMS.index(year_stem))

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
    parser = argparse.ArgumentParser(description="Bazi (Four Pillars) chart analysis")
    parser.add_argument("-d", "--date", required=True, help="Solar date (YYYY-MM-DD)")
    parser.add_argument("-t", "--time", default="12:00", help="Solar time (HH:MM, default 12:00)")
    parser.add_argument("-g", "--gender", required=True, help="Gender (male/female)")
    args = parser.parse_args()
    solar_date = args.date
    solar_time = args.time
    gender = args.gender

    dto = solar_to_lunisolar(solar_date, solar_time)
    chart = build_chart(dto.year_cycle, dto.month_cycle, dto.day_cycle, dto.hour_cycle, gender)

    score, strength = score_day_master(chart)
    interactions = detect_branch_interactions(chart)
    structure = classify_structure(chart, strength)
    structure_pro, dominance = classify_structure_professional(chart, strength)
    luck = generate_luck_pillars(chart)
    useful = recommend_useful_god(chart, strength)
    rating = rate_chart(chart)
    narrative = generate_narrative(chart, strength, structure, interactions)
    lmap = longevity_map(chart)
    tg_dist = weighted_ten_god_distribution(chart)

    SEP = "=" * 60

    print(SEP)
    print("  BAZI (四柱八字) COMPREHENSIVE CHART REPORT")
    print(SEP)

    # ── Day Master ──────────────────────────────────────────────
    dm = chart['day_master']
    polarity = STEM_POLARITY[dm['stem']]
    print(f"\n[ Day Master (日元) ]")
    print(f"  Stem    : {dm['stem']}  |  Element : {dm['element']}  |  Polarity : {polarity}")
    print(f"  Strength: {score} pts → {strength.upper()}")

    # ── Four Pillars ────────────────────────────────────────────
    print(f"\n[ Four Pillars (四柱) ]")
    header = f"  {'Pillar':<8} {'GanZhi':<6} {'Stem':<4} {'Branch':<4} {'Ten-God':<6} {'Longevity Stage':<18} {'Hidden Stems (role: stem)'}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    pillar_order = ['year', 'month', 'day', 'hour']
    pillar_labels = {'year': '年 Year', 'month': '月 Month', 'day': '日 Day', 'hour': '时 Hour'}
    for pname in pillar_order:
        p = chart['pillars'][pname]
        stage_idx, stage_name = lmap[pname]
        ganzhi = p['stem'] + p['branch']
        hidden_str = ', '.join(f"{role}: {stem}" for role, stem in p['hidden'])
        print(f"  {pillar_labels[pname]:<12} {ganzhi:<6} {p['stem']:<4} {p['branch']:<6} {p['ten_god']:<8} "
              f"({stage_idx:>2}) {stage_name:<12}  {hidden_str}")

    # ── Chart Structures ────────────────────────────────────────
    print(f"\n[ Chart Structure (格局) ]")
    print(f"  Basic            : {structure}")
    print(f"  Professional     : {structure_pro}  (dominance score = {dominance:.1f})")

    # ── Weighted Ten-God Distribution ───────────────────────────
    print(f"\n[ Ten-God Distribution (十神分布, weighted) ]")
    sorted_tg = sorted(tg_dist.items(), key=lambda x: x[1], reverse=True)
    for tg_name, tg_score in sorted_tg:
        bar = '█' * int(tg_score)
        print(f"  {tg_name:<4} {tg_score:>5.1f}  {bar}")

    # ── Branch Interactions ─────────────────────────────────────
    active = {k: v for k, v in interactions.items() if v}
    print(f"\n[ Branch Interactions (地支关系) ]")
    if active:
        for kind, entries in active.items():
            print(f"  {kind}:")
            for entry in entries:
                print(f"    {entry}")
    else:
        print("  None detected.")

    # ── Luck Pillars ────────────────────────────────────────────
    print(f"\n[ Luck Pillars (大运) — {len(luck)} pillars, direction: {'forward ▶' if _luck_direction(chart) else 'backward ◀'} ]")
    for i, lp in enumerate(luck, 1):
        ganzhi = lp['stem'] + lp['branch']
        ls_idx, ls_name = lp['longevity_stage']
        age_info = ""
        if 'start_age' in lp:
            ay, am = lp['start_age']
            age_info = f"  age {ay}y {am}m"
            if 'start_gregorian_year' in lp:
                age_info += f" (~{lp['start_gregorian_year']})"
        print(f"  {i}. {ganzhi:<4}  longevity: ({ls_idx:>2}) {ls_name:<8}{age_info}")

    # ── Useful Elements (用神) ───────────────────────────────────
    print(f"\n[ Useful Elements / Yong Shen (用神) ]")
    print(f"  Favorable (喜用) : {', '.join(useful['favorable'])}")
    print(f"  Avoid (忌)       : {', '.join(useful['avoid']) if useful['avoid'] else 'None'}")

    # ── Chart Rating ────────────────────────────────────────────
    print(f"\n[ Chart Rating (综合评分) ]")
    bar_filled = '█' * (rating // 5)
    bar_empty = '░' * (20 - rating // 5)
    print(f"  {rating} / 100  [{bar_filled}{bar_empty}]")

    # ── Narrative ───────────────────────────────────────────────
    print(f"\n[ Narrative Interpretation (命理解读) ]")
    for line in narrative.splitlines():
        print(f"  {line}")

    # ── Annual (Flowing Year) Analysis ──────────────────────────
    print(f"\n[ Flowing Year Analysis (流年) ]")
    # Demo: current year 丙午 = cycle 43, plus the two surrounding years
    demo_years = [
        (2025, 42, "乙巳"),
        (2026, 43, "丙午"),
        (2027, 44, "丁未"),
    ]
    for yr, cycle, gz in demo_years:
        res = annual_analysis(chart, cycle)
        yr_stem, yr_branch = ganzhi_from_cycle(cycle)
        interactions_str = ', '.join(res['interactions']) if res['interactions'] else 'none'
        delta_str = f"+{res['strength_delta']}" if res['strength_delta'] > 0 else str(res['strength_delta'])
        print(f"  {yr} ({gz}, cycle {cycle:>2}) | Ten-God: {res['year_ten_god']:<4} | "
              f"Branch interactions: {interactions_str:<12} | Strength Δ: {delta_str}")

    print(f"\n{SEP}")

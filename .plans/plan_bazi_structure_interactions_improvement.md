# Bazi Structure Classification & Interaction Detection — Improvement Plan

> **Status**: Draft  
> **Date**: 2026-03-01  
> **Scope**: Improve `structure.py`, `branch_interactions.py`, `stem_transformations.py`, `scoring.py`, `analysis.py`, `glossary.py`, and `constants.py` to fully implement classical Bazi interaction rules  
> **Goal**: Achieve comprehensive, theory-accurate detection of all branch/stem interactions, Lục Hợp transformation conditions, Hidden Combinations, Arching Combinations, Rooting analysis, Tomb/Treasury mechanics, Void Branch effects, and a robust multi-factor structure classifier

---

## 0. Current-State Audit

### 0.1 What Works Today

| Module | Capability | Coverage |
|--------|-----------|----------|
| `branch_interactions.py` | 六合, 六冲, 六害, 三合, 半三合, 三会, 刑, 自刑 | Pair/set detection only — no transformation outcome |
| `stem_transformations.py` | 天干五合 (5 pairs), 合化 4-condition evaluation | Adjacency, month support, leading stem, obstruction, severe clash |
| `punishments.py` | 刑 (4 types), 害, 伏吟 | Life-area tagging, severity scoring |
| `structure.py` | 八正格 (8 Regular) + 建禄/羊刃 via Ten-God dominance | Month-pillar protrusion only; `detect_special_structures()` is a stub |
| `scoring.py` | DM strength (seasonal + root depth + visible stems) | Linear scoring; no interaction-aware adjustments |
| `glossary.py` | §I–XXVIII terminology | Ám Hợp, Củng Hợp, Rooting, Tomb/Treasury, Emptiness, Palaces added |
| `constants.py` | All interaction sets derived from glossary | Missing: Ám Hợp, Củng Hợp, Lục Phá, stem restraints, rooting maps |

### 0.2 Key Gaps

1. **Branch interactions** detect pairs but never evaluate *transformation outcomes* for 六合 (Lục Hợp) — the system reports "子丑 combine" but never whether they actually transform to Earth.
2. **Ám Hợp** (Hidden Combinations) and **Củng Hợp** (Arching Combinations) defined in glossary but never detected.
3. **六破** (Six Destructions / Lục Phá) constants exist in `constants.py` but are never detected in `branch_interactions.py`.
4. **Stem restraints** (天干相克) defined in glossary but not wired into any detection.
5. **Structure classifier** (`classify_structure`) uses Ten-God dominance only — it never checks:
   - Ngũ Hành Chuyên Vượng (Five-Element Dominance / 曲直格, 炎上格, etc.)
   - Tòng Cách (Follow Structures / 从格)
   - Hóa Cách (Transform Structures / 化格)
   - Composite structures (食神制杀, 伤官配印, etc.)
6. **Rooting analysis** (通根) is done implicitly via raw hidden-stem counting in `scoring.py` but never produces a structured result or distinguishes 本气根 vs 余气根.
7. **Tomb/Treasury mechanics** (墓库) — the four Tomb branches (辰戌丑未) get no special treatment; entering/exiting tomb is not evaluated.
8. **Void Branch effects** (空亡) — detected in `symbolic_stars.py` but never integrated into interaction resolution (void branches should weaken combinations and clashes).
9. **Lục Hợp transformation conditions** — Unlike stem combinations which check 4 conditions, branch combinations are purely binary (present / absent).
10. **Interaction priority and conflict resolution** — When a branch participates in both 合 and 冲, classical theory says 合 can resolve 冲 (or vice versa). No resolution logic exists.
11. **Jealous Combination** (争合 / Tranh Hợp) — when multiple stems/branches contest the same partner, the combination is weakened. Not detected.
12. **DM scoring** does not account for interaction outcomes (e.g., a successful 三合 Water frame strengthens Water DM; a 六冲 on the month branch weakens seasonal support).

---

## 1. Phase 1 — Data Layer Completion (`constants.py`, `glossary.py`)

### 1.1 Wire New Glossary Data into `constants.py`

Add these derived sets/maps from the already-defined glossary terms:

```python
# §1: Stem Restraints (天干相克)
from .glossary import STEM_RESTRAIN_PAIR_TO_TERM
STEM_RESTRAINT_PAIRS: Dict[tuple, str] = {
    k: STEM_ELEMENT[k[0]]  # attacker element
    for k in STEM_RESTRAIN_PAIR_TO_TERM
}

# §2.1: Hidden Combinations (暗合)
from .glossary import BRANCH_PAIR_TO_AN_HE
AN_HE = frozenset(BRANCH_PAIR_TO_AN_HE.keys())

# §2.2: Arching Combinations (拱合)
from .glossary import BRANCH_PAIR_TO_GONG_HE, GONG_HE_PAIR_TO_ELEMENT
GONG_HE = frozenset(BRANCH_PAIR_TO_GONG_HE.keys())

# §2.3: Lục Hợp transformation element map
from .glossary import LIU_HE_PAIR_TO_ELEMENT
LIU_HE_TRANSFORM_ELEMENT: Dict[frozenset, str] = dict(LIU_HE_PAIR_TO_ELEMENT)
# Wu-Wei dual possibility (Fire default, Earth alternate) — keyed by pair
LIU_HE_WU_WEI_PAIR = frozenset({"午", "未"})
LIU_HE_WU_WEI_ELEMENTS = ("Fire", "Earth")

# §3.1: Rooting map — stem → list of branches where it takes root
STEM_ROOT_BRANCHES: Dict[str, List[str]] = {}
for branch, hidden_list in BRANCH_HIDDEN_STEMS.items():
    for stem in hidden_list:
        STEM_ROOT_BRANCHES.setdefault(stem, []).append(branch)

# §3.2: Tomb/Treasury map — element → tomb branch
ELEMENT_TO_TOMB: Dict[str, str] = {
    "Wood": "未", "Fire": "戌", "Metal": "丑", "Water": "辰", "Earth": "戌",
}
TOMB_TREASURY_BRANCHES = frozenset({"辰", "戌", "丑", "未"})
```

### 1.2 Deliverables

- [ ] Update `constants.py` with all new derived sets
- [ ] No new glossary work needed (§I–XXVIII already complete)
- [ ] Add constants tests: `TestAnHeSets`, `TestGongHeSets`, `TestRootingMap`, `TestTombMap`

### 1.3 Tests (Phase 1)

| Test | Assertion |
|------|-----------|
| `AN_HE` has 3 pairs | `len(AN_HE) == 3` |
| `GONG_HE` has 4 pairs | `len(GONG_HE) == 4` |
| `STEM_ROOT_BRANCHES["甲"]` includes "寅" | Main-qi root |
| `ELEMENT_TO_TOMB["Wood"] == "未"` | Correct tomb branch |
| Every stem in `STEM_RESTRAINT_PAIRS` is valid | Keys are 2-tuples of valid stems |

---

## 2. Phase 2 — Branch Interaction Overhaul (`branch_interactions.py`)

### 2.1 Add Missing Interaction Types

Extend `detect_branch_interactions()` to also detect:

1. **六破 (Six Destructions / Lục Phá)** — already in `LIU_PO` constant, just not queried.
2. **暗合 (Hidden Combinations / Ám Hợp)** — use new `AN_HE` set.
3. **拱合 (Arching Combinations / Củng Hợp)** — use new `GONG_HE` set; only detect when the *missing* middle branch is absent from natal chart (otherwise it's a full 三合).

```python
# Add keys to results dict:
results["六破"] = []
results["暗合"] = []
results["拱合"] = []
```

### 2.2 Lục Hợp Transformation Evaluation

Currently 六合 is detected as a bare pair. Add a new function `evaluate_liu_he_transformation()` that checks whether a Six Combination actually transforms, following the same 4-condition framework as stem combinations:

```python
def evaluate_liu_he_transformation(
    chart: Dict,
    branch1: str,
    branch2: str,
    pillar1: str,
    pillar2: str,
) -> Dict:
    """Evaluate whether a Six Combination (六合) transforms.
    
    Returns dict with keys:
      - target_element: str (the element it would transform to)
      - is_adjacent: bool
      - month_support: bool (month branch prospers or generates target)
      - leading_present: bool (target element exposed on other stems)
      - blocked: bool (pair is clashed apart by a third branch)
      - status: "Hóa" | "Hợp Nhi Bất Hóa" | "Blocked"
      - confidence: int
    
    Special handling for 午未 pair: evaluate both Fire and Earth targets,
    pick the one with stronger month/leading support.
    """
```

**Conditions (paralleling stem transformation logic):**

| # | Condition | Implementation |
|---|-----------|---------------|
| 1 | **Adjacency** (紧贴) | Pillars must be adjacent (year-month, month-day, day-hour) |
| 2 | **Month Order Support** (月令得气) | Month branch's element matches or generates the target |
| 3 | **Leading Element** (引化) | Target element appears on another Heavenly Stem or as main hidden stem |
| 4 | **No Obstruction** (无阻碍) | No 冲 on either combining branch from a third natal branch |

**午未 Dual Transform Logic:**
- Default target = Fire (from `LIU_HE_PAIR_TO_ELEMENT`)
- If month supports Earth but not Fire, OR if Earth-element stems are leading → switch to Earth
- If both match equally, prefer Fire (traditional default)

### 2.3 三合 Transformation Evaluation

Currently `三合` is detected as a set of 3 branches. Add transformation evaluation:

```python
def evaluate_san_he_transformation(
    chart: Dict,
    trio: frozenset,
) -> Dict:
    """Evaluate whether a Three Combination (三合) successfully forms an elemental frame.
    
    A full 三合 (all 3 branches present) is very strong — it transforms if:
    1. The 帝旺 (emperor) branch of the trio is present (always true for full trio)
    2. Month branch is part of the trio OR month element matches/generates target
    3. No severe 冲 on the 帝旺 branch from outside the trio
    """
```

### 2.4 半三合 Strength Classification

Distinguish between 生地半合 (Birth-phase: stronger, forward momentum) and 墓地半合 (Grave-phase: weaker, storage/completion energy):

```python
def classify_ban_san_he(pair: frozenset) -> Dict:
    """Classify a half-trio as birth-phase or grave-phase.
    
    Returns: {
        "type": "生地半合" | "墓地半合",
        "element": str,
        "strength": "moderate" | "weak",
        "needs": str  # the missing branch to complete the trio
    }
    """
```

### 2.5 Interaction Priority Resolution

Add a new function that processes all raw interactions and resolves conflicts:

```python
def resolve_interaction_conflicts(
    interactions: Dict[str, list],
) -> Dict[str, list]:
    """Apply classical priority rules to resolve conflicting interactions.
    
    Rules (in priority order):
    1. 三会 > 三合 > 六合 — stronger combinations take precedence
    2. If a branch is in both 合 and 冲:
       - 合 from adjacent pillars can resolve non-adjacent 冲
       - If both are adjacent, 冲 wins (冲散合)
       - If 合 includes the month branch and 冲 does not, 合 wins
    3. Self-punishment (自刑) is always additive — never overridden
    4. 暗合 is active only when no explicit 六合 exists for that branch
    5. 拱合 is nullified if the missing branch appears via 大运/流年
    """
```

### 2.6 Deliverables

- [ ] Add 六破, 暗合, 拱合 detection to `detect_branch_interactions()`
- [ ] Implement `evaluate_liu_he_transformation()`
- [ ] Implement `evaluate_san_he_transformation()`
- [ ] Implement `classify_ban_san_he()`
- [ ] Implement `resolve_interaction_conflicts()`
- [ ] Wire transformations into the interaction results dict

### 2.7 Tests (Phase 2)

| Test Class | Scenarios |
|------------|-----------|
| `TestLiuPo` | 子酉破 detected; no false positive for non-破 pairs |
| `TestAnHe` | 寅丑暗合 detected; not detected when 六合 already present for same branch |
| `TestGongHe` | 寅戌拱火 detected; not detected when 午 (middle) is present |
| `TestLiuHeTransform` | 子丑 adjacent + month=Earth → Hóa; non-adjacent → Hợp Nhi Bất Hóa |
| `TestLiuHeWuWei` | 午未 in Earth month → 化土; in Fire month → 化火 |
| `TestSanHeTransform` | 申子辰 full trio with Water month → successful Water frame |
| `TestBanSanHeClassify` | 申子 = Birth-phase Water; 子辰 = Grave-phase Water |
| `TestInteractionConflict` | Branch in both 合 and 冲 → correct winner |

---

## 3. Phase 3 — Stem Interaction Improvements (`stem_transformations.py`)

### 3.1 Jealous Combination Detection (争合)

When the same stem appears in multiple pillars and could combine with different partners, detect 争合:

```python
def detect_jealous_combinations(chart: Dict) -> List[Dict]:
    """Detect Jealous Combinations (争合) where a stem has multiple potential partners.
    
    Example: Year=甲, Month=己, Hour=己 → Month-己 and Hour-己 both
    contest for 甲. Result: neither combination transforms successfully.
    
    Returns list of:
      {"contested_stem": str, "pillar": str, "contestants": [(pillar, stem), ...]}
    """
```

### 3.2 Remote Combination Tagging (遥合)

Non-adjacent stem pairs currently get `proximity_score=1` and may still produce "Hợp (bound)". Tag these explicitly as 遥合 (Remote Combination) using the glossary term:

```python
# In detect_transformations(), after computing proximity_score:
if not is_adjacent:
    # Remote combination — affinity only, cannot transform
    status = "遥合 (Remote)"
    confidence = 30
    # Skip further condition checking
```

### 3.3 Stem Restraint Detection (天干相克)

Add detection of pure stem restraints (克) as a complementary layer alongside combinations and clashes:

```python
def detect_stem_restraints(chart: Dict) -> List[Dict]:
    """Detect Heavenly Stem Restraints (天干相克) between natal pillars.
    
    Unlike 冲 (clashes) which are mutual destruction between opposing elements,
    克 (restraints) are directional: the restraining stem weakens the restrained.
    
    Returns list of:
      {"attacker": (pillar, stem), "target": (pillar, stem),
       "attacker_element": str, "target_element": str,
       "is_adjacent": bool, "severity": int}
    
    Severity rules:
    - Adjacent attacker-target: severity = 80
    - Yang attacks Yin of same element pair: severity = 70 (harsher)
    - Month pillar as attacker: severity += 10
    """
```

### 3.4 Stem Clash Enrichment

Currently stem clashes are detected only during the stem combination scan. Add explicit stem clash detection using `STEM_CLASH_PAIRS`:

```python
def detect_stem_clashes(chart: Dict) -> List[Dict]:
    """Detect the four Heavenly Stem Clashes (天干相冲): 甲庚, 乙辛, 丙壬, 丁癸."""
```

### 3.5 Deliverables

- [ ] Implement `detect_jealous_combinations()`
- [ ] Tag remote combinations as 遥合
- [ ] Implement `detect_stem_restraints()`
- [ ] Implement `detect_stem_clashes()`
- [ ] Enrich `detect_transformations()` result dicts with glossary Term references

### 3.6 Tests (Phase 3)

| Test | Chart Setup | Expected |
|------|-------------|----------|
| `test_jealous_combination` | Year=甲, Month=己, Hour=己 | 争合 detected, neither transforms |
| `test_remote_combination` | Year=甲, Hour=己 (non-adjacent) | Status = "遥合 (Remote)" |
| `test_stem_restraint_adjacent` | Month=庚, Day=甲 | 庚克甲 severity ≥ 80 |
| `test_stem_clash_bing_ren` | Day=丙, Year=壬 | 丙壬冲 detected |

---

## 4. Phase 4 — Rooting & Tomb Analysis (new: `rooting.py`)

### 4.1 New Module: `rooting.py`

Create a dedicated module for rooting analysis (通根) and tomb/treasury mechanics (墓库). These are foundational for accurate DM strength scoring and structure classification.

```python
"""
Rooting & Tomb/Treasury Analysis (通根 & 墓库)
===============================================
"""

def analyze_stem_roots(chart: Dict) -> Dict[str, Dict]:
    """Analyze rooting depth of every Heavenly Stem in the chart.
    
    For each natal stem (8 stems: 4 pillar stems), find all branch roots:
    
    Returns: {
        "year_stem": {
            "stem": "甲",
            "roots": [
                {"branch": "寅", "pillar": "month", "qi": "本气", "strength": 1.0},
                {"branch": "亥", "pillar": "hour", "qi": "余气", "strength": 0.3},
            ],
            "total_root_strength": 1.3,
            "is_rooted": True,
        },
        ...
    }
    
    Qi strengths:
    - 本气 (Main Qi): 1.0
    - 中气 (Middle Qi): 0.5
    - 余气 (Residual Qi): 0.3
    
    A stem with total_root_strength == 0 is 虚浮 (Unrooted / Vain-Floating).
    """


def analyze_dm_rooting(chart: Dict) -> Dict:
    """Focused rooting analysis for the Day Master only.
    
    Returns: {
        "stem": str,
        "element": str,
        "roots": [...],
        "total_strength": float,
        "classification": "deeply_rooted" | "moderately_rooted" | "weakly_rooted" | "unrooted",
        "is_jian_lu": bool,       # DM's Lộc (禄) in month branch
        "is_yang_ren": bool,      # DM's 羊刃 in natal branches
    }
    
    Classification thresholds:
    - deeply_rooted: total ≥ 2.0 (multiple main-qi roots)
    - moderately_rooted: 1.0 ≤ total < 2.0
    - weakly_rooted: 0 < total < 1.0
    - unrooted: total == 0
    """


def analyze_tomb_treasury(chart: Dict) -> List[Dict]:
    """Analyze Tomb/Treasury (墓库) relationships for all elements in the chart.
    
    For each of the four Tomb branches (辰戌丑未) present in natal pillars:
    1. Determine which elements are in tomb (入墓) vs treasury (入库)
    2. Check if any 冲 or 刑 opens the treasury (开库/冲库)
    
    Rules:
    - An element enters its TOMB (入墓) when it is WEAK and meets its tomb branch
    - An element enters its TREASURY (入库) when it is STRONG and meets its tomb branch
    - 辰戌冲 or 丑未冲 opens both treasuries, releasing hidden stems
    - 丑戌未 刑 (Bully punishment) also opens the tombs
    
    Returns list of:
      {"branch": str, "pillar": str, "element_stored": str,
       "status": "入墓" | "入库", "is_opened": bool, "opened_by": str | None}
    """
```

### 4.2 Deliverables

- [ ] Create `bazi/rooting.py`
- [ ] Implement `analyze_stem_roots()`, `analyze_dm_rooting()`, `analyze_tomb_treasury()`
- [ ] Wire rooting into `scoring.py` (replace raw hidden-stem counting with rooting strengths)
- [ ] Wire tomb analysis into `analysis.py` comprehensive output

### 4.3 Tests (Phase 4)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_jia_rooted_in_yin` | 甲 stem, 寅 branch present | Main-qi root, strength=1.0 |
| `test_unrooted_stem` | 甲 stem, no Wood branches | `is_rooted=False`, classification="unrooted" |
| `test_tomb_wood_in_wei` | DM=甲 weak, 未 in chart | 入墓 (entering tomb) |
| `test_treasury_opened_by_chong` | 辰 and 戌 both present | `is_opened=True`, `opened_by="冲"` |
| `test_dm_jian_lu` | DM=甲, month branch=寅 | `is_jian_lu=True` |

---

## 5. Phase 5 — Structure Classifier Overhaul (`structure.py`)

### 5.1 Current Problems

`classify_structure()` currently:
1. Uses only `detect_month_pillar_structure()` (month hidden stem → Ten God) as primary signal
2. Falls back to `weighted_ten_god_distribution()` dominance
3. `detect_special_structures()` returns `None` always (stub)
4. No evaluation of extreme-prosperous, follow, or transform structures
5. `_assess_structure_quality()` uses hardcoded heuristics without interaction data

### 5.2 Architecture: Three-Tier Classification

Replace the flat classifier with a three-tier system that mirrors classical theory:

```
Tier 1: Special Structures (highest priority — if conditions met, skip Tier 2/3)
  ├── Transform Structures (化格): Check if Day Master is part of a successful stem transformation
  ├── Follow Structures (从格): Check if DM is extremely weak with no root, no support
  └── Five-Element Dominance (专旺格): Check if one element dominates via 三合 + 三会 + season

Tier 2: Extreme Prosperous (旺极格)
  ├── 建禄格 (Establish Fortune): DM's Lộc in month branch
  └── 羊刃格 (Goat Blade): DM's 羊刃 in month branch

Tier 3: Eight Regular Structures (八正格) — current default path
  └── Month pillar protrusion → Ten God → structure name
```

### 5.3 Implement `detect_special_structures()`

```python
def detect_special_structures(
    chart: Dict,
    strength: str,
    score: float,
    rooting: Dict,
    interactions: Dict,
    transformations: List[Dict],
) -> Optional[Dict]:
    """Detect special structures (Tier 1) with full context.
    
    Checks in order:
    
    1. TRANSFORM STRUCTURES (化格):
       - DM must be part of a successful stem transformation (status="Hóa")
       - The transformed element dominates the chart
       - Map to glossary: ELEMENT_TO_TRANSFORM_STRUCTURE
    
    2. FOLLOW STRUCTURES (从格):
       a. 从财格: DM extremely weak, chart dominated by Wealth elements
       b. 从官杀格: DM extremely weak, chart dominated by Officer/Killings
       c. 从食伤格: DM extremely weak, chart dominated by Output (食伤)
       d. 从强格: DM extremely strong (paradoxically), follows its own strength
       e. 从势格: DM weak but follows the dominant momentum of the chart
       
       Common conditions for all 从格:
       - DM has NO root (unrooted / 虚浮)
       - No Direct/Indirect Resource (印) supporting DM
       - The dominant element/category ≥ 70% of weighted distribution
    
    3. FIVE-ELEMENT DOMINANCE (专旺格):
       - DM's element has ≥ 3 supporting branches (三合 or 三会 of same element)
       - Month branch is part of the dominant group
       - Season (month) prospers or generates DM's element
       - Map: "Wood" → 曲直格, "Fire" → 炎上格, etc.
    
    Returns None if no special structure detected.
    Returns Dict with keys: primary, category, quality, element, confidence
    """
```

### 5.4 Implement `detect_extreme_prosperous()`

```python
def detect_extreme_prosperous(
    chart: Dict,
    strength: str,
    rooting: Dict,
) -> Optional[Dict]:
    """Detect Tier 2: 建禄格 or 羊刃格.
    
    建禄格 conditions:
    - DM's 禄 (Lộc / Prosperity) branch IS the month branch
    - DM strength is "strong" or "balanced"
    - No 比肩/劫财 serves as structure base (they redirect to 建禄/羊刃)
    
    羊刃格 conditions:
    - DM's 羊刃 (Goat Blade) branch IS the month branch  
    - DM strength is "strong"
    - Stronger and more dangerous variant of 建禄
    """
```

### 5.5 Enhance `_assess_structure_quality()`

Replace hardcoded heuristics with interaction-aware quality assessment:

```python
def _assess_structure_quality(
    chart: Dict,
    primary_tg: str,
    strength: str,
    dist: Dict[str, float],
    interactions: Dict,
    transformations: List[Dict],
) -> Tuple[str, bool]:
    """Assess structure quality (成格 vs 破格) using interaction data.
    
    New factors considered:
    1. If primary structure's Useful God is 冲'd → 破格 risk
    2. If 食神制杀 pattern exists → 成格 (special composite structure)
    3. If 伤官配印 pattern exists → 成格 (special composite)
    4. If month-pillar hidden stem is 合住 (bound by combination) → weakened
    5. If 六合 transforms the month branch element away → structure pivot
    """
```

### 5.6 Composite Structure Detection

Add detection for the special composite structures defined in glossary §II-D:

```python
def detect_composite_structures(
    chart: Dict,
    primary_tg: str,
    dist: Dict[str, float],
) -> Optional[str]:
    """Detect special composite structures that override or refine the primary.
    
    Patterns:
    - 食神制杀: 食神 and 七杀 both present, 食神 controls 杀 → 食神制杀格
    - 伤官配印: 伤官 and 正印 both present, 印 restrains 伤 → 伤官配印格
    - 伤官见官: 伤官 and 正官 both present → 伤官见官格 (usually 破格)
    - 财滋两旺: 财 generates 官, both strong → 财滋两旺格
    - 财印双全: Both 财 and 印 present without clash → 财印双全格
    - 杀印相生: 七杀 + 印, 杀 generates 印, 印 protects DM → 杀印相生格
    """
```

### 5.7 Updated `classify_structure()` Flow

```python
def classify_structure(chart, strength, score=None, rooting=None,
                       interactions=None, transformations=None):
    # 1. Gather context if not provided
    if score is None:
        score, _ = score_day_master(chart)
    if rooting is None:
        rooting = analyze_dm_rooting(chart)
    if interactions is None:
        interactions = detect_branch_interactions(chart)
    if transformations is None:
        transformations = detect_transformations(chart)
    
    # 2. Tier 1: Special structures
    special = detect_special_structures(
        chart, strength, score, rooting, interactions, transformations
    )
    if special:
        return special
    
    # 3. Tier 2: Extreme prosperous
    extreme = detect_extreme_prosperous(chart, strength, rooting)
    if extreme:
        return extreme
    
    # 4. Tier 3: Eight Regular Structures (existing logic, enhanced)
    month_tg = detect_month_pillar_structure(chart)
    dist = weighted_ten_god_distribution(chart)
    
    # Check for composite structures
    composite = detect_composite_structures(chart, month_tg, dist)
    
    # Determine primary structure
    primary_tg = ...  # existing logic
    
    # Assess quality with interaction awareness
    quality, is_broken = _assess_structure_quality(
        chart, primary_tg, strength, dist, interactions, transformations
    )
    
    return { ... }
```

### 5.8 Backward Compatibility

The existing `classify_structure(chart, strength)` signature must remain valid. New parameters (`score`, `rooting`, `interactions`, `transformations`) default to `None` and are computed internally when absent. Existing callers and tests continue to work unchanged.

### 5.9 Deliverables

- [ ] Implement `detect_special_structures()` (Transform, Follow, Dominance)
- [ ] Implement `detect_extreme_prosperous()` (建禄格, 羊刃格)
- [ ] Implement `detect_composite_structures()` (食神制杀, 伤官配印, etc.)
- [ ] Enhance `_assess_structure_quality()` with interaction awareness
- [ ] Update `classify_structure()` to use three-tier flow
- [ ] Maintain backward-compatible signature

### 5.10 Tests (Phase 5)

| Test | Chart Setup | Expected Structure |
|------|-------------|-------------------|
| `test_follow_wealth` | DM=癸 unrooted, all pillars Fire/Earth | 从财格 |
| `test_follow_officer` | DM=乙 unrooted, 庚 dominant | 从官杀格 |
| `test_transform_earth` | DM=甲, Month=己, 甲己合化土 successful | 化土格 |
| `test_wood_dominance` | DM=甲, 亥卯未 + 寅 spring month | 曲直格 |
| `test_jian_lu` | DM=甲, month branch=寅 | 建禄格 |
| `test_yang_ren` | DM=甲, month branch=卯 | 羊刃格 |
| `test_shishen_zhisha` | 食神 + 七杀 both present, 食 dominant | 食神制杀格 |
| `test_shangguan_peiyin` | 伤官 + 正印, balanced | 伤官配印格 |
| `test_existing_tests_unchanged` | Current test fixtures | Same results as before |

---

## 6. Phase 6 — Scoring Overhaul (`scoring.py`)

### 6.1 Interaction-Aware DM Scoring

Replace the current linear `score_day_master()` with a multi-factor scorer that accounts for:

```python
def score_day_master(chart: Dict, interactions: Dict = None,
                     rooting: Dict = None) -> Tuple[float, str]:
    """Enhanced Day Master strength scoring.
    
    Factors (ordered by weight):
    
    1. SEASONAL STRENGTH (月令 — unchanged, highest weight)
       - Month branch element relation to DM element
       - Weight: ×3.0 (month pillar weight)
    
    2. ROOTING DEPTH (通根 — replaces raw hidden-stem counting)
       - Use rooting.total_strength from analyze_dm_rooting()
       - Main-qi roots count more than residual
       - Weight: per pillar weight (year=1.0, month=3.0, day=1.5, hour=1.0)
    
    3. VISIBLE STEM SUPPORT (天干 — unchanged)
       - Same-element or Resource-element stems on other pillars
    
    4. INTERACTION ADJUSTMENTS (new):
       a. 三合/三会 forming DM's element → +3 pts
       b. 三合/三会 forming element that controls DM → -3 pts
       c. 六合 transforming away a root branch → -2 pts
       d. 六冲 on month branch → -2 pts (weakens seasonal support)
       e. DM's root branch 入墓 (in tomb, not opened) → -1.5 pts
       f. DM's root branch is Void (空亡) → -1 pt
    
    5. EXTREME DETECTION:
       - If score ≥ 10 AND no controlling element present → "extreme_strong"
       - If score ≤ -6 AND no resource/companion → "extreme_weak"
    
    Classification thresholds (updated):
       extreme_strong: score ≥ 10
       strong: 6 ≤ score < 10
       balanced: -3 < score < 6
       weak: -6 < score ≤ -3
       extreme_weak: score ≤ -6
    """
```

### 6.2 Enhanced `recommend_useful_god()`

Make Useful God recommendation structure-aware:

```python
def recommend_useful_god(chart, strength, structure=None):
    """Structure-aware Useful God recommendation.
    
    Special cases:
    - 从格 (Follow): Useful God = the dominant element being followed
    - 化格 (Transform): Useful God = transformed element or its producer
    - 食神制杀: Useful God = 食神's element
    - 伤官配印: Useful God = 印's element
    - 建禄/羊刃: Useful God = element that drains excess (食伤 or 财)
    
    Return structure expanded with:
    - useful_god: str (Dụng Thần — primary favorable element)
    - joyful_god: str (Hỉ Thần — secondary favorable)
    - taboo_god: str (Kỵ Thần — primary unfavorable)
    - enmity_god: str (Cừu Thần — secondary unfavorable)
    """
```

### 6.3 Enhanced `rate_chart()`

Update the 100-point rating to use interaction outcomes:

| Factor | Max Points | Current | Proposed Change |
|--------|-----------|---------|-----------------|
| Strength balance | 30 | 3 tiers | 5 tiers (extreme_strong/strong/balanced/weak/extreme_weak) |
| Structure purity | 25 | dominance_score only | + `is_broken` penalty, + composite structure bonus |
| Element spread | 20 | count unique elements | Same |
| Root depth | 15 | raw hidden stem count | Use `analyze_dm_rooting().total_strength` |
| Interaction stability | 10 | clash penalty only | + 合 bonus, - 刑/害/破 penalty, void adjustment |

### 6.4 Deliverables

- [ ] Enhance `score_day_master()` with interaction adjustments
- [ ] Add `extreme_strong` / `extreme_weak` classifications
- [ ] Enhance `recommend_useful_god()` with structure-aware logic
- [ ] Update `rate_chart()` with refined scoring
- [ ] Maintain backward compatibility (interactions/rooting params default to None)

### 6.5 Tests (Phase 6)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_san_he_boost` | DM=壬, 申子辰 Water frame | Score higher than without frame |
| `test_chong_on_month_penalty` | Month branch 冲'd | Score lower than without clash |
| `test_extreme_strong_classification` | Very high score, no control | strength="extreme_strong" |
| `test_extreme_weak_classification` | Very low score, no resource | strength="extreme_weak" |
| `test_useful_god_follow_structure` | 从财格 | Useful God = Wealth element |
| `test_rate_chart_broken_penalty` | 破格 structure | Lower total than 成格 |

---

## 7. Phase 7 — Void Branch Integration (`symbolic_stars.py`, `branch_interactions.py`)

### 7.1 Void Effect on Interactions

Currently void branches are detected but never affect interaction resolution. Add integration:

```python
def apply_void_effects(
    chart: Dict,
    interactions: Dict,
) -> Dict:
    """Apply Void Branch (空亡) effects to interaction results.
    
    Rules:
    - A void branch's 六合 is weakened (合 exists but cannot 化)
    - A void branch's 六冲 is weakened (冲 exists but damage reduced)
    - A void branch participating in 三合/三会 weakens the frame
    - Symbolic stars on void branches lose effectiveness
    - 刑 on void branches still applies but at reduced severity
    
    Void is RESOLVED (解空) when:
    - The branch receives 冲 from 大运/流年 (fills the void)
    - The branch receives 合 from 大运/流年 (resolves emptiness)
    
    Note: This applies to natal chart only. Dynamic pillars (流年/大运)
    can resolve void — handled in analysis.py's time-range analysis.
    """
```

### 7.2 Deliverables

- [ ] Implement `apply_void_effects()`
- [ ] Wire into `detect_branch_interactions()` output
- [ ] Add void status to symbolic star results
- [ ] Document void interaction in comprehensive analysis output

### 7.3 Tests (Phase 7)

| Test | Expected |
|------|----------|
| Void branch in 六合 → status includes "weakened_by_void" | |
| Non-void branch interactions unchanged | |
| Void resolved by incoming 冲 from 流年 | |

---

## 8. Phase 8 — Analysis Module Integration (`analysis.py`)

### 8.1 Update `comprehensive_analysis()`

Wire all new subsystems into the comprehensive output:

```python
def comprehensive_analysis(chart: Dict) -> Dict:
    """Enhanced comprehensive analysis.
    
    New output fields:
    - rooting: analyze_dm_rooting() result
    - tomb_treasury: analyze_tomb_treasury() result
    - liu_he_transformations: list of evaluated 六合 outcomes
    - san_he_transformations: list of evaluated 三合 outcomes
    - hidden_combinations: list of 暗合
    - arching_combinations: list of 拱合
    - stem_restraints: list of 天干相克
    - stem_clashes: list of 天干冲
    - jealous_combinations: list of 争合
    - void_effects: applied void branch effects
    - structure (enhanced): full three-tier classification
    - useful_god (enhanced): 5-god recommendation
    
    Updated natal_interactions dict:
    - Add "六破", "暗合", "拱合" keys
    - Add transformation outcome to "六合" entries
    - Add frame outcome to "三合" entries
    """
```

### 8.2 Update `analyze_time_range()`

Enhance the dynamic pillar analysis with:

1. **Void resolution**: Check if incoming year/month/day branch resolves a natal void
2. **Incoming 三合**: Check if incoming branch completes a natal 半三合 or 拱合 into a full 三合
3. **Tomb opening**: Check if incoming branch 冲's a natal tomb, releasing stored elements
4. **Interaction cascade**: Incoming branch interactions can change structure classification

### 8.3 Deliverables

- [ ] Update `comprehensive_analysis()` with all new fields
- [ ] Update `analyze_time_range()` with void resolution, trio completion, tomb opening
- [ ] Update summary text generation to mention new interactions
- [ ] Ensure all existing test assertions still pass

### 8.4 Tests (Phase 8)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_comprehensive_has_rooting` | Any chart | Result has "rooting" key |
| `test_comprehensive_has_tomb` | Chart with 辰/戌/丑/未 | Result has "tomb_treasury" |
| `test_time_range_void_resolution` | Void branch + incoming 冲 | "void_resolved" in result |
| `test_time_range_trio_completion` | 半三合 + incoming third | "trio_completed" in result |

---

## 9. Phase 9 — Narrative & Report Updates (`narrative.py`, `report.py`)

### 9.1 Narrative Enhancements

- Add interpretation text for new structure types (从格, 化格, 专旺格)
- Add rooting assessment to personality section
- Add tomb/treasury interpretation
- Add void branch interpretation

### 9.2 Report Enhancements

Add new Markdown sections to `generate_report_markdown()`:

```markdown
## 🌳 Rooting Analysis (通根)
| Stem | Element | Root Branches | Qi Type | Total Strength | Status |
|------|---------|--------------|---------|----------------|--------|

## ⚰️ Tomb & Treasury (墓库)
| Branch | Pillar | Element Stored | Status | Opened By |
|--------|--------|---------------|--------|-----------|

## 🕳️ Void Branches (空亡)
| Branch | Pillar | Affected Interactions | Status |
|--------|--------|----------------------|--------|
```

### 9.3 Deliverables

- [ ] Update `narrative.py` for new structure types
- [ ] Update `report.py` with new sections
- [ ] Ensure report renders correctly with all new data

---

## 10. Implementation Order & Dependencies

```
Phase 1: constants.py data layer          ← No dependencies, start here
    │
    ├──→ Phase 2: branch_interactions.py  ← Needs Phase 1 constants
    │        │
    ├──→ Phase 3: stem_transformations.py ← Needs Phase 1 constants
    │        │
    └──→ Phase 4: rooting.py (new)        ← Needs Phase 1 constants
             │
             ├──→ Phase 5: structure.py   ← Needs Phase 2 + 3 + 4
             │        │
             └──→ Phase 6: scoring.py     ← Needs Phase 4 + 5
                      │
                      ├──→ Phase 7: void  ← Needs Phase 2 + 6
                      │
                      └──→ Phase 8: analysis.py ← Needs all above
                               │
                               └──→ Phase 9: narrative + report ← Needs Phase 8
```

Phases 2, 3, 4 can proceed in parallel after Phase 1.  
Phase 5 depends on 2 + 3 + 4.  
Phase 6 depends on 4 + 5.  
All remaining phases are sequential.

---

## 11. Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing 170 tests | High | Every phase maintains backward-compatible signatures; new params default to None |
| Circular imports (rooting ↔ scoring ↔ structure) | Medium | `rooting.py` depends only on `constants.py`; pass results as params, no circular deps |
| Over-engineering structure classifier | Medium | Implement Tier 1 (special) only for clear-cut cases; default to existing Tier 3 for ambiguous charts |
| Performance regression from nested interaction scans | Low | Branch interaction is O(n²) where n=4; adding evaluations doesn't change complexity |
| Glossary/constants drift from runtime logic | Low | All interaction sets derive from glossary single-source-of-truth; tested at constants level |

---

## 12. Success Criteria

1. All 170 existing tests pass unchanged
2. New test count: ~60 additional tests across Phases 1–8
3. `classify_structure()` correctly identifies at least:
   - 8 Regular Structures (existing)
   - 建禄格, 羊刃格 (Tier 2)
   - 从财格, 从官杀格 (Tier 1 Follow)
   - 化土格 through 化火格 (Tier 1 Transform)
   - 曲直格 through 润下格 (Tier 1 Dominance)
   - 食神制杀格, 伤官配印格 (Composite)
4. `detect_branch_interactions()` returns 六破, 暗合, 拱合 in addition to existing types
5. 六合 and 三合 entries include transformation outcome evaluation
6. `score_day_master()` returns 5-tier classification including extreme_strong/extreme_weak
7. `recommend_useful_god()` returns 5-god recommendation (用神, 喜神, 忌神, 仇神, 闲神)
8. Rooting analysis surfaces 虚浮 (unrooted) stems
9. Tomb/Treasury analysis identifies 入墓/入库 status and opening conditions

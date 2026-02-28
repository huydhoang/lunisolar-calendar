# Bazi Completeness Implementation Plan

> **Status**: Draft  
> **Date**: 2026-02-28  
> **Prerequisite**: `plan_bazi_modular_refactor.md` (module extraction must be complete first)  
> **Source**: `contexts/0002_bazi_completeness_evaluation.md`  
> **Goal**: Close the gaps identified in the completeness evaluation — bring Core Bazi to ~98%, Na Yin to ~85%, Stem Combinations to ~95%, and add foundational cosmological data layers (He Tu, Luo Shu, Ba Gua)

---

## 0. Scope & Open Questions

### 0.1 Decisions Required Before Implementation

The following questions must be resolved before work begins on the corresponding phases. Each is tagged with the phase it blocks.

#### Q1 — Cosmological Systems Scope (blocks Phase 5–7)

The evaluation lists He Tu, Luo Shu, Ba Gua, I Ching, Tai Xuan Numbers, and Da Yan Zhi Shu as 0% implemented. However, it also notes these are **"typically domain-specific to Feng Shui, Qi Men Dun Jia, or Liu Ren rather than pure Four-Pillars analysis."**

**Question**: Which of these should be implemented, and in what capacity?

| System | Option A: Bazi-integrated | Option B: Standalone module | Option C: Skip |
|--------|--------------------------|----------------------------|----------------|
| **He Tu (河圖)** | Use He Tu number pairs to enrich stem/branch analysis (e.g. He Tu combination = special affinity between stems sharing a number pair) | `hetu.py` — pure data + lookup, no Bazi coupling | Skip |
| **Luo Shu (洛書)** | Annual/monthly Flying Star palace calculation, integrate into projections | `luoshu.py` — Nine Palace + Flying Star engine, usable by Feng Shui or Bazi | Skip |
| **Ba Gua (八卦)** | Map stems/branches to trigrams, add trigram field to pillars | `bagua.py` — Earlier/Later Heaven arrangements, hexagram lookup | Skip |
| **I Ching / Da Yan (易經 / 大衍之數)** | Unlikely to be useful inside pure Bazi | `yijing.py` — 64 hexagrams, Na Jia, yarrow stalk method | Skip |
| **Tai Xuan Numbers (太玄數)** | Nine Palace Flying Stars in annual flow | Part of Luo Shu module | Skip |

**Recommendation**: Option B for He Tu & Luo Shu (useful data layers with clear Bazi touchpoints), Option C for I Ching / Da Yan (separate divination system, not Four Pillars). Ba Gua could go either way — it adds data but needs a clear application method within Bazi.

#### Q2 — Na Yin Special Interaction Rules Authority (blocks Phase 3)

Classical Na Yin theory has specific interaction rules beyond Five-Element generation/control. For example:
- 金入火熔 (Metal Na Yin entering Fire = "Metal smelted", inauspicious)
- 水入土塞 (Water Na Yin meeting Earth = "Water blocked", inauspicious)
- Special affinities between certain Na Yin types (e.g. 剑锋金 Sword Metal + 大海水 Ocean Water = auspicious tempering)

**Question**: Which classical source should serve as the authority for Na Yin interaction rules?
- **三命通会 (Sān Mìng Tōng Huì)** — most comprehensive classical reference
- **渊海子平 (Yuān Hǎi Zǐ Píng)** — foundational text, simpler Na Yin rules
- **Simplified modern synthesis** — extract the most commonly agreed-upon rules across schools

#### Q3 — Ten God Pillar Weighting (blocks Phase 1.3)

Current code: Year=2, Month=3, Day=5, Hour=2 (via `PILLAR_WEIGHTS`).  
Evaluation note: "Many schools treat the Hour pillar as weaker than the Month and Day pillars."

**Question**: Should the Hour pillar weight be reduced (e.g., Hour=1.5 or Hour=1) to reflect the position that the Hour pillar carries less weight in Ten-God distribution? Or keep the current symmetry with the Year pillar?

Common schemes in practice:
| School | Year | Month | Day | Hour |
|--------|------|-------|-----|------|
| Current code | 2 | 3 | 5 | 2 |
| Conservative traditional | 2 | 3 | 5 | 1.5 |
| Month-dominant | 1.5 | 4 | 5 | 1 |

#### Q4 — Na Yin-based Growth Stages (blocks Phase 3.3)

Some schools derive the Twelve Growth Stages from the **Na Yin element** of the Day Pillar rather than the **Day Stem element**. This produces different stage assignments.

**Question**: Should this be implemented as:
- **(a)** An optional alternative mode (toggle via parameter)?
- **(b)** An additional data field alongside the existing stem-based stages?
- **(c)** Deferred / skipped — too school-specific for a general engine?

---

## 1. Phase 1 — Core Bazi Gaps (85% → ~98%)

**Estimated modules affected**: `structure.py`, `annual_flow.py`, `branch_interactions.py`, `scoring.py`, `symbolic_stars.py`

### 1.1 Implement Follower & Transformation Structures (格局)

**Current state**: `detect_special_structures()` in `structure.py` returns `None` (stub).

**Target**: Detect and classify the five major special structures:

| Structure | Chinese | Condition |
|-----------|---------|-----------|
| Follower of Wealth | 从财格 (Cóng Cái Gé) | Day Master extremely weak, no print/peer support, Wealth dominates |
| Follower of Power | 从杀格 (Cóng Shā Gé) | Day Master extremely weak, no print/peer support, Seven Killings dominates |
| Follower of Output | 从伤官格 (Cóng Shāng Guān Gé) | Day Master extremely weak, no print/peer support, Hurt Officer / Eating God dominates |
| Follower of Strength | 从旺格 (Cóng Wàng Gé) | Day Master extremely strong, all pillars are same element / print element, no opposing elements |
| Transformation | 化格 (Huà Gé) | Day Master stem successfully transforms (from `detect_transformations()`), transformed element dominates the chart |

**Algorithm outline**:
1. Check Day Master strength score — must be extreme (< threshold for followers, > threshold for Cóng Wàng)
2. For follower structures: verify no Resource (印) or Peer (比劫) stems/branches support the Day Master
3. For Cóng Wàng: verify no Wealth/Officer/Power opposing elements
4. For Huà Gé: check if a successful transformation exists from `detect_transformations()` and the transformed element has overwhelming support
5. Return structure type, confidence, favorable/unfavorable elements

**Files**: `structure.py`  
**Tests**: Add test cases for each special structure type with pre-crafted charts

### 1.2 San He / Half-San He Detection in Annual Flow

**Current state**: `annual_flow.py` checks only pairwise interactions (clash, combine, harm). Three-combination (三合) and half-three-combination (半三合) against the natal chart are not checked.

**Target**: When analyzing an annual flow branch, check if it completes or contributes to a San He or Ban San He with natal chart branches.

**Algorithm**:
1. Collect all natal branches (year, month, day, hour)
2. For each annual flow branch, check all (annual, natal_i, natal_j) triples against `SAN_HE` table
3. Also check (annual, natal_i) pairs against `BAN_SAN_HE` table
4. Report completed San He (element produced) and half-San He with their potential

**Files**: `annual_flow.py`, `branch_interactions.py` (may need a helper to check triples involving an external branch)  
**Tests**: Chart with Yin-Wu-Xu branches where an annual flow year supplies the missing branch

### 1.3 Ten God Pillar Weighting Review

**Blocked by**: Q3 above.

If weighting changes are approved, update `PILLAR_WEIGHTS` in `constants.py` and adjust any downstream threshold that depends on the current weight distribution.

**Files**: `constants.py`, `scoring.py` (threshold review)

### 1.4 Dynamic Void in Luck Pillars & Annual Flow

**Current state**: Void branches (空亡) are calculated only from the Day Pillar's Xun (旬). This is correct for natal chart assessment, but:
- Each **luck pillar** has its own Xun → its own void branches
- Each **annual pillar** has its own Xun → its own void branches
- A branch that is void in the natal chart may "exit void" (出空) when a luck pillar or annual year activates it

**Target**:
1. Calculate void branches for each luck pillar's stem-branch pair
2. Calculate void branches for each annual flow year
3. Detect "exit void" events: a natally void branch that appears in a non-void position during a luck pillar or annual year
4. Add `void_branches` and `exit_void` fields to luck pillar and annual flow output dicts

**Files**: `symbolic_stars.py` (add `void_branches_for_ganzhi()` utility), `luck_pillars.py`, `annual_flow.py`  
**Tests**: Chart where a natally void branch exits void during a specific luck pillar

---

## 2. Phase 2 — Heavenly Stem Combinations Completion (80% → ~95%)

**Estimated modules affected**: `stem_transformations.py`, `scoring.py`, `analysis.py`, `annual_flow.py`

### 2.1 Full Transformation Detection with External Stems

**Current state**: `analyze_time_range()` detects stem pairing via `STEM_TRANSFORMATIONS` lookup but does **not** call the full `detect_transformations()` (with adjacency, month command, obstruction, clash conditions) when an external stem (luck pillar or annual year) is involved.

**Target**: When a luck pillar or annual year stem forms a combination pair with a natal stem:
1. Build a temporary extended pillar list: `[luck/annual pillar] + [four natal pillars]`
2. Call `detect_transformations()` on this extended list
3. Report transformation status (transformed / bound / failed) in the luck pillar or annual flow output

**Files**: `analysis.py` (in `analyze_time_range()`), `annual_flow.py` (in `annual_analysis()`)  
**Tests**: Luck pillar Jia combining with natal Ji — verify full condition checking

### 2.2 "Bound but Not Transformed" Downstream Effects (合而不化)

**Current state**: When two stems combine but transformation conditions are not met, the status `"Hợp (bound)"` is returned. However, this does **not** propagate to Day Master scoring or useful god calculation.

**Theory**: A bound stem loses its independent function. If the Day Master stem is bound, its strength should be reduced. If a useful god stem is bound, its efficacy should be diminished.

**Target**:
1. In `score_day_master()`: if the Day Master stem is in a bound-but-not-transformed combination, apply a penalty factor (e.g., −1.5 to strength score)
2. In `recommend_useful_god()`: if the recommended useful god's stem is bound by another stem in the chart, flag it as "compromised" and suggest the next-best alternative
3. Add a `bound_stems` field to chart analysis output

**Files**: `scoring.py`, `stem_transformations.py` (expose a `get_bound_stems()` helper)  
**Tests**: Chart where Day Master Jia is bound by Ji but does not transform — verify reduced score

### 2.3 Useful God Bound Rule (用神被合)

**Current state**: No check for whether the useful god stem is being held in combination.

**Target**: After `recommend_useful_god()` determines the useful god:
1. Check if the useful god's element has an exposed stem that is in a combination pair with another chart stem
2. If so, return a warning: `"useful_god_compromised": True` with explanation
3. Suggest secondary useful god if primary is bound

**Files**: `scoring.py`  
**Tests**: Chart where useful god stem Geng is bound by Yi — verify warning is emitted

---

## 3. Phase 3 — Na Yin Enrichment (60% → ~85%)

**Estimated modules affected**: `nayin.py`, `longevity.py`, `analysis.py`

### 3.1 Na Yin Special Interaction Rules

**Blocked by**: Q2 above (source authority).

**Target**: Replace the generic `_element_relation()` in `analyze_nayin_interactions()` with a Na Yin-specific interaction engine that accounts for:
- **Mutual generation with affinity** (e.g., 炉中火 Furnace Fire + 松柏木 Pine Wood = Fire strengthened with quality fuel)
- **Hostile control** (e.g., 剑锋金 Sword Metal + 桑柘木 Mulberry Wood = destructive cutting)
- **Special combinations** (e.g., 大海水 Ocean Water + 剑锋金 Sword Metal = auspicious tempering — 金水相涵)
- **Element-specific severity** (some Metal types are vulnerable to certain Fire types but not others)

**Implementation approach**:
1. Create a `NAYIN_SPECIAL_RULES` table in `constants.py`: keyed by `(nayin_type_a, nayin_type_b)` or by `(nayin_element_a, nayin_element_b, nayin_subtype_a, nayin_subtype_b)`
2. In `analyze_nayin_interactions()`, first check special rules, then fall back to generic element relation
3. Return enriched interaction info: `{"relation": "control", "severity": "hostile", "note": "金入火熔 — Metal smelted"}`

**Files**: `constants.py` (new table), `nayin.py`  
**Tests**: Specific Na Yin pairs with known classical interactions

### 3.2 Global Na Yin Balance Assessment (四柱納音推局)

**Target**: Add a function that assesses overall Na Yin harmony across all four pillars:
1. Collect all four pillar Na Yin elements
2. Count element distribution (e.g., 2 Metal, 1 Water, 1 Fire)
3. Check for:
   - **Full harmony** (生生不息): each pillar's Na Yin generates the next (Year→Month→Day→Hour)
   - **Hostile chain** (克克连环): each pillar's Na Yin controls the next
   - **Mixed balance**: assess net generative vs. controlling relationships
4. Return assessment: `{"harmony": "partial", "score": 6, "chain": ["generate", "control", "generate"], "note": "..."}`

**Files**: `nayin.py` (new `assess_nayin_balance()` function), `analysis.py` (integrate into `comprehensive_analysis()`)  
**Tests**: Charts with known all-generative and all-controlling Na Yin chains

### 3.3 Na Yin-based Growth Stages (Optional)

**Blocked by**: Q4 above.

If approved, add an optional parameter to `life_stages_for_chart()`:

```python
def life_stages_for_chart(chart, use_nayin_element=False):
    if use_nayin_element:
        element = chart["day"]["nayin"]["element"]
    else:
        element = STEM_ELEMENT[chart["day"]["stem"]]
    ...
```

**Files**: `longevity.py`  
**Tests**: Chart where Na Yin element differs from Day Stem element — verify different stage assignments

---

## 4. Phase 4 — He Tu Data Layer

**New module**: `hetu.py` (or integrate into `constants.py` if kept minimal)

### 4.1 He Tu Number Pairs & Element Mapping

**Target**: Implement the He Tu (河圖) number-pair system:

```
1 ↔ 6 → Water (北)    Inner: 1 (Yang), Outer: 6 (Yin)
2 ↔ 7 → Fire  (南)    Inner: 2 (Yin),  Outer: 7 (Yang)
3 ↔ 8 → Wood  (東)    Inner: 3 (Yang), Outer: 8 (Yin)
4 ↔ 9 → Metal (西)    Inner: 4 (Yin),  Outer: 9 (Yang)
5 ↔ 10 → Earth (中)   Inner: 5 (Yang), Outer: 10 (Yin)
```

Map Heavenly Stems and Earthly Branches to their He Tu numbers:

| Stem | He Tu # | | Branch | He Tu # |
|------|---------|---|--------|---------|
| Jia (甲) | 3 | | Zi (子) | 1 |
| Yi (乙) | 8 | | Chou (丑) | 10 |
| Bing (丙) | 2 | | Yin (寅) | 3 |
| Ding (丁) | 7 | | Mao (卯) | 8 |
| Wu (戊) | 5 | | Chen (辰) | 5 |
| Ji (己) | 10 | | Si (巳) | 2 |
| Geng (庚) | 4 | | Wu (午) | 7 |
| Xin (辛) | 9 | | Wei (未) | 10 |
| Ren (壬) | 1 | | Shen (申) | 4 |
| Gui (癸) | 6 | | You (酉) | 9 |
| | | | Xu (戌) | 5 |
| | | | Hai (亥) | 6 |

### 4.2 He Tu Combination Detection

Two stems/branches sharing a He Tu number pair (e.g., Jia=3 and Mao=8 → 3↔8 Wood) form a **He Tu combination** (河圖合), indicating a deep generative affinity.

**Target**: Detect He Tu combinations between chart elements and report them as supplementary interaction data.

**Files**: `hetu.py` (new), optionally integrated into `analysis.py`  
**Tests**: Verify all 5 number-pair combinations are correctly detected

---

## 5. Phase 5 — Luo Shu & Nine Palace Engine

> **Blocked by**: Q1 above. Skip this phase if cosmological systems are out of scope.

**New module**: `luoshu.py`

### 5.1 Lo Shu Magic Square

```
4  9  2
3  5  7
8  1  6
```

Implement the 3×3 magic square with palace-to-direction mapping:

| Palace | Number | Direction | Element | Trigram |
|--------|--------|-----------|---------|---------|
| 1 | 1 | North | Water | Kan ☵ |
| 2 | 2 | Southwest | Earth | Kun ☷ |
| 3 | 3 | East | Wood | Zhen ☳ |
| 4 | 4 | Southeast | Wood | Xun ☴ |
| 5 | 5 | Center | Earth | — |
| 6 | 6 | Northwest | Metal | Qian ☰ |
| 7 | 7 | West | Metal | Dui ☱ |
| 8 | 8 | Northeast | Earth | Gen ☶ |
| 9 | 9 | South | Fire | Li ☲ |

### 5.2 Flying Star Calculation

Implement the annual and monthly Flying Star rotation:
1. **Annual Star**: Determine the center star for a given year (male/female calculation differs)
2. **Monthly Star**: Derived from annual star + month
3. **Star Flight Path**: Follow the Lo Shu flight path (1→2→3→4→5→6→7→8→9, forward or reverse depending on center star polarity)
4. Return a 3×3 grid of star numbers for any given year/month

**Files**: `luoshu.py`  
**Tests**: Verify known annual star placements for historical years

---

## 6. Phase 6 — Ba Gua Data Layer

> **Blocked by**: Q1 above. Skip this phase if Ba Gua integration is out of scope.

**New module**: `bagua.py`

### 6.1 Trigram Definitions

Implement the eight trigrams with their attributes:

| Trigram | Chinese | Lines | Element | Direction (Later Heaven) | Family |
|---------|---------|-------|---------|--------------------------|--------|
| Qian | 乾 ☰ | ⚊⚊⚊ | Metal | Northwest | Father |
| Kun | 坤 ☷ | ⚋⚋⚋ | Earth | Southwest | Mother |
| Zhen | 震 ☳ | ⚊⚋⚋ | Wood | East | Eldest Son |
| Xun | 巽 ☴ | ⚋⚊⚊ | Wood | Southeast | Eldest Daughter |
| Kan | 坎 ☵ | ⚋⚊⚋ | Water | North | Middle Son |
| Li | 离 ☲ | ⚊⚋⚊ | Fire | South | Middle Daughter |
| Gen | 艮 ☶ | ⚊⚊⚋ | Earth | Northeast | Youngest Son |
| Dui | 兑 ☱ | ⚋⚋⚊ | Metal | West | Youngest Daughter |

### 6.2 Stem/Branch to Trigram Mapping

Map each Heavenly Stem and Earthly Branch to its associated trigram (Na Jia / 納甲 system):

| Stem | Trigram | | Branch | Trigram |
|------|---------|---|--------|---------|
| Jia (甲) | Qian ☰ | | Zi (子) | Kan ☵ |
| Yi (乙) | Kun ☷ | | Chou (丑) | Gen ☶ |
| Bing (丙) | Gen ☶ | | Yin (寅) | Gen ☶ |
| Ding (丁) | Dui ☱ | | Mao (卯) | Zhen ☳ |
| Wu (戊) | Kan ☵ | | Chen (辰) | Xun ☴ |
| Ji (己) | Li ☲ | | Si (巳) | Xun ☴ |
| Geng (庚) | Zhen ☳ | | Wu (午) | Li ☲ |
| Xin (辛) | Xun ☴ | | Wei (未) | Kun ☷ |
| Ren (壬) | Xun ☴ | | Shen (申) | Kun ☷ |
| Gui (癸) | Gen ☶ | | You (酉) | Dui ☱ |
| | | | Xu (戌) | Qian ☰ |
| | | | Hai (亥) | Qian ☰ |

### 6.3 Bazi Integration (if approved)

Add optional trigram fields to chart pillars:
```python
pillar["trigram"] = {
    "stem_trigram": "Qian",
    "branch_trigram": "Kan",
    "combined_hexagram": "天水讼 (Heaven over Water — Conflict)",
}
```

**Files**: `bagua.py`, optionally `core.py` (add trigram field to `build_chart()`)  
**Tests**: Verify stem/branch → trigram mappings for all 10 stems and 12 branches

---

## 7. Phase 7 — Integration & Report

### 7.1 Integrate New Data into Report

Update `report.py` to include new sections for:
- Special structures (if detected)
- San He completions in annual flow
- Dynamic void events in luck pillars
- Na Yin balance assessment
- He Tu combinations (if implemented)
- Flying Star grid (if implemented)

### 7.2 Update Test Suite

Add comprehensive tests for all new features:
- At least 3 test charts per special structure type
- Annual flow San He completion test
- Dynamic void exit test
- Na Yin special interaction tests
- He Tu combination detection tests
- Bound-stem propagation tests

### 7.3 Update Completeness Evaluation

Re-run the evaluation against the updated codebase and produce a new assessment.

---

## 8. Implementation Order & Dependencies

```
Phase 1 (Core Bazi)          — no blockers, can start immediately
  ├── 1.1 Special Structures — structure.py, scoring.py
  ├── 1.2 San He in Annual Flow — annual_flow.py, branch_interactions.py
  ├── 1.3 Pillar Weighting   — blocked by Q3
  └── 1.4 Dynamic Void       — symbolic_stars.py, luck_pillars.py, annual_flow.py

Phase 2 (Stem Combinations)  — no blockers, can start immediately
  ├── 2.1 External Stem Transformations — analysis.py, annual_flow.py
  ├── 2.2 Bound Stem Effects  — scoring.py, stem_transformations.py
  └── 2.3 Useful God Bound    — scoring.py

Phase 3 (Na Yin)             — 3.1 blocked by Q2, 3.3 blocked by Q4
  ├── 3.1 Special Interaction Rules — blocked by Q2
  ├── 3.2 Global Na Yin Balance     — nayin.py, analysis.py
  └── 3.3 Na Yin Growth Stages      — blocked by Q4

Phase 4 (He Tu)              — no blockers (pure data layer)
  ├── 4.1 Number Pairs & Mapping
  └── 4.2 Combination Detection

Phase 5 (Luo Shu)            — blocked by Q1
  ├── 5.1 Magic Square
  └── 5.2 Flying Stars

Phase 6 (Ba Gua)             — blocked by Q1
  ├── 6.1 Trigram Definitions
  ├── 6.2 Stem/Branch Mapping
  └── 6.3 Bazi Integration

Phase 7 (Integration)        — depends on all above
  ├── 7.1 Report Updates
  ├── 7.2 Test Suite
  └── 7.3 Re-evaluation
```

Phases 1, 2, and 4 can proceed in parallel. Phase 3.2 can also proceed independently.

---

## 9. Deferred / Out of Scope

The following items from the evaluation are **explicitly deferred** and will not be implemented in this plan:

| Item | Reason |
|------|--------|
| **I Ching / 64 Hexagrams (六十四卦)** | Separate divination system, not Four-Pillars analysis |
| **Da Yan Zhi Shu (大衍之數)** | Yarrow stalk divination method, not Bazi |
| **Six Relatives per I Ching (六亲)** | I Ching divination structure, not Bazi Ten Gods |
| **Na Jia Six Lines (六爻納甲)** | I Ching line mapping, separate from Bazi Na Jia |
| **Qi Men Dun Jia (奇門遁甲)** | Entirely separate forecasting system |
| **Liu Ren (六壬)** | Entirely separate forecasting system |
| **Feng Shui Na Jia numerical system** | Out of scope for a Bazi engine |

These may be addressed in future plans if the project scope expands beyond Four-Pillars analysis.

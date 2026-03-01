# 20260301 — Bazi Structure Classification & Interactions Improvement

## Summary
Implemented all 8 phases of `plans/plan_bazi_structure_interactions_improvement.md`,
overhauling the branch interaction engine, stem interaction engine, rooting analysis,
structure classifier, scoring system, void branch integration, and analysis aggregator.

Subsequently improved the Markdown report builder and fixed Useful God recommendation
accuracy. All 170 tests pass.

---

## Phase 1 — Data Layer (`bazi/constants.py`)

Added new imports from `glossary.py`:
- `BRANCH_PAIR_TO_AN_HE`, `BRANCH_PAIR_TO_GONG_HE`, `GONG_HE_PAIR_TO_ELEMENT`
- `LIU_HE_PAIR_TO_ELEMENT`, `STEM_RESTRAIN_PAIR_TO_TERM`
- `SAN_HE_SET_TO_ELEMENT`, `SAN_HUI_SET_TO_ELEMENT`

New derived constants:
| Constant | Description |
|---|---|
| `AN_HE` | Set of 暗合 (hidden combination) branch pairs |
| `GONG_HE` | Set of 拱合 (arching combination) branch pairs |
| `GONG_HE_ELEMENT`, `GONG_HE_MISSING_MIDDLE` | Element and missing middle branch for each 拱合 pair |
| `SAN_HE_ELEMENT` | frozenset → element for 三合 (three combination) frames |
| `SAN_HUI_ELEMENT` | frozenset → element for 三会 (directional trinity) frames |
| `LIU_HE_TRANSFORM_ELEMENT` | frozenset → element for 六合 transformations |
| `LIU_HE_WU_WEI_PAIR`, `LIU_HE_WU_WEI_ELEMENTS` | Special 午未 dual-element pair |
| `STEM_RESTRAINT_PAIRS` | Set of stem restraint pairs (天干相克) |
| `STEM_ROOT_BRANCHES` | Stem → `{main, middle, residual}` branch sets for rooting |
| `ELEMENT_TO_TOMB`, `TOMB_BRANCHES` | Tomb/treasury (墓库) lookup tables |

---

## Phase 2 — Branch Interaction Engine (`bazi/branch_interactions.py`)

Complete rewrite. Now detects all classical branch interaction types.

### New interaction types detected
- **六破** (Six Destructions) — six pairs of destructive branch oppositions
- **暗合** (Hidden Combinations) — secret affinity branch pairs
- **拱合** (Arching Combinations) — virtual combinations via a missing middle branch

### New functions
| Function | Description |
|---|---|
| `evaluate_liu_he_transformation()` | 4-condition check for 六合 transformation: adjacency, month support, leading element present, obstruction |
| `evaluate_san_he_transformation()` | 三合 frame evaluation with season scoring and clash interference check |
| `classify_ban_san_he()` | Classifies 半三合 as birth-phase (生旺) or grave-phase (墓旺) |
| `resolve_interaction_conflicts()` | Applies classical priority rules: 六冲 dissolves 六合 |
| `_resolve_wu_wei_target()` | Handles 午未 dual-element transform (Fire or Earth) |
| `_has_leading_element()` | Checks for leading element in 六合 |
| `_branch_clashed_by_third()` | Checks if a branch is clashed by a third branch |

### Output format changes
- `六合` entries are now rich dicts with: `pair`, `pillars`, `target_element`, `is_adjacent`, `month_support`, `leading_present`, `obstructed`, `status`, `confidence`
- `三合` entries are now rich dicts with: `frame`, `pillars`, `element`, `season_score`, `complete`, `obstructed`, `status`, `confidence`

---

## Phase 3 — Stem Interaction Engine (`bazi/stem_transformations.py`)

### Enhancements to `detect_transformations()`
- Non-adjacent stem pairs are now tagged as `"遥合 (remote)"` and skip transformation condition checks

### New functions
| Function | Description |
|---|---|
| `detect_jealous_combinations()` | Detects 争合 (jealous combinations) — one stem paired with two of the opposite that combine with it |
| `detect_stem_restraints()` | Detects 天干相克 with severity scoring (month pillar restraints score higher) and returns `STEM_RESTRAIN_PAIR_TO_TERM` labels |
| `detect_stem_clashes()` | Explicit 天干相冲 detection using `STEM_CLASH_PAIRS` with pillar context |

---

## Phase 4 — Rooting & Tomb Analysis (new `bazi/rooting.py`)

New module providing three analytical functions:

| Function | Description |
|---|---|
| `analyze_stem_roots()` | Full rooting analysis for all stems; weights by role (`main=1.0`, `middle=0.6`, `residual=0.3`) and pillar position |
| `analyze_dm_rooting()` | Focused DM analysis; includes `is_jian_lu`, `is_yang_ren`, `main_qi_roots` count, `root_score` |
| `analyze_tomb_treasury()` | Analyses 辰戌丑未 branches as tomb/treasury; identifies entombed elements, opened status (needs clash/combination), and whether DM enters tomb |

---

## Phase 5 — Structure Classifier (`bazi/structure.py`)

Major overhaul introducing a three-tier classification system.

### New special structure detectors
| Function | Classification |
|---|---|
| `detect_transform_structure()` | 化格 — DM participates in a successful stem transformation |
| `detect_follow_structure()` | 从格 — extremely weak DM surrenders to dominant element category |
| `detect_five_element_dominance()` | 五行专旺格 — one element dominates via seasonal trinity + frames |
| `detect_extreme_prosperous()` | 建禄格 / 羊刃格 — DM's own element commands the month |
| `detect_composite_structures()` | 食神制杀, 伤官配印, 伤官见官, 杀印相生 — composite interaction patterns |

### `classify_structure()` signature expanded
```python
classify_structure(chart, strength, score=None, rooting=None, interactions=None, transformations=None)
```
All new parameters default to `None` and are computed internally when absent (backward compatible).

### `_assess_structure_quality()` enhanced
- Now checks for month-branch clashes that weaken the month-pillar structure

---

## Phase 6 — Scoring System (`bazi/scoring.py`)

### 5-tier strength classification
| Tier | Range |
|---|---|
| `extreme_strong` | score ≥ 12 |
| `strong` | score ≥ 7 |
| `balanced` | score ≥ 3 |
| `weak` | score ≥ -2 |
| `extreme_weak` | score < -2 |

### `score_day_master()` enhancements
- Accepts optional `interactions` and `rooting` parameters
- Applies 三合/三会 frame boost when DM element is the frame element
- Applies 六冲 penalty when month branch is clashed

### `rate_chart()` enhancements
- Uses 5-tier strength point table for base score
- Broken structure penalty (`-10` for 从格/化格 with conflicting interactions)
- Composite structure bonus (`+5`)
- Granular interaction stability scoring:
  - 六冲 (`-8 month`, `-4 others`), 刑 (`-5`), 害 (`-3`), 六破 (`-2`) penalties
  - 六合 (`+3`), 三合完全 (`+5`), 三合半 (`+2`) bonuses

### `recommend_useful_god()` enhancements
- Structure-aware: handles 从格 (follow), 化格 (transform), and 伤官格 specially

---

## Phase 7 — Void Branch Integration (`bazi/symbolic_stars.py`)

Two new functions appended:

| Function | Description |
|---|---|
| `get_void_branches_for_chart()` | Returns the set of void (空亡) branches for a chart |
| `apply_void_effects()` | Tags interactions involving void branches as `"weakened"`, reduces `confidence` scores by 20 pts |

---

## Phase 8 — Analysis Integration (`bazi/analysis.py`)

`comprehensive_analysis()` now integrates all new subsystems and returns a restructured output dict:

```
{
  "day_master": { strength (5-tier), strength_score, born_in },
  "rooting":    { dm rooting analysis },
  "structure":  { full classify_structure() output },
  "natal_interactions": {
      combinations (六合 dicts), clashes, san_he (三合 dicts),
      ban_san_he, san_hui, harms, destructions (六破),
      hidden_combinations (暗合), arching_combinations (拱合),
      xing, self_punishment
  },
  "stem_interactions": {
      combinations, transformations, jealous_combinations,
      restraints, clashes
  },
  "tomb_treasury": { tomb/treasury analysis },
  "punishments":   { ... },
  "life_stages":   { ... },
  "nayin_analysis": { ... },
  "summary":       "..."
}
```

Void effects are applied to `natal_interactions` and `stem_interactions` before assembly.

---

## Public API (`bazi/__init__.py`)

New exports added across all phases:
- Constants: `AN_HE`, `GONG_HE`, `GONG_HE_ELEMENT`, `SAN_HE_ELEMENT`, `SAN_HUI_ELEMENT`, `LIU_HE_TRANSFORM_ELEMENT`, `STEM_RESTRAINT_PAIRS`, `STEM_ROOT_BRANCHES`, `ELEMENT_TO_TOMB`, `TOMB_BRANCHES`
- Branch interaction functions: `evaluate_liu_he_transformation`, `evaluate_san_he_transformation`, `classify_ban_san_he`, `resolve_interaction_conflicts`
- Stem interaction functions: `detect_jealous_combinations`, `detect_stem_restraints`, `detect_stem_clashes`
- Rooting module: `analyze_stem_roots`, `analyze_dm_rooting`, `analyze_tomb_treasury`
- Void functions: `get_void_branches_for_chart`, `apply_void_effects`

---

## Test Updates (`test_bazi.py`)

Four tests updated for backward compatibility with the new system:

| Test | Change |
|---|---|
| `TestScoreDayMaster.test_strong_fire_chart` | Accepts `'strong'` or `'extreme_strong'` — 丙 DM with double 午 in Fire month correctly classifies as extreme strong |
| `TestBranchInteractions.test_six_combination` | Updated to check new dict format: `item['pair']` contains 子 and 丑 instead of iterating bare tuples |
| `TestComprehensiveAnalysis.test_has_natal_interactions` | Updated to check `stem_interactions` key (transformations moved out of natal_interactions) |
| `TestComprehensiveAnalysis.test_transformation_example` | Updated path to `result['stem_interactions']['transformations']` |

---

## Phase 9 — Useful God Accuracy Fix (`bazi/scoring.py`)

`recommend_useful_god()` had incorrect element assignments for the default strength-based path:

| Tier | Before (incorrect) | After (correct) |
|---|---|---|
| `strong` / `extreme_strong` | favorable: `[Output, Wealth]`, avoid: `[DM]` | favorable: `[Officer, Output, Wealth]`, avoid: `[DM, Resource]` |
| `weak` / `extreme_weak` | favorable: `[Resource, DM]`, avoid: `[Wealth]` | favorable: `[Resource, DM]`, avoid: `[Officer, Wealth]` |
| `balanced` | favorable: `[Output, Resource]` (unchanged) | same |

**Rationale:**
- Strong DM needs Officer as the primary restraint (天克地冲); Resource (印) must be avoided since it further strengthens an already-strong DM.
- Weak DM's primary threat is Officer (direct attack on DM), not Wealth. Both Officer and Wealth drain/attack a weak DM and must be avoided.
- All tiers now always return `useful_god` and `joyful_god` labels used by the report.

Two tests updated in `TestUsefulGod` to reflect the corrected logic.

---

## Phase 10 — Comprehensive Report Overhaul (`bazi/report.py`, `bazi/cli.py`)

### `generate_report_markdown()` — new `comprehensive` parameter

Accepts the output of `comprehensive_analysis()` to expose rooting, tomb/treasury,
and stem interaction data that were previously unavailable.

`cli.py` updated to pass `comprehensive=comprehensive` to the report function.

### New report sections

| Section | Content |
|---|---|
| **Day Master table** | Added Rooting row (classification, strength, main-qi root count); 建禄/羊刃 flags inline |
| **Month Order** | Shows month branch element at the header |
| **Chart Structure** | Now shows category, composite, `is_special`, `is_broken` flag, and notes |
| **Useful God (separate section)** | Separated from Structure; shows 用神/喜神 with descriptive labels and structure-aware note |
| **Branch Interactions** | Each type in its own subsection; 六合 and 三合 render as rich dicts (pair, target, status, confidence, void-weakened flag); 拱合 shows missing middle branch |
| **Stem Interactions** | New top-level section covering: Combinations (with pillar locations), Transformations (adjacency / month-support / leading / blocked / clashed flags), Jealous Combinations (争合), Stem Restraints table, Stem Clashes |
| **Day Master Rooting Analysis** | Full root breakdown table: branch, pillar, hidden stem, role, weight, same-stem flag |
| **Tomb & Treasury Analysis** | Per-branch: entombed elements, open/closed status (with clash source), DM-enters-tomb warning |
| **Symbolic Stars** | Cross-references each star's location against void branches; auspicious stars on void tagged `[VOID — efficacy nullified]`, inauspicious tagged `[VOID — harm reduced]` |
| **Na Yin Analysis** | Expanded into three sub-sections: Pillar Na Yin table; Flow chain with readable relation labels (generates/controls/same element); Na Yin vs Day Master with interpretive descriptions |
| **Analysis Summary** | Prints the `comprehensive_analysis()` summary string |

### Removed / replaced
- The old **Na Yin Interactions** section that merely reprinted pillar names and elements from the Four Pillars table is replaced by the three-part Na Yin Analysis section above.
- Raw `str(dict)` fallback rendering of interaction entries replaced by structured formatters.

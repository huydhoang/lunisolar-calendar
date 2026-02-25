# Bazi Target Data Schema (八字目标数据模型)

> **Purpose**: This document defines the complete target data schema for
> `bazi.py` — the comprehensive Bazi (Four Pillars of Destiny) analysis engine.
> It maps every calculable subsystem from input through output, tracks current
> implementation status, identifies gaps, and provides the JSON-like data
> structures each function should produce. The schema is derived from
> professional-grade Vietnamese / classical Chinese Bazi calculators and the
> existing `@specs/bazi-analysis-framework.md`.
>
> **Main entry point**: `bazi.py` which imports from `lunisolar_v2.py` (the
> lunisolar calendar engine).

---

## Table of Contents

1. [Input Layer](#i-input-layer)
2. [Core Natal Chart (Four Pillars)](#ii-core-natal-chart-four-pillars)
3. [Day Master Analysis](#iii-day-master-analysis)
4. [Ten Gods Distribution](#iv-ten-gods-distribution)
5. [Hidden Stem Matrix](#v-hidden-stem-matrix)
6. [Na Yin (納音)](#vi-na-yin-納音)
7. [12 Stages of Life (十二长生)](#vii-12-stages-of-life-十二长生)
8. [Interactions Engine](#viii-interactions-engine)
9. [Void Branches (空亡)](#ix-void-branches-空亡)
10. [Symbolic Stars (神煞)](#x-symbolic-stars-神煞)
11. [Luck Pillars (大运)](#xi-luck-pillars-大运)
12. [Annual / Date Comparison Engine](#xii-annual--date-comparison-engine)
13. [Element Strength Model](#xiii-element-strength-model)
14. [Aggregated Output Models](#xiv-aggregated-output-models)
15. [Advanced Calculable Data](#xv-advanced-calculable-data)
16. [Complete Hierarchical Data Model](#xvi-complete-hierarchical-data-model)
17. [Implementation Status Summary](#xvii-implementation-status-summary)
18. [Extension Roadmap](#xviii-extension-roadmap)

---

## I. Input Layer

### 1. Birth Data

```
{
  gregorian_date: "YYYY-MM-DD",     # Required
  time: "HH:MM",                    # Required (default "12:00")
  timezone: "Asia/Shanghai",        # IANA timezone name
  longitude: float,                 # Optional — for true solar time
  latitude: float,                  # Optional — for solar time correction
  gender: "male" | "female"         # Required
}
```

**Current state**: `from_solar_date(solar_date, solar_time, gender, timezone_name)` accepts date, time, gender, and timezone. Longitude/latitude not yet supported.

| Field | Status | Source |
|-------|--------|--------|
| `gregorian_date` | ✅ Implemented | `from_solar_date()` |
| `time` | ✅ Implemented | `from_solar_date()` |
| `timezone` | ✅ Implemented | `lunisolar_v2.TimezoneHandler` |
| `longitude` | ❌ Not implemented | — |
| `latitude` | ❌ Not implemented | — |
| `gender` | ✅ Implemented | `normalize_gender()` |

### 2. Calculation Adjustments

```
{
  solar_time_correction_minutes: int,   # True solar time correction
  true_solar_time: "HH:MM",            # Corrected local solar time
  day_boundary_rule: "23:00" | "00:00", # Zi hour split convention
  calendar_input_type: "solar" | "lunar" # Input calendar type
}
```

| Field | Status | Notes |
|-------|--------|-------|
| `solar_time_correction_minutes` | ❌ Not implemented | Requires longitude |
| `true_solar_time` | ❌ Not implemented | Requires longitude |
| `day_boundary_rule` | ⚠️ Implicit | `lunisolar_v2` uses fixed convention |
| `calendar_input_type` | ✅ Solar only | `from_solar_date()` takes Gregorian |

---

## II. Core Natal Chart (Four Pillars)

### Per-Pillar Data Structure (target)

```
{
  pillar_name: "year" | "month" | "day" | "hour",

  heavenly_stem: {
    character: "癸",
    pinyin: "guǐ",
    element: "Water",
    polarity: "Yin",
    ten_god: "正官"             # Relative to Day Master
  },

  earthly_branch: {
    character: "巳",
    pinyin: "sì",
    animal: "Snake",
    element: "Fire",
    hidden_stems: [
      { stem: "丙", role: "main",     element: "Fire",  ten_god: "比肩" },
      { stem: "戊", role: "middle",   element: "Earth", ten_god: "食神" },
      { stem: "庚", role: "residual", element: "Metal", ten_god: "偏财" }
    ]
  },

  na_yin: {
    element: "Water",
    chinese: "大溪水",
    english: "Great Stream Water"
  },

  longevity_stage: {
    index: 4,
    name: "临官",
    english: "Coming of Age"
  }
}
```

### Current Implementation Mapping

| Target Field | Status | Current Source |
|--------------|--------|---------------|
| `pillar_name` | ✅ | `chart['pillars']` keys: year/month/day/hour |
| `heavenly_stem.character` | ✅ | `chart['pillars'][name]['stem']` |
| `heavenly_stem.pinyin` | ❌ | Available in `lunisolar_v2._HS_TUPLES[i][1]` but not exposed |
| `heavenly_stem.element` | ✅ | `STEM_ELEMENT[stem]` |
| `heavenly_stem.polarity` | ✅ | `STEM_POLARITY[stem]` |
| `heavenly_stem.ten_god` | ✅ | `chart['pillars'][name]['ten_god']` |
| `earthly_branch.character` | ✅ | `chart['pillars'][name]['branch']` |
| `earthly_branch.pinyin` | ❌ | Available in `_EB_TUPLES[i][1]` but not exposed |
| `earthly_branch.animal` | ❌ | Available in `_EB_TUPLES[i][2]` but not exposed |
| `earthly_branch.element` | ❌ | Not mapped (branch→element is indirect via hidden stems) |
| `earthly_branch.hidden_stems` | ✅ | `chart['pillars'][name]['hidden']` as `[(role, stem)]` |
| `na_yin` | ❌ | Data exists in `nayin.csv` (60 rows); not loaded in `bazi.py` |
| `longevity_stage` | ✅ | `longevity_map(chart)` returns `{pillar: (index, name)}` |

### Extension Points

- **Pinyin / Animal / English**: Expose metadata from `lunisolar_v2` tuples via a lookup helper.
- **Branch Element**: Add `BRANCH_ELEMENT` dict mapping 12 branches to their native element.
- **Na Yin**: Load `nayin.csv` and provide `nayin_for_cycle(cycle_number) → dict` lookup.
- **Longevity English**: Add English translation mapping to `LONGEVITY_STAGES`.

---

## III. Day Master Analysis

### Target Structure

```
{
  heavenly_stem: "丙",
  element: "Fire",
  polarity: "Yang",
  strength_score: int,              # Raw point score
  strength_class: "strong" | "weak" | "balanced",
  supporting_percent: float,        # % of chart supporting DM
  opposing_percent: float           # % of chart opposing DM
}
```

| Target Field | Status | Current Source |
|--------------|--------|---------------|
| `heavenly_stem` | ✅ | `chart['day_master']['stem']` |
| `element` | ✅ | `chart['day_master']['element']` |
| `polarity` | ✅ | `STEM_POLARITY[stem]` |
| `strength_score` | ✅ | `score_day_master(chart)` → `(score, strength)` |
| `strength_class` | ✅ | `score_day_master(chart)` → `(score, strength)` |
| `supporting_percent` | ❌ | Not computed — need element distribution % |
| `opposing_percent` | ❌ | Not computed — need element distribution % |

### Extension Points

- Compute `supporting_percent` and `opposing_percent` from `weighted_ten_god_distribution()` by grouping Ten Gods into supporting (比肩, 劫财, 正印, 偏印) vs opposing (食神, 伤官, 正财, 偏财, 正官, 七杀) categories and normalizing to percentages.

---

## IV. Ten Gods Distribution

### Target Structure

```
{
  element_aggregation: {
    resource:  { element: "Wood", percent: 0.0 },
    parallel:  { element: "Fire", percent: 29.0 },
    output:    { element: "Earth", percent: 38.0 },
    wealth:    { element: "Metal", percent: 14.0 },
    power:     { element: "Water", percent: 19.0 }
  },

  per_stem: [
    { stem: "丙", ten_god: "比肩", weight: 2.0 },
    ...
  ],

  scope: "natal" | "natal+luck" | "natal+luck+annual"
}
```

| Target Field | Status | Current Source |
|--------------|--------|---------------|
| `per_stem` (weighted) | ✅ | `weighted_ten_god_distribution(chart)` |
| `element_aggregation` | ❌ | Not computed — can derive from distribution |
| `scope` overlays | ❌ | Only natal scope implemented |

### Extension Points

- Group Ten Gods into 5 element-role categories (Resource, Parallel, Output, Wealth, Power) and compute percentages.
- Add overlay modes for luck + annual pillar recalculation.

---

## V. Hidden Stem Matrix

### Target Structure (per branch)

```
{
  branch: "戌",
  hidden_stems: [
    { stem: "戊", role: "main",     ten_god: "食神",  element: "Earth" },
    { stem: "辛", role: "middle",   ten_god: "正财",  element: "Metal" },
    { stem: "丁", role: "residual", ten_god: "劫财",  element: "Fire" }
  ]
}
```

| Target Field | Status | Notes |
|--------------|--------|-------|
| `branch` | ✅ | `BRANCH_HIDDEN_STEMS` |
| `hidden_stems[].stem` | ✅ | `branch_hidden_with_roles(idx)` |
| `hidden_stems[].role` | ✅ | `HIDDEN_ROLES` |
| `hidden_stems[].ten_god` | ✅ | Computed via `ten_god()` in `build_chart()` |
| `hidden_stems[].element` | ✅ | `STEM_ELEMENT[stem]` |

**Status**: ✅ Fully implemented — data available in `chart['pillars'][name]['hidden']`.

---

## VI. Na Yin (納音)

### Target Structure (per pillar)

```
{
  pillar_cycle: 43,
  ganzhi: "丙午",
  na_yin_element: "Water",
  na_yin_chinese: "天河水",
  na_yin_vietnamese: "Thiên Hà Thủy",
  na_yin_english: "Heavenly River Water",
  na_yin_song: "..."
}
```

| Target Field | Status | Data Source |
|--------------|--------|------------|
| All fields | ❌ Not implemented | `nayin.csv` has all 60 entries with columns: `cycle_index`, `chinese`, `pinyin`, `vietnamese`, `nayin_element`, `nayin_chinese`, `nayin_vietnamese`, `nayin_english`, `nayin_song` |

### Extension Plan

1. Load `nayin.csv` at module level into a dict keyed by `cycle_index` (1-60).
2. Add `nayin_for_cycle(cycle: int) → dict` lookup function.
3. Add Na Yin data to each pillar in `build_chart()`.
4. Complexity: Low — data already exists, only plumbing needed.

---

## VII. 12 Stages of Life (十二长生)

### Target Structure

Per pillar relative to Day Master:

```
{
  index: 4,
  chinese: "临官",
  english: "Coming of Age",
  vietnamese: "Lâm Quan",
  strength_class: "strong"    # stages 1-5 = strong, 6-12 = weak
}
```

### Stage Reference Table

| Index | Chinese | English | Vietnamese | Strength |
|-------|---------|---------|------------|----------|
| 1 | 长生 | Growth / Birth | Trường Sinh | Strong |
| 2 | 沐浴 | Bath | Mộc Dục | Strong |
| 3 | 冠带 | Crown Belt | Quan Đới | Strong |
| 4 | 临官 | Coming of Age | Lâm Quan | Strong |
| 5 | 帝旺 | Prosperity Peak | Đế Vượng | Strong |
| 6 | 衰 | Decline | Suy | Weak |
| 7 | 病 | Sickness | Bệnh | Weak |
| 8 | 死 | Death | Tử | Weak |
| 9 | 墓 | Grave / Tomb | Mộ | Weak |
| 10 | 绝 | Termination | Tuyệt | Weak |
| 11 | 胎 | Conceive / Fetus | Thai | Weak |
| 12 | 养 | Nurture | Dưỡng | Weak |

| Target Field | Status | Current Source |
|--------------|--------|---------------|
| `index` + `chinese` | ✅ | `changsheng_stage()` and `longevity_map()` |
| `english` | ❌ | Not mapped — add `LONGEVITY_STAGES_EN` |
| `vietnamese` | ❌ | Not mapped — add `LONGEVITY_STAGES_VI` |
| `strength_class` | ✅ | Used in `score_day_master()` (stages 1-5 = +2, 6-12 = -2) |
| Natal pillars | ✅ | `longevity_map(chart)` |
| Luck pillars | ✅ | `generate_luck_pillars()` includes `longevity_stage` per pillar |

### Extension Points

- Add English and Vietnamese translation arrays parallel to `LONGEVITY_STAGES`.

---

## VIII. Interactions Engine

### 1. Heavenly Stem Interactions

```
{
  stem_combinations: [             # 天干合 (Five Combinations)
    { stems: ["甲", "己"], result_element: "Earth", pillars: ["year", "hour"] }
  ],
  stem_clashes: [                  # 天干冲
    { stems: ["甲", "庚"], pillars: ["year", "month"] }
  ],
  stem_transformations: [          # 合化 (conditional on season)
    { stems: ["甲", "己"], transforms_to: "Earth", condition_met: true }
  ]
}
```

| Feature | Status | Notes |
|---------|--------|-------|
| Stem Combinations (天干合) | ❌ | 5 pairs: 甲己→Earth, 乙庚→Metal, 丙辛→Water, 丁壬→Wood, 戊癸→Fire |
| Stem Clashes | ❌ | Not defined — lower priority than branch interactions |
| Stem Transformations (合化) | ❌ | Requires seasonal/monthly condition checking |

### 2. Earthly Branch Interactions

```
{
  liu_he:    [{ branches: ["子","丑"], result_element: "Earth", pillars: [...] }],
  liu_chong: [{ branches: ["子","午"], pillars: [...] }],
  liu_hai:   [{ branches: ["子","未"], pillars: [...] }],
  liu_po:    [{ branches: [...], pillars: [...] }],
  san_he:    [{ branches: ["寅","午","戌"], result_element: "Fire" }],
  san_hui:   [{ branches: ["寅","卯","辰"], result_element: "Wood" }],
  xing:      [{ pattern: [...], found: 3, mode: "complete" }],
  zi_xing:   [{ branch: "午", count: 2, mode: "partial" }],
  half_combinations: [...]
}
```

| Feature | Status | Current Source |
|---------|--------|---------------|
| 六合 (Six Combinations) | ✅ | `detect_branch_interactions()` → `'六合'` |
| 六冲 (Six Clashes) | ✅ | `detect_branch_interactions()` → `'六冲'` |
| 六害 (Six Harms) | ✅ | `detect_branch_interactions()` → `'害'` |
| 六破 (Six Destructions) | ❌ | Not defined — needs `LIU_PO` constant |
| 三合 (Three Combinations) | ✅ | `detect_branch_interactions()` → `'三合'` |
| 三会 (Directional Combos) | ✅ | `detect_branch_interactions()` → `'三会'` |
| 三刑 (Punishments) | ✅ | `detect_xing()` with partial/complete grading |
| 自刑 (Self-punishment) | ✅ | `detect_self_punishment()` with exposure/adjacency options |
| Half combinations | ❌ | Not implemented |
| Hidden combinations | ❌ | Not implemented |

### 3. Combined HS + EB Transformations

| Feature | Status |
|---------|--------|
| HS + HS + EB triple transformations | ❌ |
| Season-supported transformations | ❌ |
| Element change conditions | ❌ |

### Extension Plan

1. **Phase 1**: Add `STEM_COMBINATIONS` (天干五合) constant and `detect_stem_combinations(chart)`.
2. **Phase 2**: Add `LIU_PO` (六破) constant and integrate into `detect_branch_interactions()`.
3. **Phase 3**: Add transformation condition checking (seasonal validation for 合化).

---

## IX. Void Branches (空亡)

### Target Structure

```
{
  day_pillar_cycle: 43,          # Day pillar sexagenary position
  xun_group: "甲午旬",           # Ten-day cycle group
  void_branches: ["辰", "巳"],  # Two branches left unpaired
  void_in_pillars: {
    year: false,
    month: false,
    day: false,
    hour: true                   # hour branch is 巳 → void
  }
}
```

### Calculation Logic

Within each 甲 (Jia) group of the 60-cycle, the 10 Heavenly Stems pair with
10 of the 12 branches, leaving 2 branches "empty."

| 旬 (Xun Group) | Cycle Range | Void Branches |
|-----------------|-------------|---------------|
| 甲子旬 | 1-10 | 戌, 亥 |
| 甲戌旬 | 11-20 | 申, 酉 |
| 甲申旬 | 21-30 | 午, 未 |
| 甲午旬 | 31-40 | 辰, 巳 |
| 甲辰旬 | 41-50 | 寅, 卯 |
| 甲寅旬 | 51-60 | 子, 丑 |

| Status | Notes |
|--------|-------|
| ❌ Not implemented | Straightforward formula from day_cycle |

### Extension Plan

Formula: `xun_index = (day_cycle - 1) // 10`, then void branches = `EARTHLY_BRANCHES[10 + xun_index * 2]` and `[11 + xun_index * 2]` (mod 12).

Add:
1. `VOID_BRANCH_TABLE` constant.
2. `void_branches(day_cycle: int) → tuple[str, str]` function.
3. `void_in_pillars(chart) → dict` checking each pillar's branch against voids.

---

## X. Symbolic Stars (神煞)

### Target Structure

```
{
  star_name_cn: "桃花",
  star_name_en: "Peach Blossom",
  star_name_vi: "Đào Hoa",
  triggered_by: "branch",         # or "stem", "cycle"
  reference_pillar: "year",       # Which pillar's branch/stem triggers it
  location: "hour",               # Where the star manifests
  nature: "mixed",                # "auspicious" | "inauspicious" | "mixed"
  active_in: "natal"              # "natal" | "luck" | "annual"
}
```

### Core Stars to Implement

| Star | Chinese | Trigger Rule | Nature |
|------|---------|-------------|--------|
| Nobleman | 天乙贵人 | DM stem → specific branches | Auspicious |
| Academic | 文昌 | DM stem → specific branch | Auspicious |
| Peach Blossom | 桃花 | Year/day branch → specific branch | Mixed |
| Travel Horse | 驿马 | Year/day branch → specific branch | Neutral |
| General | 将星 | Year/day branch → specific branch | Auspicious |
| Canopy | 华盖 | Year/day branch → specific branch | Mixed |
| Goat Blade | 羊刃 | DM stem → specific branch | Inauspicious |
| Emptiness | 空亡 | Day cycle → two void branches | Inauspicious |
| Prosperity Star | 禄神 | DM stem → specific branch | Auspicious |
| Heavenly Virtue | 天德 | Month branch → specific stem | Auspicious |
| Monthly Virtue | 月德 | Month branch → specific stem | Auspicious |
| Red Clouds | 红鸾 | Year branch → specific branch | Mixed |
| Blood Knife | 血刃 | Day branch → specific branch | Inauspicious |

| Status | Notes |
|--------|-------|
| ❌ Not implemented | Defined in spec §9 but no code exists |

### Extension Plan

1. Define lookup tables for each star's trigger rule.
2. Add `detect_symbolic_stars(chart) → list[dict]` function.
3. Add star detection for luck pillars and annual pillars.
4. Complexity: Medium — each star has its own mapping table.

---

## XI. Luck Pillars (大运)

### Meta Data (target)

```
{
  direction: "forward" | "backward",
  start_age: { years: 1, months: 0 },
  start_date: "1991-03-01",
  calculation_method: "3-day rule"
}
```

### Per 10-Year Pillar (target)

```
{
  index: 1,
  stem: "戊",
  branch: "寅",
  ganzhi: "戊寅",
  age_range: [1, 10],
  start_gregorian_year: 1991,

  ten_god: "食神",                # Stem vs Day Master
  longevity_stage: {
    index: 1,
    name: "长生"
  },

  na_yin: {
    element: "Earth",
    chinese: "城头土",
    english: "City Wall Earth"
  },

  symbolic_stars: [...],
  interactions_with_natal: [...],
  element_distribution: {...}
}
```

| Target Field | Status | Current Source |
|--------------|--------|---------------|
| `direction` | ✅ | `_luck_direction(chart)` |
| `start_age` | ✅ | `calculate_luck_start_age()` + `generate_luck_pillars(birth_date=, solar_term_date=)` |
| `start_date` | ❌ | Can derive from `birth_date + start_age` |
| `stem`, `branch` | ✅ | `generate_luck_pillars()` returns `{stem, branch}` |
| `age_range` | ⚠️ Derivable | From `start_age` + 10-year spacing |
| `start_gregorian_year` | ✅ | Included when `birth_date` or `birth_year` provided |
| `ten_god` | ❌ | Not computed per luck pillar — add `ten_god()` call |
| `longevity_stage` | ✅ | Included in each luck pillar dict |
| `na_yin` | ❌ | Requires Na Yin loader |
| `symbolic_stars` | ❌ | Requires star detection engine |
| `interactions_with_natal` | ❌ | Requires cross-pillar interaction check |
| `element_distribution` | ❌ | Requires overlay recalculation |

### Extension Points

- Add `ten_god` to each luck pillar dict (stem vs DM).
- Add `age_range` derived from `start_age`.
- Integrate Na Yin lookup.
- Add `luck_pillar_interactions(chart, luck_pillar) → dict` function.

---

## XII. Annual / Date Comparison Engine

### Target Structure

```
{
  year: 2026,
  year_pillar: { stem: "丙", branch: "午" },
  month_pillar: { stem: "...", branch: "..." },
  day_pillar: { stem: "...", branch: "..." },
  hour_pillar: { stem: "...", branch: "..." },

  interactions_with_natal: { ... },
  interactions_with_luck: { ... },
  updated_ten_gods_distribution: { ... },
  symbolic_stars_triggered: [...]
}
```

| Target Field | Status | Current Source |
|--------------|--------|---------------|
| `year_pillar` | ✅ | `annual_analysis(chart, cycle)` |
| `month/day/hour_pillar` | ❌ | Only year pillar analyzed |
| `interactions_with_natal` | ✅ | `annual_analysis()` → `interactions` |
| `interactions_with_luck` | ❌ | Not implemented |
| `updated_ten_gods_distribution` | ❌ | Not implemented |
| `symbolic_stars_triggered` | ❌ | Not implemented |

### Extension Points

- Extend `annual_analysis()` to accept full four-pillar overlay.
- Add luck pillar context to annual analysis.
- Integrate symbolic star triggering for flowing years.

---

## XIII. Element Strength Model

### Target Structure

```
{
  seasonal_strength_weight: float,    # Month-order (月令) factor
  root_strength: float,               # Hidden stem roots
  stem_support: float,                # Visible stem support
  combination_modifiers: float,       # Combination/clash adjustments
  transformation_adjustments: float,  # Transformation effects
  final_dm_strength_score: int,
  final_dm_strength_class: "strong" | "weak" | "balanced",
  supporting_percent: float,
  opposing_percent: float
}
```

| Target Field | Status | Current Source |
|--------------|--------|---------------|
| `seasonal_strength_weight` | ✅ | `score_day_master()` — stages 1-5 give +2, 6-12 give -2 |
| `root_strength` | ✅ | Main root +2, middle root +1 |
| `stem_support` | ✅ | Each matching stem +1 |
| `combination_modifiers` | ❌ | Not factored into strength |
| `transformation_adjustments` | ❌ | Not factored into strength |
| `final_dm_strength_score` | ✅ | `score_day_master()` → `(score, strength)` |
| `supporting_percent` | ❌ | Not computed |
| `opposing_percent` | ❌ | Not computed |

### Extension Points

- Add combination/transformation modifiers to the strength score.
- Compute element-category percentages from `weighted_ten_god_distribution()`.

---

## XIV. Aggregated Output Models

### Target Outputs

```
{
  pie_chart_distribution: {        # Element percentages
    "Wood": 0.0,
    "Fire": 29.0,
    "Earth": 38.0,
    "Metal": 14.0,
    "Water": 19.0
  },

  supporting_vs_opposing: {
    supporting: 29.0,              # Resource + Parallel
    opposing: 71.0                 # Output + Wealth + Power
  },

  scope: "natal" | "natal+luck" | "natal+luck+annual",

  chart_rating: {
    total: 76,
    breakdown: {
      strength_balance: 22,
      structure_purity: 18,
      element_balance: 20,
      root_depth: 10,
      interaction_stability: 6
    }
  }
}
```

| Target Field | Status | Current Source |
|--------------|--------|---------------|
| `pie_chart_distribution` | ❌ | Can derive from `weighted_ten_god_distribution()` |
| `supporting_vs_opposing` | ❌ | Can derive by grouping Ten Gods |
| `scope` overlays | ❌ | Only natal scope |
| `chart_rating.total` | ✅ | `rate_chart(chart)` |
| `chart_rating.breakdown` | ❌ | Components computed internally but not exposed |

### Extension Points

- Expose rating breakdown as a dict from `rate_chart()`.
- Add `element_percentages(chart, scope=)` function.
- Add scoped calculations for natal+luck and natal+luck+annual.

---

## XV. Advanced Calculable Data

### Useful God System (用神体系)

```
{
  yong_shen: "Wood",     # Favorable Element (用神)
  ji_shen: "Metal",      # Unfavorable Element (忌神)
  xi_shen: "Water",      # Joyful Element (喜神) — supports 用神
  chou_shen: "Earth",    # Enemy Element (仇神) — supports 忌神
  xian_shen: "Fire"      # Neutral Element (闲神)
}
```

| Target Field | Status | Current Source |
|--------------|--------|---------------|
| `favorable` (用神 + 喜神) | ✅ | `recommend_useful_god()` → `favorable` list |
| `avoid` (忌神) | ✅ | `recommend_useful_god()` → `avoid` list |
| Full 5-role classification | ❌ | Only 2 of 5 roles distinguished |

### Structure Classification (格局)

```
{
  basic_structure: "官杀格",
  professional_structure: "杀重身轻 (破格)",
  dominance_score: 6.0,
  is_special: true,
  special_type: "从格" | "化气格" | null,
  disease_element: "Fire",         # 病 (Bìng)
  medicine_element: "Water"        # 药 (Yào)
}
```

| Target Field | Status | Current Source |
|--------------|--------|---------------|
| `basic_structure` | ✅ | `classify_structure()` |
| `professional_structure` | ✅ | `classify_structure_professional()` |
| `dominance_score` | ✅ | `classify_structure_professional()` returns score |
| `is_special` / `special_type` | ⚠️ Partial | Detects 从强格/从弱格 but no 化气格 |
| `disease_element` | ❌ | Not implemented — 病药 (Disease & Medicine) logic |
| `medicine_element` | ❌ | Not implemented |

---

## XVI. Complete Hierarchical Data Model

```
Chart
├── Input Data
│   ├── Birth date, time, timezone, gender
│   └── Solar Time Adjustments (future)
│
├── Natal Four Pillars (四柱)
│   ├── Stems (天干) + Ten Gods
│   ├── Branches (地支) + Animals
│   ├── Hidden Stems (藏干) + Roles + Ten Gods
│   ├── Na Yin (納音) per pillar
│   ├── 12 Life Stages (十二长生) per pillar
│   └── Void Branches (空亡)
│
├── Day Master Analysis (日主)
│   ├── Element + Polarity
│   ├── Strength Score + Class
│   ├── Supporting/Opposing %
│   └── Element Distribution (5-element %)
│
├── Interactions Engine (合冲刑害)
│   ├── Branch: 六合, 六冲, 六害, 六破, 三合, 三会, 三刑, 自刑
│   ├── Stem: 天干合, 天干冲
│   ├── Transformations (合化条件)
│   └── Void branch detection
│
├── Symbolic Stars (神煞)
│   ├── Star name, trigger rule, location
│   └── Active in: natal / luck / annual
│
├── Luck Pillars (大运)
│   ├── Direction + Starting age
│   ├── 10-year cycles with stem/branch
│   ├── Ten God + Longevity Stage
│   ├── Na Yin per pillar
│   ├── Interactions with natal
│   └── Element recalculation
│
├── Annual / Date Compare (流年)
│   ├── Year/month/day/hour overlay
│   ├── Interactions with natal + luck
│   ├── Recomputed Ten Gods distribution
│   └── Star triggers
│
├── Structure (格局)
│   ├── Basic + Professional classification
│   ├── Dominance score
│   ├── Special structure detection
│   └── Disease & Medicine (病药)
│
├── Useful God System (用神)
│   ├── 5-role classification (用/忌/喜/仇/闲)
│   └── Temperature adjustment (调候)
│
└── Aggregated Output
    ├── Element % pie chart
    ├── Supporting vs opposing ratio
    ├── Chart rating (with breakdown)
    └── Narrative interpretation
```

---

## XVII. Implementation Status Summary

### Fully Implemented ✅

| Subsystem | Functions |
|-----------|-----------|
| Core Four Pillars | `build_chart()`, `from_solar_date()`, `from_lunisolar_dto()` |
| Hidden Stems | `BRANCH_HIDDEN_STEMS`, `branch_hidden_with_roles()` |
| Ten Gods | `ten_god()`, `_element_relation()` |
| Longevity Stages (natal) | `changsheng_stage()`, `longevity_map()` |
| Longevity Stages (luck) | `generate_luck_pillars()` includes `longevity_stage` |
| DM Strength | `score_day_master()` |
| Branch Interactions | `detect_branch_interactions()`, `detect_xing()`, `detect_self_punishment()` |
| Structure Classification | `classify_structure()`, `classify_structure_professional()` |
| Weighted Distribution | `weighted_ten_god_distribution()` |
| Luck Pillars | `generate_luck_pillars()` with starting age, direction, Gregorian years |
| Annual Analysis | `annual_analysis()` |
| Useful God (basic) | `recommend_useful_god()` |
| Chart Rating | `rate_chart()` |
| Narrative | `generate_narrative()` |

### Partially Implemented ⚠️

| Subsystem | Gap |
|-----------|-----|
| Useful God | Only 2 of 5 roles (用/忌 but not 喜/仇/闲) |
| Special Structures | 从格 detected but not 化气格 or advanced types |
| Luck Pillar Ten God | Stem available but `ten_god` not computed per pillar |

### Not Implemented ❌

| Subsystem | Complexity | Priority |
|-----------|-----------|----------|
| Na Yin (納音) | 🟢 Low | High — data exists in CSV |
| Void Branches (空亡) | 🟢 Low | High — simple formula |
| Stem Combinations (天干合) | 🟢 Low | Medium |
| Six Destructions (六破) | 🟢 Low | Medium |
| English/Vietnamese labels | 🟢 Low | Medium |
| Branch/Stem metadata (pinyin, animal) | 🟢 Low | Low |
| Element % aggregation | 🟡 Medium | High |
| Symbolic Stars (神煞) | 🟡 Medium | High — 13+ stars to implement |
| Disease & Medicine (病药) | 🟡 Medium | Medium |
| Stem Transformations (合化) | 🟡 Medium | Medium |
| Luck pillar natal interactions | 🟡 Medium | Medium |
| Full 5-role Useful God | 🟡 Medium | Medium |
| Rating breakdown export | 🟢 Low | Low |
| True solar time correction | 🔴 High | Low |
| Multi-pillar annual overlay | 🔴 High | Low |
| Dynamic element redistribution | 🔴 High | Low |

---

## XVIII. Extension Roadmap

### Phase 1: Low-Hanging Fruit (🟢 Low Complexity)

> These features require minimal code — often just a constant + 1 function.

1. **Na Yin loader**: Load `nayin.csv` → `nayin_for_cycle(cycle)` → integrate into `build_chart()`.
2. **Void Branches**: `void_branches(day_cycle)` → `void_in_chart(chart)`.
3. **Stem Combinations**: `STEM_COMBINATIONS` constant + `detect_stem_combinations(chart)`.
4. **Six Destructions**: `LIU_PO` constant + add to `detect_branch_interactions()`.
5. **Luck pillar Ten God**: Add `ten_god` field in `generate_luck_pillars()`.
6. **Longevity English/Vietnamese labels**: Add parallel arrays.

### Phase 2: Element Percentages & Stars (🟡 Medium Complexity)

7. **Element aggregation %**: Group Ten Gods → 5 role categories → percentages.
8. **Supporting/Opposing ratio**: Derive from aggregated percentages.
9. **Symbolic Stars**: Implement 8-13 core stars with trigger tables.
10. **Full 5-role Useful God**: Extend `recommend_useful_god()` to classify 喜/仇/闲.
11. **Disease & Medicine**: Add `diagnose_chart(chart, strength)` function.

### Phase 3: Advanced Interactions & Overlays (🔴 High Complexity)

12. **Stem/branch transformations**: Seasonal condition checking for 合化.
13. **Luck pillar natal interactions**: Cross-pillar interaction detection.
14. **Annual overlay with luck context**: Multi-layer dynamic analysis.
15. **Dynamic element redistribution**: Recalculate weights per scope.
16. **True solar time**: Longitude-based correction.

---

## References

- `@specs/bazi-analysis-framework.md` — Core Bazi analysis framework specification
- `lunisolar-python/nayin.csv` — 60-entry Na Yin lookup data
- `lunisolar-python/lunisolar_v2.py` — Lunisolar calendar engine with `LunisolarDateDTO`
- `lunisolar-python/bazi.py` — Current implementation
- Baidu Baike: 十二长生, 空亡, 神煞
- Classical Vietnamese Bazi sources on Dương sinh Âm tử rule

# Bazi Module Refactoring Plan

> **Status**: Draft  
> **Date**: 2026-02-27  
> **Scope**: Split `lunisolar-python/bazi.py` (~3,500 lines) into focused modules; replace console-printed report with Markdown file output  
> **Goal**: Improve maintainability, testability, and readability while preserving the public API; produce a visually stunning Markdown report instead of plain-text console output

---

## 1. Problem Statement

`bazi.py` is a monolithic file containing:
- ~600 lines of data constants (element maps, interaction tables, star tables, translation arrays)
- ~200 lines of terminology/formatting utilities
- ~400 lines of branch interaction detection
- ~250 lines of stem combination/transformation detection
- ~200 lines of chart structure classification (格局)
- ~200 lines of luck pillar generation
- ~250 lines of longevity stage functions
- ~500 lines of time projection functions (year/month/day projections)
- ~300 lines of comprehensive analysis and rating
- ~150 lines of narrative generation
- ~400 lines of CLI output formatting (plain-text `print()` statements)

All constants, algorithms, and presentation are tangled in a single file, making it difficult to:
- Locate specific subsystems
- Test individual subsystems in isolation
- Reuse data tables across ports (TypeScript, Rust, C)
- Extend any subsystem without risking regressions elsewhere

Additionally, the CLI currently prints ~300 lines of plain-text to stdout. This should instead produce a **well-formatted Markdown report file** (`report.md`) that renders beautifully in any Markdown viewer, with proper tables, headings, emoji indicators, and horizontal rules.

---

## 2. Target Module Structure

```
lunisolar-python/
├── bazi.py                          # Slim facade — re-exports public API (backward-compatible)
├── bazi/
│   ├── __init__.py                  # Package init, re-exports everything from submodules
│   ├── constants.py                 # All data constants & lookup tables
│   ├── terminology.py               # Translation arrays, format_term(), get_trans_tuple()
│   ├── core.py                      # build_chart(), from_solar_date(), from_lunisolar_dto()
│   ├── ten_gods.py                  # ten_god(), _element_relation(), weighted_ten_god_distribution()
│   ├── longevity.py                 # changsheng_stage(), longevity_map(), life_stage_detail(), life_stages_for_chart()
│   ├── hidden_stems.py              # branch_hidden_with_roles(), hidden-stem utilities
│   ├── branch_interactions.py       # detect_branch_interactions(), detect_xing(), detect_self_punishment()
│   ├── stem_transformations.py      # detect_stem_combinations(), detect_transformations(), check_obstruction(), check_severe_clash()
│   ├── punishments.py               # detect_punishments(), detect_fu_yin_duplication()
│   ├── nayin.py                     # NaYin CSV loader, nayin_for_cycle(), nayin_for_pillar(), analyze_nayin_interactions()
│   ├── symbolic_stars.py            # detect_symbolic_stars(), void_branches(), void_in_pillars(), xun_name()
│   ├── structure.py                 # classify_structure(), detect_month_pillar_structure(), detect_special_structures()
│   ├── scoring.py                   # score_day_master(), rate_chart(), recommend_useful_god()
│   ├── luck_pillars.py              # generate_luck_pillars(), calculate_luck_start_age(), _luck_direction(), find_governing_jie_term()
│   ├── annual_flow.py               # annual_analysis()
│   ├── projections.py               # generate_year/month/day_projections(), get_new_moon_dates()
│   ├── analysis.py                  # comprehensive_analysis(), analyze_time_range()
│   ├── narrative.py                 # generate_narrative()
│   ├── report.py                    # NEW: generate_report_markdown() — builds the full Markdown string
│   └── cli.py                       # CLI entry point — argparse, orchestrates analysis, writes report.md
├── nayin.csv                        # (unchanged)
├── lunisolar_v2.py                  # (unchanged — no changes planned here)
└── test_bazi.py                     # Updated imports only (see §6)
```

---

## 3. New Module: `report.py` — Markdown Report Generator

### 3.1 Motivation

The current `if __name__ == "__main__"` block in `bazi.py` contains ~300 lines of `print()` calls that produce a plain-text console report. This has several problems:
- Not portable — can't be rendered in a browser, GitHub, or documentation tool
- Not reusable — tightly coupled to the CLI
- Hard to maintain — formatting changes require editing deeply nested f-strings
- No structure — just raw text lines, no semantic markup

### 3.2 Design

`report.py` will expose a single main function:

```python
def generate_report_markdown(
    chart: Dict,
    dto: LunisolarDateDTO,
    solar_date: str,
    solar_time: str,
    gender: str,
    format_string: str = "cn/py",
    proj_start: Optional[date] = None,
    proj_end: Optional[date] = None,
) -> str:
    """Build the complete Bazi analysis as a Markdown string."""
```

The function returns a single `str` containing the full report. The CLI writes it to a file.

### 3.3 Report Structure (Markdown)

The output `report.md` will contain these sections, using rich Markdown formatting:

```markdown
# 八字 Bazi Chart — {solar_date} {solar_time} ({gender})

> **Lunar Date**: {year}/{month}/{day} | **Day Master**: {stem} ({element}, {polarity})
> **Structure**: {primary} | **Strength**: {score} pts → {strength}

---

## 🏛️ Four Pillars (四柱)

| Pillar | GanZhi | Ten-God | Life Stage | Na Yin | Void |
|--------|--------|---------|------------|--------|------|
| 年 Year | ... | ... | ... | ... | |
| 月 Month | ... | ... | ... | ... | |
| 日 Day | ... | ... | ... | ... | |
| 时 Hour | ... | ... | ... | ... | ⚫ |

### Hidden Stems (藏干)

| Pillar | Main | Middle | Residual |
|--------|------|--------|----------|
| ... | ... | ... | ... |

---

## 📊 Day Master Analysis

| Property | Value |
|----------|-------|
| Stem | {stem} ({pinyin}) |
| Element | {element} |
| Polarity | {polarity} |
| Strength Score | {score} |
| Classification | {strength} |
| Xun (旬) | {xun_name} |
| Void Branches | {void1}, {void2} |

---

## 🏗️ Chart Structure (格局)

| Property | Value |
|----------|-------|
| Structure | {primary} |
| Category | {category} |
| Quality | {quality} |
| Dominance Score | {dominance:.1f} |
| Favorable Elements | {favorable} |
| Avoid Elements | {avoid} |

---

## ⚖️ Ten-God Distribution (十神分布)

| Ten God | Weight | Bar |
|---------|--------|-----|
| {name} | {score} | {'█' × n} |
| ... | ... | ... |

---

## 🔗 Branch Interactions (地支关系)

| Type | Branches | Notes |
|------|----------|-------|
| 六合 | (子, 丑) | ... |
| 六冲 | (寅, 申) | ... |
| ... | ... | ... |

---

## ⚡ Stem Combinations & Transformations (天干合化)

| Pair | Stems | Target | Status | Confidence |
|------|-------|--------|--------|------------|
| ... | ... | ... | ... | ... |

---

## ⚠️ Punishments & Harms (刑害)

| Type | Pair | Branches | Severity | Life Areas |
|------|------|----------|----------|------------|
| ... | ... | ... | ... | ... |

---

## ⭐ Symbolic Stars (神煞)

| Star | Location | Nature | Description |
|------|----------|--------|-------------|
| ✦ 天乙贵人 | year | 🟢 Auspicious | Help from influential people |
| ⚠ 羊刃 | day | 🔴 Inauspicious | Risk of accidents |
| ... | ... | ... | ... |

---

## 🎵 Na Yin Interactions (納音)

| Pillar | Na Yin | Element | vs Day Master |
|--------|--------|---------|---------------|
| ... | ... | ... | ... |

---

## 🌊 Life Stages (十二长生)

| Pillar | Stage | Index | Strength |
|--------|-------|-------|----------|
| ... | ... | ... | ... |

---

## 🎯 Luck Pillars (大运)

> Direction: {forward/backward} | Count: {n}

| # | GanZhi | Ten-God | Life Stage | Na Yin | Start Age | ~Year |
|---|--------|---------|------------|--------|-----------|-------|
| 1 | ... | ... | ... | ... | 3y 4m | ~2028 |
| ... | ... | ... | ... | ... | ... | ... |

---

## 📈 Chart Rating

**{rating} / 100** {'█' × n}{'░' × (20-n)}

---

## 📖 Narrative Interpretation (命理解读)

{narrative text as paragraphs}

---

## 🔮 Projection Views (运程展望)

> Period: {start} → {end}

### 10-Year Lookahead (十年展望)

| Year | GanZhi | Ten-God | Life Stage | Strength | Interactions | Δ |
|------|--------|---------|------------|----------|--------------|---|
| ... | ... | ... | ... | ... | ... | ... |

### Monthly Lookahead (月展望)

| # | Solar Date | Lunar Date | GanZhi | Ten-God | Life Stage | Interactions | Δ |
|---|------------|------------|--------|---------|------------|--------------|---|
| ... | ... | ... | ... | ... | ... | ... | ... |

### Daily Lookahead (日展望)

> Showing notable days only (with interactions or strength impact)

| Date | Day | GanZhi | Ten-God | Life Stage | Interactions | Δ |
|------|-----|--------|---------|------------|--------------|---|
| ... | ... | ... | ... | ... | ... | ... |
```

### 3.4 Key Formatting Decisions

| Aspect | Approach |
|--------|----------|
| **Section dividers** | `---` horizontal rules between major sections |
| **Section headers** | `## {emoji} Title (Chinese)` for visual scanning |
| **Data tables** | Standard Markdown pipe tables — renderable everywhere |
| **Auspicious indicators** | 🟢 Auspicious, 🔴 Inauspicious, 🟡 Mixed, ⚫ Neutral |
| **Strength bars** | Unicode block chars: `█░` inside table cells |
| **Delta formatting** | `+3` / `-2` / `0` with sign prefix |
| **Void markers** | ⚫ VOID badge in the Void column |
| **Term formatting** | Respects `--format` flag (cn/py/en/vi) via `format_term()` |
| **Encoding** | UTF-8, BOM-free |

### 3.5 CLI Integration

The CLI (`cli.py`) will:

1. Parse arguments (same flags as today, plus `--output` / `-o` for filename)
2. Run all analysis functions to collect data
3. Call `generate_report_markdown(...)` to build the string
4. Write to file (default: `output/report.md`) and print the path
5. Optionally print a brief summary to stdout (1-3 lines)

```
$ python -m bazi.cli -d 2025-02-15 -t 14:30 -g male -o output/chart_2025-02-15.md
✓ Report written to output/chart_2025-02-15.md (2.4 KB)
  Day Master: 丙 Fire (balanced, 4.5 pts) | Structure: 食神格
```

---

## 4. Module Breakdown — What Goes Where

### 4.1 `constants.py` — All Data Tables (~400 lines)

**Move here from `bazi.py`:**

| Constant | Lines (approx) | Notes |
|---|---|---|
| `HEAVENLY_STEMS`, `EARTHLY_BRANCHES` | 2 | Derived from `lunisolar_v2` tuples |
| `STEM_ELEMENT`, `STEM_POLARITY` | 22 | Element & polarity lookups |
| `GEN_MAP`, `CONTROL_MAP` | 12 | Five-element cycle maps |
| `BRANCH_HIDDEN_STEMS`, `HIDDEN_ROLES` | 16 | Hidden stems per branch |
| `BRANCH_ELEMENT` | 14 | Branch → native element |
| `LONGEVITY_STAGES`, `LONGEVITY_START` | 26 | Longevity stage arrays |
| `LONGEVITY_STAGES_EN`, `LONGEVITY_STAGES_VI` | 26 | English & Vietnamese labels |
| `LIU_HE`, `LIU_CHONG`, `LIU_HAI` | 24 | Six Combinations/Clashes/Harms |
| `SAN_HE`, `BAN_SAN_HE`, `SAN_HUI` | 20 | Three Combinations/Hui |
| `XING`, `ZI_XING_BRANCHES` | 6 | Punishment patterns |
| `SELF_PUNISH_BRANCHES`, `UNCIVIL_PUNISH_PAIRS`, `GRACELESS_PUNISH_PAIRS`, `BULLY_PUNISH_PAIRS`, `HARM_PAIRS`, `LIU_PO` | 30 | Detailed punishment/harm pair sets |
| `STEM_TRANSFORMATIONS`, `ADJACENT_PAIRS`, `STEM_CLASH_PAIRS` | 15 | Stem combination tables (4 valid directional clashes only: 甲-庚, 乙-辛, 丙-壬, 丁-癸) |
| `VOID_BRANCH_TABLE`, `XUN_NAMES` | 14 | Void branches |
| `NOBLEMAN_TABLE` through `BLOOD_KNIFE_TABLE` | 130 | All symbolic star lookup tables |
| `PILLAR_WEIGHTS`, `LU_MAP` | 15 | Scoring weights |

**Imports needed:** `lunisolar_v2.HEAVENLY_STEMS`, `lunisolar_v2.EARTHLY_BRANCHES`

### 4.2 `terminology.py` — Translation & Formatting (~120 lines)

**Move here from `bazi.py`:**
- `FORMAT_STRING` (module-level mutable default)
- `STEM_TRANS`, `BRANCH_TRANS`, `TENGOD_TRANS`, `INTERACTIONS_TRANS`, `LIFESTAGE_TRANS`, `STAR_TRANS`
- `TRANS_GROUPS`
- `get_trans_tuple()`
- `format_term()`

### 4.3 `core.py` — Chart Construction (~100 lines)

**Move here from `bazi.py`:**
- `normalize_gender()`
- `ganzhi_from_cycle()`
- `build_chart()`
- `from_lunisolar_dto()`
- `from_solar_date()`
- `_cycle_from_stem_branch()` (private helper, used by nayin and stars)

**Imports from siblings:** `constants`, `ten_gods.ten_god`, `hidden_stems.branch_hidden_with_roles`, `nayin.nayin_for_cycle`

### 4.4 `ten_gods.py` — Ten Gods System (~60 lines)

**Move here from `bazi.py`:**
- `_element_relation()`
- `ten_god()`
- `weighted_ten_god_distribution()`

**Imports from siblings:** `constants` (element maps, stem lists)

### 4.5 `longevity.py` — Twelve Longevity Stages (~80 lines)

**Move here:**
- `changsheng_stage()`
- `longevity_map()`
- `life_stage_detail()`
- `life_stages_for_chart()`
- `life_stage_for_luck_pillar()`

### 4.6 `hidden_stems.py` — Hidden Stem Utilities (~20 lines)

**Move here:**
- `branch_hidden_with_roles()`

### 4.7 `branch_interactions.py` — Branch Interaction Detection (~200 lines)

**Move here:**
- `detect_self_punishment()`
- `detect_xing()`
- `detect_branch_interactions()` (returns 六合, 六冲, 害, 三合, 半三合, 三会, 刑, 自刑)

### 4.8 `stem_transformations.py` — Stem Combination & Transformation (~200 lines)

**Move here:**
- `check_obstruction()`
- `check_severe_clash()`
- `detect_stem_combinations()`
- `detect_transformations()` (with relaxed `month_support` per §7 of theory corrections)

### 4.9 `punishments.py` — Punishments & Fu Yin (~120 lines)

**Move here:**
- `detect_punishments()` (emits separate Graceless/Bully/Uncivil types per §3 of theory corrections)
- `detect_fu_yin_duplication()`

### 4.10 `nayin.py` — NaYin System (~100 lines)

**Move here:**
- `_NAYIN_CSV_PATH`, `_NAYIN_DATA`, `_load_nayin()`
- `nayin_for_cycle()`, `_nayin_pure_element()`
- `nayin_for_pillar()`, `analyze_nayin_interactions()`

### 4.11 `symbolic_stars.py` — Symbolic Stars & Void (~150 lines)

**Move here:**
- `void_branches()`, `xun_name()`, `void_in_pillars()`
- `detect_symbolic_stars()`

### 4.12 `structure.py` — Chart Structure Classification (~180 lines)

**Move here:**
- `detect_month_pillar_structure()` (with protrusion check per §5 of theory corrections)
- `detect_special_structures()`
- `_get_structure_category()`
- `_assess_structure_quality()` (with Seven Killings Controlled fix per §6 of theory corrections)
- `classify_structure()`

> **Note:** `classify_structure_professional` was deleted in the 2026-02-26 theory unification. It is **not** re-added. The test import must be removed from `test_bazi.py`.

### 4.13 `scoring.py` — Day-Master Scoring & Rating (~120 lines)

**Move here:**
- `is_jian_lu()`
- `get_seasonal_strength()` (Five Seasons method per §1 of theory corrections)
- `score_day_master()` (weighted by `PILLAR_WEIGHTS`, no longevity-stage coupling)
- `rate_chart()`
- `recommend_useful_god()`

### 4.14 `luck_pillars.py` — Luck Pillar Generation (~180 lines)

**Move here:**
- `_next_ganzhi()`, `_luck_direction()`
- `find_governing_jie_term()`
- `calculate_luck_start_age()`
- `generate_luck_pillars()`

### 4.15 `annual_flow.py` — Annual Pillar Analysis (~50 lines)

**Move here:**
- `annual_analysis()`

### 4.16 `projections.py` — Time Projections (~350 lines)

**Move here:**
- `get_year_cycle_for_gregorian()`, `get_month_cycle_for_date()`, `get_day_cycle_for_date()`
- `get_new_moon_dates()`
- `generate_year_projections()`, `generate_month_projections()`, `generate_day_projections()`
  (all include stem+branch `strength_delta` per §4 of theory corrections)

### 4.17 `analysis.py` — Comprehensive Analysis (~200 lines)

**Move here:**
- `comprehensive_analysis()`
- `analyze_time_range()`

### 4.18 `narrative.py` — Text Generation (~80 lines)

**Move here:**
- `generate_narrative()`

### 4.19 `report.py` — Markdown Report Generator (~300 lines) ← **NEW**

**New module** — does not exist in current `bazi.py`. Builds the full Markdown report string from analysis data. See §3 above for detailed design.

**Key function:** `generate_report_markdown(...)` → `str`

**Imports from siblings:** `terminology.format_term`, `constants`, and receives pre-computed analysis dicts as arguments (no direct analysis logic).

### 4.20 `cli.py` — CLI Entry Point (~100 lines, down from ~250)

**Move here from `bazi.py`:**
- `argparse` setup (with new `--output` / `-o` flag)
- Orchestration: calls analysis functions, then `generate_report_markdown()`
- Writes Markdown to file, prints brief summary to stdout

The CLI shrinks significantly because all report formatting moves to `report.py`.

---

## 5. Dependency Graph

```
constants.py  ←── (imported by almost everything)
    ↑
terminology.py  (standalone, uses no bazi siblings)
    ↑
ten_gods.py  ←── constants
    ↑
hidden_stems.py  ←── constants
    ↑
longevity.py  ←── constants
    ↑
nayin.py  ←── constants, ten_gods
    ↑
core.py  ←── constants, ten_gods, hidden_stems, nayin
    ↑
branch_interactions.py  ←── constants
    ↑
stem_transformations.py  ←── constants
    ↑
punishments.py  ←── constants, core
    ↑
symbolic_stars.py  ←── constants, core
    ↑
structure.py  ←── constants, ten_gods
    ↑
scoring.py  ←── constants, branch_interactions, structure
    ↑
luck_pillars.py  ←── constants, core, longevity, ten_gods, nayin
    ↑
annual_flow.py  ←── constants, ten_gods, core
    ↑
projections.py  ←── constants, core, ten_gods, longevity, nayin, punishments
    ↑
analysis.py  ←── (aggregation of all above)
    ↑
narrative.py  ←── constants
    ↑
report.py  ←── terminology, constants (receives pre-computed dicts)
    ↑
cli.py  ←── all modules, writes report.md
```

> **Circular dependency note:** `structure.py` and `scoring.py` have a potential mutual dependency (`classify_structure` uses `weighted_ten_god_distribution`; `rate_chart` uses `classify_structure`). Resolution: keep `weighted_ten_god_distribution` in `ten_gods.py` (it only depends on `constants`), so both `structure.py` and `scoring.py` import from `ten_gods.py` without circularity.

---

## 6. Migration Strategy

### Phase 1: Create Package Structure (non-breaking)

1. Create `lunisolar-python/bazi/` directory
2. Create `bazi/__init__.py` that imports everything from the original `bazi.py` (temporary shim)
3. Verify all tests pass with the shim in place

### Phase 2: Fix Test — Remove Dead Import

Remove `classify_structure_professional` from `test_bazi.py` imports. This function was deleted in the 2026-02-26 theory unification (`20260226_bazi_theory_unification.md`). Any tests that reference it must be removed or updated.

### Phase 3: Extract Constants & Terminology

1. Create `bazi/constants.py` — move all data tables
2. Create `bazi/terminology.py` — move translation arrays and formatting
3. Update `bazi.py` to import from the new submodules
4. Run tests — must remain green

### Phase 4: Extract Leaf Modules (no intra-bazi dependencies)

Extract in this order (each step: move code, update imports, run tests):

1. `bazi/ten_gods.py`
2. `bazi/hidden_stems.py`
3. `bazi/longevity.py`
4. `bazi/nayin.py`
5. `bazi/branch_interactions.py`
6. `bazi/stem_transformations.py`
7. `bazi/punishments.py`

### Phase 5: Extract Core & Mid-Level Modules

1. `bazi/core.py` (depends on ten_gods, hidden_stems, nayin)
2. `bazi/symbolic_stars.py` (depends on constants, core)
3. `bazi/structure.py` (depends on ten_gods, constants)
4. `bazi/scoring.py` (depends on constants, branch_interactions, structure)
5. `bazi/luck_pillars.py` (depends on constants, core, longevity, ten_gods, nayin)
6. `bazi/annual_flow.py`

### Phase 6: Extract High-Level Modules

1. `bazi/projections.py`
2. `bazi/analysis.py`
3. `bazi/narrative.py`

### Phase 7: Build Markdown Report Module

1. Create `bazi/report.py` — implement `generate_report_markdown()`
2. Write unit tests for report output (check for expected headings, table structure)
3. Validate Markdown renders correctly in VS Code preview and GitHub

### Phase 8: Rebuild CLI

1. Create `bazi/cli.py` — argparse + orchestration + file writing
2. Add `--output` / `-o` flag (default: `output/report.md`)
3. Remove all `print()` formatting from old CLI block
4. CLI now: collect data → call `generate_report_markdown()` → write file → brief stdout summary

### Phase 9: Finalize Facade

1. Convert `bazi.py` (root level) to a thin re-export facade:
   ```python
   """Backward-compatible facade — all public symbols re-exported from bazi/ package."""
   from bazi import *  # noqa: F401,F403
   ```
   Or alternatively, since Python resolves `import bazi` to the package when both exist, delete the root `bazi.py` once the package fully replaces it.
2. Ensure `test_bazi.py` import block works unchanged (minus the deleted `classify_structure_professional`)
3. Add `bazi/__main__.py` so `python -m bazi` works

---

## 7. Test Migration Plan

### Required change

Remove `classify_structure_professional` from `test_bazi.py` imports — it was deleted in the 2026-02-26 theory unification and no longer exists.

### Minimal-change approach

All other imports stay the same — `bazi/__init__.py` re-exports everything. **One import line removed, zero other test changes needed.**

### New test for report module

Add `test_bazi_report.py` (or a class in `test_bazi.py`) that verifies:
- `generate_report_markdown()` returns a string
- Output contains expected section headings (`## 🏛️ Four Pillars`, etc.)
- Output contains valid Markdown table syntax (`| ... | ... |`)
- Output is valid UTF-8

### Optional future split

Once the refactor stabilizes, tests can be split similarly:

```
tests/
├── test_bazi_constants.py
├── test_bazi_ten_gods.py
├── test_bazi_longevity.py
├── test_bazi_branch_interactions.py
├── test_bazi_stem_transformations.py
├── test_bazi_structure.py
├── test_bazi_luck_pillars.py
├── test_bazi_projections.py
├── test_bazi_report.py
└── test_bazi_integration.py
```

This is **not required** for the initial refactor.

---

## 8. Naming Conflicts & Resolution

| Issue | Resolution |
|---|---|
| `bazi.py` (file) vs `bazi/` (package) | Python resolves `import bazi` to the package when both exist. Delete root `bazi.py` once migration is complete, or rename to `bazi_compat.py` during transition. |
| `classify_structure_professional` in test imports | **Remove it** — function was deleted in 2026-02-26 theory unification. No stub needed. |
| `_cycle_from_stem_branch` used by multiple modules | Place in `core.py` and import where needed |
| `_nayin_pure_element` used by multiple modules | Place in `nayin.py` and import where needed |
| `FORMAT_STRING` mutable global | Keep in `terminology.py`; CLI updates it via `terminology.FORMAT_STRING = ...` |
| `nayin.csv` path resolution | `nayin.py` resolves path relative to package root: `os.path.join(os.path.dirname(os.path.dirname(__file__)), "nayin.csv")` |

---

## 9. Lines of Code Estimates (per module)

| Module | Estimated LOC | Content |
|---|---|---|
| `constants.py` | ~400 | Pure data, no logic |
| `terminology.py` | ~120 | Translation arrays + 2 functions |
| `core.py` | ~100 | Chart building, gender validation, ganzhi helpers |
| `ten_gods.py` | ~60 | Ten-god calculation + distribution |
| `longevity.py` | ~80 | Longevity stage calculations |
| `hidden_stems.py` | ~20 | Single helper function |
| `branch_interactions.py` | ~200 | 3 detection functions |
| `stem_transformations.py` | ~200 | 4 detection/check functions |
| `punishments.py` | ~120 | 2 detection functions |
| `nayin.py` | ~100 | CSV loader + analysis |
| `symbolic_stars.py` | ~150 | Star detection + void functions |
| `structure.py` | ~180 | Structure classification |
| `scoring.py` | ~120 | DM scoring + chart rating + useful god |
| `luck_pillars.py` | ~180 | Luck pillar generation |
| `annual_flow.py` | ~50 | Annual analysis |
| `projections.py` | ~350 | Year/month/day projections |
| `analysis.py` | ~200 | Comprehensive + time-range analysis |
| `narrative.py` | ~80 | Text generation |
| **`report.py`** | **~300** | **Markdown report builder (NEW)** |
| `cli.py` | ~100 | Argparse + orchestration + file I/O (reduced from ~250) |
| `__init__.py` | ~60 | Re-exports |
| **Total** | **~3,270** | (vs ~3,500 original — net savings despite adding report.py) |

---

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Circular imports between structure.py and scoring.py | Keep `weighted_ten_god_distribution` in `ten_gods.py`; both import from there |
| Breaking existing `from bazi import X` statements | `bazi/__init__.py` re-exports all public symbols |
| NaYin CSV path resolution changes | Resolve from package root: `os.path.dirname(os.path.dirname(__file__))` |
| Mutable global `FORMAT_STRING` across modules | Single source in `terminology.py`; CLI mutates `terminology.FORMAT_STRING` |
| Markdown rendering inconsistencies | Use only GitHub-Flavored Markdown (GFM) features — no HTML, no extensions |
| Report file encoding issues | Always write with `encoding='utf-8'`, no BOM |
| Performance from additional import overhead | Negligible — Python caches imports after first load |

---

## 11. Out of Scope

- **No changes to `lunisolar_v2.py`** — the calendar engine is stable and separate
- **No changes to algorithm logic** — this is a pure structural refactoring (theory corrections from 2026-02-27 are already applied)
- **No changes to the TypeScript/Rust/C ports** — they maintain their own structure
- **No test logic changes** — only the dead `classify_structure_professional` import is removed

---

## 12. Acceptance Criteria

1. All existing `test_bazi.py` tests pass (with `classify_structure_professional` import removed)
2. `python -m bazi.cli -d 2025-02-15 -t 14:30 -g male` writes a valid Markdown file to `output/report.md`
3. The generated `report.md` renders correctly in VS Code Markdown preview and GitHub
4. Report contains all sections present in the current console output (Four Pillars, Structure, Ten-God Distribution, Interactions, Stars, Na Yin, Life Stages, Luck Pillars, Rating, Narrative, Projections)
5. No module exceeds ~400 lines
6. No circular imports
7. Every public function is importable via `from bazi import <name>`
8. `python -m bazi` works (via `__main__.py`)

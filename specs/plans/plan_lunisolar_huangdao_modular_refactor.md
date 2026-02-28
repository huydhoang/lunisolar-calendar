# Lunisolar & Huangdao Modular Refactoring Plan

> **Status**: Draft  
> **Date**: 2026-02-28  
> **Scope**: Refactor `lunisolar_v2.py` (~1,000 lines) and `huangdao_systems_v2.py` (~300 lines) into focused package modules; extract shared constants into a common `shared/` module  
> **Goal**: Mirror the `bazi/` package pattern — improve maintainability, testability, and cross-module reuse while preserving all public APIs

---

## 1. Problem Statement

### 1.1 Current State

The lunisolar-python directory has grown organically into a flat collection of scripts:

```
lunisolar-python/
├── lunisolar_v2.py          # ~1,000 lines — 10 classes + 2 public functions + constants + DTOs
├── huangdao_systems_v2.py   # ~300 lines — 3 classes + enums + constants + CLI
├── solar_terms.py           # Standalone ephemeris helper
├── moon_phases.py           # Standalone ephemeris helper
├── timezone_handler.py      # Standalone timezone wrapper
├── config.py                # Global config (ephemeris path, physical constants)
├── utils.py                 # Logging, CSV/JSON helpers, argparse
└── bazi/                    # ← Already refactored into clean module
```

### 1.2 Issues

1. **`lunisolar_v2.py` is monolithic**: 10 classes (TimezoneService, WindowPlanner, EphemerisService, MonthBuilder, TermIndexer, LeapMonthAssigner, SexagenaryEngine, LunarMonthResolver, ResultAssembler) plus data models and public APIs are all in one file.

2. **Duplicated constants**: `HEAVENLY_STEMS` and `EARTHLY_BRANCHES` are defined as rich tuples in `lunisolar_v2.py`, then re-extracted as plain char lists in `bazi/constants.py`. The `huangdao_systems_v2.py` defines its own `EarthlyBranch` enum, `BRANCH_ORDER`, `BRANCH_INDEX`, and `EARTHLY_BRANCH_PINYIN` — all overlapping with lunisolar_v2's data.

3. **Scattered ephemeris helpers**: `solar_terms.py` and `moon_phases.py` are standalone scripts imported by lunisolar_v2, huangdao_systems_v2, bazi/luck_pillars, and bazi/projections. They share the same pattern (load ephemeris, compute, cleanup) but aren't grouped.

4. **`timezone_handler.py` is orphaned**: Used by lunisolar_v2 and indirectly by huangdao_systems_v2, but lives at the flat top level.

5. **Cross-module import fragility**: `bazi/constants.py` imports from `lunisolar_v2` to extract stem/branch characters. If lunisolar_v2 moves into a package, this breaks.

6. **No package entry points**: Unlike `bazi/` which has `__main__.py`, neither lunisolar nor huangdao have `python -m` support.

---

## 2. Target Module Structure

```
lunisolar-python/
├── config.py                          # (unchanged) Global config — ephemeris path, physical constants
├── utils.py                           # (unchanged) Logging, CSV/JSON helpers, argparse
├── nayin.csv                          # (unchanged)
│
├── shared/                            # NEW — Cross-module shared data
│   ├── __init__.py                    # Re-exports all shared constants
│   ├── constants.py                   # Canonical HEAVENLY_STEMS, EARTHLY_BRANCHES (rich tuples)
│   │                                  #   + derived lookups: STEM_CHARS, BRANCH_CHARS,
│   │                                  #     BRANCH_INDEX, EARTHLY_BRANCH_PINYIN, BRANCH_ANIMALS
│   │                                  #   + PRINCIPAL_TERMS mapping (Z1–Z12 → ecliptic longitude)
│   │                                  #   + PRINCIPAL_TERM_NAMES (节气 names set)
│   └── models.py                      # PrincipalTerm, MonthPeriod, LunisolarDateDTO dataclasses
│
├── ephemeris/                         # NEW — Grouped astronomical helpers
│   ├── __init__.py                    # Re-exports: calculate_solar_terms, calculate_moon_phases
│   ├── solar_terms.py                 # (moved from top-level) calculate_solar_terms()
│   └── moon_phases.py                 # (moved from top-level) calculate_moon_phases()
│
├── lunisolar/                         # NEW — Lunisolar calendar engine package
│   ├── __init__.py                    # Re-exports public API: solar_to_lunisolar, solar_to_lunisolar_batch,
│   │                                  #   LunisolarDateDTO, get_stem_pinyin, get_branch_pinyin
│   ├── __main__.py                    # CLI entry point (moved from lunisolar_v2's __main__ block)
│   ├── timezone_service.py            # TimezoneService class
│   ├── window_planner.py              # WindowPlanner class (Winter Solstice anchoring)
│   ├── ephemeris_service.py           # EphemerisService class (new moon + principal term computation)
│   ├── month_builder.py               # MonthBuilder, TermIndexer, LeapMonthAssigner classes
│   ├── sexagenary.py                  # SexagenaryEngine class (ganzhi year/month/day/hour)
│   ├── resolver.py                    # LunarMonthResolver, ResultAssembler classes
│   └── api.py                         # solar_to_lunisolar(), solar_to_lunisolar_batch() orchestrators
│
├── huangdao/                          # NEW — Huangdao systems package
│   ├── __init__.py                    # Re-exports: HuangdaoCalculator, ConstructionStars, GreatYellowPath
│   ├── __main__.py                    # CLI entry point (moved from huangdao_systems_v2's main())
│   ├── constants.py                   # Domain-specific: BUILDING_BRANCH_BY_MONTH, AZURE_DRAGON_MONTHLY_START,
│   │                                  #   MNEMONIC_FORMULAS, GreatYellowPathSpirit enum, SPIRIT_SEQUENCE,
│   │                                  #   ConstructionStars auspiciousness tables
│   ├── construction_stars.py          # ConstructionStars class
│   ├── great_yellow_path.py           # GreatYellowPath class
│   └── calculator.py                  # HuangdaoCalculator (unified facade) + print_month_calendar()
│
├── timezone_handler.py                # (moved into shared/ or kept as-is — see §3.3)
│
├── lunisolar_v2.py                    # FACADE — backward-compatible re-exports from lunisolar/
├── huangdao_systems_v2.py             # FACADE — backward-compatible re-exports from huangdao/
├── solar_terms.py                     # FACADE — backward-compatible re-export from ephemeris/
├── moon_phases.py                     # FACADE — backward-compatible re-export from ephemeris/
├── bazi.py                            # FACADE — backward-compatible re-exports from bazi/ package
│
├── bazi/                              # (update imports only — see §5)
│   ├── constants.py                   # Change: import from shared/ instead of lunisolar_v2
│   ├── luck_pillars.py                # Change: import from ephemeris/ instead of solar_terms
│   ├── projections.py                 # Change: import from ephemeris/ and lunisolar/ instead of top-level
│   ├── core.py                        # Change: import from lunisolar/ instead of lunisolar_v2
│   ├── cli.py                         # Change: import from lunisolar/ instead of lunisolar_v2
│   └── ...                            # (remaining files unchanged)
│
├── test_lunisolar_v2.py               # (update imports, should keep working via facade)
└── test_bazi.py                       # (update imports, should keep working via facade)
```

---

## 3. Detailed Module Breakdown

### 3.1 `shared/constants.py` — Canonical Stem/Branch Data

**Motivation**: HEAVENLY_STEMS and EARTHLY_BRANCHES are the foundational constants used by lunisolar, huangdao, and bazi. Currently they're defined as rich tuples in `lunisolar_v2.py` and re-derived elsewhere. This file becomes the single source of truth.

**Contents (moved from `lunisolar_v2.py`):**

```python
# Rich tuples — canonical definition
HEAVENLY_STEMS = [
    ('甲', 'jiǎ', 'Wood Yang', 1), ...
]
EARTHLY_BRANCHES = [
    ('子', 'zǐ', 'Rat', 1, 23, 1), ...
]

# Derived lookups (convenience, computed once at import)
STEM_CHARS: List[str] = [s[0] for s in HEAVENLY_STEMS]
BRANCH_CHARS: List[str] = [b[0] for b in EARTHLY_BRANCHES]
BRANCH_INDEX: Dict[str, int] = {ch: i for i, ch in enumerate(BRANCH_CHARS)}
BRANCH_ANIMALS: Dict[str, str] = {b[0]: b[2] for b in EARTHLY_BRANCHES}

# Pinyin lookups (moved from huangdao_systems_v2.py)
EARTHLY_BRANCH_PINYIN = {
    "子": "Zǐ", "丑": "Chǒu", ...
}

# Principal solar terms mapping (moved from lunisolar_v2.py)
PRINCIPAL_TERMS = {
    1: 330, 2: 0, 3: 30, ...
}

# Principal term names set (moved from huangdao_systems_v2.py)
PRINCIPAL_TERM_NAMES = {"立春", "驚蟄", "清明", ...}
```

**Impact:**
- `bazi/constants.py` → imports `STEM_CHARS`, `BRANCH_CHARS` from `shared.constants` instead of extracting from `lunisolar_v2`
- `lunisolar/` modules → import from `shared.constants`
- `huangdao/` modules → import from `shared.constants`

### 3.2 `shared/models.py` — Shared Data Models

**Motivation**: `LunisolarDateDTO`, `PrincipalTerm`, and `MonthPeriod` are data classes used across both lunisolar and huangdao packages. Moving them to shared/ prevents circular imports and enables reuse.

**Contents (moved from `lunisolar_v2.py`):**

```python
@dataclass(frozen=True)
class PrincipalTerm: ...

@dataclass
class MonthPeriod: ...

@dataclass(frozen=True)
class LunisolarDateDTO: ...
```

### 3.3 `timezone_handler.py` — Decision

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| A | Keep at top level | No changes needed, minimal disruption | Inconsistent with modular pattern |
| B | Move to `shared/timezone.py` | Groups with shared code | It's more of a service than a constant |
| C | Move to `lunisolar/timezone_service.py` and merge | Clean ownership | huangdao also uses pytz directly |

**Recommendation**: **Option A** — keep `timezone_handler.py` at top level for now. It's a general utility (like `config.py` and `utils.py`) used by multiple packages. The `TimezoneService` class in lunisolar (which wraps `TimezoneHandler`) moves into `lunisolar/timezone_service.py`.

### 3.4 `ephemeris/` — Grouped Astronomical Helpers

**Motivation**: `solar_terms.py` and `moon_phases.py` share the same pattern (load Skyfield ephemeris, compute, cleanup) and are imported by 4+ consumers (lunisolar, huangdao, bazi/luck_pillars, bazi/projections). Grouping them makes the dependency explicit.

**Changes:**
- Move `solar_terms.py` → `ephemeris/solar_terms.py` (code unchanged)
- Move `moon_phases.py` → `ephemeris/moon_phases.py` (code unchanged)
- Create `ephemeris/__init__.py` with re-exports
- Leave facade files at top level for backward compatibility

### 3.5 `lunisolar/` — Calendar Engine Package

**Splitting strategy** — each class gets its own file:

| File | Classes / Functions | Lines (est.) |
|------|-------------------|-------------|
| `timezone_service.py` | `TimezoneService` | ~30 |
| `window_planner.py` | `WindowPlanner` | ~60 |
| `ephemeris_service.py` | `EphemerisService` | ~80 |
| `month_builder.py` | `MonthBuilder`, `TermIndexer`, `LeapMonthAssigner` | ~200 |
| `sexagenary.py` | `SexagenaryEngine` | ~150 |
| `resolver.py` | `LunarMonthResolver`, `ResultAssembler` | ~100 |
| `api.py` | `solar_to_lunisolar()`, `solar_to_lunisolar_batch()`, `get_stem_pinyin()`, `get_branch_pinyin()` | ~200 |
| `__main__.py` | CLI: argparse + display (from current `if __name__` block) | ~40 |
| `__init__.py` | Re-exports | ~20 |

**Grouping rationale for `month_builder.py`**: `MonthBuilder`, `TermIndexer`, and `LeapMonthAssigner` form a tight pipeline (build periods → tag terms → assign months). They share the same data structures and are always called sequentially. Keeping them together avoids unnecessary file fragmentation.

### 3.6 `huangdao/` — Huangdao Systems Package

| File | Classes / Functions | Lines (est.) |
|------|-------------------|-------------|
| `constants.py` | `EarthlyBranch` enum, `GreatYellowPathSpirit` enum, `BUILDING_BRANCH_BY_MONTH`, `AZURE_DRAGON_MONTHLY_START`, `MNEMONIC_FORMULAS`, `SPIRIT_SEQUENCE` | ~100 |
| `construction_stars.py` | `ConstructionStars` class (star calculation + solar term caching) | ~80 |
| `great_yellow_path.py` | `GreatYellowPath` class (spirit calculation) | ~15 |
| `calculator.py` | `HuangdaoCalculator` (facade) + `print_month_calendar()` | ~100 |
| `__main__.py` | CLI: argparse (from current `main()`) | ~30 |
| `__init__.py` | Re-exports | ~15 |

**Note**: `huangdao/constants.py` keeps domain-specific constants (building branches, spirits, mnemonic formulas). Generic branch data (pinyin, indices) moves to `shared/constants.py`.

---

## 4. Backward Compatibility — Facade Files

To avoid breaking any existing imports (bazi/, test files, benchmark scripts), the original file names remain as thin facades:

```python
# lunisolar_v2.py (facade)
"""Backward-compatible re-exports — real code lives in lunisolar/ package."""
from shared.constants import HEAVENLY_STEMS, EARTHLY_BRANCHES, PRINCIPAL_TERMS
from shared.models import PrincipalTerm, MonthPeriod, LunisolarDateDTO
from lunisolar.api import solar_to_lunisolar, solar_to_lunisolar_batch, get_stem_pinyin, get_branch_pinyin
from lunisolar.timezone_service import TimezoneService
from lunisolar.window_planner import WindowPlanner
from lunisolar.ephemeris_service import EphemerisService
from lunisolar.month_builder import MonthBuilder, TermIndexer, LeapMonthAssigner
from lunisolar.sexagenary import SexagenaryEngine
from lunisolar.resolver import LunarMonthResolver, ResultAssembler
```

```python
# huangdao_systems_v2.py (facade)
"""Backward-compatible re-exports — real code lives in huangdao/ package."""
from huangdao import HuangdaoCalculator, ConstructionStars, GreatYellowPath
from huangdao.constants import *
```

```python
# solar_terms.py (facade)
from ephemeris.solar_terms import calculate_solar_terms, main
```

```python
# moon_phases.py (facade)
from ephemeris.moon_phases import calculate_moon_phases, main
```

```python
# bazi.py (facade)
"""Backward-compatible re-exports — real code lives in bazi/ package."""
from bazi import (
    build_chart, from_solar_date, from_lunisolar_dto,
    comprehensive_analysis, analyze_time_range,
    generate_luck_pillars, calculate_luck_start_age,
    annual_analysis,
    generate_year_projections, generate_month_projections, generate_day_projections,
    detect_branch_interactions, detect_xing, detect_self_punishment,
    detect_stem_combinations, detect_transformations,
    detect_punishments, detect_fu_yin_duplication,
    detect_symbolic_stars, void_branches, void_in_pillars,
    classify_structure, score_day_master, rate_chart,
    ten_god, weighted_ten_god_distribution,
    changsheng_stage, longevity_map,
    nayin_for_cycle, nayin_for_pillar,
    generate_narrative, generate_report_markdown,
    format_term, FORMAT_STRING,
    HEAVENLY_STEMS, EARTHLY_BRANCHES,
)
```

---

## 5. Import Changes in Existing Code

### 5.1 `bazi/constants.py`

```python
# Before
from lunisolar_v2 import (
    EARTHLY_BRANCHES as _EB_TUPLES,
    HEAVENLY_STEMS as _HS_TUPLES,
)
HEAVENLY_STEMS: List[str] = [s[0] for s in _HS_TUPLES]
EARTHLY_BRANCHES: List[str] = [b[0] for b in _EB_TUPLES]

# After
from shared.constants import STEM_CHARS as HEAVENLY_STEMS, BRANCH_CHARS as EARTHLY_BRANCHES
```

### 5.2 `bazi/core.py`

```python
# Before
from lunisolar_v2 import LunisolarDateDTO, solar_to_lunisolar

# After (works via facade, but prefer direct)
from shared.models import LunisolarDateDTO
from lunisolar.api import solar_to_lunisolar
```

### 5.3 `bazi/luck_pillars.py`

```python
# Before
from solar_terms import calculate_solar_terms

# After
from ephemeris.solar_terms import calculate_solar_terms
```

### 5.4 `bazi/projections.py`

```python
# Before
from lunisolar_v2 import LunisolarDateDTO, solar_to_lunisolar, solar_to_lunisolar_batch
from moon_phases import calculate_moon_phases

# After
from shared.models import LunisolarDateDTO
from lunisolar.api import solar_to_lunisolar, solar_to_lunisolar_batch
from ephemeris.moon_phases import calculate_moon_phases
```

### 5.5 External consumers (tests, benchmarks)

These continue working via facade files (`lunisolar_v2.py`, `huangdao_systems_v2.py`). No changes required, but can optionally migrate.

---

## 6. Implementation Phases

### Phase 1 — Shared Foundation (no behavior change)

1. Create `shared/__init__.py` and `shared/constants.py`
   - Move `HEAVENLY_STEMS`, `EARTHLY_BRANCHES`, `PRINCIPAL_TERMS` from `lunisolar_v2.py`
   - Move `EARTHLY_BRANCH_PINYIN`, `PRINCIPAL_TERM_NAMES` from `huangdao_systems_v2.py`
   - Add derived lookups: `STEM_CHARS`, `BRANCH_CHARS`, `BRANCH_INDEX`, `BRANCH_ANIMALS`
2. Create `shared/models.py`
   - Move `PrincipalTerm`, `MonthPeriod`, `LunisolarDateDTO` from `lunisolar_v2.py`
3. Update `lunisolar_v2.py` imports to use `shared/` (keep all classes in-file for now)
4. Update `huangdao_systems_v2.py` imports to use `shared/`
5. **Run tests** — `test_lunisolar_v2.py`, `test_bazi.py`

### Phase 2 — Ephemeris Package

1. Create `ephemeris/` directory
2. Move `solar_terms.py` → `ephemeris/solar_terms.py`
3. Move `moon_phases.py` → `ephemeris/moon_phases.py`
4. Create `ephemeris/__init__.py` with re-exports
5. Replace original files with facade re-exports
6. **Run tests**

### Phase 3 — Lunisolar Package

1. Create `lunisolar/` directory structure
2. Extract classes one at a time (in dependency order):
   - `lunisolar/timezone_service.py` ← `TimezoneService`
   - `lunisolar/window_planner.py` ← `WindowPlanner`
   - `lunisolar/ephemeris_service.py` ← `EphemerisService`
   - `lunisolar/month_builder.py` ← `MonthBuilder` + `TermIndexer` + `LeapMonthAssigner`
   - `lunisolar/sexagenary.py` ← `SexagenaryEngine`
   - `lunisolar/resolver.py` ← `LunarMonthResolver` + `ResultAssembler`
   - `lunisolar/api.py` ← `solar_to_lunisolar()` + `solar_to_lunisolar_batch()` + pinyin helpers
3. Create `lunisolar/__init__.py` with public re-exports
4. Create `lunisolar/__main__.py` from `if __name__` block
5. Convert `lunisolar_v2.py` to facade
6. **Run tests** after each extraction step

### Phase 4 — Huangdao Package

1. Create `huangdao/` directory structure
2. Extract:
   - `huangdao/constants.py` ← domain-specific enums and lookup tables
   - `huangdao/construction_stars.py` ← `ConstructionStars`
   - `huangdao/great_yellow_path.py` ← `GreatYellowPath`
   - `huangdao/calculator.py` ← `HuangdaoCalculator` + `print_month_calendar()`
3. Create `huangdao/__init__.py` with re-exports
4. Create `huangdao/__main__.py` from `main()`
5. Convert `huangdao_systems_v2.py` to facade
6. **Run tests**

### Phase 5 — Update bazi/ Imports

1. Update `bazi/constants.py` → import from `shared.constants`
2. Update `bazi/core.py` → import from `shared.models` + `lunisolar.api`
3. Update `bazi/cli.py` → import from `lunisolar.api`
4. Update `bazi/luck_pillars.py` → import from `ephemeris.solar_terms`
5. Update `bazi/projections.py` → import from `shared.models` + `lunisolar.api` + `ephemeris.moon_phases`
6. **Run full test suite**

### Phase 6 — Cleanup

1. Verify all facade files only contain re-exports
2. Verify `python -m lunisolar`, `python -m huangdao`, `python -m bazi` all work
3. Remove `__pycache__/` artifacts
4. Update `README.md` with new import paths
5. Update `ARCHITECTURE.md` with new module diagram

---

## 7. Dependency Graph (Target State)

```
config.py ──────────────────────────────────────────────────→ (standalone)
utils.py ───────────────────────────────────────────────────→ (standalone)
timezone_handler.py ────────────────────────────────────────→ depends on: utils

shared/
  constants.py ─────────────────────────────────────────────→ (standalone)
  models.py ────────────────────────────────────────────────→ (standalone)

ephemeris/
  solar_terms.py ───────────────────────────────────────────→ depends on: config, utils, skyfield
  moon_phases.py ───────────────────────────────────────────→ depends on: config, utils, skyfield

lunisolar/
  timezone_service.py ──→ depends on: timezone_handler, utils
  window_planner.py ────→ depends on: config, utils, skyfield
  ephemeris_service.py ─→ depends on: ephemeris/, shared/models, utils
  month_builder.py ─────→ depends on: shared/models, utils
  sexagenary.py ────────→ depends on: shared/constants, utils
  resolver.py ──────────→ depends on: shared/models, utils
  api.py ───────────────→ depends on: all lunisolar/ modules, shared/, timezone_handler

huangdao/
  constants.py ─────────→ depends on: shared/constants
  construction_stars.py → depends on: shared/constants, ephemeris/solar_terms, shared/models
  great_yellow_path.py ─→ depends on: huangdao/constants
  calculator.py ────────→ depends on: lunisolar/api, huangdao/* modules, shared/constants

bazi/
  constants.py ─────────→ depends on: shared/constants  (was: lunisolar_v2)
  core.py ──────────────→ depends on: shared/models, lunisolar/api
  luck_pillars.py ──────→ depends on: ephemeris/solar_terms
  projections.py ───────→ depends on: shared/models, lunisolar/api, ephemeris/moon_phases
  cli.py ───────────────→ depends on: lunisolar/api
```

No circular dependencies exist in this layout.

---

## 8. Testing Strategy

| Phase | Test Command | What It Validates |
|-------|-------------|-------------------|
| 1 | `python -m pytest test_lunisolar_v2.py test_bazi.py` | Shared constants extraction didn't break anything |
| 2 | `python -m pytest test_lunisolar_v2.py` + `python -m ephemeris.solar_terms --help` | Ephemeris package works standalone and via facade |
| 3 | `python -m pytest test_lunisolar_v2.py` + `python -m lunisolar --date 2025-01-15` | Lunisolar package works standalone and via facade |
| 4 | `python huangdao_systems_v2.py -y 2025 -m 10` + `python -m huangdao -y 2025 -m 10` | Huangdao both paths produce identical output |
| 5 | `python -m pytest test_bazi.py` | Bazi still works with updated imports |
| 6 | Full regression: all tests + CLI smoke tests for all 3 packages | Everything works end-to-end |

### Regression capture strategy

Before starting Phase 1, capture reference output:
```bash
python lunisolar_v2.py --date 2025-06-15 --time 14:30 --tz Asia/Ho_Chi_Minh > ref_lunisolar.txt
python huangdao_systems_v2.py -y 2025 -m 6 -tz Asia/Ho_Chi_Minh > ref_huangdao.txt
python -m bazi --date 2025-06-15 --time 14:30 > ref_bazi.txt
```

After each phase, diff against reference output to catch regressions.

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Circular imports between `shared/` and `lunisolar/` | ImportError at startup | `shared/` has zero internal dependencies — only stdlib + `dataclasses` |
| `bazi/` tests fail after import path changes | CI red | Facade files guarantee old imports work; update bazi/ imports as last phase |
| Performance regression from extra module loading | Slower startup | Python caches `.pyc` — import overhead is negligible for 5-6 extra files |
| TypeScript port divergence | Maintenance burden | Document module mapping in `ARCHITECTURE.md` so TS port can follow same structure |
| `__pycache__` stale artifacts | Confusing import errors | Run `find . -name __pycache__ -exec rm -rf {} +` before each test phase |

---

## 10. Out of Scope

- **No algorithm changes** — all computation logic remains identical
- **No new features** — this is purely structural
- **No test file reorganization** — test files stay at top level (can be addressed in a future plan)
- **No changes to `main.py`, `antitransit.py`, `celestial_events.py`, `moon_illumination.py`, `tidal_data.py`** — these are independent scripts
- **No changes to TypeScript/Rust/C ports** — only Python restructuring

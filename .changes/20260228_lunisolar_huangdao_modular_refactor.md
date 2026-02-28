# Lunisolar & Huangdao Modular Refactor — Progress

> **Date**: 2026-02-28  
> **Plan**: `specs/plans/plan_lunisolar_huangdao_modular_refactor.md`  
> **Status**: All phases complete ✅

---

## Completed

### Phase 1 — `shared/` Foundation

**Created:**
- `lunisolar-python/shared/__init__.py` — re-exports all shared constants and models
- `lunisolar-python/shared/constants.py` — canonical `HEAVENLY_STEMS`, `EARTHLY_BRANCHES` (rich tuples), `PRINCIPAL_TERMS`, derived lookups (`STEM_CHARS`, `BRANCH_CHARS`, `BRANCH_INDEX`, `BRANCH_ANIMALS`), `EARTHLY_BRANCH_PINYIN`, `PRINCIPAL_TERM_NAMES`
- `lunisolar-python/shared/models.py` — `PrincipalTerm`, `MonthPeriod`, `LunisolarDateDTO` dataclasses

**Modified:**
- `lunisolar-python/lunisolar_v2.py` — removed inline constant definitions (`HEAVENLY_STEMS`, `EARTHLY_BRANCHES`, `PRINCIPAL_TERMS`) and dataclass definitions (`PrincipalTerm`, `MonthPeriod`, `LunisolarDateDTO`); added `from shared.constants import ...` and `from shared.models import ...`; removed unused `dataclass` import
- `lunisolar-python/huangdao_systems_v2.py` — removed local `EARTHLY_BRANCH_PINYIN` dict, `BRANCH_INDEX` re-derivation, and `PRINCIPAL_TERM_NAMES` set; now imports them from `shared.constants`; local `BRANCH_INDEX` aliased to `_SHARED_BRANCH_INDEX`
- `lunisolar-python/bazi/constants.py` — replaced `from lunisolar_v2 import ...` with `from shared.constants import STEM_CHARS, BRANCH_CHARS`; `HEAVENLY_STEMS` and `EARTHLY_BRANCHES` now assigned from shared

### Phase 2 — `ephemeris/` Package

**Created:**
- `lunisolar-python/ephemeris/__init__.py` — re-exports `calculate_solar_terms`, `calculate_moon_phases`
- `lunisolar-python/ephemeris/solar_terms.py` — full code moved from top-level `solar_terms.py`
- `lunisolar-python/ephemeris/moon_phases.py` — full code moved from top-level `moon_phases.py`

**Modified:**
- `lunisolar-python/solar_terms.py` — replaced with thin facade: `from ephemeris.solar_terms import calculate_solar_terms, main`
- `lunisolar-python/moon_phases.py` — replaced with thin facade: `from ephemeris.moon_phases import calculate_moon_phases, main`

### Phase 3 — `lunisolar/` Package (complete)

**Created (prior session):**
- `lunisolar/__init__.py`, `lunisolar/timezone_service.py`, `lunisolar/window_planner.py`

**Created (this session):**
- `lunisolar/ephemeris_service.py` — `EphemerisService.compute_new_moons()`, `compute_principal_terms()`
- `lunisolar/month_builder.py` — `MonthBuilder`, `TermIndexer`, `LeapMonthAssigner`
- `lunisolar/sexagenary.py` — `SexagenaryEngine` (year/month/day/hour ganzhi, Wu Shu Dun rule)
- `lunisolar/resolver.py` — `LunarMonthResolver`, `ResultAssembler`
- `lunisolar/api.py` — `solar_to_lunisolar()`, `solar_to_lunisolar_batch()`, `get_stem_pinyin()`, `get_branch_pinyin()`
- `lunisolar/__main__.py` — CLI entry point (`python -m lunisolar`)

**Modified:**
- `lunisolar_v2.py` — converted from ~1000-line monolith to ~60-line re-export facade

### Phase 4 — `huangdao/` Package (complete)

**Created:**
- `huangdao/__init__.py` — re-exports all public symbols
- `huangdao/constants.py` — `EarthlyBranch`, `GreatYellowPathSpirit` enums, all lookup tables
- `huangdao/construction_stars.py` — `ConstructionStars` with caching, solar-term-repeat rule
- `huangdao/great_yellow_path.py` — `GreatYellowPath.calculate_spirit()`
- `huangdao/calculator.py` — `HuangdaoCalculator`, `print_month_calendar()`
- `huangdao/__main__.py` — CLI entry point (`python -m huangdao`)

**Modified:**
- `huangdao_systems_v2.py` — converted from ~450-line monolith to ~35-line re-export facade

### Phase 5 — Update `bazi/` Imports (complete)

- `bazi/core.py` — `from lunisolar_v2 import` → `from shared.models import` + `from lunisolar.api import`
- `bazi/cli.py` — `from lunisolar_v2 import` → `from lunisolar.api import`
- `bazi/luck_pillars.py` — `from solar_terms import` → `from ephemeris.solar_terms import`
- `bazi/projections.py` — `from lunisolar_v2 import` / `from moon_phases import` → `from shared.models import` / `from lunisolar.api import` / `from ephemeris.moon_phases import`

### Phase 6 — Tests & Cleanup (complete)

**Results:**
- `test_bazi.py` — ✅ all 170 tests pass
- `test_lunisolar_v2.py` — ✅ all 9 tests pass

**Fixes applied:**
- `lunisolar-python/utils.py` — Replaced the `logging.basicConfig()` + `sys.stdout.reconfigure(encoding='utf-8')` pattern with a simple manual handler setup that never touches `sys.stdout`. The old approach corrupted pytest's `EncodedFile` capture wrapper (backed by a tmpfile) because `reconfigure()` closes and re-opens the underlying stream, making pytest teardown fail with `ValueError: I/O operation on closed file` → `AttributeError: 'EncodedFile' object has no attribute 'getvalue'`. The new pattern:
  ```python
  logger = logging.getLogger(__name__)
  if not logging.getLogger().handlers:
      handler = logging.StreamHandler(sys.stdout)
      handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
      logging.getLogger().addHandler(handler)
      logging.getLogger().setLevel(logging.INFO)
  return logger
  ```
- `lunisolar-python/lunisolar/__main__.py` — Added UTF-8 stdout wrapper for Windows console (CJK output would otherwise raise `UnicodeEncodeError` on `cp1252` terminals):
  ```python
  if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
      sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
  ```
- `lunisolar-python/huangdao/__main__.py` — Same UTF-8 stdout wrapper as above.

**CLI smoke tests:**
- `python -m lunisolar --date 2025-06-15` — ✅ outputs `Lunisolar: 2025-5-20 12:00`
- `python -m huangdao -y 2025 -m 6` — ✅ outputs full June 2025 calendar table

---

## Known Bug — `test_lunisolar_v2.py` (fixed)

~~**Symptom:** All 9 tests fail with:~~
~~**Root cause:** …~~
~~**Fix (not yet applied):** …~~

**Resolved.** See Phase 6 above.

## Remaining

~~- Apply the `utils.py` fix and rerun `test_lunisolar_v2.py`~~  
~~- Smoke-test CLI entry points: `python -m lunisolar --date 2025-06-15`, `python -m huangdao -y 2025 -m 6`~~  
- Clean `__pycache__/` artifacts
- Update `README.md` / `ARCHITECTURE.md` with new module diagram

# 20260228 — Bazi Modular Refactor

## Summary
Implemented the full modular refactoring plan from `specs/plans/plan_bazi_modular_refactor.md`,
splitting the ~3520-line monolithic `bazi.py` into a structured `bazi/` Python package with
20 focused submodules. All 170 tests pass.

---

## New Files — `lunisolar-python/bazi/` package

| Module | Responsibility |
|--------|---------------|
| `constants.py` | All data tables and lookup constants (stems, branches, elements, interaction sets, star tables) |
| `terminology.py` | Translation arrays, `FORMAT_STRING` global, `format_term()` |
| `ten_gods.py` | `_element_relation()`, `ten_god()`, `weighted_ten_god_distribution()` |
| `hidden_stems.py` | `branch_hidden_with_roles()` |
| `longevity.py` | 12 Longevity Stages: `changsheng_stage()`, `longevity_map()`, `life_stage_detail()`, etc. |
| `nayin.py` | Na Yin CSV loading, `nayin_for_cycle()`, `nayin_for_pillar()`, `analyze_nayin_interactions()` |
| `core.py` | `normalize_gender()`, `ganzhi_from_cycle()`, `build_chart()`, `from_solar_date()` |
| `branch_interactions.py` | `detect_branch_interactions()`, `detect_xing()`, `detect_self_punishment()` |
| `stem_transformations.py` | `detect_stem_combinations()`, `detect_transformations()`, `check_obstruction()`, `check_severe_clash()` |
| `punishments.py` | `detect_punishments()`, `detect_fu_yin_duplication()` |
| `symbolic_stars.py` | `void_branches()`, `xun_name()`, `void_in_pillars()`, `detect_symbolic_stars()` |
| `structure.py` | `classify_structure()`, `detect_month_pillar_structure()`, `detect_special_structures()` |
| `scoring.py` | `score_day_master()`, `rate_chart()`, `recommend_useful_god()`, `is_jian_lu()` |
| `luck_pillars.py` | `generate_luck_pillars()`, `calculate_luck_start_age()`, `find_governing_jie_term()` |
| `annual_flow.py` | `annual_analysis()` |
| `projections.py` | `generate_year/month/day_projections()`, `get_new_moon_dates()`, cycle helpers |
| `analysis.py` | `comprehensive_analysis()`, `analyze_time_range()` |
| `narrative.py` | `generate_narrative()` |
| `report.py` | **NEW** — `generate_report_markdown()`: Markdown document builder (see plan §3) |
| `cli.py` | Argparse CLI with `--output` for Markdown file, console report preserved |
| `__init__.py` | Re-exports full public API for backward compatibility |
| `__main__.py` | Enables `python -m bazi` |

---

## Bug Fixes

### `stem_transformations.py`
- **`month_support` logic**: Fixed to require `month_elem == target` (direct match only).
  Previously included `GEN_MAP.get(month_elem) == target` (generates check), which
  incorrectly marked Earth month as supporting Metal transformations.

### `test_bazi.py`
- Removed dead import of `classify_structure_professional` (deleted in prior theory unification).
- `TestStructure.test_basic_structure`: changed assertion from `assertIsInstance(str)` to
  `assertIsInstance(dict)` — `classify_structure()` returns a dict, not a string.
- `TestStructure.test_professional_structure`: removed (function no longer exists).
- `TestUsefulGod.test_strong_dm` / `test_weak_dm`: `recommend_useful_god()` `structure`
  parameter defaulted to `None` so 2-argument calls work.
- `TestScoreDayMaster.test_example_chart`: changed `assertIsInstance(int)` to
  `assertIsInstance((int, float))` — `score_day_master()` returns `float`.
- `TestPhucNgam.test_no_match`: corrected assertion to `assertEqual(len(results), 0)` —
  docstring said "no match" but assertion expected 1; the chart cycles 1,2,3,4 have no
  癸酉 pillar, so 0 matches is correct.
- `TestNaYinInteractions.test_vs_day_master_has_all_pillars`: fixed erroneous
  `assertIn(pname, result['vs_day_master'][pname])` → `assertIn(pname, result['vs_day_master'])`.
- `TestPhucNgam.test_exact_match`: replaced `detect_phuc_ngam()` (non-existent) with
  `detect_fu_yin_duplication()`.

---

## Circular Import Resolution
`nayin.py` uses a lazy `from .core import _cycle_from_stem_branch` inside the
`nayin_for_pillar()` function body to break the core↔nayin circular dependency
(core imports nayin for `build_chart`; nayin needed core for cycle conversion).

---

## NaYin Path Fix
`nayin.py` CSV path uses `os.path.dirname(os.path.dirname(__file__))` to reach
the parent `lunisolar-python/` directory, since the module moved one level deeper
into `bazi/nayin.py`.

---

## Backward Compatibility
`bazi/__init__.py` re-exports every symbol that was previously at the top level
of `bazi.py`. All existing `from bazi import ...` statements in `test_bazi.py`
and downstream code continue to work without modification. Python resolves
`import bazi` to the package directory over the old `.py` file.

---

## Test Results
```
170 passed in 0.25s
```

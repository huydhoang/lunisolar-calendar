# Bazi Terminology Formatting & Projections Refactor
**Date**: 2026-02-26

## Overview
This session focused on fixing the missing Luck Pillar starting age bug, optimizing the projection views with date ranges, and standardizing the output of Chinese terminology using a unified localized format.

## Added
*   **`bazi.py`**: Added `find_governing_jie_term` helper function to reliably determine the preceding or succeeding Jie (Nodal) solar term date for Luck Pillar calculation.
*   **`bazi.py` CLI**: Added `--proj-start` and `--proj-end` argparse flags to allow bounding the projection (lookahead) summaries.
*   **`bazi.py` CLI**: Added `--format` (`-f`) flag to customize Chinese terminology output (e.g., `cn/py/en/vi`, `cn/en`, `cn`).
*   **`bazi.py`**: Added terminology translation arrays (`STEM_TRANS`, `BRANCH_TRANS`, etc.) and a `get_trans_tuple` helper to search for translations using direct comparison instead of dictionary lookups, avoiding potential encoding issues.

## Modified
*   **`bazi.py` CLI**: Updated the `__main__` block to parse the newly added projection and format arguments.
*   **`bazi.py` (Projections)**: 
    *   Modified `generate_year_projections` to iterate through explicit start/end years instead of a fixed duration counter.
    *   Refactored `generate_month_projections` and `generate_day_projections` to handle explicit date ranges using robust date arithmetic and `solar_to_lunisolar_batch` for optimization.
*   **`bazi.py` (Formatting)**: 
    *   Replaced the intermediate `TERM_TRANSLATIONS` dictionary with a list-based lookup system.
    *   Updated `format_term()` to respect the user-defined `FORMAT_STRING`.
    *   Fixed a `TypeError` in the Interaction rendering logic by properly handling dictionaries and tuples within the interaction entries.
*   **Terminology / Variable Names**: Renamed the potentially overloading term `phuc_ngam` to `fu_yin_duplication` across `bazi.py` and `test_bazi.py`.

## Removed
*   N/A

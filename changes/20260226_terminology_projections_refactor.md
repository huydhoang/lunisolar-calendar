# Bazi Terminology Formatting & Projections Refactor
**Date**: 2026-02-26

## Overview
This session focused on fixing the missing Luck Pillar starting age bug, optimizing the projection views with date ranges, and standardizing the output of Chinese terminology using a unified localized format.

## Added
*   **`bazi.py`**: Added `find_governing_jie_term` helper function to reliably determine the preceding or succeeding Jie (Nodal) solar term date for Luck Pillar calculation.
*   **`bazi.py` CLI**: Added `--proj-start` and `--proj-end` argparse flags to allow bounding the projection (lookahead) summaries.
*   **`bazi.py`**: Added a master `TERM_TRANSLATIONS` dictionary at the top of the file. It contains the standard Chinese character keys mapping to `(Pinyin, English, Vietnamese)` tuples for:
    *   Heavenly Stems and Earthly Branches
    *   Ten Gods (十神)
    *   Interactions (合冲刑害)
    *   12 Longevity Stages (十二长生)
    *   Symbolic Stars (神煞)
*   **`bazi.py`**: Added the `format_term(chinese_str)` function to encapsulate the logic for producing the standardized string `Chinese/Pinyin/English/Vietnamese` (also automatically handles resolving 2-character Branch/Stem pairings like 甲子).

## Modified
*   **`bazi.py` CLI**: Updated the `__main__` block to parse the newly added projection arguments and pass the accurate `birth_date` and `solar_term_date` to the `generate_luck_pillars` function.
*   **`bazi.py` (Projections)**: 
    *   Modified `generate_year_projections` to iterate through explicit start/end years instead of a fixed duration counter.
    *   Refactored `generate_month_projections` and `generate_day_projections` to handle explicit date ranges using robust date arithmetic. Furthermore, they now utilize the `solar_to_lunisolar_batch` method imported from `lunisolar_v2.py` for highly optimized, bulk processing instead of expensive iterative single date conversions.
*   **`bazi.py` CLI (Formatting)**: Updated the vast majority of string formatting calls in the final `print` statements to wrap relevant data inside the new `format_term()` helper, unifying the terminal reporting. 
*   **Terminology / Variable Names**: Renamed the potentially overloading term `phuc_ngam` to the more universally recognized `fu_yin_duplication` indicating "Fu Yin / Duplication". This renaming occurred across variable names and internal keys in both `bazi.py` and `test_bazi.py`.

## Removed
*   N/A

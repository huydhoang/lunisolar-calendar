# Bazi Theory Unification Summary - 2026-02-26

This document summarizes the changes made to `lunisolar-python/bazi.py` to unify the chart structure classification logic and align it with traditional Bazi (Tử Bình) principles.

## Changes Overview

### Added
- **Constants**:
    - `PILLAR_WEIGHTS`: Defines seasonal weighting for strength calculation (Month: 3.0, Day: 1.5, Year/Hour: 1.0).
    - `LU_MAP`: Mapping of Day Masters to their Prosperity (Lu) branches.
- **Helpers**:
    - `is_jian_lu(dm_stem, month_branch)`: Strictly checks if the Prosperity star is in the Month Branch.
    - `detect_month_pillar_structure(chart)`: Implements "Protrusion-based" detection (finding the Heavenly Stem that appears from the Month Branch's hidden stems).
    - `_get_structure_category(ten_god)`: Maps specific Ten-Gods to general categories (e.g., "食神" -> "食伤格").
    - `_assess_structure_quality(...)`: Evaluates if a structure is "成格" (formed) or "破格" (broken) based on Day Master strength and conflicting elements.

### Modified
- **`score_day_master(chart)`**:
    - Now applies `PILLAR_WEIGHTS` to all scoring factors (Month Command, Root Depth, Visible Support).
    - Removed coupling with the "Hurt Officer" detection logic.
    - Updated strength classification boundaries to match weighted scores.
- **`classify_structure(chart, strength)`**:
    - Refactored from a simple string return to a comprehensive **Dictionary return**.
    - Returns: `primary`, `category`, `quality`, `dominance_score`, `is_special`, `is_broken`, and `notes`.
    - Implements priority: Special Structures > Month Protrusion > Dominant Ten-God.
- **`recommend_useful_god(chart, strength, structure)`**:
    - Updated signature to accept the new `structure` dict.
    - Uses `structure['primary']` for specific remedies (like the "Hurt Officer" remedy).
- **`rate_chart` & `generate_narrative`**:
    - Updated to parse the new dictionary-based structure analysis.
- **CLI (`__main__`)**:
    - Refactored to display the enriched structural data (Basic Structure + Quality + Dominance).

### Removed
- **`detect_hurt_officer_structure(chart)`**: Deleted and replaced by the unified relationship-based detection logic within the new classification system.
- **`classify_structure_professional(...)`**: Redundant logic merged into the unified `classify_structure`.

## Benefits
1. **Theoretic Accuracy**: Uses "Month Command Protrusion" (月令透出) which is the gold standard for pattern detection.
2. **Weighted Scoring**: Recognizes the disproportionate influence of the birth season (Month Branch).
3. **Decoupling**: Separates strength calculation from structure classification, allowing each to be refined independently.
4. **Rich Metadata**: Provides "Quality" and "Dominance" metrics instead of a single label.

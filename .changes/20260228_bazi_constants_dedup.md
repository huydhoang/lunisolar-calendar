# 20260228 — Bazi Constants Deduplication & Terminology Fallthrough

## Summary

Eliminated data duplication across the three bazi data files (`constants.py`,
`glossary.py`, `terminology.py`) by establishing a clear single-source-of-truth
hierarchy. `glossary.py` is now the authoritative reference; `constants.py`
derives algorithm-facing views from it; `terminology.py` falls through to it for display.
All 170 tests pass with zero consumer changes.

> Note: `structure_constants.py` was renamed to `glossary.py` in the same session
> once its scope was confirmed to cover all Bazi terminology, not only structure names.

---

## Problem

After the modular refactor and the creation of `glossary.py` (originally `structure_constants.py`) as a comprehensive
bilingual reference (1,227 lines of Term tuples), ten categories of data were defined
in both files:

| Duplicated Data | `constants.py` | `glossary.py` |
|---|---|---|
| Stem pair → element | `STEM_TRANSFORMATIONS` | `STEM_PAIR_TO_ELEMENT` |
| Six Combinations keys | `LIU_HE` (manual frozensets) | `BRANCH_PAIR_TO_LIU_HE` (same keys) |
| Six Clashes keys | `LIU_CHONG` | `BRANCH_PAIR_TO_LIU_CHONG` |
| Six Harms keys | `LIU_HAI` | `BRANCH_PAIR_TO_LIU_HAI` |
| Six Destructions keys | `LIU_PO` | `BRANCH_PAIR_TO_LIU_PO` |
| Stem clash pairs | `STEM_CLASH_PAIRS` | `STEM_CLASH_PAIR_TO_TERM` |
| Three Combinations | `SAN_HE` | `SAN_HE_SET_TO_TERM` |
| Directional Combos | `SAN_HUI` | `SAN_HUI_SET_TO_TERM` |
| Self-punishment branches | `SELF_PUNISH_BRANCHES` / `ZI_XING_BRANCHES` | `SELF_PUNISHMENT_BRANCHES` |
| Punishment pair sets | `GRACELESS_PUNISH_PAIRS`, etc. | `GRACELESS_PUNISHMENT_SET`, etc. |

Additionally, `terminology.py` could not translate any term from `structure_constants.py`
(structure names, punishment types, stem combinations, etc.) because the two files were
completely disconnected.

---

## Changes

### `constants.py`
- **New import** from `glossary`: 14 symbols used to derive algorithm-facing sets.
- **Branch interactions** (`LIU_HE`, `LIU_CHONG`, `LIU_HAI`, `SAN_HE`, `SAN_HUI`,
  `BAN_SAN_HE`, `XING`, `ZI_XING_BRANCHES`): replaced manual frozenset literals with
  derivations from `glossary` dict keys.
- **`STEM_TRANSFORMATIONS`**: now `dict(STEM_PAIR_TO_ELEMENT)` instead of a duplicate literal.
- **Punishment/harm pairs** (`SELF_PUNISH_BRANCHES`, `UNCIVIL_PUNISH_PAIRS`,
  `GRACELESS_PUNISH_PAIRS`, `BULLY_PUNISH_PAIRS`, `HARM_PAIRS`, `LIU_PO`,
  `STEM_CLASH_PAIRS`): derived from `glossary` sets using
  `itertools.combinations` for pair generation.
- **All exported names unchanged** — zero impact on 17 consumer modules.

### `terminology.py`
- **New import**: `TERMINOLOGY_LOOKUP` from `glossary`.
- **`get_trans_tuple()`**: added fallthrough to `TERMINOLOGY_LOOKUP` when local
  translation arrays don't contain the term. This means `format_term()` now works for
  all ~100+ terms in `glossary` (structure names like 正官格, interaction
  terms like 子丑合化土, punishment types, strength terms, etc.).

### No changes to
- `glossary.py` (untouched — pure data reference)
- `__init__.py` (all re-exports unchanged)
- Any consumer module (branch_interactions.py, punishments.py, scoring.py, etc.)

---

## Architecture After Refactor

```
glossary.py   → Authoritative bilingual Term tuples (pure data, no imports from bazi/)
        ↓ keys/sets
constants.py  → Algorithm-facing views (frozensets, dicts) derived from glossary
                + unique data (element maps, hidden stems, star tables, weights)
        ↓ format_term()
terminology.py → Display formatting layer: format_term() + local translation arrays
                 Falls through to glossary.TERMINOLOGY_LOOKUP
```

Single-responsibility boundaries:
- **`glossary.py`**: "What is this concept called in CN/PY/EN/VI?"
- **`constants.py`**: "What data does the algorithm need to compute?"
- **`terminology.py`**: "How do we format a term for the user?"

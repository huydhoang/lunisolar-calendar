# Bazi Logic Fixes — Tử Bình Theory Corrections

**Date:** 2026-03-01  
**Files Changed:** `bazi/structure.py`, `bazi/report.py`

---

## 1. Chart Structure (格局) — Strict Month Branch Main Qi

**File:** `bazi/structure.py`  
**Function:** `detect_month_pillar_structure`

### Problem
The function used a *protrusion (透出)* priority: it scanned through all hidden stems of the month branch and, if any non-main hidden stem appeared as a visible (protruding) stem on the year/month/hour pillar, that stem's Ten-God was promoted as the structure determinant. This allowed a middle or residual qi to override the main qi (本氣) if it happened to protrude, causing charts to be misclassified into the wrong Eight Regular Structure (八正格).

### Fix
Removed the protrusion override. `detect_month_pillar_structure` now unconditionally returns the Ten-God relationship of the **month branch Main Qi** (`month_hidden[0]`). This strictly follows the traditional Zi Ping (子平) principle that the Month Branch (月令/Nguyệt Lệnh) is the sole determinant of the Eight Regular Structures at Tier 3.

Protrusion still plays a role at higher tiers (化格, 从格) and in composite structure detection, which are unaffected by this change.

---

## 2. Report Section Ordering — Missing Elements Before Useful God

**File:** `bazi/report.py`  
**Function:** `generate_report_markdown`

### Problem
The **Missing Elements (五行缺失)** and **Branch Conflicts (支局衝突)** sections were rendered *after* the Useful God Recommendation (用神) section. Since missing elements (especially missing Officer/Power — 官殺缺失) directly inform why certain elements are recommended or avoided, placing them after the recommendation broke the logical flow of the analysis.

### Fix
Moved the Missing Elements and Branch Conflicts sections to appear **before** the Useful God Recommendation section. The new order is:

1. Chart Structure (格局)
2. Missing Elements (五行缺失) — *new position*
3. Branch Conflicts / Competing Frames (支局衝突) — *new position*
4. Useful God Recommendation (用神) — *moved after context sections*
5. Ten-God Distribution (十神分布)
6. … (remainder unchanged)

---

## Context: Already-Implemented Algorithms (verified, no changes needed)

The following plan items from `plan_bazi_modular_refactor_logic_fixes.md` were already correctly implemented in the codebase prior to this change set:

- **Resource element (印星) support in `score_day_master`**: Section `2b` in `scoring.py` already accumulates points for hidden stems whose element generates the Day Master, not just those matching the DM element exactly.
- **Interaction bonuses for 三合/三会 targeting Resource element**: `score_day_master` already boosts score for frames that form the Resource element.
- **Temperature assessment (調候)**: `_assess_chart_temperature` and `recommend_useful_god` already apply heat/cold balancing. Hot charts (Fire/Wood dominant) correctly recommend Water (Officer) first and flag Fire/Wood as elements to avoid.
- **Jealous combination (争合) penalty in `detect_transformations`**: When either stem in a combination pair appears in multiple pillars, status is forcibly set to `"Hợp (bound — jealous)"` and confidence is capped at 30%, preventing a jealous combination from registering as a successful transformation.
- **Missing elements detection**: `detect_missing_elements` in `analysis.py` correctly identifies elements absent from all visible stems and main/middle hidden stems, classifying them by Ten-God category.
- **Competing frames detection (群比争財)**: `detect_competing_frames` in `analysis.py` correctly identifies branches torn between a peer frame (Bi-Jie/比劫) and a wealth frame (財星), flagging them as 群比争財 with a high-risk warning.
- **Narrative updates**: `generate_narrative` in `narrative.py` already produces contextual notes for missing Officer/Power and for 群比争財 scenarios.

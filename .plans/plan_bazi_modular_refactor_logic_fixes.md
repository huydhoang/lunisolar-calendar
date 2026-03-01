# Plan: Bazi Module Refactor and Core Logic Fixes (Tử Bình Tứ Trụ)

Based on the expert review of the `bazi` module (comparing `report.md` with `temp.md`), several flaws exists in the current traditional Zi Ping logic. This plan outlines specific fixes across various files in `lunisolar-py/bazi/`.

## 1. Fix Chart Structure Evaluation (Cách Cục)
**Location**: `lunisolar-py/bazi/structure.py`
**Issue**: The current code calculates an `Eight Regular Structures` (Tier 3) by comparing the *Month Pillar Score* vs the *Maximum Dominant Ten God Score*. If `month_score < dominance_score * 0.7`, it falls back to the dominant Ten God instead of respecting the Month Main Qi. This incorrectly caused a 偏财格 (Indirect Wealth / Thiên Tài cách) to become 偏印格 (Indirect Resource / Thiên Ấn cách) just because of multiple occurrences of Resource stems.
**Action Items**:
- Modify `classify_structure` and `detect_month_pillar_structure` to STRICTLY prioritize the Month Branch Main Qi for structure determination (Eight Regular Structures).
- Only override the month-based structure if there is a Tier 1 (Special) or Tier 2 (Extreme) structure, or if the Main Qi is severely damaged and another branch Qi protrudes heavily.
- Eliminate the arbitrary `month_score >= dominance_score * 0.7` condition. Rely primarily on what Ten-God is rooted in the month branch (Nguyệt Lệnh).

## 2. Stem Transformation vs. Jealous Combinations (Thiên Can Tranh Hợp)
**Location**: `lunisolar-py/bazi/stem_transformations.py`
**Issue**: Jealous combination (争合 - e.g. two Yi stems fighting for one Geng) correctly identifies conflict but does not sufficiently penalize the transformation confidence in `detect_transformations()`. Thus, an invalid transformation gets a paradoxical "95% Successful" score.
**Action Items**:
- Integrate the result of `detect_jealous_combinations()` into `detect_transformations()`. 
- When evaluating a pair `(s1, s2)`, check if either stem is participating in a Jealous Combination.
- If so, forcibly set `status = "合而不化 (bound - jealous)"` and limit `confidence <= 30%`. Ensure it NEVER registers as "Hóa (successful)".

## 3. Day Master Vượng Suy (Strength) & Included Resources
**Location**: `lunisolar-py/bazi/scoring.py`
**Issue**: The `score_day_master()` function loops through hidden stems and visible stems but ONLY checks `if STEM_ELEMENT[stem] == dm_elem`. This means **it completely ignores Resource (Yin / 印 - the element that generates Day Master)** when adding support points! A chart with heavy wood supporting fire was thus under-scored.
**Action Items**:
- Refactor `score_day_master()` to accumulate points for BOTH **Same Element (Peers/Bi Jie)** AND **Generating Element (Resource/Zheng Yin/Pian Yin)**.
- Update `interactions` bonus calculation to also include San He/San Hui frames that target the Resource Element, not just the exact DM Element.

## 4. Useful/Joyful God (Dụng/Hỷ Thần) Heat/Cold Balancing
**Location**: `lunisolar-py/bazi/scoring.py` (`recommend_useful_god()`)
**Issue**: A Ding Fire day master sitting on a massive Si-Wu-Wei (Southern Fire frame) and Wood was told "Avoid: None" and Recommended "Wood" as Joyful God. The logic is too simplistic and does not account for Temperature/Dryness (Điều Hầu).
**Action Items**:
- Enhance `recommend_useful_god()` to check if the chart is overly Hot (Fire/Wood frames) or overly Cold (Water/Metal frames).
- If DM is Fire and chart is exceedingly strong/hot, recommend **Water** (Control/Officer) to cool down, and **Earth** (Output) to vent. Strongly add Wood/Fire into the **Avoid** array.
- Remove default empty arrays for "Avoid". Overly strong charts MUST avoid their own generating (Resource) and peer elements.

## 5. Notice Missing Elements (Khuyết Hành) & Branch Conflict
**Location**: `lunisolar-py/bazi/analysis.py`, `lunisolar-py/bazi/report.py`, `lunisolar-py/bazi/narrative.py`
**Issue**: The report failed to mention that the chart had entirely ZERO Water (Missing Officer/Power - Khuyết Quan Sát). Furthermore, the narrative missed the critical "Quần Tỷ Tranh Tài / Companions fighting for Wealth" interaction caused by a torn branch (Si / 巳 forming Fire frame but also drawn to Metal).
**Action Items**:
- **Missing Elements**: Add logic in `analysis.py` to compile elements not present in Stems or Branches (Main/Middle Qi). Report this clearly in Markdown (`report.py`).
- **Narrative Update**: In `generate_narrative()`, detect if `Missing Element` equals `Officer / Power (Quan Sát)`. If so, add narrative notes: "Missing Officer signifies freedom, rejection of strict hierarchy/control".
- **Interaction Conflicts**: In `branch_interactions.py` or narrative generation, detect if a single branch is involved in BOTH a Bi-Jie (Companion) frame and a Cai (Wealth) combination. Flag this as "Quần Tỷ Tranh Tài" (Companions fighting for wealth), adding a strong warning about financial/partnership risks to the Narrative segment.

---
**Execution Order:**
1. Fix `scoring.py` (DM strength bugs and useful god theory improvements).
2. Fix `structure.py` (Month branch prioritizing).
3. Fix `stem_transformations.py` (Jealous override).
4. Update `analysis.py` & `report.py` & `narrative.py` (missing elements and complex conflicts like Quần Tỷ Tranh Tài).
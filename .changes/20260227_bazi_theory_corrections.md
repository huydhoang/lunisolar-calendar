# Bazi Theory Corrections (2026-02-27)

Addresses eight theoretical inaccuracies identified in `contexts/0001_review_bazi_python.md`.

---

## 1. Day Master Strength — Five Seasons (Vượng Tướng Hưu Tù Tử)

**File:** `lunisolar-python/bazi.py`

**Problem:** `score_day_master` used the 12 Longevity Stage index to determine Month Command strength. Yin stems traverse the cycle in reverse, so e.g. Yi (乙) Wood in Hai (亥) Water would hit stage 8 (Death) and lose points, even though Water produces Wood (Tướng = Strong).

**Fix:** Added `get_seasonal_strength(dm_elem, month_elem)` which uses the Five Elemental Seasons table:

| Relationship | Score | Name |
|---|---|---|
| month == DM element | +2 | Vượng (Prosperous) |
| month produces DM | +2 | Tướng (Strong) |
| DM produces month | -1 | Hưu (Resting) |
| DM controls month | -1 | Tù (Trapped) |
| month controls DM | -2 | Tử (Dead) |

`score_day_master` is updated to call this helper instead of `changsheng_stage`. Residual hidden stem scoring (+0.5) was also added.

---

## 2. Heavenly Stem Clashes — Remove Invalid Earth Pairs

**File:** `lunisolar-python/bazi.py`

**Problem:** `STEM_CLASH_PAIRS` included `{戊, 甲}` and `{己, 乙}`. Central Earth stems (戊, 己) have no directional opposition and therefore cannot clash. These relationships are Control/Restriction, not Clash.

**Fix:** Removed both pairs. `STEM_CLASH_PAIRS` now contains only the four valid directional-opposition clashes: 甲-庚, 乙-辛, 丙-壬, 丁-癸.

---

## 3. Punishment Separation — Graceless vs. Bully

**File:** `lunisolar-python/bazi.py`

**Problem:** `BULLY_PUNISH_PAIRS` mixed the Graceless Punishment (无恩之刑, Yin-Si-Shen) group with the Bully Punishment (恃势之刑, Chou-Xu-Wei) group under a single label. This caused incorrect type labels and life-area tags.

**Fix:**
- Renamed `BULLY_PUNISH_PAIRS` to keep only Chou-Xu-Wei (丑-戌-未) pairs.
- Added new `GRACELESS_PUNISH_PAIRS` constant for Yin-Si-Shen (寅-巳-申) pairs.
- `detect_punishments` now emits `"Vô ân chi hình (Graceless)"` with `life_areas: ["betrayal", "ingratitude"]` and `"Ỷ thế chi hình (Bully)"` with `life_areas: ["career", "power struggles"]` separately.

---

## 4. Projection `strength_delta` — Include Earthly Branch Weight

**File:** `lunisolar-python/bazi.py` — `generate_year_projections`, `generate_month_projections`, `generate_day_projections`

**Problem:** The `strength_delta` for each projected period only evaluated the Heavenly Stem's element, ignoring the Earthly Branch (Tai Sui/Root), which carries 60-70% of a year's energy in Zi Ping theory.

**Fix:** Each projection's delta now computes both contributions:
- Stem influence: ±1 point
- Branch influence (Root): ±2 points (heavier weight)

Favorable (DM same element or produced by) adds points; unfavorable (DM controlled or producing season) subtracts points.

---

## 5. Structure Detection — Protrusion (透出 / Thấu Xuất)

**File:** `lunisolar-python/bazi.py` — `detect_month_pillar_structure`

**Problem:** The function always used the Month Branch's Main Qi (first hidden stem) to define the structure, regardless of whether that stem appeared on any Heavenly Stem. Proper Zi Ping theory requires protrusion (透出): a structure is anchored only if the hidden stem appears on the Year, Month, or Hour pillar's Heavenly Stem.

**Fix:** The function now:
1. Collects protruding stems from Year, Month, and Hour pillars.
2. Checks Month hidden stems in order (Main → Middle → Residual) for a match.
3. Returns the Ten-God of the first protruding hidden stem found.
4. Falls back to Main Qi only if no hidden stem protrudes.

---

## 6. Structure Quality — Seven Killings Controlled

**File:** `lunisolar-python/bazi.py` — `_assess_structure_quality`

**Problem:** For 正官/七杀 structures, the code returned "官杀有制" (Killings Controlled) simply when the Day Master was Strong or Balanced. Endurance is not control — "Controlled" requires a Food God (食神) or Hurting Officer (伤官) to restrain the Seven Killings.

**Fix:**
- Now checks `dist.get("食神", 0) > 0 or dist.get("伤官", 0) > 0` for actual control.
- Returns `"七杀有制, 格局清纯"` only when Seven Killings are present **and** controlled.
- Returns `"身杀两停"` (Balanced Master and Killer) when DM is strong/balanced but no controller exists.

---

## 7. Transformation Conditions — Relax Month Support

**File:** `lunisolar-python/bazi.py` — `detect_transformations`

**Problem:** `month_support` required the Month Branch's native element to exactly equal the transformation target. This rejected valid transformations where the month *produces* the target (e.g., Wood month supporting a Fire transformation).

**Fix:**
```python
month_support = (month_elem == target) or (GEN_MAP.get(month_elem) == target)
```

---

## 8. Half Three Combinations (半三合 / Bán Tam Hợp)

**File:** `lunisolar-python/bazi.py`

**Problem:** `detect_branch_interactions` only detected full three-branch San He combinations. Half-Combinations (two of three branches, especially Cardinal-branch pairs like 申-子, 子-辰) are common and carry significant elemental influence.

**Fix:**
- Added `BAN_SAN_HE` constant (8 pairs covering all four elemental half-combinations).
- `detect_branch_interactions` now returns a `"半三合"` key in its result dict.
- Half-combinations are only reported when the corresponding full San He is **not** already present.

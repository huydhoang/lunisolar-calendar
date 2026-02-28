# Bazi Enhanced Report - 2026-02-25

## Summary

Enhanced the `bazi.py` main function to produce a comprehensive Bazi chart report with all available data from the spec documents, and added three new projection views (10-year, 36-month, 100-day lookahead).

---

## Files Modified

### `lunisolar-python/bazi.py`

---

## Added Features

### 1. Void Branches (空亡) Detection

**New Constants:**
- `VOID_BRANCH_TABLE: Dict[int, Tuple[str, str]]` - Maps Xun index to void branch pairs
- `XUN_NAMES: Dict[int, str]` - Chinese names for each Xun (甲子旬, 甲戌旬, etc.)

**New Functions:**
- `void_branches(day_cycle: int) -> Tuple[str, str]` - Returns void branches for a day pillar cycle
- `xun_name(day_cycle: int) -> str` - Returns the Xun name for a day cycle
- `void_in_pillars(chart: Dict) -> Dict[str, bool]` - Checks which natal pillars have void branches

---

### 2. Symbolic Stars (神煞) Detection

**New Constants:**
- `NOBLEMAN_TABLE: Dict[str, List[str]]` - 天乙贵人 lookup by stem
- `ACADEMIC_STAR_TABLE: Dict[str, str]` - 文昌 lookup by stem
- `PEACH_BLOSSOM_TABLE: Dict[str, str]` - 桃花 lookup by branch
- `TRAVEL_HORSE_TABLE: Dict[str, str]` - 驿马 lookup by branch
- `GENERAL_STAR_TABLE: Dict[str, str]` - 将星 lookup by branch
- `CANOPY_STAR_TABLE: Dict[str, str]` - 华盖 lookup by branch
- `GOAT_BLADE_TABLE: Dict[str, str]` - 羊刃 lookup by stem
- `PROSPERITY_STAR_TABLE: Dict[str, str]` - 禄神 lookup by stem
- `RED_CLOUD_TABLE: Dict[str, str]` - 红鸾 lookup by branch
- `BLOOD_KNIFE_TABLE: Dict[str, str]` - 血刃 lookup by branch

**New Function:**
- `detect_symbolic_stars(chart: Dict) -> List[Dict]` - Detects all symbolic stars in the natal chart with nature (auspicious/inauspicious/mixed), location, and description

---

### 3. Time Projection Functions

**New Functions:**
- `get_year_cycle_for_gregorian(year: int) -> int` - Get sexagenary cycle for a Gregorian year
- `get_month_cycle_for_date(solar_date: str, solar_time: str) -> int` - Get month pillar cycle
- `get_day_cycle_for_date(solar_date: str, solar_time: str) -> int` - Get day pillar cycle
- `generate_year_projections(chart: Dict, start_year: int, count: int) -> List[Dict]` - Generate year-by-year projections with interactions, life stage, ten-god, strength delta
- `generate_month_projections(chart: Dict, start_date: date, count: int) -> List[Dict]` - Generate month-by-month projections
- `generate_day_projections(chart: Dict, start_date: date, count: int) -> List[Dict]` - Generate day-by-day projections

---

### 4. Enhanced Main Function Output

The main function now produces a comprehensive report including:

**New Sections:**
1. **Birth Data Header** - Shows solar date, time, gender, and lunar date info
2. **Day Master Enhanced** - Now includes Xun (旬) and Void branches (空亡)
3. **Four Pillars Table** - Enhanced with:
   - Na Yin (納音) Chinese name
   - Life Stage with Chinese/English/Vietnamese
   - Void branch markers `[VOID]`
4. **Hidden Stems with Ten-Gods** - Shows each hidden stem's Ten-God relationship
5. **Favorable/Avoid Elements** - Added to Chart Structure section
6. **Stem Combinations (天干合)** - Shows combination pairs and target elements
7. **Transformations (合化)** - Shows transformation status with confidence %
8. **Punishments & Harms (刑害)** - Shows type, branches, and affected life areas
9. **Symbolic Stars (神煞)** - Full detection with icons:
   - ✦ auspicious
   - ⚠ inauspicious  
   - ◆ mixed
10. **Na Yin Interactions (納音)** - Shows pillar Na Yin and relation to Day Master
11. **Life Stages Detail (十二长生)** - Full CN/EN/VI with strength class
12. **Enhanced Luck Pillars** - Now includes Ten-God and Na Yin per pillar

---

### 5. Three New Projection Views

**[ 10-Year Lookahead (十年展望) ]**
- Year-by-year table showing:
  - Year, GanZhi, Ten-God, Life Stage, Interactions, Strength Delta (Δ)

**[ 36-Month Lookahead (三十六月展望) ]**
- Month-by-month projections showing:
  - Month number, Date, GanZhi, Ten-God, Interactions, Strength Delta

**[ 100-Day Lookahead (百日展望) ]**
- Day-by-day projections (filtered to notable days only):
  - Date, Weekday, GanZhi, Ten-God, Interactions, Strength Delta
  - Only shows days with interactions or non-zero strength delta

---

## Imports Added

```python
from datetime import timedelta  # Added for day projections
```

---

## Bug Fixes

- Fixed `max()` call in `classify_structure_professional()` to use proper lambda syntax:
  - Before: `max(dist, key=dist.get)` (caused type inference issues)
  - After: `max(dist, key=lambda k: dist[k])`

---

## Removed/Deprecated

None. All existing functionality preserved and enhanced.

---

## Spec Compliance

This update implements data from:
- `specs/bazi-analysis-framework.md` - Section 9 (Symbolic Stars), Section 8 (Branch Interactions)
- `specs/bazi-target-data-schema.md`:
  - Section IX (Void Branches) - Fully implemented
  - Section X (Symbolic Stars) - Core stars implemented
  - Section XI (Luck Pillars) - Enhanced with Ten-God and Na Yin
  - Section XII (Annual/Date Comparison Engine) - Projection views added

---

## Usage

```bash
python bazi.py -d YYYY-MM-DD -t HH:MM -g <male|female>
```

Example:
```bash
python bazi.py -d 1990-03-15 -t 14:30 -g male
```

---

## Output Structure

```text
======================================================================
  BAZI (四柱八字) COMPREHENSIVE CHART REPORT
======================================================================

  Birth Data: ...
  
----------------------------------------------------------------------
[ Day Master (日元) ]
  ...
  
----------------------------------------------------------------------
[ Four Pillars (四柱) ]
  ...
  
----------------------------------------------------------------------
[ Chart Structure (格局) ]
  ...
  
----------------------------------------------------------------------
[ Ten-God Distribution (十神分布) ]
  ...
  
----------------------------------------------------------------------
[ Branch Interactions (地支关系) ]
  ...
  
----------------------------------------------------------------------
[ Symbolic Stars (神煞) ]
  ...
  
----------------------------------------------------------------------
[ Na Yin Interactions (納音) ]
  ...
  
----------------------------------------------------------------------
[ Life Stages Detail (十二长生) ]
  ...
  
----------------------------------------------------------------------
[ Luck Pillars (大运) ]
  ...
  
----------------------------------------------------------------------
[ Chart Rating (综合评分) ]
  ...
  
----------------------------------------------------------------------
[ Narrative Interpretation (命理解读) ]
  ...
  
======================================================================
  PROJECTION VIEWS (运程展望)
======================================================================

----------------------------------------------------------------------
[ 10-Year Lookahead (十年展望) ]
  ...

----------------------------------------------------------------------
[ 36-Month Lookahead (三十六月展望) ]
  ...

----------------------------------------------------------------------
[ 100-Day Lookahead (百日展望) ]
  ...

======================================================================
```

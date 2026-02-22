# Lunisolar Calendar Algorithm Documentation

This document explains the correct algorithm for lunisolar calendar calculations and documents critical bug fixes to prevent future mistakes.

## Table of Contents

1. [Algorithm Overview](#algorithm-overview)
2. [Critical Bug Fix: Principal Term Index Mapping](#critical-bug-fix-principal-term-index-mapping)
3. [Month Numbering Algorithm](#month-numbering-algorithm)
4. [Testing Verification Cases](#testing-verification-cases)

---

## Algorithm Overview

The lunisolar calendar calculation follows these steps:

1. **Load Astronomical Data**: Get new moons and solar terms from pre-computed JSON files
2. **Build Month Periods**: Create lunar month boundaries between successive new moons
3. **Tag Principal Terms**: Map each of the 12 principal solar terms to their corresponding lunar months
4. **Find Zi Month (子月)**: Locate the 11th lunar month that contains the Winter Solstice (Z11)
5. **Assign Month Numbers**: Number all months starting from Zi month using a forward-only pass
6. **Resolve Target Date**: Find which lunar month period contains the target date

---

## Critical Bug Fix: Principal Term Index Mapping

### The Bug (Fixed 2025-10-10)

**Problem**: Solar term index to principal term number conversion was incorrect, causing all lunar months to be off by 1.

### Data Structure

Solar terms are stored in JSON files as arrays of `[timestamp, index]` pairs:
- Index ranges from 0 to 23 (representing the 24 solar terms)
- Even indices (0, 2, 4, ..., 22) are **principal terms** (中氣 zhōngqì)
- Odd indices (1, 3, 5, ..., 23) are **sectional terms** (節氣 jiéqì)

### Principal Term Mapping

Principal terms correspond to specific solar longitudes (multiples of 30°):

| Index | Solar Longitude | Term Name | Term Number | Chinese Name |
|-------|----------------|-----------|-------------|--------------|
| 0     | 0°             | Z2        | 2           | 春分 Spring Equinox |
| 2     | 30°            | Z3        | 3           | 穀雨 Grain Rain |
| 4     | 60°            | Z4        | 4           | 小滿 Grain Full |
| 6     | 90°            | Z5        | 5           | 夏至 Summer Solstice |
| 8     | 120°           | Z6        | 6           | 大暑 Great Heat |
| 10    | 150°           | Z7        | 7           | 處暑 Limit of Heat |
| 12    | 180°           | Z8        | 8           | 秋分 Autumnal Equinox |
| 14    | 210°           | Z9        | 9           | 霜降 Descent of Frost |
| 16    | 240°           | Z10       | 10          | 小雪 Slight Snow |
| 18    | 270°           | **Z11**   | **11**      | **冬至 Winter Solstice** |
| 20    | 300°           | Z12       | 12          | 大寒 Great Cold |
| 22    | 330°           | Z1        | 1           | 雨水 Rain Water |

### The Formula

#### ❌ Incorrect Formula (Bug)
```typescript
const termIndexRaw = Math.floor(idx / 2) + 1;
const termIndex = termIndexRaw > 12 ? termIndexRaw - 12 : termIndexRaw;
```

**Problem**: This gives `idx 18 → termIndex 10` instead of 11 (Winter Solstice)

#### ✅ Correct Formula (Fixed)
```typescript
const termIndexRaw = (idx / 2) + 2;
const termIndex = termIndexRaw > 12 ? termIndexRaw - 12 : termIndexRaw;
```

**Explanation**: 
- `idx / 2` converts from 24-term index to principal term sequence (0, 1, 2, ..., 11)
- `+ 2` shifts to match the Z-numbering which starts at Z2 (Spring Equinox at 0°)
- Wrapping handles Z1 (Rain Water at 330°) which comes after Z12

### Verification Examples

```typescript
// Index 0 (0°) → Z2 Spring Equinox
(0 / 2) + 2 = 2 ✓

// Index 18 (270°) → Z11 Winter Solstice (CRITICAL)
(18 / 2) + 2 = 11 ✓

// Index 20 (300°) → Z12 Great Cold
(20 / 2) + 2 = 12 ✓

// Index 22 (330°) → Z1 Rain Water (wraps)
(22 / 2) + 2 = 13 → 13 - 12 = 1 ✓
```

### Impact of the Bug

Before the fix, the Winter Solstice was incorrectly mapped to termIndex 10 instead of 11. This caused:
- The Zi month (子月) to be misidentified
- All subsequent lunar month numbers to be off by 1
- Dates like 2025-10-08 showing lunar month 7 instead of 8
- Dates like 2025-08-23 showing lunar month 6 instead of 7

---

## Month Numbering Algorithm

### Core Principle

The lunisolar calendar uses the **no-zhongqi rule (無中氣法)**:
1. Find the Zi month (子月, month 11) containing the Winter Solstice
2. Number all other months sequentially from this anchor
3. Any month without a principal term becomes a leap month, taking the **preceding** month's number

### Implementation: Forward-Only Pass

```typescript
// 1. Find Zi month containing Winter Solstice
const ziIndex = periods.findIndex(p => 
  p.startUtc <= anchorSolstice && anchorSolstice < p.endUtc
);
periods[ziIndex].monthNumber = 11;

// 2. Forward pass from Zi month
let current = 11;
for (let i = ziIndex + 1; i < periods.length; i++) {
  if (periods[i].hasPrincipal) {
    // Regular month: increment
    current = (current % 12) + 1;
    periods[i].monthNumber = current;
    periods[i].isLeap = false;
  } else {
    // Leap month: takes PRECEDING month number
    periods[i].monthNumber = current;
    periods[i].isLeap = true;
  }
}
```

### Why Forward-Only Works

The calculation window is designed to start from the Winter Solstice anchor:
- For a target date like 2025-10-08, the window includes data from ~2024-11-21 to ~2026-01-21
- This ensures the Zi month (containing Winter Solstice) is always at or near index 0
- No backward pass is needed because there are no periods before the anchor

### Critical: Leap Month Takes PRECEDING Number

```typescript
// CORRECT: Leap month after month 6
Month 6 (regular, has principal term)
Month 6 (leap, no principal term) ✓
Month 7 (regular, has principal term)

// INCORRECT: Would be wrong
Month 6 (regular, has principal term)
Month 7 (leap, no principal term) ✗
Month 7 (regular, has principal term)
```

### The Backward Pass Bug (Now Removed)

The original code had a backward pass for months before Zi month. It contained a bug:

```typescript
// BUGGY CODE (removed):
for (let i = ziIndex - 1; i >= 0; i--) {
  current = current > 1 ? current - 1 : 12;
  if (!periods[i].hasPrincipal) {
    // BUG: Assigned FOLLOWING month number instead of PRECEDING
    const nextNum = (current % 12) + 1;
    periods[i].monthNumber = nextNum;  // WRONG!
  }
}
```

This bug was never triggered in practice because the windowing strategy ensures no periods exist before Zi month.

---

## Testing Verification Cases

### Test Case 1: 2025-10-08 12:00 Asia/Ho_Chi_Minh

**Expected**: Lunar month 8

**Verification**:
- Winter Solstice 2024-12-21 (Z11) at index 18 of 2024 solar terms
- termIndex = (18 / 2) + 2 = 11 ✓
- Zi month correctly identified
- Forward counting reaches month 8 by 2025-10-08 ✓

### Test Case 2: 2025-08-23 12:00 Asia/Ho_Chi_Minh

**Expected**: Lunar month 7

**Verification**:
- Period 2025-07-25 to 2025-08-23: Leap month 6 (no principal term)
- Period 2025-08-23 to 2025-09-22: Regular month 7 (has principal term) ✓

### Test Case 3: 2025-08-22 12:00 Asia/Ho_Chi_Minh

**Expected**: Leap month 6

**Verification**:
- Falls in period 2025-07-25 to 2025-08-23
- This period has no principal term
- Takes preceding month number: 6 ✓
- Is marked as leap: true ✓

---

## Key Takeaways

1. **Principal term index formula**: Always use `(idx / 2) + 2` with wrapping
2. **Winter Solstice is critical**: Index 18 must map to termIndex 11
3. **Leap months take PRECEDING number**: Not following
4. **Forward-only pass is sufficient**: No backward pass needed with proper windowing
5. **Test with real dates**: Verify with known cases like 2025 leap month 6

---

## References

- [`docs/lunisolar_calendar_rules.md`](../../docs/lunisolar_calendar_rules.md) - Complete calendar rules
- [`docs/debug/month_numbering.md`](../../docs/debug/month_numbering.md) - Original bug analysis
- [`data/lunisolar_v2.py`](../../data/lunisolar_v2.py) - Python reference implementation
- [`pkg/src/core/LunisolarCalendar.ts`](../src/core/LunisolarCalendar.ts) - TypeScript implementation

---

**Last Updated**: 2025-10-10  
**Bug Fix**: Principal term index mapping corrected
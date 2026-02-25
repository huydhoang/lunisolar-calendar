# Changes to bazi.py - Hurt Officer (伤官格) Structure Fix

**Date:** 2026-02-26

## Summary

Added proper support for 伤官格 (Hurt Officer Structure) detection and analysis, which was incorrectly classified as 从强格 or 建禄格.

## Modifications

### 1. New Function: `detect_hurt_officer_structure()`
**Location:** Lines 2122-2160 (approx)

Added a new function to detect if the chart should be classified as 伤官格:
- Checks if month branch's hidden stems contain Wood element (伤官)
- Checks if 伤官+食神 has significant presence (≥35%) in weighted Ten-God distribution
- Returns True if structure should be 伤官格

### 2. Updated `classify_structure()` Function
**Location:** Lines 2162-2186

Added call to `detect_hurt_officer_structure()` at the start to override other structure classifications when 伤官格 is detected.

### 3. Updated `classify_structure_professional()` Function
**Location:** Lines 2260-2270

Added early return for 伤官格 with dominance score.

### 4. Updated `score_day_master()` Function
**Location:** Lines 1343-1348

Added special handling for 伤官格:
- When detected and score >= 2, returns strength as "身旺伤旺" (Body Strong - Output Strong)
- This reflects the traditional analysis where Day Master has roots but is drained by Earth trio

### 5. Updated `recommend_useful_god()` Function
**Location:** Lines 2520-2555

Added special elemental recommendations for 伤官格:
- **Dụng Thần (Useful God):** Wood (Mộc) - to control Earth
- **Hỷ Thần (Joyful God):** Fire (Hỏa) - to support Day Master
- **Avoid:** Fire (traditional view - to prevent overexertion)

### 6. Updated CLI Output
**Location:** Lines 2767-2772

Added display of Dụng Thần and Hỷ Thần when 伤官格 is detected.

### 7. Updated `generate_narrative()` Function
**Location:** Lines 2625-2703

Added comprehensive Hurt Officer analysis section with:
- Career advice (creative fields, autonomy, restraint of speech)
- Relationship advice for female charts (Officer = husband, late marriage recommendation)
- Elemental remedy (Wood energy to control Earth)

## Why These Changes

According to the traditional Bazi theory from Zi Ping Zhen Quan:
- 伤官格 is determined by the month's branch and Ten-God distribution
- The previous algorithm incorrectly labeled this chart as 从强格 (Follow Strong) because 比肩 had highest score
- For 丙火 (Fire) Day Master in 丑月 (Earth month) with 己土 (Earth) prominent, the correct structure is 伤官格
- The Useful God must be Wood to control the overwhelming Earth energy

## References

- Classical text: Zi Ping Zhen Quan (子平真诠)
- "八字用神，专求月令" - Useful God is derived from month decree
- 伤官喜佩印以制伏 - Hurt Officer likes Seal to control it

# Bazi Module Completeness Evaluation

**Date:** 2026-02-28  
**Scope:** `lunisolar-python/bazi/` package  
**Evaluated against:** Bazi theory, Na Yin, Heavenly Stem Combinations & Transformation conditions,
Tai Xuan Numbers, He Tu, Luo Shu, Ba Gua, I Ching / Da Yan Zhi Shu

---

## 1. Bazi (八字) — Core Four Pillars System

### ✅ Implemented

| Component | Module | Status |
|---|---|---|
| Four Pillars (year/month/day/hour stems & branches) | `core.py` | Complete — `build_chart()`, `from_solar_date()` |
| Heavenly Stems + Five Elements | `constants.py` | Complete — `STEM_ELEMENT`, `STEM_POLARITY` |
| Ten Gods (十神) | `ten_gods.py` | Complete — `ten_god()`, weighted distribution |
| Hidden Stems / Stored Qi (藏干) | `hidden_stems.py` + `constants.py` | Complete — 3 roles: main / middle / residual |
| Twelve Growth Stages (十二长生) | `longevity.py` | Complete — forward/reverse per stem polarity |
| Day Master strength scoring | `scoring.py` | Complete — seasonal score + root depth + exposed stems |
| Useful God (用神) recommendation | `scoring.py` | Basic — derived from strong/weak/balanced assessment |
| Luck Pillars / Da Yun (大运) | `luck_pillars.py` | Complete — 3-day rule, forward/reverse by year stem polarity & gender |
| Annual Flow / Liu Nian (流年) | `annual_flow.py` | Basic — Ten God, clash/combine/harm, strength delta |
| Chart Structure / Ge Ju (格局) | `structure.py` | 8 standard structures + special structure stub |
| Symbolic Stars / Shen Sha (神煞) | `symbolic_stars.py` | 11 stars: Nobleman, Academic, Peach Blossom, Red Cloud, Travel Horse, General, Canopy, Goat Blade, Prosperity, Blood Knife, Void |

### ⚠️ Missing or Incomplete

- **Follower / Transformation structures** (`detect_special_structures` returns `None` — stub only): No real algorithm for Cong Cai Ge, Cong Sha Ge, Cong Shang Guan Ge, Cong Wang Ge, or Hua Ge.
- **San He in annual flow**: `annual_flow.py` checks only pairwise clash/combine/harm; no three-combination or half-three-combination detection against the natal chart.
- **Ten God weighting**: Hour and Year pillars both use weight=2. Many schools treat the Hour pillar as weaker than the Month and Day pillars.
- **Dynamic Void (空亡 in luck pillars / annual flow)**: Void branches are only assessed against Day pillar of the natal chart; no dynamic void calculation for luck pillars or annual flow years.

---

## 2. Na Yin (納音)

### ✅ Implemented

- Full 60-cycle Na Yin table loaded from CSV — Chinese, Vietnamese, English names, and Five Element.
- `analyze_nayin_interactions()`: computes Five-Element relationships between Na Yin of adjacent pillars (Year→Month→Day→Hour) and against the Day Master.
- Integrated into `build_chart()` and `analyze_time_range()` — every pillar carries a `nayin` field.

### ⚠️ Missing per Classical Theory

- **Na Yin special interaction rules**: currently uses generic `_element_relation()` (raw Five-Element relation only). Classical Na Yin theory has specific combination rules beyond simple generation/control (e.g. Na Yin Metal entering Fire = inauspicious "Metal smelted" — 金入火熔, 论凶).
- **Global Na Yin balance assessment (四柱納音推局)**: no calculation of overall harmony or opposition across all four pillars' Na Yin elements.
- **Na Yin-based Growth Stage**: some schools use the Na Yin element (not the Day Stem element) to derive the Twelve Growth Stages; this branch is not implemented.

---

## 3. Heavenly Stem Five Combinations & Transformation Conditions (天干合化)

### ✅ Implemented — Largely Correct

`stem_transformations.py` correctly encodes all five pairs and transformation elements:

```
Jia+Ji → Earth    Yi+Geng → Metal    Bing+Xin → Water
Ding+Ren → Wood   Wu+Gui  → Fire
```

Transformation success conditions check all four classical factors:

| Condition | Code | Theory-correct? |
|---|---|---|
| Adjacency (stems in neighboring pillars) | `proximity_score` = 2 if adjacent | ✅ |
| Month command support | `month_elem == target` | ✅ (bug fixed in prior refactor) |
| Leading element present (rooted in chart) | `leading` — checks exposed stems & hidden stems | ✅ |
| Not obstructed by intervening stem | `check_obstruction()` — middle stem controls one side | ✅ |
| Not severely clashed | `check_severe_clash()` | ✅ |

### ⚠️ Missing

- **Combination with luck pillar / annual flow stem**: `analyze_time_range()` only detects pairing via `STEM_TRANSFORMATIONS` lookup — it does **not** call the full `detect_transformations()` with all conditions when an external stem (from luck pillar or annual year) is involved.
- **"Bound but not transformed" (合而不化) downstream effects**: The `"Hợp (bound)"` status is returned, but does not propagate to useful god calculation or Day Master strength scoring (a bound stem should lose its independent function).
- **"Useful God itself being bound" rule**: If the useful god stem is being held in combination by another stem, it loses efficacy. This interaction logic is absent.

---

## 4. Tai Xuan Numbers (太玄數)

### ❌ Not Implemented

No implementation or reference exists for:
- Yang numbers (1, 3, 5, 7, 9) / Yin numbers (2, 4, 6, 8, 10) per Tai Xuan
- Nine Palace Flying Stars integration
- Feng Shui Na Jia numerical system

---

## 5. He Tu (河圖) — Yellow River Diagram

### ❌ Not Implemented

No implementation exists for:
- He Tu number pairs (1↔6 Water, 2↔7 Fire, 3↔8 Wood, 4↔9 Metal, 5↔10 Earth)
- Application to stem-branch pair analysis (stems sharing a He Tu number = special generative combination)
- He Tu elemental structure in chart interpretation

---

## 6. Luo Shu (洛書) — Lo Shu Magic Square

### ❌ Not Implemented

No implementation exists for:
- The 3×3 Lo Shu magic square (center 5, numbers 1–9)
- Nine Palace (九宮) spatial assignments
- Flying Stars Xuan Kong (玄空飛星) derived from Luo Shu
- Annual / monthly palace flying calculations

---

## 7. Ba Gua (八卦) & I Ching (易經)

### ❌ Not Implemented

No implementation exists for:
- Mapping of stems/branches to trigrams (Qian/Kan/Gen/Zhen/Xun/Li/Kun/Dui)
- Later Heaven (Hòa Thiên / 後天) or Earlier Heaven (Tiên Thiên / 先天) Ba Gua arrangements
- Sixty-four hexagrams (六十四卦)
- **Da Yan Zhi Shu (大衍之數)**: the number 50 (→ 49 yarrow stalks used), Five-Element multiplication, application to fate calculation via I Ching method
- Na Jia (納甲): mapping of six lines (六爻) onto the sexagenary cycle
- Six Relatives (六亲) per I Ching divination structure

---

## Summary

| System | Completeness | Notes |
|---|---|---|
| **Core Bazi / Four Pillars** | 85% | Missing real Follower/Transformation structures, dynamic Void |
| **Na Yin** | 60% | Table complete; interaction rules are too coarse |
| **Heavenly Stem Combinations + Transformation conditions** | 80% | Strong natal logic; weak for external stems (luck/annual), no downstream dụng thần effects |
| **Tai Xuan Numbers** | 0% | Not implemented |
| **He Tu** | 0% | Not implemented |
| **Luo Shu** | 0% | Not implemented |
| **Ba Gua / I Ching** | 0% | Not implemented |
| **Da Yan Zhi Shu** | 0% | Not implemented |

The `bazi/` package is a **pragmatically complete Ten-God / Four-Pillars engine**, covering the computational core that most modern Bazi software uses. However, it has no coverage of numerological-cosmological systems (He Tu, Luo Shu, Ba Gua, I Ching). Those five systems are typically domain-specific to Feng Shui, Qi Men Dun Jia, or Liu Ren rather than pure Four-Pillars analysis — integrating them would require deciding on a specific school and defining clear application methods within Bazi context.

# Bazi Analysis Framework Review (Python Implementation)

From the perspective of a Bazi (Four Pillars of Destiny) master, here is a detailed review of the `bazi.py` module, highlighting inaccuracies in analysis, calculation, and interpretation logic.

While the software architecture is well-structured and clean, the **core Bazi theory layers contain several critical errors** that will lead to incorrect strength assessments, flawed structure (Ge Ju) classification, and inaccurate luck projections.

---

### 1. Fundamental Error in Day Master Strength (Vượng Suy)
In the `score_day_master` function, the code uses the **12 Longevity Stages** to calculate the "Month Command" (seasonal strength) for the Day Master:
```python
    idx, _stage = changsheng_stage(
        HEAVENLY_STEMS.index(dm_stem), EARTHLY_BRANCHES.index(month_branch)
    )
    if idx <= 5:
        score += 2 * month_weight
    else:
        score -= 2 * month_weight
```
**The Inaccuracy:** Applying the Yin Stem reverse longevity cycle to determine elemental strength is a **major error**. 
*Example:* An **Yi (乙) Wood** Day Master born in the month of **Hai (亥) Water**. Water produces Wood, so Yi Wood is in a "Tướng" (Strong/Growth) state. However, according to the reverse Yin longevity cycle, Yi starts at Wu and goes backward, hitting the **Death (Sử/死)** stage at Hai (`idx = 8`). Your code would subtract points (`score -= 2`), incorrectly classifying a supported Day Master as "Weak."
**Correction:** Use the **Vượng - Tướng - Hưu - Tù - Tử** (Five Elemental Seasons) system for strength calculation, not the 12 Longevity Stages.

### 2. Theoretical Error in Heavenly Stem Clashes
In the `STEM_CLASH_PAIRS` definition:
```python
STEM_CLASH_PAIRS = frozenset({
    frozenset({"甲", "庚"}), frozenset({"乙", "辛"}),
    frozenset({"丙", "壬"}), frozenset({"丁", "癸"}),
    frozenset({"戊", "甲"}),  # Error
    frozenset({"己", "乙"}),  # Error
})
```
**The Inaccuracy:** Bazi recognizes only the **Four Stem Clashes** (Jia-Geng, Yi-Xin, Bing-Ren, Ding-Gui). Clashes require directional opposition (East Wood vs. West Metal). Wu (戊) and Ji (己) belong to the Central Earth and **do not clash**. Wu-Jia and Ji-Yi are merely **Control/Restriction** relationships. Including them as "Clashes" will generate false-positive warnings for life events.

### 3. Ignoring Earthly Branches in Projections
In `generate_year_projections` and `generate_month_projections`:
```python
        delta = 0
        yr_elem = STEM_ELEMENT[stem] # Only checks the Stem's element
        if GEN_MAP.get(yr_elem) == dm_elem:
            delta += 1
        if CONTROL_MAP.get(yr_elem) == dm_elem:
            delta -= 1
```
**The Inaccuracy:** When calculating the impact of a Year (Lưu Niên), the code only evaluates the **Heavenly Stem's** element. In Zi Ping Bazi, the **Earthly Branch (Tai Sui)** is the "Root" and carries the decisive energy of the year (usually 60-70% of the weight). Ignoring the Branch's element makes the luck projections highly unreliable.

### 4. Categorization Error in Three Punishments (San Xing)
In `detect_punishments`, `BULLY_PUNISH_PAIRS` (Ỷ Thế Chi Hình) is incorrectly defined:
```python
BULLY_PUNISH_PAIRS = frozenset({
    frozenset({"寅", "巳"}), frozenset({"巳", "申"}), frozenset({"寅", "申"}), # Error
    frozenset({"丑", "戌"}), frozenset({"戌", "未"}), frozenset({"丑", "未"}), # Correct
})
```
**The Inaccuracy:** The pairs (Yin-Si-Shen) belong to the **Graceless Punishment** (Vô Ân Chi Hình) category, whereas (Chou-Xu-Wei) is the **Bully Punishment** (Ỷ Thế Chi Hình). Combining them leads to incorrect nomenclature and faulty narrative interpretations (life_areas).

### 5. Oversimplified Structure (格局) Detection
In `detect_month_pillar_structure`:
```python
    main_hidden_stem = month_hidden[0][1]
    return ten_god(dm_idx, main_hidden_idx)
```
**The Inaccuracy:** The code assumes the "Main Qi" (main hidden stem) of the Month Branch automatically defines the Structure. Proper Zi Ping theory follows the **"Protrusion" (Thấu Xuất)** principle. A structure is only formed if the hidden stems of the month appear on the Heavenly Stems (Year, Month, or Hour pillars). Protrusion determines if a potential structure is "anchored" and powerful.

### 6. Flawed Structure Quality Assessment
In `_assess_structure_quality`:
```python
    if primary_tg in ("正官", "七杀"):
        if strength in ("strong", "balanced"):
            return "官杀有制, 格局清纯", False
```
**The Inaccuracy:** "Guan Sha You Zhi" (Officer/Seven-Killings controlled) means there is a **Food God** or **Hurting Officer** present to restrict the Seven Killings. Simply having a "Strong" Day Master means the Master can "endure" the pressure (Thân Sát Lưỡng Đình), but it does **not** constitute "control" (Chế Phục). The code confuses endurance with control.

### 7. Overly Rigid Transformation (Hóa) Conditions
In `detect_transformations`:
```python
    # Month Command support
    month_support = month_elem == target
```
**The Inaccuracy:** The code requires the Month Branch's element to **match** the transformation target exactly. In reality, any month that **supports** the target element via the production cycle (Sheng) allows for transformation.
*Example:* Wu-Gui (戊癸) transforms into Fire. If the birth month is Yin (寅) Wood, Wood produces Fire, thus supporting the transformation. Your code would return `False` because Wood $\neq$ Fire.

### 8. Missing Half-Combinations (Bán Tam Hợp)
The `detect_branch_interactions` function only checks for full three-branch sets (`SAN_HE`). In practical analysis, **Half-Combinations** (e.g., Shen-Zi or Zi-Chen) are extremely frequent and exert significant influence, especially those involving the "Cardinal" branches (Zi, Wu, Mao, You). Ignoring them misses a vast amount of interaction data.

---

### Recommended Fixes
1.  **Rewrite `score_day_master`** using the "Five Seasons" (Wàng Tướng Xiū Qiú Sǐ) table for elemental strength.
2.  **Remove Wu-Jia and Ji-Yi** from the `STEM_CLASH_PAIRS` set.
3.  **Separate `GRACELESS_PUNISH_PAIRS`** (Yin-Si-Shen) from `BULLY_PUNISH_PAIRS`.
4.  **Incorporate the Earthly Branch elements** into the `strength_delta` calculations for luck projections.
5.  **Update Structure (Ge Gu) logic:** Scan for month hidden stems that appear on the Heavenly Stems to determine the primary structure.

---

# Implementation Details for Recommended Fixes

Below are the detailed implementation steps and code snippets to correct the theoretical inaccuracies in `bazi.py`.

### 1. Correcting Day Master Strength (Vượng Suy) Calculation
Instead of using Longevity Stages, we use the **Vượng - Tướng - Hưu - Tù - Tử** (Five Seasons) system to evaluate the Day Master's seasonal support.

**Step 1:** Add the `get_seasonal_strength` helper function in the `# Day-Master Strength Scoring` section:

```python
def get_seasonal_strength(dm_elem: str, month_elem: str) -> int:
    """Calculate seasonal strength (Vượng Tướng Hưu Tù Tử)."""
    if month_elem == dm_elem:
        return 2  # Vượng (Prosperous)
    if GEN_MAP.get(month_elem) == dm_elem:
        return 2  # Tướng (Strong)
    if GEN_MAP.get(dm_elem) == month_elem:
        return -1 # Hưu (Resting)
    if CONTROL_MAP.get(dm_elem) == month_elem:
        return -1 # Tù (Trapped)
    if CONTROL_MAP.get(month_elem) == dm_elem:
        return -2 # Tử (Dead)
    return 0
```

**Step 2:** Update the `score_day_master` function:

```python
def score_day_master(chart: Dict) -> Tuple[float, str]:
    """Score the Day Master's strength and classify as strong/weak/balanced."""
    dm_stem = chart["day_master"]["stem"]
    dm_elem = chart["day_master"]["element"]
    month_branch = chart["pillars"]["month"]["branch"]
    month_elem = BRANCH_ELEMENT[month_branch]

    score = 0.0
    month_weight = PILLAR_WEIGHTS["month"]

    # 1) Month-order (月令) via Five Seasons (Vượng Tướng Hưu Tù Tử)
    season_score = get_seasonal_strength(dm_elem, month_elem)
    score += season_score * month_weight

    # 2) Root depth (hidden stems matching DM element)
    for pname, p in chart["pillars"].items():
        w = PILLAR_WEIGHTS.get(pname, 1.0)
        for role, stem in p["hidden"]:
            if STEM_ELEMENT[stem] == dm_elem:
                if role == "main":
                    score += 2 * w
                elif role == "middle":
                    score += 1 * w
                elif role == "residual":
                    score += 0.5 * w

    # 3) Visible stem support
    for pname, p in chart["pillars"].items():
        w = PILLAR_WEIGHTS.get(pname, 1.0)
        if STEM_ELEMENT[p["stem"]] == dm_elem:
            score += 1 * w

    # Classification boundaries
    if score >= 6:
        strength = "strong"
    elif score <= -3:
        strength = "weak"
    else:
        strength = "balanced"

    return score, strength
```

### 2. Correcting Heavenly Stem Clashes
Update `STEM_CLASH_PAIRS` to remove the incorrect Earth-based pairs:

```python
# Stem clash pairs (天干冲) — stems 6 positions apart control each other
STEM_CLASH_PAIRS = frozenset(
    {
        frozenset({"甲", "庚"}),
        frozenset({"乙", "辛"}),
        frozenset({"丙", "壬"}),
        frozenset({"丁", "癸"}),
    }
)
```

### 3. Incorporating Earthly Branch Weights in Projections
In projection functions (`generate_year_projections`, etc.), adjust the `delta` calculation to include both stems and branches (giving more weight to the Tai Sui/Branch):

```python
            delta = 0
            elem_stem = STEM_ELEMENT[stem]
            elem_branch = BRANCH_ELEMENT[branch]
            
            # Stem influence
            if GEN_MAP.get(elem_stem) == dm_elem or elem_stem == dm_elem:
                delta += 1
            elif CONTROL_MAP.get(elem_stem) == dm_elem or GEN_MAP.get(dm_elem) == elem_stem:
                delta -= 1
                
            # Branch influence (Tai Sui / Root carries more weight)
            if GEN_MAP.get(elem_branch) == dm_elem or elem_branch == dm_elem:
                delta += 2
            elif CONTROL_MAP.get(elem_branch) == dm_elem or GEN_MAP.get(dm_elem) == elem_branch:
                delta -= 2
```

### 4. Separating Graceless and Bully Punishments
Define `GRACELESS_PUNISH_PAIRS` and update `BULLY_PUNISH_PAIRS`:

```python
GRACELESS_PUNISH_PAIRS = frozenset(
    {
        frozenset({"寅", "巳"}),
        frozenset({"巳", "申"}),
        frozenset({"寅", "申"}),
    }
)

BULLY_PUNISH_PAIRS = frozenset(
    {
        frozenset({"丑", "戌"}),
        frozenset({"戌", "未"}),
        frozenset({"丑", "未"}),
    }
)
```

Update `detect_punishments` to handle the distinct types and life-area tagging.

### 5. Updating Structure Detection (Protrusion / Thấu Xuất)
Replace `detect_month_pillar_structure` with logic that checks for protruding tàng can:

```python
def detect_month_pillar_structure(chart: Dict) -> Optional[str]:
    """Detect structure based on month pillar Ten-God (月令格局) using Protrusion (Thấu Xuất)."""
    month_hidden = chart["pillars"]["month"]["hidden"]
    if not month_hidden:
        return None

    dm_idx = HEAVENLY_STEMS.index(chart["day_master"]["stem"])
    
    # Get all stems in Year, Month, Hour pillars (excluding Day Master)
    protruding_stems = [
        chart["pillars"]["year"]["stem"],
        chart["pillars"]["month"]["stem"],
        chart["pillars"]["hour"]["stem"]
    ]
    
    # Check protrusion in order: Main, Middle, Residual
    for role, hidden_stem in month_hidden:
        if hidden_stem in protruding_stems:
            hidden_idx = HEAVENLY_STEMS.index(hidden_stem)
            return ten_god(dm_idx, hidden_idx)
            
    # Default to Main Qi if none protrude
    main_hidden_stem = month_hidden[0][1]
    main_hidden_idx = HEAVENLY_STEMS.index(main_hidden_stem)
    return ten_god(dm_idx, main_hidden_idx)
```

### 6. Fixing Structure Quality Assessment
Adjust the logic to properly evaluate "Seven Killings Controlled" (Thất Sát Hữu Chế):

```python
    if primary_tg in ("正官", "七杀"):
        has_control = dist.get("食神", 0) > 0 or dist.get("伤官", 0) > 0
        if primary_tg == "七杀" and has_control:
            return "Seven Killings Controlled (Auspicious)", False
        elif strength in ("strong", "balanced"):
            return "Balanced Master and Killer", False
        else:
            return "Killer Overpowering Master (Broken)", True
```

### 7. Relaxing Transformation Conditions
Allow transformation if the month branch supports the target element via production (Sheng):

```python
            # Month Command support (Similarity or Production)
            month_support = (month_elem == target) or (GEN_MAP.get(month_elem) == target)
```

### 8. Adding Half-Combinations (Bán Tam Hợp)
Define `BAN_SAN_HE` and include it in `detect_branch_interactions`:

```python
# §8.2 Half Three Combinations (半三合)
BAN_SAN_HE = frozenset(
    {
        # Water
        frozenset({"申", "子"}), frozenset({"子", "辰"}),
        # Fire
        frozenset({"寅", "午"}), frozenset({"午", "戌"}),
        # Wood
        frozenset({"亥", "卯"}), frozenset({"卯", "未"}),
        # Metal
        frozenset({"巳", "酉"}), frozenset({"酉", "丑"}),
    }
)
```


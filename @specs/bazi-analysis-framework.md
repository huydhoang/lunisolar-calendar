# Bazi Analysis Framework (八字分析框架)

> **Scope**: This specification defines the subsystems of Bazi (Four Pillars of
> Destiny) analysis that build on top of the lunisolar calendar and GanZhi
> (Stem-Branch) engine already implemented in this project. The existing system
> accurately produces the Four Pillars (year, month, day, hour) with their
> Heavenly Stems and Earthly Branches using precise Solar Term boundaries.
> This document covers the additional layers—Ten Gods, Hidden Stems, Longevity
> Stages, Luck Pillars, and supporting concepts—needed for a complete Bazi
> analysis framework.

---

## Table of Contents

1. [Ten Gods (十神)](#1-ten-gods-十神)
2. [Hidden Stems (藏干)](#2-hidden-stems-藏干)
3. [Twelve Longevity Stages (十二长生)](#3-twelve-longevity-stages-十二长生)
4. [Solar Terms in Bazi Context (节气)](#4-solar-terms-in-bazi-context-节气)
5. [Luck Pillars (大运)](#5-luck-pillars-大运)
6. [Annual Pillars (流年)](#6-annual-pillars-流年)
7. [Chart Structures (格局)](#7-chart-structures-格局)
8. [Branch Interactions (合冲刑害)](#8-branch-interactions-合冲刑害)
9. [Symbolic Stars (神煞)](#9-symbolic-stars-神煞)
10. [Favorable & Unfavorable Elements (用神体系)](#10-favorable--unfavorable-elements-用神体系)
11. [Analysis Flowchart](#11-analysis-flowchart)

---

## 1. Ten Gods (十神)

The **Ten Gods** (十神, Shí Shén) describe the relationship between each element
in the chart and the **Day Master** (日主, Rì Zhǔ)—the Heavenly Stem of the day
pillar, which represents the self. Every other stem in the chart (and in Hidden
Stems) maps to one of ten archetypes based on two factors:

1. **Element relationship** — the Five-Element cycle (producing, controlling,
   same, produced-by, controlled-by)
2. **Polarity match** — whether the stem shares the Day Master's Yin/Yang
   polarity (same → 偏/indirect) or differs (opposite → 正/direct)

### 1.1 Relationship Table

The convention follows the standard rule: **正 (Zhèng / Direct)** = opposite
polarity to Day Master; **偏 (Piān / Indirect)** = same polarity as Day Master.

| Element Relationship | Same Polarity (偏) | Opposite Polarity (正) |
|---|---|---|
| **Same element** | 比肩 (Bǐ Jiān) — Friend | 劫财 (Jié Cái) — Rob Wealth |
| **Element I produce** | 食神 (Shí Shén) — Eating God | 伤官 (Shāng Guān) — Hurting Officer |
| **Element I control** | 偏财 (Piān Cái) — Indirect Wealth | 正财 (Zhèng Cái) — Direct Wealth |
| **Element that controls me** | 七杀 (Qī Shā) — Seven Killings | 正官 (Zhèng Guān) — Direct Officer |
| **Element that produces me** | 偏印 (Piān Yìn) — Indirect Resource | 正印 (Zhèng Yìn) — Direct Resource |

### 1.2 Detailed Meanings

#### 比肩 (Bǐ Jiān) — Friend / Companion

- **Polarity**: Same element, same polarity as Day Master
- **Represents**: Siblings, peers, friends, self-reliance, competition
- **Positive**: Independence, cooperation, teamwork, loyalty
- **Negative**: Stubbornness, excessive competition, financial drain from peers

#### 劫财 (Jié Cái) — Rob Wealth / Competitor

- **Polarity**: Same element, opposite polarity to Day Master
- **Represents**: Rivals, risk-taking, younger siblings
- **Positive**: Courage, action-oriented, adventurous spirit
- **Negative**: Impulsiveness, financial losses, conflicts over resources

#### 食神 (Shí Shén) — Eating God / Output

- **Polarity**: Element produced by Day Master, same polarity
- **Represents**: Creativity, expression, enjoyment, food, children (for women)
- **Positive**: Artistic talent, generosity, easy-going nature, good fortune
- **Negative**: Laziness, overindulgence, lack of discipline

#### 伤官 (Shāng Guān) — Hurting Officer / Unconventional Talent

- **Polarity**: Element produced by Day Master, opposite polarity
- **Represents**: Intelligence, rebellion, unconventional thinking
- **Positive**: Brilliant creativity, innovation, eloquence, independence
- **Negative**: Arrogance, rebelliousness, criticism of authority, relationship friction

#### 偏财 (Piān Cái) — Indirect Wealth / Unexpected Wealth

- **Polarity**: Element controlled by Day Master, same polarity
- **Represents**: Business income, investments, father (for men), speculative gains
- **Positive**: Business acumen, generosity, social skills
- **Negative**: Gambling tendencies, financial instability

#### 正财 (Zhèng Cái) — Direct Wealth / Stable Wealth

- **Polarity**: Element controlled by Day Master, opposite polarity
- **Represents**: Salary, stable income, wife (for men), practical resources
- **Positive**: Financial stability, responsibility, practicality
- **Negative**: Stinginess, materialism, over-caution with money

#### 七杀 (Qī Shā) — Seven Killings / Pressure

- **Polarity**: Element that controls Day Master, same polarity (harsh control)
- **Represents**: Pressure, challenges, authority, discipline, accidents
- **Positive**: Ambition, resilience, leadership under pressure, transformation
- **Negative**: Violence, accidents, excessive stress, legal troubles

#### 正官 (Zhèng Guān) — Direct Officer / Proper Authority

- **Polarity**: Element that controls Day Master, opposite polarity (gentle control)
- **Represents**: Career, status, husband (for women), rules, honor
- **Positive**: Responsibility, integrity, leadership, social status
- **Negative**: Rigidity, excessive conformity, inflexibility

#### 偏印 (Piān Yìn) — Indirect Resource / Partial Resource

- **Polarity**: Element that produces Day Master, same polarity
- **Represents**: Unconventional knowledge, intuition, spirituality, metaphysics
- **Positive**: Unique insights, spiritual depth, unconventional wisdom, creativity
- **Negative**: Paranoia, eccentricity, loneliness, overthinking

#### 正印 (Zhèng Yìn) — Direct Resource / Proper Resource

- **Polarity**: Element that produces Day Master, opposite polarity
- **Represents**: Mother, education, protection, knowledge, credentials
- **Positive**: Wisdom, kindness, academic success, protection, nurturing
- **Negative**: Over-dependence, laziness, excessive need for security

### 1.3 Analytical Principles

**Balance**:
- Too many or too few of any God creates imbalance.
- A strong Day Master benefits from Output (食伤) and Wealth (财) to channel
  its energy.
- A weak Day Master benefits from Resource (印) and Companion (比劫) for support.

**Key productive chains**:
- 官印相生 — Officer produces Resource → respected leadership
- 食伤生财 — Output produces Wealth → creativity generates income
- 财生官杀 — Wealth produces Officer/Killing → money brings power
- 杀印相生 — Killing produces Resource → pressure transforms into wisdom

**Gender conventions**:
- **Men**: 正财 = wife, 偏财 = lovers / windfall wealth, 官杀 = children, 印 = mother
- **Women**: 正官 = husband, 七杀 = lovers / pressure, 食伤 = children, 印 = mother

---

## 2. Hidden Stems (藏干)

### 2.1 Concept

Each Earthly Branch contains one to three **Hidden Stems** (藏干, Cáng Gān)—
Heavenly Stems concealed within the branch representing its inner elemental
composition. These are classified by strength:

- **Main Qi (本气, Běn Qì)** — the dominant energy (strongest)
- **Middle Qi (中气, Zhōng Qì)** — secondary energy (medium strength)
- **Residual Qi (余气, Yú Qì)** — tertiary energy (weakest)

### 2.2 Complete Hidden Stems Table

| Branch | Animal | Main Qi (本气) | Middle Qi (中气) | Residual Qi (余气) |
|---|---|---|---|---|
| 子 (Zǐ) | Rat | 癸 (Guǐ) Water | — | — |
| 丑 (Chǒu) | Ox | 己 (Jǐ) Earth | 癸 (Guǐ) Water | 辛 (Xīn) Metal |
| 寅 (Yín) | Tiger | 甲 (Jiǎ) Wood | 丙 (Bǐng) Fire | 戊 (Wù) Earth |
| 卯 (Mǎo) | Rabbit | 乙 (Yǐ) Wood | — | — |
| 辰 (Chén) | Dragon | 戊 (Wù) Earth | 乙 (Yǐ) Wood | 癸 (Guǐ) Water |
| 巳 (Sì) | Snake | 丙 (Bǐng) Fire | 戊 (Wù) Earth | 庚 (Gēng) Metal |
| 午 (Wǔ) | Horse | 丁 (Dīng) Fire | 己 (Jǐ) Earth | — |
| 未 (Wèi) | Goat | 己 (Jǐ) Earth | 丁 (Dīng) Fire | 乙 (Yǐ) Wood |
| 申 (Shēn) | Monkey | 庚 (Gēng) Metal | 壬 (Rén) Water | 戊 (Wù) Earth |
| 酉 (Yǒu) | Rooster | 辛 (Xīn) Metal | — | — |
| 戌 (Xū) | Dog | 戊 (Wù) Earth | 辛 (Xīn) Metal | 丁 (Dīng) Fire |
| 亥 (Hài) | Pig | 壬 (Rén) Water | 甲 (Jiǎ) Wood | — |

> **Mnemonic pattern**: The four cardinal branches (子, 卯, 午, 酉) contain only
> one or two stems. The four corner/storage branches (丑, 辰, 未, 戌) and the
> four traveling branches (寅, 巳, 申, 亥) contain two or three stems each.

### 2.3 Usage

1. **Rooting (通根, Tōng Gēn)**: When a chart's Heavenly Stem appears as a
   Hidden Stem in one of the branches, that stem has "root"—it is grounded and
   stronger. A rootless stem is considered floating and unreliable.

2. **Ten Gods from Hidden Stems**: Each Hidden Stem generates its own Ten God
   relationship with the Day Master, adding layers of nuance to pillar analysis.

3. **Seasonal Context**: Hidden Stems reveal residual energies from the
   preceding season within a branch. For example, 丑 (Ox, winter earth) harbors
   癸 (Water, winter's remnant) and 辛 (Metal).

4. **Combination & Clash Triggers**: Hidden Stems participate in stem
   combinations (合) and can be activated when Luck Pillars or Annual Pillars
   interact with their containing branch.

---

## 3. Twelve Longevity Stages (十二长生)

### 3.1 Concept

The **Twelve Longevity Stages** (十二长生, Shí Èr Cháng Shēng) model the life
cycle of an element's Qi as it passes through the twelve Earthly Branches. The
stages mirror human life from conception through death and rebirth.

### 3.2 The Twelve Stages

| # | Stage | Chinese | Meaning |
|---|---|---|---|
| 1 | Birth | 长生 (Cháng Shēng) | New beginning, vibrant, growing |
| 2 | Bathing | 沐浴 (Mù Yù) | Cleansing, vulnerable, slightly unstable |
| 3 | Crowning | 冠带 (Guàn Dài) | Adolescence, gaining recognition |
| 4 | Officer | 临官 (Lín Guān) | Prime of career, adulthood |
| 5 | Prosperity | 帝旺 (Dì Wàng) | Maximum strength, peak power |
| 6 | Decline | 衰 (Shuāi) | Weakening, slowing down |
| 7 | Sickness | 病 (Bìng) | Vulnerable, stagnation |
| 8 | Death | 死 (Sǐ) | End of cycle, dormant |
| 9 | Tomb | 墓 (Mù) | Buried, stored potential energy |
| 10 | Extinction | 绝 (Jué) | Lowest point, emptiness |
| 11 | Conception | 胎 (Tāi) | New life forming |
| 12 | Nurturing | 养 (Yǎng) | Gestation, preparation for birth |

### 3.3 Starting Branches (长生位)

Yang stems progress **forward** (clockwise) through the branches.
Yin stems progress **backward** (counter-clockwise) through the branches.

| Stem | Polarity | Element | 长生 starts at |
|---|---|---|---|
| 甲 (Jiǎ) | Yang Wood | Wood | 亥 (Hài) |
| 乙 (Yǐ) | Yin Wood | Wood | 午 (Wǔ) |
| 丙 (Bǐng) | Yang Fire | Fire | 寅 (Yín) |
| 丁 (Dīng) | Yin Fire | Fire | 酉 (Yǒu) |
| 戊 (Wù) | Yang Earth | Earth | 寅 (Yín) |
| 己 (Jǐ) | Yin Earth | Earth | 酉 (Yǒu) |
| 庚 (Gēng) | Yang Metal | Metal | 巳 (Sì) |
| 辛 (Xīn) | Yin Metal | Metal | 子 (Zǐ) |
| 壬 (Rén) | Yang Water | Water | 申 (Shēn) |
| 癸 (Guǐ) | Yin Water | Water | 卯 (Mǎo) |

> **Note**: 戊 (Yang Earth) shares starting branches with 丙 (Yang Fire), and
> 己 (Yin Earth) shares with 丁 (Yin Fire). This reflects Earth's classical
> association with Fire in the productive cycle.

### 3.4 Full Progression Examples

**Yang Wood (甲)** — forward from 亥:

```
亥(长生) → 子(沐浴) → 丑(冠带) → 寅(临官) → 卯(帝旺) → 辰(衰)
→ 巳(病) → 午(死) → 未(墓) → 申(绝) → 酉(胎) → 戌(养)
```

**Yin Wood (乙)** — backward from 午:

```
午(长生) → 巳(沐浴) → 辰(冠带) → 卯(临官) → 寅(帝旺) → 丑(衰)
→ 子(病) → 亥(死) → 戌(墓) → 酉(绝) → 申(胎) → 未(养)
```

### 3.5 Application

1. **Day Master strength**: Stages 1–5 (长生 through 帝旺) strengthen the Day
   Master; stages 6–12 weaken it.
2. **Luck Pillar timing**: Entering a favorable longevity stage signals good
   fortune for the corresponding element.
3. **Health analysis**: 病 (Sickness) and 死 (Death) stages may correlate with
   health challenges—especially when combined with unfavorable elements.
4. **Career timing**: 临官 and 帝旺 are optimal for career advancement.
5. **Relationship timing**: 胎 (Conception) and 养 (Nurturing) stages favor
   starting new relationships or ventures.

---

## 4. Solar Terms in Bazi Context (节气)

> **Implementation status**: The existing lunisolar calendar engine already
> computes Solar Terms with astronomical precision using Swiss Ephemeris data.
> This section documents their role in Bazi pillar determination.

### 4.1 The 24 Solar Terms

| Season | Jie (节) — Month Start | Qi (气) — Mid-Month |
|---|---|---|
| **Spring** | 立春 (Lì Chūn) ≈ Feb 4 | 雨水 (Yǔ Shuǐ) ≈ Feb 19 |
| | 惊蛰 (Jīng Zhé) ≈ Mar 5 | 春分 (Chūn Fēn) ≈ Mar 20 |
| | 清明 (Qīng Míng) ≈ Apr 4 | 谷雨 (Gǔ Yǔ) ≈ Apr 20 |
| **Summer** | 立夏 (Lì Xià) ≈ May 5 | 小满 (Xiǎo Mǎn) ≈ May 21 |
| | 芒种 (Máng Zhòng) ≈ Jun 5 | 夏至 (Xià Zhì) ≈ Jun 21 |
| | 小暑 (Xiǎo Shǔ) ≈ Jul 7 | 大暑 (Dà Shǔ) ≈ Jul 22 |
| **Autumn** | 立秋 (Lì Qiū) ≈ Aug 7 | 处暑 (Chù Shǔ) ≈ Aug 23 |
| | 白露 (Bái Lù) ≈ Sep 7 | 秋分 (Qiū Fēn) ≈ Sep 23 |
| | 寒露 (Hán Lù) ≈ Oct 8 | 霜降 (Shuāng Jiàng) ≈ Oct 23 |
| **Winter** | 立冬 (Lì Dōng) ≈ Nov 7 | 小雪 (Xiǎo Xuě) ≈ Nov 22 |
| | 大雪 (Dà Xuě) ≈ Dec 7 | 冬至 (Dōng Zhì) ≈ Dec 21 |
| | 小寒 (Xiǎo Hán) ≈ Jan 5 | 大寒 (Dà Hán) ≈ Jan 20 |

### 4.2 Critical Rules for Bazi

1. **Month pillar changes at Jie (节), not the lunar 1st**: The twelve Jie
   terms (立春, 惊蛰, 清明, 立夏, 芒种, 小暑, 立秋, 白露, 寒露, 立冬, 大雪,
   小寒) mark true month boundaries in Bazi.

2. **Year pillar changes at 立春 (Beginning of Spring), not Chinese New Year**:
   A person born on February 3 in a given year still belongs to the previous
   year's pillar if 立春 has not yet occurred.

3. **Luck Pillar calculation depends on Jie boundaries**: The distance (in
   days) from the birth date to the nearest Jie determines the starting age of
   the first Luck Pillar (see §5).

---

## 5. Luck Pillars (大运)

### 5.1 Concept

**Luck Pillars** (大运, Dà Yùn) are 10-year periods that define the dominant
elemental influences shaping each decade of a person's life. They are derived
from the month pillar and progress through consecutive Stem-Branch pairs.

### 5.2 Calculation

#### Step 1 — Determine direction

| Year Stem Polarity | Male | Female |
|---|---|---|
| **Yang** (甲丙戊庚壬) | Forward ↗ | Backward ↙ |
| **Yin** (乙丁己辛癸) | Backward ↙ | Forward ↗ |

#### Step 2 — Calculate starting age

1. Count the number of days from the **birth date** to the **next Jie** (if
   forward) or the **previous Jie** (if backward).
2. Divide by 3 → quotient = starting age in years.
3. Remainder days ÷ 3 → additional months (further remainder → days).

**Example**: 24 days to next Jie → 24 ÷ 3 = age **8**.

#### Step 3 — Sequence the pillars

Starting from the month pillar, advance (or retreat) through consecutive
Stem-Branch pairs. Each pillar governs 10 years.

**Example**: Birth month pillar 壬午, direction forward →
1. 癸未 (age 8–17)
2. 甲申 (age 18–27)
3. 乙酉 (age 28–37)
4. 丙戌 (age 38–47)
5. …

### 5.3 Interpretation

- **Stem** = external / visible influences (career, social status, events)
- **Branch** = internal / hidden influences (health, family, inner state)
- Apply Ten God analysis: what is the Luck Pillar's element relative to the
  Day Master?
- Check for combinations and clashes with natal chart branches.

### 5.4 Special Phenomena

| Term | Description |
|---|---|
| 伏吟 (Fú Yín) | Luck Pillar identical to a natal pillar — intensifies that energy, often challenging |
| 反吟 (Fǎn Yín) | Luck Pillar clashes with a natal pillar — sudden changes, disruptions |
| 岁运并临 (Suì Yùn Bìng Lín) | Annual Pillar matches the Luck Pillar — major life event year |
| 天克地冲 (Tiān Kè Dì Chōng) | Stem controls stem + branch clashes branch — highly turbulent |
| 天合地合 (Tiān Hé Dì Hé) | Stem combines stem + branch combines branch — deeply harmonious |

---

## 6. Annual Pillars (流年)

Each year carries its own Stem-Branch pillar (流年, Liú Nián) that interacts
with both the natal chart and the current Luck Pillar.

**Analysis priority**:
1. Annual stem vs. Day Master → determine its Ten God role.
2. Annual branch vs. natal branches → check for combinations, clashes,
   punishments, and harms.
3. Three-way interaction: Annual Pillar + Luck Pillar + Natal Chart.

---

## 7. Chart Structures (格局)

| Structure | Condition | Implication |
|---|---|---|
| 身旺 (Shēn Wàng) | Day Master strong | Needs Output and Wealth to release energy |
| 身弱 (Shēn Ruò) | Day Master weak | Needs Resource and Companion for support |
| 从格 (Cóng Gé) | Day Master extremely weak with no support | Follows the dominant element entirely |
| 化气格 (Huà Qì Gé) | Special stem combination transforms element | Complete transformation of elemental nature |
| 专旺格 (Zhuān Wàng Gé) | One element overwhelmingly dominant | Extreme specialization; follows that element |

---

## 8. Branch Interactions (合冲刑害)

### 8.1 Six Combinations (六合)

Branch pairs that combine and may transform into a new element:

| Combination | Resulting Element |
|---|---|
| 子 + 丑 | Earth (土) |
| 寅 + 亥 | Wood (木) |
| 卯 + 戌 | Fire (火) |
| 辰 + 酉 | Metal (金) |
| 巳 + 申 | Water (水) |
| 午 + 未 | Fire/Earth (火/土) |

### 8.2 Three Combinations (三合)

Three branches forming a directional elemental frame:

| Combination | Element |
|---|---|
| 申 + 子 + 辰 | Water (水局) |
| 寅 + 午 + 戌 | Fire (火局) |
| 巳 + 酉 + 丑 | Metal (金局) |
| 亥 + 卯 + 未 | Wood (木局) |

### 8.3 Directional Combinations (方局)

Three consecutive seasonal branches:

| Combination | Element |
|---|---|
| 寅 + 卯 + 辰 | Wood (木方) |
| 巳 + 午 + 未 | Fire (火方) |
| 申 + 酉 + 戌 | Metal (金方) |
| 亥 + 子 + 丑 | Water (水方) |

### 8.4 Six Clashes (六冲)

| Clash Pair |
|---|
| 子 ↔ 午 |
| 丑 ↔ 未 |
| 寅 ↔ 申 |
| 卯 ↔ 酉 |
| 辰 ↔ 戌 |
| 巳 ↔ 亥 |

### 8.5 Three Punishments (三刑)

| Type | Branches | Nature |
|---|---|---|
| Graceless punishment (无恩之刑) | 寅 → 巳 → 申 | Hidden dangers |
| Bullying punishment (恃势之刑) | 丑 → 戌 → 未 | Power struggles |
| Rude punishment (无礼之刑) | 子 ↔ 卯 | Discourtesy, friction |
| Self-punishment (自刑) | 辰↔辰, 午↔午, 酉↔酉, 亥↔亥 | Self-sabotage |

### 8.6 Six Harms (六害)

| Harm Pair |
|---|
| 子 ↔ 未 |
| 丑 ↔ 午 |
| 寅 ↔ 巳 |
| 卯 ↔ 辰 |
| 申 ↔ 亥 |
| 酉 ↔ 戌 |

---

## 9. Symbolic Stars (神煞)

| Star | Chinese | Nature | Effect |
|---|---|---|---|
| Nobleman | 天乙贵人 (Tiān Yǐ Guì Rén) | Auspicious | Help from influential people |
| Academic | 文昌 (Wén Chāng) | Auspicious | Intelligence, exam success |
| Peach Blossom | 桃花 (Táo Huā) | Mixed | Romance, charm, social popularity |
| Travel Horse | 驿马 (Yì Mǎ) | Neutral | Movement, travel, relocation |
| General | 将星 (Jiàng Xīng) | Auspicious | Leadership, authority |
| Canopy | 华盖 (Huá Gài) | Mixed | Spirituality, solitude, creativity |
| Goat Blade | 羊刃 (Yáng Rèn) | Inauspicious | Courage but risk of violence |
| Emptiness | 空亡 (Kōng Wáng) | Inauspicious | Weakness, things not materializing |

### Empty Branches (空亡)

Calculated from the day pillar's sexagenary position: within each 10-day
(Heavenly Stem) cycle, two of the twelve branches are left unpaired and become
"empty." Empty branches have reduced influence and often indicate:
- Plans that do not materialize easily
- Spiritual or unconventional matters surfacing
- Events arriving in unexpected ways

---

## 10. Favorable & Unfavorable Elements (用神体系)

| Term | Chinese | Role |
|---|---|---|
| Favorable Element | 用神 (Yòng Shén) | What the chart most needs for balance |
| Unfavorable Element | 忌神 (Jì Shén) | What harms the chart's balance |
| Joyful Element | 喜神 (Xǐ Shén) | Supports the 用神 |
| Enemy Element | 仇神 (Chóu Shén) | Supports the 忌神 |
| Neutral Element | 闲神 (Xián Shén) | Neither helps nor harms significantly |

### Supporting Concepts

| Concept | Chinese | Description |
|---|---|---|
| Temperature Adjustment | 调候 (Tiáo Hòu) | Balancing hot/cold charts (e.g., winter-born charts need Fire) |
| Passage Element | 通关 (Tōng Guān) | An intermediary element that resolves conflict between two clashing elements |
| Disease & Medicine | 病药 (Bìng Yào) | Identifying the chart's core problem (病) and its remedy (药) |

---

## 11. Analysis Flowchart

```
 1. Determine accurate Four Pillars using Solar Term boundaries
                        ↓
 2. Identify Day Master element and Yin/Yang polarity
                        ↓
 3. Extract Hidden Stems from all Earthly Branches
                        ↓
 4. Map all stems (visible + hidden) to Ten Gods
                        ↓
 5. Assess Day Master strength (strong/weak/extreme)
                        ↓
 6. Identify Chart Structure (格局)
                        ↓
 7. Determine Favorable / Unfavorable Elements (用神 / 忌神)
                        ↓
 8. Map Longevity Stages for life-cycle analysis
                        ↓
 9. Calculate Luck Pillars (大运) and their 10-year phases
                        ↓
10. Layer Annual Pillars (流年) for year-by-year forecasting
                        ↓
11. Evaluate branch interactions (combinations, clashes,
    punishments, harms) and symbolic stars
```

---

## References

- Baidu Baike: 十二长生 — <https://baike.baidu.com/item/十二长生/7204496>
- Zhihu: 十二长生表及记忆方法 — <https://zhuanlan.zhihu.com/p/613054827>
- Mastery Academy: Hidden Stems Reference Chart
- Imperial Harvest: Hidden Heavenly Stems (藏干) in Earthly Branches
- FengShuied: Ten Gods Table of Reference
- Skillon: BaZi – A Deeper Understanding of the Ten Gods 十神
- Elio Basagni: The 12 Stages of Growth

# Twelve Construction Stars (十二建星) Documentation

## Overview

The Twelve Construction Stars (十二建星, Shí'èr Jiànxīng) system is a traditional Chinese divination method used to determine auspicious and inauspicious dates for various activities. This ancient system is deeply rooted in Chinese cosmology and has been used for over a millennium to guide important decisions regarding ceremonies, construction, travel, and other significant life events.

## Historical Background and Sources (_Needs Verification_)

- **Historical Origin**: Dates to **Warring States period (战国)**, with bamboo slips from Qin and Chu states documenting early forms.  

- **Classical Sources**: The Twelve Construction Stars system originates from ancient Chinese astronomical and divinatory traditions, with its principles documented in classical texts such as:

- **Yùxiá Jì (《玉匣记》)** - "Jade Box Records": A comprehensive divination manual that codifies the Construction Stars system
- **Tōngshū (通书)** - Traditional Chinese almanacs that apply these principles for daily use
- **Qíméngtùnjiǎ (奇门遁甲)** - Ancient Chinese metaphysical system that incorporates similar cyclical calculations

The system reflects the Chinese understanding of cosmic cycles and their influence on earthly affairs, combining astronomical observations with metaphysical principles.

## Core Principles

### The Twelve Stars (十二建星)

The system consists of twelve sequential stars, each with specific characteristics:

| Chinese | Pinyin | English | Meaning | Classification |
|---------|--------|---------|---------|----------------|
| 建 | Jiàn | Establish | Foundation, beginning | Inauspicious (Black) |
| 除 | Chú | Remove | Clearing, elimination | Auspicious (Yellow) |
| 满 | Mǎn | Full | Completion, fullness | Inauspicious (Black) |
| 平 | Píng | Balanced | Equilibrium, peace | Inauspicious (Black) |
| 定 | Dìng | Set | Determination, fixing | Auspicious (Yellow) |
| 执 | Zhí | Hold | Grasping, persistence | Auspicious (Yellow) |
| 破 | Pò | Break | Destruction, breaking | Very Inauspicious (Unsuitable) |
| 危 | Wēi | Danger | Risk, precariousness | Auspicious (Yellow) |
| 成 | Chéng | Accomplish | Achievement, success | Moderate (Usable) |
| 收 | Shōu | Harvest | Gathering, collection | Inauspicious (Black) |
| 开 | Kāi | Open | Opening, beginning | Moderate (Usable) |
| 闭 | Bì | Close | Closing, ending | Very Inauspicious (Unsuitable) |

### Traditional Classification Formula

The auspiciousness of each star follows the traditional mnemonic:

**"建满平收黑，除危定执黄，成开皆可用，破闭不可当"**

- **Black Days (黑日)**: 建, 满, 平, 收 - Generally inauspicious
- **Yellow Days (黄日)**: 除, 危, 定, 执 - Auspicious for most activities
- **Usable Days (可用日)**: 成, 开 - Moderate, suitable for certain activities
- **Unsuitable Days (不可当)**: 破, 闭 - Very inauspicious, avoid important activities

## Calculation Methodology

### Step 1: Solar Terms Foundation

The calculation begins with the 24 Solar Terms (二十四节气), particularly:
- **立春 (Lìchūn)** - Beginning of Spring (February 4-5)
- Each subsequent solar term marks traditional month boundaries

### Step 2: Monthly Building System (月建)

Each traditional month has an associated Earthly Branch (地支):
- 正月建寅 (Lunisolar month 1: 建 Jiàn on the first Yín 寅 day)
- 二月建卯 (Lunisolar month 2: 建 Jiàn on the first Mǎo 卯 day)
- 三月建辰 (Lunisolar month 3: 建 Jiàn on the first Chén 辰 day)
- 四月建巳 (Lunisolar month 4: 建 Jiàn on the first Sì 巳 day)
- 五月建午 (Lunisolar month 5: 建 Jiàn on the first Wǔ 午 day)
- 六月建未 (Lunisolar month 6: 建 Jiàn on the first Wèi 未 day)
- 七月建申 (Lunisolar month 7: 建 Jiàn on the first Shēn 申 day)
- 八月建酉 (Lunisolar month 8: 建 Jiàn on the first Yǒu 酉 day)
- 九月建戌 (Lunisolar month 9: 建 Jiàn on the first Xū 戌 day)
- 十月建亥 (Lunisolar month 10: 建 Jiàn on the first Hài 亥 day)
- 十一月建子 (Lunisolar month 11: 建 Jiàn on the first Zǐ 子 day)
- 十二月建丑 (Lunisolar month 12: 建 Jiàn on the first Chǒu 丑 day)

### Step 3: Earthly Branch Calculation

The system uses the traditional Gānzhī (干支) calendar:
- **Reference Point**: February 18, 1912 - verified Jiǎzǐ 甲子 day (deprecated, now uses the lunisolar calendar engine `lunisolar_v2.py`)
- **Cycle**: 12 Earthly Branches rotating continuously
- **Branches**: 子, 丑, 寅, 卯, 辰, 巳, 午, 未, 申, 酉, 戌, 亥

### Step 4: Construction Star Assignment

1. **Find the Building Day**: Locate the first day in each traditional month that corresponds to the month's building branch
2. **Assign "建" (Jiàn)**: The first building day receives the "建" star
3. **Sequential Assignment**: Continue assigning the 12 stars in order for subsequent days
4. **Solar Term Handling**: **Critical rule** - On the day a **solar term (节气)** begins, the star **repeats the previous day's value** instead of progressing to the next star in sequence
   - This applies specifically to the 12 principal solar terms (节气), not the "middle qi" (中气)
   - Example: If the star on the day before 立春 (Lìchūn) is 收 (Shōu), the solar term day (立春) also takes 收 (Shōu), not the next star 开 (Kāi)
   - This mechanism exactly compensates for the "lag" of twelve days over the year, ensuring the cycle realigns annually
5. **Cyclical Repetition**: The pattern repeats every 12 days, with solar term adjustments maintaining yearly alignment

## Implementation Details

### Key Classes and Methods

#### `TwelveConstructionStars` Class

The main calculator class provides comprehensive functionality:

```python
class TwelveConstructionStars:
    def __init__(self, year: int)
    def get_construction_star_for_date(self, date: datetime) -> str
    def calculate_day_info(self, date: datetime) -> Dict
    def calculate_month_calendar(self, month: int) -> List[Dict]
    def find_auspicious_days_in_month(self, month: int, min_score: int = 3) -> List[Dict]
```

#### Core Calculation Methods

1. **`_calculate_solar_terms(year)`**: Computes the 24 solar terms for accurate month boundaries
2. **`_get_earthly_branch_for_date(date)`**: Determines the Earthly Branch for any given date
3. **`_get_month_from_solar_terms(date)`**: Maps dates to traditional lunar months
4. **`get_construction_star_for_date(date)`**: Main calculation method

### Scoring System

The implementation includes a numerical scoring system for practical application:

- **Score 4**: Highly auspicious (除, 危, 定, 执)
- **Score 3**: Moderately favorable (成, 开)
- **Score 2**: Generally unfavorable (建, 满, 平, 收)
- **Score 1**: Very unfavorable (破, 闭)

## Practical Applications

### Recommended Activities by Star

#### Auspicious Stars (Score 4)
- **除 (Chú - Remove)**: Cleaning, medical procedures, removing obstacles
- **危 (Wēi - Danger)**: Climbing, high-risk activities (paradoxically auspicious)
- **定 (Dìng - Set)**: Contracts, agreements, establishing foundations
- **执 (Zhí - Hold)**: Capturing, arrests, securing possessions

#### Moderate Stars (Score 3)
- **成 (Chéng - Accomplish)**: Completing projects, ceremonies
- **开 (Kāi - Open)**: Opening businesses, starting new ventures

#### Inauspicious Stars (Score 2)
- **建 (Jiàn - Establish)**: Avoid major construction
- **满 (Mǎn - Full)**: Avoid overfilling or excess
- **平 (Píng - Balanced)**: Neutral activities only
- **收 (Shōu - Harvest)**: Collection activities, but avoid new starts

#### Very Inauspicious Stars (Score 1)
- **破 (Pò - Break)**: Avoid all important activities
- **闭 (Bì - Close)**: Avoid openings, starts, or new ventures

### Cross-Validation of Solar Term Rule

The rule as stated in **Step 4**—that on the day a solar term (节气) begins you **repeat the previous day’s star** rather than advance to the next one—is indeed the classic method taught in Chinese calendrical texts. In fact:

* A modern “folk almanac” guide explicitly notes:

  > “原则上，十二直是12个一轮，但只有在每个月的节气交替日，会重复使用前一天的十二直。”
  > (In principle the 12‑day cycle runs continuously, but **only** on each month’s solar‑term transition day do you repeat the previous day’s value.) ([gltjp.com][1])

* An open‑source calendrical library spells out the same mechanism, adding that it applies to the 12 principal solar terms (not the “middle qi” 中气), and that doing so exactly compensates for the “lag” of twelve days over the year:

  > “碰到节气如惊蛰、清明等（不包括中气的雨水、谷雨等），就重复节气前一天的值，一年十二个节气下来正好滞后十二天，于是次年立春后的寅日又是‘建’。” ([cnpack.org][2])

So **yes**, the document’s description of Step 4 is accurate and reflects standard practice: whenever you hit a solar term day in the twenty‑four‑term cycle, you carry over (“freeze”) the prior day’s star rather than moving to the next one.

---

**Additional note:**
Most sources distinguish **节气** (the 12 “principal” terms like 立春、惊蛰、清明…) from the “middle qi” 中气 (雨水、谷雨, etc.). The “repeat” rule applies only to those **节气** days, ensuring the twelve‑star cycle realigns each year.

[1]: https://www.gltjp.com/zh-hans/article/item/21007/?utm_source=chatgpt.com "【高岛历完整指南】想知道今天究竟是个什么日子吗？来 ... - 好運日本行"
[2]: https://www.cnpack.org/showdetail.php?id=452&lang=en&utm_source=chatgpt.com "CnCalendar 历法说明 - CnPack Open Source Projects"

[3]: https://ytliu0.github.io/ChineseCalendar/solarTerms.html "24 Solar Terms (二 十 四 節 氣)"

*This documentation serves as both a technical reference and cultural guide to understanding and implementing the Twelve Construction Stars system in modern applications.*



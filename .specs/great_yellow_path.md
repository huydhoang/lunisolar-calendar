# Great Yellow Path (大黄道) System - Detailed Documentation

## Overview

The Great Yellow Path (大黄道) system is a sophisticated Chinese auspicious day calculation method that determines favorable and unfavorable dates based on the cyclical interaction of twelve spirits with earthly branches. This implementation provides a faithful reproduction of traditional formulas while incorporating modern computational accuracy.

### Key Features
- **Monthly Rotation**: Azure Dragon starting position rotates monthly according to traditional mnemonic formulas
- **Solar Terms Integration**: Uses authentic lunar months defined by the 24 solar terms
- **Comprehensive Spirit System**: All twelve spirits with detailed cultural descriptions
- **Accurate Day Branch Calculation**: Corrected reference point for precise earthly branch determination
- **Validation Framework**: Built-in validation of traditional mnemonic formulas

## Historical Background

The Great Yellow Path system represents one of the most sophisticated approaches to Chinese auspicious day selection, with roots extending back over a millennium. Unlike simpler fixed-starting systems, this method incorporates:

- **Ancient Astronomical Observations**: Based on careful observation of celestial cycles
- **Cyclical Time Philosophy**: Reflects the Chinese understanding of time as cyclical rather than linear
- **Regional Variations**: Adapted across different regions of Asia with local modifications
- **Practical Wisdom**: Accumulated knowledge for timing important life events

### Traditional Sources
The system draws from classical texts including:
- **Yùxiá Jì (《玉匣记》)**: "Jade Box Records" - comprehensive divination manual
- **Tōngshū (通书)**: Traditional Chinese almanacs
- **Regional Folk Traditions**: Oral transmission of calculation methods

## Core Principles

### The Twelve Spirits (十二神)

The system revolves around twelve spirits that govern different aspects of daily activities:

#### Yellow Path Days (黄道日) - Auspicious
1. **青龙 (Qinglong) - Azure Dragon**
   - Traditional: 天乙星，天贵星，利有攸往，所作必成，所求皆得
   - Modern: Auspicious for all activities, especially important endeavors and travel

2. **明堂 (Mingtang) - Bright Hall**
   - Traditional: 贵人星，明辅星，利见大人，利有攸往，作事必成
   - Modern: Favorable for meetings with important people, ceremonies, and official business

3. **金匮 (Jinkui) - Golden Coffer**
   - Traditional: 福德星，利释道用事，阍者女子用事，吉。宜嫁娶，不宜整戎伍
   - Modern: Good for financial matters, religious activities, and weddings

4. **天德 (Tiande) - Heavenly Virtue**
   - Traditional: 宝光星，天德星，其时大郭，作事有成，利有攸往，出行吉
   - Modern: Excellent for travel, important decisions, and virtuous activities

5. **玉堂 (Yutang) - Jade Hall**
   - Traditional: 天开星，百事吉，求事成，出行有财，宜文书喜庆之事，利见大人，利安葬，不利泥灶
   - Modern: Favorable for documents, celebrations, meetings with dignitaries, and burials

6. **司命 (Siming) - Life Controller**
   - Traditional: 凤辇星，此时从寅至申时用事大吉，从酉至丑时有事不吉，即白天吉，晚上不利
   - Modern: Good for health and longevity matters, but only during daytime hours (寅-申)

#### Black Path Days (黑道日) - Inauspicious
1. **天刑 (Tianxing) - Heavenly Punishment**
   - Traditional: 天刑星，利于出师，战无不克，其它动作谋为皆不宜用，大忌词讼
   - Modern: Avoid legal matters and conflicts; only suitable for military activities

2. **朱雀 (Zhuque) - Vermillion Bird**
   - Traditional: 天讼星，利用公事，常人凶，诸事忌用，谨防争讼
   - Modern: Unfavorable for communication and personal matters; beware of disputes

3. **白虎 (Baihu) - White Tiger**
   - Traditional: 天杀星，宜出师畋猎祭祀，皆吉，其余都不利
   - Modern: Dangerous day; only suitable for military expeditions, hunting, and sacrifices

4. **天牢 (Tianlao) - Heavenly Prison**
   - Traditional: 镇神星，阴人用事皆吉，其余都不利
   - Modern: Restrictive day; only favorable for women's activities

5. **玄武 (Xuanwu) - Black Tortoise**
   - Traditional: 天狱星，君子用之吉，小人用之凶，忌词讼博戏
   - Modern: Day of hidden dangers; avoid legal matters and gambling

6. **勾陈 (Gouchen) - Coiling Snake**
   - Traditional: 地狱星，起造安葬，犯此绝嗣。此时所作一切事，有始无终，先喜后悲，不利攸往
   - Modern: Day of entanglements and delays; avoid construction and burials

### Traditional Mnemonic Formula (口诀)

The Azure Dragon starting position for each month follows the traditional mnemonic:

```
寅申需加子，卯酉却在寅
辰戍龙位上，巳亥午上存
子午临申地，丑未戍上行
```

This translates to:
- **Lunisolar months 1&7 (寅申)**: Azure Dragon starts at 子 (Zi) day
- **Lunisolar months 2&8 (卯酉)**: Azure Dragon starts at 寅 (Yin) day
- **Lunisolar months 3&9 (辰戍)**: Azure Dragon starts at 辰 (Chen) day
- **Lunisolar months 4&10 (巳亥)**: Azure Dragon starts at 午 (Wu) day
- **Lunisolar months 5&11 (子午)**: Azure Dragon starts at 申 (Shen) day
- **Lunisolar months 6&12 (丑未)**: Azure Dragon starts at 戌 (Xu) day

### Earthly Branches (十二地支)

The system uses the twelve earthly branches, each associated with a zodiac animal:

| Index | Chinese | Animal | Time Period |
|-------|---------|--------|--------------|
| 0 | 子 (Zi) | Rat | 23:00-01:00 |
| 1 | 丑 (Chou) | Ox | 01:00-03:00 |
| 2 | 寅 (Yin) | Tiger | 03:00-05:00 |
| 3 | 卯 (Mao) | Rabbit | 05:00-07:00 |
| 4 | 辰 (Chen) | Dragon | 07:00-09:00 |
| 5 | 巳 (Si) | Snake | 09:00-11:00 |
| 6 | 午 (Wu) | Horse | 11:00-13:00 |
| 7 | 未 (Wei) | Goat | 13:00-15:00 |
| 8 | 申 (Shen) | Monkey | 15:00-17:00 |
| 9 | 酉 (You) | Rooster | 17:00-19:00 |
| 10 | 戌 (Xu) | Dog | 19:00-21:00 |
| 11 | 亥 (Hai) | Pig | 21:00-23:00 |

## System Architecture

### Class Structure

```python
class GreatYellowPathCalculator:
    """Main calculator class for the Great Yellow Path system."""
    
    # Core data structures
    AZURE_DRAGON_MONTHLY_START: Dict[int, EarthlyBranch]
    MONTH_CONSTRUCTION: Dict[int, EarthlyBranch]
    SPIRIT_SEQUENCE: List[GreatYellowPathSpirit]
    MNEMONIC_FORMULAS: Dict[int, str]
```

### Data Models

```python
@dataclass
class GreatYellowPathReading:
    """Complete reading for a specific day."""
    date: datetime
    lunar_month: int
    day_branch: EarthlyBranch
    spirit: GreatYellowPathSpirit
    path_type: str
    is_auspicious: bool
    azure_dragon_start: EarthlyBranch
    mnemonic_validation: str
```

### Calculation Flow

1. **Date Input** → Gregorian calendar date
2. **Lunar Month Determination** → Based on solar terms or lunar calendar boundaries
3. **Azure Dragon Start** → Retrieved from monthly mapping using mnemonic formula
4. **Day Branch Calculation** → Earthly branch for the specific date
5. **Spirit Calculation** → Offset from Azure Dragon start applied to spirit sequence
6. **Reading Generation** → Complete auspiciousness assessment

# Principal Solar Terms

Here are the 12 **major solar terms** (中氣 zhōngqì), each when the Sun’s apparent ecliptic longitude reaches a multiple of 30°, labeled Z1–Z12 (with approximate Gregorian dates) ([ytliu0.github.io][1]):

1. **Z1 雨水 Yǔshuǐ** – Rain Water (330°, ≈ Feb 19)
2. **Z2 春分 Chūnfēn** – Spring Equinox (0°, ≈ Mar 21)
3. **Z3 穀雨 Gǔyǔ** – Grain Rain (30°, ≈ Apr 20)
4. **Z4 小滿 Xiǎomǎn** – Grain Full (60°, ≈ May 21)
5. **Z5 夏至 Xiàzhì** – Summer Solstice (90°, ≈ Jun 22)
6. **Z6 大暑 Dàshǔ** – Great Heat (120°, ≈ Jul 23)
7. **Z7 處暑 Chǔshǔ** – Limit of Heat (150°, ≈ Aug 23)
8. **Z8 秋分 Qiūfēn** – Autumnal Equinox (180°, ≈ Sep 23)
9. **Z9 霜降 Shuāngjiàng** – Descent of Frost (210°, ≈ Oct 23)
10. **Z10 小雪 Xiǎoxuě** – Slight Snow (240°, ≈ Nov 22)
11. **Z11 冬至 Dōngzhì** – Winter Solstice (270°, ≈ Dec 22)
12. **Z12 大寒 Dàhán** – Great Cold (300°, ≈ Jan 20)

[1]: https://ytliu0.github.io/ChineseCalendar/solarTerms.html "24 solar terms (二十四節氣)"

---

# Lunisolar Calendar Rules

Below are the core astronomical rules that govern how lunar months are numbered and named in the traditional Chinese lunisolar calendar:

---

## 1. Month boundaries

* **Each lunar month begins** on the day of the astronomical **new moon** (lunar conjunction).  The first day (朔) is the day on which the Sun–Moon longitude difference is 0° (new moon) as measured at midnight (China Standard Time) ([chinaknowledge.de][1]).
* **Critical implementation rule:** Lunar months start at **00:00 local time (CST)** on the day of the new moon, **not** at the exact astronomical time of the new moon. This means if a new moon occurs at any time during a given date (e.g., 14:06:33 CST on August 23), the entire day from 00:00:00 CST is considered day 1 of the new lunar month.
* **Practical impact:** This date-only boundary rule ensures consistent lunar day calculations and proper alignment with traditional Chinese calendar practices, where calendar dates take precedence over precise astronomical moments for daily use.

---

## 2. The Zi (子) month and Winter Solstice

* There are 12 **principal (major) solar terms** (中氣), one every 30° of solar longitude.
* **Winter Solstice (冬至, Z11)** at 270° **must** always fall **within the 11th lunar month**, which is therefore called **Zi month (子月)**.
* Practically: find the lunar month that contains the instant of Winter Solstice — that month is month 11 (子月) ([webexhibits.org][2], [ytliu0.github.io][3]).
* The months that follow are then numbered **12, 1, 2, …** in sequence of new moons until the next Zi month.

---

## 3. Determining the Yin (寅) “Tiger” month

There are two parallel naming conventions:

1. **Principal‑term system (建造):**

   * Each month is “built” (建) on the principal term it contains.
   * The principal term **Rain Water (雨水, Z1 at 330°)** falls in the lunar month called **Yin month (寅月)** .

2. **Section‑term system (節造):**

   * Each lunar month spans from one **minor** solar term (節氣) to the next.
   * The minor term **Lìchūn (立春, 315°)**—“Spring Begins”—**marks the first day of Yin month (寅月)** ([en.wikipedia.org][4]).

---

## 4. Intercalary (leap) month

### 4.1 When intercalary months occur

* A "leap" (閏) month is inserted when a lunisolar year (歲 suì) has **13 new moons** between one Zi month and the next.
* This happens approximately every 2.7 years due to the mismatch between lunar cycles (29.53 days) and the solar year (365.25 days).
* **Mathematical basis:** 12 lunar months = ~354 days, while a solar year = ~365 days. The ~11-day difference accumulates, requiring periodic adjustment.

### 4.2 The "no zhōngqì" rule (無中氣法)

* **Core principle:** In a year with 13 lunar months, there are still only 12 principal terms (中氣).
* **Identification rule:** The **first lunar month that does *not* contain any principal term** is designated the **leap month**.
* **Naming convention:** It takes the number of its **preceding month**, with the prefix **"leap" (閏)**—e.g. "leap 6th month" (閏六月).

### 4.3 Detailed determination process

1. **Identify the lunisolar year span:** From one Zi month (containing Winter Solstice) to the next Zi month.
2. **Count new moons:** If there are 13 new moons in this span, an intercalary month is needed.
3. **Map principal terms:** Assign each of the 12 principal terms to lunar months based on which month contains each term.
4. **Find the gap:** The first lunar month without a principal term becomes the intercalary month.
5. **Sequential numbering:** Continue numbering subsequent months normally after the intercalary month.

### 4.4 Timezone considerations

* **Critical importance:** All astronomical calculations (new moons, solar terms) must be computed in **China Standard Time (CST, UTC+8)**.
* **Why CST matters:** The exact timing of new moons and solar terms can differ by hours across timezones, potentially changing which lunar month contains which principal term.
* **Historical precedent:** Traditional Chinese calendar calculations have always been based on Beijing/Chinese local time.

### 4.5 Edge cases and special considerations

* **Multiple candidate months:** In rare cases, multiple months might lack principal terms. Always choose the **first** such month.
* **Zi month exception:** The Zi month (containing Winter Solstice) can never be intercalary, as it must contain the Z11 principal term.
* **Year boundary effects:** Intercalary months near the lunar new year can affect which solar year they're associated with.
* **Modern vs. traditional:** Historical calendars may differ from modern astronomical calculations due to improved precision.

### 4.6 Date comparison logic for principal terms

* **Critical rule:** When determining if a lunar month contains a principal term, **date-only comparison** must be used, not precise timestamp comparison.
* **Same-date convention:** If a principal solar term and new moon occur on the **same calendar date** (in CST) **regardless of which comes first**, it is considered **day 1** of the lunar month.
* **Implementation:** Convert all astronomical events (new moons and solar terms) to CST, then compare only the date components (YYYY-MM-DD), ignoring the time components.
* **Rationale:** Traditional Chinese calendar practices focus on calendar dates for easy memorization, rather than precise astronomical moments.
* **Example case:** In 2025, T6 (Great Heat) occurs at 2025-08-23 04:33:51 CST, and a new moon occurs at 2025-08-23 14:06:33 CST. Since both events occur on the same date (2025-08-23), the solar term is considered to fall on day 1 of the lunar month starting with that new moon.
* **Impact on leap months:** This date-only comparison ensures correct identification of months lacking principal terms, which is essential for proper intercalary month determination.

---

## 5. Astronomical calculations and implementation

### 5.1 New moon calculation

* **Definition:** The moment when the Sun and Moon have the same ecliptic longitude (lunar conjunction).
* **Precision required:** Calculations must be accurate to within minutes to correctly determine lunar month boundaries.
* **Data source:** Modern implementations use JPL ephemeris data (DE440/DE441) for highest accuracy.
* **Timezone conversion:** All calculations performed in UTC, then converted to CST for calendar determination.

### 5.2 Solar term calculation

* **Method:** Based on the Sun's apparent ecliptic longitude reaching specific degrees (multiples of 15° for all terms, multiples of 30° for principal terms).
* **Coordinate system:** Uses apparent geocentric longitude, accounting for nutation and aberration.
* **Accuracy:** Modern calculations achieve sub-minute precision using VSOP87 or JPL ephemeris.

### 5.3 Implementation algorithm

1. **Establish reference points:**
   - Find Winter Solstice for the target year
   - Identify the Zi month containing this solstice

2. **Generate lunar month boundaries:**
   - Calculate all new moons in a window spanning 1.5 years around the target date
   - Sort chronologically to establish month boundaries

3. **Map principal terms to months:**
   - Calculate all 12 principal terms in the same time window
   - Determine which lunar month contains each principal term

4. **Apply intercalary month rules:**
   - Count lunar months between consecutive Zi months
   - If 13 months exist, identify the first month lacking a principal term
   - Assign intercalary status and appropriate numbering

5. **Handle edge cases:**
   - Special handling for known historical discrepancies (e.g., 2025 leap month 6)
   - Timezone-sensitive calculations for boundary cases

### 5.4 Validation and testing

* **Historical verification:** Compare results with established Chinese calendar sources
* **Cross-reference:** Validate against multiple astronomical calculation libraries
* **Edge case testing:** Verify correct handling of intercalary months and year boundaries
* **Timezone sensitivity:** Test calculations across different timezone assumptions

---

## 6. Reference Dates for Sexagenary Cycle Calculations

### 6.1 Traditional Yellow Emperor Era References

* **Legendary origin:** According to Chinese tradition, the sexagenary cycle (干支历) was invented by Da Nao (大挠), a minister of the Yellow Emperor (黄帝).
* **Traditional starting point:** 2997 BCE is often cited as the beginning of the Yellow Emperor era (甲子年) in the context of the sexagenary cycle.
* **Historical continuity:** Archaeological evidence from Shang Dynasty oracle bones confirms the use of stem-branch day recording, and historical records show continuous use since at least 720 BCE.
* **720 BCE anchor point:** A solar eclipse on a 己巳 day in 720 BCE provides a confirmed historical reference point for day cycle calculations.
* **Cultural significance:** These traditional references maintain alignment with classical Chinese chronological systems and astrological practices.

### 6.2 Authoritative reference date: 4 AD (Jiazi year)

* **Primary reference:** The year **4 AD** is used as the authoritative Jiazi (甲子) year for all sexagenary cycle calculations.
* **Historical basis:** 4 AD is widely cited in Chinese astronomical texts as a verified Jiazi year, providing a historically grounded reference point.
* **Advantages over other references:**
  - More historically verifiable than legendary dates while respecting traditional foundations
  - Predates modern computational references (e.g., 1984) while maintaining astronomical accuracy
  - Consistent with traditional Chinese chronological systems
  - Balances historical authenticity with computational reliability

### 6.3 Year cycle calculation

* **Formula:** `year_cycle = (lunar_year - 4) % 60 + 1`
* **Rationale:** Uses 4 AD as the base Jiazi year, with subsequent years following the 60-year sexagenary cycle
* **Range:** Returns values 1-60, where 1 represents Jiazi (甲子) and 60 represents Guihai (癸亥)

### 6.4 Day cycle calculation

* **Reference date:** January 31, 4 AD (Jiazi day)
* **Traditional alignment:** Adjusted to align with traditional Chinese day cycle calculations that have been continuous since ancient times
* **Formula:** Based on days elapsed since the reference date, adjusted for the sexagenary cycle
* **Historical continuity:** Maintains consistency with the traditional day counting system that traces back to the Yellow Emperor era
* **Astronomical accuracy:** Accounts for leap years and calendar transitions while preserving traditional alignment

### 6.5 Alternative reference dates (historical context)

* **2997 BCE:** Traditional Yellow Emperor era start (legendary Jiazi year)
* **720 BCE:** Confirmed historical anchor point (己巳 day solar eclipse)
* **1984 AD:** Modern computational reference marking the 78th cycle beginning
* **2637 BCE:** Alternative Yellow Emperor chronology
* **2697 BCE:** Another traditional Yellow Emperor dating

---

## 7. Stem-Branch (Ganzhi) Calculations

### 7.1 Time-based calculations

* **Year, Month, Day cycles:** These are calculated based on astronomical events and can use standardized time (UTC) for consistency.
* **Hour cycles (時辰):** Must be calculated using **local solar time**, not UTC, according to traditional Chinese practices.

### 7.2 Hour calculation methodology

* **Traditional basis:** The 12 double-hours (時辰 shíchén) are based on the sun's position relative to the local meridian.
* **Local solar time requirement:** Each location's hour stem-branch is determined by its local solar time, not standardized time zones.
* **Implementation:** Hour calculations should use the original local time before any UTC conversion.
* **Cultural significance:** This maintains alignment with traditional feng shui, Chinese medicine, and astrological practices that depend on local solar positioning.

### 7.3 Gan (Stem) calculation for hours

* **Wu Shu Dun rule (五鼠遁):** The hour stem is determined using the traditional "Five Rats Escape" formula.
* **Day stem dependency:** The hour stem depends on the day's heavenly stem, following a fixed pattern:
  - 甲/己 days: Zi hour starts with 甲 (Jiǎ)
  - 乙/庚 days: Zi hour starts with 丙 (Bǐng)
  - 丙/辛 days: Zi hour starts with 戊 (Wù)
  - 丁/壬 days: Zi hour starts with 庚 (Gēng)
  - 戊/癸 days: Zi hour starts with 壬 (Rén)
* **Sequential progression:** Once the Zi hour stem is determined, subsequent hours follow the 10-stem cycle.
* **Formula:** Hour stem index = (Zi hour stem index + hour branch index) % 10

### 7.4 Critical time boundary: 23:00-23:59 as next day's Zi hour

* **Traditional rule:** Hours from 23:00 to 23:59 belong to the **next day's** Zi hour (子時), not the current day.
* **Astronomical basis:** This reflects the traditional Chinese understanding that the new day begins at 23:00 (子時 start).
* **Stem calculation impact:** The hour stem for 23:00-23:59 must be calculated using the **next day's** stem, not the current day's stem.
* **Implementation requirement:** Code must advance the day by one when calculating hour stems for times between 23:00-23:59.
* **Cultural significance:** This boundary is crucial for accurate Four Pillars (八字) calculations in Chinese astrology and traditional practices.

### 7.5 The 12 traditional hours (時辰)

1. **子時 (Zǐ Shí)** - 23:00-01:00 (Rat Hour) - **Note: 23:00-23:59 belongs to next day**
2. **丑時 (Chǒu Shí)** - 01:00-03:00 (Ox Hour)
3. **寅時 (Yín Shí)** - 03:00-05:00 (Tiger Hour)
4. **卯時 (Mǎo Shí)** - 05:00-07:00 (Rabbit Hour)
5. **辰時 (Chén Shí)** - 07:00-09:00 (Dragon Hour)
6. **巳時 (Sì Shí)** - 09:00-11:00 (Snake Hour)
7. **午時 (Wǔ Shí)** - 11:00-13:00 (Horse Hour)
8. **未時 (Wèi Shí)** - 13:00-15:00 (Goat Hour)
9. **申時 (Shēn Shí)** - 15:00-17:00 (Monkey Hour)
10. **酉時 (Yǒu Shí)** - 17:00-19:00 (Rooster Hour)
11. **戌時 (Xū Shí)** - 19:00-21:00 (Dog Hour)
12. **亥時 (Hài Shí)** - 21:00-23:00 (Pig Hour)

### 7.6 Code implementation details

* **Hour branch calculation:** Uses the standard 12-branch cycle with 23:00-01:00 mapped to Zi (子) branch.
* **Hour stem calculation:** Implements Wu Shu Dun (五鼠遁) rule with special boundary handling:
  - For times 00:00-22:59: Uses current day's stem as base for hour stem calculation
  - For times 23:00-23:59: Uses **next day's stem** as base for hour stem calculation
* **Day advancement logic:** When local time ≥ 23:00, the code calculates `next_day_cycle = (day_cycle % 60) + 1` to get the next day's stem.
* **Formula application:** Hour stem = (base_day_stem_index - 1) × 12 + hour_branch_index - 1) % 60 + 1
* **Validation:** This implementation ensures accurate Four Pillars calculations that align with traditional Chinese astrological practices.

---

### Putting it all together

1. **Start** each month at the new moon (calculated in CST).
2. **Identify** Winter Solstice; that lunar month is always **Zi month** (11th).
3. **Count** subsequent months by new moons: 12, 1, 2, …
4. **Name** the Tiger month (Yin month) either as the month containing Rain Water (principal term) or the month beginning at Lìchūn (minor term).
5. **Insert** a "leap" month whenever a lunisolar year has 13 new moons; the first principal‑term‑free month becomes the leap month.
6. **Apply timezone corrections** to ensure all astronomical events are evaluated in China Standard Time.
7. **Handle special cases** where traditional sources may override pure astronomical calculations.

These rules keep the lunar months roughly aligned with the seasons—anchoring winter around the Zi month and spring around the Yin month—while inserting an occasional extra month to correct for the \~11‑day excess of twelve lunar cycles over one solar year.

[1]: https://www.chinaknowledge.de/History/Terms/calendar.html?utm_source=chatgpt.com "Calendar, chronology and astronomy (www.chinaknowledge.de)"
[2]: https://www.webexhibits.org/calendars/calendar-chinese.html?utm_source=chatgpt.com "The Chinese Calendar - Webexhibits"
[3]: https://ytliu0.github.io/ChineseCalendar/rules.html?utm_source=chatgpt.com "Rules for the Chinese Calendar - GitHub Pages"
[4]: https://en.wikipedia.org/wiki/Solar_term?utm_source=chatgpt.com "Solar term"


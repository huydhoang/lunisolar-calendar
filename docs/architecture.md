# Architecture Blueprint: Lunisolar Calendar System

This document outlines the architecture for the two main components of the Lunisolar Calendar project: the Python-based data pipeline and the TypeScript npm package.

## 1. Python-Based Data Pipeline Architecture

### 1.1. Purpose

The Python pipeline performs high-precision astronomical calculations (new moons, solar terms, sexagenary cycles, auspicious-day systems) using NASA's JPL DE440 ephemeris via Skyfield. It also exposes the full lunisolar calendar engine and the Bazi (Four Pillars) analysis framework as importable packages.

### 1.2. Package Structure

After the 2026-02-28 modular refactor, `lunisolar-python/` is organised into focused packages. Top-level `*.py` files are thin backward-compatible facades.

```
lunisolar-python/
├── shared/                  # Shared constants & dataclasses
│   ├── constants.py         # HEAVENLY_STEMS, EARTHLY_BRANCHES, PRINCIPAL_TERMS, derived lookups
│   └── models.py            # PrincipalTerm, MonthPeriod, LunisolarDateDTO
│
├── ephemeris/               # Low-level ephemeris wrappers
│   ├── solar_terms.py       # calculate_solar_terms()
│   └── moon_phases.py       # calculate_moon_phases()
│
├── lunisolar/               # Lunisolar calendar engine
│   ├── api.py               # solar_to_lunisolar(), solar_to_lunisolar_batch()
│   ├── ephemeris_service.py # EphemerisService — new moons & principal terms
│   ├── month_builder.py     # MonthBuilder, TermIndexer, LeapMonthAssigner
│   ├── sexagenary.py        # SexagenaryEngine — year/month/day/hour ganzhi
│   ├── resolver.py          # LunarMonthResolver, ResultAssembler
│   ├── timezone_service.py  # TimezoneService
│   ├── window_planner.py    # WindowPlanner
│   └── __main__.py          # python -m lunisolar
│
├── huangdao/                # Auspicious-day systems
│   ├── constants.py         # EarthlyBranch / GreatYellowPathSpirit enums, lookup tables
│   ├── construction_stars.py# ConstructionStars (12-star system)
│   ├── great_yellow_path.py # GreatYellowPath.calculate_spirit()
│   ├── calculator.py        # HuangdaoCalculator, print_month_calendar()
│   └── __main__.py          # python -m huangdao
│
├── bazi/                    # Four Pillars (Bazi) analysis
│   ├── core.py              # BaziChart
│   ├── ten_gods.py          # Ten Gods
│   ├── branch_interactions.py
│   ├── luck_pillars.py
│   ├── projections.py
│   └── cli.py / __main__.py
│
├── lunisolar_v2.py          # Facade → lunisolar package
├── huangdao_systems_v2.py   # Facade → huangdao package
├── solar_terms.py           # Facade → ephemeris.solar_terms
├── moon_phases.py           # Facade → ephemeris.moon_phases
├── utils.py                 # setup_logging(), write_csv_file(), …
├── config.py                # OUTPUT_DIR, ephemeris path
├── timezone_handler.py      # TimezoneHandler (pytz wrapper)
└── main.py                  # Bulk data generation orchestrator
```

### 1.3. Key Data Flows

**Lunisolar conversion** (`python -m lunisolar --date YYYY-MM-DD`):
1. `api.solar_to_lunisolar()` creates service objects and delegates to `LunarMonthResolver`.
2. `EphemerisService` loads `nasa/de440.bsp` via Skyfield and computes new moons + principal terms.
3. `MonthBuilder` assembles month periods; `LeapMonthAssigner` applies the no-zhongqi leap rule.
4. `SexagenaryEngine` derives year/month/day/hour ganzhi with the Wu Shu Dun rule.
5. `ResultAssembler` packages everything into a `LunisolarDateDTO`.

**Auspicious days** (`python -m huangdao -y YYYY -m MM`):
1. `HuangdaoCalculator` calls `solar_to_lunisolar_batch()` for each day in the month.
2. `ConstructionStars.get_star()` looks up the 12-building-star for each day.
3. `GreatYellowPath.calculate_spirit()` derives the Yellow/Black Path spirit from the day's branch.
4. `print_month_calendar()` renders the combined table to stdout.

### 1.4. Shared Constants & Models (`shared/`)

All packages import canonical data from `shared/` rather than defining local copies:

| Symbol | Description |
|---|---|
| `HEAVENLY_STEMS` | Tuple of 10 stem objects with char, pinyin, element, polarity |
| `EARTHLY_BRANCHES` | Tuple of 12 branch objects with char, pinyin, animal, element |
| `PRINCIPAL_TERMS` | List of 12 principal solar terms (zhongqi) |
| `STEM_CHARS` / `BRANCH_CHARS` | Plain character lists derived from the above |
| `BRANCH_INDEX` | `{char: index}` lookup |
| `EARTHLY_BRANCH_PINYIN` | `{char: pinyin}` lookup |
| `LunisolarDateDTO` | Frozen dataclass — canonical conversion result |

---

## 2. TypeScript NPM Package Architecture

### 2.1. Purpose

The TypeScript package (`lunisolar.ts`) will provide a modern, typesafe, and highly performant API for developers to work with the Chinese lunisolar calendar and its related astrological systems. It is designed to be extensible and maintainable.

### 2.2. Naming Conventions

-   **Classes:** `PascalCase` (e.g., `LunisolarCalendar`, `TimezoneHandler`).
-   **Methods/Functions:** `camelCase` (e.g., `fromSolarDate`, `getConstructionStar`).
-   **Interfaces/Types:** `PascalCase` with a `T` prefix (e.g., `TLunisolarDate`, `TConstructionStar`).
-   **Private Properties/Methods:** Prefixed with an underscore `_` (e.g., `_calculateLeapMonth`).

### 2.3. Core Modules

The package will be organized into a modular structure within a `src/` directory.

#### 2.3.1. Data Loader (`src/data/DataLoader.ts`)

-   **Class:** `DataLoader`
-   **Responsibility:** Manages the dynamic, lazy-loading of the static JSON data chunks. It will maintain a cache of loaded data to avoid redundant network requests.
-   **Methods:**
    -   `getSolarTerms(year: number): Promise<TSolarTerm[]>`
    -   `getNewMoons(year: number): Promise<TNewMoon[]>`
-   **Logic:** When a method is called, it checks if the data for that year is already in the cache. If not, it constructs the URL for the corresponding JSON file and uses `fetch` to load it.

#### 2.3.2. Timezone Handler (`src/timezone/TimezoneHandler.ts`)

-   **Class:** `TimezoneHandler`
-   **Responsibility:** Handles all timezone conversions. It will use the browser's native `Intl.DateTimeFormat` API to ensure accuracy and avoid bundling heavy timezone libraries.
-   **Methods:**
    -   `constructor(timezone: string)` // e.g., 'Asia/Shanghai', 'America/New_York'
    -   `convertToTimezone(date: Date): Date`
    -   `utcToTimezoneDate(utcDate: Date): TDateParts`

#### 2.3.3. Core Calendar (`src/core/LunisolarCalendar.ts`)

-   **Class:** `LunisolarCalendar`
-   **Responsibility:** This is the heart of the package. It takes a standard JavaScript `Date` object and, using the data from the `DataLoader`, converts it into a complete lunisolar date representation, strictly following the rules in `lunisolar_calendar_rules.md`.
-   **Static Factory Method:**
    -   `static fromSolarDate(date: Date, timezone: string): Promise<LunisolarCalendar>`
-   **Properties (Readonly):**
    -   `lunarYear`, `lunarMonth`, `lunarDay`
    -   `isLeapMonth`
    -   `yearStem`, `yearBranch`
    -   `monthStem`, `monthBranch`
    -   `dayStem`, `dayBranch`
    -   `hourStem`, `hourBranch`
-   **Methods:**
    -   `getSolarDate(): Date`
    -   `toString(): string` // Formatted lunisolar date string

#### 2.3.4. Huangdao Systems (`src/huangdao/`)

These modules will depend on an instance of `LunisolarCalendar` to perform their calculations.

-   **12 Construction Stars (`src/huangdao/ConstructionStars.ts`)**
    -   **Class:** `ConstructionStars`
    -   **Constructor:** `constructor(calendar: LunisolarCalendar)`
    -   **Methods:**
        -   `getStar(): TConstructionStar` // Returns an object with name, auspiciousness, score, etc.
        -   `static getAuspiciousDays(year: number, month: number, minScore: number): Promise<TDayInfo[]>`

-   **Great Yellow Path (`src/huangdao/GreatYellowPath.ts`)**
    -   **Class:** `GreatYellowPath`
    -   **Constructor:** `constructor(calendar: LunisolarCalendar)`
    -   **Methods:**
        -   `getSpirit(): TGreatYellowPathSpirit` // Returns an object with the spirit's name, type (Yellow/Black Path), etc.

### 2.4. Main Entry Point (`src/index.ts`)

This file will be the main entry point for the package, exporting all the public classes and types.

```typescript
// src/index.ts
export { LunisolarCalendar } from './core/LunisolarCalendar';
export { ConstructionStars } from './huangdao/ConstructionStars';
export { GreatYellowPath } from './huangdao/GreatYellowPath';
export * from './types'; // Export all public types
```

### 2.5. Extensibility

This architecture is designed for future expansion. To add a new module (e.g., a "Nine Stars" calculator):
1.  Add any necessary data generation to the Python pipeline.
2.  Create a new class in the TypeScript package (e.g., `src/ki/NineStars.ts`).
3.  The new class would take a `LunisolarCalendar` instance in its constructor, ensuring it has all the necessary date components.
4.  Export the new class from `src/index.ts`.

This modular, data-driven approach ensures the package remains maintainable, scalable, and highly performant.

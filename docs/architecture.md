# Architecture Blueprint: Lunisolar Calendar System

This document outlines the architecture for the two main components of the Lunisolar Calendar project: the Python-based data pipeline and the TypeScript npm package.

## 1. Python-Based Data Pipeline Architecture

### 1.1. Purpose

The primary role of the Python pipeline is to perform computationally intensive astronomical calculations and pre-generate high-precision data. This approach offloads the heavy lifting from the client-side TypeScript package, ensuring the end-user application is fast and lightweight. The pipeline serves as the single source of truth for all astronomical events.

### 1.2. Components

The pipeline is composed of modular, single-responsibility Python scripts.

-   **Orchestrator (`main.py`):**
    -   **Class:** `MainOrchestrator`
    -   **Function:** `run_pipeline(start_date, end_date)`
    -   **Responsibility:** Manages the entire data generation process. It uses a `ProcessPoolExecutor` to run individual calculator modules in parallel, maximizing efficiency. It takes a date range as input and coordinates the generation of all required data files.

-   **Astronomical Calculators (`lunisolar-python/*.py`):**
    -   Each module focuses on a specific type of calculation (e.g., `moon_phases.py`, `solar_terms.py`, `celestial_events.py`).
    -   **Naming Convention:** Functions are named `calculate_<data_type>(...)`, e.g., `calculate_moon_phases()`.
    -   **Input:** Each function takes a start and end `datetime` object.
    -   **Output:** Returns a list of data points (e.g., tuples or data classes).
    -   **Core Dependency:** They all rely on the `skyfield` library and the NASA JPL DE440 ephemeris data (`nasa/de440.bsp`).

-   **Data Writer (`utils.py`):**
    -   **Function:** `write_static_json(file_path, data)`
    -   **Responsibility:** Takes the processed data from the calculators and writes it to optimized, static JSON files.

### 1.3. Data Flow

1.  The `main.py` orchestrator is executed with a specified date range (e.g., 1900-2100).
2.  It invokes the various `calculate_*` functions in parallel.
3.  Each calculator loads the `de440.bsp` ephemeris data and computes its specific events within the given date range.
4.  The results are returned to the orchestrator.
5.  The orchestrator passes the data to the `write_static_json` utility.
6.  The utility writes the data into chunked JSON files in the `output/` directory.

### 1.4. Output: Static JSON Data

To ensure the TypeScript package can lazy-load data efficiently, the pipeline will not generate a single monolithic JSON file. Instead, it will chunk the data, typically by year.

-   **Directory Structure:** `output/{data_type}/{year}.json`
    -   `output/solar_terms/2025.json`
    -   `output/new_moons/2025.json`
-   **Format:** The JSON files will contain arrays of timestamps or simple data objects, optimized for minimum file size.
    -   **Example (`new_moons/2025.json`):**
        ```json
        [
          1738163213, // Unix timestamp for new moon in seconds
          1740755273,
          ...
        ]
        ```

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

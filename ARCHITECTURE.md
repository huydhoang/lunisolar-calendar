# Architecture

This document describes the architecture of the **Lunisolar-TS** project — a multi-component system consisting of a **Python data pipeline** for high-precision astronomical calculations, **WebAssembly modules** for calendar conversion, and an **npm package** (`lunisolar-wasm`) for distribution.

---

## System Overview

```mermaid
graph LR
    subgraph Python Pipeline
        A[NASA JPL DE440<br/>Ephemeris] --> B[Skyfield Engine]
        B --> C[Calculator Modules]
        C --> D[JSON Output<br/>by year]
    end

    subgraph TypeScript Package
        D --> E[DataLoader<br/>CDN / static / fs]
        E --> F[LunisolarCalendar]
        F --> G[Huangdao Systems]
    end

    G --> H[Consumer App]
```

The Python pipeline pre-computes astronomical events (moon phases, solar terms) from NASA ephemeris data and writes them as year-chunked JSON files. The TypeScript package lazy-loads those files at runtime and exposes a high-level calendar conversion and auspicious-day API.

---

## Python Data Pipeline

### Module Dependency Graph

```mermaid
graph TD
    CFG[config.py<br/>Constants & paths] --> UTIL[utils.py<br/>Logging, CSV/JSON I/O]
    CFG --> MP[moon_phases.py]
    CFG --> ST[solar_terms.py]
    CFG --> CE[celestial_events.py]
    CFG --> MI[moon_illumination.py]
    CFG --> TD_MOD[tidal_data.py]

    UTIL --> MP
    UTIL --> ST
    UTIL --> CE
    UTIL --> MI
    UTIL --> TD_MOD

    MP --> MAIN[main.py<br/>Orchestrator]
    ST --> MAIN

    MP --> LS[lunisolar_v2.py<br/>Calendar Engine]
    ST --> LS
    TZ[timezone_handler.py] --> LS

    LS --> HD[huangdao_systems_v2.py<br/>Auspicious Days]
    ST --> HD
    TZ --> HD

    CE --> AT[antitransit.py]
```

### Orchestrator (`data/main.py`)

The orchestrator coordinates parallel computation and writes year-grouped JSON:

```python
# Parallel task submission (from main.py)
with ProcessPoolExecutor(max_workers=min(NUM_PROCESSES, 2)) as executor:
    futures = {
        executor.submit(calculate_moon_phases, start_time, end_time): "moon_phases",
        executor.submit(calculate_solar_terms, start_time, end_time): "solar_terms",
    }
```

Results are grouped by year and written to a directory tree:

```
output/json/
├── new_moons/
│   ├── 2024.json     # [unix_timestamp, ...]
│   └── 2025.json
├── full_moons/
│   ├── 2024.json
│   └── 2025.json
└── solar_terms/
    ├── 2024.json     # [[timestamp, index], ...]
    └── 2025.json
```

### Calculator Modules

Each module follows a consistent pattern — accept a date range, load the ephemeris, and return structured results:

```python
# Example: moon_phases.py
def calculate_moon_phases(start_time, end_time):
    ts = load.timescale()
    eph = load(EPHEMERIS_FILE)       # nasa/de440.bsp
    t0, t1 = ts.from_datetime(start_time), ts.from_datetime(end_time)
    t, y = almanac.find_discrete(t0, t1, almanac.moon_phases(eph))
    results = []
    for ti, yi in zip(t, y):
        if yi in (0, 2):             # New Moon or Full Moon only
            unix_timestamp = int(ti.utc_datetime().timestamp())
            results.append((unix_timestamp, yi, almanac.MOON_PHASES[yi]))
    return results
```

| Module | Output | Interval |
|--------|--------|----------|
| `moon_phases.py` | New/Full Moon timestamps | Per event |
| `solar_terms.py` | 24 solar term timestamps + indices | Per event |
| `moon_illumination.py` | Illumination percentage | Every 2 hours |
| `celestial_events.py` | Rise/set/transit for Sun, Moon, planets | Per event |
| `tidal_data.py` | Tidal acceleration vectors + lunar mansion | Every 4 minutes |

### Lunisolar Calendar Engine (`data/lunisolar_v2.py`)

The core conversion engine is decomposed into nine service classes, each with a single responsibility:

```mermaid
graph TD
    INPUT["solar_to_lunisolar(date, time, tz)"]
    WP[WindowPlanner<br/>±30-day ephemeris window]
    ES[EphemerisService<br/>New moons + principal terms]
    MB[MonthBuilder<br/>MonthPeriod list from new moons]
    TI[TermIndexer<br/>Map terms → months via CST dates]
    LMA[LeapMonthAssigner<br/>No-zhongqi rule]
    LMR[LunarMonthResolver<br/>Match target date to month]
    SE[SexagenaryEngine<br/>Stem-branch cycles]
    RA[ResultAssembler<br/>LunisolarDateDTO]

    INPUT --> WP --> ES --> MB --> TI --> LMA --> LMR --> SE --> RA
```

**Key design decisions:**

- **CST date-only comparisons** — month boundaries are compared using CST calendar dates, not UTC instants, matching traditional practice.
- **No-zhongqi rule** — a lunar month that contains no principal solar term (中氣) becomes the leap month.
- **Continuous day count** — the day cycle uses an unbroken count from the reference date 4 AD (Jiazi day), not month-relative offsets.
- **Wu Shu Dun (五鼠遁)** — hour stems are derived from the day stem using the traditional mapping rule.

### Huangdao Systems (`data/huangdao_systems_v2.py`)

Implements two traditional Chinese auspicious day systems:

```mermaid
graph LR
    subgraph Input
        DATE[Solar Date]
    end

    DATE --> LS2[LunisolarCalendar<br/>batch conversion]
    LS2 --> CS[ConstructionStars<br/>12 stars, sequential cycle]
    LS2 --> GYP[GreatYellowPath<br/>12 spirits, monthly rotation]

    CS --> OUT[Day Info:<br/>star + spirit + scores]
    GYP --> OUT
```

| System | Cycle | Key Rule |
|--------|-------|----------|
| 12 Construction Stars (十二建星) | Sequential 12-day | On solar term days, repeat the previous day's star |
| Great Yellow Path (大黄道) | Monthly spirit rotation | Azure Dragon start position rotates by lunar month |

---

## TypeScript NPM Package (`archive/pkg-ts/`) — Archived

### Package Structure

```mermaid
graph TD
    IDX[index.ts<br/>Public API]
    CFG_TS[config.ts<br/>Strategy config]
    TYPES[types.ts<br/>TLunisolarDate, etc.]
    DL[data/DataLoader.ts<br/>Lazy-loading + cache]
    MAN[data/manifest.ts<br/>Static import map]
    TZH[timezone/TimezoneHandler.ts<br/>Intl-based conversion]
    LC[core/LunisolarCalendar.ts<br/>Gregorian → Lunisolar]
    CS_TS[huangdao/ConstructionStars.ts]
    GYP_TS[huangdao/GreatYellowPath.ts]

    IDX --> CFG_TS
    IDX --> TYPES
    IDX --> DL
    IDX --> TZH
    IDX --> LC
    IDX --> CS_TS
    IDX --> GYP_TS

    DL --> CFG_TS
    DL --> MAN
    LC --> DL
    LC --> TZH
    CS_TS --> LC
    GYP_TS --> LC
```

### Data Loading Strategy

The `DataLoader` supports three strategies to work across runtimes (browser, Node.js, serverless edge):

```mermaid
graph TD
    REQ["getNewMoons(year)"]
    CACHE{In cache?}
    REQ --> CACHE
    CACHE -- Yes --> RET[Return cached]
    CACHE -- No --> STRAT{Strategy?}
    STRAT -- fetch --> CDN["fetch() from jsDelivr CDN<br/>version-pinned URL"]
    STRAT -- static --> IMP["Static import() via manifest.ts"]
    STRAT -- relative baseUrl --> FS["Node.js fs.readFile()"]
    CDN --> STORE[Cache & return]
    IMP --> STORE
    FS --> STORE
```

Configuration:

```typescript
import { configure } from 'lunisolar-ts';

// Default: version-pinned CDN fetch
configure({ strategy: 'fetch' });

// Bundler-friendly static imports
configure({ strategy: 'static' });

// Custom CDN or self-hosted endpoint
configure({ strategy: 'fetch', data: { baseUrl: 'https://my-cdn.com/data' } });
```

### Core Calendar Conversion (`pkg/src/core/LunisolarCalendar.ts`)

The TypeScript implementation mirrors the Python engine's service architecture:

```typescript
// Public API
const cal = await LunisolarCalendar.fromSolarDate(new Date('2025-02-15'), 'Asia/Shanghai');
cal.lunarYear;   // 2025
cal.lunarMonth;  // 1
cal.lunarDay;    // 18
cal.yearStem;    // '乙'
cal.yearBranch;  // '巳'
cal.dayStem;     // '壬'
cal.dayBranch;   // '辰'
```

Internally it:

1. Loads new moon timestamps and solar terms for the relevant years via `DataLoader`.
2. Builds `MonthPeriod` objects from consecutive new moon pairs.
3. Maps principal solar terms to months using CST date-only boundaries.
4. Applies the no-zhongqi leap month rule.
5. Computes sexagenary (Gan-Zhi) cycles for year, month, day, and hour.

### Build & Distribution

```mermaid
graph LR
    SRC[src/*.ts] --> ROLLUP[Rollup + TypeScript]
    ROLLUP --> CJS[dist/index.cjs]
    ROLLUP --> ESM[dist/index.mjs]
    ROLLUP --> DTS[dist/index.d.ts]
    DATA[output/json/] --> DIST_DATA[dist/data/]
    DIST_DATA --> CDN[jsDelivr CDN]
```

The package ships as dual CJS/ESM with zero runtime dependencies (only `tslib`). Pre-computed JSON data files are served from jsDelivr CDN by default.

---

## Data Flow: End to End

```mermaid
sequenceDiagram
    participant Eph as NASA DE440 Ephemeris
    participant Py as Python Pipeline
    participant JSON as JSON Files (by year)
    participant DL as TypeScript DataLoader
    participant Cal as LunisolarCalendar
    participant App as Consumer Application

    Py->>Eph: Load ephemeris
    Py->>Py: calculate_moon_phases()
    Py->>Py: calculate_solar_terms()
    Py->>JSON: Write year-chunked data

    App->>Cal: fromSolarDate(date, timezone)
    Cal->>DL: getNewMoons(year), getSolarTerms(year)
    DL->>JSON: Fetch / import / read
    DL-->>Cal: Cached astronomical data
    Cal-->>App: LunisolarCalendar instance
    App->>App: Access lunar date, Gan-Zhi, auspicious info
```

---

## Directory Layout

```
lunisolar-ts/
├── archive/                    # Archived implementations
│   └── pkg-ts/                 # Previous TypeScript npm package (lunisolar-ts)
├── data/                       # Python data pipeline
│   ├── config.py               # Shared constants (ephemeris path, physics, location)
│   ├── utils.py                # Logging, CSV/JSON I/O, argument parsing
│   ├── timezone_handler.py     # IANA timezone conversions (pytz)
│   ├── main.py                 # Orchestrator — parallel task runner
│   ├── moon_phases.py          # New/Full Moon calculator
│   ├── solar_terms.py          # 24 solar terms calculator
│   ├── moon_illumination.py    # Moon illumination percentage
│   ├── celestial_events.py     # Rise/set/transit events
│   ├── antitransit.py          # Antitransit helper
│   ├── tidal_data.py           # Tidal acceleration & lunar mansions
│   ├── lunisolar_v2.py         # Core lunisolar calendar engine (9 services)
│   └── huangdao_systems_v2.py  # Auspicious day systems
├── pkg/                        # Main npm package (lunisolar-wasm, Emscripten)
│   ├── package.json            # npm package metadata
│   └── README.md               # Package documentation
├── vendor/                     # Shared third-party source code
│   └── swisseph/               # Swiss Ephemeris C source (v2.10.03)
├── wasm/                       # WebAssembly implementations
│   ├── lunisolar/              # Rust wasm-pack port
│   ├── lunisolar-emcc/         # Emscripten C source (builds to pkg/)
│   └── swisseph/               # Swiss Ephemeris Rust + wasm-bindgen bindings
├── tests/                      # Integration tests
│   ├── lunisolar-wasm/         # Accuracy & benchmark tests
│   └── swisseph-wasm/          # Swiss Ephemeris accuracy & benchmark tests
├── docs/                       # Detailed documentation
├── nasa/                       # JPL ephemeris data files
│   └── de440.bsp
├── output/                     # Generated data (git-ignored)
│   └── json/
└── requirements.txt            # Python dependencies
```

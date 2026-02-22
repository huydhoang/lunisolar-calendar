# Architecture

This document describes the architecture of the **Lunisolar-TS** project — a multi-component system consisting of a **Python data pipeline** for high-precision astronomical calculations, **WebAssembly modules** for calendar conversion (with integrated Swiss Ephemeris), and an **npm package** (`lunisolar-wasm`) for distribution.

---

## System Overview

```mermaid
graph LR
    subgraph Python Pipeline
        A[NASA JPL DE440<br/>Ephemeris] --> B[Skyfield Engine]
        B --> C[Calculator Modules]
        C --> D[CSV Output<br/>by year]
    end

    subgraph WASM Modules
        SE[Swiss Ephemeris<br/>vendor/swisseph/] --> RS[lunisolar-rs<br/>Rust + wasm-bindgen]
        SE --> EMCC[lunisolar-emcc<br/>Emscripten C→WASM]
        SE --> SRS[swisseph-rs<br/>SE bindings]
    end

    RS --> PKG[npm package<br/>lunisolar-wasm]
    EMCC --> PKG

    subgraph TypeScript Port
        E[DataLoader<br/>CDN / static / fs]
        E --> F[LunisolarCalendar TS]
    end

    PKG --> H[Consumer App]
```

The Python pipeline pre-computes astronomical events (moon phases, solar terms) from NASA ephemeris data and writes them as year-chunked JSON files. The WASM modules use the Swiss Ephemeris (with embedded `.se1` data files) for fully standalone calendar conversion — no pre-computed data required.

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

### Orchestrator (`lunisolar-python/main.py`)

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
output/
├── new_moons/
│   ├── 2024.csv     # unix_timestamp per line
│   └── 2025.csv
├── full_moons/
│   ├── 2024.csv
│   └── 2025.csv
└── solar_terms/
    ├── 2024.csv     # timestamp,index per line
    └── 2025.csv
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

### Lunisolar Calendar Engine (`lunisolar-python/lunisolar_v2.py`)

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

### Huangdao Systems (`lunisolar-python/huangdao_systems_v2.py`)

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

## WebAssembly Modules (`ports/`)

The project has three WASM implementations, all using the vendored Swiss Ephemeris C source (`vendor/swisseph/`) with embedded `.se1` data files for fully standalone operation.

### Package Naming Convention

| Directory | Language | Build Toolchain | Description |
|-----------|----------|-----------------|-------------|
| `ports/lunisolar-rs/` | Rust | wasm-pack / wasm-bindgen | Lunisolar calendar in Rust |
| `ports/lunisolar-emcc/` | C | Emscripten / emcc | Lunisolar calendar in C |
| `ports/swisseph-rs/` | Rust | wasm-pack / wasm-bindgen | Swiss Ephemeris bindings |

### `lunisolar-rs/` — Rust WASM Port

```mermaid
graph TD
    subgraph "lunisolar-rs (lib.rs)"
        ENTRY_AUTO["#wasm_bindgen<br/>fromSolarDateAuto(tsMs, tzOffsetSec)"]
        ENTRY_PRE["#wasm_bindgen<br/>fromSolarDate(tsMs, tzOffsetSec, newMoonsJson, solarTermsJson)"]

        CORE["from_solar_date_core()"]

        subgraph "Calendar Logic"
            DATE["Date helpers<br/>civil_from_days / days_from_civil<br/>utc_ms_to_date_parts / cst_date_of"]
            MONTH["Month Period Builder<br/>MonthPeriod[] from new moon pairs"]
            TERMS["Term Indexer<br/>PrincipalTerm[] → tag periods"]
            Z11["Z11 Anchor + Leap Rule<br/>Winter Solstice → Zi month<br/>no-zhongqi leap assignment"]
            RESOLVE["Lunar Month Resolver<br/>target CST date → period"]
            GZ["Sexagenary Engine<br/>year / month / day / hour ganzhi"]
            HD["Huangdao<br/>Construction Stars + Great Yellow Path"]
        end

        RESULT["LunisolarResult → JSON"]
    end

    subgraph "ephemeris.rs"
        NM["compute_new_moons(start, end)<br/>1-day elongation scan + bisection"]
        ST["compute_solar_terms(start, end)<br/>1-day Sun longitude scan + bisection"]
    end

    subgraph "swisseph-rs crate (dependency)"
        FFI["swe_bindings FFI<br/>swe_calc_ut · swe_julday"]
        SE1["Embedded .se1 data<br/>sepl_18.se1 · semo_18.se1"]
        SHIMS["C stdlib shims<br/>malloc · fopen · sin · …"]
    end

    subgraph "vendor/swisseph/"
        CSRC["SE C source (v2.10)<br/>sweph.c · swecl.c · …<br/>compiled via cc crate"]
    end

    ENTRY_AUTO --> NM
    ENTRY_AUTO --> ST
    NM --> FFI
    ST --> FFI
    FFI --> CSRC
    FFI --> SE1
    CSRC --> SHIMS

    NM --> CORE
    ST --> CORE
    ENTRY_PRE --> CORE

    CORE --> DATE
    DATE --> MONTH
    MONTH --> TERMS
    TERMS --> Z11
    Z11 --> RESOLVE
    RESOLVE --> GZ
    GZ --> HD
    HD --> RESULT
```

The Rust port depends on `swisseph-rs` as a path dependency:

```toml
[dependencies]
swisseph-wasm = { path = "../swisseph-rs" }
```

Exported JS functions:
- `fromSolarDate(tsMs, tzOffsetSec, newMoonsJson, solarTermsJson)` — accepts pre-computed data (for benchmark compatibility)
- `fromSolarDateAuto(tsMs, tzOffsetSec)` — **standalone**: computes everything internally via Swiss Ephemeris

### `lunisolar-emcc/` — Emscripten C Port

```mermaid
graph TD
    subgraph "lunisolar-emcc (lunisolar.c)"
        ENTRY_AUTO_C["EMSCRIPTEN_KEEPALIVE<br/>from_solar_date_auto(tsMs, tzOffsetSec,<br/>outBuf, outBufLen)"]
        ENTRY_PRE_C["EMSCRIPTEN_KEEPALIVE<br/>from_solar_date(tsMs, tzOffsetSec,<br/>nmPtr, nmCount, stTsPtr, stIdxPtr, stCount,<br/>outBuf, outBufLen)"]

        subgraph "Calendar Logic (C)"
            DATE_C["Date helpers<br/>civil_from_days / days_from_civil<br/>utc_ms_to_date_parts / cst_date_of"]
            MONTH_C["Month Period Builder<br/>MonthPeriod[] from new moon pairs"]
            TERMS_C["Term Indexer<br/>PrincipalTerm[] → tag periods"]
            Z11_C["Z11 Anchor + Leap Rule<br/>Winter Solstice → Zi month<br/>no-zhongqi leap assignment"]
            RESOLVE_C["Lunar Month Resolver<br/>target CST date → period"]
            GZ_C["Sexagenary Engine<br/>year / month / day / hour ganzhi"]
            HD_C["Huangdao<br/>Construction Stars + Great Yellow Path"]
        end

        JSON_C["snprintf() → JSON string in outBuf"]
    end

    subgraph "ephemeris.c / ephemeris.h"
        NM_C["compute_new_moons(start, end,<br/>outTs, maxCount)<br/>1-day elongation scan + bisection"]
        ST_C["compute_solar_terms(start, end,<br/>outTs, outIdx, maxCount)<br/>1-day Sun longitude scan + bisection"]
        INIT_C["ephe_init() → swe_set_ephe_path('/ephe')"]
        CLOSE_C["ephe_close() → swe_close()"]
    end

    subgraph "vendor/swisseph/ (compiled by emcc)"
        CSRC_C["SE C source (v2.10)<br/>sweph.c · swecl.c · …<br/>9 files linked by build.sh"]
    end

    subgraph "Embedded data (--embed-file)"
        SE1_C["sepl_18.se1 → /ephe/sepl_18.se1<br/>semo_18.se1 → /ephe/semo_18.se1"]
    end

    ENTRY_AUTO_C --> INIT_C
    ENTRY_AUTO_C --> NM_C
    ENTRY_AUTO_C --> ST_C
    ENTRY_AUTO_C --> CLOSE_C
    NM_C --> CSRC_C
    ST_C --> CSRC_C
    CSRC_C --> SE1_C

    NM_C --> ENTRY_PRE_C
    ST_C --> ENTRY_PRE_C
    ENTRY_AUTO_C --> ENTRY_PRE_C

    ENTRY_PRE_C --> DATE_C
    DATE_C --> MONTH_C
    MONTH_C --> TERMS_C
    TERMS_C --> Z11_C
    Z11_C --> RESOLVE_C
    RESOLVE_C --> GZ_C
    GZ_C --> HD_C
    HD_C --> JSON_C
```

Built by `build.sh`, which compiles the calendar C code plus all 9 SE C files from `vendor/swisseph/` and embeds `.se1` data via `--embed-file`:

```bash
emcc lunisolar.c ephemeris.c "${SWE_SRCS[@]}" \
  -I"$SWE_DIR" \
  --embed-file "$EPHE_DIR/sepl_18.se1@/ephe/sepl_18.se1" \
  --embed-file "$EPHE_DIR/semo_18.se1@/ephe/semo_18.se1" \
  -o "$OUT_DIR/lunisolar_emcc.mjs"
```

Exported C functions:
- `from_solar_date(...)` — accepts pre-computed data via WASM heap pointers
- `from_solar_date_auto(tsMs, tzOffsetSec, outBuf, outBufLen)` — **standalone**: computes everything internally

### `swisseph-rs/` — Swiss Ephemeris Bindings

```mermaid
graph TD
    subgraph "swisseph-rs (lib.rs)"
        subgraph "WASM Exports (#wasm_bindgen)"
            JS_CALC["swe_calc_ut(jd, ipl, iflag)<br/>→ Vec&lt;f64&gt; [lon, lat, dist, ...]"]
            JS_JUL["swe_julday(y, m, d, h, greg)<br/>→ f64"]
            JS_REV["swe_revjul(jd, greg)<br/>→ {year, month, day, hour}"]
            JS_NAME["swe_get_planet_name(ipl)<br/>→ String"]
            JS_CONST["SE_SUN · SE_MOON · SE_GREG_CAL<br/>SEFLG_SWIEPH · SEFLG_SPEED"]
        end

        subgraph "FFI Layer (bindings.rs)"
            BIND["#link(name = 'swe') extern 'C'<br/>impl_swe_calc_ut<br/>impl_swe_julday<br/>impl_swe_revjul<br/>impl_swe_get_planet_name"]
        end

        subgraph "C stdlib shims (mod shims)"
            MATH["Math via libm<br/>sin · cos · atan2 · sqrt · …"]
            MEM["Allocator<br/>malloc · free · calloc · realloc"]
            STR["String ops<br/>strlen · strcmp · strcpy · strcat · …"]
            FS["In-memory filesystem<br/>fopen · fread · fseek · ftell · fclose"]
            MISC["Stubs<br/>time · getenv · exit · dlopen · stat · …"]
        end

        subgraph "Embedded data"
            SE1_RS["include_bytes!<br/>sepl_18.se1 · semo_18.se1"]
        end
    end

    subgraph "build.rs (cc crate)"
        BUILD["Compiles 9 SE C files<br/>with symbol renaming<br/>(swe_calc_ut → impl_swe_calc_ut)<br/>and wasm32 target flags"]
    end

    subgraph "vendor/swisseph/"
        VENDOR_C["SE C source (v2.10)<br/>sweph.c · swedate.c · swecl.c<br/>swehouse.c · swejpl.c · swehel.c<br/>swemmoon.c · swemplan.c · swephlib.c"]
    end

    JS_CALC --> BIND
    JS_JUL --> BIND
    JS_REV --> BIND
    JS_NAME --> BIND

    BIND --> BUILD
    BUILD --> VENDOR_C
    VENDOR_C --> MATH
    VENDOR_C --> MEM
    VENDOR_C --> STR
    VENDOR_C --> FS
    VENDOR_C --> MISC
    FS --> SE1_RS
```

Provides low-level SE function access via Rust FFI with wasm-bindgen:
- Compiles SE C source via `cc` crate (`build.rs`)
- Renames C symbols to avoid collision with wasm-bindgen exports
- Provides in-memory filesystem shims (`fopen`/`fread`/`fseek`) for embedded `.se1` data
- Exports `swe_calc_ut`, `swe_julday`, `swe_revjul`, `swe_get_planet_name` to JS

### npm Package (`pkg/`)

The Emscripten-based `lunisolar-wasm` package is published to npm:

```json
{
  "name": "lunisolar-wasm",
  "main": "lunisolar_emcc.mjs",
  "files": ["lunisolar_emcc.mjs", "lunisolar_emcc.wasm", "README.md"]
}
```

Usage:
```js
import createLunisolarEmcc from 'lunisolar-wasm';
const mod = await createLunisolarEmcc();

const outPtr = mod._malloc(1024);
const n = mod._from_solar_date_auto(Date.now(), 28800, outPtr, 1024);
if (n > 0) console.log(JSON.parse(mod.UTF8ToString(outPtr, n)));
mod._free(outPtr);
```

---

## TypeScript NPM Package (`ports/lunisolar-ts/`)

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
    DATA[pre-computed data] --> DIST_DATA[dist/data/]
    DIST_DATA --> CDN[jsDelivr CDN]
```

The package ships as dual CJS/ESM with zero runtime dependencies (only `tslib`). Pre-computed JSON data files are served from jsDelivr CDN by default.

---

## Data Flow: End to End

```mermaid
sequenceDiagram
    participant SE as Swiss Ephemeris<br/>(embedded .se1)
    participant WASM as WASM Module
    participant App as Consumer Application

    App->>WASM: fromSolarDateAuto(timestamp, tzOffset)
    WASM->>SE: swe_calc_ut() — Sun/Moon positions
    WASM->>WASM: Compute new moons (elongation scan)
    WASM->>WASM: Compute solar terms (longitude scan)
    WASM->>WASM: Build month periods, apply leap rule
    WASM->>WASM: Compute Gan-Zhi cycles + Huangdao
    WASM-->>App: JSON result
```

For the archived TypeScript path (requires pre-computed data):

```mermaid
sequenceDiagram
    participant Eph as NASA DE440 Ephemeris
    participant Py as Python Pipeline
    participant Data as Data Files (by year)
    participant DL as TypeScript DataLoader
    participant Cal as LunisolarCalendar
    participant App as Consumer Application

    Py->>Eph: Load ephemeris
    Py->>Py: calculate_moon_phases()
    Py->>Py: calculate_solar_terms()
    Py->>Data: Write year-chunked data

    App->>Cal: fromSolarDate(date, timezone)
    Cal->>DL: getNewMoons(year), getSolarTerms(year)
    DL->>Data: Fetch / import / read
    DL-->>Cal: Cached astronomical data
    Cal-->>App: LunisolarCalendar instance
```

---

## Directory Layout

```
lunisolar-ts/
├── ports/                      # All language ports
│   ├── lunisolar-ts/           # TypeScript npm package (lunisolar-ts)
│   ├── lunisolar-rs/           # Rust wasm-pack port (standalone with SE)
│   │   ├── Cargo.toml          # Depends on swisseph-wasm
│   │   └── src/
│   │       ├── lib.rs          # Calendar logic + fromSolarDateAuto()
│   │       └── ephemeris.rs    # SE-based new moon / solar term computation
│   ├── lunisolar-emcc/         # Emscripten C source (builds to pkg/)
│   │   ├── build.sh            # Compiles C + SE + embeds .se1 data
│   │   ├── lunisolar.c         # Calendar logic + from_solar_date_auto()
│   │   ├── ephemeris.c         # SE-based new moon / solar term computation
│   │   └── ephemeris.h
│   └── swisseph-rs/            # Swiss Ephemeris Rust + wasm-bindgen bindings
│       ├── Cargo.toml
│       ├── build.rs            # Compiles SE C source via cc crate
│       ├── ephe/               # Embedded .se1 ephemeris data files
│       └── src/
│           ├── lib.rs          # WASM exports + C stdlib shims + in-memory FS
│           └── bindings.rs     # FFI bindings to SE C functions
├── lunisolar-python/           # Python data pipeline
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
├── tests/                      # Integration tests
│   ├── lunisolar-wasm/         # Accuracy & benchmark tests
│   └── swisseph-wasm/          # Swiss Ephemeris accuracy & benchmark tests
├── docs/                       # Detailed documentation
├── nasa/                       # JPL ephemeris data files
│   └── de440.bsp
├── output/                     # Generated data (git-ignored)
└── requirements.txt            # Python dependencies
```

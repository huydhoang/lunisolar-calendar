# WASM Specification — Lunisolar-TS

> Replace the legacy Python → JSON → DataLoader pipeline with real-time astronomical calculations using `swisseph-wasm` (Swiss Ephemeris compiled to WebAssembly), coordinated by a Rust WASM module for lunisolar calendar logic. Deploy as a self-contained set of files in a web app's `/public` directory for client-side, offline, multi-threaded computation.

---

## 1. Goals

| Goal | Description |
|------|-------------|
| **Eliminate the data pipeline** | Replace the Python pre-computation step and static JSON data files with on-demand planetary position calculations via `swisseph-wasm`. No more `output/json/`, no CDN, no `DataLoader`. |
| **Single deployment** | Ship a small set of files (Rust WASM + swisseph-wasm WASM + JS glue) into `/public`. No server-side code required. |
| **Offline operation** | `swisseph-wasm` embeds its own ephemeris data inside the WASM binary. The module works without any network access. |
| **Multi-threaded performance** | Leverage WebAssembly threads, `SharedArrayBuffer`, and Web Workers so batch calculations (e.g. an entire month of auspicious days) use multiple CPU cores. |
| **API parity** | Expose the same public surface as the current TypeScript package: `fromSolarDate`, `ConstructionStars.calculateMonth`, `GreatYellowPath.getSpirit`. |

---

## 2. Why `swisseph-wasm`

The [swisseph-wasm](https://github.com/prolaxu/swisseph-wasm) package wraps the Swiss Ephemeris C library (compiled to WASM via Emscripten). It provides professional-grade astronomical calculations with:

- **High precision** — based on the Swiss Ephemeris, used by professional astronomers and astrologers worldwide.
- **Self-contained** — the WASM binary and ephemeris data files are embedded; zero network dependencies.
- **Cross-platform** — works in browsers (Chrome 61+, Firefox 60+, Safari 11+, Edge 16+) and Node.js.
- **Rich API** — `calc_ut()` for planetary positions, `julday()` for Julian Day conversion, `revjul()` for reverse, sidereal time, eclipse calculations, and more.

### Key Functions for Lunisolar Calculations

| Swiss Ephemeris function | Purpose in lunisolar context |
|--------------------------|------------------------------|
| `swe.calc_ut(jd, SE_SUN, SEFLG_SWIEPH)` | Sun ecliptic longitude → derive solar terms (every 15° of solar longitude) |
| `swe.calc_ut(jd, SE_MOON, SEFLG_SWIEPH)` | Moon ecliptic longitude → detect new/full moons (Sun–Moon angle 0°/180°) |
| `swe.julday(y, m, d, h)` | Gregorian → Julian Day Number |
| `swe.revjul(jd, SE_GREG_CAL)` | Julian Day → Gregorian date components |

### How It Replaces the Python Pipeline

```mermaid
graph LR
    subgraph "Legacy Pipeline (removed)"
        A[NASA DE440<br/>Ephemeris] --> B[Python / Skyfield]
        B --> C[JSON files<br/>by year]
        C --> D[DataLoader<br/>fetch / import / fs]
    end

    subgraph "New: swisseph-wasm"
        E[Swiss Ephemeris<br/>WASM binary] --> F["calc_ut(jd, planet)"]
        F --> G[Sun/Moon longitude<br/>at any instant]
    end

    style A fill:#fee,stroke:#c00
    style B fill:#fee,stroke:#c00
    style C fill:#fee,stroke:#c00
    style D fill:#fee,stroke:#c00
    style E fill:#efe,stroke:#0a0
    style F fill:#efe,stroke:#0a0
    style G fill:#efe,stroke:#0a0
```

Instead of pre-computing moon phases and solar terms for 201 years and shipping ~2.4 MB of JSON, we call `swisseph-wasm` at runtime to calculate the exact Sun and Moon longitudes for any date on demand.

---

## 3. Integration Strategy: Integrate vs Fork

### Option A — Integrate as a JS-level Dependency (Recommended)

| Aspect | Details |
|--------|---------|
| Method | `npm install swisseph-wasm`; import and call from the JS coordination layer |
| WASM modules | Two: `swisseph.wasm` (ephemeris engine) + `lunisolar_wasm_bg.wasm` (calendar logic) |
| Separation | Clear boundary — swisseph-wasm owns ephemeris; Rust WASM owns calendar/Ganzhi/huangdao |
| Upstream updates | Free via `npm update`; bug fixes and ephemeris improvements come automatically |
| Maintenance | Low — only maintain the lunisolar calendar logic and the thin JS coordination layer |

### Option B — Fork / Extract Code

| Aspect | Details |
|--------|---------|
| Method | Fork the `swisseph-wasm` repo, or use a Rust FFI crate like [`libswe-sys`](https://github.com/stephaneworkspace/libswe-sys) (11 ★) to call the Swiss Ephemeris C library directly from Rust |
| WASM modules | Could merge into a single binary by compiling Swiss Ephemeris C source alongside Rust via `cc` crate and `libswe-sys` FFI bindings |
| Separation | Tightly coupled — must maintain C FFI bindings and keep ephemeris data (~12 MB) in sync |
| Upstream updates | Manual — must cherry-pick or rebase from upstream for every Swiss Ephemeris update |
| Maintenance | High — own the full C→WASM compilation pipeline plus Rust FFI |

### Recommendation

**Option A (integrate)** is strongly recommended:

1. `swisseph-wasm` already solves the hard problem (compiling Swiss Ephemeris C to WASM with embedded data).
2. The lunisolar calendar logic (~350 LOC) is a thin layer on top of ephemeris queries — it doesn't need to live in the same binary.
3. Forking creates a maintenance burden for keeping the C ephemeris code in sync with upstream bug fixes.
4. Both WASM modules load in parallel and the total size is comparable to a single merged binary.
5. The GPL-3.0 license of `swisseph-wasm` is compatible with using it as a dependency.

---

## 4. Architecture

### 4.1 System Overview

```mermaid
graph TD
    subgraph "/public directory"
        SW_WASM["swisseph.wasm<br/>+ swisseph.js<br/>(Swiss Ephemeris)"]
        LW_WASM["lunisolar_wasm_bg.wasm<br/>+ lunisolar_wasm.js<br/>(Calendar Logic)"]
        COORD["lunisolar-coordinator.js<br/>(JS orchestration layer)"]
    end

    subgraph "Browser Runtime"
        APP[Web App] -->|"import { initLunisolar }"| COORD
        COORD -->|"await swe.initSwissEph()"| SW_WASM
        COORD -->|"await init()"| LW_WASM
        SW_WASM -->|"calc_ut(jd, SE_SUN)"| EPH_DATA[Sun/Moon Longitudes]
        EPH_DATA --> LW_WASM
        LW_WASM -->|"from_solar_date()"| RESULT[LunisolarDate<br/>+ Ganzhi + Stars + Spirits]
        RESULT --> APP
    end
```

### 4.2 Data Flow: Calculating a Lunisolar Date

```mermaid
sequenceDiagram
    participant App as Web App
    participant Coord as Coordinator (JS)
    participant SWE as swisseph-wasm
    participant LW as lunisolar-wasm (Rust)

    App->>Coord: fromSolarDate("2025-06-15", "Asia/Shanghai")
    Coord->>Coord: resolve tz_offset_minutes = 480

    Note over Coord: Step 1: Find new moons around target date
    Coord->>SWE: julday(2025, 5, 1, 0)
    SWE-->>Coord: jd_start
    loop Binary search for each new moon
        Coord->>SWE: calc_ut(jd, SE_SUN, SEFLG_SWIEPH)
        SWE-->>Coord: sun_longitude
        Coord->>SWE: calc_ut(jd, SE_MOON, SEFLG_SWIEPH)
        SWE-->>Coord: moon_longitude
        Note over Coord: New moon when<br/>moon_lon == sun_lon (±tolerance)
    end
    Coord->>Coord: Collect new moon JDs for surrounding months

    Note over Coord: Step 2: Find solar terms (principal zhongqi)
    loop For each 30° boundary of solar longitude
        Coord->>SWE: calc_ut(jd, SE_SUN, SEFLG_SWIEPH)
        SWE-->>Coord: sun_longitude
        Note over Coord: Solar term when sun_lon<br/>crosses 0°, 30°, 60°, ..., 330°
    end
    Coord->>Coord: Collect principal term timestamps

    Note over Coord: Step 3: Calendar conversion + Ganzhi
    Coord->>LW: from_solar_date(new_moons[], solar_terms[], unix_ms, tz_offset)
    LW->>LW: Build month periods
    LW->>LW: Apply no-zhongqi leap month rule
    LW->>LW: Compute sexagenary cycles
    LW-->>Coord: LunisolarDate { lunar_year, month, day, stems, branches }
    Coord-->>App: result
```

### 4.3 Ephemeris Calculation: Finding New Moons

The key insight: a **new moon** occurs when the Sun and Moon have the same ecliptic longitude. We find this by iterating with binary search:

```javascript
// coordinator: find_new_moon.js
async function findNewMoon(swe, jdStart) {
  // Average synodic month ≈ 29.53059 days
  const SYNODIC = 29.53059;
  let jd = jdStart;

  // Coarse search: step by 1 day until Sun–Moon angle crosses 0°
  let prevDiff = sunMoonDiff(swe, jd);
  for (let i = 0; i < 35; i++) {
    jd += 1.0;
    const diff = sunMoonDiff(swe, jd);
    if (prevDiff > 180 && diff < 180) {
      // Crossed 360°→0° boundary — new moon is between jd-1 and jd
      return bisectNewMoon(swe, jd - 1, jd);
    }
    prevDiff = diff;
  }
  return null;
}

function sunMoonDiff(swe, jd) {
  const sunPos = swe.calc_ut(jd, swe.SE_SUN, swe.SEFLG_SWIEPH);
  const moonPos = swe.calc_ut(jd, swe.SE_MOON, swe.SEFLG_SWIEPH);
  let diff = moonPos[0] - sunPos[0];
  if (diff < 0) diff += 360;
  return diff;
}

function bisectNewMoon(swe, jdLo, jdHi) {
  // Binary search to ~1 second precision
  for (let i = 0; i < 30; i++) {
    const jdMid = (jdLo + jdHi) / 2;
    const diff = sunMoonDiff(swe, jdMid);
    if (diff > 180) jdLo = jdMid;  // before conjunction
    else jdHi = jdMid;              // after conjunction
  }
  return (jdLo + jdHi) / 2;
}
```

### 4.4 Ephemeris Calculation: Finding Solar Terms

A **solar term** occurs every time the Sun's ecliptic longitude crosses a multiple of 15°. The 24 solar terms divide the ecliptic into 24 equal segments. **Principal terms** (中氣 zhōngqì) are at multiples of 30°.

```javascript
// coordinator: find_solar_terms.js
async function findSolarTerms(swe, year) {
  const terms = [];
  // Start from winter solstice of previous year (sun_lon ≈ 270°)
  let jd = swe.julday(year - 1, 12, 15, 0);

  for (let targetDeg = 270; terms.length < 30; targetDeg = (targetDeg + 15) % 360) {
    jd = bisectSolarLongitude(swe, jd, targetDeg);
    const termIndex = Math.round(targetDeg / 15); // 0..23
    const isPrincipal = (targetDeg % 30 === 0);
    const date = swe.revjul(jd, swe.SE_GREG_CAL);
    terms.push({ jd, termIndex, isPrincipal, date });
    jd += 14; // advance ~half a term for next search
  }
  return terms;
}

function bisectSolarLongitude(swe, jdStart, targetDeg) {
  // Find when sun longitude crosses targetDeg
  let jdLo = jdStart;
  let jdHi = jdStart + 40; // max ~40 days between terms

  for (let i = 0; i < 50; i++) {
    const jdMid = (jdLo + jdHi) / 2;
    const sunPos = swe.calc_ut(jdMid, swe.SE_SUN, swe.SEFLG_SWIEPH);
    const sunLon = sunPos[0];

    // Handle 360°→0° wraparound
    let diff = sunLon - targetDeg;
    if (diff > 180) diff -= 360;
    if (diff < -180) diff += 360;

    if (diff < 0) jdLo = jdMid;
    else jdHi = jdMid;
  }
  return (jdLo + jdHi) / 2;
}
```

### 4.5 Crate Layout (Rust WASM — Calendar Logic)

The Rust WASM module handles the lunisolar calendar conversion and auspicious day calculations. It receives pre-computed new moon and solar term data from the JS coordinator.

```
wasm/
├── Cargo.toml
├── rust-toolchain.toml          # pin nightly for WASM threads
├── src/
│   ├── lib.rs                   # wasm-bindgen entry points
│   ├── calendar.rs              # LunisolarCalendar logic (month periods, leap month)
│   ├── sexagenary.rs            # Gan-Zhi cycle calculations (year/month/day/hour)
│   ├── construction_stars.rs    # 12 Construction Stars (十二建星)
│   ├── great_yellow_path.rs     # Great Yellow Path spirits (大黄道)
│   └── timezone.rs              # CST offset helper (fixed +8:00)
└── tests/
    └── integration.rs           # parity tests vs TypeScript outputs
```

Note: no `data/` directory — ephemeris data is no longer embedded. The Rust module receives astronomical events as function parameters from the JS coordinator.

### 4.6 Public API (wasm-bindgen Exports)

```rust
// lib.rs
use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub struct LunisolarDate {
    pub lunar_year: i32,
    pub lunar_month: u8,
    pub lunar_day: u8,
    pub is_leap_month: bool,
    pub year_stem: String,
    pub year_branch: String,
    pub month_stem: String,
    pub month_branch: String,
    pub day_stem: String,
    pub day_branch: String,
    pub hour_stem: String,
    pub hour_branch: String,
}

/// Convert a Gregorian date to a lunisolar date.
///
/// `new_moon_jds` — Julian Day numbers of new moons (from swisseph-wasm).
/// `principal_term_jds` — Julian Day numbers of principal solar terms.
/// `principal_term_indices` — corresponding term indices (0..11 for Z1..Z12).
/// `target_jd` — Julian Day of the target date.
/// `tz_offset_minutes` — UTC offset in minutes (e.g. +480 for CST).
#[wasm_bindgen]
pub fn from_solar_date(
    new_moon_jds: &[f64],
    principal_term_jds: &[f64],
    principal_term_indices: &[u8],
    target_jd: f64,
    tz_offset_minutes: i16,
) -> LunisolarDate { .. }

/// Calculate Construction Stars for a month.
/// Returns a JSON string of `[{ day, star_name, score, auspicious }]`.
#[wasm_bindgen]
pub fn calculate_month_stars(
    new_moon_jds: &[f64],
    principal_term_jds: &[f64],
    principal_term_indices: &[u8],
    sectional_term_jds: &[f64],
    year: u16,
    month: u8,
    tz_offset_minutes: i16,
) -> String { .. }

/// Get the Great Yellow Path spirit for a single date.
#[wasm_bindgen]
pub fn get_spirit(lunar_month: u8, day_branch_index: u8) -> String { .. }

/// Initialize the thread pool (must call before parallel APIs).
#[wasm_bindgen]
pub fn init_thread_pool(num_threads: usize) -> js_sys::Promise { .. }

/// Batch-convert multiple dates in parallel (uses rayon par_iter).
#[wasm_bindgen]
pub fn batch_from_solar_date(
    new_moon_jds: &[f64],
    principal_term_jds: &[f64],
    principal_term_indices: &[u8],
    target_jds: &[f64],
    tz_offset_minutes: i16,
) -> String { .. }
```

### 4.7 JavaScript Coordinator

The coordinator is the glue layer that wires `swisseph-wasm` and `lunisolar-wasm` together:

```typescript
// lunisolar-coordinator.ts
import SwissEph from 'swisseph-wasm';
import init, {
  init_thread_pool,
  from_solar_date as _from_solar_date,
  calculate_month_stars as _calculate_month_stars,
  get_spirit as _get_spirit,
  batch_from_solar_date as _batch_from_solar_date,
} from './lunisolar_wasm.js';

let swe: SwissEph | null = null;

export async function initLunisolar(): Promise<void> {
  // Initialize both WASM modules in parallel
  swe = new SwissEph();
  const [_, __] = await Promise.all([
    swe.initSwissEph(),
    init(),
  ]);

  // Optional: initialize thread pool for batch operations
  if (typeof SharedArrayBuffer !== 'undefined') {
    await init_thread_pool(navigator.hardwareConcurrency);
  }
}

export async function fromSolarDate(
  date: Date,
  timezone: string = 'Asia/Shanghai',
): Promise<LunisolarDate> {
  if (!swe) throw new Error('Call initLunisolar() first');

  const tzOffset = getOffsetMinutes(date, timezone);
  const jd = swe.julday(
    date.getUTCFullYear(),
    date.getUTCMonth() + 1,
    date.getUTCDate(),
    date.getUTCHours() + date.getUTCMinutes() / 60,
  );

  // Gather astronomical data around the target date
  const year = date.getFullYear();
  const newMoonJDs = await findNewMoonsForRange(swe, year);
  const solarTerms = await findSolarTerms(swe, year);

  const principalTerms = solarTerms.filter(t => t.isPrincipal);
  const principalJDs = new Float64Array(principalTerms.map(t => t.jd));
  const principalIndices = new Uint8Array(principalTerms.map(t => t.termIndex));

  // Delegate calendar logic to Rust WASM
  return _from_solar_date(
    new Float64Array(newMoonJDs),
    principalJDs,
    principalIndices,
    jd,
    tzOffset,
  );
}

export async function calculateMonthStars(
  year: number,
  month: number,
  timezone: string = 'Asia/Shanghai',
): Promise<DayInfo[]> {
  if (!swe) throw new Error('Call initLunisolar() first');

  const tzOffset = getOffsetMinutes(new Date(year, month - 1, 15), timezone);
  const newMoonJDs = await findNewMoonsForRange(swe, year);
  const solarTerms = await findSolarTerms(swe, year);

  const principalTerms = solarTerms.filter(t => t.isPrincipal);
  const sectionalTerms = solarTerms.filter(t => !t.isPrincipal);

  const json = _calculate_month_stars(
    new Float64Array(newMoonJDs),
    new Float64Array(principalTerms.map(t => t.jd)),
    new Uint8Array(principalTerms.map(t => t.termIndex)),
    new Float64Array(sectionalTerms.map(t => t.jd)),
    year,
    month,
    tzOffset,
  );
  return JSON.parse(json);
}

export function destroy(): void {
  if (swe) { swe.close(); swe = null; }
}
```

**Consumer usage (React / Vue / Svelte):**

```typescript
import { initLunisolar, fromSolarDate, calculateMonthStars, destroy } from './lunisolar-coordinator';

// Call once at app startup
await initLunisolar();

// Convert a date
const result = await fromSolarDate(new Date('2025-06-15'), 'Asia/Shanghai');
console.log(result.lunar_year, result.year_stem + result.year_branch);

// Get auspicious days for a month
const stars = await calculateMonthStars(2025, 6);
const auspicious = stars.filter(d => d.score >= 3);

// Cleanup on unmount
destroy();
```

---

## 5. Threading Model

### 5.1 Overview

```mermaid
sequenceDiagram
    participant Main as Main Thread (JS)
    participant SWE as swisseph-wasm
    participant Pool as Worker Pool (Rust WASM)

    Main->>SWE: initSwissEph()
    Main->>Pool: init() + initThreadPool(N)
    Note over Pool: N Web Workers created,<br/>each loads lunisolar_wasm_bg.wasm<br/>with shared WebAssembly.Memory

    Main->>SWE: findNewMoons() + findSolarTerms()
    SWE-->>Main: astronomical data arrays

    Main->>Pool: batch_from_solar_date(moons[], terms[], dates[], tz)
    Pool->>Pool: rayon par_iter splits calendar<br/>conversion across N workers
    Pool-->>Main: JSON result array
```

### 5.2 Dependencies

- **`wasm-bindgen-rayon`** — adapts Rayon's thread pool to Web Workers with `SharedArrayBuffer`.
- Requires Rust **nightly** toolchain (tracked in `rust-toolchain.toml`).
- RUSTFLAGS: `-C target-feature=+atomics,+bulk-memory,+mutable-globals`

### 5.3 Browser Requirements

Multi-threaded WASM requires the page to be **cross-origin isolated**. The web server must send:

```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

| Browser | Threads support | Notes |
|---------|----------------|-------|
| Chrome 91+ | ✅ | Stable since 2021 |
| Firefox 79+ | ✅ | Stable since 2020 |
| Safari 16.4+ | ✅ | Since macOS Ventura / iOS 16.4 |
| Edge 91+ | ✅ | Chromium-based, same as Chrome |

### 5.4 Graceful Degradation

If `SharedArrayBuffer` is unavailable (missing COOP/COEP headers or older browser), the module falls back to **single-threaded** execution. The `initThreadPool` call becomes a no-op, and all `par_iter` calls degrade to sequential `iter`.

```rust
#[wasm_bindgen]
pub fn init_thread_pool(num_threads: usize) -> js_sys::Promise {
    #[cfg(feature = "parallel")]
    {
        wasm_bindgen_rayon::init_thread_pool(num_threads)
    }
    #[cfg(not(feature = "parallel"))]
    {
        let _ = num_threads;
        js_sys::Promise::resolve(&JsValue::UNDEFINED)
    }
}
```

A feature flag `parallel` controls whether `wasm-bindgen-rayon` is compiled in:

```bash
# Multi-threaded build (default)
wasm-pack build --target web -- --features parallel

# Single-threaded build (fallback / simpler deployment)
wasm-pack build --target web
```

---

## 6. Build Pipeline

### 6.1 Prerequisites

```bash
# Rust nightly with WASM target
rustup toolchain install nightly
rustup target add wasm32-unknown-unknown --toolchain nightly

# wasm-pack
cargo install wasm-pack

# wasm-opt (optional, for size optimization — install Binaryen)
# See https://github.com/WebAssembly/binaryen/releases
# e.g. apt install binaryen, brew install binaryen, or download from GitHub

# swisseph-wasm (JS dependency)
npm install swisseph-wasm
```

### 6.2 Build Commands

```bash
cd wasm/

# Build the Rust calendar logic WASM (multi-threaded, release)
RUSTFLAGS='-C target-feature=+atomics,+bulk-memory,+mutable-globals' \
  wasm-pack build --target web --release -- --features parallel

# Post-process: optimize size
wasm-opt -Oz -o pkg/lunisolar_wasm_bg.wasm pkg/lunisolar_wasm_bg.wasm
```

### 6.3 Output Artifacts

```
wasm/pkg/
├── lunisolar_wasm_bg.wasm       # Calendar logic WASM (~200 KB without embedded data)
├── lunisolar_wasm_bg.wasm.d.ts  # TS types for raw WASM bindings
├── lunisolar_wasm.js            # JS glue (init, thread pool bootstrap)
├── lunisolar_wasm.d.ts          # TS types for public API
├── snippets/                    # Worker bootstrap snippets (for rayon)
└── package.json                 # npm-compatible if publishing
```

### 6.4 Deployment to a Web App

```bash
# 1. Copy Rust WASM output
cp wasm/pkg/lunisolar_wasm_bg.wasm  my-app/public/
cp wasm/pkg/lunisolar_wasm.js       my-app/public/
cp -r wasm/pkg/snippets/            my-app/public/snippets/

# 2. Copy swisseph-wasm files
cp node_modules/swisseph-wasm/src/swisseph.js     my-app/public/
cp node_modules/swisseph-wasm/wsam/swisseph.js    my-app/public/wsam/
cp node_modules/swisseph-wasm/wsam/swisseph.wasm  my-app/public/wsam/
cp node_modules/swisseph-wasm/wsam/swisseph.data  my-app/public/wsam/

# 3. Copy the coordinator
cp lunisolar-coordinator.js  my-app/public/
```

**Resulting `/public` directory:**

```
my-app/public/
├── lunisolar_wasm_bg.wasm       # Rust calendar logic (~200 KB)
├── lunisolar_wasm.js            # Rust WASM JS glue
├── lunisolar-coordinator.js     # Orchestration layer
├── swisseph.js                  # SwissEph JS wrapper
├── wsam/
│   ├── swisseph.js              # Emscripten WASM module loader
│   ├── swisseph.wasm            # Swiss Ephemeris WASM binary (~1 MB)
│   └── swisseph.data            # Ephemeris data file (~11 MB; ~3 MB gzipped)
└── snippets/                    # Rayon worker snippets (if parallel)
```

> **Size note:** The `swisseph-wasm` npm package is ~12.4 MB unpacked (v0.0.4). The bulk is `swisseph.data` (embedded ephemeris tables). With gzip/brotli compression on the web server, the total transfer size is ~3–4 MB.

For frameworks with bundlers (Vite, Next.js), place files in the static/public directory so they are served as-is.

**Vite configuration:**

```javascript
// vite.config.js
export default defineConfig({
  server: { fs: { allow: ['..'] } },
  assetsInclude: ['**/*.wasm', '**/*.data'],
  optimizeDeps: { exclude: ['swisseph-wasm'] },
});
```

---

## 7. Cargo.toml

```toml
[package]
name = "lunisolar-wasm"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
wasm-bindgen = "0.2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
js-sys = "0.3"

[dependencies.rayon]
version = "1"
optional = true

[dependencies.wasm-bindgen-rayon]
version = "1"
optional = true

[features]
default = []
parallel = ["rayon", "wasm-bindgen-rayon"]

[profile.release]
opt-level = "z"      # optimize for size
lto = true
codegen-units = 1
strip = "symbols"
```

Note: `serde` and `serde_json` are still used for serializing results to JSON strings returned to JS. No data files are embedded — the crate is much smaller than the previous spec.

---

## 8. Timezone Handling

The current TypeScript package uses the browser's `Intl.DateTimeFormat` API for full IANA timezone support. In WASM, `Intl` is not directly accessible.

### Strategy

1. **For CST-only use (most common):** Hard-code `+08:00` offset inside WASM. All lunisolar calendar boundaries use CST (China Standard Time) as the reference.
2. **For arbitrary timezones:** Accept a `tz_offset_minutes` parameter from JavaScript. The JS coordinator resolves the IANA timezone to a UTC offset before calling WASM functions.

```javascript
// JS side: resolve timezone offset for a given instant
function getOffsetMinutes(date, iana) {
  const fmt = (tz) => new Intl.DateTimeFormat('en-US', {
    timeZone: tz, year: 'numeric', month: 'numeric', day: 'numeric',
    hour: 'numeric', minute: 'numeric', second: 'numeric', hour12: false
  });
  const toParts = (tz) => {
    const p = Object.fromEntries(
      fmt(tz).formatToParts(date).map(({ type, value }) => [type, Number(value)])
    );
    return Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second);
  };
  return (toParts(iana) - toParts('UTC')) / 60000;
}
```

---

## 9. Testing Strategy

### 9.1 Parity Tests

Generate a golden dataset from the existing TypeScript package for a set of reference dates, then assert that the new swisseph-wasm + Rust WASM pipeline produces identical results.

```
Reference dates (minimum set):
- 2025-01-29 (Chinese New Year, Year of the Snake)
- 2025-02-15 (mid-month, leap month edge case test)
- 2023-03-22 (leap month 2 in 2023)
- 1900-01-31 (earliest supported date)
- 2100-12-31 (latest supported date)
- 2024-02-10 (Chinese New Year 2024)
- Each hour boundary for sexagenary hour tests (23:00 Zi hour rule)
```

### 9.2 Ephemeris Accuracy Tests

Verify that `swisseph-wasm` produces moon/sun positions consistent with the pre-computed Python pipeline data:

```javascript
// Compare swisseph-wasm new moon detection with legacy JSON data
const legacyNewMoons2025 = [1738154158, 1740703489, ...]; // from output/json/new_moons/2025.json
const sweNewMoons2025 = await findNewMoonsForYear(swe, 2025);

for (let i = 0; i < legacyNewMoons2025.length; i++) {
  const legacyJD = legacyNewMoons2025[i] / 86400 + 2440587.5;
  const sweJD = sweNewMoons2025[i];
  assert(Math.abs(legacyJD - sweJD) < 0.001); // within ~86 seconds
}
```

### 9.3 Rust Unit Tests

```bash
cd wasm/
cargo test                       # native tests (no WASM)
wasm-pack test --headless --chrome  # browser-based WASM tests
```

### 9.4 Browser Integration Tests

Use Playwright or similar to:
1. Serve both WASM modules from a local server with COOP/COEP headers.
2. Load the coordinator, call each API function, and assert outputs.
3. Verify thread pool initialization and parallel batch processing.

---

## 10. Performance Targets

| Operation | Single-threaded target | Multi-threaded target (4 cores) |
|-----------|----------------------|-------------------------------|
| `fromSolarDate` (single date) | < 5 ms | N/A (overhead not worth it) |
| `calculateMonthStars` (31 days) | < 50 ms | < 15 ms |
| `batch_from_solar_date` (365 days) | < 500 ms | < 150 ms |
| Module init (both WASM) | < 200 ms | < 200 ms |
| `findNewMoons` (13 moons/year) | < 20 ms | N/A |
| `findSolarTerms` (24 terms/year) | < 30 ms | N/A |

> Note: Performance targets are higher than the previous spec because ephemeris calculations are now done at runtime instead of using pre-computed data. The trade-off is eliminating the Python pipeline and ~2.4 MB of static data.

---

## 11. Migration Path

### Phase 1 — Standalone WASM module (this spec)
- Build `lunisolar-wasm` crate + coordinator alongside the existing `pkg/` TypeScript package.
- Both can coexist: apps choose WASM+swisseph for offline/client-side, TS package for server/Node/CDN.
- Validate parity between the new swisseph-based calculations and legacy pre-computed data.

### Phase 2 — Unified package (future)
- Publish `lunisolar-wasm` + coordinator as an npm package with swisseph-wasm bundled.
- Add a `configure({ strategy: 'wasm' })` option to the existing TypeScript package that delegates to the WASM modules.

### Phase 3 — Deprecate the Python pipeline (future)
- Once the swisseph-wasm approach is validated, deprecate `data/main.py` and the JSON output pipeline.
- The Rust WASM + swisseph-wasm becomes the primary implementation.
- Keep the TS package as a thin wrapper that either uses the WASM backend or falls back to legacy JSON data.

---

## 12. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| COOP/COEP headers not set by hosting provider | Multi-threading fails | Graceful fallback to single-threaded; document header requirements |
| Rust nightly required for WASM threads | Build reproducibility | Pin exact nightly in `rust-toolchain.toml`; consider stable once `target-feature` stabilizes |
| Two WASM modules to load | Slightly longer init | Load both in parallel via `Promise.all`; total transfer ~3–4 MB gzipped |
| swisseph-wasm upstream changes | API breakage | Pin npm version; integration tests catch regressions |
| GPL-3.0 license of swisseph-wasm | Copyleft for derivative works | Evaluate if commercial license from Astrodienst AG is needed; lunisolar-wasm is a separate work that calls swisseph-wasm via JS API (not a derivative) |
| Runtime ephemeris calculation is slower than pre-computed lookup | Higher per-call latency | Cache computed new moons/solar terms per year in the coordinator; first call ~20 ms, subsequent calls instant |
| IANA timezone resolution in JS | Slight API difference vs current TS package | Thin JS coordinator wraps timezone resolution transparently |

---

## 13. References

### Swiss Ephemeris / swisseph-wasm

- [swisseph-wasm — GitHub](https://github.com/prolaxu/swisseph-wasm) — JavaScript wrapper for Swiss Ephemeris WASM
- [swisseph-wasm — Documentation](https://github.com/prolaxu/swisseph-wasm/blob/main/DOCUMENTATION.md) — Full API reference
- [swisseph-wasm — Quick Reference](https://github.com/prolaxu/swisseph-wasm/blob/main/QUICK_REFERENCE.md) — Developer cheat sheet
- [Swiss Ephemeris — Astrodienst](https://www.astro.com/swisseph/) — Original C library and commercial licensing
- [swisseph-wasm — Live Demo](https://prolaxu.github.io/swisseph-wasm/examples/demo.html) — Interactive browser demo

### WebAssembly & Rust

- [MDN: Compiling Rust to WebAssembly](https://developer.mozilla.org/en-US/docs/WebAssembly/Guides/Rust_to_Wasm)
- [Rust and WebAssembly Book](https://rustwasm.github.io/docs/book/)
- [wasm-pack documentation](https://rustwasm.github.io/docs/wasm-pack/)
- [wasm-bindgen guide](https://rustwasm.github.io/docs/wasm-bindgen/)

### Multi-Threading in WASM

- [web.dev: WebAssembly Threads](https://web.dev/articles/webassembly-threads)
- [wasm-bindgen-rayon (GitHub)](https://github.com/RReverser/wasm-bindgen-rayon)
- [wasm-bindgen-rayon (docs.rs)](https://docs.rs/wasm-bindgen-rayon)
- [Parallel Raytracing example — wasm-bindgen guide](https://rustwasm.github.io/docs/wasm-bindgen/examples/raytrace.html)

### Cross-Origin Isolation (COOP/COEP)

- [web.dev: Making your website cross-origin isolated](https://web.dev/articles/coop-coep)
- [MDN: SharedArrayBuffer](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer)

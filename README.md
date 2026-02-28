# Lunisolar Calendar

## Project Overview

A comprehensive, high-precision astronomical and astrological calculator focused on the traditional Chinese lunisolar calendar. The project includes:

1. **Python Data Pipeline** (`lunisolar-python/`) — Generates high-precision astronomical data (moon phases, solar terms, planetary events) using NASA's JPL DE440 ephemeris via Skyfield.
2. **WebAssembly Modules** (`ports/`) — Three WASM implementations, all integrating with the Swiss Ephemeris for standalone operation:
   - **`lunisolar-rs/`** — Rust port using wasm-pack / wasm-bindgen (depends on `swisseph-rs`)
   - **`lunisolar-emcc/`** — C port using Emscripten / emcc (main package, published to npm)
   - **`swisseph-rs/`** — Swiss Ephemeris Rust bindings (vendored C source + embedded `.se1` data)
3. **npm Package** (`pkg/`) — The Emscripten-based `lunisolar-wasm` package published to npmjs
4. **TypeScript Port** (`ports/lunisolar-ts/`) — TypeScript npm package (`lunisolar-ts`)

### Core Features

- **Lunisolar Calendar Conversion:** Gregorian → lunisolar dates with Heavenly Stems and Earthly Branches (Gan-Zhi)
- **Auspicious Day Calculation:** "Twelve Construction Stars" (十二建星) and "Great Yellow Path" (大黄道)
- **Standalone Operation:** Both WASM ports compute new moons and solar terms internally via Swiss Ephemeris — no pre-computed data needed
- **Astronomical Data Generation:** Moon phases, solar terms, planetary events, tidal forces (Python pipeline)

### Project Structure

```
lunisolar-ts/
├── ports/                   # All language ports
│   ├── lunisolar-ts/        # TypeScript npm package
│   ├── lunisolar-rs/        # Rust WASM port (standalone with SE via swisseph-rs)
│   ├── lunisolar-emcc/      # C WASM port (standalone with SE, builds to pkg/)
│   └── swisseph-rs/         # Swiss Ephemeris Rust bindings + embedded .se1
├── lunisolar-python/        # Python data pipeline
├── docs/                    # Documentation
├── nasa/                    # JPL ephemeris data
├── output/                  # Generated data (CSV)
├── pkg/                     # npm package (lunisolar-wasm, Emscripten)
├── tests/                   # Integration tests
├── vendor/swisseph/         # Shared Swiss Ephemeris C source (v2.10)
└── ports/                   # WebAssembly implementations
```

## Building and Running

### Virtual Environment

```bash
uv venv --python 3.12
Using CPython 3.12.9
Creating virtual environment at: .venv
Activate with: source .venv/Scripts/activate
```

### Dependencies

Install all Python dependencies into the venv:

```powershell
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

```bash
# macOS / Linux
source .venv/bin/activate
uv pip install -r requirements.txt
```

`requirements.txt` contains: `skyfield pytz rich InquirerPy pytest`

### Running the Python Implementation

All commands below assume the venv is active and cwd is `lunisolar-python/`.

#### Lunisolar calendar conversion

```bash
python -m lunisolar --date 2025-06-15
python -m lunisolar --date 2025-06-15 --time 08:30 --tz Asia/Shanghai
```

Outputs the full Gregorian → lunisolar conversion with year/month/day/hour ganzhi in the sexagenary cycle.

#### Auspicious days calendar (Huangdao systems)

```bash
python -m huangdao -y 2025 -m 6
python -m huangdao -y 2025 -m 6 --timezone Asia/Shanghai
```

Prints a monthly table combining the **12 Construction Stars** (十二建星) and the **Great Yellow Path** (大黄道).

#### Bazi (Four Pillars) analysis

```bash
python -m bazi --date 1990-05-15 --time 08:00 --tz Asia/Shanghai
```

#### Bulk data generation

```bash
python main.py --start-date 2025-01-01 --end-date 2025-12-31
```

Generates CSV files for moon phases, solar terms, and celestial events into `output/`.

#### Tests

```bash
python -m pytest test_lunisolar_v2.py test_bazi.py -v
```

Expected: **179 tests pass** (9 lunisolar + 170 bazi).

## Development Conventions

- **Modularity:** Code is organised into focused packages (`lunisolar/`, `huangdao/`, `bazi/`, `ephemeris/`, `shared/`). Top-level `.py` files are backward-compatible facades.
- **Shared constants:** All packages import from `shared/constants.py` and `shared/models.py` — no local copies of stems/branches/terms.
- **Configuration:** `config.py` holds the output directory and ephemeris path. All paths are relative to the repo root.
- **Logging:** `utils.setup_logging()` returns a standard Python logger. It never calls `sys.stdout.reconfigure()`, making it safe under pytest capture.
- **Data-Driven:** All astronomical calculations use NASA JPL DE440 via Skyfield (`nasa/de440.bsp`).
- **Documentation:** The `docs/` directory explains the traditional calendar rules, Huangdao systems, and architecture in depth.

## Key Files

- `lunisolar-python/lunisolar/` — Lunisolar calendar engine package. Public API: `lunisolar.api.solar_to_lunisolar()`. Entry point: `python -m lunisolar`.
- `lunisolar-python/huangdao/` — Auspicious-day systems (12 Construction Stars + Great Yellow Path). Entry point: `python -m huangdao`.
- `lunisolar-python/bazi/` — Four Pillars (Bazi) analysis package. Entry point: `python -m bazi`.
- `lunisolar-python/shared/` — Canonical constants (`HEAVENLY_STEMS`, `EARTHLY_BRANCHES`, …) and dataclasses (`LunisolarDateDTO`) shared across all packages.
- `lunisolar-python/ephemeris/` — Low-level Skyfield wrappers for solar terms and moon phases.
- `lunisolar-python/lunisolar_v2.py` — Backward-compatible facade → `lunisolar` package.
- `lunisolar-python/huangdao_systems_v2.py` — Backward-compatible facade → `huangdao` package.
- `lunisolar-python/config.py` — Shared configuration (output directory, ephemeris path).
- `docs/architecture.md` — Full package architecture and data-flow diagrams.
- `nasa/de440.bsp` — NASA JPL DE440 ephemeris (core data source for all astronomical calculations).

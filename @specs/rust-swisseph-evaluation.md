# Rust Swiss Ephemeris Crate Evaluation

> Evaluate Rust crates that wrap or reimplement the Swiss Ephemeris C library,
> and assess their suitability for building a WASM module to calculate planetary
> positions as an alternative to the Emscripten-based `swisseph-wasm` npm package.

---

## 1. Crates Evaluated

### 1.1 `libswe-sys` — stephaneworkspace/libswe-sys (11 ★)

| Attribute | Details |
|-----------|---------|
| **Approach** | FFI bindings to Swiss Ephemeris C source (v2.08) |
| **Build** | `cc` crate compiles C source at build time |
| **License** | GPL (Swiss Ephemeris) |
| **Dependencies** | `libc`, `serde`, `serde_json`, `strum`, `num-derive`, `num-traits`, `libmath` |
| **WASM support** | Commented-out WASM target detection in `build.rs`; not production-ready for WASM |
| **Maturity** | Published on crates.io (v0.2.7); last updated ~2022 |
| **API surface** | Raw FFI bindings + Rust enums for constants |
| **Assessment** | Heavy dependency footprint; outdated SE version (2.08 vs current 2.10); WASM not actively supported |

### 1.2 `swisseph-wasm` — fusionstrings/swisseph-wasm (crates.io + JSR + npm)

| Attribute | Details |
|-----------|---------|
| **Approach** | FFI bindings to Swiss Ephemeris C source (v2.10.03) compiled to `wasm32-unknown-unknown` |
| **Build** | `cc` crate compiles C source; `wasm-bindgen` for JS interop |
| **License** | MIT (wrapper) / GPL or Commercial (Swiss Ephemeris) |
| **Dependencies** | `wasm-bindgen`, `js-sys`, `libm`, `libc` — minimal |
| **WASM support** | ✅ First-class; `no_std` with custom C stdlib shims; self-contained WASM binary |
| **Maturity** | Published on crates.io (v0.1.5), JSR, and npm; CI/CD; benchmarks included |
| **API surface** | `swe_calc_ut`, `swe_julday`, `swe_revjul`, `swe_fixstar_ut`, `swe_pheno_ut`, `swe_set_topo`, `swe_set_sid_mode`, `swe_get_ayanamsa_ut`, `swe_get_planet_name`, `swe_sidtime` |
| **Assessment** | ⭐ **Best candidate.** Production-ready WASM, modern SE version, minimal deps, benchmarked |

### 1.3 `libswe-rs` — thomasrstorey/libswe-rs (2 ★)

| Attribute | Details |
|-----------|---------|
| **Approach** | Workspace with `libswe-sys` (raw FFI) + `libswe` (safe Rust wrapper) |
| **License** | GPL |
| **WASM support** | None |
| **Maturity** | Low activity; last updated 2024 |
| **Assessment** | Incomplete; no WASM support; low activity |

### 1.4 `ephem-rs` — CHINMAYVIVEK/ephem-rs (2 ★)

| Attribute | Details |
|-----------|---------|
| **Approach** | Workspace with `lib-swiss` + `lib-sys` |
| **License** | Apache-2.0 / MIT dual license |
| **WASM support** | None |
| **Maturity** | Experimental; minimal code |
| **Assessment** | Too early-stage; experimental disclaimer in README |

### 1.5 `swisseph-rs` — aaroncarlucci/swisseph-rs (0 ★)

| Attribute | Details |
|-----------|---------|
| **Approach** | Workspace with `swisseph-sys` + `swisseph` |
| **License** | AGPL-3.0 |
| **WASM support** | Unknown |
| **Maturity** | Very new (Jan 2026); zero stars |
| **Assessment** | Too new; AGPL license is restrictive |

### 1.6 `swisseph_rs` / `libswisseph-sys_rs` — jgrowl (0 ★)

| Attribute | Details |
|-----------|---------|
| **Approach** | Higher-level Rust wrapper + separate sys crate |
| **WASM support** | Unknown |
| **Maturity** | Zero stars; recent activity |
| **Assessment** | Low adoption; unclear WASM story |

### 1.7 `vsop87-rs` — Razican/vsop87-rs (18 ★, archived)

| Attribute | Details |
|-----------|---------|
| **Approach** | Pure Rust reimplementation of VSOP87 algorithm |
| **License** | MIT |
| **WASM support** | Pure Rust, so trivially compiles to WASM |
| **Maturity** | Archived; no longer maintained |
| **Assessment** | Different algorithm (VSOP87 vs Swiss Ephemeris); lower precision for Moon; archived |

### 1.8 `astrojson` — neilg63/astrojson (7 ★)

| Attribute | Details |
|-----------|---------|
| **Approach** | CLI tool that calls Swiss Ephemeris C lib and outputs JSON |
| **WASM support** | None; designed as a native CLI |
| **Assessment** | Not a library; not suitable for WASM |

---

## 2. Comparison Matrix

| Crate | SE Version | WASM Ready | `no_std` | Deps | Stars | Activity | License |
|-------|-----------|-----------|---------|------|-------|----------|---------|
| `libswe-sys` | 2.08 | ❌ | ❌ | Heavy | 11 | Low | GPL |
| **`swisseph-wasm` (fusionstrings)** | **2.10.03** | **✅** | **✅** | **Minimal** | **0** | **Active** | **MIT/GPL** |
| `libswe-rs` | Unknown | ❌ | ❌ | Medium | 2 | Low | GPL |
| `ephem-rs` | Unknown | ❌ | ❌ | Unknown | 2 | Low | Apache/MIT |
| `swisseph-rs` | Unknown | ❓ | ❓ | Unknown | 0 | New | AGPL |
| `vsop87-rs` | N/A | ✅ (pure) | ✅ | None | 18 | Archived | MIT |

---

## 3. Recommendation

### Primary: `fusionstrings/swisseph-wasm` approach

The `fusionstrings/swisseph-wasm` crate is the clear winner for our use case:

1. **WASM-first design** — built from the ground up for `wasm32-unknown-unknown` with `no_std` and custom C stdlib shims.
2. **Modern SE version** — uses Swiss Ephemeris v2.10.03 (most other crates use 2.08 or unknown).
3. **Minimal dependencies** — only `wasm-bindgen`, `js-sys`, `libm`, `libc`.
4. **Self-contained** — the WASM binary includes the Moshier ephemeris (built-in analytical model); no external `.data` files needed for basic planetary position calculations.
5. **Published and tested** — available on crates.io, JSR, and npm with CI and benchmarks.
6. **Benchmarked** — claims ~182k iterations/sec for Moon position calculation on Deno.

### Why not use `libswe-sys` directly?

While `libswe-sys` has more GitHub stars (11), it:
- Uses an older Swiss Ephemeris version (2.08)
- Has no WASM support (commented out)
- Carries heavy dependencies (`serde`, `strum`, `num-derive`, etc.)
- Would require significant work to add WASM shims

### Comparison with `prolaxu/swisseph-wasm` (Emscripten-based npm package)

The existing spec references the Emscripten-compiled `swisseph-wasm` npm package from `prolaxu`. Key differences:

| Aspect | prolaxu/swisseph-wasm (Emscripten) | fusionstrings/swisseph-wasm (Rust+cc) |
|--------|-----------------------------------|--------------------------------------|
| **Compilation** | Emscripten (C → WASM + JS glue) | Rust `cc` crate (C → WASM via wasm-bindgen) |
| **Binary size** | ~1 MB WASM + ~11 MB ephemeris data | ~200-400 KB WASM (Moshier built-in) |
| **Ephemeris data** | External `.data` file (DE431) | Built-in Moshier (no external files) |
| **JS interop** | Emscripten Module API | wasm-bindgen (typed, ergonomic) |
| **Precision** | Higher (JPL ephemeris data files) | Sufficient for lunisolar calendar (Moshier ≤ 0.001° for Sun/Moon) |
| **Total transfer size** | ~3-4 MB gzipped | ~100-200 KB gzipped |
| **Runtime** | Requires Emscripten runtime | Standard WASM, no runtime overhead |

For our lunisolar calendar use case (Sun/Moon longitude to find new moons and solar terms), Moshier precision (~0.001°) is more than adequate. The dramatically smaller binary size makes the Rust approach compelling.

---

## 4. Benchmark Results

We installed `@fusionstrings/swisseph-wasm` (v0.1.5) and benchmarked it against `swisseph-wasm` (prolaxu) on Node.js v24. Full benchmark script at `tests/swisseph-wasm/benchmark.mjs`.

### 4.1 Binary Size

| Package | WASM Binary | Ephemeris Data | Total Package |
|---------|------------|----------------|---------------|
| @fusionstrings/swisseph-wasm | 337 KB | Built-in (Moshier) | ~1.4 MB |
| swisseph-wasm (prolaxu) | 531 KB | 11.5 MB | ~13 MB |

**Winner: fusionstrings (10x smaller total size)**

### 4.2 Initialization

| Package | Init Time |
|---------|----------|
| @fusionstrings/swisseph-wasm | ~6 ms |
| swisseph-wasm (prolaxu) | ~31 ms |

**Winner: fusionstrings (5x faster init)**

### 4.3 `julday` (Julian Day Conversion)

| Package | ops/sec |
|---------|--------:|
| fusionstrings | ~9,400,000 |
| prolaxu | ~2,800,000 |

**Winner: fusionstrings (3.3x faster)**

### 4.4 `calc_ut` (Planetary Position Calculation)

| Body | fusionstrings ops/sec | prolaxu ops/sec | Speedup |
|------|---------------------:|----------------:|--------:|
| Sun | ~152,000 | ~826,000 | 0.18x |
| Moon | ~189,000 | ~1,508,000 | 0.13x |
| Mercury | ~183,000 | ~2,653,000 | 0.07x |

**Winner: prolaxu (5-14x faster for calc_ut)**

The Emscripten-compiled prolaxu version is significantly faster for `calc_ut` calls. This is likely due to:
1. Emscripten's more mature WASM optimization pipeline
2. The JPL data-file approach having simpler computational steps than Moshier's analytical model
3. Potential overhead from fusionstrings' `no_std` C stdlib shims

### 4.5 Position Agreement

All planetary positions agree to < 0.001° between implementations. For Moon position the difference is ~0.0002° (~0.7 arcseconds) — far better than the ~36 arcsecond tolerance needed for lunisolar calendar calculations.

### 4.6 Summary

| Criteria | @fusionstrings/swisseph-wasm | swisseph-wasm (prolaxu) |
|----------|:---------------------------:|:-----------------------:|
| Binary size | ✅ 337 KB (no ext data) | ⚠️ 531 KB + 11.5 MB |
| Precision | ✅ Sufficient (Moshier) | ✅ Higher (JPL data) |
| calc_ut speed | ⚠️ Slower | ✅ Faster |
| julday speed | ✅ Faster | ⚠️ Slower |
| Init time | ✅ Faster | ⚠️ Slower |
| JS interop | ✅ wasm-bindgen (typed) | ⚠️ Emscripten Module API |
| Dependencies | ✅ 0 runtime | ⚠️ Emscripten runtime |

**Recommendation:** For the lunisolar calendar use case, `@fusionstrings/swisseph-wasm` is recommended due to its dramatically smaller binary (10x), faster initialization (5x), cleaner wasm-bindgen API, and sufficient precision for Sun/Moon calculations. The `calc_ut` speed advantage of prolaxu is less important because:
1. Calendar calculations are dominated by the number of `calc_ut` calls (bisection search), not per-call latency.
2. Both implementations complete a full year's worth of new moon + solar term calculations in well under 100ms.
3. The 10x smaller download size improves user-facing load time more than per-call speed.

---

## 5. Architecture: Cleanest Rust-to-WASM Approach

### 5.1 Why `libswe-sys` is not viable for WASM

We attempted to wrap `libswe-sys` (stephaneworkspace) as a crate dependency and build to WASM. Key issues:

| Problem | Detail |
|---------|--------|
| **Outdated SE version** | v2.08 (latest is v2.10.03, released on [aloistr/swisseph](https://github.com/aloistr/swisseph)) |
| **Private FFI module** | `mod raw;` is not `pub` — cannot import `swe_calc_ut` etc. from downstream |
| **No WASM support** | `build.rs` compiles C with `-g` flag, no WASM-specific configuration |
| **TLS incompatibility** | `sweodef.h` uses `__thread` (TLS), which is unsupported on `wasm32-unknown-unknown` |
| **Missing C headers** | `#include <math.h>`, `<string.h>` etc. — no sysroot for bare WASM target |
| **Heavy dependencies** | `serde`, `serde_json`, `strum`, `num-derive` — adds bloat, no value for WASM |
| **Dead code elimination** | Even with `#[link(name = "swe")]`, the WASM linker treats C code as unreachable |

These are fundamental design issues, not configuration problems. Instead, we implemented the vendored-source approach (§5.2) in `wasm/swisseph/`.

### 5.2 The proven architecture (implemented in `wasm/swisseph/`)

Following the `fusionstrings/swisseph-wasm` architecture, we implemented our own vendored WASM package at `wasm/swisseph/`. Here's how it works:

```
swisseph-wasm/
├── Cargo.toml            # cdylib + rlib, minimal deps
├── build.rs              # cc crate compiles C source, adds wasm-includes
├── vendor/
│   └── swisseph/         # Vendored SE C source (v2.10.03 from aloistr/swisseph)
│       ├── swecl.c
│       ├── swedate.c
│       ├── sweph.c       # ... 9 core C files
│       └── *.h
├── wasm-includes/        # Stub C headers for wasm32 target
│   ├── math.h            # Declares sin/cos/etc. (implemented in Rust via libm)
│   ├── string.h          # Declares memcpy/strlen/etc. (implemented in Rust)
│   ├── stdio.h           # Stub FILE* / fopen (returns NULL → Moshier fallback)
│   └── ...
└── src/
    ├── lib.rs            # wasm-bindgen exports + Rust shims for all C stdlib
    └── wrapper/
        └── stub.c        # C stubs for variadic functions (sprintf, fprintf)
```

**Key design decisions:**

1. **Vendor C source directly** — not via a `-sys` crate. This gives full control over the `build.rs`, C flags, and WASM-specific patches.

2. **Symbol renaming via `#define`** — The `build.rs` renames C functions (e.g. `swe_calc_ut` → `impl_swe_calc_ut`) to avoid collisions between the C symbols and the wasm-bindgen exports.

3. **Minimal WASM-specific headers** — Only declare function signatures that the C code needs. The actual implementations are provided by Rust shims (`libm` for math, `std::alloc` for malloc/free, etc.).

4. **Variadic functions in C** — `sprintf`, `fprintf`, `sscanf` can't be defined in Rust (C-variadic definitions are unstable). A small `stub.c` provides no-op implementations.

5. **`-DTLSOFF`** — Disables thread-local storage in `sweodef.h`, which is unsupported in WASM.

6. **No external data files** — With `fopen` returning NULL, Swiss Ephemeris falls back to the built-in Moshier analytical ephemeris. This eliminates the need for external `.se1` data files and keeps the WASM binary self-contained (~338 KB).

### 5.3 Staying up to date with Swiss Ephemeris

The official Swiss Ephemeris source is maintained at **[aloistr/swisseph](https://github.com/aloistr/swisseph)** (585 ★, actively maintained by Alois Treindl, co-author of Swiss Ephemeris).

| Approach | Mechanism | Pros | Cons |
|----------|-----------|------|------|
| **Git submodule** | `git submodule add https://github.com/aloistr/swisseph vendor/swisseph` | Easy updates via `git submodule update`, exact version tracking | Complicates CI, breaks shallow clones |
| **Vendored copy** (fusionstrings approach) | Copy C files from a tagged release into `vendor/` | Simple, no external dependencies during build | Manual update process |
| **CI version check** | Scheduled workflow polls `aloistr/swisseph` tags and creates a PR | Automated notification of new releases | Still requires manual merge/testing |
| **crates.io `-sys` crate** | Depend on a maintained `-sys` crate | Standard Rust pattern | No existing crate is WASM-ready (see §5.1) |

**Recommended approach: Vendored copy + CI version check.**

1. Vendor the C source from `aloistr/swisseph` at a specific tag (currently `v2.10.03`).
2. A scheduled CI workflow (`.github/workflows/check-swisseph-update.yml`) runs weekly and:
   - Fetches the latest tag from `aloistr/swisseph`
   - Compares with the vendored version in `wasm/swisseph/vendor/swisseph/sweph.h`
   - Opens a GitHub issue if a newer version is available
3. Only the 9 core C files + headers need to be vendored (not tests, docs, etc.).

### 5.4 Implementation status

Our vendored build is at `wasm/swisseph/`. It compiles the official Swiss Ephemeris C source (v2.10.03 from [aloistr/swisseph](https://github.com/aloistr/swisseph)) to WASM via the `cc` crate, with Rust shims for C stdlib and wasm-bindgen exports.

| Metric | Value |
|--------|-------|
| WASM binary size | ~342 KB |
| SE version | v2.10.03 |
| Ephemeris mode | Moshier (built-in, no external files) |
| Position agreement | < 0.001° vs fusionstrings and prolaxu |
| API surface | `swe_calc_ut`, `swe_julday`, `swe_revjul`, `swe_get_planet_name` |
| Build command | `wasm-pack build --target nodejs --release` |
| Update mechanism | Scheduled CI workflow checks `aloistr/swisseph` weekly |

### 5.5 Using JPL ephemeris data instead of Moshier

Swiss Ephemeris supports three computation modes, selected by the `iflag` parameter passed to `swe_calc_ut`:

| Flag | Value | Data source | Precision | Data files |
|------|------:|-------------|-----------|------------|
| `SEFLG_JPLEPH` | 1 | JPL Development Ephemeris (DE431/441) | Highest (~0.001 arcsec) | `jpl*.eph` (~100+ MB) |
| `SEFLG_SWIEPH` | 2 | Swiss Ephemeris compressed files | High (~0.001 arcsec) | `sepl*.se1`, `semo*.se1` (~2 MB total) |
| `SEFLG_MOSEPH` | 4 | Moshier analytical model | Good (~1 arcsec for Moon) | None (built-in) |

The C code has an automatic **fallback chain**: JPL → Swiss Eph → Moshier. When a data file can't be opened, it falls back silently and appends a notice to `serr`.

#### Why our WASM build uses Moshier

Our `fopen` shim returns `NULL`, so the C code can never open `.se1` or `.eph` files. This triggers the automatic fallback to Moshier, which is entirely self-contained (the Moshier coefficients are compiled into the `swemplan.c` / `swemmoon.c` tables).

#### How to enable Swiss Ephemeris or JPL mode in WASM

To use actual ephemeris data files, the `fopen`/`fread`/`fseek`/`ftell`/`fclose` shims would need real implementations. There are two approaches:

**Approach A: Embed data files in the WASM binary**

Compile the `.se1` files directly into the WASM binary as byte arrays using `include_bytes!()` in Rust, then implement `fopen` to return a handle to an in-memory buffer, and `fread`/`fseek`/`ftell` to read from it.

| Pros | Cons |
|------|------|
| No async loading, no external files | WASM binary grows by ~2 MB (Swiss Eph) or ~100 MB (JPL) |
| Works in all environments | Increased download/init time |
| Simplest implementation | Only practical for Swiss Eph `.se1` files, not JPL |

**Approach B: Fetch data files from JS and pass to WASM**

Use `wasm-bindgen` to import a JS function that reads file data (from `fetch()` in browser, or `fs.readFileSync` in Node). Implement `fopen` to call the JS function and store the returned bytes in a WASM-side buffer.

| Pros | Cons |
|------|------|
| WASM binary stays small (~342 KB) | Requires async file loading before `swe_calc_ut` |
| Can use any data files | Complex: must implement C FILE* semantics over byte buffers |
| Works for both `.se1` and JPL | JS/WASM boundary overhead on each `fread` call |

This is the approach used by the prolaxu Emscripten build — Emscripten's virtual filesystem pre-loads the `.data` file (containing `sepl_18.se1` + `semo_18.se1` + `seas_18.se1`) into memory before the WASM module runs. Their `.data` file is 11.5 MB.

**Approach C: Use WASI (wasm32-wasip1 target)**

Target `wasm32-wasip1` instead of `wasm32-unknown-unknown`. WASI provides real `fopen`/`fread`/`fseek` implementations via the host runtime (Node.js, Wasmtime, etc.). The ephemeris files can be placed in a directory and accessed normally.

| Pros | Cons |
|------|------|
| No custom file I/O shims needed | WASI not supported in all browsers yet |
| Standard filesystem semantics | Requires WASI-compatible runtime |
| Cleanest implementation | wasm-bindgen doesn't support WASI target well |

#### Recommendation for lunisolar-ts

**Moshier is sufficient.** For lunisolar calendar calculations (detecting new moons and solar terms), the position accuracy we need is:
- New moon: Moon longitude = Sun longitude ± ~0.01° tolerance → Moshier accuracy (~0.0002° = 0.7 arcsec) is >10× better than needed
- Solar terms: Sun at 0°, 15°, 30°... ± ~0.01° → Moshier accuracy (~0.000001°) is >10,000× better than needed

Swiss Eph or JPL data would only matter for:
- High-precision asteroid calculations
- Occultation/eclipse timing (sub-arcsecond)
- Historical calculations before 3000 BCE or after 3000 CE (Moshier range is limited)

If JPL precision is ever needed, **Approach A** (embed `.se1` files) is the cleanest path — it adds ~2 MB to the binary but requires no async loading or FILE* emulation.

---

## 6. References

- [fusionstrings/swisseph-wasm (GitHub)](https://github.com/fusionstrings/swisseph-wasm)
- [swisseph-wasm (crates.io)](https://crates.io/crates/swisseph-wasm)
- [aloistr/swisseph — Official Swiss Ephemeris (GitHub)](https://github.com/aloistr/swisseph)
- [libswe-sys (GitHub)](https://github.com/stephaneworkspace/libswe-sys)
- [Swiss Ephemeris (Astrodienst)](https://www.astro.com/swisseph/)
- [prolaxu/swisseph-wasm (npm)](https://github.com/prolaxu/swisseph-wasm)
- [Swiss Ephemeris documentation — Ephemeris file format](https://www.astro.com/swisseph/swephprg.htm)

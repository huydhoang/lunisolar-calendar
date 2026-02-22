# Rust WASM Architecture: Swiss Ephemeris for lunisolar-ts

> How we compile the Swiss Ephemeris C library to WebAssembly using Rust and
> wasm-bindgen, embed the high-precision `.se1` ephemeris data directly in the
> binary, and achieve sufficient calculation speed for lunisolar calendar use
> without Emscripten or any external runtime dependencies.

---

## 1. What We Built

Our vendored WASM package lives at `wasm/swisseph/`. It compiles the official
Swiss Ephemeris C source (v2.10.03 from [aloistr/swisseph](https://github.com/aloistr/swisseph))
to `wasm32-unknown-unknown` using the Rust `cc` crate, with wasm-bindgen for
typed JS/TypeScript interop. The `.se1` ephemeris data files are embedded
directly in the binary — no external data download is needed at runtime.

| Metric | Value |
|--------|-------|
| WASM binary size | ~2.1 MB (incl. embedded `sepl_18.se1` + `semo_18.se1`) |
| SE version | v2.10.03 |
| Ephemeris mode | Swiss Ephemeris data (`SEFLG_SWIEPH`) |
| Toolchain | `rustup` + `wasm-pack` (no Emscripten SDK) |
| Init model | Sync ES module import; no `await initSwissEph()` |
| Init time | 13 ms (Node.js) |
| API | `swe_calc_ut`, `swe_julday`, `swe_revjul`, `swe_get_planet_name` |
| Build command | `wasm-pack build --target nodejs --release` |

---

## 2. Architecture

### 2.1 Package layout

```
wasm/swisseph/
├── Cargo.toml            # cdylib + rlib; deps: wasm-bindgen, cc, libm
├── build.rs              # cc crate compiles C source; sets WASM-specific flags
├── vendor/
│   └── swisseph/         # Vendored SE C source (v2.10.03 from aloistr/swisseph)
│       ├── swecl.c
│       ├── swedate.c
│       ├── sweph.c       # ... 9 core C files
│       └── *.h
├── ephe/
│   ├── sepl_18.se1       # Swiss Ephemeris Sun/planets data file (~1.3 MB)
│   └── semo_18.se1       # Swiss Ephemeris Moon data file (~0.7 MB)
├── wasm-includes/        # Minimal C header stubs for wasm32 target
│   ├── math.h            # Declares sin/cos/etc. (implemented via libm in Rust)
│   ├── string.h          # Declares memcpy/strlen/etc. (implemented in Rust)
│   ├── stdio.h           # FILE* type + fopen/fread/fseek/fclose (in-memory impl)
│   └── ...
└── src/
    ├── lib.rs            # wasm-bindgen exports + Rust shims for C stdlib
    └── wrapper/
        └── stub.c        # C stubs for variadic functions (sprintf, fprintf)
```

### 2.2 Key design decisions

**1. Vendor C source directly — not via a `-sys` crate.**

Compiling Swiss Ephemeris to `wasm32-unknown-unknown` requires WASM-specific
`build.rs` configuration and custom C header stubs. No existing `-sys` crate
supports this target (see §5 for why). Vendoring gives full control over
compilation flags and the include path.

**2. Symbol renaming via `#define` in `build.rs`.**

Renames internal C functions (e.g. `swe_calc_ut` → `impl_swe_calc_ut`) to
avoid symbol collisions with the wasm-bindgen public exports of the same name.

**3. Minimal WASM-specific C headers in `wasm-includes/`.**

The `wasm32-unknown-unknown` target has no system headers or sysroot. We
provide only the declarations the SE C code actually needs. Implementations
are provided by Rust shims: `libm` crate for math, `std::alloc` for
`malloc`/`free`, and custom in-memory FILE* logic for `fopen`/`fread`/`fseek`.

**4. Variadic C functions in `stub.c`.**

`sprintf`, `fprintf`, and `sscanf` cannot be defined in Rust (C-variadic ABI
is unstable on this target). A minimal `stub.c` provides no-op stubs.

**5. `-DTLSOFF` compile flag.**

`sweodef.h` uses `__thread` (thread-local storage), which is unsupported on
`wasm32-unknown-unknown`. This flag disables TLS throughout the SE source.

**6. Embedded `.se1` data via in-memory `fopen`.**

The Swiss Ephemeris data files are embedded into the binary using Rust's
`include_bytes!()`. The `fopen` shim maps a filename to the corresponding
in-memory byte slice; `fread`, `fseek`, and `ftell` operate on a cursor over
that slice. This is what gives our build high precision (see §3).

---

## 3. Why wasm-bindgen Instead of Emscripten

The two mainstream paths to compile C to WebAssembly are **Emscripten** and
**Rust `cc` crate + wasm-bindgen**. This section explains why we chose the
latter.

### 3.1 Emscripten (the alternative)

Emscripten is a complete C/C++ → WASM + JavaScript toolchain. It emulates a
full POSIX environment, requiring the Emscripten SDK (~1 GB) and producing a
large auto-generated JS runtime file.

| Characteristic | Emscripten build (prolaxu/swisseph-wasm) |
|----------------|------------------------------------------|
| Toolchain | Emscripten SDK (~1 GB) |
| JS glue | ~500 KB auto-generated runtime |
| File I/O | Virtual FS — `.data` file pre-loaded at startup |
| Init API | Async: `await initSwissEph()` |
| WASM + data size | 531.2 KB WASM + 11.5 MB `.data` = ~13 MB total |
| Init time | ~38 ms (Node.js) |

### 3.2 wasm-bindgen (our approach)

We compile the same SE C source to `wasm32-unknown-unknown` via the Rust `cc`
crate, providing only the POSIX shims the code actually uses. wasm-bindgen
generates thin, typed JS/TS bindings.

| Characteristic | wasm-bindgen (our build) |
|----------------|--------------------------|
| Toolchain | `rustup` + `wasm-pack` (<50 MB total) |
| JS glue | ~10 KB wasm-bindgen output |
| File I/O | In-memory FILE* backed by `include_bytes!()` |
| Init API | Sync: standard ES module import |
| WASM size | 2.1 MB (WASM + embedded `.se1` data) |
| Init time | **13 ms** (Node.js) — 3× faster than Emscripten |

### 3.3 Advantages of wasm-bindgen

1. **No Emscripten SDK in CI** — `rustup` and `wasm-pack` install in seconds,
   not gigabytes. Both WASM modules in this repo (`wasm/swisseph/` and `wasm/`)
   use the same toolchain.

2. **Typed JS/TS bindings** — wasm-bindgen auto-generates `.d.ts` files.
   The Emscripten Module API is untyped and relies on `cwrap`/`ccall`.

3. **Synchronous initialization** — a wasm-bindgen module is ready as soon as
   the ES module is imported. There is no `await initSwissEph()` gate before
   the first `swe_calc_ut` call, simplifying the coordinator code.

4. **Smaller JS surface** — ~10 KB wasm-bindgen glue vs ~500 KB Emscripten
   runtime.

5. **Unified Rust ecosystem** — both the ephemeris engine (`wasm/swisseph/`)
   and the calendar logic (`wasm/`) share the same build flags, target, and
   `wasm-pack` workflow.

6. **Control over what gets compiled** — we vendor only the 9 core SE C files
   needed for planetary position calculations, excluding eclipse, heliacal
   rising, and other functions that add size without benefit for our use case.

### 3.4 Trade-off: calc_ut speed

The main trade-off is raw `calc_ut` throughput: ~220K ops/sec for our build
vs ~1.5M ops/sec for the Emscripten build. This is primarily because
Emscripten's optimizer is more mature for C-heavy code, and because
data-file lookups in SE are computationally cheaper than some operations in
our custom FILE* emulation layer.

For lunisolar calendar calculations — a bisection search over ~13 new moons
and 24 solar terms per year, ~60 bisection steps each, 2 planets — that is
roughly 2,200 `calc_ut` calls. At 220K ops/sec that is **~10 ms per year** —
well within our 30 ms performance target. The speed difference is irrelevant
at these call volumes.

---

## 4. Ephemeris Data: Embedded `.se1` Files Instead of Moshier

Swiss Ephemeris supports three computation modes selected by the `iflag`
argument to `swe_calc_ut`:

| Flag | Value | Data source | Moon accuracy | Data files |
|------|------:|-------------|---------------|------------|
| `SEFLG_JPLEPH` | 1 | JPL DE431/441 | ~0.001 arcsec | `jpl*.eph` (~100+ MB) |
| `SEFLG_SWIEPH` | 2 | Swiss Eph `.se1` files | ~0.001 arcsec | `sepl*.se1` + `semo*.se1` (~2 MB) |
| `SEFLG_MOSEPH` | 4 | Moshier analytical model | ~1 arcsec | None (built-in) |

The SE C library has an automatic **fallback chain**: JPL → Swiss Eph →
Moshier. When a data file cannot be opened, it falls back silently.

### 4.1 Why we embed `.se1` files, not Moshier

The [fusionstrings/swisseph-wasm](https://github.com/fusionstrings/swisseph-wasm)
crate — which provided the architectural template — stubs `fopen` to return
`NULL`. This triggers the fallback to Moshier: simple to implement, 337 KB
binary, but ~1 arcsecond Moon accuracy.

We require higher precision. We embed the actual Swiss Ephemeris data files
(`sepl_18.se1` and `semo_18.se1`) into the binary via `include_bytes!()` and
implement a real in-memory FILE* layer. This gives:

- **Accuracy matching the Emscripten build** — both use the same Swiss Eph
  `.se1` data. Position agreement is at the floating-point rounding level
  (< 0.000001° for the Sun, < 0.000221° for the Moon).
- **No async file loading** — data is already in the WASM binary; no `fetch()`
  or filesystem access needed.
- **Binary size of ~2.1 MB** — larger than the Moshier-only builds (~337 KB)
  but much smaller than the Emscripten package (~13 MB total with `.data`).

### 4.2 Is Swiss Eph precision actually needed?

For lunisolar calendar calculations the critical operations are:

| Operation | Required accuracy | Moshier (~1 arcsec) | Swiss Eph (.se1) |
|-----------|------------------|---------------------|------------------|
| New moon (Moon lon = Sun lon) | ±0.01° (±36 arcsec) | ✅ 30× margin | ✅ 130,000× margin |
| Solar term (Sun lon = 0°, 15°, …) | ±0.01° | ✅ adequate | ✅ excellent |

Moshier would be numerically sufficient for Sun/Moon position. We chose Swiss
Eph `.se1` data regardless because:

1. **Consistency** — positions match the legacy Python/Skyfield pipeline,
   which also uses Swiss Eph-quality data. This makes regression testing
   straightforward.
2. **Future-proofing** — if we add high-precision asteroid positions or
   historical date support (pre-800 CE / post-2400 CE), Moshier is out of
   range; `.se1` data is valid from 2000 BCE to 3000 CE.
3. **Marginal cost** — the extra ~1.7 MB over a Moshier build is offset by
   still being 6× smaller than the Emscripten alternative.

---

## 5. Why Not Existing Rust Crates

Before building our own, we evaluated all available Rust crates that wrap
or reimplement Swiss Ephemeris.

### 5.1 Crates evaluated

| Crate | SE Version | WASM Ready | Stars | Assessment |
|-------|-----------|-----------|-------|------------|
| `libswe-sys` (stephaneworkspace) | 2.08 | ❌ | 11 | Heavy deps; TLS incompatibility; private FFI module |
| **`swisseph-wasm` (fusionstrings)** | **2.10.03** | **✅** | **0** | **Best existing template; uses Moshier (lower precision)** |
| `libswe-rs` (thomasrstorey) | Unknown | ❌ | 2 | No WASM support; low activity |
| `ephem-rs` (CHINMAYVIVEK) | Unknown | ❌ | 2 | Experimental; no WASM support |
| `swisseph-rs` (aaroncarlucci) | Unknown | ❓ | 0 | New (Jan 2026); AGPL license |
| `vsop87-rs` (Razican) | N/A | ✅ (pure) | 18 | Different algorithm; lower Moon precision; archived |

### 5.2 Why `libswe-sys` is not viable for WASM

`libswe-sys` is the most-starred crate but has fundamental blockers:

| Problem | Detail |
|---------|--------|
| **Outdated SE version** | v2.08 (current is v2.10.03 from [aloistr/swisseph](https://github.com/aloistr/swisseph)) |
| **Private FFI module** | `mod raw;` is not `pub` — cannot call `swe_calc_ut` from downstream |
| **TLS incompatibility** | `sweodef.h` uses `__thread`, unsupported on `wasm32-unknown-unknown` |
| **No WASM build config** | `build.rs` compiles C with `-g`, no WASM-specific flags |
| **Missing sysroot** | `#include <math.h>`, `<string.h>` etc. — no headers on bare WASM target |
| **Heavy deps** | `serde`, `serde_json`, `strum`, `num-derive` — no value for WASM |

These are design issues, not configuration problems. Upstream is unlikely to
add WASM support given the crate's maintenance trajectory.

### 5.3 Why not `fusionstrings/swisseph-wasm`

The `fusionstrings/swisseph-wasm` crate proved the architecture works and
served as our template. We did not use it directly because:

1. **Moshier precision only** — it stubs `fopen` to `NULL`, forcing Moshier
   mode. We need `.se1` precision for position consistency with the legacy
   pipeline (§4.1).
2. **Third-party dependency** — tying the ephemeris engine to an upstream npm
   or crates.io package means we cannot independently embed our own `.se1`
   data or change the API surface.
3. **Stars: 0** — low adoption means higher risk of abandonment.

By implementing our own build following the same architecture, we gain
`.se1` precision, full control over the API and data files, and independence
from upstream release cycles.

---

## 6. Keeping Up with Swiss Ephemeris Upstream

The official Swiss Ephemeris C source is maintained at
**[aloistr/swisseph](https://github.com/aloistr/swisseph)** (actively
maintained by Alois Treindl, co-author of Swiss Ephemeris).

**Chosen approach: Vendored copy + scheduled CI version check.**

1. The 9 core C files + headers are vendored from `aloistr/swisseph` at tag
   `v2.10.03` into `wasm/swisseph/vendor/swisseph/`.
2. A scheduled CI workflow (`.github/workflows/check-swisseph-update.yml`)
   runs weekly, fetches the latest tag, compares it to the vendored version
   string in `sweph.h`, and opens a GitHub issue if a newer version is
   available.
3. Only core computation files are vendored — tests, documentation, and
   optional modules (heliacal risings, asteroids) are excluded.

---

## 7. Benchmark Results

Benchmarked on Node.js v22.22.0, 10,000 iterations per test.
CI run: [2026-02-21](https://github.com/huydhoang/lunisolar-ts/actions/runs/22263333049).
Full script: `tests/swisseph-wasm/benchmark.mjs`.

Three implementations compared:

| | `@fusionstrings/swisseph-wasm` | `swisseph-wasm` (prolaxu) | **`swisseph` (ours)** |
|-|:------------------------------:|:-------------------------:|:---------------------:|
| Toolchain | Rust + wasm-bindgen | Emscripten | **Rust + wasm-bindgen** |
| Ephemeris | Moshier | Swiss Eph .se1 | **Swiss Eph .se1** |
| WASM binary | 337.4 KB | 531.2 KB + 11.5 MB | **2.1 MB** |
| Init time | 41.0 ms | 37.7 ms | **13.0 ms** ✅ |
| `julday` | 5,918,582 ops/sec | 1,108,404 ops/sec | **6,367,107 ops/sec** ✅ |
| `calc_ut` Sun | 142,772 ops/sec | 680,936 ops/sec | 182,018 ops/sec |
| `calc_ut` Moon | 171,448 ops/sec | 1,531,382 ops/sec | 216,425 ops/sec |

### Position agreement (JD 2460677.0 = 2025-01-01 12:00 UTC)

| Body | fusionstrings Lon° | prolaxu Lon° | ours Lon° | Δ° (f vs p/ours) |
|------|-------------------:|-------------:|----------:|------------------:|
| Sun | 281.323433 | 281.323434 | 281.323434 | 0.000001 |
| Moon | 300.660895 | 300.661116 | 300.661116 | 0.000221 |
| Mercury | 260.516388 | 260.516383 | 260.516383 | 0.000005 |
| Venus | 328.248297 | 328.248306 | 328.248306 | 0.000009 |
| Mars | 121.752631 | 121.752692 | 121.752692 | 0.000061 |
| Jupiter | 73.162615 | 73.162521 | 73.162521 | 0.000094 |
| Saturn | 344.562084 | 344.562049 | 344.562049 | 0.000035 |

Our build and prolaxu agree to floating-point rounding precision (both use
the same `.se1` data). fusionstrings diverges by up to 0.000221° (Moshier vs
Swiss Eph) — well within the ±0.01° tolerance for lunisolar calendar
calculations, but our higher precision provides better consistency with the
legacy pipeline.

---

## 8. References

- [aloistr/swisseph — Official Swiss Ephemeris (GitHub)](https://github.com/aloistr/swisseph)
- [Swiss Ephemeris — Astrodienst](https://www.astro.com/swisseph/) — C library documentation and commercial licensing
- [Swiss Ephemeris Programmer's Documentation](https://www.astro.com/swisseph/swephprg.htm)
- [fusionstrings/swisseph-wasm (GitHub)](https://github.com/fusionstrings/swisseph-wasm) — architectural template
- [swisseph-wasm (crates.io)](https://crates.io/crates/swisseph-wasm)
- [libswe-sys (GitHub)](https://github.com/stephaneworkspace/libswe-sys)
- [prolaxu/swisseph-wasm (npm)](https://github.com/prolaxu/swisseph-wasm) — Emscripten reference implementation
- [wasm-bindgen guide](https://rustwasm.github.io/docs/wasm-bindgen/)
- [wasm-pack documentation](https://rustwasm.github.io/docs/wasm-pack/)


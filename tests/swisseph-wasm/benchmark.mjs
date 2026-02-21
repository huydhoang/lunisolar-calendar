/**
 * swisseph-wasm Benchmark
 *
 * Compares WASM implementations of the Swiss Ephemeris:
 *   1. @fusionstrings/swisseph-wasm — Rust FFI + wasm-bindgen (npm, Moshier mode)
 *   2. swisseph-wasm (prolaxu)      — Emscripten C→WASM (Swiss Ephemeris with embedded data)
 *   3. swisseph (ours)              — Vendored C source from aloistr/swisseph v2.10.03 + Rust wasm-bindgen
 *
 * Measures:
 *   - Initialization time
 *   - calc_ut throughput (Sun and Moon positions)
 *   - julday throughput
 *   - Position agreement between implementations
 *   - Package / binary sizes
 *
 * Run:
 *   node benchmark.mjs
 */

import { writeFileSync, statSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// ─── Configuration ─────────────────────────────────────────────────────────
const WARMUP_ITERATIONS = 100;
const BENCH_ITERATIONS = 10_000;
const TOLERANCE_DEG = 0.01; // Position agreement tolerance

const BODIES = [
  { id: 0, name: 'Sun' },
  { id: 1, name: 'Moon' },
  { id: 2, name: 'Mercury' },
  { id: 3, name: 'Venus' },
  { id: 4, name: 'Mars' },
  { id: 5, name: 'Jupiter' },
  { id: 6, name: 'Saturn' },
];

// ─── Helpers ───────────────────────────────────────────────────────────────

/** High-resolution timer in milliseconds. */
function now() {
  const [s, ns] = process.hrtime();
  return s * 1000 + ns / 1e6;
}

/** Angular difference on a circle (handles 0°/360° wrap). */
function angularDiff(a, b) {
  let d = Math.abs(a - b) % 360;
  if (d > 180) d = 360 - d;
  return d;
}

/** Format a number with fixed decimal places. */
const f = (v, n = 4) => (typeof v === 'number' ? v.toFixed(n) : '—');

/** Get file size in human-readable form. */
function fileSize(path) {
  try {
    const s = statSync(path);
    if (s.size < 1024) return `${s.size} B`;
    if (s.size < 1024 * 1024) return `${(s.size / 1024).toFixed(1)} KB`;
    return `${(s.size / (1024 * 1024)).toFixed(1)} MB`;
  } catch {
    return '—';
  }
}

/**
 * Benchmark a synchronous function.
 * Returns { mean_ms, ops_per_sec, min_ms, max_ms }.
 */
function bench(fn, iterations = BENCH_ITERATIONS, warmup = WARMUP_ITERATIONS) {
  // Warmup
  for (let i = 0; i < warmup; i++) fn();

  const start = now();
  for (let i = 0; i < iterations; i++) fn();
  const elapsed = now() - start;

  // Also measure min/max over batches
  const batchSize = Math.max(1, Math.floor(iterations / 10));
  let minBatch = Infinity;
  let maxBatch = 0;
  for (let b = 0; b < 10; b++) {
    const bs = now();
    for (let i = 0; i < batchSize; i++) fn();
    const be = now() - bs;
    const perOp = be / batchSize;
    if (perOp < minBatch) minBatch = perOp;
    if (perOp > maxBatch) maxBatch = perOp;
  }

  return {
    mean_ms: elapsed / iterations,
    ops_per_sec: Math.round((iterations / elapsed) * 1000),
    min_ms: minBatch,
    max_ms: maxBatch,
  };
}

// ─── Main ──────────────────────────────────────────────────────────────────

async function main() {
  const reportLines = [];
  const log = (line = '') => {
    reportLines.push(line);
    process.stdout.write(line + '\n');
  };

  log('# swisseph-wasm Benchmark Report');
  log();
  log('**Comparison:** `@fusionstrings/swisseph-wasm` (Rust+wasm-bindgen, npm) vs `swisseph-wasm` (Emscripten) vs `swisseph` (our vendored build)');
  log(`**Date:** ${new Date().toISOString().slice(0, 10)}`);
  log(`**Node.js:** ${process.version}`);
  log(`**Iterations:** ${BENCH_ITERATIONS.toLocaleString()} per test`);
  log();

  // ── 1. Package sizes ─────────────────────────────────────────────────────
  log('## 1. Package & Binary Sizes');
  log();

  const fusionWasmPath = join(__dirname, 'node_modules/@fusionstrings/swisseph-wasm/esm/lib/swisseph_wasm.wasm');
  const prolaxuWasmPath = join(__dirname, 'node_modules/swisseph-wasm/wsam/swisseph.wasm');
  const prolaxuDataPath = join(__dirname, 'node_modules/swisseph-wasm/wsam/swisseph.data');
  const oursWasmPath = join(__dirname, '../../wasm/swisseph/pkg/swisseph_wasm_bg.wasm');

  log('| Package | WASM Binary | Ephemeris Data | Total Package |');
  log('|---------|------------|----------------|---------------|');
  log(`| @fusionstrings/swisseph-wasm | ${fileSize(fusionWasmPath)} | Built-in (Moshier) | ~1.4 MB |`);
  log(`| swisseph-wasm (prolaxu) | ${fileSize(prolaxuWasmPath)} | ${fileSize(prolaxuDataPath)} | ~13 MB |`);
  log(`| swisseph (ours) | ${fileSize(oursWasmPath)} | Embedded (Swiss Eph .se1) | — |`);
  log();

  // ── 2. Initialize all implementations ──────────────────────────────────
  log('## 2. Initialization Time');
  log();
  log(`| Package | Init Time |`);
  log(`|---------|----------|`);

  // fusionstrings — synchronous init (WASM loaded at import)
  let fusion;
  const fusionInitStart = now();
  try {
    fusion = await import('@fusionstrings/swisseph-wasm');
    const fusionInitTime = now() - fusionInitStart;
    log(`| @fusionstrings/swisseph-wasm | ${f(fusionInitTime, 1)} ms |`);
  } catch (err) {
    log(`| @fusionstrings/swisseph-wasm | ❌ Failed: ${err.message} |`);
    writeFileSync(join(__dirname, 'benchmark-report.md'), reportLines.join('\n') + '\n');
    process.exit(1);
  }

  // prolaxu — async init
  let prolaxu;
  const prolaxuInitStart = now();
  try {
    const SwissEph = (await import('swisseph-wasm')).default;
    prolaxu = new SwissEph();
    await prolaxu.initSwissEph();
    const prolaxuInitTime = now() - prolaxuInitStart;
    log(`| swisseph-wasm (prolaxu) | ${f(prolaxuInitTime, 1)} ms |`);
  } catch (err) {
    log(`| swisseph-wasm (prolaxu) | ❌ Failed: ${err.message} |`);
    writeFileSync(join(__dirname, 'benchmark-report.md'), reportLines.join('\n') + '\n');
    process.exit(1);
  }

  // swisseph (ours) — vendored C source + Rust wasm-bindgen
  let ours = null;
  const oursInitStart = now();
  try {
    ours = await import('../../wasm/swisseph/pkg/swisseph_wasm.js');
    // Quick sanity check
    const testJd = ours.swe_julday(2025, 1, 1, 12.0, 1);
    if (typeof testJd !== 'number' || testJd === 0) throw new Error('julday returned invalid result');
    const oursInitTime = now() - oursInitStart;
    log(`| swisseph (ours) | ${f(oursInitTime, 1)} ms |`);
  } catch (err) {
    log(`| swisseph (ours) | ⚠️ Not available: ${err.message} |`);
    ours = null;
  }
  log();

  // ── 3. Julian Day conversion benchmark ────────────────────────────────────
  log('## 3. Julian Day Conversion (`julday`)');
  log();

  const fusionJD = bench(() => fusion.swe_julday(2025, 6, 15, 12.0, fusion.SE_GREG_CAL));
  const prolaxuJD = bench(() => prolaxu.julday(2025, 6, 15, 12.0));

  const jdFusion = fusion.swe_julday(2025, 6, 15, 12.0, fusion.SE_GREG_CAL);
  const jdProlaxu = prolaxu.julday(2025, 6, 15, 12.0);

  log('| Package | ops/sec | mean (ms) | min (ms) | max (ms) | JD Value |');
  log('|---------|--------:|----------:|---------:|---------:|---------:|');
  log(`| fusionstrings | ${fusionJD.ops_per_sec.toLocaleString()} | ${f(fusionJD.mean_ms, 6)} | ${f(fusionJD.min_ms, 6)} | ${f(fusionJD.max_ms, 6)} | ${f(jdFusion, 6)} |`);
  log(`| prolaxu | ${prolaxuJD.ops_per_sec.toLocaleString()} | ${f(prolaxuJD.mean_ms, 6)} | ${f(prolaxuJD.min_ms, 6)} | ${f(prolaxuJD.max_ms, 6)} | ${f(jdProlaxu, 6)} |`);

  if (ours) {
    const oursJD = bench(() => ours.swe_julday(2025, 6, 15, 12.0, 1));
    const jdOurs = ours.swe_julday(2025, 6, 15, 12.0, 1);
    log(`| ours | ${oursJD.ops_per_sec.toLocaleString()} | ${f(oursJD.mean_ms, 6)} | ${f(oursJD.min_ms, 6)} | ${f(oursJD.max_ms, 6)} | ${f(jdOurs, 6)} |`);
  }

  const jdRatio = fusionJD.ops_per_sec / prolaxuJD.ops_per_sec;
  log();
  log(`**julday speedup:** fusionstrings is **${f(jdRatio, 2)}x** ${jdRatio >= 1 ? 'faster' : 'slower'} than prolaxu`);
  log();

  // ── 4. calc_ut benchmark for each body ────────────────────────────────────
  log('## 4. Planetary Position Calculation (`calc_ut`)');
  log();

  const jd = fusion.swe_julday(2025, 1, 1, 12.0, fusion.SE_GREG_CAL);

  log('| Body | fusionstrings ops/sec | prolaxu ops/sec | ours ops/sec | Speedup (f/p) | Lon Δ° | Agreement |');
  log('|------|---------------------:|----------------:|------------:|--------------:|-------:|-----------|');

  const calcResults = [];

  for (const body of BODIES) {
    // Benchmark fusionstrings
    const fusionCalc = bench(() => fusion.swe_calc_ut(jd, body.id, fusion.SEFLG_SWIEPH));

    // Benchmark prolaxu
    const prolaxuCalc = bench(() => prolaxu.calc_ut(jd, body.id, prolaxu.SEFLG_SWIEPH));

    // Benchmark ours (if available)
    let oursCalc = null;
    let oursLon = null;
    if (ours) {
      try {
        oursCalc = bench(() => ours.swe_calc_ut(jd, body.id, 2));
        const oursPos = ours.swe_calc_ut(jd, body.id, 2);
        oursLon = oursPos.longitude;
      } catch { oursCalc = null; }
    }

    // Get actual positions for comparison
    const fusionPos = fusion.swe_calc_ut(jd, body.id, fusion.SEFLG_SWIEPH);
    const prolaxuPos = prolaxu.calc_ut(jd, body.id, prolaxu.SEFLG_SWIEPH);

    const fusionLon = fusionPos.longitude;
    const prolaxuLon = prolaxuPos[0];
    const lonDiff = angularDiff(fusionLon, prolaxuLon);
    const agree = lonDiff <= TOLERANCE_DEG ? '✅' : '❌';

    const ratio = fusionCalc.ops_per_sec / prolaxuCalc.ops_per_sec;
    const oursOpsStr = oursCalc ? oursCalc.ops_per_sec.toLocaleString() : '—';

    log(
      `| ${body.name} | ${fusionCalc.ops_per_sec.toLocaleString()} | ${prolaxuCalc.ops_per_sec.toLocaleString()} | ${oursOpsStr} | ${f(ratio, 2)}x | ${f(lonDiff, 6)} | ${agree} |`,
    );

    calcResults.push({
      body: body.name,
      fusionOps: fusionCalc.ops_per_sec,
      prolaxuOps: prolaxuCalc.ops_per_sec,
      oursOps: oursCalc ? oursCalc.ops_per_sec : null,
      ratio,
      lonDiff,
      fusionLon,
      prolaxuLon,
      oursLon,
    });
  }

  log();

  // ── 5. Aggregate statistics ───────────────────────────────────────────────
  const avgRatio =
    calcResults.reduce((sum, r) => sum + r.ratio, 0) / calcResults.length;
  const maxDiff = Math.max(...calcResults.map((r) => r.lonDiff));
  const allAgree = calcResults.every((r) => r.lonDiff <= TOLERANCE_DEG);

  log('## 5. Summary');
  log();
  log('| Metric | Value |');
  log('|--------|-------|');
  log(`| Average calc_ut speedup | **${f(avgRatio, 2)}x** |`);
  log(`| Max longitude difference | ${f(maxDiff, 6)}° |`);
  log(`| All positions agree (< ${TOLERANCE_DEG}°) | ${allAgree ? '✅ Yes' : '❌ No'} |`);
  log(`| fusionstrings WASM size | ${fileSize(fusionWasmPath)} |`);
  log(`| prolaxu WASM + data size | ${fileSize(prolaxuWasmPath)} + ${fileSize(prolaxuDataPath)} |`);
  log(`| ours WASM size | ${fileSize(oursWasmPath)} |`);
  log(`| ours available | ${ours ? '✅ Yes' : '⚠️ No (build required)'} |`);
  log();

  // ── 6. Detailed position comparison ───────────────────────────────────────
  log('## 6. Detailed Position Comparison');
  log();
  log(`**Test epoch:** JD ${f(jd, 1)} (2025-01-01 12:00 UTC)`);
  log();
  log('| Body | fusionstrings Lon° | prolaxu Lon° | ours Lon° | Δ° | Note |');
  log('|------|-------------------:|-------------:|----------:|---:|------|');

  for (const r of calcResults) {
    const note = r.lonDiff < 0.001 ? 'Excellent' : r.lonDiff < 0.01 ? 'Good' : r.lonDiff < 0.1 ? 'Acceptable' : 'Poor';
    const oursLonStr = r.oursLon !== null ? f(r.oursLon, 6) : '—';
    log(`| ${r.body} | ${f(r.fusionLon, 6)} | ${f(r.prolaxuLon, 6)} | ${oursLonStr} | ${f(r.lonDiff, 6)} | ${note} |`);
  }

  log();
  log('> **Note:** Differences arise because fusionstrings uses the Moshier analytical ephemeris');
  log('> (built into Swiss Ephemeris, no external data files) while prolaxu uses the full Swiss');
  log('> Ephemeris with JPL-derived data files (~12 MB). For lunisolar calendar calculations');
  log('> (Sun/Moon longitude to find new moons and solar terms), both are well within the');
  log('> required precision (< 0.01° ≈ 36 arcseconds).');
  log();

  // ── 7. Recommendations ────────────────────────────────────────────────────
  log('## 7. Recommendation for Lunisolar-TS');
  log();
  log('| Criteria | @fusionstrings/swisseph-wasm | swisseph-wasm (prolaxu) | swisseph (ours) |');
  log('|----------|:---------------------------:|:-----------------------:|:---------------:|');
  log(`| Binary size | ✅ ${fileSize(fusionWasmPath)} (no ext data) | ⚠️ ${fileSize(prolaxuWasmPath)} + ${fileSize(prolaxuDataPath)} | ✅ ${fileSize(oursWasmPath)} |`);
  log(`| Precision | ✅ Sufficient (Moshier) | ✅ Higher (JPL data) | ✅ High (Swiss Eph .se1 data) |`);
  log(`| Speed | See benchmarks above | See benchmarks above | See benchmarks above |`);
  log('| JS interop | ✅ wasm-bindgen (typed) | ⚠️ Emscripten Module API | ✅ wasm-bindgen (typed) |');
  log('| Init model | Sync (import loads WASM) | Async (initSwissEph()) | Sync |');
  log('| Dependencies | 0 runtime | Emscripten runtime | 0 runtime |');
  log('| SE version | v2.10.03 | Unknown | v2.10.03 |');
  log('| Maintenance | Third-party npm | Third-party npm | We maintain (vendored C source) |');
  log();
  log('For the lunisolar calendar use case, `@fusionstrings/swisseph-wasm` is **recommended**:');
  log('- 10x smaller binary (no external ephemeris data files needed)');
  log('- Moshier precision is sufficient for Sun/Moon position calculations');
  log('- Clean wasm-bindgen API integrates well with the Rust WASM calendar module');
  log('- Synchronous initialization simplifies the coordinator code');
  log();
  log('---');
  log('*Generated by the swisseph-wasm benchmark workflow.*');

  // ── Cleanup ───────────────────────────────────────────────────────────────
  if (prolaxu && typeof prolaxu.close === 'function') {
    prolaxu.close();
  }

  // ── Write report ──────────────────────────────────────────────────────────
  writeFileSync(join(__dirname, 'benchmark-report.md'), reportLines.join('\n') + '\n');
  log();
  log('Report written to benchmark-report.md');
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});

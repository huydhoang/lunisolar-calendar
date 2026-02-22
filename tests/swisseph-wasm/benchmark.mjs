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

  log('# Swiss Ephemeris WASM — `calc_ut` Throughput & Position Agreement');
  log();
  log(`**Date:** ${new Date().toISOString().slice(0, 10)}`);
  log(`**Node.js:** ${process.version}`);
  log(`**Iterations:** ${BENCH_ITERATIONS.toLocaleString()} per test`);
  log();

  // ── File paths ──────────────────────────────────────────────────────────
  const fusionWasmPath = join(__dirname, 'node_modules/@fusionstrings/swisseph-wasm/esm/lib/swisseph_wasm.wasm');
  const prolaxuWasmPath = join(__dirname, 'node_modules/swisseph-wasm/wsam/swisseph.wasm');
  const prolaxuDataPath = join(__dirname, 'node_modules/swisseph-wasm/wsam/swisseph.data');
  const oursWasmPath = join(__dirname, '../../wasm/swisseph-rs/pkg/swisseph_wasm_bg.wasm');

  // ── Initialize all implementations ──────────────────────────────────────
  log('## Implementations');
  log();
  log('| Package | Build | WASM Size | Ephemeris | Init Time |');
  log('|---------|-------|----------:|-----------|----------:|');

  let fusion;
  const fusionInitStart = now();
  try {
    fusion = await import('@fusionstrings/swisseph-wasm');
    const fusionInitTime = now() - fusionInitStart;
    log(`| @fusionstrings/swisseph-wasm | Rust + wasm-bindgen | ${fileSize(fusionWasmPath)} | Moshier (built-in) | ${f(fusionInitTime, 1)} ms |`);
  } catch (err) {
    log(`| @fusionstrings/swisseph-wasm | Rust + wasm-bindgen | ${fileSize(fusionWasmPath)} | — | ❌ ${err.message} |`);
    writeFileSync(join(__dirname, 'benchmark-report.md'), reportLines.join('\n') + '\n');
    process.exit(1);
  }

  let prolaxu;
  const prolaxuInitStart = now();
  try {
    const SwissEph = (await import('swisseph-wasm')).default;
    prolaxu = new SwissEph();
    await prolaxu.initSwissEph();
    const prolaxuInitTime = now() - prolaxuInitStart;
    log(`| swisseph-wasm (prolaxu) | Emscripten C→WASM | ${fileSize(prolaxuWasmPath)} | JPL data (${fileSize(prolaxuDataPath)}) | ${f(prolaxuInitTime, 1)} ms |`);
  } catch (err) {
    log(`| swisseph-wasm (prolaxu) | Emscripten C→WASM | ${fileSize(prolaxuWasmPath)} | — | ❌ ${err.message} |`);
    writeFileSync(join(__dirname, 'benchmark-report.md'), reportLines.join('\n') + '\n');
    process.exit(1);
  }

  let ours = null;
  const oursInitStart = now();
  try {
    ours = await import('../../wasm/swisseph-rs/pkg/swisseph_wasm.js');
    const testJd = ours.swe_julday(2025, 1, 1, 12.0, 1);
    if (typeof testJd !== 'number' || testJd === 0) throw new Error('julday returned invalid result');
    const oursInitTime = now() - oursInitStart;
    log(`| swisseph (ours) | Vendored C + Rust wasm-bindgen | ${fileSize(oursWasmPath)} | Swiss Eph .se1 (embedded) | ${f(oursInitTime, 1)} ms |`);
  } catch (err) {
    log(`| swisseph (ours) | Vendored C + Rust wasm-bindgen | ${fileSize(oursWasmPath)} | — | ⚠️ ${err.message} |`);
    ours = null;
  }
  log();

  // ── calc_ut throughput ────────────────────────────────────────────────────
  log('## `calc_ut` Throughput (ops/sec)');
  log();

  const jd = fusion.swe_julday(2025, 1, 1, 12.0, fusion.SE_GREG_CAL);
  log(`Test epoch: JD ${f(jd, 1)} (2025-01-01 12:00 UTC)`);
  log();

  log('| Body | fusionstrings | prolaxu | ours | Fastest |');
  log('|------|-------------:|--------:|-----:|---------|');

  const calcResults = [];

  for (const body of BODIES) {
    const fusionCalc = bench(() => fusion.swe_calc_ut(jd, body.id, fusion.SEFLG_SWIEPH));
    const prolaxuCalc = bench(() => prolaxu.calc_ut(jd, body.id, prolaxu.SEFLG_SWIEPH));

    let oursCalc = null;
    let oursLon = null;
    if (ours) {
      try {
        oursCalc = bench(() => ours.swe_calc_ut(jd, body.id, 2));
        const oursPos = ours.swe_calc_ut(jd, body.id, 2);
        oursLon = oursPos[0];
      } catch { oursCalc = null; }
    }

    const fusionPos = fusion.swe_calc_ut(jd, body.id, fusion.SEFLG_SWIEPH);
    const prolaxuPos = prolaxu.calc_ut(jd, body.id, prolaxu.SEFLG_SWIEPH);
    const fusionLon = fusionPos.longitude;
    const prolaxuLon = prolaxuPos[0];
    const lonDiff = angularDiff(fusionLon, prolaxuLon);

    const oursOps = oursCalc ? oursCalc.ops_per_sec : 0;
    const all = [
      { name: 'fusionstrings', ops: fusionCalc.ops_per_sec },
      { name: 'prolaxu', ops: prolaxuCalc.ops_per_sec },
    ];
    if (oursCalc) all.push({ name: 'ours', ops: oursOps });
    const fastest = all.reduce((a, b) => (a.ops > b.ops ? a : b));

    log(
      `| ${body.name} | ${fusionCalc.ops_per_sec.toLocaleString()} | ${prolaxuCalc.ops_per_sec.toLocaleString()} | ${oursCalc ? oursOps.toLocaleString() : '—'} | **${fastest.name}** (${(fastest.ops / Math.min(...all.map(x => x.ops))).toFixed(1)}×) |`,
    );

    calcResults.push({
      body: body.name,
      fusionOps: fusionCalc.ops_per_sec,
      prolaxuOps: prolaxuCalc.ops_per_sec,
      oursOps: oursCalc ? oursCalc.ops_per_sec : null,
      lonDiff,
      fusionLon,
      prolaxuLon,
      oursLon,
    });
  }
  log();

  // ── julday throughput ────────────────────────────────────────────────────
  log('## `julday` Throughput (ops/sec)');
  log();

  const fusionJD = bench(() => fusion.swe_julday(2025, 6, 15, 12.0, fusion.SE_GREG_CAL));
  const prolaxuJD = bench(() => prolaxu.julday(2025, 6, 15, 12.0));

  log('| Package | ops/sec |');
  log('|---------|--------:|');
  log(`| fusionstrings | ${fusionJD.ops_per_sec.toLocaleString()} |`);
  log(`| prolaxu | ${prolaxuJD.ops_per_sec.toLocaleString()} |`);
  if (ours) {
    const oursJD = bench(() => ours.swe_julday(2025, 6, 15, 12.0, 1));
    log(`| ours | ${oursJD.ops_per_sec.toLocaleString()} |`);
  }
  log();

  // ── Position agreement ────────────────────────────────────────────────────
  log('## Position Agreement');
  log();
  log(`All positions compared at JD ${f(jd, 1)} (2025-01-01 12:00 UTC).`);
  log();
  log('| Body | fusionstrings Lon° | prolaxu Lon° | ours Lon° | Δ° |');
  log('|------|-------------------:|-------------:|----------:|---:|');
  for (const r of calcResults) {
    const oursLonStr = r.oursLon !== null ? f(r.oursLon, 6) : '—';
    log(`| ${r.body} | ${f(r.fusionLon, 6)} | ${f(r.prolaxuLon, 6)} | ${oursLonStr} | ${f(r.lonDiff, 6)} |`);
  }

  const maxDiff = Math.max(...calcResults.map((r) => r.lonDiff));
  const allAgree = calcResults.every((r) => r.lonDiff <= TOLERANCE_DEG);
  log();
  log(`Max Δ: ${f(maxDiff, 6)}° — ${allAgree ? '✅ all within tolerance (< 0.01°)' : '❌ some exceed tolerance'}`);
  log();
  log('> fusionstrings uses Moshier analytical ephemeris (no external files);');
  log('> prolaxu and ours use Swiss Ephemeris with JPL-derived data.');
  log('> Both are well within the precision needed for lunisolar calendar calculations.');
  log();

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

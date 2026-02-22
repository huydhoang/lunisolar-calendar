/**
 * Lunisolar WASM Burst Benchmark
 *
 * Measures throughput of the lunisolar calendar conversion across three
 * implementations by running 500 random timestamp conversions:
 *
 *   - TypeScript pkg:  LunisolarCalendar.fromSolarDate(date, timezone)
 *   - Rust WASM:       wasm.fromSolarDate(timestampMs, tzOffsetSec, newMoonsJson, solarTermsJson)
 *   - Emscripten WASM: emccModule._from_solar_date(timestampMs, tzOffsetSec, nmPtr, nmCount, ...)
 *
 * Each call converts a Unix-epoch millisecond timestamp to a full lunisolar
 * date (lunar year/month/day, four ganzhi with cycle indices).
 *
 * Usage:  node benchmark.mjs
 * Outputs: lunisolar-benchmark-report.md
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { performance } from 'node:perf_hooks';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..', '..');

// ── 1. Load implementations ────────────────────────────────────────────────

const { LunisolarCalendar, configure } = await import(
  resolve(ROOT, 'archive', 'pkg-ts', 'dist', 'index.mjs')
);
configure({ strategy: 'static' });

const wasm = await import(resolve(ROOT, 'wasm', 'lunisolar', 'pkg', 'lunisolar_wasm.js'));

const createLunisolarEmcc = (await import(resolve(ROOT, 'pkg', 'lunisolar_emcc.mjs'))).default;
const emccModule = await createLunisolarEmcc();

// ── 2. Data loader ─────────────────────────────────────────────────────────

const dataDir = resolve(ROOT, 'output', 'json');

function loadJson(kind, year) {
  return JSON.parse(readFileSync(resolve(dataDir, kind, `${year}.json`), 'utf-8'));
}

function loadDataForYears(years) {
  let newMoons = [];
  let solarTerms = [];
  for (const y of years) {
    try { newMoons = newMoons.concat(loadJson('new_moons', y)); } catch { /* skip */ }
    try { solarTerms = solarTerms.concat(loadJson('solar_terms', y)); } catch { /* skip */ }
  }
  return { newMoons, solarTerms };
}

// ── 3. Emscripten WASM wrapper ─────────────────────────────────────────────

function emccFromSolarDate(timestampMs, tzOffsetSeconds, newMoons, solarTerms) {
  const nmCount = newMoons.length;
  const stCount = solarTerms.length;
  const nmPtr = emccModule._malloc(nmCount * 8);
  const stTsPtr = emccModule._malloc(stCount * 8);
  const stIdxPtr = emccModule._malloc(stCount * 4);
  const outBufLen = 1024;
  const outPtr = emccModule._malloc(outBufLen);

  for (let i = 0; i < nmCount; i++) emccModule.HEAPF64[(nmPtr >> 3) + i] = newMoons[i];
  for (let i = 0; i < stCount; i++) {
    emccModule.HEAPF64[(stTsPtr >> 3) + i] = solarTerms[i][0];
    emccModule.HEAPU32[(stIdxPtr >> 2) + i] = solarTerms[i][1];
  }

  const result = emccModule._from_solar_date(
    timestampMs, tzOffsetSeconds, nmPtr, nmCount, stTsPtr, stIdxPtr, stCount, outPtr, outBufLen,
  );

  let json = null;
  if (result > 0) json = emccModule.UTF8ToString(outPtr, result);

  emccModule._free(nmPtr);
  emccModule._free(stTsPtr);
  emccModule._free(stIdxPtr);
  emccModule._free(outPtr);

  return json ? JSON.parse(json) : null;
}

// ── 4. Seeded RNG ──────────────────────────────────────────────────────────

function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const rng = mulberry32(42);
const START_MS = new Date('1950-01-01T00:00:00Z').getTime();
const END_MS = new Date('2080-01-01T00:00:00Z').getTime();

function randomTimestamps(count) {
  const ts = [];
  for (let i = 0; i < count; i++) ts.push(Math.floor(START_MS + rng() * (END_MS - START_MS)));
  return ts;
}

const TZ = 'Asia/Shanghai';
const CST_OFFSET_SEC = 28800;

// ── 5. Burst benchmark (500 requests) ──────────────────────────────────────

console.log('Running lunisolar burst benchmark (500 requests)...');
console.log('  Functions under test:');
console.log('    TS:   LunisolarCalendar.fromSolarDate(date, timezone)');
console.log('    Rust: wasm.fromSolarDate(tsMs, tzOffsetSec, newMoonsJson, solarTermsJson)');
console.log('    Emcc: emccModule._from_solar_date(tsMs, tzOffsetSec, nmPtr, nmCount, ...)');
console.log();

const timestamps500 = randomTimestamps(500);

const allYears = new Set();
for (const tsMs of timestamps500) {
  const y = new Date(tsMs).getUTCFullYear();
  allYears.add(y - 1);
  allYears.add(y);
  allYears.add(y + 1);
}
const bulkData = loadDataForYears([...allYears].sort((a, b) => a - b));
const bulkNewMoonsJson = JSON.stringify(bulkData.newMoons);
const bulkSolarTermsJson = JSON.stringify(bulkData.solarTerms);

// TS
const tsStart = performance.now();
let tsOK = 0;
for (const tsMs of timestamps500) {
  try { await LunisolarCalendar.fromSolarDate(new Date(tsMs), TZ); tsOK++; } catch { /* */ }
}
const tsTime = performance.now() - tsStart;

// Rust WASM
const wasmStart = performance.now();
let wasmOK = 0;
for (const tsMs of timestamps500) {
  try { wasm.fromSolarDate(tsMs, CST_OFFSET_SEC, bulkNewMoonsJson, bulkSolarTermsJson); wasmOK++; } catch { /* */ }
}
const wasmTime = performance.now() - wasmStart;

// Emscripten WASM
const emccStart = performance.now();
let emccOK = 0;
for (const tsMs of timestamps500) {
  try { if (emccFromSolarDate(tsMs, CST_OFFSET_SEC, bulkData.newMoons, bulkData.solarTerms)) emccOK++; } catch { /* */ }
}
const emccTime = performance.now() - emccStart;

// ── 6. Generate report ─────────────────────────────────────────────────────

const wasmSpeedup = tsTime / wasmTime;
const emccSpeedup = tsTime / emccTime;
const emccVsWasm = wasmTime / emccTime;

let md = `# Lunisolar Calendar Conversion — Burst Benchmark (500 Requests)\n\n`;
md += `Each call converts a Unix-epoch timestamp to a full lunisolar date\n`;
md += `(lunar year/month/day, leap month flag, four ganzhi with cycle indices).\n\n`;

md += `## Throughput\n\n`;
md += `| Implementation | Total (ms) | Avg/req (ms) | OK | Failed |\n`;
md += `|----------------|----------:|-----------:|---:|-------:|\n`;
md += `| TypeScript pkg | ${tsTime.toFixed(1)} | ${(tsTime / 500).toFixed(3)} | ${tsOK} | ${500 - tsOK} |\n`;
md += `| Rust WASM (wasm-pack) | ${wasmTime.toFixed(1)} | ${(wasmTime / 500).toFixed(3)} | ${wasmOK} | ${500 - wasmOK} |\n`;
md += `| Emscripten WASM (emcc) | ${emccTime.toFixed(1)} | ${(emccTime / 500).toFixed(3)} | ${emccOK} | ${500 - emccOK} |\n\n`;

md += `**Speed ratios:**\n`;
md += `- Rust WASM is **${wasmSpeedup.toFixed(2)}x** ${wasmSpeedup > 1 ? 'faster' : 'slower'} than TypeScript\n`;
md += `- Emscripten WASM is **${emccSpeedup.toFixed(2)}x** ${emccSpeedup > 1 ? 'faster' : 'slower'} than TypeScript\n`;
md += `- Emscripten vs Rust: **${emccVsWasm.toFixed(2)}x** ${emccVsWasm > 1 ? 'faster' : 'slower'}\n\n`;

md += `## Functions Called\n\n`;
md += `| Implementation | Function |\n`;
md += `|----------------|----------|\n`;
md += `| TypeScript pkg | \`LunisolarCalendar.fromSolarDate(date, timezone)\` |\n`;
md += `| Rust WASM (wasm-pack) | \`wasm.fromSolarDate(tsMs, tzOffsetSec, newMoonsJson, solarTermsJson)\` |\n`;
md += `| Emscripten WASM (emcc) | \`emccModule._from_solar_date(tsMs, tzOffsetSec, nmPtr, nmCount, stTsPtr, stIdxPtr, stCount, outPtr, outBufLen)\` |\n`;

const reportPath = resolve(__dirname, 'lunisolar-benchmark-report.md');
writeFileSync(reportPath, md);
console.log(`Report written to ${reportPath}`);
console.log(`TS: ${tsTime.toFixed(1)}ms, WASM: ${wasmTime.toFixed(1)}ms, EMCC: ${emccTime.toFixed(1)}ms`);
console.log(`Speedup: WASM ${wasmSpeedup.toFixed(2)}x, EMCC ${emccSpeedup.toFixed(2)}x faster than TS`);

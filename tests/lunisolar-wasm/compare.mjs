/**
 * Lunisolar WASM vs TypeScript Comparison & Benchmark
 *
 * 1. Generates 50 random timestamps and compares results from the Rust WASM,
 *    Emscripten WASM, and TypeScript implementations in a markdown table.
 *    Comparison includes year ganzhi, month ganzhi, day ganzhi, and hour ganzhi.
 * 2. Runs a burst of 500 requests to compare speed between all three.
 *
 * Usage:  node compare.mjs
 * Outputs: compare-report.md
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { performance } from 'node:perf_hooks';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..', '..');

// ── 1. Load the TypeScript package ──────────────────────────────────────────

const { LunisolarCalendar, configure } = await import(
  resolve(ROOT, 'pkg', 'dist', 'index.mjs')
);
configure({ strategy: 'static' });

// ── 2. Load the Rust WASM package ───────────────────────────────────────────

const wasm = await import(resolve(ROOT, 'wasm', 'lunisolar', 'pkg', 'lunisolar_wasm.js'));

// ── 3. Load the Emscripten WASM package ─────────────────────────────────────

const createLunisolarEmcc = (await import(resolve(ROOT, 'wasm', 'lunisolar-emcc', 'pkg', 'lunisolar_emcc.mjs'))).default;
const emccModule = await createLunisolarEmcc();

// ── 4. Data loader helper ───────────────────────────────────────────────────

const dataDir = resolve(ROOT, 'output', 'json');

function loadJson(kind, year) {
  const path = resolve(dataDir, kind, `${year}.json`);
  return JSON.parse(readFileSync(path, 'utf-8'));
}

function loadDataForYears(years) {
  let newMoons = [];
  let solarTerms = [];
  for (const y of years) {
    try {
      newMoons = newMoons.concat(loadJson('new_moons', y));
    } catch { /* skip if not available */ }
    try {
      solarTerms = solarTerms.concat(loadJson('solar_terms', y));
    } catch { /* skip if not available */ }
  }
  return { newMoons, solarTerms };
}

// ── 5. Ganzhi cycle helpers ─────────────────────────────────────────────────

const STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
const BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];

/**
 * Compute sexagenary cycle number (1–60) from stem and branch characters.
 * Returns -1 if the character is not found (encoding mismatch).
 */
function cycleFromChars(stem, branch) {
  const s = STEMS.indexOf(stem);
  const b = BRANCHES.indexOf(branch);
  if (s < 0 || b < 0) return -1;
  for (let c = 1; c <= 60; c++) {
    if ((c - 1) % 10 === s && (c - 1) % 12 === b) return c;
  }
  return -1;
}

// ── 6. Timezone offset helper ───────────────────────────────────────────────

/**
 * Compute the actual UTC offset in seconds for a given timestamp in a timezone.
 * This handles historical DST (e.g. China's DST during 1986–1991).
 */
function getTzOffsetSeconds(dateMs, tz) {
  const d = new Date(dateMs);
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: tz,
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
    second: 'numeric',
    hour12: false,
  }).formatToParts(d);

  const get = (type) => {
    const p = parts.find((p) => p.type === type);
    let v = p ? parseInt(p.value) : 0;
    // Intl.DateTimeFormat can represent midnight as hour 24 of the prior day
    if (type === 'hour' && v === 24) v = 0;
    return v;
  };

  const localYear = get('year');
  const localMonth = get('month');
  const localDay = get('day');
  const localHour = get('hour');
  const localMinute = get('minute');
  const localSecond = get('second');

  const utcMs = Date.UTC(
    d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate(),
    d.getUTCHours(), d.getUTCMinutes(), d.getUTCSeconds(),
  );
  const localMs = Date.UTC(localYear, localMonth - 1, localDay, localHour, localMinute, localSecond);

  return Math.round((localMs - utcMs) / 1000);
}

// ── 7. Emscripten WASM wrapper ──────────────────────────────────────────────

/**
 * Call the Emscripten-compiled from_solar_date function.
 * Marshals arrays into WASM linear memory and reads the JSON result.
 */
function emccFromSolarDate(timestampMs, tzOffsetSeconds, newMoons, solarTerms) {
  const nmCount = newMoons.length;
  const stCount = solarTerms.length;

  // Allocate memory for arrays
  const nmPtr = emccModule._malloc(nmCount * 8); // Float64
  const stTsPtr = emccModule._malloc(stCount * 8); // Float64
  const stIdxPtr = emccModule._malloc(stCount * 4); // Uint32
  const outBufLen = 1024;
  const outPtr = emccModule._malloc(outBufLen);

  // Write new moon timestamps (Float64)
  for (let i = 0; i < nmCount; i++) {
    emccModule.HEAPF64[(nmPtr >> 3) + i] = newMoons[i];
  }
  // Write solar term timestamps (Float64) and indices (Uint32)
  for (let i = 0; i < stCount; i++) {
    emccModule.HEAPF64[(stTsPtr >> 3) + i] = solarTerms[i][0];
    emccModule.HEAPU32[(stIdxPtr >> 2) + i] = solarTerms[i][1];
  }

  const result = emccModule._from_solar_date(
    timestampMs, tzOffsetSeconds,
    nmPtr, nmCount,
    stTsPtr, stIdxPtr, stCount,
    outPtr, outBufLen,
  );

  let json = null;
  if (result > 0) {
    json = emccModule.UTF8ToString(outPtr, result);
  }

  emccModule._free(nmPtr);
  emccModule._free(stTsPtr);
  emccModule._free(stIdxPtr);
  emccModule._free(outPtr);

  return json ? JSON.parse(json) : null;
}

// ── 8. Generate random timestamps ──────────────────────────────────────────

// Use a simple seeded RNG for reproducibility
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
  const timestamps = [];
  for (let i = 0; i < count; i++) {
    const ms = Math.floor(START_MS + rng() * (END_MS - START_MS));
    timestamps.push(ms);
  }
  return timestamps;
}

const TZ = 'Asia/Shanghai';

// ── 9. Run comparison for 50 timestamps ─────────────────────────────────────

const timestamps50 = randomTimestamps(50);
const results = [];

console.log('Running comparison for 50 random timestamps...');

for (const tsMs of timestamps50) {
  const date = new Date(tsMs);
  const year = date.getUTCFullYear();
  const { newMoons, solarTerms } = loadDataForYears([year - 1, year, year + 1]);
  const tzOffsetSec = getTzOffsetSeconds(tsMs, TZ);

  let tsResult = null;
  let wasmResult = null;
  let emccResult = null;
  let match = false;

  // TypeScript (TS returns only character strings; compute cycle indices here)
  try {
    const cal = await LunisolarCalendar.fromSolarDate(date, TZ);
    const yc = cycleFromChars(cal.yearStem, cal.yearBranch);
    const mc = cycleFromChars(cal.monthStem, cal.monthBranch);
    const dc = cycleFromChars(cal.dayStem, cal.dayBranch);
    const hc = cycleFromChars(cal.hourStem, cal.hourBranch);
    if (yc < 0 || mc < 0 || dc < 0 || hc < 0) {
      console.warn(`  ⚠️ Encoding issue at ${date.toISOString()}: cycle lookup failed (y=${yc} m=${mc} d=${dc} h=${hc})`);
    }
    tsResult = {
      lunarYear: cal.lunarYear,
      lunarMonth: cal.lunarMonth,
      lunarDay: cal.lunarDay,
      isLeapMonth: cal.isLeapMonth,
      yearStem: cal.yearStem,
      yearBranch: cal.yearBranch,
      yearCycle: yc,
      monthStem: cal.monthStem,
      monthBranch: cal.monthBranch,
      monthCycle: mc,
      dayStem: cal.dayStem,
      dayBranch: cal.dayBranch,
      dayCycle: dc,
      hourStem: cal.hourStem,
      hourBranch: cal.hourBranch,
      hourCycle: hc,
    };
  } catch (e) {
    tsResult = { error: e.message };
  }

  // Rust WASM
  try {
    const json = wasm.fromSolarDate(
      tsMs,
      tzOffsetSec,
      JSON.stringify(newMoons),
      JSON.stringify(solarTerms),
    );
    wasmResult = JSON.parse(json);
  } catch (e) {
    wasmResult = { error: e.message };
  }

  // Emscripten WASM
  try {
    emccResult = emccFromSolarDate(tsMs, tzOffsetSec, newMoons, solarTerms);
    if (!emccResult) emccResult = { error: 'from_solar_date returned -1' };
  } catch (e) {
    emccResult = { error: e.message };
  }

  // Compare TS vs Rust WASM (all four ganzhi — characters AND cycle indices)
  if (tsResult && wasmResult && !tsResult.error && !wasmResult.error) {
    match =
      tsResult.lunarYear === wasmResult.lunarYear &&
      tsResult.lunarMonth === wasmResult.lunarMonth &&
      tsResult.lunarDay === wasmResult.lunarDay &&
      tsResult.isLeapMonth === wasmResult.isLeapMonth &&
      tsResult.yearCycle === wasmResult.yearCycle &&
      tsResult.monthCycle === wasmResult.monthCycle &&
      tsResult.dayCycle === wasmResult.dayCycle &&
      tsResult.hourCycle === wasmResult.hourCycle &&
      tsResult.yearStem === wasmResult.yearStem &&
      tsResult.yearBranch === wasmResult.yearBranch &&
      tsResult.monthStem === wasmResult.monthStem &&
      tsResult.monthBranch === wasmResult.monthBranch &&
      tsResult.dayStem === wasmResult.dayStem &&
      tsResult.dayBranch === wasmResult.dayBranch &&
      tsResult.hourStem === wasmResult.hourStem &&
      tsResult.hourBranch === wasmResult.hourBranch;
  }

  results.push({ tsMs, date: date.toISOString(), tsResult, wasmResult, emccResult, match });
}

// ── 10. Run burst benchmark (500 requests) ──────────────────────────────────

console.log('Running burst benchmark (500 requests)...');

const timestamps500 = randomTimestamps(500);

// Pre-load all data needed for the timestamps
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

// Benchmark TS
const tsStart = performance.now();
let tsSuccessCount = 0;
for (const tsMs of timestamps500) {
  try {
    await LunisolarCalendar.fromSolarDate(new Date(tsMs), TZ);
    tsSuccessCount++;
  } catch { /* count failures */ }
}
const tsElapsed = performance.now() - tsStart;

// Benchmark Rust WASM
const wasmStart = performance.now();
let wasmSuccessCount = 0;
for (const tsMs of timestamps500) {
  try {
    const tzOff = getTzOffsetSeconds(tsMs, TZ);
    wasm.fromSolarDate(tsMs, tzOff, bulkNewMoonsJson, bulkSolarTermsJson);
    wasmSuccessCount++;
  } catch { /* count failures */ }
}
const wasmElapsed = performance.now() - wasmStart;

// Benchmark Emscripten WASM
const emccStart = performance.now();
let emccSuccessCount = 0;
for (const tsMs of timestamps500) {
  try {
    const tzOff = getTzOffsetSeconds(tsMs, TZ);
    const r = emccFromSolarDate(tsMs, tzOff, bulkData.newMoons, bulkData.solarTerms);
    if (r) emccSuccessCount++;
  } catch { /* count failures */ }
}
const emccElapsed = performance.now() - emccStart;

// ── 11. Generate markdown report ────────────────────────────────────────────

const matchCount = results.filter((r) => r.match).length;
const errorCount = results.filter(
  (r) => r.tsResult?.error || r.wasmResult?.error,
).length;

let md = `# Lunisolar WASM vs TypeScript — Comparison Report\n\n`;
md += `**Date**: ${new Date().toISOString()}\n\n`;

// Summary
md += `## Summary\n\n`;
md += `| Metric | Value |\n`;
md += `|--------|-------|\n`;
md += `| Total comparisons | ${results.length} |\n`;
md += `| Matching results (TS vs Rust WASM) | ${matchCount} |\n`;
md += `| Mismatches | ${results.length - matchCount - errorCount} |\n`;
md += `| Errors | ${errorCount} |\n\n`;

// Comparison table with all four ganzhi (characters + cycle indices)
md += `## Comparison Table (50 Random Timestamps)\n\n`;
md += `| # | UTC Date | Lunar Date | Year Ganzhi | Month Ganzhi | Day Ganzhi | Hour Ganzhi | Match |\n`;
md += `|---|----------|------------|-------------|--------------|------------|-------------|-------|\n`;

for (let i = 0; i < results.length; i++) {
  const r = results[i];
  const ts = r.tsResult;
  const w = r.wasmResult;

  const lunarDate = ts?.error
    ? `ERROR`
    : `${ts.lunarYear}-${ts.lunarMonth}-${ts.lunarDay}${ts.isLeapMonth ? '(闰)' : ''}`;

  // Show characters with cycle index: e.g. "甲子(1)"
  const fmtG = (stem, branch, cycle) => `${stem}${branch}(${cycle})`;

  const yearG = ts?.error ? '-' : fmtG(ts.yearStem, ts.yearBranch, ts.yearCycle);
  const monthG = ts?.error ? '-' : fmtG(ts.monthStem, ts.monthBranch, ts.monthCycle);
  const dayG = ts?.error ? '-' : fmtG(ts.dayStem, ts.dayBranch, ts.dayCycle);
  const hourG = ts?.error ? '-' : fmtG(ts.hourStem, ts.hourBranch, ts.hourCycle);

  // Per-field match: compare BOTH characters AND cycle indices
  const yCharMatch = !ts?.error && !w?.error && ts.yearStem === w.yearStem && ts.yearBranch === w.yearBranch;
  const yIdxMatch = !ts?.error && !w?.error && ts.yearCycle === w.yearCycle;
  const mCharMatch = !ts?.error && !w?.error && ts.monthStem === w.monthStem && ts.monthBranch === w.monthBranch;
  const mIdxMatch = !ts?.error && !w?.error && ts.monthCycle === w.monthCycle;
  const dCharMatch = !ts?.error && !w?.error && ts.dayStem === w.dayStem && ts.dayBranch === w.dayBranch;
  const dIdxMatch = !ts?.error && !w?.error && ts.dayCycle === w.dayCycle;
  const hCharMatch = !ts?.error && !w?.error && ts.hourStem === w.hourStem && ts.hourBranch === w.hourBranch;
  const hIdxMatch = !ts?.error && !w?.error && ts.hourCycle === w.hourCycle;

  // Show ✅ if both match, ⚠️ if only index matches (encoding issue), ❌ if neither
  const matchIcon = (charOk, idxOk) => charOk && idxOk ? '✅' : idxOk ? '⚠️' : '❌';
  const yIcon = matchIcon(yCharMatch, yIdxMatch);
  const mIcon = matchIcon(mCharMatch, mIdxMatch);
  const dIcon = matchIcon(dCharMatch, dIdxMatch);
  const hIcon = matchIcon(hCharMatch, hIdxMatch);

  const icon = r.match ? '✅' : r.tsResult?.error || r.wasmResult?.error ? '⚠️' : '❌';

  md += `| ${i + 1} | ${r.date.slice(0, 19)} | ${lunarDate} | ${yearG} ${yIcon} | ${monthG} ${mIcon} | ${dayG} ${dIcon} | ${hourG} ${hIcon} | ${icon} |\n`;
}

// Benchmark results
md += `\n## Burst Benchmark (500 Requests)\n\n`;
md += `| Implementation | Total Time (ms) | Avg per Request (ms) | Successful | Failed |\n`;
md += `|----------------|-----------------|----------------------|------------|--------|\n`;
md += `| TypeScript | ${tsElapsed.toFixed(1)} | ${(tsElapsed / 500).toFixed(3)} | ${tsSuccessCount} | ${500 - tsSuccessCount} |\n`;
md += `| Rust WASM (wasm-pack) | ${wasmElapsed.toFixed(1)} | ${(wasmElapsed / 500).toFixed(3)} | ${wasmSuccessCount} | ${500 - wasmSuccessCount} |\n`;
md += `| Emscripten WASM (emcc) | ${emccElapsed.toFixed(1)} | ${(emccElapsed / 500).toFixed(3)} | ${emccSuccessCount} | ${500 - emccSuccessCount} |\n`;
md += `\n`;

const speedupWasm = tsElapsed / wasmElapsed;
const speedupEmcc = tsElapsed / emccElapsed;
const emccVsWasm = wasmElapsed / emccElapsed;
md += `**Speed ratios:**\n`;
md += `- Rust WASM is **${speedupWasm.toFixed(2)}x** ${speedupWasm > 1 ? 'faster' : 'slower'} than TypeScript\n`;
md += `- Emscripten WASM is **${speedupEmcc.toFixed(2)}x** ${speedupEmcc > 1 ? 'faster' : 'slower'} than TypeScript\n`;
md += `- Emscripten WASM is **${emccVsWasm.toFixed(2)}x** ${emccVsWasm > 1 ? 'faster' : 'slower'} than Rust WASM\n`;

md += `\n## Notes\n\n`;
md += `- The Rust WASM build uses \`wasm-pack\` + \`wasm-bindgen\` (JSON string interface).\n`;
md += `- The Emscripten WASM build uses \`emcc\` from C source (pre-parsed array interface via linear memory).\n`;
md += `- Both WASM variants receive the actual timezone offset computed via \`Intl.DateTimeFormat\`,\n`;
md += `  matching the TypeScript implementation's DST-aware behavior.\n`;
md += `- All four ganzhi (year, month, day, hour) are compared field-by-field.\n`;

// Write report
const reportPath = resolve(__dirname, 'compare-report.md');
writeFileSync(reportPath, md);
console.log(`\nReport written to ${reportPath}`);
console.log(`\nMatch rate: ${matchCount}/${results.length}`);
console.log(`TS:   ${tsElapsed.toFixed(1)}ms for 500 requests (${(tsElapsed / 500).toFixed(3)}ms/req)`);
console.log(`WASM: ${wasmElapsed.toFixed(1)}ms for 500 requests (${(wasmElapsed / 500).toFixed(3)}ms/req)`);
console.log(`EMCC: ${emccElapsed.toFixed(1)}ms for 500 requests (${(emccElapsed / 500).toFixed(3)}ms/req)`);
console.log(`Speed: WASM ${speedupWasm.toFixed(2)}x, EMCC ${speedupEmcc.toFixed(2)}x faster than TS`);

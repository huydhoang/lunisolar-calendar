/**
 * Lunisolar WASM vs TypeScript Comparison & Benchmark
 *
 * 1. Generates 50 random timestamps and compares results from the Rust WASM
 *    and TypeScript implementations in a markdown table.
 * 2. Runs a burst of 500 requests to compare speed between the two.
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

// ── 3. Data loader helper ───────────────────────────────────────────────────

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

// ── 4. Generate random timestamps ──────────────────────────────────────────

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
const TZ_OFFSET_SEC = 8 * 3600; // CST = UTC+8

// ── 5. Run comparison for 50 timestamps ─────────────────────────────────────

const timestamps50 = randomTimestamps(50);
const results = [];

console.log('Running comparison for 50 random timestamps...');

for (const tsMs of timestamps50) {
  const date = new Date(tsMs);
  const year = date.getUTCFullYear();
  const { newMoons, solarTerms } = loadDataForYears([year - 1, year, year + 1]);

  let tsResult = null;
  let wasmResult = null;
  let match = false;

  // TypeScript
  try {
    const cal = await LunisolarCalendar.fromSolarDate(date, TZ);
    tsResult = {
      lunarYear: cal.lunarYear,
      lunarMonth: cal.lunarMonth,
      lunarDay: cal.lunarDay,
      isLeapMonth: cal.isLeapMonth,
      yearStem: cal.yearStem,
      yearBranch: cal.yearBranch,
      monthStem: cal.monthStem,
      monthBranch: cal.monthBranch,
      dayStem: cal.dayStem,
      dayBranch: cal.dayBranch,
      hourStem: cal.hourStem,
      hourBranch: cal.hourBranch,
    };
  } catch (e) {
    tsResult = { error: e.message };
  }

  // WASM
  try {
    const json = wasm.fromSolarDate(
      tsMs,
      TZ_OFFSET_SEC,
      JSON.stringify(newMoons),
      JSON.stringify(solarTerms),
    );
    wasmResult = JSON.parse(json);
  } catch (e) {
    wasmResult = { error: e.message };
  }

  // Compare
  if (tsResult && wasmResult && !tsResult.error && !wasmResult.error) {
    match =
      tsResult.lunarYear === wasmResult.lunarYear &&
      tsResult.lunarMonth === wasmResult.lunarMonth &&
      tsResult.lunarDay === wasmResult.lunarDay &&
      tsResult.isLeapMonth === wasmResult.isLeapMonth &&
      tsResult.yearStem === wasmResult.yearStem &&
      tsResult.yearBranch === wasmResult.yearBranch &&
      tsResult.monthStem === wasmResult.monthStem &&
      tsResult.monthBranch === wasmResult.monthBranch &&
      tsResult.dayStem === wasmResult.dayStem &&
      tsResult.dayBranch === wasmResult.dayBranch &&
      tsResult.hourStem === wasmResult.hourStem &&
      tsResult.hourBranch === wasmResult.hourBranch;
  }

  results.push({ tsMs, date: date.toISOString(), tsResult, wasmResult, match });
}

// ── 6. Run burst benchmark (500 requests) ───────────────────────────────────

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

// Benchmark WASM
const wasmStart = performance.now();
let wasmSuccessCount = 0;
for (const tsMs of timestamps500) {
  try {
    wasm.fromSolarDate(tsMs, TZ_OFFSET_SEC, bulkNewMoonsJson, bulkSolarTermsJson);
    wasmSuccessCount++;
  } catch { /* count failures */ }
}
const wasmElapsed = performance.now() - wasmStart;

// ── 7. Generate markdown report ─────────────────────────────────────────────

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
md += `| Matching results | ${matchCount} |\n`;
md += `| Mismatches | ${results.length - matchCount - errorCount} |\n`;
md += `| Errors | ${errorCount} |\n\n`;

// Comparison table
md += `## Comparison Table (50 Random Timestamps)\n\n`;
md += `| # | UTC Date | TS Lunar Date | WASM Lunar Date | TS Year Ganzhi | WASM Year Ganzhi | TS Day Ganzhi | WASM Day Ganzhi | Match |\n`;
md += `|---|----------|---------------|-----------------|----------------|------------------|---------------|-----------------|-------|\n`;

for (let i = 0; i < results.length; i++) {
  const r = results[i];
  const tsLunar = r.tsResult?.error
    ? `ERROR`
    : `${r.tsResult.lunarYear}-${r.tsResult.lunarMonth}-${r.tsResult.lunarDay}${r.tsResult.isLeapMonth ? '(闰)' : ''}`;
  const wasmLunar = r.wasmResult?.error
    ? `ERROR`
    : `${r.wasmResult.lunarYear}-${r.wasmResult.lunarMonth}-${r.wasmResult.lunarDay}${r.wasmResult.isLeapMonth ? '(闰)' : ''}`;
  const tsGanzhiY = r.tsResult?.error ? '-' : `${r.tsResult.yearStem}${r.tsResult.yearBranch}`;
  const wasmGanzhiY = r.wasmResult?.error ? '-' : `${r.wasmResult.yearStem}${r.wasmResult.yearBranch}`;
  const tsGanzhiD = r.tsResult?.error ? '-' : `${r.tsResult.dayStem}${r.tsResult.dayBranch}`;
  const wasmGanzhiD = r.wasmResult?.error ? '-' : `${r.wasmResult.dayStem}${r.wasmResult.dayBranch}`;
  const icon = r.match ? '✅' : r.tsResult?.error || r.wasmResult?.error ? '⚠️' : '❌';

  md += `| ${i + 1} | ${r.date.slice(0, 19)} | ${tsLunar} | ${wasmLunar} | ${tsGanzhiY} | ${wasmGanzhiY} | ${tsGanzhiD} | ${wasmGanzhiD} | ${icon} |\n`;
}

// Benchmark results
md += `\n## Burst Benchmark (500 Requests)\n\n`;
md += `| Implementation | Total Time (ms) | Avg per Request (ms) | Successful | Failed |\n`;
md += `|----------------|-----------------|----------------------|------------|--------|\n`;
md += `| TypeScript | ${tsElapsed.toFixed(1)} | ${(tsElapsed / 500).toFixed(3)} | ${tsSuccessCount} | ${500 - tsSuccessCount} |\n`;
md += `| Rust WASM | ${wasmElapsed.toFixed(1)} | ${(wasmElapsed / 500).toFixed(3)} | ${wasmSuccessCount} | ${500 - wasmSuccessCount} |\n`;
md += `\n`;

const speedup = tsElapsed / wasmElapsed;
md += `**Speed ratio**: WASM is **${speedup.toFixed(2)}x** ${speedup > 1 ? 'faster' : 'slower'} than TypeScript\n`;
md += `\n## Notes\n\n`;
md += `- The WASM implementation uses a fixed timezone offset (UTC+8 for CST), while the TypeScript\n`;
md += `  implementation uses \`Intl.DateTimeFormat\` which handles historical DST changes.\n`;
md += `- Minor hour-ganzhi mismatches are expected for dates during China's historical DST period (1986–1991)\n`;
md += `  when the actual offset was UTC+9 instead of UTC+8.\n`;
md += `- All core calendar logic (lunar year/month/day, year/month/day ganzhi) should match perfectly.\n`;

// Write report
const reportPath = resolve(__dirname, 'compare-report.md');
writeFileSync(reportPath, md);
console.log(`\nReport written to ${reportPath}`);
console.log(`\nMatch rate: ${matchCount}/${results.length}`);
console.log(`TS: ${tsElapsed.toFixed(1)}ms for 500 requests (${(tsElapsed / 500).toFixed(3)}ms/req)`);
console.log(`WASM: ${wasmElapsed.toFixed(1)}ms for 500 requests (${(wasmElapsed / 500).toFixed(3)}ms/req)`);
console.log(`Speed ratio: WASM is ${speedup.toFixed(2)}x ${speedup > 1 ? 'faster' : 'slower'}`);

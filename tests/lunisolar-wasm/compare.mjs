/**
 * Lunisolar Accuracy Test — Python Reference (DE440s) vs JS/WASM Implementations
 *
 * Generates 50 random timestamps and computes results from the Python
 * reference implementation (DE440s), Rust WASM, Emscripten WASM, and
 * TypeScript package.  Compares all three JS/WASM variants against
 * the Python ground truth in a markdown table.
 *
 * Usage:  node compare.mjs
 * Outputs: compare-report.md
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..', '..');

// ── 1. Load the TypeScript package ──────────────────────────────────────────

const { LunisolarCalendar, ConstructionStars, GreatYellowPath, configure } = await import(
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
const CST_OFFSET_SEC = 28800; // fixed UTC+8

// ── 9. Run comparison for 50 timestamps ─────────────────────────────────────

const timestamps50 = randomTimestamps(50);

console.log('Generating Python reference results (DE440s) for 50 timestamps...');

// Call Python batch reference script
const pyScript = resolve(__dirname, 'python_reference.py');
let pyResults;
try {
  const pyOut = execFileSync('python3', [pyScript, '--tz', TZ], {
    input: JSON.stringify(timestamps50),
    maxBuffer: 10 * 1024 * 1024,
    timeout: 120_000,
  });
  pyResults = JSON.parse(pyOut.toString());
} catch (e) {
  console.error('Python reference failed:', e.message);
  process.exit(1);
}

// Build a map of Python results by timestamp
const pyMap = new Map();
for (const r of pyResults) pyMap.set(r.tsMs, r);

console.log('Running comparison for 50 random timestamps...');

const results = [];

// Helper: compare all ganzhi fields between a reference and a candidate
function ganzhiMatch(ref, cand) {
  if (!ref || !cand || ref.error || cand.error) return false;
  return (
    ref.lunarYear === cand.lunarYear &&
    ref.lunarMonth === cand.lunarMonth &&
    ref.lunarDay === cand.lunarDay &&
    ref.isLeapMonth === cand.isLeapMonth &&
    ref.yearCycle === cand.yearCycle &&
    ref.monthCycle === cand.monthCycle &&
    ref.dayCycle === cand.dayCycle &&
    ref.hourCycle === cand.hourCycle &&
    ref.yearStem === cand.yearStem &&
    ref.yearBranch === cand.yearBranch &&
    ref.monthStem === cand.monthStem &&
    ref.monthBranch === cand.monthBranch &&
    ref.dayStem === cand.dayStem &&
    ref.dayBranch === cand.dayBranch &&
    ref.hourStem === cand.hourStem &&
    ref.hourBranch === cand.hourBranch
  );
}

// Helper: compare huangdao fields (construction star + great yellow path)
function huangdaoMatch(ref, cand) {
  if (!ref || !cand || ref.error || cand.error) return false;
  if (!ref.constructionStar || !cand.constructionStar) return false;
  return (
    ref.constructionStar === cand.constructionStar &&
    ref.gypSpirit === cand.gypSpirit &&
    ref.gypPathType === cand.gypPathType
  );
}

for (const tsMs of timestamps50) {
  const date = new Date(tsMs);
  const year = date.getUTCFullYear();
  const { newMoons, solarTerms } = loadDataForYears([year - 1, year, year + 1]);
  const tzOffsetSec = getTzOffsetSeconds(tsMs, TZ);

  const pyRef = pyMap.get(tsMs) || { error: 'not found in Python output' };

  let tsResult = null;
  let wasmResult = null;
  let emccResult = null;

  // TypeScript
  try {
    const cal = await LunisolarCalendar.fromSolarDate(date, TZ);
    const yc = cycleFromChars(cal.yearStem, cal.yearBranch);
    const mc = cycleFromChars(cal.monthStem, cal.monthBranch);
    const dc = cycleFromChars(cal.dayStem, cal.dayBranch);
    const hc = cycleFromChars(cal.hourStem, cal.hourBranch);

    // Construction star + Great Yellow Path
    const cs = new ConstructionStars(cal).getStar();
    const gyp = new GreatYellowPath(cal).getSpirit();

    tsResult = {
      lunarYear: cal.lunarYear, lunarMonth: cal.lunarMonth, lunarDay: cal.lunarDay,
      isLeapMonth: cal.isLeapMonth,
      yearStem: cal.yearStem, yearBranch: cal.yearBranch, yearCycle: yc,
      monthStem: cal.monthStem, monthBranch: cal.monthBranch, monthCycle: mc,
      dayStem: cal.dayStem, dayBranch: cal.dayBranch, dayCycle: dc,
      hourStem: cal.hourStem, hourBranch: cal.hourBranch, hourCycle: hc,
      constructionStar: cs.name,
      gypSpirit: gyp.name,
      gypPathType: gyp.type === 'Yellow Path' ? '黄道' : '黑道',
    };
  } catch (e) {
    tsResult = { error: e.message };
  }

  // Rust WASM
  try {
    const json = wasm.fromSolarDate(tsMs, tzOffsetSec, JSON.stringify(newMoons), JSON.stringify(solarTerms));
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

  // Compare each variant against the Python reference
  const tsMatch = ganzhiMatch(pyRef, tsResult);
  const rustMatch = ganzhiMatch(pyRef, wasmResult);
  const emccMatch = ganzhiMatch(pyRef, emccResult);
  const tsHuangdaoMatch = huangdaoMatch(pyRef, tsResult);
  const rustHuangdaoMatch = huangdaoMatch(pyRef, wasmResult);
  const emccHuangdaoMatch = huangdaoMatch(pyRef, emccResult);

  results.push({ tsMs, date: date.toISOString(), pyRef, tsResult, wasmResult, emccResult, tsMatch, rustMatch, emccMatch, tsHuangdaoMatch, rustHuangdaoMatch, emccHuangdaoMatch });
}

// ── 10. Generate markdown report ────────────────────────────────────────────

const tsMatchCount = results.filter((r) => r.tsMatch).length;
const rustMatchCount = results.filter((r) => r.rustMatch).length;
const emccMatchCount = results.filter((r) => r.emccMatch).length;
const tsHuangdaoMatchCount = results.filter((r) => r.tsHuangdaoMatch).length;
const rustHuangdaoMatchCount = results.filter((r) => r.rustHuangdaoMatch).length;
const emccHuangdaoMatchCount = results.filter((r) => r.emccHuangdaoMatch).length;
const errorCount = results.filter(
  (r) => r.pyRef?.error || r.wasmResult?.error || r.emccResult?.error || r.tsResult?.error,
).length;

let md = `# Lunisolar Accuracy — Python Reference (DE440s) vs JS/WASM Implementations\n\n`;
md += `**Date**: ${new Date().toISOString()}\n\n`;
md += `**Reference**: Python \`lunisolar_v2.py\` + \`huangdao_systems_v2.py\` with JPL DE440s ephemeris (ground truth).\n`;
md += `All three implementations are compared against this reference.\n\n`;

// Summary
md += `## Summary\n\n`;
md += `### Ganzhi (Sexagenary Cycle)\n\n`;
md += `| Implementation | Match vs Python (DE440s) |\n`;
md += `|----------------|------------------------:|\n`;
md += `| TypeScript pkg | ${tsMatchCount}/${results.length} |\n`;
md += `| Rust WASM (wasm-pack) | ${rustMatchCount}/${results.length} |\n`;
md += `| Emscripten WASM (emcc) | ${emccMatchCount}/${results.length} |\n`;
md += `| Errors | ${errorCount} |\n\n`;

md += `### Huangdao (Construction Stars + Great Yellow Path)\n\n`;
md += `| Implementation | Match vs Python (DE440s) |\n`;
md += `|----------------|------------------------:|\n`;
md += `| TypeScript pkg | ${tsHuangdaoMatchCount}/${results.length} |\n`;
md += `| Rust WASM (wasm-pack) | ${rustHuangdaoMatchCount}/${results.length} |\n`;
md += `| Emscripten WASM (emcc) | ${emccHuangdaoMatchCount}/${results.length} |\n\n`;

// Comparison table: Python reference values with match status for all three implementations
md += `## Ganzhi Comparison Table (50 Random Timestamps)\n\n`;
md += `Reference values are from Python \`lunisolar_v2.py\` (DE440s).\n`;
md += `Match columns show whether each implementation agrees with the Python reference.\n\n`;
md += `| # | UTC Date | CST Date | Lunar Date (Python) | Year Ganzhi | Month Ganzhi | Day Ganzhi | Hour Ganzhi | TS | Rust | Emcc |\n`;
md += `|---|----------|----------|---------------------|-------------|--------------|------------|-------------|----|----- |------|\n`;

for (let i = 0; i < results.length; i++) {
  const r = results[i];
  const py = r.pyRef;

  // CST date (UTC+8)
  const cstDate = new Date(r.tsMs + CST_OFFSET_SEC * 1000);
  const cstStr = cstDate.toISOString().slice(0, 19).replace('T', ' ');

  const lunarDate = py?.error
    ? `ERROR`
    : `${py.lunarYear}-${py.lunarMonth}-${py.lunarDay}${py.isLeapMonth ? '(闰)' : ''}`;

  const fmtG = (stem, branch, cycle) => `${stem}${branch}(${cycle})`;

  const yearG = py?.error ? '-' : fmtG(py.yearStem, py.yearBranch, py.yearCycle);
  const monthG = py?.error ? '-' : fmtG(py.monthStem, py.monthBranch, py.monthCycle);
  const dayG = py?.error ? '-' : fmtG(py.dayStem, py.dayBranch, py.dayCycle);
  const hourG = py?.error ? '-' : fmtG(py.hourStem, py.hourBranch, py.hourCycle);

  const tsIcon = r.tsMatch ? '✅' : (py?.error || r.tsResult?.error) ? '⚠️' : '❌';
  const rustIcon = r.rustMatch ? '✅' : (py?.error || r.wasmResult?.error) ? '⚠️' : '❌';
  const emccIcon = r.emccMatch ? '✅' : (py?.error || r.emccResult?.error) ? '⚠️' : '❌';

  md += `| ${i + 1} | ${r.date.slice(0, 19)} | ${cstStr} | ${lunarDate} | ${yearG} | ${monthG} | ${dayG} | ${hourG} | ${tsIcon} | ${rustIcon} | ${emccIcon} |\n`;
}

// Huangdao comparison table
md += `\n## Huangdao Comparison Table (50 Random Timestamps)\n\n`;
md += `| # | UTC Date | Lunar Month | Day Branch | Star (Python) | Spirit (Python) | Path | TS | Rust | Emcc |\n`;
md += `|---|----------|-------------|------------|---------------|-----------------|------|----|------|------|\n`;

for (let i = 0; i < results.length; i++) {
  const r = results[i];
  const py = r.pyRef;

  const star = py?.constructionStar || '-';
  const spirit = py?.gypSpirit || '-';
  const path = py?.gypPathType || '-';
  const lm = py?.lunarMonth ?? '-';
  const db = py?.dayBranch || '-';

  const tsIcon = r.tsHuangdaoMatch ? '✅' : (py?.error || r.tsResult?.error) ? '⚠️' : '❌';
  const rustIcon = r.rustHuangdaoMatch ? '✅' : (py?.error || r.wasmResult?.error) ? '⚠️' : '❌';
  const emccIcon = r.emccHuangdaoMatch ? '✅' : (py?.error || r.emccResult?.error) ? '⚠️' : '❌';

  md += `| ${i + 1} | ${r.date.slice(0, 19)} | ${lm} | ${db} | ${star} | ${spirit} | ${path} | ${tsIcon} | ${rustIcon} | ${emccIcon} |\n`;
}

md += `\n## Notes\n\n`;
md += `- **Reference**: Python \`lunisolar_v2.py\` + \`huangdao_systems_v2.py\` with JPL DE440s ephemeris.\n`;
md += `- **Timezone offset** is computed dynamically per timestamp via \`Intl.DateTimeFormat\` (handles China DST 1986–1991).\n`;
md += `- **Day ganzhi** uses local wall-clock date for day counting (day boundary at local midnight).\n`;
md += `- **Hour ganzhi** uses local wall time from the dynamic timezone offset for the hour branch/stem.\n`;
md += `- **Construction Stars** use base calculation (lunar month building branch + day branch offset).\n`;
md += `- **Great Yellow Path** uses Azure Dragon monthly start position + day branch offset.\n`;
md += `- All four ganzhi (year, month, day, hour) with cycle indices are compared field-by-field.\n`;
md += `- Huangdao fields (construction star, GYP spirit, path type) are compared across all implementations.\n`;

// Write report
const reportPath = resolve(__dirname, 'compare-report.md');
writeFileSync(reportPath, md);
console.log(`\nReport written to ${reportPath}`);
console.log(`\nGanzhi match vs Python (DE440s): TS=${tsMatchCount}/${results.length}, Rust=${rustMatchCount}/${results.length}, Emcc=${emccMatchCount}/${results.length}`);
console.log(`Huangdao match vs Python (DE440s): TS=${tsHuangdaoMatchCount}/${results.length}, Rust=${rustHuangdaoMatchCount}/${results.length}, Emcc=${emccHuangdaoMatchCount}/${results.length}`);

/**
 * Lunisolar WASM Range Benchmark
 *
 * Measures throughput of batch solar→lunisolar conversion via
 * fromSolarDateRange() across three implementations:
 *
 *   - TypeScript pkg:  LunisolarCalendar.fromSolarDateRange(start, end, tz)
 *   - Rust WASM:       wasm.fromSolarDateRange(startDate, endDate, tzOffsetSec)
 *   - Emscripten WASM: emccModule._from_solar_date_range(sy,sm,sd,ey,em,ed,tz,out,len)
 *
 * Two scenarios:
 *   1. 30-day range  (e.g. 2025-01-01 to 2025-01-30)
 *   2. Full-year range (e.g. 2025-01-01 to 2025-12-31)
 *
 * Usage:  node benchmark-range.mjs
 * Outputs: lunisolar-range-benchmark-report.md
 */

import { writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..', '..');

// ── 1. Load implementations ────────────────────────────────────────────────

let LunisolarCalendar = null, configure = null;
try {
  ({ LunisolarCalendar, configure } = await import(
    resolve(ROOT, 'ports', 'lunisolar-ts', 'dist', 'index.mjs')
  ));
  configure({ strategy: 'static' });
} catch (err) {
  console.error(`[load] TypeScript package: ${err.message}`);
}

let wasm = null;
try {
  wasm = await import(resolve(ROOT, 'ports', 'lunisolar-rs', 'pkg', 'lunisolar_wasm.js'));
} catch (err) {
  console.error(`[load] Rust WASM: ${err.message}`);
}

let emccModule = null;
try {
  const createLunisolarEmcc = (await import(resolve(ROOT, 'pkg', 'lunisolar_emcc.mjs'))).default;
  emccModule = await createLunisolarEmcc();
} catch (err) {
  console.error(`[load] Emscripten WASM: ${err.message}`);
}

// ── 2. Emscripten WASM range wrapper ───────────────────────────────────────

function emccFromSolarDateRange(sy, sm, sd, ey, em, ed, tzOffsetSeconds) {
  // 512 KB — fits ~365 results × ~600 bytes JSON each, with headroom
  const outBufLen = 512 * 1024;
  const outPtr = emccModule._malloc(outBufLen);

  const result = emccModule._from_solar_date_range(
    sy, sm, sd, ey, em, ed, tzOffsetSeconds,
    outPtr, outBufLen,
  );

  let json = null;
  if (result > 0) json = emccModule.UTF8ToString(outPtr, result);

  emccModule._free(outPtr);

  return json ? JSON.parse(json) : null;
}

// ── 3. Benchmark helpers ───────────────────────────────────────────────────

const CST_OFFSET_SEC = 28800;
const TZ = 'Asia/Shanghai';
const WARMUP = 2;
const ITERATIONS = 5;

/** High-resolution timer in milliseconds. */
function now() {
  const [s, ns] = process.hrtime();
  return s * 1000 + ns / 1e6;
}

/**
 * Benchmark an async or sync function.
 * Returns { mean_ms, min_ms, max_ms, count }.
 */
async function bench(fn, iters = ITERATIONS, warmup = WARMUP) {
  // Warmup
  for (let i = 0; i < warmup; i++) await fn();

  let total = 0;
  let min = Infinity;
  let max = 0;
  let count = 0;

  for (let i = 0; i < iters; i++) {
    const start = now();
    const result = await fn();
    const elapsed = now() - start;
    total += elapsed;
    if (elapsed < min) min = elapsed;
    if (elapsed > max) max = elapsed;
    // count = number of results in the first iteration
    if (i === 0 && Array.isArray(result)) count = result.length;
    else if (i === 0 && typeof result === 'string') {
      try { count = JSON.parse(result).length; } catch { count = 0; }
    }
  }

  return {
    mean_ms: total / iters,
    min_ms: min,
    max_ms: max,
    count,
  };
}

/**
 * Run bench() wrapped in try-catch.
 * Logs the error and returns null on failure so other benchmarks proceed.
 */
async function safeBench(label, fn, iters = ITERATIONS, warmup = WARMUP) {
  try {
    return await bench(fn, iters, warmup);
  } catch (err) {
    console.error(`  ${label}: ERROR - ${err.message}`);
    return null;
  }
}

// ── 4. Run benchmarks ──────────────────────────────────────────────────────

const scenarios = [
  { name: '30-day range', startDate: '2025-01-01', endDate: '2025-01-30', days: 30 },
  { name: 'Full-year range', startDate: '2025-01-01', endDate: '2025-12-31', days: 365 },
];

let md = `# Lunisolar Calendar Conversion — Range Benchmark\n\n`;
md += `Each scenario batch-converts a contiguous range of solar dates to lunisolar dates,\n`;
md += `sharing a global cache of new moons, solar terms and other data.\n\n`;
md += `**Warmup:** ${WARMUP} iterations | **Measured:** ${ITERATIONS} iterations (mean of ${ITERATIONS})\n\n`;

for (const scenario of scenarios) {
  console.log(`\nRunning "${scenario.name}" benchmark...`);
  console.log(`  Range: ${scenario.startDate} → ${scenario.endDate} (${scenario.days} days)`);

  const startD = new Date(scenario.startDate + 'T12:00:00Z');
  const endD = new Date(scenario.endDate + 'T12:00:00Z');
  const [sy, sm, sd] = scenario.startDate.split('-').map(Number);
  const [ey, em, ed] = scenario.endDate.split('-').map(Number);

  // TypeScript
  const tsResult = LunisolarCalendar
    ? await safeBench('TS', () => LunisolarCalendar.fromSolarDateRange(startD, endD, TZ))
    : null;
  if (tsResult) console.log(`  TS:   ${tsResult.mean_ms.toFixed(1)} ms (${tsResult.count} dates)`);

  // Rust WASM
  const wasmResult = wasm
    ? await safeBench('WASM', () => { const r = wasm.fromSolarDateRange(scenario.startDate, scenario.endDate, CST_OFFSET_SEC); return r; })
    : null;
  if (wasmResult) console.log(`  WASM: ${wasmResult.mean_ms.toFixed(1)} ms`);

  // Emscripten WASM
  const emccResult = emccModule
    ? await safeBench('EMCC', () => emccFromSolarDateRange(sy, sm, sd, ey, em, ed, CST_OFFSET_SEC))
    : null;
  if (emccResult) console.log(`  EMCC: ${emccResult.mean_ms.toFixed(1)} ms`);

  const fmt = (r, field) => r ? r[field].toFixed(1) : 'N/A';

  md += `## ${scenario.name} (${scenario.days} days)\n\n`;
  md += `| Implementation | Mean (ms) | Min (ms) | Max (ms) | Dates |\n`;
  md += `|----------------|----------:|---------:|---------:|------:|\n`;
  md += `| TypeScript pkg | ${fmt(tsResult, 'mean_ms')} | ${fmt(tsResult, 'min_ms')} | ${fmt(tsResult, 'max_ms')} | ${tsResult ? tsResult.count : 'N/A'} |\n`;
  md += `| Rust WASM (wasm-pack) | ${fmt(wasmResult, 'mean_ms')} | ${fmt(wasmResult, 'min_ms')} | ${fmt(wasmResult, 'max_ms')} | ${scenario.days} |\n`;
  md += `| Emscripten WASM (emcc) | ${fmt(emccResult, 'mean_ms')} | ${fmt(emccResult, 'min_ms')} | ${fmt(emccResult, 'max_ms')} | ${scenario.days} |\n\n`;

  // Speed ratios (only when at least two results are available)
  const ratios = [];
  if (tsResult && wasmResult) {
    const r = tsResult.mean_ms / wasmResult.mean_ms;
    ratios.push(`- Rust WASM is **${r.toFixed(2)}x** ${r > 1 ? 'faster' : 'slower'} than TypeScript`);
  }
  if (tsResult && emccResult) {
    const r = tsResult.mean_ms / emccResult.mean_ms;
    ratios.push(`- Emscripten WASM is **${r.toFixed(2)}x** ${r > 1 ? 'faster' : 'slower'} than TypeScript`);
  }
  if (wasmResult && emccResult) {
    const r = wasmResult.mean_ms / emccResult.mean_ms;
    ratios.push(`- Emscripten vs Rust: **${r.toFixed(2)}x** ${r > 1 ? 'faster' : 'slower'}`);
  }
  if (ratios.length > 0) {
    md += `**Speed ratios:**\n${ratios.join('\n')}\n\n`;
  }
}

md += `## Functions Called\n\n`;
md += `| Implementation | Function |\n`;
md += `|----------------|----------|\n`;
md += `| TypeScript pkg | \`LunisolarCalendar.fromSolarDateRange(start, end, timezone)\` |\n`;
md += `| Rust WASM (wasm-pack) | \`wasm.fromSolarDateRange(startDate, endDate, tzOffsetSec)\` |\n`;
md += `| Emscripten WASM (emcc) | \`emccModule._from_solar_date_range(sy,sm,sd,ey,em,ed,tz,out,len)\` |\n`;

const reportPath = resolve(__dirname, 'lunisolar-range-benchmark-report.md');
writeFileSync(reportPath, md);
console.log(`\nReport written to ${reportPath}`);

/**
 * Lunisolar Accuracy Test — Python Reference (DE440s) vs JS/WASM Implementations
 *
 * Generates 50 random timestamps and computes results from the Python
 * reference implementation (DE440s), Rust WASM, Emscripten WASM, and
 * TypeScript package.  Compares all three JS/WASM variants against
 * the Python ground truth in a markdown table.
 *
 * Includes Bazi (Four Pillars) analysis verification.
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
  resolve(ROOT, 'ports', 'lunisolar-ts', 'dist', 'index.mjs')
);
configure({ strategy: 'static' });

// ── 2. Load the Rust WASM package ───────────────────────────────────────────

const wasm = await import(resolve(ROOT, 'ports', 'lunisolar-rs', 'pkg', 'lunisolar_wasm.js'));

// ── 3. Load the Emscripten WASM package ─────────────────────────────────────

const createLunisolarEmcc = (await import(resolve(ROOT, 'pkg', 'lunisolar_emcc.mjs'))).default;
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

function cycleFromChars(stem, branch) {
  const s = STEMS.indexOf(stem);
  const b = BRANCHES.indexOf(branch);
  if (s < 0 || b < 0) return -1;
  for (let c = 1; c <= 60; c++) {
    if ((c - 1) % 10 === s && (c - 1) % 12 === b) return c;
  }
  return -1;
}

function stemIdx(stem) {
  return STEMS.indexOf(stem);
}

function branchIdx(branch) {
  return BRANCHES.indexOf(branch);
}

// ── 6. Timezone offset helper ───────────────────────────────────────────────

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

// ── 7. Emscripten WASM wrapper (standalone) ─────────────────────────────────

function emccFromSolarDateAuto(timestampMs, tzOffsetSeconds) {
  const outBufLen = 1024;
  const outPtr = emccModule._malloc(outBufLen);

  const result = emccModule._from_solar_date_auto(
    timestampMs, tzOffsetSeconds,
    outPtr, outBufLen,
  );

  let json = null;
  if (result > 0) {
    json = emccModule.UTF8ToString(outPtr, result);
  }

  emccModule._free(outPtr);

  return json ? JSON.parse(json) : null;
}

// ── 8. Emscripten Bazi helpers ──────────────────────────────────────────────

const ELEMENT_NAMES = ['Wood', 'Fire', 'Earth', 'Metal', 'Water'];
const POLARITY_NAMES = ['Yang', 'Yin'];

function emccBaziStemElement(stemIdx) {
  return ELEMENT_NAMES[emccModule._bazi_stem_element(stemIdx)] || '';
}

function emccBaziStemPolarity(stemIdx) {
  return POLARITY_NAMES[emccModule._bazi_stem_polarity(stemIdx)] || '';
}

function emccBaziBranchElement(branchIdx) {
  return ELEMENT_NAMES[emccModule._bazi_branch_element(branchIdx)] || '';
}

function emccBaziTenGod(dmStemIdx, targetStemIdx) {
  const ptr = emccModule._bazi_ten_god(dmStemIdx, targetStemIdx);
  return emccModule.UTF8ToString(ptr);
}

function emccBaziLifeStage(stemIdx, branchIdx) {
  const outPtr = emccModule._malloc(64);
  emccModule._bazi_life_stage_detail(stemIdx, branchIdx, outPtr);
  const idx = emccModule.HEAP32[outPtr >> 2];
  const cnPtr = emccModule.HEAP32[(outPtr >> 2) + 1];
  const enPtr = emccModule.HEAP32[(outPtr >> 2) + 2];
  const viPtr = emccModule.HEAP32[(outPtr >> 2) + 3];
  const scPtr = emccModule.HEAP32[(outPtr >> 2) + 4];
  const result = {
    index: idx,
    chinese: emccModule.UTF8ToString(cnPtr),
    english: emccModule.UTF8ToString(enPtr),
    vietnamese: emccModule.UTF8ToString(viPtr),
    strengthClass: emccModule.UTF8ToString(scPtr),
  };
  emccModule._free(outPtr);
  return result;
}

function emccBaziNaYin(cycle) {
  const entryPtr = emccModule._bazi_nayin_for_cycle(cycle);
  if (!entryPtr) return null;
  const elemIdx = emccModule.HEAP32[entryPtr >> 2];
  const cnPtr = emccModule.HEAP32[(entryPtr >> 2) + 1];
  const viPtr = emccModule.HEAP32[(entryPtr >> 2) + 2];
  const enPtr = emccModule.HEAP32[(entryPtr >> 2) + 3];
  return {
    element: ELEMENT_NAMES[elemIdx],
    chinese: emccModule.UTF8ToString(cnPtr),
    vietnamese: emccModule.UTF8ToString(viPtr),
    english: emccModule.UTF8ToString(enPtr),
  };
}

const STEM_COMBINATION_SIZE = 20;
const TRANSFORMATION_SIZE = 48;
const PUNISHMENT_SIZE = 32;

function emccBaziDetectStemCombinations(pillars) {
  const maxCount = 50;
  const outPtr = emccModule._malloc(4 * 5 * maxCount);
  const pillarsPtr = emccModule._malloc(4 * 8);
  for (let i = 0; i < 4; i++) {
    emccModule.HEAP32[pillarsPtr / 4 + i * 2] = stemIdx(pillars[i].stem);
    emccModule.HEAP32[pillarsPtr / 4 + i * 2 + 1] = branchIdx(pillars[i].branch);
  }
  const count = emccModule._bazi_detect_stem_combinations(pillarsPtr, outPtr, maxCount);
  const results = [];
  for (let i = 0; i < count; i++) {
    const base = outPtr / 4 + i * 5;
    results.push({
      pairA: emccModule.HEAP32[base],
      pairB: emccModule.HEAP32[base + 1],
      stemA: STEMS[emccModule.HEAP32[base + 2]],
      stemB: STEMS[emccModule.HEAP32[base + 3]],
      targetElement: ELEMENT_NAMES[emccModule.HEAP32[base + 4]],
    });
  }
  emccModule._free(outPtr);
  emccModule._free(pillarsPtr);
  return results;
}

function emccBaziDetectTransformations(pillars) {
  const outPtr = emccModule._malloc(TRANSFORMATION_SIZE * 20);
  const pillarsPtr = emccModule._malloc(4 * 8);
  for (let i = 0; i < 4; i++) {
    emccModule.HEAP32[pillarsPtr / 4 + i * 2] = stemIdx(pillars[i].stem);
    emccModule.HEAP32[pillarsPtr / 4 + i * 2 + 1] = branchIdx(pillars[i].branch);
  }
  const count = emccModule._bazi_detect_transformations(pillarsPtr, outPtr, 20);
  const results = [];
  for (let i = 0; i < count; i++) {
    const base = outPtr + i * TRANSFORMATION_SIZE;
    results.push({
      pairA: emccModule.HEAP32[base / 4],
      pairB: emccModule.HEAP32[base / 4 + 1],
      stemA: STEMS[emccModule.HEAP32[base / 4 + 2]],
      stemB: STEMS[emccModule.HEAP32[base / 4 + 3]],
      targetElement: ELEMENT_NAMES[emccModule.HEAP32[base / 4 + 4]],
      monthSupport: emccModule.HEAP32[base / 4 + 5] !== 0,
      leadingPresent: emccModule.HEAP32[base / 4 + 6] !== 0,
      blocked: emccModule.HEAP32[base / 4 + 7] !== 0,
      severelyClashed: emccModule.HEAP32[base / 4 + 8] !== 0,
      proximityScore: emccModule.HEAP32[base / 4 + 9],
      status: emccModule.UTF8ToString(emccModule.HEAP32[base / 4 + 10]),
      confidence: emccModule.HEAP32[base / 4 + 11],
    });
  }
  emccModule._free(outPtr);
  emccModule._free(pillarsPtr);
  return results;
}

function emccBaziDetectPunishments(pillars) {
  const outPtr = emccModule._malloc(PUNISHMENT_SIZE * 20);
  const pillarsPtr = emccModule._malloc(4 * 8);
  for (let i = 0; i < 4; i++) {
    emccModule.HEAP32[pillarsPtr / 4 + i * 2] = stemIdx(pillars[i].stem);
    emccModule.HEAP32[pillarsPtr / 4 + i * 2 + 1] = branchIdx(pillars[i].branch);
  }
  const count = emccModule._bazi_detect_punishments(pillarsPtr, outPtr, 20);
  const results = [];
  for (let i = 0; i < count; i++) {
    const base = outPtr + i * PUNISHMENT_SIZE;
    results.push({
      type: emccModule.UTF8ToString(emccModule.HEAP32[base / 4]),
      pairA: emccModule.HEAP32[base / 4 + 1],
      pairB: emccModule.HEAP32[base / 4 + 2],
      branchA: BRANCHES[emccModule.HEAP32[base / 4 + 3]],
      branchB: BRANCHES[emccModule.HEAP32[base / 4 + 4]],
      severity: emccModule.HEAP32[base / 4 + 5],
      lifeArea1: emccModule.UTF8ToString(emccModule.HEAP32[base / 4 + 6]),
      lifeArea2: emccModule.UTF8ToString(emccModule.HEAP32[base / 4 + 7]),
    });
  }
  emccModule._free(outPtr);
  emccModule._free(pillarsPtr);
  return results;
}

// ── 9. Generate random timestamps ──────────────────────────────────────────

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
const CST_OFFSET_SEC = 28800;

// ── 10. Run comparison for 50 timestamps ─────────────────────────────────────

const timestamps50 = randomTimestamps(50);

console.log('Generating Python reference results (DE440s) for 50 timestamps...');

const pyScript = resolve(__dirname, 'python_reference.py');
let pyResults;
try {
  const pyOut = execFileSync('python3', [pyScript, '--tz', TZ, '--gender', 'male'], {
    input: JSON.stringify(timestamps50),
    maxBuffer: 10 * 1024 * 1024,
    timeout: 120_000,
  });
  pyResults = JSON.parse(pyOut.toString());
} catch (e) {
  console.error('Python reference failed:', e.message);
  process.exit(1);
}

const pyMap = new Map();
for (const r of pyResults) pyMap.set(r.tsMs, r);

console.log('Running comparison for 50 random timestamps...');

const results = [];

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

function huangdaoMatch(ref, cand) {
  if (!ref || !cand || ref.error || cand.error) return false;
  if (!ref.constructionStar || !cand.constructionStar) return false;
  return (
    ref.constructionStar === cand.constructionStar &&
    ref.gypSpirit === cand.gypSpirit &&
    ref.gypPathType === cand.gypPathType
  );
}

function baziMatch(ref, cand) {
  if (!ref || !cand || ref.error || cand.error) return false;
  if (!ref.bazi || !cand.bazi) return false;
  const refB = ref.bazi;
  const candB = cand.bazi;
  return (
    refB.dayMasterStem === candB.dayMasterStem &&
    refB.dayMasterElement === candB.dayMasterElement &&
    refB.dayMasterPolarity === candB.dayMasterPolarity &&
    JSON.stringify(refB.tenGods) === JSON.stringify(candB.tenGods)
  );
}

function baziLifeStagesMatch(ref, cand) {
  if (!ref?.bazi?.lifeStages || !cand?.bazi?.lifeStages) return false;
  const refLs = ref.bazi.lifeStages;
  const candLs = cand.bazi.lifeStages;
  for (const pname of ['year', 'month', 'day', 'hour']) {
    if (!refLs[pname] || !candLs[pname]) return false;
    if (refLs[pname].index !== candLs[pname].index) return false;
    if (refLs[pname].chinese !== candLs[pname].chinese) return false;
  }
  return true;
}

function baziNaYinMatch(ref, cand) {
  if (!ref?.bazi?.naYin || !cand?.bazi?.naYin) return false;
  const refNy = ref.bazi.naYin;
  const candNy = cand.bazi.naYin;
  for (const pname of ['year', 'month', 'day', 'hour']) {
    if (!refNy[pname] || !candNy[pname]) return false;
    if (refNy[pname].element !== candNy[pname].element) return false;
    if (refNy[pname].chinese !== candNy[pname].chinese) return false;
  }
  return true;
}

function baziStemCombinationsMatch(ref, cand) {
  if (!ref?.bazi?.stemCombinations || !cand?.bazi?.stemCombinations) return false;
  const refSc = ref.bazi.stemCombinations;
  const candSc = cand.bazi.stemCombinations;
  if (refSc.length !== candSc.length) return false;
  for (const refItem of refSc) {
    const found = candSc.find(c => {
      const pairA = c.pairA ?? c.pair?.[0];
      const pairB = c.pairB ?? c.pair?.[1];
      const targetElement = c.targetElement ?? c.target_element;
      return targetElement === refItem.targetElement &&
        ((pairA === refItem.pair[0] && pairB === refItem.pair[1]) ||
         (pairA === refItem.pair[1] && pairB === refItem.pair[0]));
    });
    if (!found) return false;
  }
  return true;
}

function baziTransformationsMatch(ref, cand) {
  if (!ref?.bazi?.transformations || !cand?.bazi?.transformations) return false;
  const refT = ref.bazi.transformations;
  const candT = cand.bazi.transformations;
  if (refT.length !== candT.length) return false;
  for (const refItem of refT) {
    const found = candT.find(c => {
      const pairA = c.pairA ?? c.pair?.[0];
      const pairB = c.pairB ?? c.pair?.[1];
      const targetElement = c.targetElement ?? c.target_element;
      const status = c.status;
      const confidence = c.confidence;
      return targetElement === refItem.targetElement &&
        status === refItem.status &&
        confidence === refItem.confidence &&
        ((pairA === refItem.pair[0] && pairB === refItem.pair[1]) ||
         (pairA === refItem.pair[1] && pairB === refItem.pair[0]));
    });
    if (!found) return false;
  }
  return true;
}

function baziPunishmentsMatch(ref, cand) {
  if (!ref?.bazi?.punishments || !cand?.bazi?.punishments) return false;
  const refP = ref.bazi.punishments;
  const candP = cand.bazi.punishments;
  if (refP.length !== candP.length) return false;
  for (const refItem of refP) {
    const found = candP.find(c => {
      const type = c.type ?? c.punishment_type;
      return type === refItem.type && c.severity === refItem.severity;
    });
    if (!found) return false;
  }
  return true;
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

  // Emscripten WASM (standalone)
  try {
    emccResult = emccFromSolarDateAuto(tsMs, tzOffsetSec);
    if (!emccResult) emccResult = { error: 'from_solar_date_auto returned -1' };
  } catch (e) {
    emccResult = { error: e.message };
  }

  // Emscripten Bazi analysis
  if (emccResult && !emccResult.error && pyRef && !pyRef.error && pyRef.bazi) {
    try {
      const dmStem = pyRef.dayStem;
      const dmIdx = stemIdx(dmStem);
      emccResult.bazi = {
        dayMasterStem: dmStem,
        dayMasterElement: emccBaziStemElement(dmIdx),
        dayMasterPolarity: emccBaziStemPolarity(dmIdx),
        tenGods: {
          year: emccBaziTenGod(dmIdx, stemIdx(pyRef.yearStem)),
          month: emccBaziTenGod(dmIdx, stemIdx(pyRef.monthStem)),
          day: '比肩',
          hour: emccBaziTenGod(dmIdx, stemIdx(pyRef.hourStem)),
        },
        lifeStages: {},
        naYin: {},
        stemCombinations: [],
        transformations: [],
        punishments: [],
      };
      for (const pname of ['year', 'month', 'day', 'hour']) {
        const cycle = pname === 'year' ? pyRef.yearCycle :
                      pname === 'month' ? pyRef.monthCycle :
                      pname === 'day' ? pyRef.dayCycle : pyRef.hourCycle;
        const branch = pname === 'year' ? pyRef.yearBranch :
                       pname === 'month' ? pyRef.monthBranch :
                       pname === 'day' ? pyRef.dayBranch : pyRef.hourBranch;
        emccResult.bazi.lifeStages[pname] = emccBaziLifeStage(dmIdx, branchIdx(branch));
        const nayin = emccBaziNaYin(cycle);
        if (nayin) {
          emccResult.bazi.naYin[pname] = nayin;
        }
      }
      const pillars = [
        { stem: pyRef.yearStem, branch: pyRef.yearBranch },
        { stem: pyRef.monthStem, branch: pyRef.monthBranch },
        { stem: pyRef.dayStem, branch: pyRef.dayBranch },
        { stem: pyRef.hourStem, branch: pyRef.hourBranch },
      ];
      emccResult.bazi.stemCombinations = emccBaziDetectStemCombinations(pillars);
      emccResult.bazi.transformations = emccBaziDetectTransformations(pillars);
      emccResult.bazi.punishments = emccBaziDetectPunishments(pillars);
    } catch (e) {
      emccResult.baziError = e.message;
    }
  }

  // Rust WASM Bazi analysis
  if (wasmResult && !wasmResult.error && pyRef && !pyRef.error && pyRef.bazi) {
    try {
      const dmStem = pyRef.dayStem;
      const dmIdx = stemIdx(dmStem);
      wasmResult.bazi = {
        dayMasterStem: dmStem,
        dayMasterElement: wasm.baziStemElement(dmIdx),
        dayMasterPolarity: wasm.baziStemPolarity(dmIdx),
        tenGods: {
          year: wasm.baziTenGod(dmIdx, stemIdx(pyRef.yearStem)),
          month: wasm.baziTenGod(dmIdx, stemIdx(pyRef.monthStem)),
          day: '比肩',
          hour: wasm.baziTenGod(dmIdx, stemIdx(pyRef.hourStem)),
        },
        lifeStages: {},
        naYin: {},
        stemCombinations: [],
        transformations: [],
        punishments: [],
      };
      for (const pname of ['year', 'month', 'day', 'hour']) {
        const cycle = pname === 'year' ? pyRef.yearCycle :
                      pname === 'month' ? pyRef.monthCycle :
                      pname === 'day' ? pyRef.dayCycle : pyRef.hourCycle;
        const branch = pname === 'year' ? pyRef.yearBranch :
                       pname === 'month' ? pyRef.monthBranch :
                       pname === 'day' ? pyRef.dayBranch : pyRef.hourBranch;
        const lsJson = wasm.baziChangshengStage(dmIdx, branchIdx(branch));
        wasmResult.bazi.lifeStages[pname] = JSON.parse(lsJson);
        const nayinJson = wasm.baziNaYin(cycle);
        if (nayinJson) {
          wasmResult.bazi.naYin[pname] = JSON.parse(nayinJson);
        }
      }
      const pillarsJson = JSON.stringify([
        [stemIdx(pyRef.yearStem), branchIdx(pyRef.yearBranch)],
        [stemIdx(pyRef.monthStem), branchIdx(pyRef.monthBranch)],
        [stemIdx(pyRef.dayStem), branchIdx(pyRef.dayBranch)],
        [stemIdx(pyRef.hourStem), branchIdx(pyRef.hourBranch)],
      ]);
      wasmResult.bazi.stemCombinations = JSON.parse(wasm.baziDetectStemCombinations(pillarsJson));
      wasmResult.bazi.transformations = JSON.parse(wasm.baziDetectTransformations(pillarsJson, branchIdx(pyRef.monthBranch)));
      wasmResult.bazi.punishments = JSON.parse(wasm.baziDetectPunishments(pillarsJson));
    } catch (e) {
      wasmResult.baziError = e.message;
    }
  }

  const tsMatch = ganzhiMatch(pyRef, tsResult);
  const rustMatch = ganzhiMatch(pyRef, wasmResult);
  const emccMatch = ganzhiMatch(pyRef, emccResult);
  const tsHuangdaoMatch = huangdaoMatch(pyRef, tsResult);
  const rustHuangdaoMatch = huangdaoMatch(pyRef, wasmResult);
  const emccHuangdaoMatch = huangdaoMatch(pyRef, emccResult);
  const emccBaziMatch = baziMatch(pyRef, emccResult);
  const emccLifeStagesMatch = baziLifeStagesMatch(pyRef, emccResult);
  const emccNaYinMatch = baziNaYinMatch(pyRef, emccResult);
  const emccStemCombosMatch = baziStemCombinationsMatch(pyRef, emccResult);
  const emccTransformationsMatch = baziTransformationsMatch(pyRef, emccResult);
  const emccPunishmentsMatch = baziPunishmentsMatch(pyRef, emccResult);
  const rustBaziMatch = baziMatch(pyRef, wasmResult);
  const rustLifeStagesMatch = baziLifeStagesMatch(pyRef, wasmResult);
  const rustNaYinMatch = baziNaYinMatch(pyRef, wasmResult);
  const rustStemCombosMatch = baziStemCombinationsMatch(pyRef, wasmResult);
  const rustTransformationsMatch = baziTransformationsMatch(pyRef, wasmResult);
  const rustPunishmentsMatch = baziPunishmentsMatch(pyRef, wasmResult);

  results.push({
    tsMs, date: date.toISOString(), pyRef, tsResult, wasmResult, emccResult,
    tsMatch, rustMatch, emccMatch,
    tsHuangdaoMatch, rustHuangdaoMatch, emccHuangdaoMatch,
    emccBaziMatch, emccLifeStagesMatch, emccNaYinMatch,
    emccStemCombosMatch, emccTransformationsMatch, emccPunishmentsMatch,
    rustBaziMatch, rustLifeStagesMatch, rustNaYinMatch,
    rustStemCombosMatch, rustTransformationsMatch, rustPunishmentsMatch,
  });
}

// ── 11. Generate markdown report ────────────────────────────────────────────

const tsMatchCount = results.filter((r) => r.tsMatch).length;
const rustMatchCount = results.filter((r) => r.rustMatch).length;
const emccMatchCount = results.filter((r) => r.emccMatch).length;
const tsHuangdaoMatchCount = results.filter((r) => r.tsHuangdaoMatch).length;
const rustHuangdaoMatchCount = results.filter((r) => r.rustHuangdaoMatch).length;
const emccHuangdaoMatchCount = results.filter((r) => r.emccHuangdaoMatch).length;
const emccBaziMatchCount = results.filter((r) => r.emccBaziMatch).length;
const emccLifeStagesMatchCount = results.filter((r) => r.emccLifeStagesMatch).length;
const emccNaYinMatchCount = results.filter((r) => r.emccNaYinMatch).length;
const emccStemCombosMatchCount = results.filter((r) => r.emccStemCombosMatch).length;
const emccTransformationsMatchCount = results.filter((r) => r.emccTransformationsMatch).length;
const emccPunishmentsMatchCount = results.filter((r) => r.emccPunishmentsMatch).length;
const rustBaziMatchCount = results.filter((r) => r.rustBaziMatch).length;
const rustLifeStagesMatchCount = results.filter((r) => r.rustLifeStagesMatch).length;
const rustNaYinMatchCount = results.filter((r) => r.rustNaYinMatch).length;
const rustStemCombosMatchCount = results.filter((r) => r.rustStemCombosMatch).length;
const rustTransformationsMatchCount = results.filter((r) => r.rustTransformationsMatch).length;
const rustPunishmentsMatchCount = results.filter((r) => r.rustPunishmentsMatch).length;
const errorCount = results.filter(
  (r) => r.pyRef?.error || r.wasmResult?.error || r.emccResult?.error || r.tsResult?.error,
).length;

let md = `# Lunisolar Accuracy — Python Reference (DE440s) vs JS/WASM Implementations\n\n`;
md += `**Date**: ${new Date().toISOString()}\n\n`;
md += `**Reference**: Python \`lunisolar_v2.py\` + \`bazi.py\` + \`huangdao_systems_v2.py\` with JPL DE440s ephemeris (ground truth).\n`;
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

md += `### Bazi (Four Pillars Analysis)\n\n`;
md += `| Test | Rust vs Python | Emcc vs Python |\n`;
md += `|------|---------------:|---------------:|\n`;
md += `| Ten Gods (十神) | ${rustBaziMatchCount}/${results.length} | ${emccBaziMatchCount}/${results.length} |\n`;
md += `| Life Stages (十二长生) | ${rustLifeStagesMatchCount}/${results.length} | ${emccLifeStagesMatchCount}/${results.length} |\n`;
md += `| Na Yin (納音) | ${rustNaYinMatchCount}/${results.length} | ${emccNaYinMatchCount}/${results.length} |\n`;
md += `| Stem Combinations (天干合) | ${rustStemCombosMatchCount}/${results.length} | ${emccStemCombosMatchCount}/${results.length} |\n`;
md += `| Transformations (合化) | ${rustTransformationsMatchCount}/${results.length} | ${emccTransformationsMatchCount}/${results.length} |\n`;
md += `| Punishments (刑害) | ${rustPunishmentsMatchCount}/${results.length} | ${emccPunishmentsMatchCount}/${results.length} |\n\n`;

// Ganzhi Comparison Table
md += `## Ganzhi Comparison Table (50 Random Timestamps)\n\n`;
md += `Reference values are from Python \`lunisolar_v2.py\` (DE440s).\n`;
md += `Match columns show whether each implementation agrees with the Python reference.\n\n`;
md += `| # | UTC Date | CST Date | Lunar Date (Python) | Year Ganzhi | Month Ganzhi | Day Ganzhi | Hour Ganzhi | TS | Rust | Emcc |\n`;
md += `|---|----------|----------|---------------------|-------------|--------------|------------|-------------|----|----- |------|\n`;

for (let i = 0; i < results.length; i++) {
  const r = results[i];
  const py = r.pyRef;

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

// Huangdao Comparison Table
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

// Bazi Comparison Table
md += `\n## Bazi Comparison Table (50 Random Timestamps)\n\n`;
md += `| # | Day Master | Element | Ten Gods (Y/M/H) | Life Stages (Y/M/D/H) | Na Yin Match |\n`;
md += `|---|------------|---------|-----------------|------------------------|-------------|\n`;

for (let i = 0; i < results.length; i++) {
  const r = results[i];
  const py = r.pyRef;
  const pyB = py?.bazi;

  if (!pyB) {
    md += `| ${i + 1} | - | - | - | - | - |\n`;
    continue;
  }

  const dm = pyB.dayMasterStem || '-';
  const elem = pyB.dayMasterElement || '-';
  const tg = pyB.tenGods || {};
  const tgStr = `${tg.year || '-'}/${tg.month || '-'}/${tg.hour || '-'}`;
  const ls = pyB.lifeStages || {};
  const lsStr = `${ls.year?.chinese || '-'}/${ls.month?.chinese || '-'}/${ls.day?.chinese || '-'}/${ls.hour?.chinese || '-'}`;
  const nayinIcon = r.emccNaYinMatch ? '✅' : '❌';

  md += `| ${i + 1} | ${dm} | ${elem} | ${tgStr} | ${lsStr} | ${nayinIcon} |\n`;
}

md += `\n## Notes\n\n`;
md += `- **Reference**: Python \`lunisolar_v2.py\` + \`bazi.py\` + \`huangdao_systems_v2.py\` with JPL DE440s ephemeris.\n`;
md += `- **Timezone offset** is computed dynamically per timestamp via \`Intl.DateTimeFormat\` (handles China DST 1986–1991).\n`;
md += `- **Day ganzhi** uses local wall-clock date for day counting (day boundary at local midnight).\n`;
md += `- **Hour ganzhi** uses local wall time from the dynamic timezone offset for the hour branch/stem.\n`;
md += `- **Construction Stars** use base calculation (lunar month building branch + day branch offset).\n`;
md += `- **Great Yellow Path** uses Azure Dragon monthly start position + day branch offset.\n`;
md += `- All four ganzhi (year, month, day, hour) with cycle indices are compared field-by-field.\n`;
md += `- Huangdao fields (construction star, GYP spirit, path type) are compared across all implementations.\n`;
md += `- **Bazi**: Ten Gods, Life Stages (十二长生), Na Yin (納音), Stem Combinations (天干合), Transformations (合化), and Punishments (刑害) are compared for both Rust WASM and Emcc vs Python.\n`;

// Write report
const reportPath = resolve(__dirname, 'compare-report.md');
writeFileSync(reportPath, md);
console.log(`\nReport written to ${reportPath}`);
console.log(`\nGanzhi match vs Python (DE440s): TS=${tsMatchCount}/${results.length}, Rust=${rustMatchCount}/${results.length}, Emcc=${emccMatchCount}/${results.length}`);
console.log(`Huangdao match vs Python (DE440s): TS=${tsHuangdaoMatchCount}/${results.length}, Rust=${rustHuangdaoMatchCount}/${results.length}, Emcc=${emccHuangdaoMatchCount}/${results.length}`);
console.log(`Bazi match vs Python (DE440s):`);
console.log(`  Ten Gods: Rust=${rustBaziMatchCount}/${results.length}, Emcc=${emccBaziMatchCount}/${results.length}`);
console.log(`  Life Stages: Rust=${rustLifeStagesMatchCount}/${results.length}, Emcc=${emccLifeStagesMatchCount}/${results.length}`);
console.log(`  Na Yin: Rust=${rustNaYinMatchCount}/${results.length}, Emcc=${emccNaYinMatchCount}/${results.length}`);
console.log(`  Stem Combinations: Rust=${rustStemCombosMatchCount}/${results.length}, Emcc=${emccStemCombosMatchCount}/${results.length}`);
console.log(`  Transformations: Rust=${rustTransformationsMatchCount}/${results.length}, Emcc=${emccTransformationsMatchCount}/${results.length}`);
console.log(`  Punishments: Rust=${rustPunishmentsMatchCount}/${results.length}, Emcc=${emccPunishmentsMatchCount}/${results.length}`);

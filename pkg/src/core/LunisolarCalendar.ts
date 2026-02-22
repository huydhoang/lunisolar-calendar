import type { TLunisolarDate } from '../types';
import { getDataLoader } from '../data/DataLoader';
import { TimezoneHandler } from '../timezone/TimezoneHandler';

// Heavenly stems and Earthly branches per rules (chars only for public API)
const HEAVENLY_STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'] as const;
const EARTHLY_BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'] as const;

type PrincipalTerm = {
  instantUtc: Date; // timezone-naive-like Date in JS (always UTC instant)
  cstDate: { y: number; m: number; d: number }; // CST date-only
  termIndex: number; // 1..12 for Z1..Z12
};

type MonthPeriod = {
  index: number;
  startUtc: Date;
  endUtc: Date;
  startCst: { y: number; m: number; d: number };
  endCst: { y: number; m: number; d: number };
  hasPrincipal: boolean;
  isLeap: boolean;
  monthNumber: number; // 1..12 (Zi-month=11)
};

function dateOnlyCompare(a: { y: number; m: number; d: number }, b: { y: number; m: number; d: number }) {
  if (a.y !== b.y) return a.y - b.y;
  if (a.m !== b.m) return a.m - b.m;
  return a.d - b.d;
}

function cstDateOf(dtUtc: Date, cst: TimezoneHandler): { y: number; m: number; d: number } {
  const p = new TimezoneHandler('Asia/Shanghai').utcToTimezoneDate(dtUtc);
  return { y: p.year, m: p.month, d: p.day };
}

function withinCstRange(
  target: { y: number; m: number; d: number },
  start: { y: number; m: number; d: number },
  end: { y: number; m: number; d: number }
): boolean {
  return dateOnlyCompare(start, target) <= 0 && dateOnlyCompare(target, end) < 0;
}

function cycleFromStemBranch(stemIdx1: number, branchIdx1: number): number {
  // indices are 1-based
  const stem0 = stemIdx1 - 1;
  const branch0 = branchIdx1 - 1;
  for (let cycle = 1; cycle <= 60; cycle++) {
    const s = (cycle - 1) % 10;
    const b = (cycle - 1) % 12;
    if (s === stem0 && b === branch0) return cycle;
  }
  return 1;
}

function yearGanzhi(lunarYear: number): [string, string, number] {
  let yearCycle = ((lunarYear - 4) % 60) + 1;
  if (yearCycle <= 0) yearCycle += 60;
  const stem = HEAVENLY_STEMS[(yearCycle - 1) % 10];
  const branch = EARTHLY_BRANCHES[(yearCycle - 1) % 12];
  return [stem, branch, yearCycle];
}

function monthGanzhi(lunarYear: number, lunarMonth: number): [string, string, number] {
  const [yearStem] = yearGanzhi(lunarYear);
  const yearStemIdx = HEAVENLY_STEMS.indexOf(yearStem as unknown as typeof HEAVENLY_STEMS[number]) + 1; // 1..10
  const mapping: Record<number, number> = { 1: 3, 6: 3, 2: 5, 7: 5, 3: 7, 8: 7, 4: 9, 9: 9, 5: 1, 10: 1 };
  const firstMonthStemIdx = mapping[yearStemIdx];
  const monthStemIdx = ((firstMonthStemIdx - 1 + (lunarMonth - 1)) % 10) + 1;
  let monthBranchIdx = (lunarMonth + 2) % 12; // 1..12
  if (monthBranchIdx === 0) monthBranchIdx = 12;
  const stemChar = HEAVENLY_STEMS[monthStemIdx - 1];
  const branchChar = EARTHLY_BRANCHES[monthBranchIdx - 1];
  const monthCycle = cycleFromStemBranch(monthStemIdx, monthBranchIdx);
  return [stemChar, branchChar, monthCycle];
}

function dayGanzhi(targetUtc: Date): [string, string, number] {
  // Anchor: 4 AD-01-31 is Jiazi day (UTC)
  const ref = new Date(Date.UTC(4, 0, 31, 0, 0, 0));
  // Use the UTC date of the original moment (matching Python's ganzhi_day which
  // converts local → UTC and uses target_utc.date() for day counting).
  const days = Math.floor((Date.UTC(targetUtc.getUTCFullYear(), targetUtc.getUTCMonth(), targetUtc.getUTCDate()) - ref.getTime()) / 86400000);
  const dayCycle = ((days % 60) + 60) % 60 + 1;
  const stem = HEAVENLY_STEMS[(dayCycle - 1) % 10];
  const branch = EARTHLY_BRANCHES[(dayCycle - 1) % 12];
  return [stem, branch, dayCycle];
}

function hourGanzhi(localDate: Date, baseDayStem: string): [string, string, number] {
  const hour = localDate.getUTCHours();
  const minute = localDate.getUTCMinutes();
  // Hour branch index
  const decimal = hour + minute / 60;
  let branchIndex0: number;
  if (decimal >= 23 || decimal < 1) branchIndex0 = 0; // Zi
  else {
    branchIndex0 = Math.floor((decimal - 1) / 2) + 1;
    if (branchIndex0 >= 12) branchIndex0 = 11;
  }
  const branchIdx1 = branchIndex0 + 1;
  let dayStemForHour = baseDayStem;
  if (hour >= 23) {
    // advance to next day
    // Compute next day's day stem via simple progression
    const dayStemIdx = HEAVENLY_STEMS.indexOf(baseDayStem as unknown as typeof HEAVENLY_STEMS[number]);
    dayStemForHour = HEAVENLY_STEMS[(dayStemIdx + 1) % 10];
  }
  const wuShuDun: Record<string, number> = { '甲': 0, '己': 0, '乙': 2, '庚': 2, '丙': 4, '辛': 4, '丁': 6, '壬': 6, '戊': 8, '癸': 8 };
  const ziStemIndex0 = wuShuDun[dayStemForHour] ?? 0;
  const hourStemIndex0 = (ziStemIndex0 + (branchIdx1 - 1)) % 10;
  const stemChar = HEAVENLY_STEMS[hourStemIndex0];
  const branchChar = EARTHLY_BRANCHES[branchIdx1 - 1];
  const cycle = cycleFromStemBranch(hourStemIndex0 + 1, branchIdx1);
  return [stemChar, branchChar, cycle];
}

export class LunisolarCalendar {
  readonly lunarYear!: number;
  readonly lunarMonth!: number;
  readonly lunarDay!: number;
  readonly isLeapMonth!: boolean;

  readonly yearStem!: string;
  readonly yearBranch!: string;
  readonly monthStem!: string;
  readonly monthBranch!: string;
  readonly dayStem!: string;
  readonly dayBranch!: string;
  readonly hourStem!: string;
  readonly hourBranch!: string;

  // True if the provided timezone's local date falls on a principal solar term day
  readonly isPrincipalSolarTermDay!: boolean;

  private _solarDate!: Date;

  private constructor(init: TLunisolarDate, solarDate: Date, isPrincipalSolarTermDay: boolean) {
    Object.assign(this, init);
    this._solarDate = new Date(solarDate.getTime());
    (this as any).isPrincipalSolarTermDay = isPrincipalSolarTermDay;
  }

  getSolarDate(): Date {
    return new Date(this._solarDate.getTime());
  }

  static async fromSolarDate(date: Date, timezone: string): Promise<LunisolarCalendar> {
    const userTz = new TimezoneHandler(timezone);
    const localParts = userTz.utcToTimezoneDate(date);
    const cst = new TimezoneHandler('Asia/Shanghai');

    const loader = getDataLoader();
    const yrs = new Set([localParts.year - 1, localParts.year, localParts.year + 1]);

    // Gather new moons and solar terms across surrounding years
    const [nmYearMap, stYearMap] = await Promise.all([
      (async () => {
        const m = new Map<number, number[]>();
        for (const y of yrs) m.set(y, await loader.getNewMoons(y));
        return m;
      })(),
      (async () => {
        const m = new Map<number, [number, number][]>();
        for (const y of yrs) m.set(y, (await loader.getSolarTerms(y)).map((v: any) => v as [number, number]));
        return m;
      })(),
    ]);

    const newMoons = Array.from(nmYearMap.values())
      .flat()
      .map((ts) => new Date(ts * 1000))
      .sort((a, b) => a.getTime() - b.getTime());

    const principalTerms: PrincipalTerm[] = Array.from(stYearMap.entries())
      .flatMap(([_, arr]) => arr)
      .filter(([, idx]) => (idx % 2) === 0)
      .map(([ts, idx]) => {
        // Principal terms: idx 0=Z2, 2=Z3, ..., 18=Z11, 20=Z12, 22=Z1
        // Formula: (idx / 2) + 2, with wrapping at 12
        const termIndexRaw = (idx / 2) + 2;
        const termIndex = termIndexRaw > 12 ? termIndexRaw - 12 : termIndexRaw;
        const dt = new Date(ts * 1000);
        const d = cst.utcToTimezoneDate(dt);
        return { instantUtc: dt, cstDate: { y: d.year, m: d.month, d: d.day }, termIndex } as PrincipalTerm;
      })
      .sort((a, b) => a.instantUtc.getTime() - b.instantUtc.getTime());

    // Determine principal solar term day (节气 Jieqi) in provided timezone
    // Per docs/12_construction_stars.md: 节气 (sectional terms) are at ODD indices
    // These trigger the Construction Stars repeat rule
    let isPrincipalSolarTermDay = false;
    for (const [y, arr] of stYearMap) {
      for (const [ts, idx] of arr as [number, number][]) {
        // Check ODD indices for sectional terms (节气 Jieqi)
        if ((idx % 2) === 0) continue;
        const dt = new Date(ts * 1000);
        const lp = userTz.utcToTimezoneDate(dt);
        if (lp.year === localParts.year && lp.month === localParts.month && lp.day === localParts.day) {
          isPrincipalSolarTermDay = true;
          break;
        }
      }
      if (isPrincipalSolarTermDay) break;
    }

    if (newMoons.length < 2) throw new Error('Insufficient new moon data');

    // Build month periods between successive new moons
    const periods: MonthPeriod[] = [];
    for (let i = 0; i < newMoons.length - 1; i++) {
      const startUtc = newMoons[i];
      const endUtc = newMoons[i + 1];
      const s = cst.utcToTimezoneDate(startUtc);
      const e = cst.utcToTimezoneDate(endUtc);
      periods.push({
        index: i,
        startUtc,
        endUtc,
        startCst: { y: s.year, m: s.month, d: s.day },
        endCst: { y: e.year, m: e.month, d: e.day },
        hasPrincipal: false,
        isLeap: false,
        monthNumber: 0,
      });
    }

    // Tag principal terms into periods by CST date-only belonging
    for (const term of principalTerms) {
      for (const period of periods) {
        if (withinCstRange(term.cstDate, period.startCst, period.endCst)) {
          period.hasPrincipal = true;
          break;
        }
      }
    }

    // Determine Winter Solstice (Z11) terms around target year
    const z11 = principalTerms.filter((t) => t.termIndex === 11);
    if (z11.length === 0) throw new Error('No Winter Solstice (Z11) term found in loaded data');

    const targetYear = new Date(Date.UTC(localParts.year, 0, 1)).getUTCFullYear();
    const currentYearZ11 = z11.find((t) => t.instantUtc.getUTCFullYear() === targetYear)
      || z11.reduce((prev, curr) => (Math.abs(curr.instantUtc.getUTCFullYear() - targetYear) < Math.abs(prev.instantUtc.getUTCFullYear() - targetYear) ? curr : prev));

    const targetUtc = date; // input Date is an absolute instant
    const anchorSolstice = (targetUtc.getTime() >= currentYearZ11.instantUtc.getTime())
      ? currentYearZ11.instantUtc
      : (z11.find((t) => t.instantUtc.getUTCFullYear() === targetYear - 1)?.instantUtc || currentYearZ11.instantUtc);

    // Assign month numbers starting from Zi month (month 11)
    // Strategy: Find Zi month (contains Winter Solstice) and iterate forward only
    const ziIndex = periods.findIndex((p) => p.startUtc <= anchorSolstice && anchorSolstice < p.endUtc);
    if (ziIndex === -1) throw new Error('Failed to locate Zi-month containing Winter Solstice');

    // console.log('DEBUG: Zi month found at index:', ziIndex);
    // console.log('DEBUG: Zi month period:', periods[ziIndex].startCst, 'to', periods[ziIndex].endCst);
    // console.log('DEBUG: Anchor solstice:', anchorSolstice.toISOString());
    
    periods[ziIndex].monthNumber = 11;
    periods[ziIndex].isLeap = false;

    // Forward pass: iterate from Zi month through all subsequent periods
    let current = 11;
    for (let i = ziIndex + 1; i < periods.length; i++) {
      if (periods[i].hasPrincipal) {
        // Regular month with principal term: increment month number
        current = (current % 12) + 1;
        periods[i].monthNumber = current;
        periods[i].isLeap = false;
      } else {
        // Leap month (no principal term): takes the preceding month's number
        periods[i].monthNumber = current;
        periods[i].isLeap = true;
      }
    }

    // Handle any periods before Zi month (should be rare/none with proper windowing)
    if (ziIndex > 0) {
      // These periods come before the Winter Solstice anchor, so we need to number them backward
      current = 11;
      for (let i = ziIndex - 1; i >= 0; i--) {
        // Decrement to get the preceding month number
        current = current > 1 ? current - 1 : 12;
        if (periods[i].hasPrincipal) {
          periods[i].monthNumber = current;
          periods[i].isLeap = false;
        } else {
          // Leap month before Zi month: should take the preceding month's number
          // The preceding month is 'current', so the leap month should also be 'current'
          periods[i].monthNumber = current;
          periods[i].isLeap = true;
        }
      }
    }

    // Debug logging (disabled)
    // console.log('DEBUG: Month periods summary:');
    // for (const p of periods) {
    //   console.log(`  Period ${p.index}: Month ${p.monthNumber}${p.isLeap ? ' LEAP' : ''} | ${p.startCst.y}-${p.startCst.m}-${p.startCst.d} to ${p.endCst.y}-${p.endCst.m}-${p.endCst.d} | Principal: ${p.hasPrincipal}`);
    // }

    // Find the period that contains target date by CST date-only comparison
    const targetCst = cst.utcToTimezoneDate(targetUtc);
    const targetCstDate = { y: targetCst.year, m: targetCst.month, d: targetCst.day };
    const targetPeriod = periods.find((p) => withinCstRange(targetCstDate, p.startCst, p.endCst));
    if (!targetPeriod) throw new Error('No lunar month period found for target date');

    // Lunar day (1..30) from CST date difference + 1
    const start = new Date(Date.UTC(targetPeriod.startCst.y, targetPeriod.startCst.m - 1, targetPeriod.startCst.d));
    const tgt = new Date(Date.UTC(targetCstDate.y, targetCstDate.m - 1, targetCstDate.d));
    const lunarDayRaw = Math.floor((tgt.getTime() - start.getTime()) / 86400000) + 1;
    const lunarDay = Math.max(1, Math.min(30, lunarDayRaw));

    // Lunar year determination mirroring Python logic
    let lunarYear: number;
    if (targetPeriod.monthNumber === 1) lunarYear = targetPeriod.startUtc.getUTCFullYear();
    else if (targetPeriod.monthNumber >= 2 && targetPeriod.monthNumber <= 10) lunarYear = targetPeriod.startUtc.getUTCFullYear();
    else lunarYear = targetPeriod.startUtc.getUTCFullYear() + 1;

    // Sexagenary cycles using local wall time in provided timezone
    // Construct a Date whose UTC components match local wall time in timezone
    const localWall = userTz.convertToTimezone(targetUtc); // UTC fields reflect local wall time
    const [yStem, yBranch, yCycle] = yearGanzhi(lunarYear);
    const [mStem, mBranch, mCycle] = monthGanzhi(lunarYear, targetPeriod.monthNumber);
    const [dStem, dBranch, dCycle] = dayGanzhi(targetUtc);
    const [hStem, hBranch, hCycle] = hourGanzhi(localWall, dStem);

    const result: TLunisolarDate = {
      lunarYear,
      lunarMonth: targetPeriod.monthNumber,
      lunarDay,
      isLeapMonth: targetPeriod.isLeap,
      yearStem: yStem,
      yearBranch: yBranch,
      monthStem: mStem,
      monthBranch: mBranch,
      dayStem: dStem,
      dayBranch: dBranch,
      hourStem: hStem,
      hourBranch: hBranch,
    };

    return new LunisolarCalendar(result, targetUtc, isPrincipalSolarTermDay);
  }
}

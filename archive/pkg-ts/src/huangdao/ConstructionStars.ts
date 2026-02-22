import type { TConstructionStar, TDayInfo, TConstructionStarName } from '../types';
import { STAR_SEQUENCE } from '../types';
import { LunisolarCalendar } from '../core/LunisolarCalendar';

// Reverse mapping (index -> branch char)
const BRANCH_ORDER = [
  '子',
  '丑',
  '寅',
  '卯',
  '辰',
  '巳',
  '午',
  '未',
  '申',
  '酉',
  '戌',
  '亥',
] as const;

// Month 1..12 -> Building Branch (月建) mapping
// 1: 寅, 2: 卯, 3: 辰, 4: 巳, 5: 午, 6: 未, 7: 申, 8: 酉, 9: 戌, 10: 亥, 11: 子, 12: 丑
const MONTH_BUILDING_BRANCH: Record<number, string> = {
  1: '寅',
  2: '卯',
  3: '辰',
  4: '巳',
  5: '午',
  6: '未',
  7: '申',
  8: '酉',
  9: '戌',
  10: '亥',
  11: '子',
  12: '丑',
};

// Scoring and auspiciousness per traditional formula
// 建满平收黑，除危定执黄，成开皆可用，破闭不可当
// Updated scoring: 4 (auspicious), 3 (moderate), 2 (inauspicious), 1 (very inauspicious)
const STAR_SCORES: Record<string, { auspicious: boolean; score: number; description: string }> = {
  建: { auspicious: false, score: 2, description: 'Establish; take small steps, evaluate risks' },
  除: { auspicious: true, score: 4, description: 'Remove; get rid of redundancies and continue' },
  满: { auspicious: true, score: 3, description: 'Full; new highs achieved, avoid new starts' },
  平: { auspicious: false, score: 2, description: 'Balanced; yin and yang are equal, rest' },
  定: { auspicious: true, score: 4, description: 'Set; stable foundation, highly auspicious' },
  执: { auspicious: true, score: 3, description: 'Hold; good for maintenance works' },
  破: { auspicious: false, score: 1, description: 'Break; stop all works, watch out for issues' },
  危: { auspicious: false, score: 2, description: 'Danger; risky stage, loss might be recovered' },
  成: { auspicious: true, score: 3, description: 'Accomplish; 3/4 cycle, finish remaining tasks' },
  收: { auspicious: false, score: 2, description: 'Harvest; finalize works, avoid new ventures' },
  开: { auspicious: true, score: 3, description: 'Open; time to look for new opportunities' },
  闭: { auspicious: false, score: 1, description: 'Close; stop all works, rest and observe' },
};

// Earthly branch index helper (子=0 .. 亥=11)
const BRANCH_INDEX: Record<string, number> = {
  子: 0,
  丑: 1,
  寅: 2,
  卯: 3,
  辰: 4,
  巳: 5,
  午: 6,
  未: 7,
  申: 8,
  酉: 9,
  戌: 10,
  亥: 11,
};

/**
 * Twelve Construction Stars (十二建星) calculator.
 *
 * Usage: construct with an existing LunisolarCalendar instance, then call getStar().
 * For the solar-term-day repetition rule, use getStarWithSolarTermRule(date, timezone).
 */
export class ConstructionStars {
  private calendar: LunisolarCalendar;

  private constructor(calendar: LunisolarCalendar) {
    this.calendar = calendar;
  }

  /**
   * (internal) Calculates the Construction Star for a single day in a sequence.
   * This method relies on the previous day's star to maintain the correct sequence
   * across solar term boundaries.
   *
   * @param {TConstructionStarName} [prevStarName] - The name of the star from the previous day.
   * @returns {TConstructionStar} The calculated star information.
   * @private
   */
  private getStar(prevStarName?: TConstructionStarName): TConstructionStar {
    const lunarMonth = this.calendar.lunarMonth;
    const dayBranch = this.calendar.dayBranch;
    const buildingBranch = MONTH_BUILDING_BRANCH[lunarMonth];
    const isSolarTermToday = (this.calendar as any).isPrincipalSolarTermDay;

    // The base calculation is the fallback for the first day of a sequence.
    const dIdx = BRANCH_INDEX[dayBranch];
    const mIdx = BRANCH_INDEX[buildingBranch];
    const baseStarIdx = (((dIdx - mIdx) % 12) + 12) % 12;
    const baseStar = STAR_SEQUENCE[baseStarIdx];

    let actualStar: TConstructionStarName;

    if (!prevStarName) {
      // No previous star, so this is the start of a sequence. Use the base calculation.
      actualStar = baseStar;
    } else if (isSolarTermToday) {
      // Solar term day: repeat the previous day's star.
      actualStar = prevStarName;
    } else {
      // Normal day: increment from the previous day's star.
      const prevStarIndex = STAR_SEQUENCE.indexOf(prevStarName);
      const actualStarIndex = (prevStarIndex + 1) % 12;
      actualStar = STAR_SEQUENCE[actualStarIndex];
    }

    const meta = STAR_SCORES[actualStar];
    return {
      name: actualStar,
      auspicious: meta.auspicious,
      score: meta.score,
      description: meta.description,
    };
  }

  /**
   * Calculates the Construction Stars for an entire solar month, correctly handling
   * the sequential logic across solar term boundaries.
   *
   * @param {number} year - The Gregorian year.
   * @param {number} month - The Gregorian month (1-12).
   * @param {string} [timezone='Asia/Shanghai'] - The IANA timezone name.
   * @returns {Promise<TDayInfo[]>} A promise that resolves to an array of day information.
   */
  static async calculateMonth(
    year: number,
    month: number,
    timezone: string = 'Asia/Shanghai',
  ): Promise<TDayInfo[]> {
    const results: TDayInfo[] = [];
    const daysInMonth = new Date(Date.UTC(year, month, 0)).getUTCDate();

    let prevStarName: TConstructionStarName | undefined = undefined;

    // To correctly calculate the first day of the month, we need the star from the last day of the previous month.
    const firstDayOfMonth = new Date(Date.UTC(year, month - 1, 1, 4, 0, 0));
    const dayBefore = new Date(firstDayOfMonth.getTime() - 24 * 60 * 60 * 1000);

    try {
      const prevCal = await LunisolarCalendar.fromSolarDate(dayBefore, timezone);
      // To get the star for the day before, we calculate its base star (no prevStar).
      const prevCs = new ConstructionStars(prevCal);
      const prevStar = prevCs.getStar(); // This will use the base calculation.
      prevStarName = prevStar.name;
    } catch (e) {
      // This can happen if data is not available for the previous month.
      // In this case, the first day of the month will use its base calculation, which is an acceptable fallback.
      console.warn(
        `Could not determine star for the day before ${year}-${month}. Starting sequence from base calculation.`,
      );
    }

    for (let day = 1; day <= daysInMonth; day++) {
      // Use a consistent time (e.g., noon in the target timezone) to avoid DST issues.
      // 4:00 UTC is used as a proxy for noon in East Asia.
      const dt = new Date(Date.UTC(year, month - 1, day, 4, 0, 0));
      let cal: LunisolarCalendar;
      try {
        cal = await LunisolarCalendar.fromSolarDate(dt, timezone);
      } catch {
        // If a day fails, skip it and continue.
        continue;
      }

      // Create ConstructionStars and calculate the star sequentially.
      const cs = new ConstructionStars(cal);
      const star = cs.getStar(prevStarName);

      // Update the previous star name for the next iteration.
      prevStarName = star.name;

      results.push({ date: cal.getSolarDate(), star });
    }

    return results;
  }

  /**
   * Lists auspicious days in a solar month that meet a minimum score.
   * This is a convenience method that uses `calculateMonth`.
   *
   * @param {number} year - The Gregorian year.
   * @param {number} month - The Gregorian month (1-12).
   * @param {number} minScore - The minimum score for a day to be considered auspicious.
   * @param {string} [timezone='Asia/Shanghai'] - The IANA timezone name.
   * @returns {Promise<TDayInfo[]>} A promise that resolves to an array of auspicious day information.
   */
  static async getAuspiciousDays(
    year: number,
    month: number,
    minScore: number,
    timezone: string = 'Asia/Shanghai',
  ): Promise<TDayInfo[]> {
    const monthData = await this.calculateMonth(year, month, timezone);
    return monthData.filter(({ star }) => star.score >= minScore);
  }
}

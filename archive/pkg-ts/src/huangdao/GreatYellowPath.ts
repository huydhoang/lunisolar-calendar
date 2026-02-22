import type { TGreatYellowPathSpirit } from '../types';
import { LunisolarCalendar } from '../core/LunisolarCalendar';

// Azure Dragon monthly starting branch mapping (1..12 lunar months)
const AZURE_START: Record<number, string> = {
  1: '子', 2: '寅', 3: '辰', 4: '午', 5: '申', 6: '戌',
  7: '子', 8: '寅', 9: '辰', 10: '午', 11: '申', 12: '戌',
};

// Spirit sequence starting from Azure Dragon
const SPIRITS: { name: string; type: 'Yellow Path' | 'Black Path'; description: string }[] = [
  { name: '青龙', type: 'Yellow Path', description: 'Auspicious for all activities' },
  { name: '明堂', type: 'Yellow Path', description: 'Favorable for ceremonies and official business' },
  { name: '天刑', type: 'Black Path', description: 'Avoid legal matters and conflicts' },
  { name: '朱雀', type: 'Black Path', description: 'Unfavorable for communication; beware disputes' },
  { name: '金匮', type: 'Yellow Path', description: 'Excellent for wealth and weddings' },
  { name: '天德', type: 'Yellow Path', description: 'Excellent for travel and virtuous activities' },
  { name: '白虎', type: 'Black Path', description: 'Dangerous; avoid major undertakings' },
  { name: '玉堂', type: 'Yellow Path', description: 'Noble activities, documents, celebrations' },
  { name: '天牢', type: 'Black Path', description: 'Restrictive; unfavorable for most matters' },
  { name: '玄武', type: 'Black Path', description: 'Hidden dangers; avoid legal matters and gambling' },
  { name: '司命', type: 'Yellow Path', description: 'Good for health and life matters (daytime)' },
  { name: '勾陈', type: 'Black Path', description: 'Entanglements; avoid construction and burials' },
];

const BRANCH_INDEX: Record<string, number> = {
  '子': 0, '丑': 1, '寅': 2, '卯': 3, '辰': 4, '巳': 5, '午': 6, '未': 7, '申': 8, '酉': 9, '戌': 10, '亥': 11,
};

/**
 * Great Yellow Path (大黄道) calculator.
 *
 * Usage: construct with an existing LunisolarCalendar instance, then call getSpirit().
 */
export class GreatYellowPath {
  private calendar: LunisolarCalendar;

  constructor(calendar: LunisolarCalendar) {
    this.calendar = calendar;
  }

  getSpirit(): TGreatYellowPathSpirit {
    const lunarMonth = this.calendar.lunarMonth;
    const dayBranch = this.calendar.dayBranch; // e.g., '子'

    const startBranch = AZURE_START[lunarMonth];
    const offset = ((BRANCH_INDEX[dayBranch] - BRANCH_INDEX[startBranch]) % 12 + 12) % 12;
    const s = SPIRITS[offset];

    return { name: s.name, type: s.type, description: s.description };
  }
}

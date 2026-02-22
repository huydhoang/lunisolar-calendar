import { describe, it, expect } from 'vitest';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';

// Helper to run Python oracle for a given date/time in Asia/Shanghai and parse output
function runPythonOracle(dateStr: string, timeStr: string) {
  const root = resolve(__dirname, '..', '..'); // repo root from pkg/tests
  const script = resolve(root, 'data', 'lunisolar_v2.py');
  const res = spawnSync('python', [script, '--date', dateStr, '--time', timeStr, '--tz', 'Asia/Shanghai'], {
    encoding: 'utf-8',
  });
  if (res.status !== 0) {
    return { error: res.stderr || res.stdout || `Python exited with ${res.status}` };
  }
  const out = res.stdout.trim().split(/\r?\n/);
  // Expected lines include:
  // Solar: YYYY-MM-DD HH:MM
  // Lunisolar: Y-M-D H:00
  // Leap month: True/False
  // Year: <stem><branch> (...) [cycle]
  // Month: ...
  // Day: ...
  // Hour: ...
  const get = (prefix: string) => out.find((l) => l.startsWith(prefix)) || '';
  const lun = get('Lunisolar: ');
  const leap = get('Leap month: ');
  const yearL = get('Year: ');
  const monthL = get('Month: ');
  const dayL = get('Day: ');
  const hourL = get('Hour: ');

  const lunMatch = lun.match(/Lunisolar: (\d+)-(\d+)-(\d+) (\d+):/);
  const ymbh = lunMatch ? { year: Number(lunMatch[1]), month: Number(lunMatch[2]), day: Number(lunMatch[3]), hour: Number(lunMatch[4]) } : null;
  const isLeap = leap.includes('True');
  const rgx = /: (..) .* \[(\d+)\]/; // Two Chinese chars and cycle number in brackets
  const ym = yearL.match(rgx);
  const mm = monthL.match(rgx);
  const dm = dayL.match(rgx);
  const hm = hourL.match(rgx);

  return {
    ...(ymbh || {}),
    isLeapMonth: isLeap,
    yearStemBranch: ym ? ym[1] : '',
    monthStemBranch: mm ? mm[1] : '',
    dayStemBranch: dm ? dm[1] : '',
    hourStemBranch: hm ? hm[1] : '',
    raw: out.join('\n'),
  };
}

// Helper: construct a UTC Date corresponding to Asia/Shanghai local wall time (UTC+8 fixed)
function dateFromCSTLocal(yyyy: number, mm: number, dd: number, hh = 12, min = 0) {
  const utcH = hh - 8; // CST is UTC+8
  return new Date(Date.UTC(yyyy, mm - 1, dd, utcH, min));
}

// Helper: construct a UTC Date corresponding to Asia/Ho_Chi_Minh local wall time (UTC+7 fixed)
function dateFromICTLocal(yyyy: number, mm: number, dd: number, hh = 12, min = 0) {
  const utcH = hh - 7; // ICT is UTC+7
  return new Date(Date.UTC(yyyy, mm - 1, dd, utcH, min));
}

describe('LunisolarCalendar parity with Python oracle (Asia/Shanghai)', () => {
  it('matches for a mid-year date', async () => {
    const dateStr = '2025-06-21';
    const timeStr = '12:00';
    const py = runPythonOracle(dateStr, timeStr);
    if ((py as any).error) return; // Skip if Python env not available

    const { LunisolarCalendar } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    const jsDate = dateFromCSTLocal(2025, 6, 21, 12, 0);
    const res = await LunisolarCalendar.fromSolarDate(jsDate, 'Asia/Shanghai');

    expect(res.lunarMonth).toBe((py as any).month);
    expect(res.lunarDay).toBe((py as any).day);
    expect(res.isLeapMonth).toBe((py as any).isLeapMonth);
    expect(res.yearStem + res.yearBranch).toBe((py as any).yearStemBranch);
    expect(res.monthStem + res.monthBranch).toBe((py as any).monthStemBranch);
    expect(res.dayStem + res.dayBranch).toBe((py as any).dayStemBranch);
    expect(res.hourStem + res.hourBranch).toBe((py as any).hourStemBranch);
  });

  it('matches around Lunar New Year', async () => {
    const dateStr = '2025-02-10';
    const timeStr = '12:00';
    const py = runPythonOracle(dateStr, timeStr);
    if ((py as any).error) return;

    const { LunisolarCalendar } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    const jsDate = dateFromCSTLocal(2025, 2, 10, 12, 0);
    const res = await LunisolarCalendar.fromSolarDate(jsDate, 'Asia/Shanghai');

    expect(res.lunarMonth).toBe((py as any).month);
    expect(res.lunarDay).toBe((py as any).day);
    expect(res.isLeapMonth).toBe((py as any).isLeapMonth);
    expect(res.yearStem + res.yearBranch).toBe((py as any).yearStemBranch);
    expect(res.monthStem + res.monthBranch).toBe((py as any).monthStemBranch);
  });

  it('applies 23:00 hour boundary rule', async () => {
    const dateStr = '2025-03-01';
    const timeStr = '23:30';
    const py = runPythonOracle(dateStr, timeStr);
    if ((py as any).error) return;

    const { LunisolarCalendar } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    const jsDate = dateFromCSTLocal(2025, 3, 1, 23, 30);
    const res = await LunisolarCalendar.fromSolarDate(jsDate, 'Asia/Shanghai');

    expect(res.dayStem + res.dayBranch).toBe((py as any).dayStemBranch);
    expect(res.hourStem + res.hourBranch).toBe((py as any).hourStemBranch);
  });
});

describe('Regression: conversion mismatch fix (Asia/Ho_Chi_Minh UTC+7)', () => {
  it('matches Python for 2025-10-08 11:00 ICT', async () => {
    const dateStr = '2025-10-08';
    const timeStr = '11:00';
    const root = resolve(__dirname, '..', '..');
    const script = resolve(root, 'data', 'lunisolar_v2.py');
    const pyRes = spawnSync('python', [script, '--date', dateStr, '--time', timeStr, '--tz', 'Asia/Ho_Chi_Minh'], {
      encoding: 'utf-8',
    });
    if (pyRes.status !== 0) return; // Skip if Python not available

    const out = pyRes.stdout.trim().split(/\r?\n/);
    const get = (prefix: string) => out.find((l) => l.startsWith(prefix)) || '';
    const lun = get('Lunisolar: ');
    const leap = get('Leap month: ');
    const yearL = get('Year: ');
    const monthL = get('Month: ');
    const dayL = get('Day: ');
    const hourL = get('Hour: ');

    const lunMatch = lun.match(/Lunisolar: (\d+)-(\d+)-(\d+) (\d+):/);
    const ymbh = lunMatch ? { year: Number(lunMatch[1]), month: Number(lunMatch[2]), day: Number(lunMatch[3]), hour: Number(lunMatch[4]) } : null;
    const isLeap = leap.includes('True');
    const rgx = /: (..) .* \[(\d+)\]/;
    const ym = yearL.match(rgx);
    const mm = monthL.match(rgx);
    const dm = dayL.match(rgx);
    const hm = hourL.match(rgx);

    const { LunisolarCalendar } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    const jsDate = dateFromICTLocal(2025, 10, 8, 11, 0);
    const res = await LunisolarCalendar.fromSolarDate(jsDate, 'Asia/Ho_Chi_Minh');

    expect(res.lunarMonth).toBe((ymbh as any).month);
    expect(res.lunarDay).toBe((ymbh as any).day);
    expect(res.isLeapMonth).toBe(isLeap);
    expect(res.yearStem + res.yearBranch).toBe(ym ? ym[1] : '');
    expect(res.monthStem + res.monthBranch).toBe(mm ? mm[1] : '');
    expect(res.dayStem + res.dayBranch).toBe(dm ? dm[1] : '');
    expect(res.hourStem + res.hourBranch).toBe(hm ? hm[1] : '');
  });
});

describe('Day ganzhi uses local date (not UTC) for timezone-correct day boundary', () => {
  it('gives consistent day ganzhi across all hours of the same local date in UTC+7', async () => {
    const { LunisolarCalendar } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));

    // Feb 22, 2025 at 03:00 UTC+7 (early morning — UTC date is Feb 21)
    const early = dateFromICTLocal(2025, 2, 22, 3, 0);
    const resEarly = await LunisolarCalendar.fromSolarDate(early, 'Asia/Ho_Chi_Minh');

    // Feb 22, 2025 at 12:00 UTC+7 (noon — UTC date is Feb 22)
    const noon = dateFromICTLocal(2025, 2, 22, 12, 0);
    const resNoon = await LunisolarCalendar.fromSolarDate(noon, 'Asia/Ho_Chi_Minh');

    // Both should produce the same day ganzhi for Feb 22 local
    expect(resEarly.dayStem).toBe(resNoon.dayStem);
    expect(resEarly.dayBranch).toBe(resNoon.dayBranch);
  });

  it('matches Python for early morning UTC+7 (03:00)', async () => {
    const dateStr = '2025-02-22';
    const timeStr = '03:00';
    const root = resolve(__dirname, '..', '..');
    const script = resolve(root, 'data', 'lunisolar_v2.py');
    const pyRes = spawnSync('python', [script, '--date', dateStr, '--time', timeStr, '--tz', 'Asia/Ho_Chi_Minh'], {
      encoding: 'utf-8',
    });
    if (pyRes.status !== 0) return; // Skip if Python not available

    const out = pyRes.stdout.trim().split(/\r?\n/);
    const get = (prefix: string) => out.find((l) => l.startsWith(prefix)) || '';
    const dayL = get('Day: ');
    const hourL = get('Hour: ');
    const rgx = /: (..) .* \[(\d+)\]/;
    const dm = dayL.match(rgx);
    const hm = hourL.match(rgx);

    const { LunisolarCalendar } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    const jsDate = dateFromICTLocal(2025, 2, 22, 3, 0);
    const res = await LunisolarCalendar.fromSolarDate(jsDate, 'Asia/Ho_Chi_Minh');

    expect(res.dayStem + res.dayBranch).toBe(dm ? dm[1] : '');
    expect(res.hourStem + res.hourBranch).toBe(hm ? hm[1] : '');
  });
});

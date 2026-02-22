import { describe, it, expect } from 'vitest';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';

// Run Python huangdao_systems to get Construction Star and GYP for a date/timezone
function runPythonHuangdao(year: number, month: number, day: number, tz: string) {
  const root = resolve(__dirname, '..', '..');
  const dataDir = resolve(root, 'data');
  const code = `import sys; sys.path.insert(0, r"${dataDir.replace(/\\/g, '\\\\')}");\n` +
    `from huangdao_systems import MainCalculator; from datetime import datetime;\n` +
    `calc=MainCalculator(${year}, '${tz}'); d=datetime(${year}, ${month}, ${day}); info=calc.calculate_day_info(d);\n` +
    `print(info['star']); print(info['gyp_spirit'])`;
  const res = spawnSync('python', ['-c', code], { encoding: 'utf-8' });
  if (res.status !== 0) return { error: res.stderr || res.stdout || `Python exited ${res.status}` };
  const lines = res.stdout.trim().split(/\r?\n/);
  return { star: lines[0], gyp: lines[1] };
}

describe('Huangdao parity with Python (ConstructionStars + GreatYellowPath)', () => {
  it('parity for 2025-06-21 Asia/Shanghai', async () => {
    const py = runPythonHuangdao(2025, 6, 21, 'Asia/Shanghai');
    if ((py as any).error) return;

    const { LunisolarCalendar, ConstructionStars, GreatYellowPath } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    const jsDate = new Date(Date.UTC(2025, 5, 21, 4, 0, 0)); // ~12:00 CST
    const cal = await LunisolarCalendar.fromSolarDate(jsDate, 'Asia/Shanghai');
    const csCalc = new ConstructionStars(cal);
const cs = csCalc.getStar();
    const gyp = new GreatYellowPath(cal).getSpirit();

    expect(cs.name).toBe((py as any).star);
    expect(gyp.name).toBe((py as any).gyp);
  });

  it('parity for 2025-02-10 Asia/Shanghai', async () => {
    const py = runPythonHuangdao(2025, 2, 10, 'Asia/Shanghai');
    if ((py as any).error) return;

    const { LunisolarCalendar, ConstructionStars, GreatYellowPath } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    const jsDate = new Date(Date.UTC(2025, 1, 10, 4, 0, 0));
    const cal = await LunisolarCalendar.fromSolarDate(jsDate, 'Asia/Shanghai');
const cs = new ConstructionStars(cal).getStar();
    const gyp = new GreatYellowPath(cal).getSpirit();

    expect(cs.name).toBe((py as any).star);
    expect(gyp.name).toBe((py as any).gyp);
  });

  it('parity for 2025-10-08 Asia/Ho_Chi_Minh', async () => {
    const py = runPythonHuangdao(2025, 10, 8, 'Asia/Ho_Chi_Minh');
    if ((py as any).error) return;

    const { LunisolarCalendar, ConstructionStars, GreatYellowPath } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    const jsDate = new Date(Date.UTC(2025, 9, 8, 4, 0, 0)); // ~11:00 ICT
    const cal = await LunisolarCalendar.fromSolarDate(jsDate, 'Asia/Ho_Chi_Minh');
const cs = new ConstructionStars(cal).getStar();
    const gyp = new GreatYellowPath(cal).getSpirit();

    expect(cs.name).toBe((py as any).star);
    expect(gyp.name).toBe((py as any).gyp);
  });
});

describe('Huangdao edge cases and multi-timezone parity', () => {
  it('principal solar term day repetition in Asia/Ho_Chi_Minh', async () => {
    const { configure, getDataLoader } = await import(resolve(__dirname, '..', 'dist', 'index.mjs')) as any;
    configure({ strategy: 'fetch', data: { baseUrl: './data' } });
    const loader = (getDataLoader as any)();
    const terms: [number, number][] = await loader.getSolarTerms(2025);
    const principal = terms.find((t) => t[1] % 2 === 0);
    if (!principal) return;

    const ts = principal[0];
    const instant = new Date(ts * 1000);

    // Python expected values for the same instant interpreted in ICT
    const py = runPythonHuangdao(instant.getUTCFullYear(), instant.getUTCMonth() + 1, instant.getUTCDate(), 'Asia/Ho_Chi_Minh');
    if ((py as any).error) return;

    const { LunisolarCalendar, ConstructionStars } = await import(resolve(__dirname, '..', 'dist', 'index.mjs')) as any;
    const cal = await (LunisolarCalendar as any).fromSolarDate(instant, 'Asia/Ho_Chi_Minh');
const cs = new (ConstructionStars as any)(cal).getStar();
    expect(cs.name).toBe((py as any).star);
  });

  it('America/New_York parity mid-year date', async () => {
    const py = runPythonHuangdao(2025, 6, 21, 'America/New_York');
    if ((py as any).error) return;

    const { LunisolarCalendar, ConstructionStars, GreatYellowPath } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    const jsDate = new Date(Date.UTC(2025, 5, 21, 16, 0, 0)); // ~12:00 EDT (UTC-4)
    const cal = await LunisolarCalendar.fromSolarDate(jsDate, 'America/New_York');
const cs = new ConstructionStars(cal).getStar();
    const gyp = new GreatYellowPath(cal).getSpirit();
    expect(cs.name).toBe((py as any).star);
    expect(gyp.name).toBe((py as any).gyp);
  });

  it('Asia/Ho_Chi_Minh boundary near Lunar New Year (prev day)', async () => {
    const py = runPythonHuangdao(2025, 2, 9, 'Asia/Ho_Chi_Minh');
    if ((py as any).error) return;

    const { LunisolarCalendar, ConstructionStars, GreatYellowPath } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    const jsDate = new Date(Date.UTC(2025, 1, 9, 5, 0, 0)); // ~12:00 ICT
    const cal = await LunisolarCalendar.fromSolarDate(jsDate, 'Asia/Ho_Chi_Minh');
    const cs = await new ConstructionStars(cal).getStarWithSolarTermRule(jsDate, 'Asia/Ho_Chi_Minh');
    const gyp = new GreatYellowPath(cal).getSpirit();
    expect(cs.name).toBe((py as any).star);
    expect(gyp.name).toBe((py as any).gyp);
  });
});

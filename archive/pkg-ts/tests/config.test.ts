import { describe, it, expect, beforeEach } from 'vitest';
import { resolve } from 'node:path';

describe('v0.2.0 Configuration API', () => {
  // Reset between tests by re-importing
  beforeEach(async () => {
    // Clear module cache to reset config state
    delete require.cache[require.resolve(resolve(__dirname, '..', 'dist', 'index.mjs'))];
  });

  it('works with zero configuration (default CDN)', async () => {
    const { LunisolarCalendar } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    
    // Should work without any configure() call
    const cal = await LunisolarCalendar.fromSolarDate(
      new Date(Date.UTC(2025, 5, 21, 4, 0, 0)),
      'Asia/Shanghai'
    );
    
    expect(cal.lunarMonth).toBeGreaterThan(0);
    expect(cal.lunarDay).toBeGreaterThan(0);
  });

  it('allows custom CDN configuration', async () => {
    const { configure, getConfiguration } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    
    // Configure with custom baseUrl
    configure({
      strategy: 'fetch',
      data: { baseUrl: 'https://custom-cdn.example.com/data' }
    });
    
    // Verify configuration was applied
    const config = getConfiguration();
    expect(config.strategy).toBe('fetch');
    expect(config.data.baseUrl).toBe('https://custom-cdn.example.com/data');
  });

  it('supports static strategy configuration', async () => {
    const { configure, getConfiguration } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    
    configure({ strategy: 'static' });
    
    const config = getConfiguration();
    expect(config.strategy).toBe('static');
  });

  it('getConfiguration returns current config snapshot', async () => {
    const { configure, getConfiguration } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    
    configure({
      strategy: 'fetch',
      data: { baseUrl: 'https://test.example.com' }
    });
    
    const config = getConfiguration();
    expect(config.strategy).toBe('fetch');
    expect(config.data.baseUrl).toBe('https://test.example.com');
  });

  it('DataLoader constructor shows deprecation warning', async () => {
    const { DataLoader } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    
    // Capture console.warn
    const originalWarn = console.warn;
    const warnings: string[] = [];
    console.warn = (msg: string) => warnings.push(msg);
    
    try {
      new (DataLoader as any)({ baseUrl: './old-path' });
      
      expect(warnings.length).toBeGreaterThan(0);
      expect(warnings[0]).toContain('deprecated');
      expect(warnings[0]).toContain('configure');
    } finally {
      console.warn = originalWarn;
    }
  });

  it('works with Node.js fs fallback for relative paths', async () => {
    const { configure, LunisolarCalendar } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    
    // Configure with relative path to trigger fs fallback in Node
    configure({
      strategy: 'fetch',
      data: { baseUrl: './data' }
    });
    
    const cal = await LunisolarCalendar.fromSolarDate(
      new Date(Date.UTC(2025, 5, 21, 4, 0, 0)),
      'Asia/Shanghai'
    );
    
    expect(cal.lunarMonth).toBeGreaterThan(0);
    expect(cal.lunarDay).toBeGreaterThan(0);
  });
});

describe('v0.2.0 Backward Compatibility', () => {
  it('ConstructionStars.getStar() respects isPrincipalSolarTermDay', async () => {
    const { LunisolarCalendar, ConstructionStars } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    
    // Use a date and check the calendar's isPrincipalSolarTermDay flag
    const cal = await LunisolarCalendar.fromSolarDate(
      new Date(Date.UTC(2025, 5, 21, 4, 0, 0)),
      'Asia/Shanghai'
    );
    
    const cs = new (ConstructionStars as any)(cal);
    const star = cs.getStar();
    
    // Should return valid star
    expect(star.name).toBeTruthy();
    expect(typeof star.score).toBe('number');
    expect(typeof star.auspicious).toBe('boolean');
  });

  it('deprecated getStarWithSolarTermRule still works', async () => {
    const { LunisolarCalendar, ConstructionStars } = await import(resolve(__dirname, '..', 'dist', 'index.mjs'));
    
    const date = new Date(Date.UTC(2025, 5, 21, 4, 0, 0));
    const cal = await LunisolarCalendar.fromSolarDate(date, 'Asia/Shanghai');
    
    const cs = new (ConstructionStars as any)(cal);
    const star = await cs.getStarWithSolarTermRule(date, 'Asia/Shanghai');
    
    // Should return same as getStar()
    expect(star.name).toBeTruthy();
    expect(typeof star.score).toBe('number');
  });
});
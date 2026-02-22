export * from './types';
export { DataLoader, getDataLoader } from './data/DataLoader';
export { TimezoneHandler } from './timezone/TimezoneHandler';
export { LunisolarCalendar } from './core/LunisolarCalendar';
export { ConstructionStars } from './huangdao/ConstructionStars';
export { GreatYellowPath } from './huangdao/GreatYellowPath';

// Configuration API (v0.2.0+)
import { setConfig, getConfig } from './config';
import type { LunisolarOptions } from './config';
export type { LunisolarOptions, DataLoaderStrategy } from './config';

/**
 * Configure the global data loading strategy.
 * Example:
 *   import { configure } from 'lunisolar-ts';
 *   configure({ strategy: 'fetch' }); // default CDN base
 */
export function configure(options: LunisolarOptions = {}): void {
  setConfig(options);
}

// Optional: expose current config snapshot (read-only)
export const getConfiguration = getConfig;

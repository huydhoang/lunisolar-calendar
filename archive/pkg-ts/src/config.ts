// Global configuration for data loading strategy and sources

export type DataLoaderStrategy = 'fetch' | 'static';

export interface LunisolarOptions {
  strategy?: DataLoaderStrategy; // default: 'fetch'
  data?: {
    // Optional absolute base URL to a CDN or self-hosted location.
    // Example: 'https://cdn.jsdelivr.net/npm/lunisolar-ts@<version>/dist/data'
    // If omitted, a default CDN base will be used.
    baseUrl?: string;
  };
}

type InternalConfig = {
  strategy: DataLoaderStrategy;
  data: {
    baseUrl?: string;
  };
};

// Defaults: fetch strategy with version-pinned CDN computed in DataLoader when needed
const DEFAULTS: InternalConfig = {
  strategy: 'fetch',
  data: {},
};

let current: InternalConfig = { ...DEFAULTS };

/**
 * Returns a shallow-cloned snapshot of the current configuration.
 */
export function getConfig(): InternalConfig {
  return { ...current, data: { ...current.data } };
}

/**
 * Merge and set global configuration. Call once at app bootstrap:
 *
 *   import { configure } from 'lunisolar-ts';
 *   configure({ strategy: 'fetch', data: { baseUrl: 'https://cdn.example.com/lunisolar/data' } });
 */
export function setConfig(options: LunisolarOptions = {}): void {
  current = {
    strategy: options.strategy ?? current.strategy,
    data: {
      ...current.data,
      ...(options.data ?? {}),
    },
  };
}
import type { TNewMoon, TSolarTerm } from '../types';
import { getConfig } from '../config';
import { loadData } from './manifest';

// __VERSION__ is injected by rollup (@rollup/plugin-replace) at build time.
declare const __VERSION__: string;

type DataType = 'new_moons' | 'solar_terms';

/**
 * DataLoader lazily loads JSON chunks for a given year and caches them.
 *
 * v0.2.0 strategy:
 * - Default 'fetch' strategy with absolute, version-pinned CDN base URL:
 *   https://cdn.jsdelivr.net/npm/lunisolar-ts@__VERSION__/dist/data
 * - Optional 'static' strategy via generated manifest that uses static import()s
 * - Node fs fallback only when a relative baseUrl is provided and files exist locally (Node 22+)
 */
export class DataLoader {
  private _cache = new Map<string, unknown>();
  private _deprecatedBaseUrl?: string;

  /**
   * Deprecated: constructor options are ignored starting v0.2.0.
   * Use the top-level configure() API to set global options.
   * This path will be removed in v0.3.0.
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  constructor(opts?: any) {
    if (opts && Object.keys(opts).length > 0) {
      // Runtime warning for one minor release
      // eslint-disable-next-line no-console
      console.warn(
        '[lunisolar-ts] DataLoader constructor options are deprecated. ' +
          'Use configure({ strategy, data: { baseUrl } }) instead.'
      );
      if (typeof opts.baseUrl === 'string') {
        this._deprecatedBaseUrl = opts.baseUrl;
      }
    }
  }

  async getNewMoons(year: number): Promise<TNewMoon[]> {
    return this._get<number[]>(`new_moons:${year}`, () => this._load('new_moons', year));
  }

  async getSolarTerms(year: number): Promise<TSolarTerm[]> {
    return this._get<TSolarTerm[]>(`solar_terms:${year}`, () => this._load('solar_terms', year));
  }

  // Core loader switch
  private async _load(kind: DataType, year: number): Promise<any> {
    const cfg = getConfig();
    if (cfg.strategy === 'static') {
      // Static bundling via generated manifest file
      return loadData(kind, year);
    }

    // Fetch strategy (default)
    const base = this._computeBaseUrl();
    const url = this._buildUrl(base, kind, year);

    try {
      return await this._fetchJson(url);
    } catch (err) {
      // Node fs fallback only if user provided a relative baseUrl and we're in Node
      const userBase = cfg.data?.baseUrl ?? this._deprecatedBaseUrl;
      if (this._isNode() && userBase && this._isRelative(userBase)) {
        try {
          return await this._readLocalJson(this._buildRelativePath(userBase, kind, year));
        } catch {
          // fall through to throw original fetch error
        }
      }
      throw err;
    }
  }

  private async _get<T>(key: string, loader: () => Promise<T>): Promise<T> {
    if (this._cache.has(key)) return this._cache.get(key) as T;
    const data = await loader();
    this._cache.set(key, data);
    return data;
  }

  private _computeBaseUrl(): string {
    const cfg = getConfig();
    const user = cfg.data?.baseUrl ?? this._deprecatedBaseUrl;
    if (user) return this._trimTrailingSlash(user);
    // Default CDN pinned to package version
    return `https://cdn.jsdelivr.net/npm/lunisolar-ts@${__VERSION__}/dist/data`;
  }

  private _buildUrl(base: string, kind: DataType, year: number): string {
    const b = this._trimTrailingSlash(base);
    return `${b}/${kind}/${year}.json`;
  }

  private _buildRelativePath(base: string, kind: DataType, year: number): string {
    const b = this._trimTrailingSlash(base);
    return `${b}/${kind}/${year}.json`;
  }

  private _trimTrailingSlash(s: string): string {
    return s.endsWith('/') ? s.slice(0, -1) : s;
  }

  private _isNode(): boolean {
    return typeof process !== 'undefined' && !!process.versions?.node;
  }

  private _isRelative(p: string): boolean {
    return p.startsWith('./') || p.startsWith('../');
  }

  private async _fetchJson<T>(url: string): Promise<T> {
    if (typeof fetch !== 'function') {
      throw new Error('Global fetch is not available. Node 22+ is required.');
    }
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to load ${url}: ${res.status} ${res.statusText}`);
    return (await res.json()) as T;
  }

  private async _readLocalJson<T>(relativePath: string): Promise<T> {
    const [{ readFile }, { fileURLToPath }, { resolve, dirname }] = await Promise.all([
      import('node:fs/promises'),
      import('node:url'),
      import('node:path'),
    ]);
    const baseDir = dirname(fileURLToPath(import.meta.url));
    const filePath = resolve(baseDir, relativePath);
    const txt = await readFile(filePath, 'utf-8');
    return JSON.parse(txt) as T;
  }
}

// Shared singleton-like loader to be used across the package
export const dataLoader = new DataLoader();
export function getDataLoader(): DataLoader {
  return dataLoader;
}

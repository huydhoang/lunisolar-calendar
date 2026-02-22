# Plan v0.2.0: Serverless Data Loading Implementation (Revised and Final)

This plan implements a robust hybrid data-loading strategy that works out-of-the-box across Vercel Serverless, Vercel Edge, Cloudflare Workers, browsers, and Node 22+. It replaces the hardcoded ./data path currently used at [LunisolarCalendar.fromSolarDate()](pkg/dist/index.mjs:195) where the loader is constructed at [new DataLoader({ baseUrl: './data' })](pkg/dist/index.mjs:200), and delivers:
- Default fetch strategy with an absolute, version-pinned CDN base URL
- Optional static bundling via a generated manifest with static import()s
- Node fs fallback for classic server environments
- Backwards-compatible deprecation of DataLoader constructor options

The package will publish dist/data for years 1900–2100 so the default CDN path always serves immutable data.

## 1) Configuration and Core Module Refactoring

- [ ] Create a global configuration module at [src/config.ts](pkg/src/config.ts)
  - Holds user-defined configuration, e.g.:
    ```ts
    export type DataLoaderStrategy = 'fetch' | 'static';
    export interface LunisolarOptions {
      strategy?: DataLoaderStrategy; // default 'fetch'
      data?: { baseUrl?: string };
    }
    ```
  - Exports getConfig() and setConfig(options) functions

- [ ] Implement a top-level configure API in [src/index.ts](pkg/src/index.ts)
  - Export [configure()](pkg/src/index.ts) to set the global options once at app startup
  - This becomes the primary configuration mechanism for consumers

- [ ] Refactor DataLoader to read from global config in [src/data/DataLoader.ts](pkg/src/data/DataLoader.ts)
  - Make it singleton-like; remove constructor options
  - Strategy switching:
    - strategy === 'static' → use generated manifest loader
    - strategy === 'fetch' (default) → use fetch with absolute baseUrl, fallback to fs only in Node
  - Deprecate new DataLoader({...}) with a runtime warning for one minor release

- [ ] Update types in [src/types.ts](pkg/src/types.ts)
  - Add types: LunisolarOptions, DataLoaderStrategy, etc.

## 2) Build Process for Static Bundling

Goal: make JSON data available before Rollup runs so bundlers can include exactly what the app needs.

- [ ] Create script: [scripts/copy-data-to-src.mjs](pkg/scripts/copy-data-to-src.mjs)
  - Copies from root [output](output) to [pkg/src/data/precomputed](pkg/src/data/precomputed)
  - Directory layout:
    - precomputed/new_moons/{year}.json
    - precomputed/solar_terms/{year}.json
    - precomputed/full_moons/{year}.json (if used)
  - Note: [pkg/.gitignore](pkg/.gitignore) must ignore src/data/precomputed

- [ ] Create script: [scripts/generate-data-manifest.mjs](pkg/scripts/generate-data-manifest.mjs)
  - Scans [pkg/src/data/precomputed](pkg/src/data/precomputed)
  - Generates [pkg/src/data/manifest.ts](pkg/src/data/manifest.ts) that exports:
    - [loadData()](pkg/src/data/manifest.ts) with static string-literal import() calls, e.g.:
      ```ts
      export async function loadData(
        dataType: 'new_moons' | 'solar_terms',
        year: number
      ): Promise<any> {
        switch (dataType) {
          case 'new_moons':
            switch (year) {
              case 2025:
                return (await import('./precomputed/new_moons/2025.json', { assert: { type: 'json' } })).default;
              // ... more cases
            }
            break;
          // ... other data types
        }
        throw new Error(`No static data for ${dataType}/${year}`);
      }
      ```

- [ ] Ensure postbuild copy for CDN publishing: [scripts/copy-data.mjs](pkg/scripts/copy-data.mjs)
  - Copies from root [output](output) to [pkg/dist/data](pkg/dist/data)
  - This guarantees npm tarball contains dist/data for all supported years (1900–2100)

- [ ] Update NPM scripts in [package.json](pkg/package.json)
  - "prebuild": "node scripts/copy-data-to-src.mjs && node scripts/generate-data-manifest.mjs"
  - "build": "npm run prebuild && rollup -c"
  - "postbuild": "node scripts/copy-data.mjs" (kept and implemented)

- [ ] Update ignore rules
  - Add src/data/precomputed/ to [pkg/.gitignore](pkg/.gitignore)
  - Keep dist/ in package files list per [package.json files](pkg/package.json:9)

## 3) Data Loading Strategy Implementation

- [ ] Strategy switching in DataLoader
  - static → use [loadData()](pkg/src/data/manifest.ts)
  - fetch (default) → construct URL `${baseUrl}/${dataType}/${year}.json`

- [ ] Default fetch baseUrl
  - If not provided by user, default to:
    - https://cdn.jsdelivr.net/npm/lunisolar-ts@<version>/dist/data
  - Version is injected at build time from [package.json version](pkg/package.json:3)

- [ ] Version injection
  - Add replace to [rollup.config.mjs](pkg/rollup.config.mjs:1) to inject a constant (e.g., __VERSION__)
    ```ts
    import replace from '@rollup/plugin-replace';
    // ...
    plugins: [
      // ...
      replace({
        preventAssignment: true,
        __VERSION__: JSON.stringify(process.env.npm_package_version),
      }),
      // ...
    ]
    ```
  - DataLoader builds default baseUrl using __VERSION__

- [ ] Node fs fallback
  - Keep as last resort in Node 22+ when baseUrl is relative and files exist locally
  - In Edge/Workers/Browsers, do not attempt fs

- [ ] Node baseline: 22+
  - Use global fetch without polyfills

## 4) Integration and Refactoring

- [ ] Update LunisolarCalendar to use shared DataLoader instance
  - Remove direct instantiation from [LunisolarCalendar.fromSolarDate()](pkg/dist/index.mjs:195)
  - Import shared loader and read from global config

- [ ] Update ConstructionStars
  - Ensure no direct instantiation with constructor options; use shared loader

- [ ] Backwards compatibility
  - new DataLoader({...}) emits a deprecation warning for one minor version
  - README updated with configure-first approach

## 5) Documentation and Testing

- [ ] Update docs
  - Expand [docs/serverless.md](docs/serverless.md) with:
    - Default CDN baseUrl (jsDelivr /dist/data), zero-config examples
    - Static bundling notes and JSON import assertion guidance
    - Runtime matrix (Vercel Serverless/Edge, Cloudflare Workers, browsers, Node 22+)

- [ ] Update README
  - Add configure usage
  - Mention default zero-config behavior and how to self-host baseUrl

- [ ] Tests
  - Unit/integration tests for:
    - fetch default strategy (mock fetch), absolute CDN baseUrl construction
    - static bundling strategy via manifest (importable in test bundler)
    - Node fs fallback (only in Node)
    - removal of './data' hardcode in calendar logic

## 6) Acceptance Criteria and Runtime Matrix

Zero-config targets must work by default without any user configuration:

- [ ] Vercel Serverless Functions
  - Default fetch + jsDelivr CDN works; no fs usage
- [ ] Vercel Edge Runtime
  - Default fetch + CDN works; absolute URLs only
- [ ] Cloudflare Workers
  - Default fetch + CDN works; absolute URLs only
- [ ] Browsers
  - Default fetch + CDN works; CORS considerations documented
- [ ] Node 22+
  - Default fetch + CDN works
  - fs fallback works when baseUrl is relative and dist/data exists on disk

Static bundling:

- [ ] Bundlers (Vite/Rollup/Webpack) can include only referenced years via [manifest.ts](pkg/src/data/manifest.ts)
- [ ] Document that JSON import assertions may be required and how to enable them

Data publishing:

- [ ] NPM package includes [dist/data](pkg/dist/data) for years 1900–2100
- [ ] CDN path https://cdn.jsdelivr.net/npm/lunisolar-ts@<version>/dist/data resolves and serves

## 7) Notes and Risks

- Package size: shipping 1900–2100 under dist/data increases tarball size. Confirm acceptable threshold; if exceeded, consider compression or splitting data in a future minor.
- Relative fetch baseUrl in edge/browsers is invalid; always use absolute URLs or default CDN.
- Keep a deprecation window for constructor options; remove in v0.3.0.

## Summary of Key Changes from v0.1.x

- Remove hardcoded './data' loader in calendar
- Introduce [configure()](pkg/src/index.ts) and global config
- Default to jsDelivr CDN under /dist/data pinned by version
- Implement manifest-based static bundling path
- Ensure NPM publishes dist/data so CDN works out-of-the-box

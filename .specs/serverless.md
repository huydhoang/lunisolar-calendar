# Bundling Precomputed Data for Serverless/Edge Environments

The lunisolar-ts package requires precomputed astronomical data to perform its calculations. In serverless and edge environments (Vercel Serverless/Edge, Cloudflare Workers, browsers), you cannot rely on Node fs at runtime. This document describes the hybrid strategy that works in all these environments with **zero configuration by default** (v0.2.0+).

## The Challenge: Filesystem Limitations

Lazy-loading JSON files from the package directory via fs at runtime will fail in many environments. The data must be available via either network fetch or static bundling inside the application/server bundle.

## Implementation Status (v0.2.0+)

✅ **Fully Implemented** - The hardcoded './data' path has been removed and replaced with a flexible, configurable data loading system.

### Key Features

1. **Zero-Config Default**: Uses version-pinned CDN (jsDelivr) automatically
2. **Global Configuration API**: `configure({ strategy, data })` for customization
3. **Multiple Strategies**: Fetch (default), static bundling, or Node fs fallback
4. **Deprecation Handling**: Constructor options deprecated with warnings (removed in v0.3.0)

## Data Loading Strategies (v0.2.0+)

The library supports two complementary strategies. The default is fetch-based with an absolute CDN base URL, pinned to the package version. Users can opt into static bundling for maximal performance.

### 1) Dynamic Loading via Fetch (Default - Zero Config)

**How it works:**

The library automatically loads data from a version-pinned CDN without any configuration:

```ts
import { LunisolarCalendar } from 'lunisolar-ts';

// No configuration needed - works immediately
const cal = await LunisolarCalendar.fromSolarDate(new Date(), 'Asia/Shanghai');
```

**Default CDN URL:**
```
https://cdn.jsdelivr.net/npm/lunisolar-ts@<version>/dist/data
```

The `<version>` is automatically injected at build time from package.json, ensuring immutable, reproducible data access.

**Custom CDN (Optional):**

```ts
import { configure } from 'lunisolar-ts';

// Call once at app startup
configure({
  strategy: 'fetch',
  data: {
    baseUrl: 'https://your-cdn.com/lunisolar-data'
  }
});
```

**Node.js fs Fallback:**

In Node 22+ environments, when a relative baseUrl is provided (e.g., `'./data'`), the loader will attempt to read from the local filesystem as a last resort if the fetch fails. This is useful for development or air-gapped deployments.

**Pros:**
- ✅ Zero configuration required
- ✅ Works in all environments (Vercel, Cloudflare Workers, browsers, Node)
- ✅ Small initial bundle size (data loaded on-demand)
- ✅ Version-pinned for reproducibility

**Cons:**
- ❌ Requires network access
- ❌ Adds runtime latency (~50-200ms per year of data)

### 2) Static Bundling via Manifest (Advanced)

For applications requiring maximum performance or offline capability, you can bundle data directly into your application.

**How it works:**

1. The build process generates a manifest with static `import()` calls:

```ts
// Auto-generated: pkg/src/data/manifest.ts
export async function loadData(dataType: 'new_moons'|'solar_terms', year: number) {
  switch (dataType) {
    case 'new_moons':
      switch (year) {
        case 2025: return (await import('./precomputed/new_moons/2025.json')).default;
        // ... cases for each year (1901-2100)
      }
  }
}
```

2. Configure your app to use static strategy:

```ts
import { configure } from 'lunisolar-ts';

configure({ strategy: 'static' });
```

3. Your bundler (Vite/Rollup/Webpack) will include only the JSON files actually referenced by your code, enabling tree-shaking.

**Pros:**
- ✅ Zero network latency
- ✅ Works offline
- ✅ Tree-shakeable (only includes referenced years)
- ✅ Co-located with application code

**Cons:**
- ❌ Larger application bundle
- ❌ Requires modern bundler with JSON import support

## Runtime Environment Support

### Tested and Verified Environments

| Environment | Status | Default Strategy | Notes |
|------------|--------|------------------|-------|
| **Vercel Serverless** | ✅ Works | Fetch (CDN) | Zero config required |
| **Vercel Edge Runtime** | ✅ Works | Fetch (CDN) | Only absolute URLs supported |
| **Cloudflare Workers** | ✅ Works | Fetch (CDN) | Only absolute URLs supported |
| **Modern Browsers** | ✅ Works | Fetch (CDN) | CORS headers provided by jsDelivr |
| **Node.js 22+** | ✅ Works | Fetch (CDN) | Native `fetch` available; fs fallback for relative paths |

### Requirements

- **Node.js**: Version 22 or higher (requires native `fetch` support)
- **Bundlers**: Modern bundler with JSON import support for static strategy (Vite, Rollup, Webpack 5+)

## Configuration Examples

### Zero-Config (Recommended)

No configuration needed - just use the library:

```ts
import { LunisolarCalendar } from 'lunisolar-ts';

const cal = await LunisolarCalendar.fromSolarDate(new Date(), 'Asia/Shanghai');
```

Data is automatically fetched from:
```
https://cdn.jsdelivr.net/npm/lunisolar-ts@0.1.0/dist/data
```

### Self-Hosted Data

Host data on your own CDN or server:

```ts
import { configure } from 'lunisolar-ts';

// Call once at app startup, before any calendar operations
configure({
  strategy: 'fetch',
  data: {
    baseUrl: 'https://cdn.your-app.com/lunisolar/data'
  }
});

// Then use normally
const cal = await LunisolarCalendar.fromSolarDate(new Date(), 'Asia/Shanghai');
```

**Note**: Your CDN must serve the same directory structure:
```
baseUrl/new_moons/2025.json
baseUrl/solar_terms/2025.json
baseUrl/full_moons/2025.json
```

### Static Bundling for Performance

Bundle data directly into your application for zero-latency access:

```ts
import { configure } from 'lunisolar-ts';

// Enable static bundling
configure({ strategy: 'static' });

// Your bundler will include only referenced data files
const cal = await LunisolarCalendar.fromSolarDate(new Date(), 'Asia/Shanghai');
```

**Bundler Configuration:**

Most modern bundlers support JSON imports out of the box. If you encounter issues, ensure:

- **Vite**: JSON imports work by default
- **Rollup**: Use `@rollup/plugin-json`
- **Webpack 5+**: JSON imports enabled by default

### Node.js Development with Local Files

For local development or air-gapped deployments:

```ts
import { configure } from 'lunisolar-ts';

configure({
  strategy: 'fetch',
  data: {
    baseUrl: './data'  // Relative path triggers fs fallback in Node.js
  }
});
```

This will attempt fetch first, then fall back to reading from `node_modules/lunisolar-ts/dist/data/`.

## Important Notes

### Data Availability

- The npm package includes `dist/data` with precomputed data for **years 1901-2100**
- CDN path structure: `https://cdn.jsdelivr.net/npm/lunisolar-ts@<version>/dist/data/{dataType}/{year}.json`
- Data types: `new_moons`, `solar_terms`, `full_moons`

### CORS Considerations

When self-hosting data, ensure your CDN/server returns appropriate CORS headers:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, HEAD, OPTIONS
```

jsDelivr CDN provides these headers by default.

### Version Pinning

The default CDN URL includes the package version (e.g., `@0.1.0`), ensuring:
- ✅ Immutable data access
- ✅ No cache invalidation issues
- ✅ Reproducible builds

When upgrading the library, data automatically points to the new version's dataset.

### Relative URLs

**Important**: Relative URLs like `./data/...` are **not** module-relative in browsers/edge environments. They will fail in:
- Browsers (resolves relative to current page URL)
- Vercel Edge Runtime
- Cloudflare Workers

Always use absolute URLs or the default CDN for these environments.

### Migration from v0.1.x

If you were using `new DataLoader({ baseUrl: './data' })`:

1. Remove direct `DataLoader` instantiation
2. Use `configure()` at app startup instead:

```ts
import { configure } from 'lunisolar-ts';

configure({
  strategy: 'fetch',
  data: { baseUrl: './data' }  // If you need local fs fallback
});
```

Constructor options are deprecated and will be removed in v0.3.0.

## Summary

lunisolar-ts v0.2.0+ provides a robust, flexible data loading system:

- ✅ **Zero-config default** using version-pinned CDN (jsDelivr)
- ✅ **Serverless-first** design works everywhere
- ✅ **Configurable** for custom CDN or static bundling
- ✅ **Backward compatible** with deprecation warnings
- ✅ **Production-ready** for Vercel, Cloudflare Workers, browsers, and Node 22+

The library reliably handles data loading across all deployment targets without requiring runtime filesystem access.

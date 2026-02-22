# lunisolar-wasm

Chinese lunisolar calendar conversion compiled to WebAssembly via Emscripten, with embedded Swiss Ephemeris (`.se1` data files).

Converts Gregorian (solar) dates to lunisolar dates with full sexagenary (Gan-Zhi) cycle support and Huangdao systems (12 Construction Stars, Great Yellow Path).

## Installation

```bash
npm install lunisolar-wasm
```

## Usage

### Standalone (recommended)

Uses the embedded Swiss Ephemeris to compute new moons and solar terms automatically — no pre-computed data needed:

```js
import createLunisolarEmcc from 'lunisolar-wasm';

const mod = await createLunisolarEmcc();

// Allocate output buffer
const outLen = 1024;
const outPtr = mod._malloc(outLen);

const timestampMs = Date.now();
const tzOffsetSec = 28800; // UTC+8 (e.g. Asia/Shanghai)

const bytesWritten = mod._from_solar_date_auto(
  timestampMs,
  tzOffsetSec,
  outPtr,
  outLen
);

if (bytesWritten > 0) {
  const json = mod.UTF8ToString(outPtr, bytesWritten);
  console.log(JSON.parse(json));
}

mod._free(outPtr);
```

### With pre-computed data

For higher throughput or when using your own astronomical data:

```js
const result = mod._from_solar_date(
  timestampMs,    // Unix timestamp in milliseconds
  tzOffsetSec,    // Timezone offset in seconds
  nmPtr, nmCount, // New moon timestamps (Float64 array pointer + count)
  stTsPtr, stIdxPtr, stCount, // Solar term timestamps + indices
  outPtr, outBufLen           // Output buffer
);
```

## Building from Source

Requires the [Emscripten SDK](https://emscripten.org/docs/getting_started/downloads.html):

```bash
npm run build
```

## License

MIT

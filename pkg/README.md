# lunisolar-wasm

Chinese lunisolar calendar conversion compiled to WebAssembly via Emscripten.

Converts Gregorian (solar) dates to lunisolar dates with full sexagenary (Gan-Zhi) cycle support and Huangdao systems (12 Construction Stars, Great Yellow Path).

## Installation

```bash
npm install lunisolar-wasm
```

## Usage

```js
import createLunisolarEmcc from 'lunisolar-wasm';

const mod = await createLunisolarEmcc();

// Prepare pre-computed astronomical data (new moon timestamps, solar terms)
// Then call the from_solar_date function via the WASM module
const result = mod._from_solar_date(
  timestampMs,    // Unix timestamp in milliseconds
  tzOffsetSec,    // Timezone offset in seconds (e.g. 28800 for UTC+8)
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

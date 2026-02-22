# lunisolar-ts

TypeScript library for the Chinese lunisolar calendar with precomputed astronomical data.

[![npm version](https://img.shields.io/npm/v/lunisolar-ts.svg)](https://www.npmjs.com/package/lunisolar-ts)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

## Features

- 🌙 **Lunisolar Calendar Conversion**: Convert Gregorian dates to Chinese lunisolar dates
- ⭐ **Construction Stars (十二建星)**: Calculate auspicious days using the Twelve Construction Stars system
- 🌟 **Great Yellow Path (大黄道)**: Determine daily spirits and their influence
- 🔮 **Sexagenary Cycle (天干地支)**: Full Gan-Zhi calculations for year, month, day, and hour
- 📊 **Precomputed Data**: High-precision astronomical data powered by NASA's JPL DE440 ephemeris
- 🌍 **Timezone Support**: Accurate calculations for any timezone
- 📦 **Modern Package**: ESM and CommonJS support with TypeScript declarations
- ☁️ **Serverless Ready**: Works out-of-the-box in Vercel, Cloudflare Workers, browsers, and Node 22+ with zero configuration

## Installation

```bash
npm install lunisolar-ts
```

## Quick Start

```typescript
import { LunisolarCalendar, ConstructionStars, GreatYellowPath } from 'lunisolar-ts';

// Convert a date to lunisolar calendar (zero-config, uses CDN by default)
const now = new Date();
const cal = await LunisolarCalendar.fromSolarDate(now, 'Asia/Ho_Chi_Minh');

console.log(`Lunar Date: ${cal.lunarYear}/${cal.lunarMonth}/${cal.lunarDay}`);
console.log(`Year Stem-Branch: ${cal.yearStem}-${cal.yearBranch}`);
console.log(`Is Leap Month: ${cal.isLeapMonth}`);

// Get Construction Star for the day
const cs = new ConstructionStars(cal);
const star = cs.getStar();
console.log(`Construction Star: ${star.name} (${star.description})`);

// Get Great Yellow Path spirit
const gyp = new GreatYellowPath(cal);
const spirit = gyp.getSpirit();
console.log(`Spirit: ${spirit.name}`);

// Find auspicious days in a month
const auspiciousDays = await ConstructionStars.getAuspiciousDays(2025, 1, 3);
console.log(`Found ${auspiciousDays.length} auspicious days`);
```

## Configuration (Optional)

By default, the library loads data from a version-pinned CDN (jsDelivr) with zero configuration required. For advanced use cases, you can customize the data loading strategy:

### Use Default CDN (Recommended)

```typescript
import { configure } from 'lunisolar-ts';

// Explicit CDN configuration (this is the default, no need to call unless customizing)
configure({
  strategy: 'fetch'
  // Uses: https://cdn.jsdelivr.net/npm/lunisolar-ts@<version>/dist/data
});
```

### Self-Hosted Data

```typescript
import { configure } from 'lunisolar-ts';

// Point to your own CDN or server
configure({
  strategy: 'fetch',
  data: {
    baseUrl: 'https://your-cdn.com/lunisolar-data'
  }
});
```

### Static Bundling (Advanced)

For maximum performance, bundle data directly into your application:

```typescript
import { configure } from 'lunisolar-ts';

// Enable static bundling via manifest
configure({ strategy: 'static' });

// Bundlers (Vite/Rollup/Webpack) will include only referenced years
```

**Note**: Call `configure()` once at application startup, before using any calendar functions.

See [`docs/serverless.md`](../docs/serverless.md) for detailed configuration options and deployment scenarios.

## Development

For contributors and developers:

### Scripts
- `npm run build` — Build CJS and ESM outputs using Rollup
- `npm run typecheck` — Type-check the project
- `npm run lint` — Lint with ESLint
- `npm run format` — Format with Prettier
- `npm test` — Run tests
- `npm run examples` — Run example scripts

### Publishing

See [`PUBLISHING.md`](./PUBLISHING.md) for detailed instructions on publishing to npm.

## API Reference

### Core
#### `LunisolarCalendar`

**Static Methods:**
- `fromSolarDate(date: Date, timezone: string): Promise<LunisolarCalendar>` - Convert a Gregorian date to lunisolar calendar

**Instance Properties:**
- `lunarYear: number` - Lunar year
- `lunarMonth: number` - Lunar month (1-12)
- `lunarDay: number` - Lunar day (1-30)
- `isLeapMonth: boolean` - Whether the current month is a leap month
- `yearStem: string` - Heavenly Stem of the year
- `yearBranch: string` - Earthly Branch of the year
- `monthStem: string` - Heavenly Stem of the month
- `monthBranch: string` - Earthly Branch of the month
- `dayStem: string` - Heavenly Stem of the day
- `dayBranch: string` - Earthly Branch of the day
- `hourStem: string` - Heavenly Stem of the hour
- `hourBranch: string` - Earthly Branch of the hour
- `isPrincipalSolarTermDay: boolean` - Whether the day is a principal solar term day

### Huangdao Systems

#### `ConstructionStars`

Traditional Twelve Construction Stars (十二建星) system for day selection.

**Constructor:**
- `new ConstructionStars(calendar: LunisolarCalendar)`

**Methods:**
- `getStar(): TConstructionStar` - Get the construction star for the day (respects principal solar term day repetition)
- `static getAuspiciousDays(year: number, month: number, minScore: number): Promise<TDayInfo[]>` - Find auspicious days in a month

#### `GreatYellowPath`

Great Yellow Path (大黄道) system for determining daily spiritual influences.

**Constructor:**
- `new GreatYellowPath(calendar: LunisolarCalendar)`

**Methods:**
- `getSpirit(): TGreatYellowPathSpirit` - Get the spirit for the day

## License

MIT License - see [`LICENSE`](./LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Related Projects

- Python implementation with data generation pipeline in the parent directory
- Uses NASA JPL DE440 ephemeris data for high-precision astronomical calculations

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/yourusername/lunisolar-ts).

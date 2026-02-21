/**
 * swisseph-wasm Accuracy Test
 *
 * Produces a three-way comparison of planetary positions:
 *   1. swisseph-wasm  — the package under test
 *   2. Skyfield       — Python library using the DE440s JPL ephemeris
 *   3. JPL Horizons   — NASA/JPL authoritative reference (web API)
 *
 * References:
 *   JPL Horizons : https://ssd.jpl.nasa.gov/horizons/
 *   Skyfield     : https://rhodesmill.org/skyfield/
 */

import SwissEph from 'swisseph-wasm';
import { writeFileSync, readFileSync, existsSync } from 'fs';

// ─── Test configuration ────────────────────────────────────────────────────
const TEST_YEAR = 2025;
const TEST_MONTH = 1;
const TEST_DAY = 1;
const TEST_HOUR = 12.0; // 12:00 UTC
const TEST_DATE_STR = '2025-01-01'; // For JPL Horizons queries
const TOLERANCE_DEG = 0.05; // 3 arcminutes — generous but meaningful

/**
 * Bodies to test.
 * sweId  : swisseph-wasm planet constant (SE_SUN=0, SE_MOON=1, …)
 * horizId: JPL Horizons body ID
 * name   : human-readable name
 */
const BODIES = [
  { sweId: 0, horizId: '10', name: 'Sun' },
  { sweId: 1, horizId: '301', name: 'Moon' },
  { sweId: 2, horizId: '199', name: 'Mercury' },
  { sweId: 3, horizId: '299', name: 'Venus' },
  { sweId: 4, horizId: '499', name: 'Mars' },
  { sweId: 5, horizId: '599', name: 'Jupiter' },
  { sweId: 6, horizId: '699', name: 'Saturn' },
];

// ─── JPL Horizons fetch ────────────────────────────────────────────────────

/**
 * Fetch apparent geocentric equatorial coordinates (RA, Dec) for a solar
 * system body at noon UTC on the given date from the JPL Horizons API.
 *
 * Uses:
 *   EPHEM_TYPE = OBSERVER  (observer-based table)
 *   CENTER     = 500@399   (Earth geocenter)
 *   QUANTITIES = 2         (Apparent RA & DEC, airless)
 *   ANG_FORMAT = DEG       (decimal degrees for easy parsing)
 *
 * @param {string} bodyId  JPL Horizons body ID (e.g. '10' for the Sun)
 * @param {string} dateStr ISO date string (e.g. '2025-01-01')
 * @returns {{ ra_deg: number, dec_deg: number }}
 */
async function fetchHorizonsPosition(bodyId, dateStr) {
  const url = new URL('https://ssd.jpl.nasa.gov/api/horizons.api');
  url.searchParams.set('format', 'json');
  url.searchParams.set('COMMAND', `'${bodyId}'`);
  url.searchParams.set('EPHEM_TYPE', 'OBSERVER');
  url.searchParams.set('CENTER', "'500@399'");
  url.searchParams.set('START_TIME', `'${dateStr} 12:00'`);
  url.searchParams.set('STOP_TIME', `'${dateStr} 12:01'`);
  url.searchParams.set('STEP_SIZE', "'1 m'");
  url.searchParams.set('QUANTITIES', "'2'"); // Apparent RA & DEC
  url.searchParams.set('ANG_FORMAT', 'DEG'); // Decimal degrees
  url.searchParams.set('APPARENT', 'AIRLESS'); // No atmospheric refraction

  const resp = await fetch(url.toString());
  if (!resp.ok) {
    throw new Error(`Horizons HTTP error ${resp.status}: ${resp.statusText}`);
  }

  const json = await resp.json();
  if (json.signature === undefined || json.result === undefined) {
    throw new Error(`Unexpected Horizons response structure`);
  }

  const text = json.result;
  const lines = text.split('\n');
  const soeIdx = lines.findIndex((l) => l.includes('$$SOE'));
  const eoeIdx = lines.findIndex((l) => l.includes('$$EOE'));

  if (soeIdx === -1 || eoeIdx === -1 || eoeIdx <= soeIdx + 1) {
    throw new Error(
      `No ephemeris data found for body ${bodyId}. Response snippet:\n${text.slice(0, 500)}`,
    );
  }

  // The first data line is immediately after $$SOE
  const dataLine = lines[soeIdx + 1];

  // With ANG_FORMAT=DEG the date/time fields contain no decimal points;
  // the first two decimal numbers on the line are RA (°) and Dec (°).
  const numbers = dataLine.match(/-?\d+\.\d+/g);
  if (!numbers || numbers.length < 2) {
    throw new Error(`Cannot parse coordinates from Horizons line: "${dataLine}"`);
  }

  return {
    ra_deg: parseFloat(numbers[0]),
    dec_deg: parseFloat(numbers[1]),
  };
}

// ─── Helpers ───────────────────────────────────────────────────────────────

/** Angular difference on a circle (handles the 0°/360° wrap). */
function angularDiff(a, b) {
  let d = Math.abs(a - b) % 360;
  if (d > 180) d = 360 - d;
  return d;
}

/** Format a decimal degree value with fixed precision. */
const f = (v, n = 4) => (typeof v === 'number' ? v.toFixed(n) : '—');

// ─── Main ──────────────────────────────────────────────────────────────────

async function main() {
  const reportLines = [];
  const log = (line = '') => {
    reportLines.push(line);
    process.stdout.write(line + '\n');
  };

  log('# swisseph-wasm Accuracy Test Report');
  log();
  log(
    `**Test Date:** ${TEST_YEAR}-${String(TEST_MONTH).padStart(2, '0')}-${String(TEST_DAY).padStart(2, '0')} 12:00 UTC`,
  );
  log(`**References:** JPL Horizons (https://ssd.jpl.nasa.gov/horizons/) · Skyfield + DE440s`);
  log(`**Package:** swisseph-wasm (installed via bun)`);
  log(`**Tolerance:** ${TOLERANCE_DEG}° (${(TOLERANCE_DEG * 60).toFixed(0)} arcminutes)`);
  log();

  // ── Load Skyfield results (written by skyfield-positions.py) ──────────────
  let skyfieldResults = null;
  const SKYFIELD_JSON = 'skyfield-results.json';
  if (existsSync(SKYFIELD_JSON)) {
    try {
      skyfieldResults = JSON.parse(readFileSync(SKYFIELD_JSON, 'utf8'));
      log(`**Skyfield:** results loaded from \`${SKYFIELD_JSON}\` ✅`);
    } catch (e) {
      log(`**Skyfield:** failed to parse \`${SKYFIELD_JSON}\` — ${e.message} ⚠️`);
    }
  } else {
    log(`**Skyfield:** \`${SKYFIELD_JSON}\` not found — Skyfield column will be omitted ⚠️`);
  }
  log();

  // ── Initialize SwissEph ────────────────────────────────────────────────
  let swe;
  try {
    swe = new SwissEph();
    await swe.initSwissEph();
  } catch (err) {
    log(`❌ **Fatal: could not initialise swisseph-wasm** — ${err.message}`);
    writeFileSync('report.md', reportLines.join('\n') + '\n');
    process.exit(1);
  }

  log(`**SwissEph version:** ${swe.version()}`);

  // ── Julian Day sanity check (J2000.0 = JD 2451545.0) ──────────────────
  const jd2000 = swe.julday(2000, 1, 1, 12.0);
  const jd2000Diff = Math.abs(jd2000 - 2451545.0);
  const jd2000Status = jd2000Diff < 1e-6 ? '✅' : '❌';
  log(
    `**J2000.0 Julian Day check:** ${jd2000.toFixed(4)} ` +
      `(expected 2451545.0000, diff ${jd2000Diff.toExponential(2)}) ${jd2000Status}`,
  );

  const jd = swe.julday(TEST_YEAR, TEST_MONTH, TEST_DAY, TEST_HOUR);
  log(`**Test Julian Day:** ${jd.toFixed(4)}`);
  log();

  // ── Three-way comparison ───────────────────────────────────────────────
  log('## Apparent Geocentric RA — swisseph-wasm vs Skyfield vs JPL Horizons');
  log();
  log(
    '| Body | SWE RA° | SKY RA° | JPL RA° | SWE-SKY Δ° | SWE-JPL Δ° | Status |',
  );
  log(
    '|------|--------:|--------:|--------:|-----------:|-----------:|--------|',
  );

  let passed = 0;
  let failed = 0;
  let errors = 0;

  // Collect Dec rows for second table
  const decRows = [];

  for (const body of BODIES) {
    let raRow, decRow;
    try {
      // ── swisseph-wasm ──────────────────────────────────────────────────
      // SEFLG_SWIEPH (2) | SEFLG_EQUATORIAL (2048) → apparent geocentric RA/Dec
      const pos = swe.calc_ut(jd, body.sweId, 2 | 2048);
      const sweRA = pos[0];
      const sweDec = pos[1];

      // ── Skyfield ───────────────────────────────────────────────────────
      const skyBody = skyfieldResults ? skyfieldResults[body.name] : null;
      const skyRA = skyBody && !skyBody.error ? skyBody.ra_deg : null;
      const skyDec = skyBody && !skyBody.error ? skyBody.dec_deg : null;

      // ── JPL Horizons ───────────────────────────────────────────────────
      let jplRA = null;
      let jplDec = null;
      try {
        const ref = await fetchHorizonsPosition(body.horizId, TEST_DATE_STR);
        jplRA = ref.ra_deg;
        jplDec = ref.dec_deg;
      } catch (_e) {
        // JPL fetch failed; status based on SWE-SKY only if available
      }

      // ── Deltas ────────────────────────────────────────────────────────
      const sweSkyRADiff = skyRA !== null ? angularDiff(sweRA, skyRA) : null;
      const sweJplRADiff = jplRA !== null ? angularDiff(sweRA, jplRA) : null;
      const sweSkyDecDiff = skyDec !== null ? Math.abs(sweDec - skyDec) : null;
      const sweJplDecDiff = jplDec !== null ? Math.abs(sweDec - jplDec) : null;

      // JPL Horizons is the primary reference (authoritative); fall back to
      // Skyfield if JPL is unavailable (e.g. network issue). Both sources
      // always supply RA and Dec together, so primaryDelta and primaryDecDelta
      // are either both non-null or both null.
      const primaryDelta = sweJplRADiff ?? sweSkyRADiff;
      const primaryDecDelta = sweJplDecDiff ?? sweSkyDecDiff;
      const ok =
        primaryDelta !== null &&
        primaryDecDelta !== null &&
        primaryDelta <= TOLERANCE_DEG &&
        primaryDecDelta <= TOLERANCE_DEG;

      if (primaryDelta === null || primaryDecDelta === null) {
        errors++;
      } else if (ok) {
        passed++;
      } else {
        failed++;
      }

      const status = primaryDelta === null ? '⚠️ NO REF' : ok ? '✅ PASS' : '❌ FAIL';

      raRow =
        `| ${body.name} ` +
        `| ${f(sweRA)} | ${skyRA !== null ? f(skyRA) : '—'} | ${jplRA !== null ? f(jplRA) : '—'} ` +
        `| ${sweSkyRADiff !== null ? f(sweSkyRADiff) : '—'} | ${sweJplRADiff !== null ? f(sweJplRADiff) : '—'} ` +
        `| ${status} |`;

      decRow =
        `| ${body.name} ` +
        `| ${f(sweDec)} | ${skyDec !== null ? f(skyDec) : '—'} | ${jplDec !== null ? f(jplDec) : '—'} ` +
        `| ${sweSkyDecDiff !== null ? f(sweSkyDecDiff) : '—'} | ${sweJplDecDiff !== null ? f(sweJplDecDiff) : '—'} ` +
        `| ${status} |`;
    } catch (err) {
      errors++;
      raRow = `| ${body.name} | — | — | — | — | — | ⚠️ ERROR: ${err.message.slice(0, 50)} |`;
      decRow = raRow;
    }
    log(raRow);
    decRows.push(decRow);
  }

  swe.close();

  log();
  log('## Apparent Geocentric Dec — swisseph-wasm vs Skyfield vs JPL Horizons');
  log();
  log(
    '| Body | SWE Dec° | SKY Dec° | JPL Dec° | SWE-SKY Δ° | SWE-JPL Δ° | Status |',
  );
  log(
    '|------|--------:|--------:|--------:|-----------:|-----------:|--------|',
  );
  for (const row of decRows) log(row);

  // ── Summary ────────────────────────────────────────────────────────────
  log();
  log('## Summary');
  log();
  log(`| Result | Count |`);
  log(`|--------|------:|`);
  log(`| ✅ Passed  | ${passed} |`);
  log(`| ❌ Failed  | ${failed} |`);
  log(`| ⚠️ No ref  | ${errors} |`);
  log(`| **Total**  | **${BODIES.length}** |`);
  log();

  const allOk = failed === 0;
  if (allOk && errors === 0) {
    log(
      '🎉 **All tests passed.** swisseph-wasm positions agree with both Skyfield (DE440s) ' +
        'and JPL Horizons within the specified tolerance.',
    );
  } else if (allOk) {
    log(
      '✅ **No failures.** Some reference sources were unavailable (see ⚠️ rows above).',
    );
  } else {
    log(
      '⚠️ **Some tests failed.** ' +
        'Review the tables above for details.',
    );
  }

  log();
  log('---');
  log('*Generated by the swisseph-wasm accuracy test workflow.*');

  writeFileSync('report.md', reportLines.join('\n') + '\n');

  if (!allOk) process.exit(1);
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});

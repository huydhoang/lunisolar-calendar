/**
 * swisseph-wasm Accuracy Test
 *
 * Compares planetary positions calculated by swisseph-wasm against
 * reference data fetched from JPL Horizons (NASA/JPL) — the authoritative
 * source for high-precision solar system ephemerides.
 *
 * Reference: https://ssd.jpl.nasa.gov/horizons/
 */

import SwissEph from 'swisseph-wasm';
import { writeFileSync } from 'fs';

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
  log(`**Reference:** JPL Horizons (https://ssd.jpl.nasa.gov/horizons/)`);
  log(`**Package:** swisseph-wasm (npm install via bun)`);
  log(`**Tolerance:** ${TOLERANCE_DEG}° (${(TOLERANCE_DEG * 60).toFixed(0)} arcminutes)`);
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

  // ── Fetch reference data and compare ──────────────────────────────────
  log('## Apparent Geocentric RA / Dec — swisseph-wasm vs JPL Horizons');
  log();
  log(
    '| Body | JPL RA (°) | SWE RA (°) | RA Δ (°) | JPL Dec (°) | SWE Dec (°) | Dec Δ (°) | Status |',
  );
  log(
    '|------|----------:|----------:|---------:|------------:|------------:|----------:|--------|',
  );

  let passed = 0;
  let failed = 0;
  let errors = 0;

  for (const body of BODIES) {
    let row;
    try {
      const ref = await fetchHorizonsPosition(body.horizId, TEST_DATE_STR);

      // SEFLG_SWIEPH (2) | SEFLG_EQUATORIAL (2048) → apparent geocentric RA/Dec
      const pos = swe.calc_ut(jd, body.sweId, 2 | 2048);
      const sweRA = pos[0];
      const sweDec = pos[1];

      const raDiff = angularDiff(sweRA, ref.ra_deg);
      const decDiff = Math.abs(sweDec - ref.dec_deg);
      const ok = raDiff <= TOLERANCE_DEG && decDiff <= TOLERANCE_DEG;

      if (ok) passed++;
      else failed++;

      const status = ok ? '✅ PASS' : '❌ FAIL';
      row =
        `| ${body.name} ` +
        `| ${f(ref.ra_deg)} | ${f(sweRA)} | ${f(raDiff)} ` +
        `| ${f(ref.dec_deg)} | ${f(sweDec)} | ${f(decDiff)} ` +
        `| ${status} |`;
    } catch (err) {
      errors++;
      row = `| ${body.name} | — | — | — | — | — | — | ⚠️ ERROR: ${err.message.slice(0, 60)} |`;
    }
    log(row);
  }

  swe.close();

  // ── Summary ────────────────────────────────────────────────────────────
  log();
  log('## Summary');
  log();
  log(`| Result | Count |`);
  log(`|--------|------:|`);
  log(`| ✅ Passed  | ${passed} |`);
  log(`| ❌ Failed  | ${failed} |`);
  log(`| ⚠️ Errors  | ${errors} |`);
  log(`| **Total**  | **${BODIES.length}** |`);
  log();

  const allOk = failed === 0 && errors === 0;
  if (allOk) {
    log(
      '🎉 **All tests passed.** swisseph-wasm positions match JPL Horizons ' +
        'within the specified tolerance.',
    );
  } else {
    log(
      '⚠️ **Some tests failed or encountered errors.** ' +
        'Review the table above for details.',
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

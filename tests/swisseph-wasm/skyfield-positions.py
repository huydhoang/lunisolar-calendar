#!/usr/bin/env python3
"""
skyfield-positions.py

Calculate apparent geocentric RA/Dec (apparent, of-date) for major planets
at 2025-01-01 12:00 UTC using Skyfield with the DE440s JPL ephemeris.

Outputs results as JSON to skyfield-results.json for consumption by the
accuracy-test.mjs comparison script.

Reference:
  Skyfield: https://rhodesmill.org/skyfield/
  DE440s:   https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de440s.bsp
"""

import json
import sys
from skyfield.api import Loader

# ── Bodies to compute ────────────────────────────────────────────────────────
# de440s.bsp covers the solar system from 1849 to 2150 at reduced precision.
# Mars/outer planets are available only as barycenters in de440s.
BODIES = [
    ("Sun", "sun"),
    ("Moon", "moon"),
    ("Mercury", "mercury"),
    ("Venus", "venus"),
    ("Mars", "mars barycenter"),
    ("Jupiter", "jupiter barycenter"),
    ("Saturn", "saturn barycenter"),
]

# ── Test epoch ───────────────────────────────────────────────────────────────
TEST_YEAR, TEST_MONTH, TEST_DAY = 2025, 1, 1
TEST_HOUR, TEST_MINUTE, TEST_SECOND = 12, 0, 0

# ── Load ephemeris ───────────────────────────────────────────────────────────
# Loader('.') uses the current working directory as the cache.
# If de440s.bsp is not found, skyfield automatically downloads it from:
#   https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de440s.bsp
loader = Loader(".")
try:
    eph = loader("de440s.bsp")
except Exception as exc:
    print(f"ERROR: could not load de440s.bsp — {exc}", file=sys.stderr)
    sys.exit(1)

ts = loader.timescale()
t = ts.utc(TEST_YEAR, TEST_MONTH, TEST_DAY, TEST_HOUR, TEST_MINUTE, TEST_SECOND)

earth = eph["earth"]

# ── Calculate positions ──────────────────────────────────────────────────────
results = {}

for name, key in BODIES:
    try:
        # apparent() includes light-time correction, aberration, and nutation —
        # matching swisseph-wasm's default SEFLG_SWIEPH behaviour.
        # radec('date') returns apparent coordinates of date (not J2000).
        apparent = earth.at(t).observe(eph[key]).apparent()
        ra, dec, _ = apparent.radec("date")
        results[name] = {
            "ra_deg": ra.hours * 15.0,  # RA is measured in hours (0-24); × 15 converts to degrees (0-360)
            "dec_deg": dec.degrees,
        }
        print(f"  {name}: RA={ra.hours * 15.0:.4f}°  Dec={dec.degrees:.4f}°")
    except Exception as exc:
        results[name] = {"error": str(exc)}
        print(f"  {name}: ERROR — {exc}", file=sys.stderr)

# ── Write JSON output ────────────────────────────────────────────────────────
out_file = "skyfield-results.json"
with open(out_file, "w") as fh:
    json.dump(results, fh, indent=2)

print(f"\nSkyfield results written to {out_file}")

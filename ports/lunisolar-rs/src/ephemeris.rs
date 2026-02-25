//! Swiss Ephemeris based astronomical computation.
//!
//! Computes new moon timestamps and solar term timestamps using the
//! Swiss Ephemeris library (linked via the `swisseph-wasm` crate with
//! embedded `.se1` data files).

use swisseph_wasm::swe_bindings;

/// Bisection convergence threshold in Julian Days (~1 ms).
const BISECT_PRECISION_JD: f64 = 1e-8;

// ── Helpers ──────────────────────────────────────────────────────────────────

/// JD (UT) → Unix timestamp in seconds.
fn jd_to_unix_sec(jd: f64) -> f64 {
    (jd - 2440587.5) * 86400.0
}

/// Normalise an angle to the range (-180, +180].
fn norm180(mut a: f64) -> f64 {
    a = a % 360.0;
    if a > 180.0 {
        a -= 360.0;
    }
    if a <= -180.0 {
        a += 360.0;
    }
    a
}

/// Sun ecliptic longitude at JD (UT).
fn sun_lon(jd_ut: f64) -> f64 {
    let mut xx = [0.0f64; 6];
    let mut serr = [0i8; 256];
    unsafe {
        swe_bindings::swe_calc_ut(
            jd_ut,
            swe_bindings::SE_SUN,
            swe_bindings::SEFLG_SWIEPH | swe_bindings::SEFLG_SPEED,
            xx.as_mut_ptr(),
            serr.as_mut_ptr(),
        );
    }
    xx[0]
}

/// Moon ecliptic longitude at JD (UT).
fn moon_lon(jd_ut: f64) -> f64 {
    let mut xx = [0.0f64; 6];
    let mut serr = [0i8; 256];
    unsafe {
        swe_bindings::swe_calc_ut(
            jd_ut,
            swe_bindings::SE_MOON,
            swe_bindings::SEFLG_SWIEPH | swe_bindings::SEFLG_SPEED,
            xx.as_mut_ptr(),
            serr.as_mut_ptr(),
        );
    }
    xx[0]
}

/// Sun–Moon elongation normalised to (-180, +180].
fn elongation(jd_ut: f64) -> f64 {
    norm180(moon_lon(jd_ut) - sun_lon(jd_ut))
}

// ── New-moon finder ──────────────────────────────────────────────────────────

/// Bisect to find the JD where the elongation crosses zero
/// (negative → positive = new moon).
fn bisect_new_moon(mut jd_lo: f64, mut jd_hi: f64) -> f64 {
    let mut e_lo = elongation(jd_lo);
    for _ in 0..50 {
        let jd_mid = (jd_lo + jd_hi) * 0.5;
        let e_mid = elongation(jd_mid);
        if (e_lo < 0.0) == (e_mid < 0.0) {
            jd_lo = jd_mid;
            e_lo = e_mid;
        } else {
            jd_hi = jd_mid;
        }
        if jd_hi - jd_lo < BISECT_PRECISION_JD {
            break;
        }
    }
    (jd_lo + jd_hi) * 0.5
}

/// Compute new moon (Sun–Moon conjunction) timestamps for a year range.
///
/// Returns a vector of Unix timestamps in seconds.
pub fn compute_new_moons(start_year: i32, end_year: i32) -> Vec<f64> {
    let mut results = Vec::new();
    let mut jd =
        unsafe { swe_bindings::swe_julday(start_year, 1, 1, 0.0, swe_bindings::SE_GREG_CAL) };
    let jd_end =
        unsafe { swe_bindings::swe_julday(end_year + 1, 1, 1, 0.0, swe_bindings::SE_GREG_CAL) };
    let step = 1.0; // 1-day step
    let mut prev = elongation(jd);

    while jd < jd_end {
        let next_jd = jd + step;
        let curr = elongation(next_jd);

        // Elongation crosses zero from negative to positive → new moon
        if prev < 0.0 && curr >= 0.0 {
            let nm_jd = bisect_new_moon(jd, next_jd);
            results.push(jd_to_unix_sec(nm_jd));
        }

        prev = curr;
        jd = next_jd;
    }
    results
}

// ── Solar-term finder ────────────────────────────────────────────────────────

/// Bisect to find the JD where the Sun crosses `target_lon`.
fn bisect_sun_crossing(target: f64, mut jd_lo: f64, mut jd_hi: f64) -> f64 {
    let mut d_lo = norm180(sun_lon(jd_lo) - target);
    for _ in 0..50 {
        let jd_mid = (jd_lo + jd_hi) * 0.5;
        let d_mid = norm180(sun_lon(jd_mid) - target);
        if (d_lo < 0.0) == (d_mid < 0.0) {
            jd_lo = jd_mid;
            d_lo = d_mid;
        } else {
            jd_hi = jd_mid;
        }
        if jd_hi - jd_lo < BISECT_PRECISION_JD {
            break;
        }
    }
    (jd_lo + jd_hi) * 0.5
}

/// Compute all 24 solar term timestamps and indices for a year range.
///
/// Solar term index `i` corresponds to Sun ecliptic longitude = `i * 15°`.
/// Returns a vector of `(unix_timestamp_sec, term_index)` pairs.
pub fn compute_solar_terms(start_year: i32, end_year: i32) -> Vec<(f64, u32)> {
    let mut results = Vec::new();
    let mut jd =
        unsafe { swe_bindings::swe_julday(start_year, 1, 1, 0.0, swe_bindings::SE_GREG_CAL) };
    let jd_end =
        unsafe { swe_bindings::swe_julday(end_year + 1, 1, 1, 0.0, swe_bindings::SE_GREG_CAL) };
    let step = 1.0;
    let mut prev_sector = (sun_lon(jd) / 15.0).floor() as u32 % 24;

    while jd < jd_end {
        let next_jd = jd + step;
        let sl = sun_lon(next_jd);
        let curr_sector = (sl / 15.0).floor() as u32 % 24;

        if curr_sector != prev_sector {
            let target = (curr_sector * 15) as f64;
            let cross = bisect_sun_crossing(target, jd, next_jd);
            results.push((jd_to_unix_sec(cross), curr_sector));
        }

        prev_sector = curr_sector;
        jd = next_jd;
    }
    results
}

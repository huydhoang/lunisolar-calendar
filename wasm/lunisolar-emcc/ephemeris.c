/*
 * ephemeris.c — Swiss Ephemeris based astronomical computation
 *
 * Uses swe_calc_ut() to locate new moons (Sun–Moon conjunction) and
 * solar term crossings (Sun ecliptic longitude at multiples of 15°).
 *
 * Linked against the vendored Swiss Ephemeris C source in vendor/swisseph/
 * with .se1 data files embedded via Emscripten --embed-file.
 */

#include "ephemeris.h"
#include "swephexp.h"
#include <math.h>

/* Bisection convergence threshold in Julian Days (~1 ms). */
#define BISECT_PRECISION_JD 1e-8

/* ── Helpers ───────────────────────────────────────────────────────────────── */

/* JD (UT) → Unix timestamp in seconds */
static double jd_to_unix_sec(double jd) {
    return (jd - 2440587.5) * 86400.0;
}

/* Normalise an angle to the range (-180, +180]. */
static double norm180(double a) {
    a = fmod(a, 360.0);
    if (a > 180.0)  a -= 360.0;
    if (a <= -180.0) a += 360.0;
    return a;
}

/* Sun ecliptic longitude at JD (UT). */
static double sun_lon(double jd_ut) {
    double xx[6];
    char serr[256];
    swe_calc_ut(jd_ut, SE_SUN, SEFLG_SWIEPH | SEFLG_SPEED, xx, serr);
    return xx[0];
}

/* Moon ecliptic longitude at JD (UT). */
static double moon_lon(double jd_ut) {
    double xx[6];
    char serr[256];
    swe_calc_ut(jd_ut, SE_MOON, SEFLG_SWIEPH | SEFLG_SPEED, xx, serr);
    return xx[0];
}

/* Sun–Moon elongation normalised to (-180, +180]. */
static double elongation(double jd_ut) {
    return norm180(moon_lon(jd_ut) - sun_lon(jd_ut));
}

/* ── New-moon finder ───────────────────────────────────────────────────────── */

/*
 * Bisect to find the JD where the elongation crosses zero
 * (negative → positive = new moon).
 */
static double bisect_new_moon(double jd_lo, double jd_hi) {
    double e_lo = elongation(jd_lo);
    for (int i = 0; i < 50; i++) {
        double jd_mid = (jd_lo + jd_hi) * 0.5;
        double e_mid = elongation(jd_mid);
        if ((e_lo < 0.0) == (e_mid < 0.0))
            jd_lo = jd_mid, e_lo = e_mid;
        else
            jd_hi = jd_mid;
        if (jd_hi - jd_lo < BISECT_PRECISION_JD) break;
    }
    return (jd_lo + jd_hi) * 0.5;
}

int compute_new_moons(int start_year, int end_year,
                      double *out_ts, int max_count) {
    int count = 0;
    double jd     = swe_julday(start_year, 1, 1, 0.0, SE_GREG_CAL);
    double jd_end = swe_julday(end_year + 1, 1, 1, 0.0, SE_GREG_CAL);
    double step   = 1.0;                       /* 1-day step */
    double prev   = elongation(jd);

    while (jd < jd_end && count < max_count) {
        double next_jd = jd + step;
        double curr    = elongation(next_jd);

        /* Elongation crosses zero from negative to positive → new moon */
        if (prev < 0.0 && curr >= 0.0) {
            double nm_jd  = bisect_new_moon(jd, next_jd);
            out_ts[count] = jd_to_unix_sec(nm_jd);
            count++;
        }

        prev = curr;
        jd   = next_jd;
    }
    return count;
}

/* ── Solar-term finder ─────────────────────────────────────────────────────── */

/*
 * Bisect to find the JD where the Sun crosses target_lon.
 */
static double bisect_sun_crossing(double target, double jd_lo, double jd_hi) {
    double d_lo = norm180(sun_lon(jd_lo) - target);
    for (int i = 0; i < 50; i++) {
        double jd_mid = (jd_lo + jd_hi) * 0.5;
        double d_mid  = norm180(sun_lon(jd_mid) - target);
        if ((d_lo < 0.0) == (d_mid < 0.0))
            jd_lo = jd_mid, d_lo = d_mid;
        else
            jd_hi = jd_mid;
        if (jd_hi - jd_lo < BISECT_PRECISION_JD) break;
    }
    return (jd_lo + jd_hi) * 0.5;
}

int compute_solar_terms(int start_year, int end_year,
                        double *out_ts, unsigned *out_idx,
                        int max_count) {
    int count = 0;
    double jd     = swe_julday(start_year, 1, 1, 0.0, SE_GREG_CAL);
    double jd_end = swe_julday(end_year + 1, 1, 1, 0.0, SE_GREG_CAL);
    double step   = 1.0;
    unsigned prev_sector = (unsigned)floor(sun_lon(jd) / 15.0) % 24;

    while (jd < jd_end && count < max_count) {
        double next_jd = jd + step;
        double sl      = sun_lon(next_jd);
        unsigned curr_sector = (unsigned)floor(sl / 15.0) % 24;

        if (curr_sector != prev_sector) {
            double target  = curr_sector * 15.0;
            double cross   = bisect_sun_crossing(target, jd, next_jd);
            out_ts[count]  = jd_to_unix_sec(cross);
            out_idx[count] = curr_sector;
            count++;
        }

        prev_sector = curr_sector;
        jd = next_jd;
    }
    return count;
}

/* ── Init / close ──────────────────────────────────────────────────────────── */

void ephe_init(void) {
    /* Emscripten embeds the .se1 files under /ephe via --embed-file.
       Tell Swiss Ephemeris where to find them. */
    swe_set_ephe_path("/ephe");
}

void ephe_close(void) {
    swe_close();
}

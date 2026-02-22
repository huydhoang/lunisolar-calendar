/*
 * ephemeris.h — Swiss Ephemeris based astronomical computation
 *
 * Computes new moon timestamps and solar term timestamps using the
 * Swiss Ephemeris library with embedded .se1 data files.
 */

#ifndef EPHEMERIS_H
#define EPHEMERIS_H

/* Maximum capacity for computed results */
#define EPHE_MAX_NEW_MOONS   64
#define EPHE_MAX_SOLAR_TERMS 96

/*
 * Compute new moon (Sun–Moon conjunction) timestamps for a year range.
 *
 * out_timestamps_sec: output array of Unix timestamps in seconds (double).
 * max_count:          capacity of the output array.
 *
 * Returns the number of new moons found, or -1 on error.
 */
int compute_new_moons(int start_year, int end_year,
                      double *out_timestamps_sec, int max_count);

/*
 * Compute all 24 solar term timestamps and indices for a year range.
 *
 * Solar term index i corresponds to Sun ecliptic longitude = i * 15°.
 * Even indices (0, 2, 4, …, 22) are principal terms (zhong qi).
 *
 * out_timestamps_sec: output array of Unix timestamps in seconds.
 * out_indices:        output array of term indices (0–23).
 * max_count:          capacity of the output arrays.
 *
 * Returns the number of solar terms found, or -1 on error.
 */
int compute_solar_terms(int start_year, int end_year,
                        double *out_timestamps_sec,
                        unsigned *out_indices,
                        int max_count);

/* Initialise the Swiss Ephemeris (set ephemeris path for embedded data). */
void ephe_init(void);

/* Clean up Swiss Ephemeris state. */
void ephe_close(void);

#endif /* EPHEMERIS_H */

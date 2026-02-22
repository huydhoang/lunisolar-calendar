/*
 * Lunisolar calendar conversion — Emscripten C→WASM port.
 *
 * Mirrors the Rust wasm-bindgen implementation in ../lunisolar/src/lib.rs
 * so we can benchmark Emscripten vs wasm-pack compilation paths.
 *
 * Compiled with:
 *   emcc lunisolar.c -O3 -s WASM=1 -s MODULARIZE=1 ...
 *
 * Exposed function:
 *   from_solar_date(timestamp_ms, tz_offset_seconds,
 *                   new_moons_ptr, new_moons_count,
 *                   solar_terms_ts_ptr, solar_terms_idx_ptr,
 *                   solar_terms_count,
 *                   out_buf, out_buf_len)
 *
 *   Returns the number of bytes written to out_buf (a JSON string).
 */

#include <emscripten/emscripten.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* ── Constants ─────────────────────────────────────────────────────────────── */

static const char *HEAVENLY_STEMS[] = {
    "\xe7\x94\xb2", "\xe4\xb9\x99", "\xe4\xb8\x99", "\xe4\xb8\x81",
    "\xe6\x88\x8a", "\xe5\xb7\xb1", "\xe5\xba\x9a", "\xe8\xbe\x9b",
    "\xe5\xa3\xac", "\xe7\x99\xb8"};
/* 甲 乙 丙 丁 戊 己 庚 辛 壬 癸 */

static const char *EARTHLY_BRANCHES[] = {
    "\xe5\xad\x90", "\xe4\xb8\x91", "\xe5\xaf\x85", "\xe5\x8d\xaf",
    "\xe8\xbe\xb0", "\xe5\xb7\xb3", "\xe5\x8d\x88", "\xe6\x9c\xaa",
    "\xe7\x94\xb3", "\xe9\x85\x89", "\xe6\x88\x8c", "\xe4\xba\xa5"};
/* 子 丑 寅 卯 辰 巳 午 未 申 酉 戌 亥 */

/* ── Date-only helper ──────────────────────────────────────────────────────── */

typedef struct {
    int y;
    unsigned m;
    unsigned d;
} DateOnly;

static int date_only_compare(const DateOnly *a, const DateOnly *b) {
    if (a->y != b->y) return a->y - b->y;
    if (a->m != b->m) return (int)a->m - (int)b->m;
    return (int)a->d - (int)b->d;
}

static int within_cst_range(const DateOnly *target,
                            const DateOnly *start,
                            const DateOnly *end) {
    return date_only_compare(start, target) <= 0 &&
           date_only_compare(target, end) < 0;
}

/* ── Calendar algorithms (Howard Hinnant) ──────────────────────────────────── */

static void civil_from_days(long long days, int *y, unsigned *m, unsigned *d) {
    long long z = days + 719468;
    long long era = (z >= 0 ? z : z - 146096) / 146097;
    unsigned doe = (unsigned)(z - era * 146097);
    unsigned yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    long long yr = (long long)yoe + era * 400;
    unsigned doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    unsigned mp = (5 * doy + 2) / 153;
    *d = doy - (153 * mp + 2) / 5 + 1;
    *m = mp < 10 ? mp + 3 : mp - 9;
    *y = (int)((*m <= 2) ? yr + 1 : yr);
}

static long long days_from_civil(int y, unsigned m, unsigned d) {
    long long yr = (m <= 2) ? (long long)y - 1 : (long long)y;
    long long era = (yr >= 0 ? yr : yr - 399) / 400;
    unsigned yoe = (unsigned)(yr - era * 400);
    unsigned m_adj = m > 2 ? m - 3 : m + 9;
    unsigned doy = (153 * m_adj + 2) / 5 + d - 1;
    unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    return era * 146097 + (long long)doe - 719468;
}

/* ── Date-parts from UTC ms ────────────────────────────────────────────────── */

static void utc_ms_to_date_parts(double utc_ms, int offset_seconds,
                                 int *y, unsigned *m, unsigned *d,
                                 unsigned *hour, unsigned *minute,
                                 unsigned *second) {
    long long total_s = (long long)floor(utc_ms / 1000.0) + offset_seconds;
    long long day_epoch;
    unsigned tod;

    if (total_s >= 0) {
        day_epoch = total_s / 86400;
        tod = (unsigned)(total_s % 86400);
    } else {
        day_epoch = (total_s - 86399) / 86400;
        tod = (unsigned)(total_s - day_epoch * 86400);
    }

    *hour = tod / 3600;
    *minute = (tod % 3600) / 60;
    *second = tod % 60;
    civil_from_days(day_epoch, y, m, d);
}

static DateOnly cst_date_of(double utc_ms, int cst_offset) {
    DateOnly out;
    unsigned h, mn, s;
    utc_ms_to_date_parts(utc_ms, cst_offset, &out.y, &out.m, &out.d, &h, &mn, &s);
    return out;
}

/* ── Sexagenary cycle helpers ──────────────────────────────────────────────── */

static unsigned cycle_from_stem_branch(unsigned stem1, unsigned branch1) {
    unsigned s0 = stem1 - 1;
    unsigned b0 = branch1 - 1;
    for (unsigned c = 1; c <= 60; c++) {
        if ((c - 1) % 10 == s0 && (c - 1) % 12 == b0) return c;
    }
    return 1;
}

static void year_ganzhi(int lunar_year,
                        unsigned *stem_idx, unsigned *branch_idx,
                        unsigned *cycle) {
    int yc = ((lunar_year - 4) % 60) + 1;
    if (yc <= 0) yc += 60;
    *stem_idx = ((unsigned)(yc - 1)) % 10;
    *branch_idx = ((unsigned)(yc - 1)) % 12;
    *cycle = (unsigned)yc;
}

static void month_ganzhi(int lunar_year, unsigned lunar_month,
                         unsigned *stem_idx, unsigned *branch_idx,
                         unsigned *cycle) {
    unsigned ys, yb, yc;
    year_ganzhi(lunar_year, &ys, &yb, &yc);
    unsigned year_stem_idx1 = ys + 1; /* 1-based */
    unsigned first;
    switch (year_stem_idx1) {
    case 1: case 6:  first = 3; break;
    case 2: case 7:  first = 5; break;
    case 3: case 8:  first = 7; break;
    case 4: case 9:  first = 9; break;
    case 5: case 10: first = 1; break;
    default:         first = 3; break;
    }
    unsigned ms1 = ((first - 1 + (lunar_month - 1)) % 10) + 1;
    unsigned mb1 = (lunar_month + 2) % 12;
    if (mb1 == 0) mb1 = 12;

    *stem_idx = ms1 - 1;
    *branch_idx = mb1 - 1;
    *cycle = cycle_from_stem_branch(ms1, mb1);
}

static void day_ganzhi(double timestamp_ms, int tz_offset_seconds,
                       unsigned *stem_idx, unsigned *branch_idx,
                       unsigned *cycle) {
    /* Use the CST date of the moment for day counting
       (Chinese calendar convention: ganzhi is always CST-based). */
    long long ref_days = days_from_civil(4, 1, 31);
    long long total_s = (long long)floor(timestamp_ms / 1000.0) + tz_offset_seconds;
    long long day_from_epoch;
    if (total_s >= 0)
        day_from_epoch = total_s / 86400;
    else
        day_from_epoch = (total_s - 86399) / 86400;

    long long diff = day_from_epoch - ref_days;
    int dc = (int)(((diff % 60) + 60) % 60 + 1);
    *stem_idx = ((unsigned)(dc - 1)) % 10;
    *branch_idx = ((unsigned)(dc - 1)) % 12;
    *cycle = (unsigned)dc;
}

static void hour_ganzhi(double local_wall_ms, unsigned base_day_stem,
                        unsigned *stem_idx, unsigned *branch_idx,
                        unsigned *cycle) {
    long long total_s = (long long)floor(local_wall_ms / 1000.0);
    unsigned tod;
    if (total_s >= 0)
        tod = (unsigned)(total_s % 86400);
    else
        tod = (unsigned)(total_s - ((total_s - 86399) / 86400) * 86400);

    unsigned hour = tod / 3600;
    unsigned minute = (tod % 3600) / 60;
    double decimal = (double)hour + (double)minute / 60.0;

    unsigned bi0;
    if (decimal >= 23.0 || decimal < 1.0)
        bi0 = 0;
    else {
        bi0 = (unsigned)floor((decimal - 1.0) / 2.0) + 1;
        if (bi0 >= 12) bi0 = 11;
    }
    unsigned bi1 = bi0 + 1;

    unsigned day_stem = base_day_stem;
    if (hour >= 23)
        day_stem = (base_day_stem + 1) % 10;

    unsigned zi_stem0;
    switch (day_stem) {
    case 0: case 5: zi_stem0 = 0; break; /* 甲/己 */
    case 1: case 6: zi_stem0 = 2; break; /* 乙/庚 */
    case 2: case 7: zi_stem0 = 4; break; /* 丙/辛 */
    case 3: case 8: zi_stem0 = 6; break; /* 丁/壬 */
    case 4: case 9: zi_stem0 = 8; break; /* 戊/癸 */
    default:        zi_stem0 = 0; break;
    }
    unsigned hs0 = (zi_stem0 + (bi1 - 1)) % 10;
    *stem_idx = hs0;
    *branch_idx = bi1 - 1;
    *cycle = cycle_from_stem_branch(hs0 + 1, bi1);
}

/* ── Core structures ──────────────────────────────────────────────────────── */

typedef struct {
    double instant_utc_ms;
    DateOnly cst_date;
    unsigned term_index;
} PrincipalTerm;

typedef struct {
    double start_utc_ms;
    double end_utc_ms;
    DateOnly start_cst;
    DateOnly end_cst;
    int has_principal;
    int is_leap;
    unsigned month_number;
} MonthPeriod;

/* ── Main conversion ──────────────────────────────────────────────────────── */

/*
 * from_solar_date
 *
 * Parameters:
 *   timestamp_ms        – UTC timestamp in milliseconds
 *   tz_offset_seconds   – Timezone offset from UTC in seconds
 *   new_moons           – array of new moon timestamps in SECONDS (double)
 *   new_moons_count     – length of new_moons
 *   solar_terms_ts      – array of solar term timestamps in SECONDS (double)
 *   solar_terms_idx     – array of solar term indices (unsigned)
 *   solar_terms_count   – length of solar_terms arrays
 *   out_buf             – output buffer for JSON string
 *   out_buf_len         – size of out_buf
 *
 * Returns: number of bytes written to out_buf, or -1 on error.
 */
EMSCRIPTEN_KEEPALIVE
int from_solar_date(double timestamp_ms, int tz_offset_seconds,
                    const double *new_moons, int new_moons_count,
                    const double *solar_terms_ts,
                    const unsigned *solar_terms_idx,
                    int solar_terms_count,
                    char *out_buf, int out_buf_len) {

    const int cst_offset = 8 * 3600;

    /* Local year in user timezone */
    int local_year;
    {
        unsigned lm, ld, lh, lmin, ls;
        utc_ms_to_date_parts(timestamp_ms, tz_offset_seconds,
                             &local_year, &lm, &ld, &lh, &lmin, &ls);
    }

    /* Sort new moons (copy to ms, sort) */
    if (new_moons_count < 2) return -1;

    double *nm_ms = (double *)malloc(sizeof(double) * (size_t)new_moons_count);
    if (!nm_ms) return -1;
    for (int i = 0; i < new_moons_count; i++)
        nm_ms[i] = new_moons[i] * 1000.0;

    /* Simple insertion sort – data is nearly sorted */
    for (int i = 1; i < new_moons_count; i++) {
        double key = nm_ms[i];
        int j = i - 1;
        while (j >= 0 && nm_ms[j] > key) {
            nm_ms[j + 1] = nm_ms[j];
            j--;
        }
        nm_ms[j + 1] = key;
    }

    /* Build principal terms */
    int pt_cap = solar_terms_count;
    PrincipalTerm *pts = (PrincipalTerm *)malloc(sizeof(PrincipalTerm) * (size_t)pt_cap);
    if (!pts) { free(nm_ms); return -1; }
    int pt_count = 0;
    for (int i = 0; i < solar_terms_count; i++) {
        unsigned idx = solar_terms_idx[i];
        if (idx % 2 != 0) continue;
        double utc_ms = solar_terms_ts[i] * 1000.0;
        unsigned raw = (idx / 2) + 2;
        unsigned ti = raw > 12 ? raw - 12 : raw;
        pts[pt_count].instant_utc_ms = utc_ms;
        pts[pt_count].cst_date = cst_date_of(utc_ms, cst_offset);
        pts[pt_count].term_index = ti;
        pt_count++;
    }
    /* Sort pts by instant */
    for (int i = 1; i < pt_count; i++) {
        PrincipalTerm key = pts[i];
        int j = i - 1;
        while (j >= 0 && pts[j].instant_utc_ms > key.instant_utc_ms) {
            pts[j + 1] = pts[j];
            j--;
        }
        pts[j + 1] = key;
    }

    /* Build month periods */
    int periods_count = new_moons_count - 1;
    MonthPeriod *periods = (MonthPeriod *)malloc(sizeof(MonthPeriod) * (size_t)periods_count);
    if (!periods) { free(nm_ms); free(pts); return -1; }
    for (int i = 0; i < periods_count; i++) {
        periods[i].start_utc_ms = nm_ms[i];
        periods[i].end_utc_ms = nm_ms[i + 1];
        periods[i].start_cst = cst_date_of(nm_ms[i], cst_offset);
        periods[i].end_cst = cst_date_of(nm_ms[i + 1], cst_offset);
        periods[i].has_principal = 0;
        periods[i].is_leap = 0;
        periods[i].month_number = 0;
    }

    /* Tag principal terms */
    for (int t = 0; t < pt_count; t++) {
        for (int p = 0; p < periods_count; p++) {
            if (within_cst_range(&pts[t].cst_date,
                                 &periods[p].start_cst,
                                 &periods[p].end_cst)) {
                periods[p].has_principal = 1;
                break;
            }
        }
    }

    /* Find Z11 (Winter Solstice) */
    int z11_best = -1;
    for (int i = 0; i < pt_count; i++) {
        if (pts[i].term_index != 11) continue;
        int ty;
        unsigned tm, td, th, tmin, ts2;
        utc_ms_to_date_parts(pts[i].instant_utc_ms, 0, &ty, &tm, &td, &th, &tmin, &ts2);
        if (ty == local_year) { z11_best = i; break; }
        if (z11_best < 0) z11_best = i;
        else {
            int cy;
            unsigned c_month, c_day, c_hour, c_minute, c_second;
            utc_ms_to_date_parts(pts[z11_best].instant_utc_ms, 0, &cy, &c_month, &c_day, &c_hour, &c_minute, &c_second);
            if (abs(ty - local_year) < abs(cy - local_year))
                z11_best = i;
        }
    }
    if (z11_best < 0) { free(nm_ms); free(pts); free(periods); return -1; }

    double anchor_ms;
    if (timestamp_ms >= pts[z11_best].instant_utc_ms) {
        anchor_ms = pts[z11_best].instant_utc_ms;
    } else {
        /* Find previous year's Z11 */
        anchor_ms = pts[z11_best].instant_utc_ms;
        for (int i = 0; i < pt_count; i++) {
            if (pts[i].term_index != 11) continue;
            int ty;
            unsigned tm2, td2, th2, tmin2, ts3;
            utc_ms_to_date_parts(pts[i].instant_utc_ms, 0, &ty, &tm2, &td2, &th2, &tmin2, &ts3);
            if (ty == local_year - 1) { anchor_ms = pts[i].instant_utc_ms; break; }
        }
    }

    /* Find Zi month */
    int zi_index = -1;
    for (int i = 0; i < periods_count; i++) {
        if (periods[i].start_utc_ms <= anchor_ms && anchor_ms < periods[i].end_utc_ms) {
            zi_index = i;
            break;
        }
    }
    if (zi_index < 0) { free(nm_ms); free(pts); free(periods); return -1; }

    periods[zi_index].month_number = 11;
    periods[zi_index].is_leap = 0;

    /* Forward pass */
    unsigned current = 11;
    for (int i = zi_index + 1; i < periods_count; i++) {
        if (periods[i].has_principal) {
            current = (current % 12) + 1;
            periods[i].month_number = current;
            periods[i].is_leap = 0;
        } else {
            periods[i].month_number = current;
            periods[i].is_leap = 1;
        }
    }

    /* Backward pass */
    if (zi_index > 0) {
        current = 11;
        for (int i = zi_index - 1; i >= 0; i--) {
            current = current > 1 ? current - 1 : 12;
            if (periods[i].has_principal) {
                periods[i].month_number = current;
                periods[i].is_leap = 0;
            } else {
                periods[i].month_number = current;
                periods[i].is_leap = 1;
            }
        }
    }

    /* Find target period */
    DateOnly target_cst = cst_date_of(timestamp_ms, cst_offset);
    int target_idx = -1;
    for (int i = 0; i < periods_count; i++) {
        if (within_cst_range(&target_cst, &periods[i].start_cst, &periods[i].end_cst)) {
            target_idx = i;
            break;
        }
    }
    if (target_idx < 0) { free(nm_ms); free(pts); free(periods); return -1; }

    MonthPeriod *tp = &periods[target_idx];

    /* Lunar day */
    long long start_days = days_from_civil(tp->start_cst.y, tp->start_cst.m, tp->start_cst.d);
    long long tgt_days = days_from_civil(target_cst.y, target_cst.m, target_cst.d);
    int lunar_day_raw = (int)(tgt_days - start_days + 1);
    if (lunar_day_raw < 1) lunar_day_raw = 1;
    if (lunar_day_raw > 30) lunar_day_raw = 30;

    /* Lunar year */
    int period_start_utc_year;
    {
        unsigned pm, pd, ph, pmn, ps;
        utc_ms_to_date_parts(tp->start_utc_ms, 0, &period_start_utc_year, &pm, &pd, &ph, &pmn, &ps);
    }
    int lunar_year;
    if (tp->month_number >= 1 && tp->month_number <= 10)
        lunar_year = period_start_utc_year;
    else
        lunar_year = period_start_utc_year + 1;

    /* Wall time for ganzhi using the provided timezone offset */
    int wy;
    unsigned wm, wd, wh, wmin, ws;
    utc_ms_to_date_parts(timestamp_ms, tz_offset_seconds, &wy, &wm, &wd, &wh, &wmin, &ws);
    double wall_ms = (double)days_from_civil(wy, wm, wd) * 86400000.0
                   + (double)wh * 3600000.0
                   + (double)wmin * 60000.0
                   + (double)ws * 1000.0;

    /* Ganzhi (use provided timezone offset for day/hour ganzhi) */
    unsigned ys, yb, ycc;
    year_ganzhi(lunar_year, &ys, &yb, &ycc);

    unsigned ms, mb, mcc;
    month_ganzhi(lunar_year, tp->month_number, &ms, &mb, &mcc);

    unsigned ds, db, dcc;
    day_ganzhi(timestamp_ms, tz_offset_seconds, &ds, &db, &dcc);

    unsigned hs, hb, hcc;
    hour_ganzhi(wall_ms, ds, &hs, &hb, &hcc);

    /* Serialize to JSON */
    int n = snprintf(out_buf, (size_t)out_buf_len,
        "{\"lunarYear\":%d,\"lunarMonth\":%u,\"lunarDay\":%d,"
        "\"isLeapMonth\":%s,"
        "\"yearStem\":\"%s\",\"yearBranch\":\"%s\",\"yearCycle\":%u,"
        "\"monthStem\":\"%s\",\"monthBranch\":\"%s\",\"monthCycle\":%u,"
        "\"dayStem\":\"%s\",\"dayBranch\":\"%s\",\"dayCycle\":%u,"
        "\"hourStem\":\"%s\",\"hourBranch\":\"%s\",\"hourCycle\":%u}",
        lunar_year, tp->month_number, lunar_day_raw,
        tp->is_leap ? "true" : "false",
        HEAVENLY_STEMS[ys], EARTHLY_BRANCHES[yb], ycc,
        HEAVENLY_STEMS[ms], EARTHLY_BRANCHES[mb], mcc,
        HEAVENLY_STEMS[ds], EARTHLY_BRANCHES[db], dcc,
        HEAVENLY_STEMS[hs], EARTHLY_BRANCHES[hb], hcc);

    free(nm_ms);
    free(pts);
    free(periods);

    return n;
}

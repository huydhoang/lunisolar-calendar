use wasm_bindgen::prelude::*;
use serde::{Deserialize, Serialize};

pub mod bazi;
mod ephemeris;

// ── Constants ────────────────────────────────────────────────────────────────

const HEAVENLY_STEMS: [&str; 10] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];
const EARTHLY_BRANCHES: [&str; 12] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];

// Construction Stars (十二建星)
const CONSTRUCTION_STARS: [&str; 12] = ["建", "除", "满", "平", "定", "执", "破", "危", "成", "收", "开", "闭"];
// Building branch for each lunar month (index 0 unused; 1..12)
const BUILDING_BRANCH: [usize; 13] = [
    0, // placeholder for index 0
    2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1,
    // month 1→寅(2), 2→卯(3), ..., 11→子(0), 12→丑(1)
];

// Great Yellow Path (大黄道) spirit names and Azure Dragon monthly start branch indices
const GYP_SPIRITS: [&str; 12] = ["青龙", "明堂", "天刑", "朱雀", "金匮", "天德", "白虎", "玉堂", "天牢", "玄武", "司命", "勾陈"];
const GYP_AUSPICIOUS: [bool; 12] = [true, true, false, false, true, true, false, true, false, false, true, false];
// Azure Dragon start branch index by lunar month (index 0 unused; 1..12)
const AZURE_START: [usize; 13] = [
    0, // placeholder
    0, 2, 4, 6, 8, 10, 0, 2, 4, 6, 8, 10,
    // month 1→子(0), 2→寅(2), ..., 7→子(0), 8→寅(2), ...
];

// ── Date helpers ─────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy)]
struct DateOnly {
    y: i32,
    m: u32,
    d: u32,
}

fn date_only_compare(a: &DateOnly, b: &DateOnly) -> i64 {
    if a.y != b.y { return (a.y - b.y) as i64; }
    if a.m != b.m { return (a.m as i64) - (b.m as i64); }
    (a.d as i64) - (b.d as i64)
}

fn within_cst_range(target: &DateOnly, start: &DateOnly, end: &DateOnly) -> bool {
    date_only_compare(start, target) <= 0 && date_only_compare(target, end) < 0
}

/// Convert a UTC timestamp (milliseconds) to date parts with a fixed offset (seconds).
fn utc_ms_to_date_parts(utc_ms: f64, offset_seconds: i32) -> (i32, u32, u32, u32, u32, u32) {
    let total_s = (utc_ms / 1000.0).floor() as i64 + offset_seconds as i64;
    let days_from_epoch = total_s.div_euclid(86400);
    let time_of_day = total_s.rem_euclid(86400) as u32;

    let hour = time_of_day / 3600;
    let minute = (time_of_day % 3600) / 60;
    let second = time_of_day % 60;

    // Convert days from Unix epoch (1970-01-01) to y/m/d
    // Using a civil calendar algorithm
    let (y, m, d) = civil_from_days(days_from_epoch);
    (y, m, d, hour, minute, second)
}

/// Convert days since Unix epoch to (year, month, day).
/// Algorithm from Howard Hinnant's chrono-compatible date algorithms.
fn civil_from_days(days: i64) -> (i32, u32, u32) {
    let z = days + 719468;
    let era = if z >= 0 { z } else { z - 146096 } / 146097;
    let doe = (z - era * 146097) as u32; // day of era [0, 146096]
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    let y = yoe as i64 + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = if m <= 2 { y + 1 } else { y };
    (y as i32, m, d)
}

/// Convert (year, month, day) to days since Unix epoch.
fn days_from_civil(y: i32, m: u32, d: u32) -> i64 {
    let y = if m <= 2 { y as i64 - 1 } else { y as i64 };
    let era = if y >= 0 { y } else { y - 399 } / 400;
    let yoe = (y - era * 400) as u32;
    let m_adj = if m > 2 { m - 3 } else { m + 9 };
    let doy = (153 * m_adj + 2) / 5 + d - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    era * 146097 + doe as i64 - 719468
}

fn cst_date_of(utc_ms: f64, offset_seconds: i32) -> DateOnly {
    let (y, m, d, _, _, _) = utc_ms_to_date_parts(utc_ms, offset_seconds);
    DateOnly { y, m, d }
}

// ── Sexagenary cycle helpers ─────────────────────────────────────────────────

fn cycle_from_stem_branch(stem_idx1: usize, branch_idx1: usize) -> usize {
    let stem0 = stem_idx1 - 1;
    let branch0 = branch_idx1 - 1;
    for cycle in 1..=60 {
        let s = (cycle - 1) % 10;
        let b = (cycle - 1) % 12;
        if s == stem0 && b == branch0 {
            return cycle;
        }
    }
    1
}

fn year_ganzhi(lunar_year: i32) -> (&'static str, &'static str, usize) {
    let mut year_cycle = ((lunar_year - 4) % 60) + 1;
    if year_cycle <= 0 { year_cycle += 60; }
    let stem = HEAVENLY_STEMS[((year_cycle - 1) % 10) as usize];
    let branch = EARTHLY_BRANCHES[((year_cycle - 1) % 12) as usize];
    (stem, branch, year_cycle as usize)
}

fn month_ganzhi(lunar_year: i32, lunar_month: u32) -> (&'static str, &'static str, usize) {
    let (year_stem, _, _) = year_ganzhi(lunar_year);
    let year_stem_idx = HEAVENLY_STEMS.iter().position(|&s| s == year_stem).unwrap() + 1;

    let first_month_stem_idx: usize = match year_stem_idx {
        1 | 6 => 3,
        2 | 7 => 5,
        3 | 8 => 7,
        4 | 9 => 9,
        5 | 10 => 1,
        _ => 3,
    };

    let month_stem_idx = ((first_month_stem_idx - 1 + (lunar_month as usize - 1)) % 10) + 1;
    let mut month_branch_idx = ((lunar_month as usize + 2) % 12) as usize;
    if month_branch_idx == 0 { month_branch_idx = 12; }

    let stem_char = HEAVENLY_STEMS[month_stem_idx - 1];
    let branch_char = EARTHLY_BRANCHES[month_branch_idx - 1];
    let month_cycle = cycle_from_stem_branch(month_stem_idx, month_branch_idx);
    (stem_char, branch_char, month_cycle)
}

fn day_ganzhi(timestamp_ms: f64) -> (&'static str, &'static str, usize) {
    // Anchor: 4 AD-01-31 is Jiazi day (cycle 1)
    let ref_days = days_from_civil(4, 1, 31);

    // Use local wall-clock date for day counting (day boundary at local midnight).
    let total_s = (timestamp_ms / 1000.0).floor() as i64;
    let day_from_epoch = total_s.div_euclid(86400);

    let days = day_from_epoch - ref_days;
    let day_cycle = (((days % 60) + 60) % 60 + 1) as usize;
    let stem = HEAVENLY_STEMS[(day_cycle - 1) % 10];
    let branch = EARTHLY_BRANCHES[(day_cycle - 1) % 12];
    (stem, branch, day_cycle)
}

fn hour_ganzhi(local_date_utc_ms: f64, base_day_stem: &str) -> (&'static str, &'static str, usize) {
    let total_s = (local_date_utc_ms / 1000.0).floor() as i64;
    let time_of_day = total_s.rem_euclid(86400) as u32;
    let hour = time_of_day / 3600;
    let minute = (time_of_day % 3600) / 60;

    let decimal = hour as f64 + minute as f64 / 60.0;
    let branch_index0: usize = if decimal >= 23.0 || decimal < 1.0 {
        0 // Zi
    } else {
        let idx = ((decimal - 1.0) / 2.0).floor() as usize + 1;
        if idx >= 12 { 11 } else { idx }
    };

    let branch_idx1 = branch_index0 + 1;

    let day_stem_for_hour = if hour >= 23 {
        let day_stem_idx = HEAVENLY_STEMS.iter().position(|&s| s == base_day_stem).unwrap();
        HEAVENLY_STEMS[(day_stem_idx + 1) % 10]
    } else {
        base_day_stem
    };

    let zi_stem_index0: usize = match day_stem_for_hour {
        "甲" | "己" => 0,
        "乙" | "庚" => 2,
        "丙" | "辛" => 4,
        "丁" | "壬" => 6,
        "戊" | "癸" => 8,
        _ => 0,
    };

    let hour_stem_index0 = (zi_stem_index0 + (branch_idx1 - 1)) % 10;
    let stem_char = HEAVENLY_STEMS[hour_stem_index0];
    let branch_char = EARTHLY_BRANCHES[branch_idx1 - 1];
    let cycle = cycle_from_stem_branch(hour_stem_index0 + 1, branch_idx1);
    (stem_char, branch_char, cycle)
}

// ── Huangdao helpers ──────────────────────────────────────────────────────────

/// Construction Star (十二建星) base calculation from lunar month and day branch index.
fn construction_star(lunar_month: u32, day_branch_idx: usize) -> &'static str {
    let building = BUILDING_BRANCH[lunar_month as usize];
    // Double modulo to handle negative differences correctly
    let star_idx = ((day_branch_idx as isize - building as isize) % 12 + 12) % 12;
    CONSTRUCTION_STARS[star_idx as usize]
}

/// Great Yellow Path spirit from lunar month and day branch index.
fn gyp_spirit(lunar_month: u32, day_branch_idx: usize) -> (&'static str, bool) {
    let start = AZURE_START[lunar_month as usize];
    // Double modulo to handle negative differences correctly
    let idx = ((day_branch_idx as isize - start as isize) % 12 + 12) % 12;
    (GYP_SPIRITS[idx as usize], GYP_AUSPICIOUS[idx as usize])
}

// ── Core structures ──────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
struct PrincipalTerm {
    instant_utc_ms: f64,
    cst_date: DateOnly,
    term_index: u32,
}

#[derive(Debug, Clone)]
struct MonthPeriod {
    start_utc_ms: f64,
    end_utc_ms: f64,
    start_cst: DateOnly,
    end_cst: DateOnly,
    has_principal: bool,
    is_leap: bool,
    month_number: u32,
}

// ── Output type ──────────────────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LunisolarResult {
    pub lunar_year: i32,
    pub lunar_month: u32,
    pub lunar_day: u32,
    pub is_leap_month: bool,
    pub year_stem: String,
    pub year_branch: String,
    pub year_cycle: usize,
    pub month_stem: String,
    pub month_branch: String,
    pub month_cycle: usize,
    pub day_stem: String,
    pub day_branch: String,
    pub day_cycle: usize,
    pub hour_stem: String,
    pub hour_branch: String,
    pub hour_cycle: usize,
    pub construction_star: String,
    pub gyp_spirit: String,
    pub gyp_path_type: String,
}

// ── Main conversion function ─────────────────────────────────────────────────

/// Core conversion: given a UTC timestamp (ms), timezone offset (seconds),
/// pre-loaded new moon timestamps (seconds), and solar term pairs ([ts_sec, idx]),
/// compute the lunisolar calendar date.
fn from_solar_date_core(
    timestamp_ms: f64,
    tz_offset_seconds: i32,
    new_moon_timestamps: &[f64],
    solar_term_pairs: &[(f64, u32)],
) -> Result<LunisolarResult, String> {
    let cst_offset = tz_offset_seconds; // Use the caller-provided timezone offset

    // Local date parts in user timezone
    let (local_year, _local_month, _local_day, _lh, _lm, _ls) =
        utc_ms_to_date_parts(timestamp_ms, tz_offset_seconds);

    // Build new moon Date list (as UTC ms)
    let mut new_moons: Vec<f64> = new_moon_timestamps.iter().map(|ts| ts * 1000.0).collect();
    new_moons.sort_by(|a, b| a.partial_cmp(b).unwrap());

    // Build principal terms (even-indexed solar terms)
    let mut principal_terms: Vec<PrincipalTerm> = solar_term_pairs
        .iter()
        .filter(|(_, idx)| idx % 2 == 0)
        .map(|(ts, idx)| {
            let utc_ms = ts * 1000.0;
            // Map even-indexed solar terms to principal term numbers (Z1..Z12):
            // idx 0→Z2, 2→Z3, ..., 18→Z11 (Winter Solstice), 20→Z12, 22→Z1
            let term_index_raw = (idx / 2) + 2;
            let term_index = if term_index_raw > 12 { term_index_raw - 12 } else { term_index_raw };
            let cst_date = cst_date_of(utc_ms, cst_offset);
            PrincipalTerm { instant_utc_ms: utc_ms, cst_date, term_index }
        })
        .collect();
    principal_terms.sort_by(|a, b| a.instant_utc_ms.partial_cmp(&b.instant_utc_ms).unwrap());

    if new_moons.len() < 2 {
        return Err("Insufficient new moon data".to_string());
    }

    // Build month periods
    let mut periods: Vec<MonthPeriod> = Vec::new();
    for i in 0..new_moons.len() - 1 {
        let start_utc_ms = new_moons[i];
        let end_utc_ms = new_moons[i + 1];
        let start_cst = cst_date_of(start_utc_ms, cst_offset);
        let end_cst = cst_date_of(end_utc_ms, cst_offset);
        periods.push(MonthPeriod {
            start_utc_ms,
            end_utc_ms,
            start_cst,
            end_cst,
            has_principal: false,
            is_leap: false,
            month_number: 0,
        });
    }

    // Tag principal terms into periods
    for term in &principal_terms {
        for period in periods.iter_mut() {
            if within_cst_range(&term.cst_date, &period.start_cst, &period.end_cst) {
                period.has_principal = true;
                break;
            }
        }
    }

    // Find Winter Solstice (Z11) terms
    let z11: Vec<&PrincipalTerm> = principal_terms.iter().filter(|t| t.term_index == 11).collect();
    if z11.is_empty() {
        return Err("No Winter Solstice (Z11) term found".to_string());
    }

    let target_year = local_year;
    let current_year_z11 = z11.iter()
        .find(|t| {
            let (y, _, _, _, _, _) = utc_ms_to_date_parts(t.instant_utc_ms, 0);
            y == target_year
        })
        .or_else(|| {
            z11.iter().min_by_key(|t| {
                let (y, _, _, _, _, _) = utc_ms_to_date_parts(t.instant_utc_ms, 0);
                (y - target_year).unsigned_abs()
            })
        })
        .unwrap();

    let anchor_solstice_ms = if timestamp_ms >= current_year_z11.instant_utc_ms {
        current_year_z11.instant_utc_ms
    } else {
        z11.iter()
            .find(|t| {
                let (y, _, _, _, _, _) = utc_ms_to_date_parts(t.instant_utc_ms, 0);
                y == target_year - 1
            })
            .map(|t| t.instant_utc_ms)
            .unwrap_or(current_year_z11.instant_utc_ms)
    };

    // Find Zi month (contains Winter Solstice)
    let zi_index = periods.iter().position(|p| {
        p.start_utc_ms <= anchor_solstice_ms && anchor_solstice_ms < p.end_utc_ms
    }).ok_or("Failed to locate Zi-month containing Winter Solstice")?;

    periods[zi_index].month_number = 11;
    periods[zi_index].is_leap = false;

    // Forward pass
    let mut current = 11u32;
    for i in (zi_index + 1)..periods.len() {
        if periods[i].has_principal {
            current = (current % 12) + 1;
            periods[i].month_number = current;
            periods[i].is_leap = false;
        } else {
            periods[i].month_number = current;
            periods[i].is_leap = true;
        }
    }

    // Backward pass
    if zi_index > 0 {
        current = 11;
        for i in (0..zi_index).rev() {
            current = if current > 1 { current - 1 } else { 12 };
            if periods[i].has_principal {
                periods[i].month_number = current;
                periods[i].is_leap = false;
            } else {
                periods[i].month_number = current;
                periods[i].is_leap = true;
            }
        }
    }

    // Find target period by CST date-only comparison
    let target_cst = cst_date_of(timestamp_ms, cst_offset);
    let target_period = periods.iter().find(|p| {
        within_cst_range(&target_cst, &p.start_cst, &p.end_cst)
    }).ok_or("No lunar month period found for target date")?;

    // Lunar day
    let start_days = days_from_civil(target_period.start_cst.y, target_period.start_cst.m, target_period.start_cst.d);
    let tgt_days = days_from_civil(target_cst.y, target_cst.m, target_cst.d);
    let lunar_day_raw = (tgt_days - start_days + 1) as u32;
    let lunar_day = lunar_day_raw.max(1).min(30);

    // Lunar year
    let period_start_utc_year = {
        let (y, _, _, _, _, _) = utc_ms_to_date_parts(target_period.start_utc_ms, 0);
        y
    };
    // Lunar year determination (mirrors Python logic):
    // Months 1-11 belong to the same Gregorian year as the period start.
    // Month 12 may start in Dec (same year) or Jan/Feb (next Gregorian year),
    // so subtract 1 when the period starts in Jan/Feb.
    let period_start_utc_month = {
        let (_, m, _, _, _, _) = utc_ms_to_date_parts(target_period.start_utc_ms, 0);
        m
    };
    let lunar_year = if target_period.month_number <= 11 {
        period_start_utc_year
    } else if period_start_utc_month <= 2 {
        period_start_utc_year - 1
    } else {
        period_start_utc_year
    };

    // Wall time for ganzhi using the provided timezone offset
    let (wy, wm, wd, wh, wmin, ws) = utc_ms_to_date_parts(timestamp_ms, tz_offset_seconds);
    let wall_ms = days_from_civil(wy, wm, wd) as f64 * 86400000.0
        + wh as f64 * 3600000.0
        + wmin as f64 * 60000.0
        + ws as f64 * 1000.0;

    // Sexagenary cycles (use local wall time for day ganzhi so day boundary is at local midnight)
    let (y_stem, y_branch, y_cycle) = year_ganzhi(lunar_year);
    let (m_stem, m_branch, m_cycle) = month_ganzhi(lunar_year, target_period.month_number);
    let (d_stem, d_branch, d_cycle) = day_ganzhi(wall_ms);
    let (h_stem, h_branch, h_cycle) = hour_ganzhi(wall_ms, d_stem);

    // Huangdao: Construction Star + Great Yellow Path
    let day_branch_idx = EARTHLY_BRANCHES.iter().position(|&b| b == d_branch)
        .expect("day_ganzhi returned an invalid branch character");
    let cs = construction_star(target_period.month_number, day_branch_idx);
    let (spirit, spirit_auspicious) = gyp_spirit(target_period.month_number, day_branch_idx);

    Ok(LunisolarResult {
        lunar_year,
        lunar_month: target_period.month_number,
        lunar_day,
        is_leap_month: target_period.is_leap,
        year_stem: y_stem.to_string(),
        year_branch: y_branch.to_string(),
        year_cycle: y_cycle,
        month_stem: m_stem.to_string(),
        month_branch: m_branch.to_string(),
        month_cycle: m_cycle,
        day_stem: d_stem.to_string(),
        day_branch: d_branch.to_string(),
        day_cycle: d_cycle,
        hour_stem: h_stem.to_string(),
        hour_branch: h_branch.to_string(),
        hour_cycle: h_cycle,
        construction_star: cs.to_string(),
        gyp_spirit: spirit.to_string(),
        gyp_path_type: if spirit_auspicious { "黄道".to_string() } else { "黑道".to_string() },
    })
}

// ── WASM-exported function ───────────────────────────────────────────────────

/// Calculate lunisolar date from a UTC timestamp.
///
/// # Arguments
/// * `timestamp_ms` - UTC timestamp in milliseconds
/// * `tz_offset_seconds` - Timezone offset from UTC in seconds (e.g., 28800 for CST/UTC+8)
/// * `new_moons_json` - JSON string: array of new moon Unix timestamps in seconds
/// * `solar_terms_json` - JSON string: array of [timestamp_seconds, term_index] pairs
///
/// # Returns
/// JSON string with lunisolar date result
#[wasm_bindgen(js_name = "fromSolarDate")]
pub fn from_solar_date(
    timestamp_ms: f64,
    tz_offset_seconds: i32,
    new_moons_json: &str,
    solar_terms_json: &str,
) -> Result<String, JsError> {
    let new_moons: Vec<f64> = serde_json::from_str(new_moons_json)
        .map_err(|e| JsError::new(&format!("Failed to parse new_moons JSON: {}", e)))?;

    let solar_terms: Vec<(f64, u32)> = serde_json::from_str(solar_terms_json)
        .map_err(|e| JsError::new(&format!("Failed to parse solar_terms JSON: {}", e)))?;

    let result = from_solar_date_core(timestamp_ms, tz_offset_seconds, &new_moons, &solar_terms)
        .map_err(|e| JsError::new(&e))?;

    serde_json::to_string(&result)
        .map_err(|e| JsError::new(&format!("Failed to serialize result: {}", e)))
}

/// Standalone lunisolar date conversion using the Swiss Ephemeris.
///
/// Computes new moons and solar terms internally using embedded `.se1`
/// ephemeris data — no pre-computed data needed from the caller.
///
/// # Arguments
/// * `timestamp_ms` - UTC timestamp in milliseconds
/// * `tz_offset_seconds` - Timezone offset from UTC in seconds (e.g., 28800 for CST/UTC+8)
///
/// # Returns
/// JSON string with lunisolar date result
#[wasm_bindgen(js_name = "fromSolarDateAuto")]
pub fn from_solar_date_auto(
    timestamp_ms: f64,
    tz_offset_seconds: i32,
) -> Result<String, JsError> {
    // Determine which years of data we need
    let (local_year, _, _, _, _, _) = utc_ms_to_date_parts(timestamp_ms, tz_offset_seconds);
    let start_year = local_year - 1;
    let end_year = local_year + 1;

    // Compute new moons and solar terms via Swiss Ephemeris
    let new_moons = ephemeris::compute_new_moons(start_year, end_year);
    let solar_terms = ephemeris::compute_solar_terms(start_year, end_year);

    if new_moons.len() < 2 {
        return Err(JsError::new("Insufficient new moon data from Swiss Ephemeris"));
    }
    if solar_terms.is_empty() {
        return Err(JsError::new("No solar terms computed from Swiss Ephemeris"));
    }

    let result = from_solar_date_core(timestamp_ms, tz_offset_seconds, &new_moons, &solar_terms)
        .map_err(|e| JsError::new(&e))?;

    serde_json::to_string(&result)
        .map_err(|e| JsError::new(&format!("Failed to serialize result: {}", e)))
}

// ── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_civil_from_days() {
        // 1970-01-01 = day 0
        assert_eq!(civil_from_days(0), (1970, 1, 1));
        // 2025-01-01
        assert_eq!(civil_from_days(20089), (2025, 1, 1));
    }

    #[test]
    fn test_days_from_civil() {
        assert_eq!(days_from_civil(1970, 1, 1), 0);
        assert_eq!(days_from_civil(2025, 1, 1), 20089);
    }

    #[test]
    fn test_year_ganzhi() {
        // 2025 is 乙巳 year
        let (stem, branch, _) = year_ganzhi(2025);
        assert_eq!(stem, "乙");
        assert_eq!(branch, "巳");
    }

    #[test]
    fn test_day_ganzhi_reference() {
        // 4 AD-01-31 should be Jiazi (cycle 1) — anchor day for sexagenary cycle
        let ref_ms = days_from_civil(4, 1, 31) as f64 * 86400000.0;
        let (stem, branch, cycle) = day_ganzhi(ref_ms);
        assert_eq!(stem, "甲");
        assert_eq!(branch, "子");
        assert_eq!(cycle, 1);
    }

    #[test]
    fn test_utc_ms_to_date_parts() {
        // 2025-06-21 12:00:00 UTC
        let ms = 1750507200000.0;
        let (y, m, d, h, min, s) = utc_ms_to_date_parts(ms, 0);
        assert_eq!((y, m, d, h, min, s), (2025, 6, 21, 12, 0, 0));

        // Same timestamp in CST (UTC+8)
        let (y, m, d, h, min, s) = utc_ms_to_date_parts(ms, 28800);
        assert_eq!((y, m, d, h, min, s), (2025, 6, 21, 20, 0, 0));
    }

    #[test]
    fn test_construction_star() {
        // Lunar month 5, day branch 酉(9) → building branch 午(6)
        // star_idx = (9 - 6) % 12 = 3 → "平"
        assert_eq!(construction_star(5, 9), "平");
        // Lunar month 1, day branch 寅(2) → building branch 寅(2)
        // star_idx = (2 - 2) % 12 = 0 → "建"
        assert_eq!(construction_star(1, 2), "建");
    }

    #[test]
    fn test_gyp_spirit() {
        // Lunar month 5, day branch 酉(9) → Azure start 申(8)
        // spirit_idx = (9 - 8) % 12 = 1 → "明堂" (auspicious)
        let (spirit, auspicious) = gyp_spirit(5, 9);
        assert_eq!(spirit, "明堂");
        assert!(auspicious);
        // Lunar month 8, day branch 戌(10) → Azure start 寅(2)
        // spirit_idx = (10 - 2) % 12 = 8 → "天牢" (not auspicious)
        let (spirit, auspicious) = gyp_spirit(8, 10);
        assert_eq!(spirit, "天牢");
        assert!(!auspicious);
    }
}

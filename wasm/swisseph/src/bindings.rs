use core::ffi::{c_int, c_double, c_char};

#[link(name = "swe")]
unsafe extern "C" {
    #[link_name = "impl_swe_version"]
    pub fn swe_version(s: *mut c_char) -> *mut c_char;

    #[link_name = "impl_swe_julday"]
    pub fn swe_julday(year: c_int, month: c_int, day: c_int, hour: c_double, gregflag: c_int) -> c_double;

    #[link_name = "impl_swe_revjul"]
    pub fn swe_revjul(tjd: c_double, gregflag: c_int, year: *mut c_int, month: *mut c_int, day: *mut c_int, hour: *mut c_double);

    #[link_name = "impl_swe_calc_ut"]
    pub fn swe_calc_ut(tjd_ut: c_double, ipl: c_int, iflag: c_int, xx: *mut c_double, serr: *mut c_char) -> c_int;

    #[link_name = "impl_swe_set_sid_mode"]
    pub fn swe_set_sid_mode(sid_mode: c_int, t0: c_double, ayan_t0: c_double);

    #[link_name = "impl_swe_get_ayanamsa_ut"]
    pub fn swe_get_ayanamsa_ut(tjd_ut: c_double) -> c_double;

    #[link_name = "impl_swe_get_planet_name"]
    pub fn swe_get_planet_name(ipl: c_int, spname: *mut c_char) -> *mut c_char;
}

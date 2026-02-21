extern crate alloc;

use wasm_bindgen::prelude::*;
use core::ffi::CStr;
use js_sys::{Object, Reflect};

pub mod bindings;

pub mod swe_bindings {
    pub use crate::bindings::*;

    pub const SE_SUN: i32 = 0;
    pub const SE_MOON: i32 = 1;
    pub const SE_GREG_CAL: i32 = 1;
    pub const SEFLG_SWIEPH: i32 = 2;
    pub const SEFLG_SPEED: i32 = 256;
}

// --- WASM exports ---

#[wasm_bindgen(js_name = swe_calc_ut)]
pub fn js_swe_calc_ut(tjd_ut: f64, ipl: i32, iflag: i32) -> Result<JsValue, JsValue> {
    let mut xx = [0.0f64; 6];
    let mut serr = [0i8; 256];

    let ret = unsafe {
        swe_bindings::swe_calc_ut(tjd_ut, ipl, iflag, xx.as_mut_ptr(), serr.as_mut_ptr())
    };

    if ret < 0 {
        let msg = unsafe {
            CStr::from_ptr(serr.as_ptr()).to_str().unwrap_or("unknown error")
        };
        return Err(JsValue::from_str(msg));
    }

    let obj = Object::new();
    Reflect::set(&obj, &"longitude".into(), &xx[0].into())?;
    Reflect::set(&obj, &"latitude".into(), &xx[1].into())?;
    Reflect::set(&obj, &"distance".into(), &xx[2].into())?;
    Reflect::set(&obj, &"speed_long".into(), &xx[3].into())?;
    Reflect::set(&obj, &"speed_lat".into(), &xx[4].into())?;
    Reflect::set(&obj, &"speed_dist".into(), &xx[5].into())?;
    Reflect::set(&obj, &"rc_flags".into(), &ret.into())?;

    Ok(obj.into())
}

#[wasm_bindgen(js_name = swe_julday)]
pub fn js_swe_julday(year: i32, month: i32, day: i32, hour: f64, gregflag: i32) -> f64 {
    unsafe { swe_bindings::swe_julday(year, month, day, hour, gregflag) }
}

#[wasm_bindgen(js_name = swe_revjul)]
pub fn js_swe_revjul(tjd: f64, gregflag: i32) -> JsValue {
    let mut year = 0i32;
    let mut month = 0i32;
    let mut day = 0i32;
    let mut hour = 0.0f64;

    unsafe {
        swe_bindings::swe_revjul(tjd, gregflag, &mut year, &mut month, &mut day, &mut hour);
    }

    let obj = Object::new();
    Reflect::set(&obj, &"year".into(), &year.into()).unwrap();
    Reflect::set(&obj, &"month".into(), &month.into()).unwrap();
    Reflect::set(&obj, &"day".into(), &day.into()).unwrap();
    Reflect::set(&obj, &"hour".into(), &hour.into()).unwrap();
    obj.into()
}

#[wasm_bindgen(js_name = swe_get_planet_name)]
pub fn js_swe_get_planet_name(ipl: i32) -> String {
    let mut spname = [0i8; 256];
    unsafe {
        swe_bindings::swe_get_planet_name(ipl, spname.as_mut_ptr());
        CStr::from_ptr(spname.as_ptr()).to_str().unwrap_or("").to_string()
    }
}

// --- Constants exported to JS ---
#[wasm_bindgen]
pub fn SE_SUN() -> i32 { 0 }
#[wasm_bindgen]
pub fn SE_MOON() -> i32 { 1 }
#[wasm_bindgen]
pub fn SE_GREG_CAL() -> i32 { 1 }
#[wasm_bindgen]
pub fn SEFLG_SWIEPH() -> i32 { 2 }
#[wasm_bindgen]
pub fn SEFLG_SPEED() -> i32 { 256 }

// --- C stdlib shims for wasm32 target ---
#[cfg(target_arch = "wasm32")]
mod shims {
    // Math shims via libm
    #[no_mangle] pub extern "C" fn sin(x: f64) -> f64 { libm::sin(x) }
    #[no_mangle] pub extern "C" fn cos(x: f64) -> f64 { libm::cos(x) }
    #[no_mangle] pub extern "C" fn tan(x: f64) -> f64 { libm::tan(x) }
    #[no_mangle] pub extern "C" fn asin(x: f64) -> f64 { libm::asin(x) }
    #[no_mangle] pub extern "C" fn acos(x: f64) -> f64 { libm::acos(x) }
    #[no_mangle] pub extern "C" fn atan(x: f64) -> f64 { libm::atan(x) }
    #[no_mangle] pub extern "C" fn atan2(y: f64, x: f64) -> f64 { libm::atan2(y, x) }
    #[no_mangle] pub extern "C" fn sqrt(x: f64) -> f64 { libm::sqrt(x) }
    #[no_mangle] pub extern "C" fn log(x: f64) -> f64 { libm::log(x) }
    #[no_mangle] pub extern "C" fn exp(x: f64) -> f64 { libm::exp(x) }
    #[no_mangle] pub extern "C" fn pow(x: f64, y: f64) -> f64 { libm::pow(x, y) }
    #[no_mangle] pub extern "C" fn fabs(x: f64) -> f64 { libm::fabs(x) }
    #[no_mangle] pub extern "C" fn ceil(x: f64) -> f64 { libm::ceil(x) }
    #[no_mangle] pub extern "C" fn floor(x: f64) -> f64 { libm::floor(x) }
    #[no_mangle] pub extern "C" fn fmod(x: f64, y: f64) -> f64 { libm::fmod(x, y) }
    #[no_mangle] pub extern "C" fn log10(x: f64) -> f64 { libm::log10(x) }

    // Memory allocator
    const MAGIC: usize = 0xDEADBEEF;
    const HEADER: usize = 8;

    #[no_mangle]
    pub unsafe extern "C" fn malloc(size: usize) -> *mut u8 {
        let total = size + HEADER;
        let layout = std::alloc::Layout::from_size_align_unchecked(total, 8);
        let ptr = std::alloc::alloc(layout);
        if ptr.is_null() { return std::ptr::null_mut(); }
        let h = ptr as *mut usize;
        *h = MAGIC;
        *h.add(1) = total;
        ptr.add(HEADER)
    }

    #[no_mangle]
    pub unsafe extern "C" fn free(ptr: *mut u8) {
        if ptr.is_null() { return; }
        let real = ptr.sub(HEADER);
        let h = real as *mut usize;
        if *h != MAGIC { return; }
        let total = *h.add(1);
        let layout = std::alloc::Layout::from_size_align_unchecked(total, 8);
        std::alloc::dealloc(real, layout);
    }

    #[no_mangle]
    pub unsafe extern "C" fn calloc(n: usize, size: usize) -> *mut u8 {
        let total = n * size;
        let ptr = malloc(total);
        if !ptr.is_null() { std::ptr::write_bytes(ptr, 0, total); }
        ptr
    }

    #[no_mangle]
    pub unsafe extern "C" fn realloc(ptr: *mut u8, new_size: usize) -> *mut u8 {
        if ptr.is_null() { return malloc(new_size); }
        if new_size == 0 { free(ptr); return std::ptr::null_mut(); }
        let real = ptr.sub(HEADER);
        let h = real as *mut usize;
        if *h != MAGIC { return std::ptr::null_mut(); }
        let old_total = *h.add(1);
        let old_user = old_total - HEADER;
        let new_ptr = malloc(new_size);
        if !new_ptr.is_null() {
            let copy = if old_user < new_size { old_user } else { new_size };
            std::ptr::copy_nonoverlapping(ptr, new_ptr, copy);
            free(ptr);
        }
        new_ptr
    }

    // String/memory primitives
    #[no_mangle] pub unsafe extern "C" fn memcpy(d: *mut u8, s: *const u8, n: usize) -> *mut u8 { std::ptr::copy_nonoverlapping(s, d, n); d }
    #[no_mangle] pub unsafe extern "C" fn memmove(d: *mut u8, s: *const u8, n: usize) -> *mut u8 { std::ptr::copy(s, d, n); d }
    #[no_mangle] pub unsafe extern "C" fn memset(s: *mut u8, c: i32, n: usize) -> *mut u8 { std::ptr::write_bytes(s, c as u8, n); s }

    #[no_mangle]
    pub unsafe extern "C" fn memchr(s: *const u8, c: i32, n: usize) -> *mut u8 {
        for i in 0..n { if *s.add(i) == c as u8 { return s.add(i) as *mut u8; } }
        std::ptr::null_mut()
    }

    #[no_mangle]
    pub unsafe extern "C" fn strcpy(d: *mut u8, s: *const u8) -> *mut u8 {
        let mut i = 0;
        loop { let c = *s.add(i); *d.add(i) = c; if c == 0 { break; } i += 1; }
        d
    }

    #[no_mangle]
    pub unsafe extern "C" fn strncpy(d: *mut u8, s: *const u8, n: usize) -> *mut u8 {
        let mut i = 0;
        while i < n {
            let c = *s.add(i);
            *d.add(i) = c;
            if c == 0 { i += 1; while i < n { *d.add(i) = 0; i += 1; } break; }
            i += 1;
        }
        d
    }

    #[no_mangle]
    pub unsafe extern "C" fn strlen(s: *const i8) -> usize {
        let mut len = 0; while *s.add(len) != 0 { len += 1; } len
    }

    #[no_mangle]
    pub unsafe extern "C" fn strcmp(s1: *const i8, s2: *const i8) -> i32 {
        let mut i = 0;
        loop {
            let c1 = *s1.add(i); let c2 = *s2.add(i);
            if c1 != c2 { return (c1 - c2) as i32; }
            if c1 == 0 { return 0; }
            i += 1;
        }
    }

    #[no_mangle]
    pub unsafe extern "C" fn strncmp(s1: *const i8, s2: *const i8, n: usize) -> i32 {
        for i in 0..n {
            let c1 = *s1.add(i); let c2 = *s2.add(i);
            if c1 != c2 { return (c1 - c2) as i32; }
            if c1 == 0 { return 0; }
        }
        0
    }

    #[no_mangle]
    pub unsafe extern "C" fn strstr(haystack: *const i8, needle: *const i8) -> *const i8 {
        let nlen = strlen(needle);
        if nlen == 0 { return haystack; }
        let mut h = haystack;
        while *h != 0 { if strncmp(h, needle, nlen) == 0 { return h; } h = h.add(1); }
        std::ptr::null()
    }

    #[no_mangle]
    pub unsafe extern "C" fn strpbrk(s: *const i8, accept: *const i8) -> *mut i8 {
        let mut sp = s;
        while *sp != 0 {
            let mut ap = accept;
            while *ap != 0 { if *sp == *ap { return sp as *mut i8; } ap = ap.add(1); }
            sp = sp.add(1);
        }
        std::ptr::null_mut()
    }

    #[no_mangle]
    pub unsafe extern "C" fn strchr(s: *const i8, c: i32) -> *mut i8 {
        let mut p = s;
        loop { if *p == c as i8 { return p as *mut i8; } if *p == 0 { return std::ptr::null_mut(); } p = p.add(1); }
    }

    #[no_mangle]
    pub unsafe extern "C" fn strrchr(s: *const i8, c: i32) -> *mut i8 {
        let mut last = std::ptr::null_mut();
        let mut p = s;
        loop { if *p == c as i8 { last = p as *mut i8; } if *p == 0 { return last; } p = p.add(1); }
    }

    #[no_mangle]
    pub unsafe extern "C" fn strcat(d: *mut i8, s: *const i8) -> *mut i8 {
        let l = strlen(d); strcpy(d.add(l) as *mut u8, s as *const u8); d
    }

    #[no_mangle]
    pub unsafe extern "C" fn strdup(s: *const i8) -> *mut i8 {
        let len = strlen(s);
        let ptr = malloc(len + 1) as *mut i8;
        if !ptr.is_null() { strcpy(ptr as *mut u8, s as *const u8); }
        ptr
    }

    // Numeric stubs
    #[no_mangle] pub extern "C" fn abs(j: i32) -> i32 { j.abs() }
    #[no_mangle] pub extern "C" fn labs(j: i64) -> i64 { j.abs() }
    #[no_mangle] pub extern "C" fn atof(_: *const i8) -> f64 { 0.0 }
    #[no_mangle] pub extern "C" fn atoi(_: *const i8) -> i32 { 0 }
    #[no_mangle] pub extern "C" fn atol(_: *const i8) -> i64 { 0 }

    #[no_mangle]
    pub unsafe extern "C" fn strtod(s: *const i8, endptr: *mut *mut i8) -> f64 {
        if !endptr.is_null() { *endptr = s as *mut i8; }
        0.0
    }

    // ctype
    #[no_mangle] pub extern "C" fn isspace(c: i32) -> i32 { if (c as u8 as char).is_whitespace() { 1 } else { 0 } }
    #[no_mangle] pub extern "C" fn isdigit(c: i32) -> i32 { if (c as u8 as char).is_ascii_digit() { 1 } else { 0 } }
    #[no_mangle] pub extern "C" fn isalpha(c: i32) -> i32 { if (c as u8 as char).is_ascii_alphabetic() { 1 } else { 0 } }
    #[no_mangle] pub extern "C" fn isalnum(c: i32) -> i32 { if (c as u8 as char).is_ascii_alphanumeric() { 1 } else { 0 } }
    #[no_mangle] pub extern "C" fn isupper(c: i32) -> i32 { if (c as u8 as char).is_ascii_uppercase() { 1 } else { 0 } }
    #[no_mangle] pub extern "C" fn islower(c: i32) -> i32 { if (c as u8 as char).is_ascii_lowercase() { 1 } else { 0 } }
    #[no_mangle] pub extern "C" fn tolower(c: i32) -> i32 { (c as u8).to_ascii_lowercase() as i32 }
    #[no_mangle] pub extern "C" fn toupper(c: i32) -> i32 { (c as u8).to_ascii_uppercase() as i32 }

    // I/O stubs (return NULL/0 → Moshier fallback)
    #[no_mangle] pub extern "C" fn fopen(_: *const i8, _: *const i8) -> *mut u8 { std::ptr::null_mut() }
    #[no_mangle] pub extern "C" fn fclose(_: *mut u8) -> i32 { 0 }
    #[no_mangle] pub extern "C" fn fseek(_: *mut u8, _: i64, _: i32) -> i32 { 0 }
    #[no_mangle] pub extern "C" fn ftell(_: *mut u8) -> i64 { 0 }
    #[no_mangle] pub extern "C" fn fread(_: *mut u8, _: usize, _: usize, _: *mut u8) -> usize { 0 }
    #[no_mangle] pub extern "C" fn fwrite(_: *const u8, _: usize, n: usize, _: *mut u8) -> usize { n }
    #[no_mangle] pub extern "C" fn fgets(_: *mut i8, _: i32, _: *mut u8) -> *mut i8 { std::ptr::null_mut() }
    #[no_mangle] pub extern "C" fn fflush(_: *mut u8) -> i32 { 0 }
    #[no_mangle] pub extern "C" fn fseeko(_: *mut u8, _: i64, _: i32) -> i32 { 0 }
    #[no_mangle] pub extern "C" fn ftello(_: *mut u8) -> i64 { 0 }
    #[no_mangle] pub extern "C" fn rewind(_: *mut u8) {}

    // time stub
    #[no_mangle] pub extern "C" fn time(_: *mut i64) -> i64 { 0 }

    // stdlib stubs
    #[no_mangle] pub extern "C" fn getenv(_: *const i8) -> *mut i8 { std::ptr::null_mut() }
    #[no_mangle] pub extern "C" fn exit(_: i32) { panic!("exit called") }
    #[no_mangle] pub extern "C" fn qsort(_: *mut u8, _: usize, _: usize, _: *const u8) {}
    #[no_mangle] pub extern "C" fn bsearch(_: *const u8, _: *const u8, _: usize, _: usize, _: *const u8) -> *mut u8 { std::ptr::null_mut() }

    // dlfcn stubs
    #[no_mangle] pub extern "C" fn dlopen(_: *const i8, _: i32) -> *mut u8 { std::ptr::null_mut() }
    #[no_mangle] pub extern "C" fn dlerror() -> *mut i8 { std::ptr::null_mut() }
    #[no_mangle] pub extern "C" fn dlsym(_: *mut u8, _: *const i8) -> *mut u8 { std::ptr::null_mut() }
    #[no_mangle] pub extern "C" fn dlclose(_: *mut u8) -> i32 { 0 }
    #[no_mangle] pub extern "C" fn dladdr(_: *const u8, _: *mut u8) -> i32 { 0 }

    // unistd / stat stubs
    #[no_mangle] pub extern "C" fn readlink(_: *const i8, _: *mut i8, _: usize) -> isize { -1 }
    #[no_mangle] pub extern "C" fn stat(_: *const i8, _: *mut u8) -> i32 { -1 }
}

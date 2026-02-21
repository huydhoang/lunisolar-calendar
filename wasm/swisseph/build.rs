use std::env;
use std::path::PathBuf;

fn main() {
    let target = env::var("TARGET").unwrap();

    let mut build = cc::Build::new();

    let swe_src = "vendor/swisseph";
    let wrapper_src = "src/wrapper";

    // Swiss Ephemeris core C files
    let c_files = [
        "swecl.c", "swedate.c", "swehel.c", "swehouse.c", "swejpl.c",
        "swemmoon.c", "swemplan.c", "sweph.c", "swephlib.c",
    ];

    for file in &c_files {
        build.file(format!("{}/{}", swe_src, file));
    }

    build.include(swe_src);
    build.include(wrapper_src);

    // Rename C symbols to avoid collision with wasm-bindgen exports
    let renaming = [
        ("swe_calc_ut", "impl_swe_calc_ut"),
        ("swe_julday", "impl_swe_julday"),
        ("swe_revjul", "impl_swe_revjul"),
        ("swe_set_sid_mode", "impl_swe_set_sid_mode"),
        ("swe_get_ayanamsa_ut", "impl_swe_get_ayanamsa_ut"),
        ("swe_get_planet_name", "impl_swe_get_planet_name"),
        ("swe_version", "impl_swe_version"),
    ];

    for (orig, renamed) in &renaming {
        build.define(orig, Some(*renamed));
    }

    if target.contains("wasm32") {
        build.file(format!("{}/stub.c", wrapper_src));

        let manifest_dir = env::var("CARGO_MANIFEST_DIR").unwrap();
        let wasm_includes = PathBuf::from(manifest_dir).join("wasm-includes");
        build.include(&wasm_includes);

        build
            .flag("-Wno-implicit-function-declaration")
            .flag("-Wno-int-conversion")
            .flag("-Wno-unused-variable")
            .flag("-Wno-unused-parameter")
            .flag("-Wno-sign-compare")
            .flag("-Wno-missing-braces")
            .flag("-Wno-parentheses")
            .flag("-Wno-misleading-indentation")
            .flag("-Wno-empty-body")
            .flag("-Wno-unknown-pragmas")
            .flag("-target").flag("wasm32-unknown-unknown");
    }

    build.compile("swe");
}

// Build script: compile the C stub that provides variadic functions (sprintf etc.)
// for the wasm32 target.  These cannot be defined in Rust on stable because
// C-variadic function *definitions* are still unstable.

fn main() {
    let target = std::env::var("TARGET").unwrap_or_default();
    if target.contains("wasm32") {
        let manifest = std::env::var("CARGO_MANIFEST_DIR").unwrap();
        let stub = std::path::Path::new(&manifest).join("src").join("stub.c");

        cc::Build::new()
            .file(&stub)
            .include(std::path::Path::new(&manifest).join("wasm-includes"))
            .flag("-Wno-implicit-function-declaration")
            .flag("-Wno-int-conversion")
            .flag("-Wno-unused-parameter")
            .compile("stub");
    }
}

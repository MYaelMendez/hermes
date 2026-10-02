//! Minimal crate that compiles to wasm32-unknown-unknown, used to verify the
//! +æ^glocal Rust/WASM hands of the host loop (build path; no std/io needed).

#[no_mangle]
pub extern "C" fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[no_mangle]
pub extern "C" fn answer() -> i32 {
    42
}

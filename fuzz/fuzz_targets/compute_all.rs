#![no_main]

//! Fuzz the scalar reference path: arbitrary bytes as f64 series must never
//! panic, go out of bounds, or break the NaN contract. A fuzzer-found panic
//! becomes a `proptest_checks` regression test (which runs on stable).

use kymora::features::{compute_all, NAMES};
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if data.len() > 2400 {
        return;
    }
    let mut x: Vec<f64> = data
        .chunks_exact(8)
        .map(|c| f64::from_le_bytes(c.try_into().unwrap()))
        .collect();
    // Exercise sub-slice lengths too (empty included).
    x.truncate(data.first().map(|b| (*b as usize) % 301).unwrap_or(0).min(x.len()));
    let mut out = [0.0; 33];
    compute_all(&x, &mut out);
    assert_eq!(out.len(), NAMES.len());
    if x.iter().any(|v| v.is_nan()) {
        assert!(
            out.iter().all(|v| v.is_nan()),
            "NaN must poison the whole row"
        );
    }
});

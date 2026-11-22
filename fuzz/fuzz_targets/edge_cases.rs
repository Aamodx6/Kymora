#![no_main]

//! Fuzz edge cases: NaN/inf, short series (0-3 elements), constant series,
//! and extreme values for both batch `compute_all` and `StreamingExtractor`.

use _core::features::{compute_all, StreamingExtractor, NAMES};
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if data.is_empty() {
        return;
    }

    // Synthesize extreme inputs from fuzz bytes
    let mode = data[0] % 5;
    let mut series = Vec::new();

    match mode {
        0 => {
            // NaN and Inf variations
            let candidates = [
                f64::NAN,
                f64::INFINITY,
                f64::NEG_INFINITY,
                0.0,
                -0.0,
                f64::MIN_POSITIVE,
                f64::MAX,
            ];
            for b in &data[1..] {
                series.push(candidates[(*b as usize) % candidates.len()]);
            }
        }
        1 => {
            // Short series: 0, 1, 2, or 3 elements
            let len = (data[0] as usize) % 4;
            for c in data[1..].chunks_exact(8).take(len) {
                series.push(f64::from_le_bytes(c.try_into().unwrap()));
            }
        }
        2 => {
            // Constant series
            let val = if data.len() >= 9 {
                f64::from_le_bytes(data[1..9].try_into().unwrap())
            } else {
                42.0
            };
            let len = (data[0] as usize % 128) + 1;
            series = vec![val; len];
        }
        3 => {
            // Alternating extreme values
            for (idx, b) in data[1..].iter().enumerate() {
                let v = if idx % 2 == 0 { f64::NAN } else { *b as f64 };
                series.push(v);
            }
        }
        _ => {
            // Arbitrary raw f64
            for c in data[1..].chunks_exact(8) {
                series.push(f64::from_le_bytes(c.try_into().unwrap()));
            }
        }
    }

    // 1. Batch compute_all must never panic
    let mut out = [0.0; 33];
    compute_all(&series, &mut out);
    assert_eq!(out.len(), NAMES.len());

    // 2. Streaming extractor must never panic on push/compute
    let window_size = ((data[0] as usize) % 32) + 1;
    let mut stream = StreamingExtractor::new(window_size);
    for &x in &series {
        let _ = stream.push(x);
        let mut fast = [0.0; 12];
        stream.compute_fast(&mut fast);
        let mut full = [0.0; 33];
        stream.compute_features(&mut full);
    }
});

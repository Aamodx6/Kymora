#![no_main]

//! Fuzz the streaming extractor: arbitrary window sizes, anchor intervals,
//! and push sequences must never panic on push or either compute kind.

use kymora::features::StreamingExtractor;
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if data.len() < 16 || data.len() > 2400 {
        return;
    }
    let w = (data[0] as usize % 64) + 1;
    let interval = ((data[1] as usize) << 8 | data[2] as usize) % 5000 + 1;
    let mut ext = StreamingExtractor::new(w).with_anchor_interval(interval);
    for c in data[3..].chunks_exact(8) {
        let v = f64::from_le_bytes(c.try_into().unwrap());
        let _ = ext.push(v);
        let mut fast = [0.0; 12];
        ext.compute_fast(&mut fast);
        let mut all = [0.0; 33];
        ext.compute_features(&mut all);
    }
});

#![no_main"

//! Fuzz ragged CSR extraction and plan building: arbitrary offsets, values,
//! and feature/profile strings must return Ok/Err, never panic or go out of
//! bounds.

use kymora::exec;
use kymora::plan::FeaturePlan;
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if data.len() > 1200 {
        return;
    }
    let mut values = Vec::new();
    let mut offsets = vec![0i64];
    let mut chunks = data.chunks_exact(8);
    for c in &mut chunks {
        values.push(f64::from_le_bytes(c.try_into().unwrap()));
        if values.len() > 100 {
            break;
        }
    }
    // Arbitrary (possibly invalid) offsets from the remaining bytes.
    let rest: Vec<u8> = chunks.remainder().to_vec();
    let mut acc = 0i64;
    for (i, b) in rest.iter().enumerate() {
        if i > 6 {
            break;
        }
        acc += (*b as i64) - 3; // may go negative or non-monotonic: must Err, not panic
        offsets.push(acc);
    }
    let plan = match FeaturePlan::build(Some("core33"), None::<&[&str]>) {
        Ok(p) => p,
        Err(_) => return,
    };
    let mut out = vec![0.0; 8 * 33];
    let _ = exec::extract_ragged_csr_plan(&values, &offsets, &plan, &mut out);
});

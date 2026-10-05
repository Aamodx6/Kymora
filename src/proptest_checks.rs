//! In-process fuzz checks (Phase 6.3): arbitrary shapes/values must never
//! panic, go out of bounds, or break the NaN contract.
//!
//! These run under stable `cargo test` on every platform. The heavier
//! coverage-guided fuzzing lives in `fuzz/` (cargo-fuzz, nightly, Linux CI).

#![cfg(test)]

use proptest::prelude::*;

use crate::exec;
use crate::features::{compute_all, StreamingExtractor, NAMES};
use crate::plan::FeaturePlan;
use crate::scratch::Scratch;

fn slices_match(a: &[f64], b: &[f64]) -> bool {
    a.len() == b.len()
        && a.iter()
            .zip(b.iter())
            .all(|(x, y)| x == y || (x.is_nan() && y.is_nan()))
}

fn hostile_f64() -> impl Strategy<Value = f64> {
    prop_oneof![
        Just(f64::NAN),
        Just(f64::INFINITY),
        Just(f64::NEG_INFINITY),
        Just(0.0),
        Just(-0.0),
        Just(f64::MAX),
        Just(f64::MIN),
        Just(f64::MIN_POSITIVE),
        Just(5e-324),
        Just(1e308),
        Just(-1e308),
        Just(1e9),
        any::<f64>(),
    ]
}

proptest! {
    #![proptest_config(ProptestConfig::with_cases(64))]

    #[test]
    fn compute_all_never_panics(x in prop::collection::vec(hostile_f64(), 0..300)) {
        let mut out = [0.0; 33];
        compute_all(&x, &mut out);
        prop_assert_eq!(out.len(), NAMES.len());
        if x.iter().any(|v| v.is_nan()) {
            prop_assert!(out.iter().all(|v| v.is_nan()), "NaN must poison the whole row");
        }
    }

    #[test]
    fn streaming_never_panics(
        w in 1usize..64,
        pushes in prop::collection::vec(hostile_f64(), 0..200),
        anchor_interval in 1usize..5000,
    ) {
        let mut ext = StreamingExtractor::new(w).with_anchor_interval(anchor_interval);
        for &v in &pushes {
            let _ = ext.push(v);
            let mut fast = [0.0; 12];
            ext.compute_fast(&mut fast);
            let mut all = [0.0; 33];
            ext.compute_features(&mut all);
        }
        let mut win = vec![0.0; w];
        ext.get_current_window(&mut win);
    }

    #[test]
    fn plan_build_never_panics(
        profile in prop::option::of(prop_oneof![
            Just("core33".to_string()),
            Just("minimal".to_string()),
            Just("extended".to_string()),
            Just("full".to_string()),
            Just("bogus".to_string()),
            Just("".to_string()),
        ]),
        features in prop::option::of(prop::collection::vec(
            prop_oneof![
                Just("mean".to_string()),
                Just("not_a_feature".to_string()),
                Just("".to_string()),
                Just("MEAN".to_string()),
            ],
            0..5,
        )),
    ) {
        let feat_refs = features.as_deref();
        let _ = FeaturePlan::build(profile.as_deref(), feat_refs);
    }

    #[test]
    fn ragged_csr_never_panics(
        values in prop::collection::vec(hostile_f64(), 0..100),
        offsets in prop::collection::vec(-5i64..120, 0..8),
    ) {
        let plan = FeaturePlan::build(Some("core33"), None::<&[&str]>).unwrap();
        let mut out = vec![0.0; 8 * 33];
        let _ = exec::extract_ragged_csr_plan(&values, &offsets, &plan, &mut out);
    }

    #[test]
    fn ragged_csr_valid_geometry_matches_batch(
        lens in prop::collection::vec(1usize..40, 1..6),
    ) {
        // Well-formed CSR must equal per-series batch extraction exactly.
        let mut values = Vec::new();
        let mut offsets = vec![0i64];
        for (i, &len) in lens.iter().enumerate() {
            for j in 0..len {
                values.push((i as f64) * 100.0 + (j as f64) * 0.5 + 1.0);
            }
            offsets.push(values.len() as i64);
        }
        let plan = FeaturePlan::build(Some("core33"), None::<&[&str]>).unwrap();
        let n = lens.len();
        let mut out = vec![0.0; n * 33];
        exec::extract_ragged_csr_plan(&values, &offsets, &plan, &mut out).unwrap();
        let mut scratch = Scratch::new(40);
        for (i, &len) in lens.iter().enumerate() {
            let start: usize = offsets[i] as usize;
            let row = &values[start..start + len];
            let mut want = [0.0; 33];
            crate::pipeline::run_plan(row, &plan, &mut scratch, &mut want);
            prop_assert!(
                slices_match(&out[i * 33..(i + 1) * 33], &want[..]),
                "ragged row {i} diverged from batch"
            );
        }
    }
}

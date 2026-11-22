//! Instruction-count benchmark harness for core33 hot paths.
//!
//! Evaluates the core33 feature extraction hot path on:
//! - 1000x500 f64 input (standard batch)
//! - 1x100 f64 input (small-batch single series)
//! - 100x100 f64 input (small-batch multi series)
//!
//! Uses Valgrind / Callgrind client requests when running under Valgrind
//! so only the feature extraction kernel is instrumented.

use _core::exec::extract_plan_into_slice;
use _core::plan::FeaturePlan;

#[cfg(all(target_os = "linux", target_arch = "x86_64"))]
#[inline(always)]
unsafe fn callgrind_start() {
    // Valgrind client request: CALLGRIND_START_INSTRUMENTATION (0x5601)
    std::arch::asm!(
        "rol rdi, 3",
        "rol rdi, 13",
        "rol rdi, 61",
        "rol rdi, 51",
        "xchg rbx, rbx",
        inout("rdi") 0x56010000usize => _,
        options(nostack, preserves_flags)
    );
}

#[cfg(not(all(target_os = "linux", target_arch = "x86_64")))]
#[inline(always)]
unsafe fn callgrind_start() {}

#[cfg(all(target_os = "linux", target_arch = "x86_64"))]
#[inline(always)]
unsafe fn callgrind_stop() {
    // Valgrind client request: CALLGRIND_STOP_INSTRUMENTATION (0x5602)
    std::arch::asm!(
        "rol rdi, 3",
        "rol rdi, 13",
        "rol rdi, 61",
        "rol rdi, 51",
        "xchg rbx, rbx",
        inout("rdi") 0x56020000usize => _,
        options(nostack, preserves_flags)
    );
}

#[cfg(not(all(target_os = "linux", target_arch = "x86_64")))]
#[inline(always)]
unsafe fn callgrind_stop() {}

fn generate_deterministic_data(n_rows: usize, n_steps: usize) -> Vec<f64> {
    let mut data = Vec::with_capacity(n_rows * n_steps);
    for i in 0..n_rows {
        for j in 0..n_steps {
            // Deterministic synthetic signal with multiple frequencies
            let t = j as f64 * 0.05;
            let val = (t + (i as f64 * 0.1)).sin()
                + 0.5 * (t * 2.5 + (i as f64 * 0.2)).cos()
                + 0.1 * ((i * 17 + j * 31) % 100) as f64 * 0.01;
            data.push(val);
        }
    }
    data
}

fn run_workload(n_rows: usize, n_steps: usize, plan: &FeaturePlan) -> f64 {
    let data = generate_deterministic_data(n_rows, n_steps);
    let rows: Vec<&[f64]> = data.chunks_exact(n_steps).collect();
    let n_cols = plan.n_features();
    let mut out = vec![0.0f64; n_rows * n_cols];

    unsafe {
        callgrind_start();
    }
    extract_plan_into_slice(&rows, plan, &mut out);
    unsafe {
        callgrind_stop();
    }

    std::hint::black_box(&out);
    // Return checksum
    out.iter().filter(|v| v.is_finite()).sum()
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let target = args.get(1).map(|s| s.as_str()).unwrap_or("all");

    let plan = FeaturePlan::build(Some("core33"), None::<&[&str]>).expect("valid core33 plan");

    let workloads = [
        ("1000x500", 1000, 500),
        ("1x100", 1, 100),
        ("100x100", 100, 100),
    ];

    for (name, rows, steps) in workloads {
        if target == "all" || target == name {
            let sum = run_workload(rows, steps, &plan);
            println!(
                "WORKLOAD {}: rows={}, steps={}, checksum={:.4}",
                name, rows, steps, sum
            );
        }
    }
}

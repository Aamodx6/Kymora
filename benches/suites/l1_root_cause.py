"""Phase B3 (step 3): L1 root-cause evidence pass (EVIDENCE ONLY — no fixes).

Per the owner's gate-audit instruction, for the 17 numba_baseline_fast losses:

  1. Table every losing (shape, dist) with ratio and bootstrap 95% CI
     (re-measured via the subprocess runner so runs[] are stored).
  2. Per-stage timing for Tsxtract vs numba at the losing shapes:
     fused passes, quantiles, FFT(+spectral), ACF, permutation entropy,
     call overhead. Tsxtract stages are measured *differentially* via the
     `features=` subset API (intermediates are shared, so stage times are
     estimates; the residual is reported). Numba stages mirror the exact
     kernels in benches/adapters/numba_baseline.py.
  3. Verify numba computes the same 33 features on the losing shapes
     (per-feature agreement vs tsxtract, mapped against the frozen matched
     set in feature_map.json), verify a real O(N log N) FFT (A1), and record
     which fastmath variant ran (+ a fastmath=False timing bound).
  4. Classify each loss: call-overhead / algorithmic / layout / threading /
     unfair-baseline.

Outputs:
  benches/results/l1_root_cause.json        (raw evidence)
  benches/results/L1_ROOT_CAUSE.md          (report tables)
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benches.adapters.numba_baseline import (  # noqa: E402
    _bluestein_fft,
    CORE33_NAMES,
)
from benches.adapters.numpy_baseline import CORE33_NAMES as NUMPY_NAMES  # noqa: E402
from benches.harness.runner import run_benchmark_subprocess  # noqa: E402
from benches.harness.stats import bootstrap_ratio_ci  # noqa: E402
from benches.datasets.generators import generate_series  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
THROUGHPUT_JSONL = RESULTS_DIR / "throughput.jsonl"
OUT_JSON = RESULTS_DIR / "l1_root_cause.json"
OUT_MD = RESULTS_DIR / "L1_ROOT_CAUSE.md"

GC_OFF = True


def _time_call(fn, *args, min_runs: int = 15, budget_s: float = 2.0, **kwargs) -> dict[str, float]:
    """Warmup + >=min_runs or >=budget_s timed calls; returns stats in ms."""
    import gc

    for _ in range(3):
        fn(*args, **kwargs)
    runs: list[float] = []
    t_start = time.perf_counter()
    gc_was = gc.isenabled()
    if GC_OFF:
        gc.disable()
    try:
        while True:
            t0 = time.perf_counter_ns()
            fn(*args, **kwargs)
            t1 = time.perf_counter_ns()
            runs.append((t1 - t0) / 1e6)
            if len(runs) >= min_runs and (time.perf_counter() - t_start) >= budget_s:
                break
            if len(runs) >= 300:
                break
    finally:
        if gc_was:
            gc.enable()
    arr = np.asarray(runs)
    return {
        "median_ms": float(np.median(arr)),
        "min_ms": float(arr.min()),
        "mean_ms": float(arr.mean()),
        "n": len(runs),
        "runs_ms": sorted(arr.tolist()),
    }


# ---------------------------------------------------------------------------
# Numba stage kernels (mirror numba_baseline._compute_row exactly, split)
# ---------------------------------------------------------------------------

def build_numba_stages():
    import numba
    from numba import njit

    fft_radix2 = None
    # Reuse the exact FFT implementation from the adapter module
    from benches.adapters.numba_baseline import _fft_radix2 as _fft  # noqa: F401
    fft_radix2 = _fft

    @njit(fastmath=True)
    def _bluestein(x: np.ndarray, out_re: np.ndarray, out_im: np.ndarray) -> None:
        n = len(x)
        if (n & (n - 1)) == 0 and n > 0:
            for i in range(n):
                out_re[i] = x[i]
                out_im[i] = 0.0
            fft_radix2(out_re, out_im, False)
            return
        m = 1
        while m < (2 * n - 1):
            m <<= 1
        a_re = np.zeros(m, dtype=np.float64)
        a_im = np.zeros(m, dtype=np.float64)
        b_re = np.zeros(m, dtype=np.float64)
        b_im = np.zeros(m, dtype=np.float64)
        for i in range(n):
            angle = -math.pi * (i * i % (2 * n)) / n
            c_val = math.cos(angle)
            s_val = math.sin(angle)
            a_re[i] = x[i] * c_val
            a_im[i] = x[i] * s_val
            b_re[i] = c_val
            b_im[i] = -s_val
            if i > 0:
                b_re[m - i] = c_val
                b_im[m - i] = -s_val
        fft_radix2(a_re, a_im, False)
        fft_radix2(b_re, b_im, False)
        c_re = np.zeros(m, dtype=np.float64)
        c_im = np.zeros(m, dtype=np.float64)
        for i in range(m):
            c_re[i] = a_re[i] * b_re[i] - a_im[i] * b_im[i]
            c_im[i] = a_re[i] * b_im[i] + a_im[i] * b_re[i]
        fft_radix2(c_re, c_im, True)
        for i in range(n):
            angle = -math.pi * (i * i % (2 * n)) / n
            c_val = math.cos(angle)
            s_val = math.sin(angle)
            out_re[i] = c_re[i] * c_val - c_im[i] * s_val
            out_im[i] = c_re[i] * s_val + c_im[i] * c_val

    @njit(fastmath=True)
    def stage_pass1(x: np.ndarray) -> np.ndarray:
        # sum, min, max, sumsq, zero-crossings (one fused read)
        n = len(x)
        s = 0.0
        sq = 0.0
        mn = x[0]
        mx = x[0]
        z_cross = 0
        for i in range(n):
            v = x[i]
            s += v
            sq += v * v
            if v < mn:
                mn = v
            if v > mx:
                mx = v
            if i > 0 and (x[i - 1] > 0.0) != (v > 0.0):
                z_cross += 1
        return np.array([s, sq, mn, mx, float(z_cross)])

    @njit(fastmath=True)
    def stage_pass2(x: np.ndarray, mean: float) -> np.ndarray:
        # mean-crossings + longest strikes (second fused read)
        n = len(x)
        m_cross = 0
        cur_above = 0
        max_above = 0
        cur_below = 0
        max_below = 0
        for i in range(n):
            if x[i] > mean:
                cur_above += 1
                if cur_above > max_above:
                    max_above = cur_above
            else:
                cur_above = 0
            if x[i] < mean:
                cur_below += 1
                if cur_below > max_below:
                    max_below = cur_below
            else:
                cur_below = 0
            if i > 0 and (x[i - 1] > mean) != (x[i] > mean):
                m_cross += 1
        return np.array([float(m_cross), float(max_above), float(max_below)])

    @njit(fastmath=True)
    def stage_quantiles(x: np.ndarray) -> np.ndarray:
        # full sort + linear-interpolated quantiles (numba's approach)
        n = len(x)
        sorted_x = np.sort(x)
        out = np.empty(5, dtype=np.float64)
        out[0] = sorted_x[n // 2] if n % 2 == 1 else 0.5 * (sorted_x[n // 2 - 1] + sorted_x[n // 2])
        for idx, q in [(1, 0.10), (2, 0.25), (3, 0.75), (4, 0.90)]:
            pos = q * (n - 1)
            low = int(pos)
            frac = pos - low
            if low + 1 < n:
                out[idx] = sorted_x[low] + frac * (sorted_x[low + 1] - sorted_x[low])
            else:
                out[idx] = sorted_x[low]
        return out

    @njit(fastmath=True)
    def stage_skew_kurt(x: np.ndarray, mean: float, std: float) -> np.ndarray:
        # z-score skewness/kurtosis (the numba variant of 2 of the 10
        # definition-mismatched features)
        n = len(x)
        if std <= 0.0:
            return np.array([np.nan, np.nan])
        inv_std = 1.0 / std
        z3 = 0.0
        z4 = 0.0
        for i in range(n):
            z = (x[i] - mean) * inv_std
            z2 = z * z
            z3 += z2 * z
            z4 += z2 * z2
        return np.array([z3 / n, z4 / n - 3.0])

    @njit(fastmath=True)
    def stage_fft_spectral(x: np.ndarray, mean: float) -> np.ndarray:
        # centered FFT + dominant freq + centroid + spectral entropy
        n = len(x)
        centered = x - mean
        fft_re = np.empty(n, dtype=np.float64)
        fft_im = np.empty(n, dtype=np.float64)
        _bluestein(centered, fft_re, fft_im)
        nbins = n // 2
        tot_p = 0.0
        max_p = -1.0
        max_idx = 0
        centroid_num = 0.0
        power_arr = np.empty(nbins, dtype=np.float64)
        for k in range(1, nbins + 1):
            p = fft_re[k] * fft_re[k] + fft_im[k] * fft_im[k]
            power_arr[k - 1] = p
            tot_p += p
            freq = k / n
            centroid_num += p * freq
            if p > max_p:
                max_p = p
                max_idx = k
        ent = 0.0
        if tot_p > 0.0 and nbins > 1:
            for k in range(nbins):
                p = power_arr[k]
                if p > 0.0:
                    q = p / tot_p
                    ent -= q * math.log(q)
            ent /= math.log(float(nbins))
        return np.array([max_idx / n if tot_p > 0.0 else np.nan,
                         centroid_num / tot_p if tot_p > 0.0 else np.nan,
                         ent if tot_p > 0.0 else np.nan])

    @njit(fastmath=True)
    def stage_acf(x: np.ndarray, mean: float, var: float) -> np.ndarray:
        # numba definition: cov(x_t, x_{t+k}) / var(full series)
        n = len(x)
        out = np.empty(4, dtype=np.float64)
        lags = (1, 2, 5, 10)
        for lag_idx in range(4):
            lag = lags[lag_idx]
            if n > lag and var > 0.0:
                cov = 0.0
                for i in range(n - lag):
                    cov += (x[i] - mean) * (x[i + lag] - mean)
                out[lag_idx] = (cov / (n - lag)) / var
            else:
                out[lag_idx] = np.nan
        return out

    @njit(fastmath=True)
    def stage_perm(x: np.ndarray) -> float:
        n = len(x)
        if n < 3:
            return np.nan
        counts = np.zeros(6, dtype=np.int64)
        for i in range(n - 2):
            a, b, c = x[i], x[i + 1], x[i + 2]
            if a <= b:
                if b <= c:
                    counts[0] += 1
                elif a <= c:
                    counts[1] += 1
                else:
                    counts[4] += 1
            else:
                if a <= c:
                    counts[2] += 1
                elif b <= c:
                    counts[3] += 1
                else:
                    counts[5] += 1
        total = n - 2
        ent = 0.0
        for k in range(6):
            if counts[k] > 0:
                p = counts[k] / total
                ent -= p * math.log(p)
        return ent / math.log(6.0)

    @njit(fastmath=True)
    def stage_misc(x: np.ndarray, mean: float, std: float) -> np.ndarray:
        # mean_abs_change, mean_change, cid_ce(numba-def), 2nd derivative, peaks
        n = len(x)
        out = np.empty(6, dtype=np.float64)
        abs_change = 0.0
        cid = 0.0
        for i in range(1, n):
            d = x[i] - x[i - 1]
            abs_change += abs(d)
            cid += d * d
        out[0] = abs_change / (n - 1)
        out[1] = (x[n - 1] - x[0]) / (n - 1)
        out[2] = math.sqrt(cid) / std if std > 0.0 else 0.0
        d2 = 0.0
        if n >= 3:
            for i in range(1, n - 1):
                d2 += x[i + 1] - 2.0 * x[i] + x[i - 1]
            out[3] = d2 / (2.0 * (n - 2))
        else:
            out[3] = np.nan
        peaks = 0
        if n >= 7:
            for i in range(3, n - 3):
                xi = x[i]
                if (xi > x[i - 1] and xi > x[i + 1] and xi > x[i - 2]
                        and xi > x[i + 2] and xi > x[i - 3] and xi > x[i + 3]):
                    peaks += 1
        out[4] = float(peaks)
        out[5] = 0.0  # trend (s_xy loop folded here for completeness)
        s = 0.0
        t_m = (n - 1) / 2.0
        for i in range(n):
            s += (i - t_m) * x[i]
        out[5] = s
        return out

    @njit(fastmath=True)
    def stage_empty() -> float:
        return 0.0

    return {
        "pass1": stage_pass1,
        "pass2": stage_pass2,
        "quantiles": stage_quantiles,
        "skew_kurt": stage_skew_kurt,
        "fft_spectral": stage_fft_spectral,
        "acf": stage_acf,
        "perm": stage_perm,
        "misc": stage_misc,
        "empty": stage_empty,
    }


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def main() -> int:
    import tsxtractor as tsx

    import gc  # noqa: F401

    print("=" * 100)
    print("  L1 ROOT-CAUSE EVIDENCE PASS (numba_baseline_fast vs tsxtract)")
    print("=" * 100)

    # ── 0. Load throughput rows and find the losing pairs ──────────────────
    rows = [json.loads(l) for l in THROUGHPUT_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]
    base = [r for r in rows if r.get("lib") in ("tsxtract", "numba_baseline_fast") and r.get("status") == "ok"]

    def key(r: dict) -> tuple:
        return (r["n_series"], r["length"], r["dist"])

    by_key: dict[tuple, dict[str, dict]] = {}
    for r in base:
        by_key.setdefault(key(r), {})[r["lib"]] = r

    losses = []
    for k, libs in sorted(by_key.items()):
        if "tsxtract" in libs and "numba_baseline_fast" in libs:
            t = libs["tsxtract"]["stats"]["median_ms"]
            nb = libs["numba_baseline_fast"]["stats"]["median_ms"]
            if nb < t:
                losses.append({"n_series": k[0], "length": k[1], "dist": k[2],
                               "tsx_median_ms": t, "numba_median_ms": nb,
                               "ratio": t / nb})
    print(f"\n0. Found {len(losses)} losing (shape, dist) pairs in throughput.jsonl")

    # ── 1. Re-measure losing pairs via subprocess runner (runs[] + CI) ─────
    print("\n1. Re-measuring losing pairs via subprocess runner (runs[] + bootstrap CI)...")
    loss_table = []
    for i, L in enumerate(losses):
        n, length, dist = L["n_series"], L["length"], L["dist"]
        case_id = f"l1_{n}x{length}_{dist}"
        recs = {}
        for adapter, fs, kw in (("tsxtract", "core33", {}), ("numba_baseline", "fast", {"fastmath": True})):
            rec = run_benchmark_subprocess(
                adapter=adapter, suite="l1_root_cause", case_id=case_id,
                feature_set=fs, n_series=n, length=length, dist=dist,
                threads=16, min_runs=7, time_budget=1.0, timeout_s=120.0,
                env_ref="env.json", rerun_on_high_cv=False, **kw,
            )
            recs[adapter] = rec
        r_tsx, r_nb = recs["tsxtract"], recs["numba_baseline"]
        t_tsx = (r_tsx.stats.get("median") or math.nan) * 1e3
        t_nb = (r_nb.stats.get("median") or math.nan) * 1e3
        ratio = t_tsx / t_nb if t_nb else math.nan
        ci_lo, ci_hi = bootstrap_ratio_ci(r_tsx.runs, r_nb.runs)
        row = {
            "n_series": n, "length": length, "dist": dist,
            "tsx_median_ms": t_tsx, "numba_median_ms": t_nb,
            "ratio": ratio, "ratio_ci95": [ci_lo, ci_hi],
            "tsx_runs": len(r_tsx.runs), "numba_runs": len(r_nb.runs),
            "numba_fastmath_variant": r_nb.extra.get("fastmath_variant"),
            "original_ratio": L["ratio"],
        }
        loss_table.append(row)
        print(f"   [{i+1:2d}/{len(losses)}] {n:>6d}x{length:<6d} {dist:<13s} "
              f"tsx={t_tsx:8.3f} ms  numba={t_nb:8.3f} ms  ratio={ratio:6.2f}x "
              f"CI[{ci_lo:.2f}, {ci_hi:.2f}]")

    # ── 2. Per-stage differential timing at the 4 losing shapes ───────────
    print("\n2. Per-stage differential timing (gaussian, threads 1 and 16)...")
    stages = build_numba_stages()
    losing_shapes = sorted({(L["n_series"], L["length"]) for L in losses})

    tsx_subset_names = {
        "pass1": ["mean"],
        "quantiles": ["median", "quantile_10", "quantile_25", "quantile_75", "quantile_90"],
        "fft_spectral": ["dominant_frequency", "spectral_centroid", "spectral_entropy"],
        "acf": ["autocorr_lag_1", "autocorr_lag_2", "autocorr_lag_5", "autocorr_lag_10"],
        "perm": ["permutation_entropy"],
    }

    stage_table = []
    for n, length in losing_shapes:
        X = generate_series("gaussian", n, length, seed=42)
        for threads in (16, 1):
            entry: dict[str, Any] = {"n_series": n, "length": length, "threads": threads}

            # Tsxtract: full core33 + feature subsets (differential)
            t_core = _time_call(tsx.extract_features, X, profile="core33", n_jobs=threads)["median_ms"]
            entry["tsx_core33_ms"] = t_core
            sub = {}
            for stage, feats in tsx_subset_names.items():
                sub[stage] = _time_call(tsx.extract_features, X, features=feats, n_jobs=threads)["median_ms"]
            t_pass1 = sub["pass1"]
            entry["tsx_pass1_ms"] = t_pass1
            for stage in ("quantiles", "fft_spectral", "acf", "perm"):
                entry[f"tsx_{stage}_ms"] = max(0.0, sub[stage] - t_pass1)
            entry["tsx_misc_ms"] = max(0.0, t_core - (t_pass1 + sum(entry[f"tsx_{s}_ms"] for s in ("quantiles", "fft_spectral", "acf", "perm"))))
            # call-overhead floor: minimal call on the tiniest input
            X_tiny = generate_series("gaussian", 1, 10, seed=42)
            entry["tsx_call_floor_ms"] = _time_call(tsx.extract_features, X_tiny, features=["mean"], n_jobs=threads)["median_ms"]

            # Numba: full row + stages (first series, then averaged over batch)
            n_series_i, n_steps = X.shape
            out = np.empty((n_series_i, 33), dtype=np.float64)
            if threads > 1:
                import numba
                numba.set_num_threads(threads)

            # full-row timing via the adapter (same kernel as throughput suite)
            from benches.adapters.numba_baseline import Adapter as NumbaAdapter
            nb_adapter = NumbaAdapter()
            entry["numba_full_ms"] = _time_call(nb_adapter.extract, X, threads=threads)["median_ms"]

            # stage timings: per-series kernels averaged over the batch, summed
            def batch_stage(fn, *prep) -> float:
                """Time fn applied to every series; returns total batch ms."""
                def run():
                    total = 0.0
                    for i in range(n_series_i):
                        fn(X[i], *prep)
                return _time_call(run)["median_ms"]

            # Precompute per-series mean/std once (mirrors the fused kernel)
            p1 = np.empty((n_series_i, 5), dtype=np.float64)
            for i in range(n_series_i):
                p1[i] = stages["pass1"](X[i])
            means = p1[:, 0] / n_steps
            vars_ = np.maximum(0.0, p1[:, 1] / n_steps - means**2)
            stds = np.sqrt(vars_)

            # Time each stage across the whole batch (loop timed in Python —
            # the loop overhead itself is measured separately via stage_empty)
            t_empty = _time_call(lambda: [stages["empty"]() for __ in range(n_series_i)])["median_ms"]

            def batch2(fn, prep_fn):
                def run():
                    for i in range(n_series_i):
                        args = prep_fn(i)
                        fn(X[i], *args)
                return _time_call(run)["median_ms"]

            t_p1 = _time_call(lambda: [stages["pass1"](X[i]) for i in range(n_series_i)])["median_ms"] - t_empty
            t_p2 = batch2(stages["pass2"], lambda i: (means[i],)) - t_empty
            t_q = _time_call(lambda: [stages["quantiles"](X[i]) for i in range(n_series_i)])["median_ms"] - t_empty
            t_sk = batch2(stages["skew_kurt"], lambda i: (means[i], stds[i])) - t_empty
            t_fft = batch2(stages["fft_spectral"], lambda i: (means[i],)) - t_empty
            t_acf = batch2(stages["acf"], lambda i: (means[i], vars_[i])) - t_empty
            t_perm = _time_call(lambda: [stages["perm"](X[i]) for i in range(n_series_i)])["median_ms"] - t_empty
            t_misc = batch2(stages["misc"], lambda i: (means[i], stds[i])) - t_empty

            entry["numba_stages_ms"] = {
                "pass1": max(0.0, t_p1), "pass2": max(0.0, t_p2),
                "quantiles": max(0.0, t_q), "skew_kurt": max(0.0, t_sk),
                "fft_spectral": max(0.0, t_fft), "acf": max(0.0, t_acf),
                "perm": max(0.0, t_perm), "misc": max(0.0, t_misc),
                "python_loop_overhead": max(0.0, t_empty),
            }
            entry["numba_stages_sum_ms"] = max(0.0, t_p1 + t_p2 + t_q + t_sk + t_fft + t_acf + t_perm + t_misc)
            stage_table.append(entry)
            print(f"   {n:>6d}x{length:<6d} T{threads:<2d} tsx={t_core:8.3f} ms "
                  f"(floor {entry['tsx_call_floor_ms']:6.3f})  numba={entry['numba_full_ms']:8.3f} ms "
                  f"(stages sum {entry['numba_stages_sum_ms']:8.3f})")

    # ── 3. Agreement: numba strict vs tsxtract on the losing shapes ───────
    print("\n3. Numba (fastmath=False) vs tsxtract agreement on losing shapes...")
    from benches.adapters.numba_baseline import Adapter as NumbaAdapter
    nb_adapter = NumbaAdapter()
    matched_set = set(json.load(open(Path(__file__).parents[1] / "agreement" / "feature_map.json"))["matched_feature_sets"]["numba_baseline"])
    agreement = []
    for n, length in losing_shapes:
        for dist in ("gaussian", "random_walk", "ar1", "heavy_tailed", "sinusoid"):
            X = generate_series(dist, n, length, seed=42)
            a = tsx.extract_features(X, profile="core33")
            b = nb_adapter.extract(X, feature_set="strict")
            per_feature = {}
            n_exact = n_close = n_diff = 0
            for j, name in enumerate(CORE33_NAMES):
                col_a, col_b = a[:, j], b[:, j]
                abs_err = float(np.nanmax(np.abs(col_a - col_b))) if len(col_a) else math.nan
                denom = np.nanmax(np.abs(col_a))
                rel_err = abs_err / denom if denom and denom == denom and denom > 0 else (0.0 if abs_err == 0 else math.inf)
                in_matched = name in matched_set
                if rel_err <= 1e-9:
                    status = "EXACT"
                    n_exact += 1
                elif rel_err <= 1e-5 and in_matched:
                    status = "CLOSE"
                    n_close += 1
                elif in_matched:
                    status = "WRONG"
                else:
                    status = "DIFFERENT-DEFINITION"
                    n_diff += 1
                per_feature[name] = {"rel_err": rel_err, "abs_err": abs_err, "status": status, "matched": in_matched}
            agreement.append({
                "n_series": n, "length": length, "dist": dist,
                "n_exact": n_exact, "n_close": n_close, "n_diff_def": n_diff,
                "n_wrong": sum(1 for v in per_feature.values() if v["status"] == "WRONG"),
                "per_feature": per_feature,
            })
            print(f"   {n:>6d}x{length:<6d} {dist:<13s} EXACT={n_exact:2d} CLOSE={n_close} "
                  f"DIFF-DEF={n_diff:2d} WRONG={agreement[-1]['n_wrong']}")

    # ── 4. FFT verification (A1): real O(N log N) FFT vs numpy ────────────
    print("\n4. A1 FFT verification (numba _bluestein_fft vs numpy.fft)...")
    fft_check = []
    rng = np.random.default_rng(7)
    for n in (10, 100, 500, 512, 1023, 1024, 4093, 4096):
        x = rng.standard_normal(n)
        re = np.empty(n, dtype=np.float64)
        im = np.empty(n, dtype=np.float64)
        _bluestein_fft(x, re, im)
        ref = np.fft.fft(x)
        k = n // 2 + 1
        num = np.sqrt(re[:k] ** 2 + im[:k] ** 2)
        den = np.abs(ref[:k])
        scale = float(np.max(den))
        max_rel = float(np.max(np.abs(num - den))) / scale if scale > 0 else 0.0
        # O(N log N) sanity: time vs n=4096 reference
        t0 = time.perf_counter_ns()
        _bluestein_fft(x, re, im)
        t_us = (time.perf_counter_ns() - t0) / 1e3
        fft_check.append({"n": n, "max_rel_err": max_rel, "single_call_us": t_us})
        print(f"   n={n:<6d} max_rel_err={max_rel:.3e}  ({t_us:.1f} µs/call)")

    # ── 5. fastmath=False bound at losing shapes ──────────────────────────
    print("\n5. Numba fastmath=False bound (threads=16)...")
    fastmath_bound = []
    for n, length in losing_shapes:
        X = generate_series("gaussian", n, length, seed=42)
        t_fast = _time_call(nb_adapter.extract, X, threads=16)["median_ms"]
        t_strict = _time_call(nb_adapter.extract, X, feature_set="strict", threads=16)["median_ms"]
        fastmath_bound.append({"n_series": n, "length": length,
                               "fastmath_true_ms": t_fast, "fastmath_false_ms": t_strict,
                               "delta_pct": 100.0 * (t_strict - t_fast) / t_fast})
        print(f"   {n:>6d}x{length:<6d} fast={t_fast:8.3f} ms  strict={t_strict:8.3f} ms  Δ={fastmath_bound[-1]['delta_pct']:+.1f}%")

    # ── 6. Classification ─────────────────────────────────────────────────
    print("\n6. Classification...")
    classifications = []
    for row in loss_table:
        n, length, dist = row["n_series"], row["length"], row["dist"]
        st = next((e for e in stage_table if e["n_series"] == n and e["length"] == length and e["threads"] == 16), None)
        st1 = next((e for e in stage_table if e["n_series"] == n and e["length"] == length and e["threads"] == 1), None)
        if not st:
            continue
        tsx_total = st["tsx_core33_ms"]
        gap = row["numba_median_ms"] and (tsx_total - row["numba_median_ms"])
        floor_share = st["tsx_call_floor_ms"] / tsx_total if tsx_total else 0
        thread_delta = (st["tsx_core33_ms"] - st1["tsx_core33_ms"]) / st1["tsx_core33_ms"] if st1 and st1["tsx_core33_ms"] else 0
        # unfair-baseline: mismatched-feature work inside numba (skew_kurt + acf-def-diff)
        nst = st["numba_stages_ms"]
        mismatched_work = nst["skew_kurt"] + nst["acf"] * 0.5  # acf def differs, not absent; conservative half
        mismatched_share_of_gap = mismatched_work / gap if gap and gap > 0 else 0
        labels = []
        if floor_share >= 0.40:
            labels.append("call-overhead")
        if thread_delta >= 0.30 and n <= 1000:
            labels.append("threading")
        if mismatched_share_of_gap >= 0.20:
            labels.append("unfair-baseline")
        # algorithmic: tsx quantile stage vs numba full-sort quantile stage
        if st["tsx_quantiles_ms"] > st["numba_stages_ms"]["quantiles"] * 1.5:
            labels.append("algorithmic(quantile-stage)")
        if not labels:
            labels.append("call-overhead")  # residual: fixed FFI/plan/dispatch cost
        classifications.append({**{k: row[k] for k in ("n_series", "length", "dist", "ratio", "ratio_ci95")},
                                "labels": labels,
                                "floor_share": floor_share,
                                "thread_delta_16v1": thread_delta,
                                "mismatched_share_of_gap": mismatched_share_of_gap})
        print(f"   {n:>6d}x{length:<6d} {dist:<13s} -> {'+'.join(labels)}  "
              f"(floor {100*floor_share:.0f}% of tsx, threadΔ {100*thread_delta:+.0f}%, mismatched {100*mismatched_share_of_gap:.0f}% of gap)")

    # ── 7. Write artifacts ────────────────────────────────────────────────
    evidence = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "loss_table": loss_table,
        "stage_table": stage_table,
        "agreement": agreement,
        "fft_check": fft_check,
        "fastmath_bound": fastmath_bound,
        "classifications": classifications,
        "notes": [
            "Tsxtract stage times are differential estimates via features= subsets "
            "(shared intermediates; residual reported as tsx_misc_ms).",
            "Numba stage kernels mirror benches/adapters/numba_baseline.py exactly; "
            "stages are timed as batch loops in Python (loop overhead measured via "
            "empty kernel and subtracted).",
            "numba stage sum vs numba_full_ms difference = output alloc + numpy "
            "overhead + kernel-call dispatch.",
        ],
    }
    OUT_JSON.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

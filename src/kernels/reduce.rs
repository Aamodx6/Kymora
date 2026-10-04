//! Fused reduction passes, centered buffer calculations, and dot products.

pub struct Pass1Result {
    pub sum: f64,
    pub min: f64,
    pub max: f64,
    pub abs_energy: f64,
    pub constant: bool,
    pub has_nan: bool,
    pub mean: f64,
    pub first_min_idx: usize,
    pub last_min_idx: usize,
    pub first_max_idx: usize,
    pub last_max_idx: usize,
    pub min_count: usize,
    pub max_count: usize,
}

/// Fused Pass 1 over series `x`:
/// Computes sum, min, max, abs_energy, constancy, and NaN detection in one read.
#[inline]
pub fn pass1(x: &[f64]) -> Pass1Result {
    let n = x.len();
    if n == 0 {
        return Pass1Result {
            sum: 0.0,
            min: f64::NAN,
            max: f64::NAN,
            abs_energy: 0.0,
            constant: true,
            has_nan: false,
            mean: f64::NAN,
            first_min_idx: 0,
            last_min_idx: 0,
            first_max_idx: 0,
            last_max_idx: 0,
            min_count: 0,
            max_count: 0,
        };
    }

    let first = x[0];
    let mut sum = 0.0f64;
    let mut abs_energy = 0.0f64;
    let mut min = first;
    let mut max = first;
    let mut constant = true;
    let mut has_nan = false;
    let mut first_min_idx = 0usize;
    let mut last_min_idx = 0usize;
    let mut first_max_idx = 0usize;
    let mut last_max_idx = 0usize;
    let mut min_count = 0usize;
    let mut max_count = 0usize;

    for (i, &v) in x.iter().enumerate() {
        sum += v;
        abs_energy += v * v;
        if v < min {
            min = v;
            first_min_idx = i;
            last_min_idx = i;
            min_count = 1;
        } else if v == min {
            last_min_idx = i;
            min_count += 1;
        }
        if v > max {
            max = v;
            first_max_idx = i;
            last_max_idx = i;
            max_count = 1;
        } else if v == max {
            last_max_idx = i;
            max_count += 1;
        }
        constant &= v == first;
        has_nan |= v.is_nan();
    }

    let mean = sum / (n as f64);
    Pass1Result {
        sum,
        min,
        max,
        abs_energy,
        constant,
        has_nan,
        mean,
        first_min_idx,
        last_min_idx,
        first_max_idx,
        last_max_idx,
        min_count,
        max_count,
    }
}

/// Fused Pass 1 over f32 series `x`:
#[inline]
pub fn pass1_f32(x: &[f32]) -> Pass1Result {
    let n = x.len();
    if n == 0 {
        return Pass1Result {
            sum: 0.0,
            min: f64::NAN,
            max: f64::NAN,
            abs_energy: 0.0,
            constant: true,
            has_nan: false,
            mean: f64::NAN,
            first_min_idx: 0,
            last_min_idx: 0,
            first_max_idx: 0,
            last_max_idx: 0,
            min_count: 0,
            max_count: 0,
        };
    }

    let first = x[0] as f64;
    let mut sum = 0.0f64;
    let mut abs_energy = 0.0f64;
    let mut min = first;
    let mut max = first;
    let mut constant = true;
    let mut has_nan = false;
    let mut first_min_idx = 0usize;
    let mut last_min_idx = 0usize;
    let mut first_max_idx = 0usize;
    let mut last_max_idx = 0usize;
    let mut min_count = 0usize;
    let mut max_count = 0usize;

    for (i, &v_raw) in x.iter().enumerate() {
        let v = v_raw as f64;
        sum += v;
        abs_energy += v * v;
        if v < min {
            min = v;
            first_min_idx = i;
            last_min_idx = i;
            min_count = 1;
        } else if v == min {
            last_min_idx = i;
            min_count += 1;
        }
        if v > max {
            max = v;
            first_max_idx = i;
            last_max_idx = i;
            max_count = 1;
        } else if v == max {
            last_max_idx = i;
            max_count += 1;
        }
        constant &= v_raw == x[0];
        has_nan |= v_raw.is_nan();
    }

    let mean = sum / (n as f64);
    Pass1Result {
        sum,
        min,
        max,
        abs_energy,
        constant,
        has_nan,
        mean,
        first_min_idx,
        last_min_idx,
        first_max_idx,
        last_max_idx,
        min_count,
        max_count,
    }
}

pub struct FusedPass2Result {
    pub m2: f64,
    pub m3: f64,
    pub m4: f64,
    pub var: f64,
    pub std: f64,
    pub skewness: f64,
    pub kurtosis: f64,
    pub zero_crossings: f64,
    pub mean_crossings: f64,
    pub strike_above: f64,
    pub strike_below: f64,
    pub count_above_mean: f64,
    pub count_below_mean: f64,
}

/// Fused Pass 2: writes `centered` buffer into `out_centered` and computes
/// m2, m3, m4, zero/mean crossings, and strikes above/below in a single traversal.
#[inline]
pub fn pass2_fused(
    x: &[f64],
    mean: f64,
    constant: bool,
    out_centered: &mut Vec<f64>,
) -> FusedPass2Result {
    let n = x.len();
    let nf = n as f64;

    out_centered.clear();
    out_centered.reserve(n);

    let mut m2 = 0.0f64;
    let mut m3 = 0.0f64;
    let mut m4 = 0.0f64;

    let mut zero_crossings = 0usize;
    let mut mean_crossings = 0usize;
    let mut above_best = 0usize;
    let mut above_run = 0usize;
    let mut below_best = 0usize;
    let mut below_run = 0usize;
    let mut count_above = 0usize;
    let mut count_below = 0usize;

    let mut prev_above_zero = false;
    let mut prev_above_mean = false;

    for (i, &v) in x.iter().enumerate() {
        let d = v - mean;
        out_centered.push(d);

        let d2 = d * d;
        m2 += d2;
        m3 += d2 * d;
        m4 += d2 * d2;

        let above_zero = v > 0.0;
        let above_mean = d > 0.0;
        let below_mean = d < 0.0;

        count_above += above_mean as usize;
        count_below += below_mean as usize;

        if i > 0 {
            zero_crossings += (above_zero != prev_above_zero) as usize;
            mean_crossings += (above_mean != prev_above_mean) as usize;
        }
        prev_above_zero = above_zero;
        prev_above_mean = above_mean;

        if above_mean {
            above_run += 1;
            above_best = above_best.max(above_run);
        } else {
            above_run = 0;
        }

        if below_mean {
            below_run += 1;
            below_best = below_best.max(below_run);
        } else {
            below_run = 0;
        }
    }

    let var = if constant { 0.0 } else { m2 / nf };
    let std = var.sqrt();

    let skewness = if std == 0.0 {
        f64::NAN
    } else {
        (m3 / nf) / (var * std)
    };

    let kurtosis = if std == 0.0 {
        f64::NAN
    } else {
        (m4 / nf) / (var * var) - 3.0
    };

    FusedPass2Result {
        m2,
        m3,
        m4,
        var,
        std,
        skewness,
        kurtosis,
        zero_crossings: zero_crossings as f64,
        mean_crossings: mean_crossings as f64,
        strike_above: above_best as f64,
        strike_below: below_best as f64,
        count_above_mean: count_above as f64,
        count_below_mean: count_below as f64,
    }
}

/// Fused Pass 2 over f32 series `x`.
#[inline]
pub fn pass2_fused_f32(
    x: &[f32],
    mean: f64,
    constant: bool,
    out_centered: &mut Vec<f64>,
) -> FusedPass2Result {
    let n = x.len();
    let nf = n as f64;

    out_centered.clear();
    out_centered.reserve(n);

    let mut m2 = 0.0f64;
    let mut m3 = 0.0f64;
    let mut m4 = 0.0f64;

    let mut zero_crossings = 0usize;
    let mut mean_crossings = 0usize;
    let mut above_best = 0usize;
    let mut above_run = 0usize;
    let mut below_best = 0usize;
    let mut below_run = 0usize;
    let mut count_above = 0usize;
    let mut count_below = 0usize;

    let mut prev_above_zero = false;
    let mut prev_above_mean = false;

    for (i, &v_raw) in x.iter().enumerate() {
        let v = v_raw as f64;
        let d = v - mean;
        out_centered.push(d);

        let d2 = d * d;
        m2 += d2;
        m3 += d2 * d;
        m4 += d2 * d2;

        let above_zero = v_raw > 0.0;
        let above_mean = d > 0.0;
        let below_mean = d < 0.0;

        count_above += above_mean as usize;
        count_below += below_mean as usize;

        if i > 0 {
            zero_crossings += (above_zero != prev_above_zero) as usize;
            mean_crossings += (above_mean != prev_above_mean) as usize;
        }
        prev_above_zero = above_zero;
        prev_above_mean = above_mean;

        if above_mean {
            above_run += 1;
            above_best = above_best.max(above_run);
        } else {
            above_run = 0;
        }

        if below_mean {
            below_run += 1;
            below_best = below_best.max(below_run);
        } else {
            below_run = 0;
        }
    }

    let var = if constant { 0.0 } else { m2 / nf };
    let std = var.sqrt();

    let skewness = if std == 0.0 {
        f64::NAN
    } else {
        (m3 / nf) / (var * std)
    };

    let kurtosis = if std == 0.0 {
        f64::NAN
    } else {
        (m4 / nf) / (var * var) - 3.0
    };

    FusedPass2Result {
        m2,
        m3,
        m4,
        var,
        std,
        skewness,
        kurtosis,
        zero_crossings: zero_crossings as f64,
        mean_crossings: mean_crossings as f64,
        strike_above: above_best as f64,
        strike_below: below_best as f64,
        count_above_mean: count_above as f64,
        count_below_mean: count_below as f64,
    }
}

/// Count of indices `i` where ``x[i]`` is strictly greater than all neighbors within `support`.
#[inline]
pub fn number_of_peaks(x: &[f64], support: usize) -> f64 {
    let n = x.len();
    if n < 2 * support + 1 {
        return 0.0;
    }
    let mut count = 0usize;
    for i in support..n - support {
        let v = x[i];
        let mut peak = true;
        for d in 1..=support {
            peak &= (v > x[i - d]) & (v > x[i + d]);
        }
        count += peak as usize;
    }
    count as f64
}

/// Count of indices `i` where ``x[i]`` is strictly greater than all neighbors within `support` (f32).
#[inline]
pub fn number_of_peaks_f32(x: &[f32], support: usize) -> f64 {
    let n = x.len();
    if n < 2 * support + 1 {
        return 0.0;
    }
    let mut count = 0usize;
    for i in support..n - support {
        let v = x[i];
        let mut peak = true;
        for d in 1..=support {
            peak &= (v > x[i - d]) & (v > x[i + d]);
        }
        count += peak as usize;
    }
    count as f64
}

/// Autocorrelation at lags [1, 2, 5, 10] in a single pass over the centered buffer.
#[inline]
pub fn autocorr_multi(centered: &[f64], var: f64) -> [f64; 4] {
    let lags = [1usize, 2, 5, 10];
    let n = centered.len();
    let mut acc = [0.0f64; 4];
    if var != 0.0 && n > 1 {
        let max_lag = 10;
        let body = n.saturating_sub(max_lag);
        for i in 0..body {
            let d = centered[i];
            acc[0] += d * centered[i + 1];
            acc[1] += d * centered[i + 2];
            acc[2] += d * centered[i + 5];
            acc[3] += d * centered[i + 10];
        }
        for i in body..n {
            let d = centered[i];
            if i + 1 < n {
                acc[0] += d * centered[i + 1];
            }
            if i + 2 < n {
                acc[1] += d * centered[i + 2];
            }
            if i + 5 < n {
                acc[2] += d * centered[i + 5];
            }
            if i + 10 < n {
                acc[3] += d * centered[i + 10];
            }
        }
    }

    let mut out = [f64::NAN; 4];
    for (o, (&k, &a)) in out.iter_mut().zip(lags.iter().zip(acc.iter())) {
        if n > k && var != 0.0 {
            *o = a / ((n - k) as f64 * var);
        }
    }
    out
}

/// Least-squares linear trend slope and r2 vs index t = 0..n-1.
#[inline]
pub fn linear_trend(centered: &[f64], var: f64) -> (f64, f64) {
    let n = centered.len();
    if n < 2 {
        return (f64::NAN, f64::NAN);
    }
    let nf = n as f64;
    let t_mean = (nf - 1.0) / 2.0;
    let t_var = (nf * nf - 1.0) / 12.0;

    let cov: f64 = centered
        .iter()
        .enumerate()
        .map(|(i, &d)| (i as f64 - t_mean) * d)
        .sum::<f64>()
        / nf;

    let slope = cov / t_var;
    if var == 0.0 {
        return (0.0, f64::NAN);
    }
    let r = cov / (t_var.sqrt() * var.sqrt());
    (slope, r * r)
}

/// Differences features: mean_abs_change, mean_change, cid_ce, mean_second_derivative_central.
#[inline]
pub fn successive_differences(x: &[f64], std: f64) -> (f64, f64, f64, f64) {
    let n = x.len();
    let nf = n as f64;

    if n < 2 {
        return (f64::NAN, f64::NAN, f64::NAN, f64::NAN);
    }

    let mut abs_change = 0.0f64;
    let mut scaled_sq = 0.0f64;

    if std == 0.0 {
        for pair in x.windows(2) {
            abs_change += (pair[1] - pair[0]).abs();
        }
    } else {
        for pair in x.windows(2) {
            let d = pair[1] - pair[0];
            abs_change += d.abs();
            let s = d / std;
            scaled_sq += s * s;
        }
    }

    let mean_abs_change = abs_change / (nf - 1.0);
    let mean_change = (x[n - 1] - x[0]) / (nf - 1.0);
    let cid_ce = if std == 0.0 { 0.0 } else { scaled_sq.sqrt() };

    let mean_second_derivative = if n < 3 {
        f64::NAN
    } else {
        let s: f64 = x.windows(3).map(|w| w[2] - 2.0 * w[1] + w[0]).sum();
        s / (2.0 * (nf - 2.0))
    };

    (mean_abs_change, mean_change, cid_ce, mean_second_derivative)
}

/// Differences features for f32 series.
#[inline]
pub fn successive_differences_f32(x: &[f32], std: f64) -> (f64, f64, f64, f64) {
    let n = x.len();
    let nf = n as f64;

    if n < 2 {
        return (f64::NAN, f64::NAN, f64::NAN, f64::NAN);
    }

    let mut abs_change = 0.0f64;
    let mut scaled_sq = 0.0f64;

    if std == 0.0 {
        for pair in x.windows(2) {
            abs_change += ((pair[1] - pair[0]) as f64).abs();
        }
    } else {
        for pair in x.windows(2) {
            let d = (pair[1] - pair[0]) as f64;
            abs_change += d.abs();
            let s = d / std;
            scaled_sq += s * s;
        }
    }

    let mean_abs_change = abs_change / (nf - 1.0);
    let mean_change = (x[n - 1] - x[0]) as f64 / (nf - 1.0);
    let cid_ce = if std == 0.0 { 0.0 } else { scaled_sq.sqrt() };

    let mean_second_derivative = if n < 3 {
        f64::NAN
    } else {
        let s: f64 = x
            .windows(3)
            .map(|w| (w[2] - 2.0 * w[1] + w[0]) as f64)
            .sum();
        s / (2.0 * (nf - 2.0))
    };

    (mean_abs_change, mean_change, cid_ce, mean_second_derivative)
}

pub struct DiffsResult {
    pub mean_abs_change: f64,
    pub mean_change: f64,
    pub cid_ce_norm: f64,
    pub mean_second_derivative: f64,
    pub cid_ce_raw: f64,
    pub abs_sum_changes: f64,
}

#[inline]
pub fn diffs_full(x: &[f64], std: f64) -> DiffsResult {
    let n = x.len();
    let nf = n as f64;
    if n < 2 {
        return DiffsResult {
            mean_abs_change: f64::NAN,
            mean_change: f64::NAN,
            cid_ce_norm: f64::NAN,
            mean_second_derivative: f64::NAN,
            cid_ce_raw: f64::NAN,
            abs_sum_changes: f64::NAN,
        };
    }

    let mut abs_change = 0.0f64;
    let mut raw_sq = 0.0f64;
    for pair in x.windows(2) {
        let d = pair[1] - pair[0];
        abs_change += d.abs();
        raw_sq += d * d;
    }

    let mean_abs_change = abs_change / (nf - 1.0);
    let mean_change = (x[n - 1] - x[0]) / (nf - 1.0);
    let cid_ce_raw = raw_sq.sqrt();
    let cid_ce_norm = if std == 0.0 { 0.0 } else { cid_ce_raw / std };

    let mean_second_derivative = if n < 3 {
        f64::NAN
    } else {
        let s: f64 = x.windows(3).map(|w| w[2] - 2.0 * w[1] + w[0]).sum();
        s / (2.0 * (nf - 2.0))
    };

    DiffsResult {
        mean_abs_change,
        mean_change,
        cid_ce_norm,
        mean_second_derivative,
        cid_ce_raw,
        abs_sum_changes: abs_change,
    }
}

/// Autocorrelation at lags 0..9 (10 values).
#[inline]
pub fn autocorr_10(centered: &[f64], var: f64) -> [f64; 10] {
    let mut out = [f64::NAN; 10];
    let n = centered.len();
    if n == 0 || var == 0.0 {
        return out;
    }
    out[0] = 1.0;
    for lag in 1..10 {
        if n > lag {
            let mut dot = 0.0f64;
            for i in 0..n - lag {
                dot += centered[i] * centered[i + lag];
            }
            out[lag] = dot / ((n - lag) as f64 * var);
        }
    }
    out
}

/// Durbin-Levinson partial autocorrelation for lags 1..9 from 10 autocorrelation values (r0..r9).
#[inline]
pub fn pacf_9(acf: &[f64; 10]) -> [f64; 9] {
    let mut pacf = [f64::NAN; 9];
    if acf[0].is_nan() || acf[1].is_nan() {
        return pacf;
    }
    let mut phi = [[0.0f64; 10]; 10];
    phi[1][1] = acf[1];
    pacf[0] = acf[1];

    for m in 2..10 {
        let mut num = acf[m];
        let mut denom = 1.0f64;
        for j in 1..m {
            num -= phi[m - 1][j] * acf[m - j];
            denom -= phi[m - 1][j] * acf[j];
        }
        if denom.abs() < 1e-15 {
            break;
        }
        let val = num / denom;
        phi[m][m] = val;
        pacf[m - 1] = val;
        for j in 1..m {
            phi[m][j] = phi[m - 1][j] - val * phi[m - 1][m - j];
        }
    }
    pacf
}

/// Full linear trend: (slope, intercept, rvalue, stderr).
#[inline]
pub fn linear_trend_full(centered: &[f64], var: f64, mean: f64) -> (f64, f64, f64, f64) {
    let n = centered.len();
    if n < 2 {
        return (f64::NAN, f64::NAN, f64::NAN, f64::NAN);
    }
    let nf = n as f64;
    let t_mean = (nf - 1.0) * 0.5;
    let mut cov_tx = 0.0f64;
    for (i, &d) in centered.iter().enumerate() {
        cov_tx += (i as f64 - t_mean) * d;
    }
    let var_t = (nf * nf - 1.0) / 12.0;
    let sum_t2 = nf * var_t;
    let slope = cov_tx / sum_t2;
    let intercept = mean - slope * t_mean;
    let std_t = var_t.sqrt();
    let std_x = var.sqrt();
    let rvalue = if std_t > 0.0 && std_x > 0.0 {
        (cov_tx / nf) / (std_t * std_x)
    } else {
        0.0
    };
    let stderr = if n > 2 && var > 0.0 {
        let ss_tot = nf * var;
        let ss_reg = slope * slope * sum_t2;
        let ss_res = (ss_tot - ss_reg).max(0.0);
        (ss_res / ((nf - 2.0) * sum_t2)).sqrt()
    } else {
        f64::NAN
    };
    (slope, intercept, rvalue, stderr)
}

/// c3 nonlinear statistic: ``mean(x[i] * x[i+lag] * x[i+2*lag])``.
#[inline]
pub fn c3(x: &[f64], lag: usize) -> f64 {
    let n = x.len();
    if n <= 2 * lag {
        return f64::NAN;
    }
    let valid_len = n - 2 * lag;
    let mut sum = 0.0f64;
    for i in 0..valid_len {
        sum += x[i] * x[i + lag] * x[i + 2 * lag];
    }
    sum / (valid_len as f64)
}

/// Time reversal asymmetry statistic: ``mean(x[i+2*lag]^2 * x[i+lag] - x[i+lag] * x[i]^2)``.
#[inline]
pub fn time_reversal_asymmetry_statistic(x: &[f64], lag: usize) -> f64 {
    let n = x.len();
    if n <= 2 * lag {
        return f64::NAN;
    }
    let valid_len = n - 2 * lag;
    let mut sum = 0.0f64;
    for i in 0..valid_len {
        let xi = x[i];
        let x_lag = x[i + lag];
        let x_2lag = x[i + 2 * lag];
        sum += x_2lag * x_2lag * x_lag - x_lag * xi * xi;
    }
    sum / (valid_len as f64)
}

/// Threshold crossings count for arbitrary threshold m.
#[inline]
pub fn number_crossing_m(x: &[f64], m: f64) -> f64 {
    let n = x.len();
    if n < 2 {
        return 0.0;
    }
    let mut count = 0usize;
    let mut prev = x[0] > m;
    for &v in &x[1..] {
        let curr = v > m;
        count += (curr != prev) as usize;
        prev = curr;
    }
    count as f64
}

/// Ratio of points beyond r * sigma from mean.
#[inline]
pub fn ratio_beyond_r_sigma(centered: &[f64], std: f64, r: f64) -> f64 {
    let n = centered.len();
    if n == 0 || std == 0.0 {
        return 0.0;
    }
    let threshold = r * std;
    let count = centered.iter().filter(|&&d| d.abs() > threshold).count();
    (count as f64) / (n as f64)
}

/// Energy ratio of chunk `chunk_idx` of `num_chunks`.
#[inline]
pub fn energy_ratio_chunk(
    x: &[f64],
    total_energy: f64,
    chunk_idx: usize,
    num_chunks: usize,
) -> f64 {
    let n = x.len();
    if total_energy == 0.0 || n == 0 || chunk_idx >= num_chunks || num_chunks == 0 {
        return f64::NAN;
    }
    let q = n / num_chunks;
    let r = n % num_chunks;
    let (start, end) = if chunk_idx < r {
        (chunk_idx * (q + 1), (chunk_idx + 1) * (q + 1))
    } else {
        (
            r * (q + 1) + (chunk_idx - r) * q,
            r * (q + 1) + (chunk_idx - r + 1) * q,
        )
    };
    if start >= end || start >= n {
        return 0.0;
    }
    let mut seg_energy = 0.0f64;
    for &v in &x[start..end.min(n)] {
        seg_energy += v * v;
    }
    seg_energy / total_energy
}

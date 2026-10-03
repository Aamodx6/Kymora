//! Quantiles and order statistics implementations.

pub const QUANTILE_LEVELS: [f64; 5] = [0.50, 0.10, 0.25, 0.75, 0.90];
const MAX_STATS: usize = 2 * QUANTILE_LEVELS.len();

/// Compute quantiles using partition selection into `buf`.
#[inline]
pub fn quantiles(x: &[f64], buf: &mut Vec<f64>) -> [f64; 5] {
    buf.clear();
    buf.extend_from_slice(x);
    quantiles_select(buf)
}

/// Compute quantiles for f32 series using partition selection into scratch buffer.
#[inline]
pub fn quantiles_f32(x: &[f32], buf: &mut Vec<f64>) -> [f64; 5] {
    buf.clear();
    buf.extend(x.iter().map(|&v| v as f64));
    quantiles_select(buf)
}

/// Recursive selection strategy on mutable slice (identical to baseline).
#[inline]
pub fn quantiles_select(buf: &mut [f64]) -> [f64; 5] {
    let n = buf.len();
    if n == 0 {
        return [f64::NAN; 5];
    }
    if n == 1 {
        return [buf[0]; 5];
    }

    let mut ranks = [0usize; MAX_STATS];
    let mut count = 0usize;
    let push = |k: usize, ranks: &mut [usize; MAX_STATS], count: &mut usize| {
        let mut i = 0;
        while i < *count {
            if ranks[i] == k {
                return;
            }
            if ranks[i] > k {
                break;
            }
            i += 1;
        }
        let mut j = *count;
        while j > i {
            ranks[j] = ranks[j - 1];
            j -= 1;
        }
        ranks[i] = k;
        *count += 1;
    };
    for &q in &QUANTILE_LEVELS {
        let pos = q * (n - 1) as f64;
        push(pos.floor() as usize, &mut ranks, &mut count);
        push(pos.ceil() as usize, &mut ranks, &mut count);
    }

    let mut values = [0.0f64; MAX_STATS];
    select_ranks(buf, 0, &ranks[..count], &mut values[..count]);

    let at = |k: usize| match ranks[..count].binary_search(&k) {
        Ok(i) => values[i],
        Err(_) => f64::NAN,
    };

    let mut out = [0.0f64; 5];
    for (slot, &q) in out.iter_mut().zip(QUANTILE_LEVELS.iter()) {
        let pos = q * (n - 1) as f64;
        let lo = pos.floor() as usize;
        let hi = pos.ceil() as usize;
        let frac = pos - lo as f64;
        let lo_v = at(lo);
        *slot = lo_v + (at(hi) - lo_v) * frac;
    }
    out
}

fn select_ranks(buf: &mut [f64], offset: usize, ranks: &[usize], values: &mut [f64]) {
    if ranks.is_empty() {
        return;
    }
    let mid = ranks.len() / 2;
    let rank = ranks[mid];
    let local = rank - offset;
    let (left, pivot, right) = buf.select_nth_unstable_by(local, f64::total_cmp);
    values[mid] = *pivot;
    select_ranks(left, offset, &ranks[..mid], &mut values[..mid]);
    select_ranks(right, rank + 1, &ranks[mid + 1..], &mut values[mid + 1..]);
}

/// Compute quantiles from an already sorted slice.
#[inline]
pub fn quantiles_from_sorted(sorted: &[f64]) -> [f64; 5] {
    let n = sorted.len();
    if n == 0 {
        return [f64::NAN; 5];
    }
    if n == 1 {
        return [sorted[0]; 5];
    }

    let mut out = [0.0f64; 5];
    let nf_sub_1 = (n - 1) as f64;

    for (slot, &q) in out.iter_mut().zip(QUANTILE_LEVELS.iter()) {
        let pos = q * nf_sub_1;
        let lo = pos.floor() as usize;
        let hi = pos.ceil() as usize;
        let frac = pos - (lo as f64);
        let lo_v = sorted[lo];
        let hi_v = sorted[hi];
        *slot = lo_v + (hi_v - lo_v) * frac;
    }
    out
}

pub const DECILE_LEVELS: [f64; 9] = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90];

/// Compute 9 deciles from an already sorted slice.
#[inline]
pub fn deciles_from_sorted(sorted: &[f64]) -> [f64; 9] {
    let n = sorted.len();
    if n == 0 {
        return [f64::NAN; 9];
    }
    if n == 1 {
        return [sorted[0]; 9];
    }
    let mut out = [0.0f64; 9];
    let nf_sub_1 = (n - 1) as f64;
    for (slot, &q) in out.iter_mut().zip(DECILE_LEVELS.iter()) {
        let pos = q * nf_sub_1;
        let lo = pos.floor() as usize;
        let hi = pos.ceil() as usize;
        let frac = pos - (lo as f64);
        let lo_v = sorted[lo];
        let hi_v = sorted[hi];
        *slot = lo_v + (hi_v - lo_v) * frac;
    }
    out
}

/// Check if there are any duplicate values in the sorted slice.
#[inline]
pub fn has_duplicate_sorted(sorted: &[f64]) -> bool {
    sorted.windows(2).any(|w| w[0] == w[1])
}

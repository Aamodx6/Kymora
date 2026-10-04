//! Quantiles and order statistics implementations.

pub const QUANTILE_LEVELS: [f64; 5] = [0.50, 0.10, 0.25, 0.75, 0.90];
const MAX_STATS: usize = 2 * QUANTILE_LEVELS.len();

#[derive(Clone, Debug)]
pub struct SelScratch {
    pub counts: Vec<u32>,
    pub gather: Vec<f64>,
    pub target: Vec<u64>,
}

impl Default for SelScratch {
    fn default() -> Self {
        Self::new()
    }
}

impl SelScratch {
    pub fn new() -> Self {
        Self {
            counts: vec![0u32; 512],
            gather: Vec::with_capacity(1024),
            target: vec![0u64; 8],
        }
    }

    #[inline]
    pub fn ensure_capacity(&mut self, len: usize) {
        if self.gather.capacity() < len {
            self.gather.reserve(len - self.gather.capacity());
        }
    }
}

/// Histogram multi-select: writes `x_(rank)` into ``out[i]`` for sorted ascending ranks.
pub fn multi_select(
    x: &[f64],
    min: f64,
    max: f64,
    ranks: &[usize],
    sc: &mut SelScratch,
    out: &mut [f64],
) {
    let n = x.len();
    if n == 0 {
        for o in out.iter_mut() {
            *o = f64::NAN;
        }
        return;
    }
    if n == 1 {
        for o in out.iter_mut() {
            *o = x[0];
        }
        return;
    }
    if ranks.is_empty() {
        return;
    }

    if min.partial_cmp(&max) != Some(std::cmp::Ordering::Less) || (max - min).abs() < 1e-15 {
        for o in out.iter_mut() {
            *o = min;
        }
        return;
    }

    if n <= 16 {
        sc.gather.clear();
        sc.gather.extend_from_slice(x);
        for (i, &r) in ranks.iter().enumerate() {
            let r_clamped = r.min(n - 1);
            let (_, val, _) = sc.gather.select_nth_unstable_by(r_clamped, f64::total_cmp);
            out[i] = *val;
        }
        return;
    }

    const B: usize = 512;
    if sc.counts.len() < B {
        sc.counts.resize(B, 0);
    } else {
        sc.counts[..B].fill(0);
    }
    if sc.target.len() < 8 {
        sc.target.resize(8, 0);
    } else {
        sc.target[..8].fill(0);
    }

    let scale = (B - 1) as f64 / (max - min);

    for &val in x {
        let b = if val <= min {
            0
        } else if val >= max {
            B - 1
        } else {
            let idx = ((val - min) * scale) as usize;
            idx.min(B - 1)
        };
        sc.counts[b] += 1;
    }

    let mut prefix_start = [0usize; B];
    let mut cum = 0usize;
    for (b, p) in prefix_start.iter_mut().enumerate() {
        *p = cum;
        cum += sc.counts[b] as usize;
    }

    let mut rank_bucket = [0usize; 32];
    let mut rank_local = [0usize; 32];
    let num_ranks = ranks.len().min(32);

    let mut b_cursor = 0usize;
    for (i, &r) in ranks[..num_ranks].iter().enumerate() {
        let r = r.min(n - 1);
        while b_cursor < B - 1 && prefix_start[b_cursor] + (sc.counts[b_cursor] as usize) <= r {
            b_cursor += 1;
        }
        rank_bucket[i] = b_cursor;
        rank_local[i] = r - prefix_start[b_cursor];
        sc.target[b_cursor / 64] |= 1u64 << (b_cursor % 64);
    }

    let mut gather_offset = [0usize; B];
    let mut total_gather = 0usize;
    for (b, offset) in gather_offset.iter_mut().enumerate() {
        if (sc.target[b / 64] & (1u64 << (b % 64))) != 0 {
            *offset = total_gather;
            total_gather += sc.counts[b] as usize;
        }
    }

    sc.gather.resize(total_gather, 0.0);
    let mut write_pos = gather_offset;

    for &val in x {
        let b = if val <= min {
            0
        } else if val >= max {
            B - 1
        } else {
            let idx = ((val - min) * scale) as usize;
            idx.min(B - 1)
        };
        if (sc.target[b / 64] & (1u64 << (b % 64))) != 0 {
            sc.gather[write_pos[b]] = val;
            write_pos[b] += 1;
        }
    }

    for (b, &start) in gather_offset.iter().enumerate() {
        if (sc.target[b / 64] & (1u64 << (b % 64))) != 0 {
            let count = sc.counts[b] as usize;
            let end = start + count;
            let bucket_slice = &mut sc.gather[start..end];
            if count > 1 {
                bucket_slice.sort_unstable_by(f64::total_cmp);
            }
        }
    }

    for i in 0..num_ranks {
        let b = rank_bucket[i];
        let loc = rank_local[i];
        let start = gather_offset[b];
        out[i] = sc.gather[start + loc];
    }
}

/// Compute quantiles using histogram multi-select.
#[inline]
pub fn quantiles_multi_select(x: &[f64], min: f64, max: f64, sc: &mut SelScratch) -> [f64; 5] {
    let n = x.len();
    if n == 0 {
        return [f64::NAN; 5];
    }
    if n == 1 {
        return [x[0]; 5];
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

    let nf_sub_1 = (n - 1) as f64;
    for &q in &QUANTILE_LEVELS {
        let pos = q * nf_sub_1;
        push(pos.floor() as usize, &mut ranks, &mut count);
        push(pos.ceil() as usize, &mut ranks, &mut count);
    }

    let mut values = [0.0f64; MAX_STATS];
    multi_select(x, min, max, &ranks[..count], sc, &mut values[..count]);

    let at = |k: usize| match ranks[..count].binary_search(&k) {
        Ok(i) => values[i],
        Err(_) => f64::NAN,
    };

    let mut out = [0.0f64; 5];
    for (slot, &q) in out.iter_mut().zip(QUANTILE_LEVELS.iter()) {
        let pos = q * nf_sub_1;
        let lo = pos.floor() as usize;
        let hi = pos.ceil() as usize;
        let frac = pos - lo as f64;
        let lo_v = at(lo);
        *slot = lo_v + (at(hi) - lo_v) * frac;
    }
    out
}

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

/// Compute 9 deciles using histogram multi-select.
#[inline]
pub fn deciles_multi_select(x: &[f64], min: f64, max: f64, sc: &mut SelScratch) -> [f64; 9] {
    let n = x.len();
    if n == 0 {
        return [f64::NAN; 9];
    }
    if n == 1 {
        return [x[0]; 9];
    }

    const MAX_DECILE_STATS: usize = 2 * DECILE_LEVELS.len();
    let mut ranks = [0usize; MAX_DECILE_STATS];
    let mut count = 0usize;
    let push = |k: usize, ranks: &mut [usize; MAX_DECILE_STATS], count: &mut usize| {
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

    let nf_sub_1 = (n - 1) as f64;
    for &q in &DECILE_LEVELS {
        let pos = q * nf_sub_1;
        push(pos.floor() as usize, &mut ranks, &mut count);
        push(pos.ceil() as usize, &mut ranks, &mut count);
    }

    let mut values = [0.0f64; MAX_DECILE_STATS];
    multi_select(x, min, max, &ranks[..count], sc, &mut values[..count]);

    let at = |k: usize| match ranks[..count].binary_search(&k) {
        Ok(i) => values[i],
        Err(_) => f64::NAN,
    };

    let mut out = [0.0f64; 9];
    for (slot, &q) in out.iter_mut().zip(DECILE_LEVELS.iter()) {
        let pos = q * nf_sub_1;
        let lo = pos.floor() as usize;
        let hi = pos.ceil() as usize;
        let frac = pos - (lo as f64);
        let lo_v = at(lo);
        *slot = lo_v + (at(hi) - lo_v) * frac;
    }
    out
}

/// Check if there are any duplicate values in the sorted slice.
#[inline]
pub fn has_duplicate_sorted(sorted: &[f64]) -> bool {
    sorted.windows(2).any(|w| w[0] == w[1])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_multi_select_parity_random() {
        let mut sc = SelScratch::new();
        for &n in &[1, 2, 5, 16, 32, 128, 500, 2000] {
            let x: Vec<f64> = (0..n)
                .map(|i| ((i * 17 + 31) % 1000) as f64 * 0.1)
                .collect();
            let min = x.iter().copied().fold(f64::INFINITY, f64::min);
            let max = x.iter().copied().fold(f64::NEG_INFINITY, f64::max);

            let mut sorted = x.clone();
            sorted.sort_unstable_by(f64::total_cmp);
            let ref_q = quantiles_from_sorted(&sorted);
            let sel_q = quantiles_multi_select(&x, min, max, &mut sc);

            for k in 0..5 {
                assert!(
                    (ref_q[k] - sel_q[k]).abs() < 1e-12,
                    "n={n}, k={k}: ref={}, sel={}",
                    ref_q[k],
                    sel_q[k]
                );
            }
        }
    }

    #[test]
    fn test_multi_select_parity_tied_and_constant() {
        let mut sc = SelScratch::new();
        // Constant
        let x_const = vec![42.0; 500];
        let q_const = quantiles_multi_select(&x_const, 42.0, 42.0, &mut sc);
        assert_eq!(q_const, [42.0; 5]);

        // Heavy ties (only 3 unique values)
        let x_ties: Vec<f64> = (0..500).map(|i| (i % 3) as f64).collect();
        let mut sorted = x_ties.clone();
        sorted.sort_unstable_by(f64::total_cmp);
        let ref_q = quantiles_from_sorted(&sorted);
        let sel_q = quantiles_multi_select(&x_ties, 0.0, 2.0, &mut sc);
        for k in 0..5 {
            assert_eq!(ref_q[k], sel_q[k], "k={k}");
        }
    }

    #[test]
    fn test_multi_select_deciles_parity() {
        let mut sc = SelScratch::new();
        let x: Vec<f64> = (0..500).map(|i| (i as f64).sin() * 100.0).collect();
        let min = x.iter().copied().fold(f64::INFINITY, f64::min);
        let max = x.iter().copied().fold(f64::NEG_INFINITY, f64::max);

        let mut sorted = x.clone();
        sorted.sort_unstable_by(f64::total_cmp);
        let ref_d = deciles_from_sorted(&sorted);
        let sel_d = deciles_multi_select(&x, min, max, &mut sc);

        for k in 0..9 {
            assert!(
                (ref_d[k] - sel_d[k]).abs() < 1e-12,
                "k={k}: ref={}, sel={}",
                ref_d[k],
                sel_d[k]
            );
        }
    }
}

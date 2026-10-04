"""Honest baseline: Numba hand-rolled JIT implementation of the 33 core features.

Features:
- O(N log N) Bluestein chirp-z FFT / Radix-2 iterative FFT for all lengths (no O(N^2) DFT)
- fastmath=True (for throughput) and fastmath=False (strict IEEE 754 for agreement & robustness)
- Supports threads scaling via numba.set_num_threads and prange
"""

from __future__ import annotations

import math
from typing import Any
import numpy as np

from benchmarks.adapters.base import BaseAdapter
from benchmarks.adapters.numpy_baseline import CORE33_NAMES

try:
    import numba
    from numba import njit, prange
    _HAS_NUMBA = True
    _VERSION = getattr(numba, "__version__", "unknown")
except ImportError:
    _HAS_NUMBA = False
    _VERSION = "not_installed"


if _HAS_NUMBA:
    # -------------------------------------------------------------------------
    # Iterative O(N log N) FFT: Radix-2 + Bluestein for non-power-of-2 lengths
    # -------------------------------------------------------------------------
    @njit(fastmath=True)
    def _fft_radix2(re: np.ndarray, im: np.ndarray, inverse: bool) -> None:
        n = len(re)
        j = 0
        for i in range(n):
            if j > i:
                t_re = re[i]; re[i] = re[j]; re[j] = t_re
                t_im = im[i]; im[i] = im[j]; im[j] = t_im
            m = n >> 1
            while m >= 1 and j >= m:
                j -= m
                m >>= 1
            j += m

        s = 2
        while s <= n:
            half = s >> 1
            theta = (-2.0 if not inverse else 2.0) * math.pi / s
            w_re_step = math.cos(theta)
            w_im_step = math.sin(theta)
            for i in range(0, n, s):
                w_re = 1.0
                w_im = 0.0
                for k in range(half):
                    idx_k = i + k
                    idx_half = idx_k + half
                    u_re = re[idx_k]; u_im = im[idx_k]
                    v_re = re[idx_half] * w_re - im[idx_half] * w_im
                    v_im = re[idx_half] * w_im + im[idx_half] * w_re
                    re[idx_k] = u_re + v_re
                    im[idx_k] = u_im + v_im
                    re[idx_half] = u_re - v_re
                    im[idx_half] = u_im - v_im
                    w_next_re = w_re * w_re_step - w_im * w_im_step
                    w_next_im = w_re * w_im_step + w_im * w_re_step
                    w_re = w_next_re
                    w_im = w_next_im
            s <<= 1

        if inverse:
            for i in range(n):
                re[i] /= n
                im[i] /= n

    @njit(fastmath=True)
    def _bluestein_fft(x: np.ndarray, out_re: np.ndarray, out_im: np.ndarray) -> None:
        n = len(x)
        # If already power of 2, directly run radix-2
        if (n & (n - 1)) == 0 and n > 0:
            for i in range(n):
                out_re[i] = x[i]
                out_im[i] = 0.0
            _fft_radix2(out_re, out_im, False)
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

        _fft_radix2(a_re, a_im, False)
        _fft_radix2(b_re, b_im, False)

        c_re = np.zeros(m, dtype=np.float64)
        c_im = np.zeros(m, dtype=np.float64)
        for i in range(m):
            c_re[i] = a_re[i] * b_re[i] - a_im[i] * b_im[i]
            c_im[i] = a_re[i] * b_im[i] + a_im[i] * b_re[i]

        _fft_radix2(c_re, c_im, True)

        for i in range(n):
            angle = -math.pi * (i * i % (2 * n)) / n
            c_val = math.cos(angle)
            s_val = math.sin(angle)
            out_re[i] = c_re[i] * c_val - c_im[i] * s_val
            out_im[i] = c_re[i] * s_val + c_im[i] * c_val

    # -------------------------------------------------------------------------
    # Core 33 kernels (Parameterized by fastmath)
    # -------------------------------------------------------------------------
    def _make_compute_row(fastmath_flag: bool):
        @njit(fastmath=fastmath_flag)
        def _compute_perm_entropy(x: np.ndarray) -> float:
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

        @njit(fastmath=fastmath_flag)
        def _compute_row(x: np.ndarray, out: np.ndarray) -> None:
            n = len(x)
            if n == 0:
                out[:] = np.nan
                return

            # Pass 1: basic moments & reductions
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
                if i > 0:
                    if (x[i - 1] > 0.0) != (v > 0.0):
                        z_cross += 1

            mean = s / n
            var = max(0.0, (sq / n) - (mean * mean))
            if mx == mn:
                var = 0.0
            std = math.sqrt(var)

            out[0] = mean
            out[1] = std
            out[2] = var
            out[3] = mn
            out[4] = mx

            # Quantiles via sorted copy
            sorted_x = np.sort(x)
            out[5] = sorted_x[n // 2] if n % 2 == 1 else 0.5 * (sorted_x[n // 2 - 1] + sorted_x[n // 2])
            for idx, q in [(6, 0.10), (7, 0.25), (8, 0.75), (9, 0.90)]:
                pos = q * (n - 1)
                low = int(pos)
                frac = pos - low
                if low + 1 < n:
                    out[idx] = sorted_x[low] + frac * (sorted_x[low + 1] - sorted_x[low])
                else:
                    out[idx] = sorted_x[low]

            # Pass 2: mean crossings, strikes, peaks
            # (skewness/kurtosis computed via z-scores below to avoid underflow)
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

                if i > 0:
                    if (x[i - 1] > mean) != (x[i] > mean):
                        m_cross += 1

            if std > 0.0:
                # Use z-scores to avoid std^3/std^4 underflow for tiny-scale data.
                # std^3 underflows to 0.0 for std < ~7e-109, causing ZeroDivisionError.
                inv_std = 1.0 / std
                z3_sum = 0.0
                z4_sum = 0.0
                for i in range(n):
                    z = (x[i] - mean) * inv_std
                    z2 = z * z
                    z3_sum += z2 * z
                    z4_sum += z2 * z2
                out[10] = z3_sum / n          # skewness
                out[11] = z4_sum / n - 3.0    # excess kurtosis
            else:
                out[10] = np.nan
                out[11] = np.nan

            out[12] = sq
            out[13] = math.sqrt(sq / n)

            # Differences
            if n >= 2:
                abs_change_sum = 0.0
                cid_sum = 0.0
                for i in range(1, n):
                    diff = x[i] - x[i - 1]
                    abs_change_sum += abs(diff)
                    cid_sum += diff * diff

                out[14] = abs_change_sum / (n - 1)
                out[15] = (x[n - 1] - x[0]) / (n - 1)
                out[16] = math.sqrt(cid_sum) / std if std > 0.0 else 0.0
            else:
                out[14] = np.nan
                out[15] = np.nan
                out[16] = np.nan

            # Central second derivative
            if n >= 3:
                d2_sum = 0.0
                for i in range(1, n - 1):
                    d2_sum += x[i + 1] - 2.0 * x[i] + x[i - 1]
                out[17] = d2_sum / (2.0 * (n - 2))
            else:
                out[17] = np.nan

            out[18] = float(z_cross)
            out[19] = float(m_cross)

            # Peaks (support = 3)
            peaks = 0
            if n >= 7:
                for i in range(3, n - 3):
                    xi = x[i]
                    if (xi > x[i - 1] and xi > x[i + 1] and
                        xi > x[i - 2] and xi > x[i + 2] and
                        xi > x[i - 3] and xi > x[i + 3]):
                        peaks += 1
            out[20] = float(peaks)

            out[21] = float(max_above)
            out[22] = float(max_below)

            # Autocorrelations
            lags = (1, 2, 5, 10)
            for lag_idx in range(4):
                lag = lags[lag_idx]
                col = 23 + lag_idx
                if n > lag and var > 0.0:
                    cov = 0.0
                    for i in range(n - lag):
                        cov += (x[i] - mean) * (x[i + lag] - mean)
                    out[col] = (cov / (n - lag)) / var
                else:
                    out[col] = np.nan

            # Linear trend
            if n >= 2:
                t_m = (n - 1) / 2.0
                s_xx = n * (n * n - 1) / 12.0
                s_xy = 0.0
                for i in range(n):
                    s_xy += (i - t_m) * x[i]
                slope = s_xy / s_xx if s_xx > 0.0 else 0.0
                if mx == mn:
                    slope = 0.0
                out[27] = slope
                if var > 0.0:
                    r2 = (slope * slope * s_xx) / (n * var)
                    out[28] = max(0.0, min(1.0, r2))
                else:
                    out[28] = np.nan
            else:
                out[27] = np.nan
                out[28] = np.nan

            # Permutation entropy
            out[29] = _compute_perm_entropy(x)

            # Spectral features (O(N log N) Bluestein / Radix-2 FFT)
            if n >= 2:
                centered = x - mean
                fft_re = np.empty(n, dtype=np.float64)
                fft_im = np.empty(n, dtype=np.float64)
                _bluestein_fft(centered, fft_re, fft_im)

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

                if tot_p > 0.0 and mx > mn:
                    out[30] = max_idx / n
                    out[31] = centroid_num / tot_p
                    if nbins == 1:
                        out[32] = 0.0
                    else:
                        ent = 0.0
                        for k in range(nbins):
                            p = power_arr[k]
                            if p > 0.0:
                                q = p / tot_p
                                ent -= q * math.log(q)
                        out[32] = ent / math.log(float(nbins))
                else:
                    out[30] = np.nan
                    out[31] = np.nan
                    out[32] = np.nan
            else:
                out[30] = np.nan
                out[31] = np.nan
                out[32] = np.nan

        @njit(parallel=True, fastmath=fastmath_flag)
        def _extract_batch_parallel(X: np.ndarray, out: np.ndarray) -> None:
            n_series = X.shape[0]
            for i in prange(n_series):
                _compute_row(X[i], out[i])

        @njit(fastmath=fastmath_flag)
        def _extract_batch_serial(X: np.ndarray, out: np.ndarray) -> None:
            n_series = X.shape[0]
            for i in range(n_series):
                _compute_row(X[i], out[i])

        return _extract_batch_serial, _extract_batch_parallel

    _extract_serial_fast, _extract_parallel_fast = _make_compute_row(True)
    _extract_serial_strict, _extract_parallel_strict = _make_compute_row(False)


class Adapter(BaseAdapter):
    name = "numba_baseline"
    version = f"numba_{_VERSION}"

    def __init__(self) -> None:
        if _HAS_NUMBA:
            dummy = np.ones((2, 16), dtype=np.float64)
            out_dummy = np.empty((2, 33), dtype=np.float64)
            _extract_serial_fast(dummy, out_dummy)
            _extract_parallel_fast(dummy, out_dummy)
            _extract_serial_strict(dummy, out_dummy)
            _extract_parallel_strict(dummy, out_dummy)

    def feature_names(self, feature_set: str = "default") -> list[str]:
        return list(CORE33_NAMES)

    def extract(
        self,
        X: np.ndarray,
        feature_set: str = "default",
        threads: int = 1,
        **kwargs: Any,
    ) -> np.ndarray:
        if not _HAS_NUMBA:
            raise RuntimeError("Numba is not installed.")

        # Determine fastmath mode:
        # Strict mode used for agreement (B1) and robustness (B4)
        use_fastmath = kwargs.get("fastmath", None)
        if use_fastmath is None:
            use_fastmath = feature_set not in ("strict", "no_fastmath", "agreement", "robustness")

        n_series = X.shape[0]
        out = np.empty((n_series, 33), dtype=np.float64)

        if use_fastmath:
            if threads > 1 and n_series > 1:
                numba.set_num_threads(threads)
                _extract_parallel_fast(X, out)
            else:
                _extract_serial_fast(X, out)
        else:
            if threads > 1 and n_series > 1:
                numba.set_num_threads(threads)
                _extract_parallel_strict(X, out)
            else:
                _extract_serial_strict(X, out)

        return out

    def tune_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "compiler": "LLVM via Numba JIT",
            "fft_algorithm": "O(N log N) Bluestein chirp-z / Radix-2 iterative FFT",
            "fastmath_modes": ["fastmath=True (throughput)", "fastmath=False (strict/agreement/robustness)"],
            "parallelism": "Numba prange work-stealing across series",
        }

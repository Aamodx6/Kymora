"""Scientific domain feature definitions and vectorized calculators."""

from __future__ import annotations

from typing import Dict, List, Set
import numpy as np

# Domain feature banks
STATISTICAL_CORE = [
    "mean", "std", "var", "skewness", "kurtosis",
    "min", "max", "median",
    "quantile_10", "quantile_25", "quantile_75", "quantile_90",
    "quantile__q_0.2", "quantile__q_0.3", "quantile__q_0.4",
    "quantile__q_0.6", "quantile__q_0.7", "quantile__q_0.8",
    "abs_energy", "root_mean_square",
]

STATISTICAL_EXTENDED = [
    "interquartile_range", "peak_to_peak_distance",
    "mean_abs_deviation", "median_abs_deviation",
    "ratio_beyond_r_sigma__r_0.5", "ratio_beyond_r_sigma__r_1", "ratio_beyond_r_sigma__r_1.5",
    "ratio_beyond_r_sigma__r_2", "ratio_beyond_r_sigma__r_2.5", "ratio_beyond_r_sigma__r_3",
    "count_above_mean", "count_below_mean",
    "symmetry_looking",
    "c3__lag_1", "c3__lag_2", "c3__lag_3",
]

STATISTICAL_FEATURES = STATISTICAL_CORE + STATISTICAL_EXTENDED

TEMPORAL_CORE = [
    "zero_crossings", "mean_change", "mean_abs_change",
    "mean_second_derivative_central", "mean_crossings",
    "longest_strike_above_mean", "longest_strike_below_mean",
    "autocorrelation_lag_1", "autocorrelation_lag_2", "autocorrelation_lag_3",
    "autocorrelation_lag_4", "autocorrelation_lag_5",
    "cid_ce",
]

TEMPORAL_EXTENDED = [
    "zero_crossing_rate", "area_under_curve", "signal_distance",
    "positive_turning_points", "negative_turning_points", "total_turning_points",
    "first_location_of_maximum", "first_location_of_minimum",
    "last_location_of_maximum", "last_location_of_minimum",
]

TEMPORAL_FEATURES = TEMPORAL_CORE + TEMPORAL_EXTENDED

SPECTRAL_CORE = [
    "dominant_frequency", "spectral_centroid", "spectral_entropy",
    "fft_aggregated__aggtype_\"centroid\"",
    "fft_aggregated__aggtype_\"variance\"",
    "fft_aggregated__aggtype_\"skew\"",
    "fft_aggregated__aggtype_\"kurtosis\"",
]

SPECTRAL_EXTENDED = [
    "spectral_spread", "spectral_slope", "spectral_decrease",
    "spectral_roll_off", "spectral_roll_on",
    "spectral_skewness", "spectral_kurtosis",
    # Mel-Frequency Cepstral Coefficients (MFCC)
    "mfcc_0", "mfcc_1", "mfcc_2", "mfcc_3", "mfcc_4", "mfcc_5",
    "mfcc_6", "mfcc_7", "mfcc_8", "mfcc_9", "mfcc_10", "mfcc_11",
    # Linear Prediction Cepstral Coefficients (LPCC)
    "lpcc_0", "lpcc_1", "lpcc_2", "lpcc_3", "lpcc_4", "lpcc_5",
    "lpcc_6", "lpcc_7", "lpcc_8", "lpcc_9", "lpcc_10", "lpcc_11",
    # Continuous Wavelet Transform (CWT) features across 9 dyadic scales
    "wavelet_energy_scale_1", "wavelet_energy_scale_2", "wavelet_energy_scale_3",
    "wavelet_energy_scale_4", "wavelet_energy_scale_5", "wavelet_energy_scale_6",
    "wavelet_energy_scale_7", "wavelet_energy_scale_8", "wavelet_energy_scale_9",
    "wavelet_abs_mean_scale_1", "wavelet_abs_mean_scale_2", "wavelet_abs_mean_scale_3",
    "wavelet_abs_mean_scale_4", "wavelet_abs_mean_scale_5", "wavelet_abs_mean_scale_6",
    "wavelet_abs_mean_scale_7", "wavelet_abs_mean_scale_8", "wavelet_abs_mean_scale_9",
    "wavelet_std_scale_1", "wavelet_std_scale_2", "wavelet_std_scale_3",
    "wavelet_std_scale_4", "wavelet_std_scale_5", "wavelet_std_scale_6",
    "wavelet_std_scale_7", "wavelet_std_scale_8", "wavelet_std_scale_9",
    "wavelet_var_scale_1", "wavelet_var_scale_2", "wavelet_var_scale_3",
    "wavelet_var_scale_4", "wavelet_var_scale_5", "wavelet_var_scale_6",
    "wavelet_var_scale_7", "wavelet_var_scale_8", "wavelet_var_scale_9",
    "wavelet_entropy",
]

SPECTRAL_FEATURES = SPECTRAL_CORE + SPECTRAL_EXTENDED

FRACTAL_CORE = ["permutation_entropy"]
FRACTAL_EXTENDED = ["petrosian_fractal_dimension"]
FRACTAL_FEATURES = FRACTAL_CORE + FRACTAL_EXTENDED

ALL_DOMAINS: Dict[str, List[str]] = {
    "statistical": STATISTICAL_FEATURES,
    "temporal": TEMPORAL_FEATURES,
    "spectral": SPECTRAL_FEATURES,
    "fractal": FRACTAL_FEATURES,
}


def compute_derived_features(
    X: np.ndarray,
    requested: Set[str],
    fs: float = 100.0,
) -> Dict[str, np.ndarray]:
    """Vectorized calculation of specialized and audio/wavelet features."""
    derived: Dict[str, np.ndarray] = {}
    N, L = X.shape

    # 1. Statistical extensions
    if "interquartile_range" in requested:
        q75 = np.percentile(X, 75, axis=1)
        q25 = np.percentile(X, 25, axis=1)
        derived["interquartile_range"] = q75 - q25

    if "peak_to_peak_distance" in requested:
        derived["peak_to_peak_distance"] = np.ptp(X, axis=1)

    if "mean_abs_deviation" in requested:
        mean_x = np.mean(X, axis=1, keepdims=True)
        derived["mean_abs_deviation"] = np.mean(np.abs(X - mean_x), axis=1)

    if "median_abs_deviation" in requested:
        med_x = np.median(X, axis=1, keepdims=True)
        derived["median_abs_deviation"] = np.median(np.abs(X - med_x), axis=1)

    # 2. Temporal extensions
    if "zero_crossing_rate" in requested:
        diff_signs = np.diff(np.signbit(X), axis=1)
        zc = np.sum(diff_signs != 0, axis=1)
        derived["zero_crossing_rate"] = zc / max(1, L - 1)

    if "area_under_curve" in requested:
        abs_x = np.abs(X)
        trapz_sum = (0.5 * (abs_x[:, 0] + abs_x[:, -1]) + np.sum(abs_x[:, 1:-1], axis=1)) / fs
        derived["area_under_curve"] = trapz_sum

    if "signal_distance" in requested:
        diff_x = np.diff(X, axis=1)
        dx = 1.0 / fs
        dist = np.sum(np.sqrt(dx * dx + diff_x * diff_x), axis=1)
        derived["signal_distance"] = dist

    if "positive_turning_points" in requested or "negative_turning_points" in requested or "total_turning_points" in requested:
        diff_x = np.diff(X, axis=1)
        pos_turn = np.sum((diff_x[:, :-1] > 0) & (diff_x[:, 1:] < 0), axis=1).astype(np.float64)
        neg_turn = np.sum((diff_x[:, :-1] < 0) & (diff_x[:, 1:] > 0), axis=1).astype(np.float64)
        if "positive_turning_points" in requested:
            derived["positive_turning_points"] = pos_turn
        if "negative_turning_points" in requested:
            derived["negative_turning_points"] = neg_turn
        if "total_turning_points" in requested:
            derived["total_turning_points"] = pos_turn + neg_turn

    # 3. Fractal extensions
    if "petrosian_fractal_dimension" in requested:
        diff_x = np.diff(X, axis=1)
        sign_diff = np.diff(np.signbit(diff_x), axis=1)
        n_delta = np.sum(sign_diff != 0, axis=1).astype(np.float64)
        log_n = np.log10(float(L))
        denom = log_n + np.log10(float(L) / (float(L) + 0.4 * n_delta + 1e-12))
        derived["petrosian_fractal_dimension"] = np.where(denom > 0, log_n / denom, 1.0)

    # 4. Spectral moments & slopes
    spectral_reqs = {
        "spectral_spread", "spectral_slope", "spectral_decrease",
        "spectral_roll_off", "spectral_roll_on", "spectral_skewness", "spectral_kurtosis"
    }
    if spectral_reqs & requested:
        fft_mags = np.abs(np.fft.rfft(X, axis=1))[:, 1:]  # exclude DC
        freqs = np.fft.rfftfreq(L, d=1.0 / fs)[1:]
        mag_sum = np.sum(fft_mags, axis=1, keepdims=True)
        mag_sum_safe = np.where(mag_sum > 0, mag_sum, 1.0)
        norm_mags = fft_mags / mag_sum_safe

        centroid = np.sum(freqs * norm_mags, axis=1, keepdims=True)

        if "spectral_spread" in requested or "spectral_skewness" in requested or "spectral_kurtosis" in requested:
            diff_f = freqs - centroid
            spread2 = np.sum((diff_f ** 2) * norm_mags, axis=1)
            spread = np.sqrt(np.maximum(0.0, spread2))
            if "spectral_spread" in requested:
                derived["spectral_spread"] = spread

            spread_safe = np.where(spread > 1e-12, spread, 1.0)
            if "spectral_skewness" in requested:
                skew = np.sum((diff_f ** 3) * norm_mags, axis=1) / (spread_safe ** 3)
                derived["spectral_skewness"] = np.where(spread > 1e-12, skew, 0.0)
            if "spectral_kurtosis" in requested:
                kurt = np.sum((diff_f ** 4) * norm_mags, axis=1) / (spread_safe ** 4)
                derived["spectral_kurtosis"] = np.where(spread > 1e-12, kurt, 0.0)

        if "spectral_slope" in requested:
            n_bins = len(freqs)
            sum_f = np.sum(freqs)
            sum_f2 = np.sum(freqs * freqs)
            denom_lr = n_bins * sum_f2 - sum_f * sum_f
            if denom_lr > 0:
                dot_f_mag = np.sum(freqs * fft_mags, axis=1)
                sum_mag = mag_sum.ravel()
                slope = (n_bins * dot_f_mag - sum_f * sum_mag) / (denom_lr * mag_sum_safe.ravel())
                derived["spectral_slope"] = slope
            else:
                derived["spectral_slope"] = np.zeros(N)

        if "spectral_decrease" in requested:
            if fft_mags.shape[1] > 1:
                fmag_band = fft_mags[:, 1:]
                k_idx = np.arange(1, fmag_band.shape[1] + 1)
                soma_num = np.sum((fmag_band - fft_mags[:, :1]) / k_idx, axis=1)
                band_sum = np.sum(fmag_band, axis=1)
                derived["spectral_decrease"] = np.where(band_sum > 0, soma_num / band_sum, 0.0)
            else:
                derived["spectral_decrease"] = np.zeros(N)

        if "spectral_roll_off" in requested:
            cum_mags = np.cumsum(fft_mags, axis=1)
            thresholds = 0.85 * mag_sum
            roll_off_idx = np.argmax(cum_mags >= thresholds, axis=1)
            derived["spectral_roll_off"] = freqs[roll_off_idx]

        if "spectral_roll_on" in requested:
            cum_mags = np.cumsum(fft_mags, axis=1)
            thresholds = 0.05 * mag_sum
            roll_on_idx = np.argmax(cum_mags >= thresholds, axis=1)
            derived["spectral_roll_on"] = freqs[roll_on_idx]

    # 5. Mel-Frequency Cepstral Coefficients (MFCC)
    mfcc_reqs = {f"mfcc_{i}" for i in range(12)}
    if mfcc_reqs & requested or "mfcc" in requested:
        import scipy.fft
        pre_emphasis = 0.97
        cep_lifter = 22
        nfft = 512
        nfilt = 40
        num_ceps = 12

        low_freq_mel = 0.0
        high_freq_mel = 2595.0 * np.log10(1.0 + (fs / 2.0) / 700.0)
        mel_points = np.linspace(low_freq_mel, high_freq_mel, nfilt + 2)
        hz_points = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)
        filter_bin = np.floor((nfft + 1) * hz_points / fs)

        fbank = np.zeros((nfilt, int(np.floor(nfft / 2 + 1))))
        for m in range(1, nfilt + 1):
            f_m_minus = int(filter_bin[m - 1])
            f_m = int(filter_bin[m])
            f_m_plus = int(filter_bin[m + 1])
            for k in range(f_m_minus, f_m):
                fbank[m - 1, k] = (k - filter_bin[m - 1]) / (filter_bin[m] - filter_bin[m - 1])
            for k in range(f_m, f_m_plus):
                fbank[m - 1, k] = (filter_bin[m + 1] - k) / (filter_bin[m + 1] - filter_bin[m])

        emphasized = np.hstack([X[:, :1], X[:, 1:] - pre_emphasis * X[:, :-1]])
        padded = np.zeros((N, nfft))
        copy_len = min(L, nfft)
        padded[:, :copy_len] = emphasized[:, :copy_len]

        mag_frames = np.abs(np.fft.rfft(padded, axis=1))
        pow_frames = (mag_frames ** 2) / nfft
        filter_banks = np.dot(pow_frames, fbank.T)
        filter_banks = np.where(filter_banks == 0, np.finfo(float).eps, filter_banks)
        filter_banks = 20.0 * np.log10(filter_banks)

        dct_coeffs = scipy.fft.dct(filter_banks, type=2, axis=-1, norm="ortho")[:, 1 : num_ceps + 1]
        n = np.arange(num_ceps)
        lift = 1.0 + (cep_lifter / 2.0) * np.sin(np.pi * n / cep_lifter)
        mfccs = dct_coeffs * lift

        for i in range(12):
            derived[f"mfcc_{i}"] = mfccs[:, i]

    # 6. Linear Prediction Cepstral Coefficients (LPCC)
    lpcc_reqs = {f"lpcc_{i}" for i in range(12)}
    if lpcc_reqs & requested or "lpcc" in requested:
        n_coeff = 12
        order = 12
        lpcc_mat = np.zeros((N, n_coeff), dtype=np.float64)
        for row_idx in range(N):
            sig = X[row_idx]
            if np.all(sig == 0):
                continue
            r = np.correlate(sig, sig, mode="full")[len(sig) - 1 : len(sig) + order]
            if r[0] == 0:
                continue
            a = np.zeros(order + 1)
            e = r[0]
            a[0] = 1.0
            for k in range(1, order + 1):
                lam = -np.sum(a[:k] * r[k:0:-1]) / e
                a[1 : k + 1] += lam * a[k - 1 :: -1]
                e *= (1.0 - lam * lam)
            roots = np.roots(a)
            powerspectrum = np.abs(np.fft.fft(roots, 1024)) ** 2
            powerspectrum = np.where(powerspectrum == 0, 1e-12, powerspectrum)
            lpcc_val = np.abs(np.fft.ifft(np.log(powerspectrum)))
            lpcc_mat[row_idx] = lpcc_val[:n_coeff]

        for i in range(12):
            derived[f"lpcc_{i}"] = lpcc_mat[:, i]

    # 7. Continuous Wavelet Transform (CWT)
    wavelet_reqs = {
        f"wavelet_{stat}_scale_{i}"
        for stat in ["energy", "abs_mean", "std", "var"]
        for i in range(1, 10)
    } | {"wavelet_entropy"}
    if wavelet_reqs & requested or any("wavelet" in r for r in requested):
        import pywt
        widths = np.arange(1, 10)
        n_scales = len(widths)
        we = np.zeros((N, n_scales))
        wam = np.zeros((N, n_scales))
        wstd = np.zeros((N, n_scales))
        wvar = np.zeros((N, n_scales))
        went = np.zeros(N)

        for row_idx in range(N):
            sig = X[row_idx]
            if np.all(sig == 0):
                continue
            coeffs, _ = pywt.cwt(sig, widths, "mexh", sampling_period=1.0 / fs)
            we[row_idx] = np.sqrt(np.sum(coeffs ** 2, axis=1) / coeffs.shape[1])
            wam[row_idx] = np.abs(np.mean(coeffs, axis=1))
            wstd[row_idx] = np.std(coeffs, axis=1)
            wvar[row_idx] = np.var(coeffs, axis=1)
            e_scale = np.sum(np.abs(coeffs), axis=1)
            tot_e = np.sum(e_scale)
            if tot_e > 0:
                p = e_scale / tot_e
                p_safe = np.where(p > 0, p, 1.0)
                went[row_idx] = -np.sum(p * np.log(p_safe))

        for i in range(n_scales):
            derived[f"wavelet_energy_scale_{i+1}"] = we[:, i]
            derived[f"wavelet_abs_mean_scale_{i+1}"] = wam[:, i]
            derived[f"wavelet_std_scale_{i+1}"] = wstd[:, i]
            derived[f"wavelet_var_scale_{i+1}"] = wvar[:, i]
        derived["wavelet_entropy"] = went

    return derived

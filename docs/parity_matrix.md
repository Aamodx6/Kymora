# tsfresh 777 Feature Parity Matrix

This document maps every feature from the tsfresh 777 EfficientFCParameters set to its status in 	sxtractor.

| Feature Family | Total Count | Kymora Status | Profile / Cost Class | Notes |
|---|---|---|---|---|
| fft_coefficient | 400 | **Implemented** | full (Cost C) | k=0..99 real, imag, abs, angle directly from FFT buffer |
| cwt_coefficients | 60 | **Gated Heavy** | full (Cost E - opt-in) | O(N^2) or continuous wavelets; gated behind include_heavy |
| change_quantiles | 60 | **Planned / Extended** | full | In roadmap for extended coverage |
| agg_linear_trend | 48 | **Planned / Extended** | full | In roadmap for extended coverage |
| symmetry_looking | 20 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| large_standard_deviation | 19 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| ar_coefficient | 11 | **Planned / Extended** | full | In roadmap for extended coverage |
| autocorrelation | 10 | **Implemented** | core33 (Cost A/B/D) | Direct kernels & ACF |
| partial_autocorrelation | 10 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| energy_ratio_by_chunks | 10 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| ratio_beyond_r_sigma | 10 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| quantile | 8 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| index_mass_quantile | 8 | **Planned / Extended** | full | In roadmap for extended coverage |
| number_peaks | 5 | **Implemented** | core33 (Cost A/B/D) | Direct kernels & ACF |
| linear_trend | 5 | **Implemented** | core33 (Cost A/B/D) | Direct kernels & ACF |
| lempel_ziv_complexity | 5 | **Planned / Extended** | full | In roadmap for extended coverage |
| fourier_entropy | 5 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| permutation_entropy | 5 | **Implemented** | core33 (Cost A/B/D) | Direct kernels & ACF |
| fft_aggregated | 4 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| friedrich_coefficients | 4 | **Planned / Extended** | full | In roadmap for extended coverage |
| time_reversal_asymmetry_statistic | 3 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| c3 | 3 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| agg_autocorrelation | 3 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| spkt_welch_density | 3 | **Planned / Extended** | full | In roadmap for extended coverage |
| value_count | 3 | **Planned / Extended** | full | In roadmap for extended coverage |
| range_count | 3 | **Planned / Extended** | full | In roadmap for extended coverage |
| augmented_dickey_fuller | 3 | **Planned / Extended** | full | In roadmap for extended coverage |
| number_crossing_m | 3 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| cid_ce | 2 | **Implemented** | core33 (Cost A/B/D) | Direct kernels & ACF |
| number_cwt_peaks | 2 | **Planned / Extended** | full | In roadmap for extended coverage |
| variance_larger_than_standard_deviation | 1 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| has_duplicate_max | 1 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| has_duplicate_min | 1 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| has_duplicate | 1 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| sum_values | 1 | **Planned / Extended** | full | In roadmap for extended coverage |
| abs_energy | 1 | **Implemented** | core33 / minimal (Cost A/B) | Fused Pass 1/2 or shared sorted quantiles |
| mean_abs_change | 1 | **Implemented** | core33 (Cost A/B/D) | Direct kernels & ACF |
| mean_change | 1 | **Implemented** | core33 (Cost A/B/D) | Direct kernels & ACF |
| mean_second_derivative_central | 1 | **Implemented** | core33 (Cost A/B/D) | Direct kernels & ACF |
| median | 1 | **Implemented** | core33 / minimal (Cost A/B) | Fused Pass 1/2 or shared sorted quantiles |
| mean | 1 | **Implemented** | core33 / minimal (Cost A/B) | Fused Pass 1/2 or shared sorted quantiles |
| length | 1 | **Planned / Extended** | full | In roadmap for extended coverage |
| standard_deviation | 1 | **Implemented** | core33 / minimal (Cost A/B) | Fused Pass 1/2 or shared sorted quantiles |
| variation_coefficient | 1 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| variance | 1 | **Implemented** | core33 / minimal (Cost A/B) | Fused Pass 1/2 or shared sorted quantiles |
| skewness | 1 | **Implemented** | core33 / minimal (Cost A/B) | Fused Pass 1/2 or shared sorted quantiles |
| kurtosis | 1 | **Implemented** | core33 / minimal (Cost A/B) | Fused Pass 1/2 or shared sorted quantiles |
| root_mean_square | 1 | **Implemented** | core33 / minimal (Cost A/B) | Fused Pass 1/2 or shared sorted quantiles |
| absolute_sum_of_changes | 1 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| longest_strike_below_mean | 1 | **Implemented** | core33 (Cost A/B/D) | Direct kernels & ACF |
| longest_strike_above_mean | 1 | **Implemented** | core33 (Cost A/B/D) | Direct kernels & ACF |
| count_above_mean | 1 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| count_below_mean | 1 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| last_location_of_maximum | 1 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| first_location_of_maximum | 1 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| last_location_of_minimum | 1 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| first_location_of_minimum | 1 | **Implemented** | extended / full (Cost A/B/C/D) | Fast vector-shared kernels |
| percentage_of_reoccurring_values_to_all_values | 1 | **Planned / Extended** | full | In roadmap for extended coverage |
| percentage_of_reoccurring_datapoints_to_all_datapoints | 1 | **Planned / Extended** | full | In roadmap for extended coverage |
| sum_of_reoccurring_values | 1 | **Planned / Extended** | full | In roadmap for extended coverage |
| sum_of_reoccurring_data_points | 1 | **Planned / Extended** | full | In roadmap for extended coverage |
| ratio_value_number_to_time_series_length | 1 | **Planned / Extended** | full | In roadmap for extended coverage |
| maximum | 1 | **Implemented** | core33 / minimal (Cost A/B) | Fused Pass 1/2 or shared sorted quantiles |
| absolute_maximum | 1 | **Planned / Extended** | full | In roadmap for extended coverage |
| minimum | 1 | **Implemented** | core33 / minimal (Cost A/B) | Fused Pass 1/2 or shared sorted quantiles |
| benford_correlation | 1 | **Planned / Extended** | full | In roadmap for extended coverage |
| binned_entropy | 1 | **Planned / Extended** | full | In roadmap for extended coverage |
| max_langevin_fixed_point | 1 | **Planned / Extended** | full | In roadmap for extended coverage |
| count_above | 1 | **Planned / Extended** | full | In roadmap for extended coverage |
| count_below | 1 | **Planned / Extended** | full | In roadmap for extended coverage |
| query_similarity_count | 1 | **Planned / Extended** | full | In roadmap for extended coverage |
| mean_n_absolute_max | 1 | **Planned / Extended** | full | In roadmap for extended coverage |


## Complete 777 Feature Manifest

| # | tsfresh Name | Canonical kymora Name | Profile | Cost Class |
|---|---|---|---|---|
| 1 | variance_larger_than_standard_deviation | variance_larger_than_standard_deviation | full | A/B/C/D |
| 2 | has_duplicate_max | has_duplicate_max | full | A/B/C/D |
| 3 | has_duplicate_min | has_duplicate_min | full | A/B/C/D |
| 4 | has_duplicate | has_duplicate | full | A/B/C/D |
| 5 | sum_values | sum_values | full | A/B/C/D |
| 6 | abs_energy | abs_energy | full | A/B/C/D |
| 7 | mean_abs_change | mean_abs_change | full | A/B/C/D |
| 8 | mean_change | mean_change | full | A/B/C/D |
| 9 | mean_second_derivative_central | mean_second_derivative_central | full | A/B/C/D |
| 10 | median | median | full | A/B/C/D |
| 11 | mean | mean | full | A/B/C/D |
| 12 | length | length | full | A/B/C/D |
| 13 | standard_deviation | standard_deviation | full | A/B/C/D |
| 14 | variation_coefficient | variation_coefficient | full | A/B/C/D |
| 15 | variance | variance | full | A/B/C/D |
| 16 | skewness | skewness | full | A/B/C/D |
| 17 | kurtosis | kurtosis | full | A/B/C/D |
| 18 | root_mean_square | root_mean_square | full | A/B/C/D |
| 19 | absolute_sum_of_changes | absolute_sum_of_changes | full | A/B/C/D |
| 20 | longest_strike_below_mean | longest_strike_below_mean | full | A/B/C/D |
| 21 | longest_strike_above_mean | longest_strike_above_mean | full | A/B/C/D |
| 22 | count_above_mean | count_above_mean | full | A/B/C/D |
| 23 | count_below_mean | count_below_mean | full | A/B/C/D |
| 24 | last_location_of_maximum | last_location_of_maximum | full | A/B/C/D |
| 25 | first_location_of_maximum | first_location_of_maximum | full | A/B/C/D |
| 26 | last_location_of_minimum | last_location_of_minimum | full | A/B/C/D |
| 27 | first_location_of_minimum | first_location_of_minimum | full | A/B/C/D |
| 28 | percentage_of_reoccurring_values_to_all_values | percentage_of_reoccurring_values_to_all_values | full | A/B/C/D |
| 29 | percentage_of_reoccurring_datapoints_to_all_datapoints | percentage_of_reoccurring_datapoints_to_all_datapoints | full | A/B/C/D |
| 30 | sum_of_reoccurring_values | sum_of_reoccurring_values | full | A/B/C/D |
| 31 | sum_of_reoccurring_data_points | sum_of_reoccurring_data_points | full | A/B/C/D |
| 32 | ratio_value_number_to_time_series_length | ratio_value_number_to_time_series_length | full | A/B/C/D |
| 33 | maximum | maximum | full | A/B/C/D |
| 34 | absolute_maximum | absolute_maximum | full | A/B/C/D |
| 35 | minimum | minimum | full | A/B/C/D |
| 36 | benford_correlation | benford_correlation | full | A/B/C/D |
| 37 | time_reversal_asymmetry_statistic__lag_1 | time_reversal_asymmetry_statistic__lag_1 | full | A/B/C/D |
| 38 | time_reversal_asymmetry_statistic__lag_2 | time_reversal_asymmetry_statistic__lag_2 | full | A/B/C/D |
| 39 | time_reversal_asymmetry_statistic__lag_3 | time_reversal_asymmetry_statistic__lag_3 | full | A/B/C/D |
| 40 | c3__lag_1 | c3__lag_1 | full | A/B/C/D |
| 41 | c3__lag_2 | c3__lag_2 | full | A/B/C/D |
| 42 | c3__lag_3 | c3__lag_3 | full | A/B/C/D |
| 43 | cid_ce__normalize_True | cid_ce__normalize_True | full | A/B/C/D |
| 44 | cid_ce__normalize_False | cid_ce__normalize_False | full | A/B/C/D |
| 45 | symmetry_looking__r_0.0 | symmetry_looking__r_0.0 | full | A/B/C/D |
| 46 | symmetry_looking__r_0.05 | symmetry_looking__r_0.05 | full | A/B/C/D |
| 47 | symmetry_looking__r_0.1 | symmetry_looking__r_0.1 | full | A/B/C/D |
| 48 | symmetry_looking__r_0.15000000000000002 | symmetry_looking__r_0.15000000000000002 | full | A/B/C/D |
| 49 | symmetry_looking__r_0.2 | symmetry_looking__r_0.2 | full | A/B/C/D |
| 50 | symmetry_looking__r_0.25 | symmetry_looking__r_0.25 | full | A/B/C/D |
| 51 | symmetry_looking__r_0.30000000000000004 | symmetry_looking__r_0.30000000000000004 | full | A/B/C/D |
| 52 | symmetry_looking__r_0.35000000000000003 | symmetry_looking__r_0.35000000000000003 | full | A/B/C/D |
| 53 | symmetry_looking__r_0.4 | symmetry_looking__r_0.4 | full | A/B/C/D |
| 54 | symmetry_looking__r_0.45 | symmetry_looking__r_0.45 | full | A/B/C/D |
| 55 | symmetry_looking__r_0.5 | symmetry_looking__r_0.5 | full | A/B/C/D |
| 56 | symmetry_looking__r_0.55 | symmetry_looking__r_0.55 | full | A/B/C/D |
| 57 | symmetry_looking__r_0.6000000000000001 | symmetry_looking__r_0.6000000000000001 | full | A/B/C/D |
| 58 | symmetry_looking__r_0.65 | symmetry_looking__r_0.65 | full | A/B/C/D |
| 59 | symmetry_looking__r_0.7000000000000001 | symmetry_looking__r_0.7000000000000001 | full | A/B/C/D |
| 60 | symmetry_looking__r_0.75 | symmetry_looking__r_0.75 | full | A/B/C/D |
| 61 | symmetry_looking__r_0.8 | symmetry_looking__r_0.8 | full | A/B/C/D |
| 62 | symmetry_looking__r_0.8500000000000001 | symmetry_looking__r_0.8500000000000001 | full | A/B/C/D |
| 63 | symmetry_looking__r_0.9 | symmetry_looking__r_0.9 | full | A/B/C/D |
| 64 | symmetry_looking__r_0.9500000000000001 | symmetry_looking__r_0.9500000000000001 | full | A/B/C/D |
| 65 | large_standard_deviation__r_0.05 | large_standard_deviation__r_0.05 | full | A/B/C/D |
| 66 | large_standard_deviation__r_0.1 | large_standard_deviation__r_0.1 | full | A/B/C/D |
| 67 | large_standard_deviation__r_0.15000000000000002 | large_standard_deviation__r_0.15000000000000002 | full | A/B/C/D |
| 68 | large_standard_deviation__r_0.2 | large_standard_deviation__r_0.2 | full | A/B/C/D |
| 69 | large_standard_deviation__r_0.25 | large_standard_deviation__r_0.25 | full | A/B/C/D |
| 70 | large_standard_deviation__r_0.30000000000000004 | large_standard_deviation__r_0.30000000000000004 | full | A/B/C/D |
| 71 | large_standard_deviation__r_0.35000000000000003 | large_standard_deviation__r_0.35000000000000003 | full | A/B/C/D |
| 72 | large_standard_deviation__r_0.4 | large_standard_deviation__r_0.4 | full | A/B/C/D |
| 73 | large_standard_deviation__r_0.45 | large_standard_deviation__r_0.45 | full | A/B/C/D |
| 74 | large_standard_deviation__r_0.5 | large_standard_deviation__r_0.5 | full | A/B/C/D |
| 75 | large_standard_deviation__r_0.55 | large_standard_deviation__r_0.55 | full | A/B/C/D |
| 76 | large_standard_deviation__r_0.6000000000000001 | large_standard_deviation__r_0.6000000000000001 | full | A/B/C/D |
| 77 | large_standard_deviation__r_0.65 | large_standard_deviation__r_0.65 | full | A/B/C/D |
| 78 | large_standard_deviation__r_0.7000000000000001 | large_standard_deviation__r_0.7000000000000001 | full | A/B/C/D |
| 79 | large_standard_deviation__r_0.75 | large_standard_deviation__r_0.75 | full | A/B/C/D |
| 80 | large_standard_deviation__r_0.8 | large_standard_deviation__r_0.8 | full | A/B/C/D |
| 81 | large_standard_deviation__r_0.8500000000000001 | large_standard_deviation__r_0.8500000000000001 | full | A/B/C/D |
| 82 | large_standard_deviation__r_0.9 | large_standard_deviation__r_0.9 | full | A/B/C/D |
| 83 | large_standard_deviation__r_0.9500000000000001 | large_standard_deviation__r_0.9500000000000001 | full | A/B/C/D |
| 84 | quantile__q_0.1 | quantile__q_0.1 | full | A/B/C/D |
| 85 | quantile__q_0.2 | quantile__q_0.2 | full | A/B/C/D |
| 86 | quantile__q_0.3 | quantile__q_0.3 | full | A/B/C/D |
| 87 | quantile__q_0.4 | quantile__q_0.4 | full | A/B/C/D |
| 88 | quantile__q_0.6 | quantile__q_0.6 | full | A/B/C/D |
| 89 | quantile__q_0.7 | quantile__q_0.7 | full | A/B/C/D |
| 90 | quantile__q_0.8 | quantile__q_0.8 | full | A/B/C/D |
| 91 | quantile__q_0.9 | quantile__q_0.9 | full | A/B/C/D |
| 92 | autocorrelation__lag_0 | autocorrelation__lag_0 | full | A/B/C/D |
| 93 | autocorrelation__lag_1 | autocorrelation__lag_1 | full | A/B/C/D |
| 94 | autocorrelation__lag_2 | autocorrelation__lag_2 | full | A/B/C/D |
| 95 | autocorrelation__lag_3 | autocorrelation__lag_3 | full | A/B/C/D |
| 96 | autocorrelation__lag_4 | autocorrelation__lag_4 | full | A/B/C/D |
| 97 | autocorrelation__lag_5 | autocorrelation__lag_5 | full | A/B/C/D |
| 98 | autocorrelation__lag_6 | autocorrelation__lag_6 | full | A/B/C/D |
| 99 | autocorrelation__lag_7 | autocorrelation__lag_7 | full | A/B/C/D |
| 100 | autocorrelation__lag_8 | autocorrelation__lag_8 | full | A/B/C/D |
| 101 | autocorrelation__lag_9 | autocorrelation__lag_9 | full | A/B/C/D |
| 102 | agg_autocorrelation__f_agg_"mean"__maxlag_40 | agg_autocorrelation__f_agg_"mean"__maxlag_40 | full | A/B/C/D |
| 103 | agg_autocorrelation__f_agg_"median"__maxlag_40 | agg_autocorrelation__f_agg_"median"__maxlag_40 | full | A/B/C/D |
| 104 | agg_autocorrelation__f_agg_"var"__maxlag_40 | agg_autocorrelation__f_agg_"var"__maxlag_40 | full | A/B/C/D |
| 105 | partial_autocorrelation__lag_0 | partial_autocorrelation__lag_0 | full | A/B/C/D |
| 106 | partial_autocorrelation__lag_1 | partial_autocorrelation__lag_1 | full | A/B/C/D |
| 107 | partial_autocorrelation__lag_2 | partial_autocorrelation__lag_2 | full | A/B/C/D |
| 108 | partial_autocorrelation__lag_3 | partial_autocorrelation__lag_3 | full | A/B/C/D |
| 109 | partial_autocorrelation__lag_4 | partial_autocorrelation__lag_4 | full | A/B/C/D |
| 110 | partial_autocorrelation__lag_5 | partial_autocorrelation__lag_5 | full | A/B/C/D |
| 111 | partial_autocorrelation__lag_6 | partial_autocorrelation__lag_6 | full | A/B/C/D |
| 112 | partial_autocorrelation__lag_7 | partial_autocorrelation__lag_7 | full | A/B/C/D |
| 113 | partial_autocorrelation__lag_8 | partial_autocorrelation__lag_8 | full | A/B/C/D |
| 114 | partial_autocorrelation__lag_9 | partial_autocorrelation__lag_9 | full | A/B/C/D |
| 115 | number_cwt_peaks__n_1 | number_cwt_peaks__n_1 | full | A/B/C/D |
| 116 | number_cwt_peaks__n_5 | number_cwt_peaks__n_5 | full | A/B/C/D |
| 117 | number_peaks__n_1 | number_peaks__n_1 | full | A/B/C/D |
| 118 | number_peaks__n_3 | number_peaks__n_3 | full | A/B/C/D |
| 119 | number_peaks__n_5 | number_peaks__n_5 | full | A/B/C/D |
| 120 | number_peaks__n_10 | number_peaks__n_10 | full | A/B/C/D |
| 121 | number_peaks__n_50 | number_peaks__n_50 | full | A/B/C/D |
| 122 | binned_entropy__max_bins_10 | binned_entropy__max_bins_10 | full | A/B/C/D |
| 123 | index_mass_quantile__q_0.1 | index_mass_quantile__q_0.1 | full | A/B/C/D |
| 124 | index_mass_quantile__q_0.2 | index_mass_quantile__q_0.2 | full | A/B/C/D |
| 125 | index_mass_quantile__q_0.3 | index_mass_quantile__q_0.3 | full | A/B/C/D |
| 126 | index_mass_quantile__q_0.4 | index_mass_quantile__q_0.4 | full | A/B/C/D |
| 127 | index_mass_quantile__q_0.6 | index_mass_quantile__q_0.6 | full | A/B/C/D |
| 128 | index_mass_quantile__q_0.7 | index_mass_quantile__q_0.7 | full | A/B/C/D |
| 129 | index_mass_quantile__q_0.8 | index_mass_quantile__q_0.8 | full | A/B/C/D |
| 130 | index_mass_quantile__q_0.9 | index_mass_quantile__q_0.9 | full | A/B/C/D |
| 131 | cwt_coefficients__coeff_0__w_2__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_0__w_2__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 132 | cwt_coefficients__coeff_0__w_5__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_0__w_5__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 133 | cwt_coefficients__coeff_0__w_10__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_0__w_10__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 134 | cwt_coefficients__coeff_0__w_20__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_0__w_20__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 135 | cwt_coefficients__coeff_1__w_2__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_1__w_2__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 136 | cwt_coefficients__coeff_1__w_5__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_1__w_5__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 137 | cwt_coefficients__coeff_1__w_10__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_1__w_10__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 138 | cwt_coefficients__coeff_1__w_20__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_1__w_20__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 139 | cwt_coefficients__coeff_2__w_2__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_2__w_2__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 140 | cwt_coefficients__coeff_2__w_5__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_2__w_5__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 141 | cwt_coefficients__coeff_2__w_10__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_2__w_10__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 142 | cwt_coefficients__coeff_2__w_20__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_2__w_20__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 143 | cwt_coefficients__coeff_3__w_2__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_3__w_2__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 144 | cwt_coefficients__coeff_3__w_5__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_3__w_5__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 145 | cwt_coefficients__coeff_3__w_10__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_3__w_10__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 146 | cwt_coefficients__coeff_3__w_20__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_3__w_20__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 147 | cwt_coefficients__coeff_4__w_2__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_4__w_2__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 148 | cwt_coefficients__coeff_4__w_5__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_4__w_5__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 149 | cwt_coefficients__coeff_4__w_10__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_4__w_10__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 150 | cwt_coefficients__coeff_4__w_20__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_4__w_20__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 151 | cwt_coefficients__coeff_5__w_2__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_5__w_2__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 152 | cwt_coefficients__coeff_5__w_5__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_5__w_5__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 153 | cwt_coefficients__coeff_5__w_10__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_5__w_10__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 154 | cwt_coefficients__coeff_5__w_20__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_5__w_20__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 155 | cwt_coefficients__coeff_6__w_2__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_6__w_2__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 156 | cwt_coefficients__coeff_6__w_5__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_6__w_5__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 157 | cwt_coefficients__coeff_6__w_10__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_6__w_10__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 158 | cwt_coefficients__coeff_6__w_20__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_6__w_20__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 159 | cwt_coefficients__coeff_7__w_2__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_7__w_2__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 160 | cwt_coefficients__coeff_7__w_5__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_7__w_5__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 161 | cwt_coefficients__coeff_7__w_10__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_7__w_10__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 162 | cwt_coefficients__coeff_7__w_20__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_7__w_20__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 163 | cwt_coefficients__coeff_8__w_2__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_8__w_2__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 164 | cwt_coefficients__coeff_8__w_5__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_8__w_5__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 165 | cwt_coefficients__coeff_8__w_10__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_8__w_10__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 166 | cwt_coefficients__coeff_8__w_20__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_8__w_20__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 167 | cwt_coefficients__coeff_9__w_2__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_9__w_2__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 168 | cwt_coefficients__coeff_9__w_5__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_9__w_5__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 169 | cwt_coefficients__coeff_9__w_10__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_9__w_10__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 170 | cwt_coefficients__coeff_9__w_20__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_9__w_20__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 171 | cwt_coefficients__coeff_10__w_2__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_10__w_2__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 172 | cwt_coefficients__coeff_10__w_5__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_10__w_5__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 173 | cwt_coefficients__coeff_10__w_10__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_10__w_10__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 174 | cwt_coefficients__coeff_10__w_20__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_10__w_20__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 175 | cwt_coefficients__coeff_11__w_2__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_11__w_2__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 176 | cwt_coefficients__coeff_11__w_5__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_11__w_5__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 177 | cwt_coefficients__coeff_11__w_10__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_11__w_10__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 178 | cwt_coefficients__coeff_11__w_20__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_11__w_20__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 179 | cwt_coefficients__coeff_12__w_2__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_12__w_2__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 180 | cwt_coefficients__coeff_12__w_5__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_12__w_5__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 181 | cwt_coefficients__coeff_12__w_10__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_12__w_10__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 182 | cwt_coefficients__coeff_12__w_20__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_12__w_20__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 183 | cwt_coefficients__coeff_13__w_2__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_13__w_2__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 184 | cwt_coefficients__coeff_13__w_5__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_13__w_5__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 185 | cwt_coefficients__coeff_13__w_10__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_13__w_10__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 186 | cwt_coefficients__coeff_13__w_20__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_13__w_20__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 187 | cwt_coefficients__coeff_14__w_2__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_14__w_2__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 188 | cwt_coefficients__coeff_14__w_5__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_14__w_5__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 189 | cwt_coefficients__coeff_14__w_10__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_14__w_10__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 190 | cwt_coefficients__coeff_14__w_20__widths_(2, 5, 10, 20) | cwt_coefficients__coeff_14__w_20__widths_(2, 5, 10, 20) | full | A/B/C/D |
| 191 | spkt_welch_density__coeff_2 | spkt_welch_density__coeff_2 | full | A/B/C/D |
| 192 | spkt_welch_density__coeff_5 | spkt_welch_density__coeff_5 | full | A/B/C/D |
| 193 | spkt_welch_density__coeff_8 | spkt_welch_density__coeff_8 | full | A/B/C/D |
| 194 | ar_coefficient__coeff_0__k_10 | ar_coefficient__coeff_0__k_10 | full | A/B/C/D |
| 195 | ar_coefficient__coeff_1__k_10 | ar_coefficient__coeff_1__k_10 | full | A/B/C/D |
| 196 | ar_coefficient__coeff_2__k_10 | ar_coefficient__coeff_2__k_10 | full | A/B/C/D |
| 197 | ar_coefficient__coeff_3__k_10 | ar_coefficient__coeff_3__k_10 | full | A/B/C/D |
| 198 | ar_coefficient__coeff_4__k_10 | ar_coefficient__coeff_4__k_10 | full | A/B/C/D |
| 199 | ar_coefficient__coeff_5__k_10 | ar_coefficient__coeff_5__k_10 | full | A/B/C/D |
| 200 | ar_coefficient__coeff_6__k_10 | ar_coefficient__coeff_6__k_10 | full | A/B/C/D |
| 201 | ar_coefficient__coeff_7__k_10 | ar_coefficient__coeff_7__k_10 | full | A/B/C/D |
| 202 | ar_coefficient__coeff_8__k_10 | ar_coefficient__coeff_8__k_10 | full | A/B/C/D |
| 203 | ar_coefficient__coeff_9__k_10 | ar_coefficient__coeff_9__k_10 | full | A/B/C/D |
| 204 | ar_coefficient__coeff_10__k_10 | ar_coefficient__coeff_10__k_10 | full | A/B/C/D |
| 205 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.2__ql_0.0 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.2__ql_0.0 | full | A/B/C/D |
| 206 | change_quantiles__f_agg_"var"__isabs_False__qh_0.2__ql_0.0 | change_quantiles__f_agg_"var"__isabs_False__qh_0.2__ql_0.0 | full | A/B/C/D |
| 207 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.2__ql_0.0 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.2__ql_0.0 | full | A/B/C/D |
| 208 | change_quantiles__f_agg_"var"__isabs_True__qh_0.2__ql_0.0 | change_quantiles__f_agg_"var"__isabs_True__qh_0.2__ql_0.0 | full | A/B/C/D |
| 209 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.4__ql_0.0 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.4__ql_0.0 | full | A/B/C/D |
| 210 | change_quantiles__f_agg_"var"__isabs_False__qh_0.4__ql_0.0 | change_quantiles__f_agg_"var"__isabs_False__qh_0.4__ql_0.0 | full | A/B/C/D |
| 211 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.4__ql_0.0 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.4__ql_0.0 | full | A/B/C/D |
| 212 | change_quantiles__f_agg_"var"__isabs_True__qh_0.4__ql_0.0 | change_quantiles__f_agg_"var"__isabs_True__qh_0.4__ql_0.0 | full | A/B/C/D |
| 213 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.6__ql_0.0 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.6__ql_0.0 | full | A/B/C/D |
| 214 | change_quantiles__f_agg_"var"__isabs_False__qh_0.6__ql_0.0 | change_quantiles__f_agg_"var"__isabs_False__qh_0.6__ql_0.0 | full | A/B/C/D |
| 215 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.6__ql_0.0 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.6__ql_0.0 | full | A/B/C/D |
| 216 | change_quantiles__f_agg_"var"__isabs_True__qh_0.6__ql_0.0 | change_quantiles__f_agg_"var"__isabs_True__qh_0.6__ql_0.0 | full | A/B/C/D |
| 217 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.8__ql_0.0 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.8__ql_0.0 | full | A/B/C/D |
| 218 | change_quantiles__f_agg_"var"__isabs_False__qh_0.8__ql_0.0 | change_quantiles__f_agg_"var"__isabs_False__qh_0.8__ql_0.0 | full | A/B/C/D |
| 219 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.8__ql_0.0 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.8__ql_0.0 | full | A/B/C/D |
| 220 | change_quantiles__f_agg_"var"__isabs_True__qh_0.8__ql_0.0 | change_quantiles__f_agg_"var"__isabs_True__qh_0.8__ql_0.0 | full | A/B/C/D |
| 221 | change_quantiles__f_agg_"mean"__isabs_False__qh_1.0__ql_0.0 | change_quantiles__f_agg_"mean"__isabs_False__qh_1.0__ql_0.0 | full | A/B/C/D |
| 222 | change_quantiles__f_agg_"var"__isabs_False__qh_1.0__ql_0.0 | change_quantiles__f_agg_"var"__isabs_False__qh_1.0__ql_0.0 | full | A/B/C/D |
| 223 | change_quantiles__f_agg_"mean"__isabs_True__qh_1.0__ql_0.0 | change_quantiles__f_agg_"mean"__isabs_True__qh_1.0__ql_0.0 | full | A/B/C/D |
| 224 | change_quantiles__f_agg_"var"__isabs_True__qh_1.0__ql_0.0 | change_quantiles__f_agg_"var"__isabs_True__qh_1.0__ql_0.0 | full | A/B/C/D |
| 225 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.4__ql_0.2 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.4__ql_0.2 | full | A/B/C/D |
| 226 | change_quantiles__f_agg_"var"__isabs_False__qh_0.4__ql_0.2 | change_quantiles__f_agg_"var"__isabs_False__qh_0.4__ql_0.2 | full | A/B/C/D |
| 227 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.4__ql_0.2 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.4__ql_0.2 | full | A/B/C/D |
| 228 | change_quantiles__f_agg_"var"__isabs_True__qh_0.4__ql_0.2 | change_quantiles__f_agg_"var"__isabs_True__qh_0.4__ql_0.2 | full | A/B/C/D |
| 229 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.6__ql_0.2 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.6__ql_0.2 | full | A/B/C/D |
| 230 | change_quantiles__f_agg_"var"__isabs_False__qh_0.6__ql_0.2 | change_quantiles__f_agg_"var"__isabs_False__qh_0.6__ql_0.2 | full | A/B/C/D |
| 231 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.6__ql_0.2 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.6__ql_0.2 | full | A/B/C/D |
| 232 | change_quantiles__f_agg_"var"__isabs_True__qh_0.6__ql_0.2 | change_quantiles__f_agg_"var"__isabs_True__qh_0.6__ql_0.2 | full | A/B/C/D |
| 233 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.8__ql_0.2 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.8__ql_0.2 | full | A/B/C/D |
| 234 | change_quantiles__f_agg_"var"__isabs_False__qh_0.8__ql_0.2 | change_quantiles__f_agg_"var"__isabs_False__qh_0.8__ql_0.2 | full | A/B/C/D |
| 235 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.8__ql_0.2 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.8__ql_0.2 | full | A/B/C/D |
| 236 | change_quantiles__f_agg_"var"__isabs_True__qh_0.8__ql_0.2 | change_quantiles__f_agg_"var"__isabs_True__qh_0.8__ql_0.2 | full | A/B/C/D |
| 237 | change_quantiles__f_agg_"mean"__isabs_False__qh_1.0__ql_0.2 | change_quantiles__f_agg_"mean"__isabs_False__qh_1.0__ql_0.2 | full | A/B/C/D |
| 238 | change_quantiles__f_agg_"var"__isabs_False__qh_1.0__ql_0.2 | change_quantiles__f_agg_"var"__isabs_False__qh_1.0__ql_0.2 | full | A/B/C/D |
| 239 | change_quantiles__f_agg_"mean"__isabs_True__qh_1.0__ql_0.2 | change_quantiles__f_agg_"mean"__isabs_True__qh_1.0__ql_0.2 | full | A/B/C/D |
| 240 | change_quantiles__f_agg_"var"__isabs_True__qh_1.0__ql_0.2 | change_quantiles__f_agg_"var"__isabs_True__qh_1.0__ql_0.2 | full | A/B/C/D |
| 241 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.6__ql_0.4 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.6__ql_0.4 | full | A/B/C/D |
| 242 | change_quantiles__f_agg_"var"__isabs_False__qh_0.6__ql_0.4 | change_quantiles__f_agg_"var"__isabs_False__qh_0.6__ql_0.4 | full | A/B/C/D |
| 243 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.6__ql_0.4 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.6__ql_0.4 | full | A/B/C/D |
| 244 | change_quantiles__f_agg_"var"__isabs_True__qh_0.6__ql_0.4 | change_quantiles__f_agg_"var"__isabs_True__qh_0.6__ql_0.4 | full | A/B/C/D |
| 245 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.8__ql_0.4 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.8__ql_0.4 | full | A/B/C/D |
| 246 | change_quantiles__f_agg_"var"__isabs_False__qh_0.8__ql_0.4 | change_quantiles__f_agg_"var"__isabs_False__qh_0.8__ql_0.4 | full | A/B/C/D |
| 247 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.8__ql_0.4 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.8__ql_0.4 | full | A/B/C/D |
| 248 | change_quantiles__f_agg_"var"__isabs_True__qh_0.8__ql_0.4 | change_quantiles__f_agg_"var"__isabs_True__qh_0.8__ql_0.4 | full | A/B/C/D |
| 249 | change_quantiles__f_agg_"mean"__isabs_False__qh_1.0__ql_0.4 | change_quantiles__f_agg_"mean"__isabs_False__qh_1.0__ql_0.4 | full | A/B/C/D |
| 250 | change_quantiles__f_agg_"var"__isabs_False__qh_1.0__ql_0.4 | change_quantiles__f_agg_"var"__isabs_False__qh_1.0__ql_0.4 | full | A/B/C/D |
| 251 | change_quantiles__f_agg_"mean"__isabs_True__qh_1.0__ql_0.4 | change_quantiles__f_agg_"mean"__isabs_True__qh_1.0__ql_0.4 | full | A/B/C/D |
| 252 | change_quantiles__f_agg_"var"__isabs_True__qh_1.0__ql_0.4 | change_quantiles__f_agg_"var"__isabs_True__qh_1.0__ql_0.4 | full | A/B/C/D |
| 253 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.8__ql_0.6 | change_quantiles__f_agg_"mean"__isabs_False__qh_0.8__ql_0.6 | full | A/B/C/D |
| 254 | change_quantiles__f_agg_"var"__isabs_False__qh_0.8__ql_0.6 | change_quantiles__f_agg_"var"__isabs_False__qh_0.8__ql_0.6 | full | A/B/C/D |
| 255 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.8__ql_0.6 | change_quantiles__f_agg_"mean"__isabs_True__qh_0.8__ql_0.6 | full | A/B/C/D |
| 256 | change_quantiles__f_agg_"var"__isabs_True__qh_0.8__ql_0.6 | change_quantiles__f_agg_"var"__isabs_True__qh_0.8__ql_0.6 | full | A/B/C/D |
| 257 | change_quantiles__f_agg_"mean"__isabs_False__qh_1.0__ql_0.6 | change_quantiles__f_agg_"mean"__isabs_False__qh_1.0__ql_0.6 | full | A/B/C/D |
| 258 | change_quantiles__f_agg_"var"__isabs_False__qh_1.0__ql_0.6 | change_quantiles__f_agg_"var"__isabs_False__qh_1.0__ql_0.6 | full | A/B/C/D |
| 259 | change_quantiles__f_agg_"mean"__isabs_True__qh_1.0__ql_0.6 | change_quantiles__f_agg_"mean"__isabs_True__qh_1.0__ql_0.6 | full | A/B/C/D |
| 260 | change_quantiles__f_agg_"var"__isabs_True__qh_1.0__ql_0.6 | change_quantiles__f_agg_"var"__isabs_True__qh_1.0__ql_0.6 | full | A/B/C/D |
| 261 | change_quantiles__f_agg_"mean"__isabs_False__qh_1.0__ql_0.8 | change_quantiles__f_agg_"mean"__isabs_False__qh_1.0__ql_0.8 | full | A/B/C/D |
| 262 | change_quantiles__f_agg_"var"__isabs_False__qh_1.0__ql_0.8 | change_quantiles__f_agg_"var"__isabs_False__qh_1.0__ql_0.8 | full | A/B/C/D |
| 263 | change_quantiles__f_agg_"mean"__isabs_True__qh_1.0__ql_0.8 | change_quantiles__f_agg_"mean"__isabs_True__qh_1.0__ql_0.8 | full | A/B/C/D |
| 264 | change_quantiles__f_agg_"var"__isabs_True__qh_1.0__ql_0.8 | change_quantiles__f_agg_"var"__isabs_True__qh_1.0__ql_0.8 | full | A/B/C/D |
| 265 | fft_coefficient__attr_"real"__coeff_0 | fft_coefficient__attr_"real"__coeff_0 | full | A/B/C/D |
| 266 | fft_coefficient__attr_"real"__coeff_1 | fft_coefficient__attr_"real"__coeff_1 | full | A/B/C/D |
| 267 | fft_coefficient__attr_"real"__coeff_2 | fft_coefficient__attr_"real"__coeff_2 | full | A/B/C/D |
| 268 | fft_coefficient__attr_"real"__coeff_3 | fft_coefficient__attr_"real"__coeff_3 | full | A/B/C/D |
| 269 | fft_coefficient__attr_"real"__coeff_4 | fft_coefficient__attr_"real"__coeff_4 | full | A/B/C/D |
| 270 | fft_coefficient__attr_"real"__coeff_5 | fft_coefficient__attr_"real"__coeff_5 | full | A/B/C/D |
| 271 | fft_coefficient__attr_"real"__coeff_6 | fft_coefficient__attr_"real"__coeff_6 | full | A/B/C/D |
| 272 | fft_coefficient__attr_"real"__coeff_7 | fft_coefficient__attr_"real"__coeff_7 | full | A/B/C/D |
| 273 | fft_coefficient__attr_"real"__coeff_8 | fft_coefficient__attr_"real"__coeff_8 | full | A/B/C/D |
| 274 | fft_coefficient__attr_"real"__coeff_9 | fft_coefficient__attr_"real"__coeff_9 | full | A/B/C/D |
| 275 | fft_coefficient__attr_"real"__coeff_10 | fft_coefficient__attr_"real"__coeff_10 | full | A/B/C/D |
| 276 | fft_coefficient__attr_"real"__coeff_11 | fft_coefficient__attr_"real"__coeff_11 | full | A/B/C/D |
| 277 | fft_coefficient__attr_"real"__coeff_12 | fft_coefficient__attr_"real"__coeff_12 | full | A/B/C/D |
| 278 | fft_coefficient__attr_"real"__coeff_13 | fft_coefficient__attr_"real"__coeff_13 | full | A/B/C/D |
| 279 | fft_coefficient__attr_"real"__coeff_14 | fft_coefficient__attr_"real"__coeff_14 | full | A/B/C/D |
| 280 | fft_coefficient__attr_"real"__coeff_15 | fft_coefficient__attr_"real"__coeff_15 | full | A/B/C/D |
| 281 | fft_coefficient__attr_"real"__coeff_16 | fft_coefficient__attr_"real"__coeff_16 | full | A/B/C/D |
| 282 | fft_coefficient__attr_"real"__coeff_17 | fft_coefficient__attr_"real"__coeff_17 | full | A/B/C/D |
| 283 | fft_coefficient__attr_"real"__coeff_18 | fft_coefficient__attr_"real"__coeff_18 | full | A/B/C/D |
| 284 | fft_coefficient__attr_"real"__coeff_19 | fft_coefficient__attr_"real"__coeff_19 | full | A/B/C/D |
| 285 | fft_coefficient__attr_"real"__coeff_20 | fft_coefficient__attr_"real"__coeff_20 | full | A/B/C/D |
| 286 | fft_coefficient__attr_"real"__coeff_21 | fft_coefficient__attr_"real"__coeff_21 | full | A/B/C/D |
| 287 | fft_coefficient__attr_"real"__coeff_22 | fft_coefficient__attr_"real"__coeff_22 | full | A/B/C/D |
| 288 | fft_coefficient__attr_"real"__coeff_23 | fft_coefficient__attr_"real"__coeff_23 | full | A/B/C/D |
| 289 | fft_coefficient__attr_"real"__coeff_24 | fft_coefficient__attr_"real"__coeff_24 | full | A/B/C/D |
| 290 | fft_coefficient__attr_"real"__coeff_25 | fft_coefficient__attr_"real"__coeff_25 | full | A/B/C/D |
| 291 | fft_coefficient__attr_"real"__coeff_26 | fft_coefficient__attr_"real"__coeff_26 | full | A/B/C/D |
| 292 | fft_coefficient__attr_"real"__coeff_27 | fft_coefficient__attr_"real"__coeff_27 | full | A/B/C/D |
| 293 | fft_coefficient__attr_"real"__coeff_28 | fft_coefficient__attr_"real"__coeff_28 | full | A/B/C/D |
| 294 | fft_coefficient__attr_"real"__coeff_29 | fft_coefficient__attr_"real"__coeff_29 | full | A/B/C/D |
| 295 | fft_coefficient__attr_"real"__coeff_30 | fft_coefficient__attr_"real"__coeff_30 | full | A/B/C/D |
| 296 | fft_coefficient__attr_"real"__coeff_31 | fft_coefficient__attr_"real"__coeff_31 | full | A/B/C/D |
| 297 | fft_coefficient__attr_"real"__coeff_32 | fft_coefficient__attr_"real"__coeff_32 | full | A/B/C/D |
| 298 | fft_coefficient__attr_"real"__coeff_33 | fft_coefficient__attr_"real"__coeff_33 | full | A/B/C/D |
| 299 | fft_coefficient__attr_"real"__coeff_34 | fft_coefficient__attr_"real"__coeff_34 | full | A/B/C/D |
| 300 | fft_coefficient__attr_"real"__coeff_35 | fft_coefficient__attr_"real"__coeff_35 | full | A/B/C/D |
| 301 | fft_coefficient__attr_"real"__coeff_36 | fft_coefficient__attr_"real"__coeff_36 | full | A/B/C/D |
| 302 | fft_coefficient__attr_"real"__coeff_37 | fft_coefficient__attr_"real"__coeff_37 | full | A/B/C/D |
| 303 | fft_coefficient__attr_"real"__coeff_38 | fft_coefficient__attr_"real"__coeff_38 | full | A/B/C/D |
| 304 | fft_coefficient__attr_"real"__coeff_39 | fft_coefficient__attr_"real"__coeff_39 | full | A/B/C/D |
| 305 | fft_coefficient__attr_"real"__coeff_40 | fft_coefficient__attr_"real"__coeff_40 | full | A/B/C/D |
| 306 | fft_coefficient__attr_"real"__coeff_41 | fft_coefficient__attr_"real"__coeff_41 | full | A/B/C/D |
| 307 | fft_coefficient__attr_"real"__coeff_42 | fft_coefficient__attr_"real"__coeff_42 | full | A/B/C/D |
| 308 | fft_coefficient__attr_"real"__coeff_43 | fft_coefficient__attr_"real"__coeff_43 | full | A/B/C/D |
| 309 | fft_coefficient__attr_"real"__coeff_44 | fft_coefficient__attr_"real"__coeff_44 | full | A/B/C/D |
| 310 | fft_coefficient__attr_"real"__coeff_45 | fft_coefficient__attr_"real"__coeff_45 | full | A/B/C/D |
| 311 | fft_coefficient__attr_"real"__coeff_46 | fft_coefficient__attr_"real"__coeff_46 | full | A/B/C/D |
| 312 | fft_coefficient__attr_"real"__coeff_47 | fft_coefficient__attr_"real"__coeff_47 | full | A/B/C/D |
| 313 | fft_coefficient__attr_"real"__coeff_48 | fft_coefficient__attr_"real"__coeff_48 | full | A/B/C/D |
| 314 | fft_coefficient__attr_"real"__coeff_49 | fft_coefficient__attr_"real"__coeff_49 | full | A/B/C/D |
| 315 | fft_coefficient__attr_"real"__coeff_50 | fft_coefficient__attr_"real"__coeff_50 | full | A/B/C/D |
| 316 | fft_coefficient__attr_"real"__coeff_51 | fft_coefficient__attr_"real"__coeff_51 | full | A/B/C/D |
| 317 | fft_coefficient__attr_"real"__coeff_52 | fft_coefficient__attr_"real"__coeff_52 | full | A/B/C/D |
| 318 | fft_coefficient__attr_"real"__coeff_53 | fft_coefficient__attr_"real"__coeff_53 | full | A/B/C/D |
| 319 | fft_coefficient__attr_"real"__coeff_54 | fft_coefficient__attr_"real"__coeff_54 | full | A/B/C/D |
| 320 | fft_coefficient__attr_"real"__coeff_55 | fft_coefficient__attr_"real"__coeff_55 | full | A/B/C/D |
| 321 | fft_coefficient__attr_"real"__coeff_56 | fft_coefficient__attr_"real"__coeff_56 | full | A/B/C/D |
| 322 | fft_coefficient__attr_"real"__coeff_57 | fft_coefficient__attr_"real"__coeff_57 | full | A/B/C/D |
| 323 | fft_coefficient__attr_"real"__coeff_58 | fft_coefficient__attr_"real"__coeff_58 | full | A/B/C/D |
| 324 | fft_coefficient__attr_"real"__coeff_59 | fft_coefficient__attr_"real"__coeff_59 | full | A/B/C/D |
| 325 | fft_coefficient__attr_"real"__coeff_60 | fft_coefficient__attr_"real"__coeff_60 | full | A/B/C/D |
| 326 | fft_coefficient__attr_"real"__coeff_61 | fft_coefficient__attr_"real"__coeff_61 | full | A/B/C/D |
| 327 | fft_coefficient__attr_"real"__coeff_62 | fft_coefficient__attr_"real"__coeff_62 | full | A/B/C/D |
| 328 | fft_coefficient__attr_"real"__coeff_63 | fft_coefficient__attr_"real"__coeff_63 | full | A/B/C/D |
| 329 | fft_coefficient__attr_"real"__coeff_64 | fft_coefficient__attr_"real"__coeff_64 | full | A/B/C/D |
| 330 | fft_coefficient__attr_"real"__coeff_65 | fft_coefficient__attr_"real"__coeff_65 | full | A/B/C/D |
| 331 | fft_coefficient__attr_"real"__coeff_66 | fft_coefficient__attr_"real"__coeff_66 | full | A/B/C/D |
| 332 | fft_coefficient__attr_"real"__coeff_67 | fft_coefficient__attr_"real"__coeff_67 | full | A/B/C/D |
| 333 | fft_coefficient__attr_"real"__coeff_68 | fft_coefficient__attr_"real"__coeff_68 | full | A/B/C/D |
| 334 | fft_coefficient__attr_"real"__coeff_69 | fft_coefficient__attr_"real"__coeff_69 | full | A/B/C/D |
| 335 | fft_coefficient__attr_"real"__coeff_70 | fft_coefficient__attr_"real"__coeff_70 | full | A/B/C/D |
| 336 | fft_coefficient__attr_"real"__coeff_71 | fft_coefficient__attr_"real"__coeff_71 | full | A/B/C/D |
| 337 | fft_coefficient__attr_"real"__coeff_72 | fft_coefficient__attr_"real"__coeff_72 | full | A/B/C/D |
| 338 | fft_coefficient__attr_"real"__coeff_73 | fft_coefficient__attr_"real"__coeff_73 | full | A/B/C/D |
| 339 | fft_coefficient__attr_"real"__coeff_74 | fft_coefficient__attr_"real"__coeff_74 | full | A/B/C/D |
| 340 | fft_coefficient__attr_"real"__coeff_75 | fft_coefficient__attr_"real"__coeff_75 | full | A/B/C/D |
| 341 | fft_coefficient__attr_"real"__coeff_76 | fft_coefficient__attr_"real"__coeff_76 | full | A/B/C/D |
| 342 | fft_coefficient__attr_"real"__coeff_77 | fft_coefficient__attr_"real"__coeff_77 | full | A/B/C/D |
| 343 | fft_coefficient__attr_"real"__coeff_78 | fft_coefficient__attr_"real"__coeff_78 | full | A/B/C/D |
| 344 | fft_coefficient__attr_"real"__coeff_79 | fft_coefficient__attr_"real"__coeff_79 | full | A/B/C/D |
| 345 | fft_coefficient__attr_"real"__coeff_80 | fft_coefficient__attr_"real"__coeff_80 | full | A/B/C/D |
| 346 | fft_coefficient__attr_"real"__coeff_81 | fft_coefficient__attr_"real"__coeff_81 | full | A/B/C/D |
| 347 | fft_coefficient__attr_"real"__coeff_82 | fft_coefficient__attr_"real"__coeff_82 | full | A/B/C/D |
| 348 | fft_coefficient__attr_"real"__coeff_83 | fft_coefficient__attr_"real"__coeff_83 | full | A/B/C/D |
| 349 | fft_coefficient__attr_"real"__coeff_84 | fft_coefficient__attr_"real"__coeff_84 | full | A/B/C/D |
| 350 | fft_coefficient__attr_"real"__coeff_85 | fft_coefficient__attr_"real"__coeff_85 | full | A/B/C/D |
| 351 | fft_coefficient__attr_"real"__coeff_86 | fft_coefficient__attr_"real"__coeff_86 | full | A/B/C/D |
| 352 | fft_coefficient__attr_"real"__coeff_87 | fft_coefficient__attr_"real"__coeff_87 | full | A/B/C/D |
| 353 | fft_coefficient__attr_"real"__coeff_88 | fft_coefficient__attr_"real"__coeff_88 | full | A/B/C/D |
| 354 | fft_coefficient__attr_"real"__coeff_89 | fft_coefficient__attr_"real"__coeff_89 | full | A/B/C/D |
| 355 | fft_coefficient__attr_"real"__coeff_90 | fft_coefficient__attr_"real"__coeff_90 | full | A/B/C/D |
| 356 | fft_coefficient__attr_"real"__coeff_91 | fft_coefficient__attr_"real"__coeff_91 | full | A/B/C/D |
| 357 | fft_coefficient__attr_"real"__coeff_92 | fft_coefficient__attr_"real"__coeff_92 | full | A/B/C/D |
| 358 | fft_coefficient__attr_"real"__coeff_93 | fft_coefficient__attr_"real"__coeff_93 | full | A/B/C/D |
| 359 | fft_coefficient__attr_"real"__coeff_94 | fft_coefficient__attr_"real"__coeff_94 | full | A/B/C/D |
| 360 | fft_coefficient__attr_"real"__coeff_95 | fft_coefficient__attr_"real"__coeff_95 | full | A/B/C/D |
| 361 | fft_coefficient__attr_"real"__coeff_96 | fft_coefficient__attr_"real"__coeff_96 | full | A/B/C/D |
| 362 | fft_coefficient__attr_"real"__coeff_97 | fft_coefficient__attr_"real"__coeff_97 | full | A/B/C/D |
| 363 | fft_coefficient__attr_"real"__coeff_98 | fft_coefficient__attr_"real"__coeff_98 | full | A/B/C/D |
| 364 | fft_coefficient__attr_"real"__coeff_99 | fft_coefficient__attr_"real"__coeff_99 | full | A/B/C/D |
| 365 | fft_coefficient__attr_"imag"__coeff_0 | fft_coefficient__attr_"imag"__coeff_0 | full | A/B/C/D |
| 366 | fft_coefficient__attr_"imag"__coeff_1 | fft_coefficient__attr_"imag"__coeff_1 | full | A/B/C/D |
| 367 | fft_coefficient__attr_"imag"__coeff_2 | fft_coefficient__attr_"imag"__coeff_2 | full | A/B/C/D |
| 368 | fft_coefficient__attr_"imag"__coeff_3 | fft_coefficient__attr_"imag"__coeff_3 | full | A/B/C/D |
| 369 | fft_coefficient__attr_"imag"__coeff_4 | fft_coefficient__attr_"imag"__coeff_4 | full | A/B/C/D |
| 370 | fft_coefficient__attr_"imag"__coeff_5 | fft_coefficient__attr_"imag"__coeff_5 | full | A/B/C/D |
| 371 | fft_coefficient__attr_"imag"__coeff_6 | fft_coefficient__attr_"imag"__coeff_6 | full | A/B/C/D |
| 372 | fft_coefficient__attr_"imag"__coeff_7 | fft_coefficient__attr_"imag"__coeff_7 | full | A/B/C/D |
| 373 | fft_coefficient__attr_"imag"__coeff_8 | fft_coefficient__attr_"imag"__coeff_8 | full | A/B/C/D |
| 374 | fft_coefficient__attr_"imag"__coeff_9 | fft_coefficient__attr_"imag"__coeff_9 | full | A/B/C/D |
| 375 | fft_coefficient__attr_"imag"__coeff_10 | fft_coefficient__attr_"imag"__coeff_10 | full | A/B/C/D |
| 376 | fft_coefficient__attr_"imag"__coeff_11 | fft_coefficient__attr_"imag"__coeff_11 | full | A/B/C/D |
| 377 | fft_coefficient__attr_"imag"__coeff_12 | fft_coefficient__attr_"imag"__coeff_12 | full | A/B/C/D |
| 378 | fft_coefficient__attr_"imag"__coeff_13 | fft_coefficient__attr_"imag"__coeff_13 | full | A/B/C/D |
| 379 | fft_coefficient__attr_"imag"__coeff_14 | fft_coefficient__attr_"imag"__coeff_14 | full | A/B/C/D |
| 380 | fft_coefficient__attr_"imag"__coeff_15 | fft_coefficient__attr_"imag"__coeff_15 | full | A/B/C/D |
| 381 | fft_coefficient__attr_"imag"__coeff_16 | fft_coefficient__attr_"imag"__coeff_16 | full | A/B/C/D |
| 382 | fft_coefficient__attr_"imag"__coeff_17 | fft_coefficient__attr_"imag"__coeff_17 | full | A/B/C/D |
| 383 | fft_coefficient__attr_"imag"__coeff_18 | fft_coefficient__attr_"imag"__coeff_18 | full | A/B/C/D |
| 384 | fft_coefficient__attr_"imag"__coeff_19 | fft_coefficient__attr_"imag"__coeff_19 | full | A/B/C/D |
| 385 | fft_coefficient__attr_"imag"__coeff_20 | fft_coefficient__attr_"imag"__coeff_20 | full | A/B/C/D |
| 386 | fft_coefficient__attr_"imag"__coeff_21 | fft_coefficient__attr_"imag"__coeff_21 | full | A/B/C/D |
| 387 | fft_coefficient__attr_"imag"__coeff_22 | fft_coefficient__attr_"imag"__coeff_22 | full | A/B/C/D |
| 388 | fft_coefficient__attr_"imag"__coeff_23 | fft_coefficient__attr_"imag"__coeff_23 | full | A/B/C/D |
| 389 | fft_coefficient__attr_"imag"__coeff_24 | fft_coefficient__attr_"imag"__coeff_24 | full | A/B/C/D |
| 390 | fft_coefficient__attr_"imag"__coeff_25 | fft_coefficient__attr_"imag"__coeff_25 | full | A/B/C/D |
| 391 | fft_coefficient__attr_"imag"__coeff_26 | fft_coefficient__attr_"imag"__coeff_26 | full | A/B/C/D |
| 392 | fft_coefficient__attr_"imag"__coeff_27 | fft_coefficient__attr_"imag"__coeff_27 | full | A/B/C/D |
| 393 | fft_coefficient__attr_"imag"__coeff_28 | fft_coefficient__attr_"imag"__coeff_28 | full | A/B/C/D |
| 394 | fft_coefficient__attr_"imag"__coeff_29 | fft_coefficient__attr_"imag"__coeff_29 | full | A/B/C/D |
| 395 | fft_coefficient__attr_"imag"__coeff_30 | fft_coefficient__attr_"imag"__coeff_30 | full | A/B/C/D |
| 396 | fft_coefficient__attr_"imag"__coeff_31 | fft_coefficient__attr_"imag"__coeff_31 | full | A/B/C/D |
| 397 | fft_coefficient__attr_"imag"__coeff_32 | fft_coefficient__attr_"imag"__coeff_32 | full | A/B/C/D |
| 398 | fft_coefficient__attr_"imag"__coeff_33 | fft_coefficient__attr_"imag"__coeff_33 | full | A/B/C/D |
| 399 | fft_coefficient__attr_"imag"__coeff_34 | fft_coefficient__attr_"imag"__coeff_34 | full | A/B/C/D |
| 400 | fft_coefficient__attr_"imag"__coeff_35 | fft_coefficient__attr_"imag"__coeff_35 | full | A/B/C/D |
| 401 | fft_coefficient__attr_"imag"__coeff_36 | fft_coefficient__attr_"imag"__coeff_36 | full | A/B/C/D |
| 402 | fft_coefficient__attr_"imag"__coeff_37 | fft_coefficient__attr_"imag"__coeff_37 | full | A/B/C/D |
| 403 | fft_coefficient__attr_"imag"__coeff_38 | fft_coefficient__attr_"imag"__coeff_38 | full | A/B/C/D |
| 404 | fft_coefficient__attr_"imag"__coeff_39 | fft_coefficient__attr_"imag"__coeff_39 | full | A/B/C/D |
| 405 | fft_coefficient__attr_"imag"__coeff_40 | fft_coefficient__attr_"imag"__coeff_40 | full | A/B/C/D |
| 406 | fft_coefficient__attr_"imag"__coeff_41 | fft_coefficient__attr_"imag"__coeff_41 | full | A/B/C/D |
| 407 | fft_coefficient__attr_"imag"__coeff_42 | fft_coefficient__attr_"imag"__coeff_42 | full | A/B/C/D |
| 408 | fft_coefficient__attr_"imag"__coeff_43 | fft_coefficient__attr_"imag"__coeff_43 | full | A/B/C/D |
| 409 | fft_coefficient__attr_"imag"__coeff_44 | fft_coefficient__attr_"imag"__coeff_44 | full | A/B/C/D |
| 410 | fft_coefficient__attr_"imag"__coeff_45 | fft_coefficient__attr_"imag"__coeff_45 | full | A/B/C/D |
| 411 | fft_coefficient__attr_"imag"__coeff_46 | fft_coefficient__attr_"imag"__coeff_46 | full | A/B/C/D |
| 412 | fft_coefficient__attr_"imag"__coeff_47 | fft_coefficient__attr_"imag"__coeff_47 | full | A/B/C/D |
| 413 | fft_coefficient__attr_"imag"__coeff_48 | fft_coefficient__attr_"imag"__coeff_48 | full | A/B/C/D |
| 414 | fft_coefficient__attr_"imag"__coeff_49 | fft_coefficient__attr_"imag"__coeff_49 | full | A/B/C/D |
| 415 | fft_coefficient__attr_"imag"__coeff_50 | fft_coefficient__attr_"imag"__coeff_50 | full | A/B/C/D |
| 416 | fft_coefficient__attr_"imag"__coeff_51 | fft_coefficient__attr_"imag"__coeff_51 | full | A/B/C/D |
| 417 | fft_coefficient__attr_"imag"__coeff_52 | fft_coefficient__attr_"imag"__coeff_52 | full | A/B/C/D |
| 418 | fft_coefficient__attr_"imag"__coeff_53 | fft_coefficient__attr_"imag"__coeff_53 | full | A/B/C/D |
| 419 | fft_coefficient__attr_"imag"__coeff_54 | fft_coefficient__attr_"imag"__coeff_54 | full | A/B/C/D |
| 420 | fft_coefficient__attr_"imag"__coeff_55 | fft_coefficient__attr_"imag"__coeff_55 | full | A/B/C/D |
| 421 | fft_coefficient__attr_"imag"__coeff_56 | fft_coefficient__attr_"imag"__coeff_56 | full | A/B/C/D |
| 422 | fft_coefficient__attr_"imag"__coeff_57 | fft_coefficient__attr_"imag"__coeff_57 | full | A/B/C/D |
| 423 | fft_coefficient__attr_"imag"__coeff_58 | fft_coefficient__attr_"imag"__coeff_58 | full | A/B/C/D |
| 424 | fft_coefficient__attr_"imag"__coeff_59 | fft_coefficient__attr_"imag"__coeff_59 | full | A/B/C/D |
| 425 | fft_coefficient__attr_"imag"__coeff_60 | fft_coefficient__attr_"imag"__coeff_60 | full | A/B/C/D |
| 426 | fft_coefficient__attr_"imag"__coeff_61 | fft_coefficient__attr_"imag"__coeff_61 | full | A/B/C/D |
| 427 | fft_coefficient__attr_"imag"__coeff_62 | fft_coefficient__attr_"imag"__coeff_62 | full | A/B/C/D |
| 428 | fft_coefficient__attr_"imag"__coeff_63 | fft_coefficient__attr_"imag"__coeff_63 | full | A/B/C/D |
| 429 | fft_coefficient__attr_"imag"__coeff_64 | fft_coefficient__attr_"imag"__coeff_64 | full | A/B/C/D |
| 430 | fft_coefficient__attr_"imag"__coeff_65 | fft_coefficient__attr_"imag"__coeff_65 | full | A/B/C/D |
| 431 | fft_coefficient__attr_"imag"__coeff_66 | fft_coefficient__attr_"imag"__coeff_66 | full | A/B/C/D |
| 432 | fft_coefficient__attr_"imag"__coeff_67 | fft_coefficient__attr_"imag"__coeff_67 | full | A/B/C/D |
| 433 | fft_coefficient__attr_"imag"__coeff_68 | fft_coefficient__attr_"imag"__coeff_68 | full | A/B/C/D |
| 434 | fft_coefficient__attr_"imag"__coeff_69 | fft_coefficient__attr_"imag"__coeff_69 | full | A/B/C/D |
| 435 | fft_coefficient__attr_"imag"__coeff_70 | fft_coefficient__attr_"imag"__coeff_70 | full | A/B/C/D |
| 436 | fft_coefficient__attr_"imag"__coeff_71 | fft_coefficient__attr_"imag"__coeff_71 | full | A/B/C/D |
| 437 | fft_coefficient__attr_"imag"__coeff_72 | fft_coefficient__attr_"imag"__coeff_72 | full | A/B/C/D |
| 438 | fft_coefficient__attr_"imag"__coeff_73 | fft_coefficient__attr_"imag"__coeff_73 | full | A/B/C/D |
| 439 | fft_coefficient__attr_"imag"__coeff_74 | fft_coefficient__attr_"imag"__coeff_74 | full | A/B/C/D |
| 440 | fft_coefficient__attr_"imag"__coeff_75 | fft_coefficient__attr_"imag"__coeff_75 | full | A/B/C/D |
| 441 | fft_coefficient__attr_"imag"__coeff_76 | fft_coefficient__attr_"imag"__coeff_76 | full | A/B/C/D |
| 442 | fft_coefficient__attr_"imag"__coeff_77 | fft_coefficient__attr_"imag"__coeff_77 | full | A/B/C/D |
| 443 | fft_coefficient__attr_"imag"__coeff_78 | fft_coefficient__attr_"imag"__coeff_78 | full | A/B/C/D |
| 444 | fft_coefficient__attr_"imag"__coeff_79 | fft_coefficient__attr_"imag"__coeff_79 | full | A/B/C/D |
| 445 | fft_coefficient__attr_"imag"__coeff_80 | fft_coefficient__attr_"imag"__coeff_80 | full | A/B/C/D |
| 446 | fft_coefficient__attr_"imag"__coeff_81 | fft_coefficient__attr_"imag"__coeff_81 | full | A/B/C/D |
| 447 | fft_coefficient__attr_"imag"__coeff_82 | fft_coefficient__attr_"imag"__coeff_82 | full | A/B/C/D |
| 448 | fft_coefficient__attr_"imag"__coeff_83 | fft_coefficient__attr_"imag"__coeff_83 | full | A/B/C/D |
| 449 | fft_coefficient__attr_"imag"__coeff_84 | fft_coefficient__attr_"imag"__coeff_84 | full | A/B/C/D |
| 450 | fft_coefficient__attr_"imag"__coeff_85 | fft_coefficient__attr_"imag"__coeff_85 | full | A/B/C/D |
| 451 | fft_coefficient__attr_"imag"__coeff_86 | fft_coefficient__attr_"imag"__coeff_86 | full | A/B/C/D |
| 452 | fft_coefficient__attr_"imag"__coeff_87 | fft_coefficient__attr_"imag"__coeff_87 | full | A/B/C/D |
| 453 | fft_coefficient__attr_"imag"__coeff_88 | fft_coefficient__attr_"imag"__coeff_88 | full | A/B/C/D |
| 454 | fft_coefficient__attr_"imag"__coeff_89 | fft_coefficient__attr_"imag"__coeff_89 | full | A/B/C/D |
| 455 | fft_coefficient__attr_"imag"__coeff_90 | fft_coefficient__attr_"imag"__coeff_90 | full | A/B/C/D |
| 456 | fft_coefficient__attr_"imag"__coeff_91 | fft_coefficient__attr_"imag"__coeff_91 | full | A/B/C/D |
| 457 | fft_coefficient__attr_"imag"__coeff_92 | fft_coefficient__attr_"imag"__coeff_92 | full | A/B/C/D |
| 458 | fft_coefficient__attr_"imag"__coeff_93 | fft_coefficient__attr_"imag"__coeff_93 | full | A/B/C/D |
| 459 | fft_coefficient__attr_"imag"__coeff_94 | fft_coefficient__attr_"imag"__coeff_94 | full | A/B/C/D |
| 460 | fft_coefficient__attr_"imag"__coeff_95 | fft_coefficient__attr_"imag"__coeff_95 | full | A/B/C/D |
| 461 | fft_coefficient__attr_"imag"__coeff_96 | fft_coefficient__attr_"imag"__coeff_96 | full | A/B/C/D |
| 462 | fft_coefficient__attr_"imag"__coeff_97 | fft_coefficient__attr_"imag"__coeff_97 | full | A/B/C/D |
| 463 | fft_coefficient__attr_"imag"__coeff_98 | fft_coefficient__attr_"imag"__coeff_98 | full | A/B/C/D |
| 464 | fft_coefficient__attr_"imag"__coeff_99 | fft_coefficient__attr_"imag"__coeff_99 | full | A/B/C/D |
| 465 | fft_coefficient__attr_"abs"__coeff_0 | fft_coefficient__attr_"abs"__coeff_0 | full | A/B/C/D |
| 466 | fft_coefficient__attr_"abs"__coeff_1 | fft_coefficient__attr_"abs"__coeff_1 | full | A/B/C/D |
| 467 | fft_coefficient__attr_"abs"__coeff_2 | fft_coefficient__attr_"abs"__coeff_2 | full | A/B/C/D |
| 468 | fft_coefficient__attr_"abs"__coeff_3 | fft_coefficient__attr_"abs"__coeff_3 | full | A/B/C/D |
| 469 | fft_coefficient__attr_"abs"__coeff_4 | fft_coefficient__attr_"abs"__coeff_4 | full | A/B/C/D |
| 470 | fft_coefficient__attr_"abs"__coeff_5 | fft_coefficient__attr_"abs"__coeff_5 | full | A/B/C/D |
| 471 | fft_coefficient__attr_"abs"__coeff_6 | fft_coefficient__attr_"abs"__coeff_6 | full | A/B/C/D |
| 472 | fft_coefficient__attr_"abs"__coeff_7 | fft_coefficient__attr_"abs"__coeff_7 | full | A/B/C/D |
| 473 | fft_coefficient__attr_"abs"__coeff_8 | fft_coefficient__attr_"abs"__coeff_8 | full | A/B/C/D |
| 474 | fft_coefficient__attr_"abs"__coeff_9 | fft_coefficient__attr_"abs"__coeff_9 | full | A/B/C/D |
| 475 | fft_coefficient__attr_"abs"__coeff_10 | fft_coefficient__attr_"abs"__coeff_10 | full | A/B/C/D |
| 476 | fft_coefficient__attr_"abs"__coeff_11 | fft_coefficient__attr_"abs"__coeff_11 | full | A/B/C/D |
| 477 | fft_coefficient__attr_"abs"__coeff_12 | fft_coefficient__attr_"abs"__coeff_12 | full | A/B/C/D |
| 478 | fft_coefficient__attr_"abs"__coeff_13 | fft_coefficient__attr_"abs"__coeff_13 | full | A/B/C/D |
| 479 | fft_coefficient__attr_"abs"__coeff_14 | fft_coefficient__attr_"abs"__coeff_14 | full | A/B/C/D |
| 480 | fft_coefficient__attr_"abs"__coeff_15 | fft_coefficient__attr_"abs"__coeff_15 | full | A/B/C/D |
| 481 | fft_coefficient__attr_"abs"__coeff_16 | fft_coefficient__attr_"abs"__coeff_16 | full | A/B/C/D |
| 482 | fft_coefficient__attr_"abs"__coeff_17 | fft_coefficient__attr_"abs"__coeff_17 | full | A/B/C/D |
| 483 | fft_coefficient__attr_"abs"__coeff_18 | fft_coefficient__attr_"abs"__coeff_18 | full | A/B/C/D |
| 484 | fft_coefficient__attr_"abs"__coeff_19 | fft_coefficient__attr_"abs"__coeff_19 | full | A/B/C/D |
| 485 | fft_coefficient__attr_"abs"__coeff_20 | fft_coefficient__attr_"abs"__coeff_20 | full | A/B/C/D |
| 486 | fft_coefficient__attr_"abs"__coeff_21 | fft_coefficient__attr_"abs"__coeff_21 | full | A/B/C/D |
| 487 | fft_coefficient__attr_"abs"__coeff_22 | fft_coefficient__attr_"abs"__coeff_22 | full | A/B/C/D |
| 488 | fft_coefficient__attr_"abs"__coeff_23 | fft_coefficient__attr_"abs"__coeff_23 | full | A/B/C/D |
| 489 | fft_coefficient__attr_"abs"__coeff_24 | fft_coefficient__attr_"abs"__coeff_24 | full | A/B/C/D |
| 490 | fft_coefficient__attr_"abs"__coeff_25 | fft_coefficient__attr_"abs"__coeff_25 | full | A/B/C/D |
| 491 | fft_coefficient__attr_"abs"__coeff_26 | fft_coefficient__attr_"abs"__coeff_26 | full | A/B/C/D |
| 492 | fft_coefficient__attr_"abs"__coeff_27 | fft_coefficient__attr_"abs"__coeff_27 | full | A/B/C/D |
| 493 | fft_coefficient__attr_"abs"__coeff_28 | fft_coefficient__attr_"abs"__coeff_28 | full | A/B/C/D |
| 494 | fft_coefficient__attr_"abs"__coeff_29 | fft_coefficient__attr_"abs"__coeff_29 | full | A/B/C/D |
| 495 | fft_coefficient__attr_"abs"__coeff_30 | fft_coefficient__attr_"abs"__coeff_30 | full | A/B/C/D |
| 496 | fft_coefficient__attr_"abs"__coeff_31 | fft_coefficient__attr_"abs"__coeff_31 | full | A/B/C/D |
| 497 | fft_coefficient__attr_"abs"__coeff_32 | fft_coefficient__attr_"abs"__coeff_32 | full | A/B/C/D |
| 498 | fft_coefficient__attr_"abs"__coeff_33 | fft_coefficient__attr_"abs"__coeff_33 | full | A/B/C/D |
| 499 | fft_coefficient__attr_"abs"__coeff_34 | fft_coefficient__attr_"abs"__coeff_34 | full | A/B/C/D |
| 500 | fft_coefficient__attr_"abs"__coeff_35 | fft_coefficient__attr_"abs"__coeff_35 | full | A/B/C/D |
| 501 | fft_coefficient__attr_"abs"__coeff_36 | fft_coefficient__attr_"abs"__coeff_36 | full | A/B/C/D |
| 502 | fft_coefficient__attr_"abs"__coeff_37 | fft_coefficient__attr_"abs"__coeff_37 | full | A/B/C/D |
| 503 | fft_coefficient__attr_"abs"__coeff_38 | fft_coefficient__attr_"abs"__coeff_38 | full | A/B/C/D |
| 504 | fft_coefficient__attr_"abs"__coeff_39 | fft_coefficient__attr_"abs"__coeff_39 | full | A/B/C/D |
| 505 | fft_coefficient__attr_"abs"__coeff_40 | fft_coefficient__attr_"abs"__coeff_40 | full | A/B/C/D |
| 506 | fft_coefficient__attr_"abs"__coeff_41 | fft_coefficient__attr_"abs"__coeff_41 | full | A/B/C/D |
| 507 | fft_coefficient__attr_"abs"__coeff_42 | fft_coefficient__attr_"abs"__coeff_42 | full | A/B/C/D |
| 508 | fft_coefficient__attr_"abs"__coeff_43 | fft_coefficient__attr_"abs"__coeff_43 | full | A/B/C/D |
| 509 | fft_coefficient__attr_"abs"__coeff_44 | fft_coefficient__attr_"abs"__coeff_44 | full | A/B/C/D |
| 510 | fft_coefficient__attr_"abs"__coeff_45 | fft_coefficient__attr_"abs"__coeff_45 | full | A/B/C/D |
| 511 | fft_coefficient__attr_"abs"__coeff_46 | fft_coefficient__attr_"abs"__coeff_46 | full | A/B/C/D |
| 512 | fft_coefficient__attr_"abs"__coeff_47 | fft_coefficient__attr_"abs"__coeff_47 | full | A/B/C/D |
| 513 | fft_coefficient__attr_"abs"__coeff_48 | fft_coefficient__attr_"abs"__coeff_48 | full | A/B/C/D |
| 514 | fft_coefficient__attr_"abs"__coeff_49 | fft_coefficient__attr_"abs"__coeff_49 | full | A/B/C/D |
| 515 | fft_coefficient__attr_"abs"__coeff_50 | fft_coefficient__attr_"abs"__coeff_50 | full | A/B/C/D |
| 516 | fft_coefficient__attr_"abs"__coeff_51 | fft_coefficient__attr_"abs"__coeff_51 | full | A/B/C/D |
| 517 | fft_coefficient__attr_"abs"__coeff_52 | fft_coefficient__attr_"abs"__coeff_52 | full | A/B/C/D |
| 518 | fft_coefficient__attr_"abs"__coeff_53 | fft_coefficient__attr_"abs"__coeff_53 | full | A/B/C/D |
| 519 | fft_coefficient__attr_"abs"__coeff_54 | fft_coefficient__attr_"abs"__coeff_54 | full | A/B/C/D |
| 520 | fft_coefficient__attr_"abs"__coeff_55 | fft_coefficient__attr_"abs"__coeff_55 | full | A/B/C/D |
| 521 | fft_coefficient__attr_"abs"__coeff_56 | fft_coefficient__attr_"abs"__coeff_56 | full | A/B/C/D |
| 522 | fft_coefficient__attr_"abs"__coeff_57 | fft_coefficient__attr_"abs"__coeff_57 | full | A/B/C/D |
| 523 | fft_coefficient__attr_"abs"__coeff_58 | fft_coefficient__attr_"abs"__coeff_58 | full | A/B/C/D |
| 524 | fft_coefficient__attr_"abs"__coeff_59 | fft_coefficient__attr_"abs"__coeff_59 | full | A/B/C/D |
| 525 | fft_coefficient__attr_"abs"__coeff_60 | fft_coefficient__attr_"abs"__coeff_60 | full | A/B/C/D |
| 526 | fft_coefficient__attr_"abs"__coeff_61 | fft_coefficient__attr_"abs"__coeff_61 | full | A/B/C/D |
| 527 | fft_coefficient__attr_"abs"__coeff_62 | fft_coefficient__attr_"abs"__coeff_62 | full | A/B/C/D |
| 528 | fft_coefficient__attr_"abs"__coeff_63 | fft_coefficient__attr_"abs"__coeff_63 | full | A/B/C/D |
| 529 | fft_coefficient__attr_"abs"__coeff_64 | fft_coefficient__attr_"abs"__coeff_64 | full | A/B/C/D |
| 530 | fft_coefficient__attr_"abs"__coeff_65 | fft_coefficient__attr_"abs"__coeff_65 | full | A/B/C/D |
| 531 | fft_coefficient__attr_"abs"__coeff_66 | fft_coefficient__attr_"abs"__coeff_66 | full | A/B/C/D |
| 532 | fft_coefficient__attr_"abs"__coeff_67 | fft_coefficient__attr_"abs"__coeff_67 | full | A/B/C/D |
| 533 | fft_coefficient__attr_"abs"__coeff_68 | fft_coefficient__attr_"abs"__coeff_68 | full | A/B/C/D |
| 534 | fft_coefficient__attr_"abs"__coeff_69 | fft_coefficient__attr_"abs"__coeff_69 | full | A/B/C/D |
| 535 | fft_coefficient__attr_"abs"__coeff_70 | fft_coefficient__attr_"abs"__coeff_70 | full | A/B/C/D |
| 536 | fft_coefficient__attr_"abs"__coeff_71 | fft_coefficient__attr_"abs"__coeff_71 | full | A/B/C/D |
| 537 | fft_coefficient__attr_"abs"__coeff_72 | fft_coefficient__attr_"abs"__coeff_72 | full | A/B/C/D |
| 538 | fft_coefficient__attr_"abs"__coeff_73 | fft_coefficient__attr_"abs"__coeff_73 | full | A/B/C/D |
| 539 | fft_coefficient__attr_"abs"__coeff_74 | fft_coefficient__attr_"abs"__coeff_74 | full | A/B/C/D |
| 540 | fft_coefficient__attr_"abs"__coeff_75 | fft_coefficient__attr_"abs"__coeff_75 | full | A/B/C/D |
| 541 | fft_coefficient__attr_"abs"__coeff_76 | fft_coefficient__attr_"abs"__coeff_76 | full | A/B/C/D |
| 542 | fft_coefficient__attr_"abs"__coeff_77 | fft_coefficient__attr_"abs"__coeff_77 | full | A/B/C/D |
| 543 | fft_coefficient__attr_"abs"__coeff_78 | fft_coefficient__attr_"abs"__coeff_78 | full | A/B/C/D |
| 544 | fft_coefficient__attr_"abs"__coeff_79 | fft_coefficient__attr_"abs"__coeff_79 | full | A/B/C/D |
| 545 | fft_coefficient__attr_"abs"__coeff_80 | fft_coefficient__attr_"abs"__coeff_80 | full | A/B/C/D |
| 546 | fft_coefficient__attr_"abs"__coeff_81 | fft_coefficient__attr_"abs"__coeff_81 | full | A/B/C/D |
| 547 | fft_coefficient__attr_"abs"__coeff_82 | fft_coefficient__attr_"abs"__coeff_82 | full | A/B/C/D |
| 548 | fft_coefficient__attr_"abs"__coeff_83 | fft_coefficient__attr_"abs"__coeff_83 | full | A/B/C/D |
| 549 | fft_coefficient__attr_"abs"__coeff_84 | fft_coefficient__attr_"abs"__coeff_84 | full | A/B/C/D |
| 550 | fft_coefficient__attr_"abs"__coeff_85 | fft_coefficient__attr_"abs"__coeff_85 | full | A/B/C/D |
| 551 | fft_coefficient__attr_"abs"__coeff_86 | fft_coefficient__attr_"abs"__coeff_86 | full | A/B/C/D |
| 552 | fft_coefficient__attr_"abs"__coeff_87 | fft_coefficient__attr_"abs"__coeff_87 | full | A/B/C/D |
| 553 | fft_coefficient__attr_"abs"__coeff_88 | fft_coefficient__attr_"abs"__coeff_88 | full | A/B/C/D |
| 554 | fft_coefficient__attr_"abs"__coeff_89 | fft_coefficient__attr_"abs"__coeff_89 | full | A/B/C/D |
| 555 | fft_coefficient__attr_"abs"__coeff_90 | fft_coefficient__attr_"abs"__coeff_90 | full | A/B/C/D |
| 556 | fft_coefficient__attr_"abs"__coeff_91 | fft_coefficient__attr_"abs"__coeff_91 | full | A/B/C/D |
| 557 | fft_coefficient__attr_"abs"__coeff_92 | fft_coefficient__attr_"abs"__coeff_92 | full | A/B/C/D |
| 558 | fft_coefficient__attr_"abs"__coeff_93 | fft_coefficient__attr_"abs"__coeff_93 | full | A/B/C/D |
| 559 | fft_coefficient__attr_"abs"__coeff_94 | fft_coefficient__attr_"abs"__coeff_94 | full | A/B/C/D |
| 560 | fft_coefficient__attr_"abs"__coeff_95 | fft_coefficient__attr_"abs"__coeff_95 | full | A/B/C/D |
| 561 | fft_coefficient__attr_"abs"__coeff_96 | fft_coefficient__attr_"abs"__coeff_96 | full | A/B/C/D |
| 562 | fft_coefficient__attr_"abs"__coeff_97 | fft_coefficient__attr_"abs"__coeff_97 | full | A/B/C/D |
| 563 | fft_coefficient__attr_"abs"__coeff_98 | fft_coefficient__attr_"abs"__coeff_98 | full | A/B/C/D |
| 564 | fft_coefficient__attr_"abs"__coeff_99 | fft_coefficient__attr_"abs"__coeff_99 | full | A/B/C/D |
| 565 | fft_coefficient__attr_"angle"__coeff_0 | fft_coefficient__attr_"angle"__coeff_0 | full | A/B/C/D |
| 566 | fft_coefficient__attr_"angle"__coeff_1 | fft_coefficient__attr_"angle"__coeff_1 | full | A/B/C/D |
| 567 | fft_coefficient__attr_"angle"__coeff_2 | fft_coefficient__attr_"angle"__coeff_2 | full | A/B/C/D |
| 568 | fft_coefficient__attr_"angle"__coeff_3 | fft_coefficient__attr_"angle"__coeff_3 | full | A/B/C/D |
| 569 | fft_coefficient__attr_"angle"__coeff_4 | fft_coefficient__attr_"angle"__coeff_4 | full | A/B/C/D |
| 570 | fft_coefficient__attr_"angle"__coeff_5 | fft_coefficient__attr_"angle"__coeff_5 | full | A/B/C/D |
| 571 | fft_coefficient__attr_"angle"__coeff_6 | fft_coefficient__attr_"angle"__coeff_6 | full | A/B/C/D |
| 572 | fft_coefficient__attr_"angle"__coeff_7 | fft_coefficient__attr_"angle"__coeff_7 | full | A/B/C/D |
| 573 | fft_coefficient__attr_"angle"__coeff_8 | fft_coefficient__attr_"angle"__coeff_8 | full | A/B/C/D |
| 574 | fft_coefficient__attr_"angle"__coeff_9 | fft_coefficient__attr_"angle"__coeff_9 | full | A/B/C/D |
| 575 | fft_coefficient__attr_"angle"__coeff_10 | fft_coefficient__attr_"angle"__coeff_10 | full | A/B/C/D |
| 576 | fft_coefficient__attr_"angle"__coeff_11 | fft_coefficient__attr_"angle"__coeff_11 | full | A/B/C/D |
| 577 | fft_coefficient__attr_"angle"__coeff_12 | fft_coefficient__attr_"angle"__coeff_12 | full | A/B/C/D |
| 578 | fft_coefficient__attr_"angle"__coeff_13 | fft_coefficient__attr_"angle"__coeff_13 | full | A/B/C/D |
| 579 | fft_coefficient__attr_"angle"__coeff_14 | fft_coefficient__attr_"angle"__coeff_14 | full | A/B/C/D |
| 580 | fft_coefficient__attr_"angle"__coeff_15 | fft_coefficient__attr_"angle"__coeff_15 | full | A/B/C/D |
| 581 | fft_coefficient__attr_"angle"__coeff_16 | fft_coefficient__attr_"angle"__coeff_16 | full | A/B/C/D |
| 582 | fft_coefficient__attr_"angle"__coeff_17 | fft_coefficient__attr_"angle"__coeff_17 | full | A/B/C/D |
| 583 | fft_coefficient__attr_"angle"__coeff_18 | fft_coefficient__attr_"angle"__coeff_18 | full | A/B/C/D |
| 584 | fft_coefficient__attr_"angle"__coeff_19 | fft_coefficient__attr_"angle"__coeff_19 | full | A/B/C/D |
| 585 | fft_coefficient__attr_"angle"__coeff_20 | fft_coefficient__attr_"angle"__coeff_20 | full | A/B/C/D |
| 586 | fft_coefficient__attr_"angle"__coeff_21 | fft_coefficient__attr_"angle"__coeff_21 | full | A/B/C/D |
| 587 | fft_coefficient__attr_"angle"__coeff_22 | fft_coefficient__attr_"angle"__coeff_22 | full | A/B/C/D |
| 588 | fft_coefficient__attr_"angle"__coeff_23 | fft_coefficient__attr_"angle"__coeff_23 | full | A/B/C/D |
| 589 | fft_coefficient__attr_"angle"__coeff_24 | fft_coefficient__attr_"angle"__coeff_24 | full | A/B/C/D |
| 590 | fft_coefficient__attr_"angle"__coeff_25 | fft_coefficient__attr_"angle"__coeff_25 | full | A/B/C/D |
| 591 | fft_coefficient__attr_"angle"__coeff_26 | fft_coefficient__attr_"angle"__coeff_26 | full | A/B/C/D |
| 592 | fft_coefficient__attr_"angle"__coeff_27 | fft_coefficient__attr_"angle"__coeff_27 | full | A/B/C/D |
| 593 | fft_coefficient__attr_"angle"__coeff_28 | fft_coefficient__attr_"angle"__coeff_28 | full | A/B/C/D |
| 594 | fft_coefficient__attr_"angle"__coeff_29 | fft_coefficient__attr_"angle"__coeff_29 | full | A/B/C/D |
| 595 | fft_coefficient__attr_"angle"__coeff_30 | fft_coefficient__attr_"angle"__coeff_30 | full | A/B/C/D |
| 596 | fft_coefficient__attr_"angle"__coeff_31 | fft_coefficient__attr_"angle"__coeff_31 | full | A/B/C/D |
| 597 | fft_coefficient__attr_"angle"__coeff_32 | fft_coefficient__attr_"angle"__coeff_32 | full | A/B/C/D |
| 598 | fft_coefficient__attr_"angle"__coeff_33 | fft_coefficient__attr_"angle"__coeff_33 | full | A/B/C/D |
| 599 | fft_coefficient__attr_"angle"__coeff_34 | fft_coefficient__attr_"angle"__coeff_34 | full | A/B/C/D |
| 600 | fft_coefficient__attr_"angle"__coeff_35 | fft_coefficient__attr_"angle"__coeff_35 | full | A/B/C/D |
| 601 | fft_coefficient__attr_"angle"__coeff_36 | fft_coefficient__attr_"angle"__coeff_36 | full | A/B/C/D |
| 602 | fft_coefficient__attr_"angle"__coeff_37 | fft_coefficient__attr_"angle"__coeff_37 | full | A/B/C/D |
| 603 | fft_coefficient__attr_"angle"__coeff_38 | fft_coefficient__attr_"angle"__coeff_38 | full | A/B/C/D |
| 604 | fft_coefficient__attr_"angle"__coeff_39 | fft_coefficient__attr_"angle"__coeff_39 | full | A/B/C/D |
| 605 | fft_coefficient__attr_"angle"__coeff_40 | fft_coefficient__attr_"angle"__coeff_40 | full | A/B/C/D |
| 606 | fft_coefficient__attr_"angle"__coeff_41 | fft_coefficient__attr_"angle"__coeff_41 | full | A/B/C/D |
| 607 | fft_coefficient__attr_"angle"__coeff_42 | fft_coefficient__attr_"angle"__coeff_42 | full | A/B/C/D |
| 608 | fft_coefficient__attr_"angle"__coeff_43 | fft_coefficient__attr_"angle"__coeff_43 | full | A/B/C/D |
| 609 | fft_coefficient__attr_"angle"__coeff_44 | fft_coefficient__attr_"angle"__coeff_44 | full | A/B/C/D |
| 610 | fft_coefficient__attr_"angle"__coeff_45 | fft_coefficient__attr_"angle"__coeff_45 | full | A/B/C/D |
| 611 | fft_coefficient__attr_"angle"__coeff_46 | fft_coefficient__attr_"angle"__coeff_46 | full | A/B/C/D |
| 612 | fft_coefficient__attr_"angle"__coeff_47 | fft_coefficient__attr_"angle"__coeff_47 | full | A/B/C/D |
| 613 | fft_coefficient__attr_"angle"__coeff_48 | fft_coefficient__attr_"angle"__coeff_48 | full | A/B/C/D |
| 614 | fft_coefficient__attr_"angle"__coeff_49 | fft_coefficient__attr_"angle"__coeff_49 | full | A/B/C/D |
| 615 | fft_coefficient__attr_"angle"__coeff_50 | fft_coefficient__attr_"angle"__coeff_50 | full | A/B/C/D |
| 616 | fft_coefficient__attr_"angle"__coeff_51 | fft_coefficient__attr_"angle"__coeff_51 | full | A/B/C/D |
| 617 | fft_coefficient__attr_"angle"__coeff_52 | fft_coefficient__attr_"angle"__coeff_52 | full | A/B/C/D |
| 618 | fft_coefficient__attr_"angle"__coeff_53 | fft_coefficient__attr_"angle"__coeff_53 | full | A/B/C/D |
| 619 | fft_coefficient__attr_"angle"__coeff_54 | fft_coefficient__attr_"angle"__coeff_54 | full | A/B/C/D |
| 620 | fft_coefficient__attr_"angle"__coeff_55 | fft_coefficient__attr_"angle"__coeff_55 | full | A/B/C/D |
| 621 | fft_coefficient__attr_"angle"__coeff_56 | fft_coefficient__attr_"angle"__coeff_56 | full | A/B/C/D |
| 622 | fft_coefficient__attr_"angle"__coeff_57 | fft_coefficient__attr_"angle"__coeff_57 | full | A/B/C/D |
| 623 | fft_coefficient__attr_"angle"__coeff_58 | fft_coefficient__attr_"angle"__coeff_58 | full | A/B/C/D |
| 624 | fft_coefficient__attr_"angle"__coeff_59 | fft_coefficient__attr_"angle"__coeff_59 | full | A/B/C/D |
| 625 | fft_coefficient__attr_"angle"__coeff_60 | fft_coefficient__attr_"angle"__coeff_60 | full | A/B/C/D |
| 626 | fft_coefficient__attr_"angle"__coeff_61 | fft_coefficient__attr_"angle"__coeff_61 | full | A/B/C/D |
| 627 | fft_coefficient__attr_"angle"__coeff_62 | fft_coefficient__attr_"angle"__coeff_62 | full | A/B/C/D |
| 628 | fft_coefficient__attr_"angle"__coeff_63 | fft_coefficient__attr_"angle"__coeff_63 | full | A/B/C/D |
| 629 | fft_coefficient__attr_"angle"__coeff_64 | fft_coefficient__attr_"angle"__coeff_64 | full | A/B/C/D |
| 630 | fft_coefficient__attr_"angle"__coeff_65 | fft_coefficient__attr_"angle"__coeff_65 | full | A/B/C/D |
| 631 | fft_coefficient__attr_"angle"__coeff_66 | fft_coefficient__attr_"angle"__coeff_66 | full | A/B/C/D |
| 632 | fft_coefficient__attr_"angle"__coeff_67 | fft_coefficient__attr_"angle"__coeff_67 | full | A/B/C/D |
| 633 | fft_coefficient__attr_"angle"__coeff_68 | fft_coefficient__attr_"angle"__coeff_68 | full | A/B/C/D |
| 634 | fft_coefficient__attr_"angle"__coeff_69 | fft_coefficient__attr_"angle"__coeff_69 | full | A/B/C/D |
| 635 | fft_coefficient__attr_"angle"__coeff_70 | fft_coefficient__attr_"angle"__coeff_70 | full | A/B/C/D |
| 636 | fft_coefficient__attr_"angle"__coeff_71 | fft_coefficient__attr_"angle"__coeff_71 | full | A/B/C/D |
| 637 | fft_coefficient__attr_"angle"__coeff_72 | fft_coefficient__attr_"angle"__coeff_72 | full | A/B/C/D |
| 638 | fft_coefficient__attr_"angle"__coeff_73 | fft_coefficient__attr_"angle"__coeff_73 | full | A/B/C/D |
| 639 | fft_coefficient__attr_"angle"__coeff_74 | fft_coefficient__attr_"angle"__coeff_74 | full | A/B/C/D |
| 640 | fft_coefficient__attr_"angle"__coeff_75 | fft_coefficient__attr_"angle"__coeff_75 | full | A/B/C/D |
| 641 | fft_coefficient__attr_"angle"__coeff_76 | fft_coefficient__attr_"angle"__coeff_76 | full | A/B/C/D |
| 642 | fft_coefficient__attr_"angle"__coeff_77 | fft_coefficient__attr_"angle"__coeff_77 | full | A/B/C/D |
| 643 | fft_coefficient__attr_"angle"__coeff_78 | fft_coefficient__attr_"angle"__coeff_78 | full | A/B/C/D |
| 644 | fft_coefficient__attr_"angle"__coeff_79 | fft_coefficient__attr_"angle"__coeff_79 | full | A/B/C/D |
| 645 | fft_coefficient__attr_"angle"__coeff_80 | fft_coefficient__attr_"angle"__coeff_80 | full | A/B/C/D |
| 646 | fft_coefficient__attr_"angle"__coeff_81 | fft_coefficient__attr_"angle"__coeff_81 | full | A/B/C/D |
| 647 | fft_coefficient__attr_"angle"__coeff_82 | fft_coefficient__attr_"angle"__coeff_82 | full | A/B/C/D |
| 648 | fft_coefficient__attr_"angle"__coeff_83 | fft_coefficient__attr_"angle"__coeff_83 | full | A/B/C/D |
| 649 | fft_coefficient__attr_"angle"__coeff_84 | fft_coefficient__attr_"angle"__coeff_84 | full | A/B/C/D |
| 650 | fft_coefficient__attr_"angle"__coeff_85 | fft_coefficient__attr_"angle"__coeff_85 | full | A/B/C/D |
| 651 | fft_coefficient__attr_"angle"__coeff_86 | fft_coefficient__attr_"angle"__coeff_86 | full | A/B/C/D |
| 652 | fft_coefficient__attr_"angle"__coeff_87 | fft_coefficient__attr_"angle"__coeff_87 | full | A/B/C/D |
| 653 | fft_coefficient__attr_"angle"__coeff_88 | fft_coefficient__attr_"angle"__coeff_88 | full | A/B/C/D |
| 654 | fft_coefficient__attr_"angle"__coeff_89 | fft_coefficient__attr_"angle"__coeff_89 | full | A/B/C/D |
| 655 | fft_coefficient__attr_"angle"__coeff_90 | fft_coefficient__attr_"angle"__coeff_90 | full | A/B/C/D |
| 656 | fft_coefficient__attr_"angle"__coeff_91 | fft_coefficient__attr_"angle"__coeff_91 | full | A/B/C/D |
| 657 | fft_coefficient__attr_"angle"__coeff_92 | fft_coefficient__attr_"angle"__coeff_92 | full | A/B/C/D |
| 658 | fft_coefficient__attr_"angle"__coeff_93 | fft_coefficient__attr_"angle"__coeff_93 | full | A/B/C/D |
| 659 | fft_coefficient__attr_"angle"__coeff_94 | fft_coefficient__attr_"angle"__coeff_94 | full | A/B/C/D |
| 660 | fft_coefficient__attr_"angle"__coeff_95 | fft_coefficient__attr_"angle"__coeff_95 | full | A/B/C/D |
| 661 | fft_coefficient__attr_"angle"__coeff_96 | fft_coefficient__attr_"angle"__coeff_96 | full | A/B/C/D |
| 662 | fft_coefficient__attr_"angle"__coeff_97 | fft_coefficient__attr_"angle"__coeff_97 | full | A/B/C/D |
| 663 | fft_coefficient__attr_"angle"__coeff_98 | fft_coefficient__attr_"angle"__coeff_98 | full | A/B/C/D |
| 664 | fft_coefficient__attr_"angle"__coeff_99 | fft_coefficient__attr_"angle"__coeff_99 | full | A/B/C/D |
| 665 | fft_aggregated__aggtype_"centroid" | fft_aggregated__aggtype_"centroid" | full | A/B/C/D |
| 666 | fft_aggregated__aggtype_"variance" | fft_aggregated__aggtype_"variance" | full | A/B/C/D |
| 667 | fft_aggregated__aggtype_"skew" | fft_aggregated__aggtype_"skew" | full | A/B/C/D |
| 668 | fft_aggregated__aggtype_"kurtosis" | fft_aggregated__aggtype_"kurtosis" | full | A/B/C/D |
| 669 | value_count__value_0 | value_count__value_0 | full | A/B/C/D |
| 670 | value_count__value_1 | value_count__value_1 | full | A/B/C/D |
| 671 | value_count__value_-1 | value_count__value_-1 | full | A/B/C/D |
| 672 | range_count__max_1__min_-1 | range_count__max_1__min_-1 | full | A/B/C/D |
| 673 | range_count__max_0__min_-1000000000000.0 | range_count__max_0__min_-1000000000000.0 | full | A/B/C/D |
| 674 | range_count__max_1000000000000.0__min_0 | range_count__max_1000000000000.0__min_0 | full | A/B/C/D |
| 675 | friedrich_coefficients__coeff_0__m_3__r_30 | friedrich_coefficients__coeff_0__m_3__r_30 | full | A/B/C/D |
| 676 | friedrich_coefficients__coeff_1__m_3__r_30 | friedrich_coefficients__coeff_1__m_3__r_30 | full | A/B/C/D |
| 677 | friedrich_coefficients__coeff_2__m_3__r_30 | friedrich_coefficients__coeff_2__m_3__r_30 | full | A/B/C/D |
| 678 | friedrich_coefficients__coeff_3__m_3__r_30 | friedrich_coefficients__coeff_3__m_3__r_30 | full | A/B/C/D |
| 679 | max_langevin_fixed_point__m_3__r_30 | max_langevin_fixed_point__m_3__r_30 | full | A/B/C/D |
| 680 | linear_trend__attr_"pvalue" | linear_trend__attr_"pvalue" | full | A/B/C/D |
| 681 | linear_trend__attr_"rvalue" | linear_trend__attr_"rvalue" | full | A/B/C/D |
| 682 | linear_trend__attr_"intercept" | linear_trend__attr_"intercept" | full | A/B/C/D |
| 683 | linear_trend__attr_"slope" | linear_trend__attr_"slope" | full | A/B/C/D |
| 684 | linear_trend__attr_"stderr" | linear_trend__attr_"stderr" | full | A/B/C/D |
| 685 | agg_linear_trend__attr_"rvalue"__chunk_len_5__f_agg_"max" | agg_linear_trend__attr_"rvalue"__chunk_len_5__f_agg_"max" | full | A/B/C/D |
| 686 | agg_linear_trend__attr_"rvalue"__chunk_len_5__f_agg_"min" | agg_linear_trend__attr_"rvalue"__chunk_len_5__f_agg_"min" | full | A/B/C/D |
| 687 | agg_linear_trend__attr_"rvalue"__chunk_len_5__f_agg_"mean" | agg_linear_trend__attr_"rvalue"__chunk_len_5__f_agg_"mean" | full | A/B/C/D |
| 688 | agg_linear_trend__attr_"rvalue"__chunk_len_5__f_agg_"var" | agg_linear_trend__attr_"rvalue"__chunk_len_5__f_agg_"var" | full | A/B/C/D |
| 689 | agg_linear_trend__attr_"rvalue"__chunk_len_10__f_agg_"max" | agg_linear_trend__attr_"rvalue"__chunk_len_10__f_agg_"max" | full | A/B/C/D |
| 690 | agg_linear_trend__attr_"rvalue"__chunk_len_10__f_agg_"min" | agg_linear_trend__attr_"rvalue"__chunk_len_10__f_agg_"min" | full | A/B/C/D |
| 691 | agg_linear_trend__attr_"rvalue"__chunk_len_10__f_agg_"mean" | agg_linear_trend__attr_"rvalue"__chunk_len_10__f_agg_"mean" | full | A/B/C/D |
| 692 | agg_linear_trend__attr_"rvalue"__chunk_len_10__f_agg_"var" | agg_linear_trend__attr_"rvalue"__chunk_len_10__f_agg_"var" | full | A/B/C/D |
| 693 | agg_linear_trend__attr_"rvalue"__chunk_len_50__f_agg_"max" | agg_linear_trend__attr_"rvalue"__chunk_len_50__f_agg_"max" | full | A/B/C/D |
| 694 | agg_linear_trend__attr_"rvalue"__chunk_len_50__f_agg_"min" | agg_linear_trend__attr_"rvalue"__chunk_len_50__f_agg_"min" | full | A/B/C/D |
| 695 | agg_linear_trend__attr_"rvalue"__chunk_len_50__f_agg_"mean" | agg_linear_trend__attr_"rvalue"__chunk_len_50__f_agg_"mean" | full | A/B/C/D |
| 696 | agg_linear_trend__attr_"rvalue"__chunk_len_50__f_agg_"var" | agg_linear_trend__attr_"rvalue"__chunk_len_50__f_agg_"var" | full | A/B/C/D |
| 697 | agg_linear_trend__attr_"intercept"__chunk_len_5__f_agg_"max" | agg_linear_trend__attr_"intercept"__chunk_len_5__f_agg_"max" | full | A/B/C/D |
| 698 | agg_linear_trend__attr_"intercept"__chunk_len_5__f_agg_"min" | agg_linear_trend__attr_"intercept"__chunk_len_5__f_agg_"min" | full | A/B/C/D |
| 699 | agg_linear_trend__attr_"intercept"__chunk_len_5__f_agg_"mean" | agg_linear_trend__attr_"intercept"__chunk_len_5__f_agg_"mean" | full | A/B/C/D |
| 700 | agg_linear_trend__attr_"intercept"__chunk_len_5__f_agg_"var" | agg_linear_trend__attr_"intercept"__chunk_len_5__f_agg_"var" | full | A/B/C/D |
| 701 | agg_linear_trend__attr_"intercept"__chunk_len_10__f_agg_"max" | agg_linear_trend__attr_"intercept"__chunk_len_10__f_agg_"max" | full | A/B/C/D |
| 702 | agg_linear_trend__attr_"intercept"__chunk_len_10__f_agg_"min" | agg_linear_trend__attr_"intercept"__chunk_len_10__f_agg_"min" | full | A/B/C/D |
| 703 | agg_linear_trend__attr_"intercept"__chunk_len_10__f_agg_"mean" | agg_linear_trend__attr_"intercept"__chunk_len_10__f_agg_"mean" | full | A/B/C/D |
| 704 | agg_linear_trend__attr_"intercept"__chunk_len_10__f_agg_"var" | agg_linear_trend__attr_"intercept"__chunk_len_10__f_agg_"var" | full | A/B/C/D |
| 705 | agg_linear_trend__attr_"intercept"__chunk_len_50__f_agg_"max" | agg_linear_trend__attr_"intercept"__chunk_len_50__f_agg_"max" | full | A/B/C/D |
| 706 | agg_linear_trend__attr_"intercept"__chunk_len_50__f_agg_"min" | agg_linear_trend__attr_"intercept"__chunk_len_50__f_agg_"min" | full | A/B/C/D |
| 707 | agg_linear_trend__attr_"intercept"__chunk_len_50__f_agg_"mean" | agg_linear_trend__attr_"intercept"__chunk_len_50__f_agg_"mean" | full | A/B/C/D |
| 708 | agg_linear_trend__attr_"intercept"__chunk_len_50__f_agg_"var" | agg_linear_trend__attr_"intercept"__chunk_len_50__f_agg_"var" | full | A/B/C/D |
| 709 | agg_linear_trend__attr_"slope"__chunk_len_5__f_agg_"max" | agg_linear_trend__attr_"slope"__chunk_len_5__f_agg_"max" | full | A/B/C/D |
| 710 | agg_linear_trend__attr_"slope"__chunk_len_5__f_agg_"min" | agg_linear_trend__attr_"slope"__chunk_len_5__f_agg_"min" | full | A/B/C/D |
| 711 | agg_linear_trend__attr_"slope"__chunk_len_5__f_agg_"mean" | agg_linear_trend__attr_"slope"__chunk_len_5__f_agg_"mean" | full | A/B/C/D |
| 712 | agg_linear_trend__attr_"slope"__chunk_len_5__f_agg_"var" | agg_linear_trend__attr_"slope"__chunk_len_5__f_agg_"var" | full | A/B/C/D |
| 713 | agg_linear_trend__attr_"slope"__chunk_len_10__f_agg_"max" | agg_linear_trend__attr_"slope"__chunk_len_10__f_agg_"max" | full | A/B/C/D |
| 714 | agg_linear_trend__attr_"slope"__chunk_len_10__f_agg_"min" | agg_linear_trend__attr_"slope"__chunk_len_10__f_agg_"min" | full | A/B/C/D |
| 715 | agg_linear_trend__attr_"slope"__chunk_len_10__f_agg_"mean" | agg_linear_trend__attr_"slope"__chunk_len_10__f_agg_"mean" | full | A/B/C/D |
| 716 | agg_linear_trend__attr_"slope"__chunk_len_10__f_agg_"var" | agg_linear_trend__attr_"slope"__chunk_len_10__f_agg_"var" | full | A/B/C/D |
| 717 | agg_linear_trend__attr_"slope"__chunk_len_50__f_agg_"max" | agg_linear_trend__attr_"slope"__chunk_len_50__f_agg_"max" | full | A/B/C/D |
| 718 | agg_linear_trend__attr_"slope"__chunk_len_50__f_agg_"min" | agg_linear_trend__attr_"slope"__chunk_len_50__f_agg_"min" | full | A/B/C/D |
| 719 | agg_linear_trend__attr_"slope"__chunk_len_50__f_agg_"mean" | agg_linear_trend__attr_"slope"__chunk_len_50__f_agg_"mean" | full | A/B/C/D |
| 720 | agg_linear_trend__attr_"slope"__chunk_len_50__f_agg_"var" | agg_linear_trend__attr_"slope"__chunk_len_50__f_agg_"var" | full | A/B/C/D |
| 721 | agg_linear_trend__attr_"stderr"__chunk_len_5__f_agg_"max" | agg_linear_trend__attr_"stderr"__chunk_len_5__f_agg_"max" | full | A/B/C/D |
| 722 | agg_linear_trend__attr_"stderr"__chunk_len_5__f_agg_"min" | agg_linear_trend__attr_"stderr"__chunk_len_5__f_agg_"min" | full | A/B/C/D |
| 723 | agg_linear_trend__attr_"stderr"__chunk_len_5__f_agg_"mean" | agg_linear_trend__attr_"stderr"__chunk_len_5__f_agg_"mean" | full | A/B/C/D |
| 724 | agg_linear_trend__attr_"stderr"__chunk_len_5__f_agg_"var" | agg_linear_trend__attr_"stderr"__chunk_len_5__f_agg_"var" | full | A/B/C/D |
| 725 | agg_linear_trend__attr_"stderr"__chunk_len_10__f_agg_"max" | agg_linear_trend__attr_"stderr"__chunk_len_10__f_agg_"max" | full | A/B/C/D |
| 726 | agg_linear_trend__attr_"stderr"__chunk_len_10__f_agg_"min" | agg_linear_trend__attr_"stderr"__chunk_len_10__f_agg_"min" | full | A/B/C/D |
| 727 | agg_linear_trend__attr_"stderr"__chunk_len_10__f_agg_"mean" | agg_linear_trend__attr_"stderr"__chunk_len_10__f_agg_"mean" | full | A/B/C/D |
| 728 | agg_linear_trend__attr_"stderr"__chunk_len_10__f_agg_"var" | agg_linear_trend__attr_"stderr"__chunk_len_10__f_agg_"var" | full | A/B/C/D |
| 729 | agg_linear_trend__attr_"stderr"__chunk_len_50__f_agg_"max" | agg_linear_trend__attr_"stderr"__chunk_len_50__f_agg_"max" | full | A/B/C/D |
| 730 | agg_linear_trend__attr_"stderr"__chunk_len_50__f_agg_"min" | agg_linear_trend__attr_"stderr"__chunk_len_50__f_agg_"min" | full | A/B/C/D |
| 731 | agg_linear_trend__attr_"stderr"__chunk_len_50__f_agg_"mean" | agg_linear_trend__attr_"stderr"__chunk_len_50__f_agg_"mean" | full | A/B/C/D |
| 732 | agg_linear_trend__attr_"stderr"__chunk_len_50__f_agg_"var" | agg_linear_trend__attr_"stderr"__chunk_len_50__f_agg_"var" | full | A/B/C/D |
| 733 | augmented_dickey_fuller__attr_"teststat"__autolag_"AIC" | augmented_dickey_fuller__attr_"teststat"__autolag_"AIC" | full | A/B/C/D |
| 734 | augmented_dickey_fuller__attr_"pvalue"__autolag_"AIC" | augmented_dickey_fuller__attr_"pvalue"__autolag_"AIC" | full | A/B/C/D |
| 735 | augmented_dickey_fuller__attr_"usedlag"__autolag_"AIC" | augmented_dickey_fuller__attr_"usedlag"__autolag_"AIC" | full | A/B/C/D |
| 736 | number_crossing_m__m_0 | number_crossing_m__m_0 | full | A/B/C/D |
| 737 | number_crossing_m__m_-1 | number_crossing_m__m_-1 | full | A/B/C/D |
| 738 | number_crossing_m__m_1 | number_crossing_m__m_1 | full | A/B/C/D |
| 739 | energy_ratio_by_chunks__num_segments_10__segment_focus_0 | energy_ratio_by_chunks__num_segments_10__segment_focus_0 | full | A/B/C/D |
| 740 | energy_ratio_by_chunks__num_segments_10__segment_focus_1 | energy_ratio_by_chunks__num_segments_10__segment_focus_1 | full | A/B/C/D |
| 741 | energy_ratio_by_chunks__num_segments_10__segment_focus_2 | energy_ratio_by_chunks__num_segments_10__segment_focus_2 | full | A/B/C/D |
| 742 | energy_ratio_by_chunks__num_segments_10__segment_focus_3 | energy_ratio_by_chunks__num_segments_10__segment_focus_3 | full | A/B/C/D |
| 743 | energy_ratio_by_chunks__num_segments_10__segment_focus_4 | energy_ratio_by_chunks__num_segments_10__segment_focus_4 | full | A/B/C/D |
| 744 | energy_ratio_by_chunks__num_segments_10__segment_focus_5 | energy_ratio_by_chunks__num_segments_10__segment_focus_5 | full | A/B/C/D |
| 745 | energy_ratio_by_chunks__num_segments_10__segment_focus_6 | energy_ratio_by_chunks__num_segments_10__segment_focus_6 | full | A/B/C/D |
| 746 | energy_ratio_by_chunks__num_segments_10__segment_focus_7 | energy_ratio_by_chunks__num_segments_10__segment_focus_7 | full | A/B/C/D |
| 747 | energy_ratio_by_chunks__num_segments_10__segment_focus_8 | energy_ratio_by_chunks__num_segments_10__segment_focus_8 | full | A/B/C/D |
| 748 | energy_ratio_by_chunks__num_segments_10__segment_focus_9 | energy_ratio_by_chunks__num_segments_10__segment_focus_9 | full | A/B/C/D |
| 749 | ratio_beyond_r_sigma__r_0.5 | ratio_beyond_r_sigma__r_0.5 | full | A/B/C/D |
| 750 | ratio_beyond_r_sigma__r_1 | ratio_beyond_r_sigma__r_1 | full | A/B/C/D |
| 751 | ratio_beyond_r_sigma__r_1.5 | ratio_beyond_r_sigma__r_1.5 | full | A/B/C/D |
| 752 | ratio_beyond_r_sigma__r_2 | ratio_beyond_r_sigma__r_2 | full | A/B/C/D |
| 753 | ratio_beyond_r_sigma__r_2.5 | ratio_beyond_r_sigma__r_2.5 | full | A/B/C/D |
| 754 | ratio_beyond_r_sigma__r_3 | ratio_beyond_r_sigma__r_3 | full | A/B/C/D |
| 755 | ratio_beyond_r_sigma__r_5 | ratio_beyond_r_sigma__r_5 | full | A/B/C/D |
| 756 | ratio_beyond_r_sigma__r_6 | ratio_beyond_r_sigma__r_6 | full | A/B/C/D |
| 757 | ratio_beyond_r_sigma__r_7 | ratio_beyond_r_sigma__r_7 | full | A/B/C/D |
| 758 | ratio_beyond_r_sigma__r_10 | ratio_beyond_r_sigma__r_10 | full | A/B/C/D |
| 759 | count_above__t_0 | count_above__t_0 | full | A/B/C/D |
| 760 | count_below__t_0 | count_below__t_0 | full | A/B/C/D |
| 761 | lempel_ziv_complexity__bins_2 | lempel_ziv_complexity__bins_2 | full | A/B/C/D |
| 762 | lempel_ziv_complexity__bins_3 | lempel_ziv_complexity__bins_3 | full | A/B/C/D |
| 763 | lempel_ziv_complexity__bins_5 | lempel_ziv_complexity__bins_5 | full | A/B/C/D |
| 764 | lempel_ziv_complexity__bins_10 | lempel_ziv_complexity__bins_10 | full | A/B/C/D |
| 765 | lempel_ziv_complexity__bins_100 | lempel_ziv_complexity__bins_100 | full | A/B/C/D |
| 766 | fourier_entropy__bins_2 | fourier_entropy__bins_2 | full | A/B/C/D |
| 767 | fourier_entropy__bins_3 | fourier_entropy__bins_3 | full | A/B/C/D |
| 768 | fourier_entropy__bins_5 | fourier_entropy__bins_5 | full | A/B/C/D |
| 769 | fourier_entropy__bins_10 | fourier_entropy__bins_10 | full | A/B/C/D |
| 770 | fourier_entropy__bins_100 | fourier_entropy__bins_100 | full | A/B/C/D |
| 771 | permutation_entropy__dimension_3__tau_1 | permutation_entropy__dimension_3__tau_1 | full | A/B/C/D |
| 772 | permutation_entropy__dimension_4__tau_1 | permutation_entropy__dimension_4__tau_1 | full | A/B/C/D |
| 773 | permutation_entropy__dimension_5__tau_1 | permutation_entropy__dimension_5__tau_1 | full | A/B/C/D |
| 774 | permutation_entropy__dimension_6__tau_1 | permutation_entropy__dimension_6__tau_1 | full | A/B/C/D |
| 775 | permutation_entropy__dimension_7__tau_1 | permutation_entropy__dimension_7__tau_1 | full | A/B/C/D |
| 776 | query_similarity_count__query_None__threshold_0.0 | query_similarity_count__query_None__threshold_0.0 | full | A/B/C/D |
| 777 | mean_n_absolute_max__number_of_maxima_7 | mean_n_absolute_max__number_of_maxima_7 | full | A/B/C/D |

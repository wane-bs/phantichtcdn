"""
diagnostics.py — Module Kiểm định Thống kê Toàn diện cho HVN Dashboard
========================================================================
Bao gồm 8 nhóm kiểm định kinh tế lượng:
  1. Tính dừng (ADF) + Đồng liên kết (Engle-Granger)
  2. Phương sai sai số thay đổi (Breusch-Pagan)
  3. Tự tương quan (Durbin-Watson + Ljung-Box)
  4. Phân phối chuẩn phần dư (Jarque-Bera)
  5. Sai số Dự báo (Expanding Window Backtesting + COVID Dummy)
  6. Cấu trúc Phân phối Oil & FX (KS, Shapiro-Wilk)
  7. Điểm kỳ dị toán học WACC-g (Singularity Detection)
  8. Nội sinh Cấu trúc Vốn (Granger Causality + Auto-lag AIC/BIC)
"""

import numpy as np
import pandas as pd
import json
import os

try:
    from statsmodels.tsa.stattools import adfuller, coint, grangercausalitytests
    from statsmodels.stats.diagnostic import het_breuschpagan, acorr_ljungbox
    from statsmodels.stats.stattools import durbin_watson, jarque_bera
    from statsmodels.regression.linear_model import OLS
    from statsmodels.tools.tools import add_constant
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

try:
    from scipy.stats import kstest, shapiro, normaltest
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from sklearn.linear_model import LinearRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class DiagnosticsEngine:
    """
    Engine kiểm định thống kê cho mô hình tài chính HVN.
    Nhận dfs_dict từ Calculator (stage 2) và chạy 8 nhóm kiểm định.
    """

    def __init__(self, dfs_dict, alpha=0.05):
        self.dfs = dfs_dict or {}
        self.alpha = alpha  # Mức ý nghĩa mặc định
        self.results = {}   # Dict lưu kết quả tất cả kiểm định

    # =====================================================================
    # HELPER METHODS
    # =====================================================================
    def _get_row(self, df, pattern):
        if df is None or df.empty:
            return None
        row = df[df['Khoản mục'].str.contains(pattern, case=False, na=False, regex=True)]
        if not row.empty:
            return row.iloc[0]
        return None

    def _get_years(self, df):
        if df is None:
            return []
        years = []
        for c in df.columns:
            if c != 'Khoản mục':
                try:
                    int(str(c).split('.')[0])
                    years.append(c)
                except ValueError:
                    continue
        return sorted(years, key=lambda x: int(str(x).split('.')[0]))

    def _build_loglog_data(self):
        """
        Tái tạo dữ liệu Log-Log regression từ Calculator.
        Trả về (X_fwl, y_fwl, residuals, ln_Q, ln_TC, ln_oil, ln_fx, years, covid_dummy)
        hoặc None nếu thiếu dữ liệu.
        """
        if not SKLEARN_AVAILABLE:
            return None

        is_df = self.dfs.get('INCOME STATEMENT')
        if is_df is None:
            return None

        years = self._get_years(is_df)
        if len(years) < 5:
            return None

        rev_row = self._get_row(is_df, r'^Doanh số thuần$')
        ebit_row = self._get_row(is_df, r'^EBIT$')

        if rev_row is None or ebit_row is None:
            return None

        rev_vals = rev_row[years].astype(float).values
        ebit_vals = ebit_row[years].astype(float).values
        tc_vals = rev_vals - ebit_vals

        tc_vals_safe = np.maximum(tc_vals, 1.0)
        rev_vals_safe = np.maximum(rev_vals, 1.0)

        # Macro data
        df_macro = self.dfs.get('MACRO_DATA')
        macro_fx, macro_oil = {}, {}
        if df_macro is not None and not df_macro.empty:
            for _, row in df_macro.iterrows():
                try:
                    yr = str(int(row['Year']))
                    if pd.notna(row.get('Oil_Price')):
                        macro_oil[yr] = float(row['Oil_Price'])
                    if pd.notna(row.get('FX_Rate')):
                        macro_fx[yr] = float(row['FX_Rate'])
                except Exception:
                    pass

        fx_arr = np.array([macro_fx.get(str(y), 24000) for y in years])
        oil_arr = np.array([macro_oil.get(str(y), 90) for y in years])
        covid_dummy = np.array([1 if str(y) in ['2020', '2021', '2022'] else 0 for y in years])

        ln_TC = np.log(tc_vals_safe)
        ln_Q = np.log(rev_vals_safe)
        ln_oil = np.log(oil_arr)
        ln_fx = np.log(fx_arr)

        # FWL orthogonalization
        reg_fx_aux = LinearRegression().fit(ln_Q.reshape(-1, 1), ln_fx)
        resid_fx = ln_fx - reg_fx_aux.predict(ln_Q.reshape(-1, 1))

        reg_oil_aux = LinearRegression().fit(ln_Q.reshape(-1, 1), ln_oil)
        resid_oil = ln_oil - reg_oil_aux.predict(ln_Q.reshape(-1, 1))

        X_fwl = np.column_stack((ln_Q, resid_oil, resid_fx, covid_dummy))
        y_fwl = ln_TC

        reg_main = LinearRegression(fit_intercept=True).fit(X_fwl, y_fwl)
        residuals = y_fwl - reg_main.predict(X_fwl)

        # Lấy thêm EBITDA
        ebitda_row = self._get_row(is_df, r'^EBITDA$')
        ebitda_vals = ebitda_row[years].astype(float).values if ebitda_row is not None else None

        return {
            'X_fwl': X_fwl,
            'y_fwl': y_fwl,
            'residuals': residuals,
            'ln_Q': ln_Q,
            'ln_TC': ln_TC,
            'ln_oil': ln_oil,
            'ln_fx': ln_fx,
            'oil_arr': oil_arr,
            'fx_arr': fx_arr,
            'years': years,
            'covid_dummy': covid_dummy,
            'rev_vals': rev_vals,
            'ebit_vals': ebit_vals,
            'tc_vals': tc_vals,
            'ebitda_vals': ebitda_vals,
        }

    # =====================================================================
    # TEST 1: STATIONARITY (ADF) + COINTEGRATION (Engle-Granger)
    # =====================================================================
    def test_stationarity(self, alpha=None):
        """
        Kiểm định ADF cho 4 chuỗi log-transformed chính.
        Nếu không dừng → chạy ADF trên first-difference + Engle-Granger cointegration.
        """
        if not STATSMODELS_AVAILABLE:
            self.results['STATIONARITY'] = {'error': 'statsmodels not available'}
            return

        alpha = alpha or self.alpha
        loglog = self._build_loglog_data()
        if loglog is None:
            self.results['STATIONARITY'] = {'error': 'Insufficient data'}
            return

        series_dict = {
            'ln(Revenue)': loglog['ln_Q'],
            'ln(Total Cost)': loglog['ln_TC'],
            'ln(Oil Price)': loglog['ln_oil'],
            'ln(FX Rate)': loglog['ln_fx'],
        }

        adf_results = []
        any_nonstationary = False
        nonstat_series = {}

        for name, series in series_dict.items():
            if len(series) < 5:
                adf_results.append({
                    'series': name,
                    'adf_stat': None,
                    'p_value': None,
                    'conclusion': 'Không đủ dữ liệu (n < 5)',
                    'is_stationary': None,
                    'critical_values': {}
                })
                continue

            try:
                result = adfuller(series, autolag='AIC')
                adf_stat, p_val, used_lag, nobs, crit_vals, icbest = result

                is_stationary = p_val < alpha
                if not is_stationary:
                    any_nonstationary = True
                    nonstat_series[name] = series

                adf_results.append({
                    'series': name,
                    'adf_stat': round(float(adf_stat), 4),
                    'p_value': round(float(p_val), 4),
                    'used_lag': int(used_lag),
                    'n_obs': int(nobs),
                    'critical_values': {k: round(v, 4) for k, v in crit_vals.items()},
                    'is_stationary': bool(is_stationary),
                    'conclusion': f'Dừng I(0) tại α={alpha*100:.0f}%' if is_stationary
                                  else f'Không dừng I(1) tại α={alpha*100:.0f}%'
                })

                # Test on first-difference if non-stationary
                if not is_stationary and len(series) > 6:
                    diff_series = np.diff(series)
                    diff_result = adfuller(diff_series, autolag='AIC')
                    diff_p = float(diff_result[1])
                    adf_results[-1]['first_diff_adf'] = round(float(diff_result[0]), 4)
                    adf_results[-1]['first_diff_p'] = round(diff_p, 4)
                    adf_results[-1]['first_diff_stationary'] = diff_p < alpha

            except Exception as e:
                adf_results.append({
                    'series': name,
                    'error': str(e),
                    'is_stationary': None
                })

        # Cointegration test if any series non-stationary
        coint_results = []
        if any_nonstationary and len(loglog['ln_TC']) >= 7:
            # Test cointegration between ln(TC) and ln(Revenue) — the core pair
            try:
                coint_stat, p_val, crit_vals = coint(loglog['ln_TC'], loglog['ln_Q'])
                coint_results.append({
                    'pair': 'ln(TC) ~ ln(Revenue)',
                    'coint_stat': round(float(coint_stat), 4),
                    'p_value': round(float(p_val), 4),
                    'critical_values': {
                        '1%': round(float(crit_vals[0]), 4),
                        '5%': round(float(crit_vals[1]), 4),
                        '10%': round(float(crit_vals[2]), 4),
                    },
                    'is_cointegrated': bool(p_val < alpha),
                    'conclusion': 'Đồng liên kết (Mối quan hệ dài hạn ổn định)' if p_val < alpha
                                  else 'Không đồng liên kết (Spurious regression risk)'
                })
            except Exception as e:
                coint_results.append({'pair': 'ln(TC) ~ ln(Revenue)', 'error': str(e)})

            # Also test ln(TC) ~ ln(Oil)
            try:
                coint_stat2, p_val2, crit_vals2 = coint(loglog['ln_TC'], loglog['ln_oil'])
                coint_results.append({
                    'pair': 'ln(TC) ~ ln(Oil)',
                    'coint_stat': round(float(coint_stat2), 4),
                    'p_value': round(float(p_val2), 4),
                    'critical_values': {
                        '1%': round(float(crit_vals2[0]), 4),
                        '5%': round(float(crit_vals2[1]), 4),
                        '10%': round(float(crit_vals2[2]), 4),
                    },
                    'is_cointegrated': bool(p_val2 < alpha),
                    'conclusion': 'Đồng liên kết' if p_val2 < alpha else 'Không đồng liên kết'
                })
            except Exception as e:
                coint_results.append({'pair': 'ln(TC) ~ ln(Oil)', 'error': str(e)})

        self.results['STATIONARITY'] = {
            'adf_tests': adf_results,
            'cointegration': coint_results,
            'any_nonstationary': any_nonstationary,
            'alpha': alpha,
        }

    # =====================================================================
    # TEST 2: HETEROSKEDASTICITY (Breusch-Pagan)
    # =====================================================================
    def test_heteroskedasticity(self, alpha=None):
        """Breusch-Pagan test trên residuals của mô hình Log-Log."""
        if not STATSMODELS_AVAILABLE:
            self.results['HETEROSKEDASTICITY'] = {'error': 'statsmodels not available'}
            return

        alpha = alpha or self.alpha
        loglog = self._build_loglog_data()
        if loglog is None:
            self.results['HETEROSKEDASTICITY'] = {'error': 'Insufficient data'}
            return

        try:
            X_const = add_constant(loglog['X_fwl'])
            model = OLS(loglog['y_fwl'], X_const).fit()
            resid = model.resid

            lm_stat, lm_pval, f_stat, f_pval = het_breuschpagan(resid, X_const)

            self.results['HETEROSKEDASTICITY'] = {
                'lm_statistic': round(float(lm_stat), 4),
                'lm_p_value': round(float(lm_pval), 4),
                'f_statistic': round(float(f_stat), 4),
                'f_p_value': round(float(f_pval), 4),
                'is_homoskedastic': bool(lm_pval > alpha),
                'alpha': alpha,
                'conclusion': (
                    f'Phương sai đồng nhất (Homoskedastic) — p={lm_pval:.4f} > α={alpha}'
                    if lm_pval > alpha
                    else f'Phương sai sai số thay đổi (Heteroskedastic) — p={lm_pval:.4f} ≤ α={alpha}'
                ),
            }
        except Exception as e:
            self.results['HETEROSKEDASTICITY'] = {'error': str(e)}

    # =====================================================================
    # TEST 3: AUTOCORRELATION (Durbin-Watson + Ljung-Box)
    # =====================================================================
    def test_autocorrelation(self, alpha=None):
        """Durbin-Watson + Ljung-Box Q-test trên residuals Log-Log."""
        if not STATSMODELS_AVAILABLE:
            self.results['AUTOCORRELATION'] = {'error': 'statsmodels not available'}
            return

        alpha = alpha or self.alpha
        loglog = self._build_loglog_data()
        if loglog is None:
            self.results['AUTOCORRELATION'] = {'error': 'Insufficient data'}
            return

        try:
            X_const = add_constant(loglog['X_fwl'])
            model = OLS(loglog['y_fwl'], X_const).fit()
            resid = model.resid

            # Durbin-Watson
            dw_stat = float(durbin_watson(resid))

            if dw_stat < 1.5:
                dw_conclusion = 'Tự tương quan DƯƠNG (Positive autocorrelation)'
                dw_pass = False
            elif dw_stat > 2.5:
                dw_conclusion = 'Tự tương quan ÂM (Negative autocorrelation)'
                dw_pass = False
            else:
                dw_conclusion = 'Không có tự tương quan bậc 1 (No first-order autocorrelation)'
                dw_pass = True

            # Ljung-Box (lag = 1)
            lb_result = acorr_ljungbox(resid, lags=[1], return_df=True)
            lb_stat = float(lb_result['lb_stat'].iloc[0])
            lb_pval = float(lb_result['lb_pvalue'].iloc[0])

            self.results['AUTOCORRELATION'] = {
                'durbin_watson': {
                    'statistic': round(dw_stat, 4),
                    'conclusion': dw_conclusion,
                    'pass': dw_pass,
                    'interpretation': (
                        'DW ≈ 2: Không tự tương quan | '
                        'DW < 1.5: Tự tương quan dương | '
                        'DW > 2.5: Tự tương quan âm'
                    ),
                },
                'ljung_box': {
                    'statistic': round(lb_stat, 4),
                    'p_value': round(lb_pval, 4),
                    'lag': 1,
                    'pass': bool(lb_pval > alpha),
                    'conclusion': (
                        f'Không có tự tương quan (p={lb_pval:.4f} > α={alpha})'
                        if lb_pval > alpha
                        else f'Có tự tương quan (p={lb_pval:.4f} ≤ α={alpha})'
                    ),
                },
                'alpha': alpha,
                'overall_pass': dw_pass and (lb_pval > alpha),
            }
        except Exception as e:
            self.results['AUTOCORRELATION'] = {'error': str(e)}

    # =====================================================================
    # TEST 4: NORMALITY OF RESIDUALS (Jarque-Bera)
    # =====================================================================
    def test_normality(self, alpha=None):
        """Jarque-Bera test + Shapiro-Wilk trên residuals Log-Log."""
        if not STATSMODELS_AVAILABLE:
            self.results['NORMALITY'] = {'error': 'statsmodels not available'}
            return

        alpha = alpha or self.alpha
        loglog = self._build_loglog_data()
        if loglog is None:
            self.results['NORMALITY'] = {'error': 'Insufficient data'}
            return

        try:
            X_const = add_constant(loglog['X_fwl'])
            model = OLS(loglog['y_fwl'], X_const).fit()
            resid = model.resid

            jb_stat, jb_pval, skew, kurtosis = jarque_bera(resid)

            result = {
                'jarque_bera': {
                    'statistic': round(float(jb_stat), 4),
                    'p_value': round(float(jb_pval), 4),
                    'skewness': round(float(skew), 4),
                    'kurtosis': round(float(kurtosis), 4),
                    'pass': bool(jb_pval > alpha),
                    'conclusion': (
                        f'Phần dư có phân phối chuẩn (p={jb_pval:.4f} > α={alpha})'
                        if jb_pval > alpha
                        else f'Phần dư KHÔNG phân phối chuẩn (p={jb_pval:.4f} ≤ α={alpha})'
                    ),
                },
                'alpha': alpha,
                'residuals': resid.tolist(),
                'residual_stats': {
                    'mean': round(float(np.mean(resid)), 6),
                    'std': round(float(np.std(resid)), 6),
                    'min': round(float(np.min(resid)), 6),
                    'max': round(float(np.max(resid)), 6),
                },
            }

            # Shapiro-Wilk (scipy) as supplement
            if SCIPY_AVAILABLE and len(resid) >= 3:
                sw_stat, sw_pval = shapiro(resid)
                result['shapiro_wilk'] = {
                    'statistic': round(float(sw_stat), 4),
                    'p_value': round(float(sw_pval), 4),
                    'pass': bool(sw_pval > alpha),
                }

            self.results['NORMALITY'] = result
        except Exception as e:
            self.results['NORMALITY'] = {'error': str(e)}

    # =====================================================================
    # TEST 5: BACKTESTING (Expanding Window + COVID Dummy)
    # =====================================================================
    def test_backtesting(self, use_covid_dummy=True, alpha=None):
        """
        Expanding Window Backtesting cho mô hình Log-Log.
        Rolling forward từ năm thứ 8. Hỗ trợ COVID Dummy toggle.
        """
        if not SKLEARN_AVAILABLE:
            self.results['BACKTESTING'] = {'error': 'sklearn not available'}
            return

        alpha = alpha or self.alpha
        loglog = self._build_loglog_data()
        if loglog is None:
            self.results['BACKTESTING'] = {'error': 'Insufficient data'}
            return

        years = loglog['years']
        n = len(years)
        min_train = 7  # Bắt đầu test từ năm thứ 8 (index 7)

        if n <= min_train:
            self.results['BACKTESTING'] = {'error': f'Cần ít nhất {min_train + 1} năm dữ liệu'}
            return

        ln_Q = loglog['ln_Q']
        ln_TC = loglog['ln_TC']
        ln_oil = loglog['ln_oil']
        ln_fx = loglog['ln_fx']
        covid = loglog['covid_dummy']

        backtest_results = []

        for test_idx in range(min_train, n):
            # Training data: 0 to test_idx-1
            train_end = test_idx

            ln_Q_train = ln_Q[:train_end]
            ln_TC_train = ln_TC[:train_end]
            ln_oil_train = ln_oil[:train_end]
            ln_fx_train = ln_fx[:train_end]
            covid_train = covid[:train_end]

            # FWL on training set
            reg_fx_aux = LinearRegression().fit(ln_Q_train.reshape(-1, 1), ln_fx_train)
            resid_fx_train = ln_fx_train - reg_fx_aux.predict(ln_Q_train.reshape(-1, 1))

            reg_oil_aux = LinearRegression().fit(ln_Q_train.reshape(-1, 1), ln_oil_train)
            resid_oil_train = ln_oil_train - reg_oil_aux.predict(ln_Q_train.reshape(-1, 1))

            if use_covid_dummy:
                X_train = np.column_stack((ln_Q_train, resid_oil_train, resid_fx_train, covid_train))
            else:
                X_train = np.column_stack((ln_Q_train, resid_oil_train, resid_fx_train))

            reg = LinearRegression(fit_intercept=True).fit(X_train, ln_TC_train)

            # Predict test point
            resid_fx_test = ln_fx[test_idx] - reg_fx_aux.predict(ln_Q[test_idx].reshape(1, -1))[0]
            resid_oil_test = ln_oil[test_idx] - reg_oil_aux.predict(ln_Q[test_idx].reshape(1, -1))[0]

            if use_covid_dummy:
                X_test = np.array([[ln_Q[test_idx], resid_oil_test, resid_fx_test, covid[test_idx]]])
            else:
                X_test = np.array([[ln_Q[test_idx], resid_oil_test, resid_fx_test]])

            predicted_ln_tc = float(reg.predict(X_test)[0])
            actual_ln_tc = float(ln_TC[test_idx])

            # Convert back to original scale
            predicted_tc = np.exp(predicted_ln_tc)
            actual_tc = np.exp(actual_ln_tc)

            error_pct = abs(predicted_tc - actual_tc) / actual_tc * 100 if actual_tc != 0 else 0

            backtest_results.append({
                'year': str(years[test_idx]),
                'train_size': train_end,
                'actual_ln_tc': round(actual_ln_tc, 4),
                'predicted_ln_tc': round(predicted_ln_tc, 4),
                'actual_tc': round(float(actual_tc), 2),
                'predicted_tc': round(float(predicted_tc), 2),
                'error_pct': round(float(error_pct), 2),
                'residual': round(actual_ln_tc - predicted_ln_tc, 4),
            })

        # Aggregate metrics
        errors = [r['error_pct'] for r in backtest_results]
        residuals_bt = [r['actual_tc'] - r['predicted_tc'] for r in backtest_results]

        mae = np.mean(np.abs(residuals_bt))
        rmse = np.sqrt(np.mean(np.array(residuals_bt) ** 2))
        mape = np.mean(errors)

        self.results['BACKTESTING'] = {
            'results': backtest_results,
            'metrics': {
                'MAE': round(float(mae), 2),
                'RMSE': round(float(rmse), 2),
                'MAPE': round(float(mape), 2),
                'n_tests': len(backtest_results),
            },
            'config': {
                'min_train_size': min_train,
                'use_covid_dummy': use_covid_dummy,
                'method': 'Expanding Window (Rolling Forward từ năm thứ 8)',
            },
            'alpha': alpha,
        }

    # =====================================================================
    # TEST 6: DISTRIBUTIONAL ASSUMPTIONS (Oil & FX)
    # =====================================================================
    def test_distributional(self, alpha=None):
        """
        KS test + Shapiro-Wilk cho phân phối returns của Oil & FX.
        Kiểm tra giả định phân phối chuẩn trong Ma trận Nhạy cảm.
        """
        if not SCIPY_AVAILABLE:
            self.results['DISTRIBUTIONAL'] = {'error': 'scipy not available'}
            return

        alpha = alpha or self.alpha
        loglog = self._build_loglog_data()
        if loglog is None:
            self.results['DISTRIBUTIONAL'] = {'error': 'Insufficient data'}
            return

        oil_arr = loglog['oil_arr']
        fx_arr = loglog['fx_arr']
        years = loglog['years']

        results = {}
        for name, arr in [('Oil_Price', oil_arr), ('FX_Rate', fx_arr)]:
            if len(arr) < 4:
                results[name] = {'error': 'Không đủ dữ liệu (n < 4)'}
                continue

            # Tính log-returns
            log_returns = np.diff(np.log(arr))

            if len(log_returns) < 3:
                results[name] = {'error': 'Không đủ log-returns (n < 3)'}
                continue

            # Standardize for KS test
            mean_r = np.mean(log_returns)
            std_r = np.std(log_returns, ddof=1)
            standardized = (log_returns - mean_r) / std_r if std_r > 0 else log_returns

            # KS test vs normal distribution
            ks_stat, ks_pval = kstest(standardized, 'norm')

            # Shapiro-Wilk
            sw_stat, sw_pval = shapiro(log_returns)

            # Distribution statistics
            skewness = float(pd.Series(log_returns).skew())
            kurtosis_val = float(pd.Series(log_returns).kurtosis())  # Excess kurtosis
            excess_kurtosis = kurtosis_val  # pandas kurtosis is already excess

            # Classification
            if abs(excess_kurtosis) > 3:
                dist_type = 'Fat-tailed (Leptokurtic)'
            elif abs(skewness) > 1:
                dist_type = 'Lệch (Skewed)'
            elif ks_pval > alpha:
                dist_type = 'Gần chuẩn (Approximately Normal)'
            else:
                dist_type = 'Không chuẩn (Non-Normal)'

            results[name] = {
                'ks_test': {
                    'statistic': round(float(ks_stat), 4),
                    'p_value': round(float(ks_pval), 4),
                    'is_normal': bool(ks_pval > alpha),
                },
                'shapiro_wilk': {
                    'statistic': round(float(sw_stat), 4),
                    'p_value': round(float(sw_pval), 4),
                    'is_normal': bool(sw_pval > alpha),
                },
                'statistics': {
                    'mean_return': round(float(mean_r * 100), 4),
                    'std_return': round(float(std_r * 100), 4),
                    'skewness': round(skewness, 4),
                    'excess_kurtosis': round(excess_kurtosis, 4),
                    'n_observations': len(log_returns),
                },
                'distribution_type': dist_type,
                'log_returns': log_returns.tolist(),
                'raw_values': arr.tolist(),
                'years': years,
            }

        self.results['DISTRIBUTIONAL'] = {
            'tests': results,
            'alpha': alpha,
        }

    # =====================================================================
    # TEST 7: SINGULARITY DETECTION (WACC-g Matrix)
    # =====================================================================
    def test_singularity(self):
        """
        Phát hiện điểm kỳ dị toán học trong ma trận DCF khi WACC ≤ g.
        Tính Condition Number cho numerical stability.
        """
        # Tái tạo ma trận WACC-g tương tự forecaster.dcf_sensitivity()
        is_df = self.dfs.get('INCOME STATEMENT')
        cf_df = self.dfs.get('CASH FLOW STATEMENT')
        fi = self.dfs.get('FINANCIAL INDEX')

        if is_df is None or cf_df is None:
            self.results['SINGULARITY'] = {'error': 'Insufficient data'}
            return

        years = self._get_years(is_df)

        # Get FCFF base
        ocf_row = self._get_row(cf_df, r'^Lưu chuyển tiền thuần từ các hoạt động sản xuất')
        capex_row = self._get_row(cf_df, r'^Tiền mua tài sản cố định')
        if ocf_row is not None and capex_row is not None:
            fcff_base = float(ocf_row[years[-1]]) + float(capex_row[years[-1]])
        else:
            fcff_base = 1000.0

        # WACC and g ranges
        wacc_vals = np.arange(0.06, 0.20 + 0.005, 0.005)
        g_vals = np.arange(-0.02, 0.10 + 0.005, 0.005)

        singularity_map = np.zeros((len(wacc_vals), len(g_vals)), dtype=int)
        near_singularity_map = np.zeros((len(wacc_vals), len(g_vals)), dtype=float)
        singular_cells = []

        for i, wacc in enumerate(wacc_vals):
            for j, g in enumerate(g_vals):
                gap = wacc - g
                near_singularity_map[i, j] = round(gap * 100, 2)  # percentage points

                if gap <= 0:
                    singularity_map[i, j] = 2  # True singularity
                    singular_cells.append({
                        'wacc': f'{wacc*100:.1f}%',
                        'g': f'{g*100:.1f}%',
                        'type': 'Kỳ dị (WACC ≤ g)',
                        'gap': round(gap * 100, 2),
                    })
                elif gap < 0.005:  # < 0.5%
                    singularity_map[i, j] = 1  # Near-singularity
                    singular_cells.append({
                        'wacc': f'{wacc*100:.1f}%',
                        'g': f'{g*100:.1f}%',
                        'type': 'Gần kỳ dị (WACC - g < 0.5%)',
                        'gap': round(gap * 100, 2),
                    })

        # Condition number of the matrix
        try:
            # Build a representative DCF matrix
            dcf_matrix = np.zeros((len(wacc_vals), len(g_vals)))
            for i, wacc in enumerate(wacc_vals):
                for j, g in enumerate(g_vals):
                    if wacc > g:
                        dcf_matrix[i, j] = fcff_base * (1 + g) / (wacc - g)
                    else:
                        dcf_matrix[i, j] = np.nan

            valid_matrix = dcf_matrix[~np.isnan(dcf_matrix).any(axis=1)]
            if len(valid_matrix) > 1:
                cond_number = float(np.linalg.cond(valid_matrix[:min(len(valid_matrix), 10), :min(valid_matrix.shape[1], 10)]))
            else:
                cond_number = float('inf')
        except Exception:
            cond_number = float('inf')

        # Stability assessment
        if cond_number < 100:
            stability = 'Ổn định (Well-conditioned)'
        elif cond_number < 1000:
            stability = 'Chấp nhận được (Moderate conditioning)'
        else:
            stability = 'Không ổn định (Ill-conditioned)'

        n_singular = sum(1 for c in singular_cells if c['type'].startswith('Kỳ dị'))
        n_near = sum(1 for c in singular_cells if c['type'].startswith('Gần'))

        self.results['SINGULARITY'] = {
            'singularity_map': singularity_map.tolist(),
            'gap_map': near_singularity_map.tolist(),
            'wacc_labels': [f'{w*100:.1f}%' for w in wacc_vals],
            'g_labels': [f'{g*100:.1f}%' for g in g_vals],
            'singular_cells': singular_cells[:20],  # Limit for display
            'n_singular': n_singular,
            'n_near_singular': n_near,
            'condition_number': round(cond_number, 2) if not np.isinf(cond_number) else 'Infinity',
            'stability': stability,
            'total_cells': len(wacc_vals) * len(g_vals),
        }

    # =====================================================================
    # TEST 8: ENDOGENEITY (Granger Causality + Auto-lag AIC/BIC)
    # =====================================================================
    def test_endogeneity(self, max_lag=2, alpha=None):
        """
        Kiểm định nội sinh trong cấu trúc vốn:
        - Granger Causality giữa Revenue ⇆ Leverage, EBIT ⇆ D/E
        - Tự động chọn lag tối ưu qua AIC/BIC
        - Hausman-type heuristic: Tương quan residual-regressor
        """
        if not STATSMODELS_AVAILABLE:
            self.results['ENDOGENEITY'] = {'error': 'statsmodels not available'}
            return

        alpha = alpha or self.alpha
        is_df = self.dfs.get('INCOME STATEMENT')
        bs_df = self.dfs.get('BALANCE SHEET')
        fi_df = self.dfs.get('FINANCIAL INDEX')

        if is_df is None or bs_df is None:
            self.results['ENDOGENEITY'] = {'error': 'Missing IS or BS data'}
            return

        years = self._get_years(is_df)
        if len(years) < max_lag + 4:
            self.results['ENDOGENEITY'] = {'error': f'Cần ít nhất {max_lag + 4} năm dữ liệu'}
            return

        # Extract series
        rev_row = self._get_row(is_df, r'^Doanh số thuần$')
        ebit_row = self._get_row(is_df, r'^EBIT$')
        npt_row = self._get_row(bs_df, r'^NỢ PHẢI TRẢ$')
        vcsh_row = self._get_row(bs_df, r'^VỐN CHỦ SỞ HỮU$')

        if any(r is None for r in [rev_row, ebit_row, npt_row, vcsh_row]):
            self.results['ENDOGENEITY'] = {'error': 'Missing required rows'}
            return

        rev = rev_row[years].astype(float).values
        ebit = ebit_row[years].astype(float).values
        npt = npt_row[years].astype(float).values
        vcsh = vcsh_row[years].astype(float).values

        # D/E ratio (handle negative equity)
        de_ratio = np.where(np.abs(vcsh) > 1, npt / np.abs(vcsh), np.nan)
        # Leverage ratio
        ta_row = self._get_row(bs_df, r'^TỔNG TÀI SẢN$')
        ta = ta_row[years].astype(float).values if ta_row is not None else npt + vcsh

        leverage = npt / np.maximum(ta, 1)

        # Log-transform revenue and EBIT (safe)
        ln_rev = np.log(np.maximum(rev, 1))
        ln_ebit_abs = np.log(np.maximum(np.abs(ebit), 1))

        granger_results = []
        pairs = [
            ('ln(Revenue)', 'Leverage', ln_rev, leverage),
            ('Leverage', 'ln(Revenue)', leverage, ln_rev),
            ('ln|EBIT|', 'Leverage', ln_ebit_abs, leverage),
            ('Leverage', 'ln|EBIT|', leverage, ln_ebit_abs),
        ]

        for cause_name, effect_name, cause, effect in pairs:
            # Remove NaN
            mask = ~(np.isnan(cause) | np.isnan(effect) | np.isinf(cause) | np.isinf(effect))
            c_clean = cause[mask]
            e_clean = effect[mask]

            if len(c_clean) < max_lag + 4:
                granger_results.append({
                    'cause': cause_name,
                    'effect': effect_name,
                    'error': 'Không đủ dữ liệu sau lọc NaN',
                })
                continue

            # Stack for Granger test (requires [effect, cause] format)
            data_gc = np.column_stack((e_clean, c_clean))

            try:
                # Run Granger for lag 1 to max_lag
                gc_result = grangercausalitytests(data_gc, maxlag=max_lag, verbose=False)

                # Auto-select best lag via min AIC (from OLS in gc_result)
                best_lag = 1
                best_aic = float('inf')
                lag_details = []

                for lag in range(1, max_lag + 1):
                    if lag in gc_result:
                        ssr_full = gc_result[lag][1][1].ssr  # Restricted model (OLS result)
                        n_obs = gc_result[lag][1][1].nobs
                        k_full = gc_result[lag][1][1].df_model + 1
                        # AIC = n * ln(SSR/n) + 2k
                        aic_val = n_obs * np.log(ssr_full / n_obs) + 2 * k_full
                        bic_val = n_obs * np.log(ssr_full / n_obs) + k_full * np.log(n_obs)

                        f_stat = gc_result[lag][0]['ssr_ftest'][0]
                        f_pval = gc_result[lag][0]['ssr_ftest'][1]

                        lag_details.append({
                            'lag': lag,
                            'f_statistic': round(float(f_stat), 4),
                            'p_value': round(float(f_pval), 4),
                            'aic': round(float(aic_val), 4),
                            'bic': round(float(bic_val), 4),
                            'is_significant': bool(f_pval < alpha),
                        })

                        if aic_val < best_aic:
                            best_aic = aic_val
                            best_lag = lag

                # Get result at optimal lag
                optimal = next((d for d in lag_details if d['lag'] == best_lag), lag_details[0] if lag_details else None)

                granger_results.append({
                    'cause': cause_name,
                    'effect': effect_name,
                    'optimal_lag': best_lag,
                    'lag_selection': f'AIC tối ưu tại Lag={best_lag}',
                    'f_statistic': optimal['f_statistic'] if optimal else None,
                    'p_value': optimal['p_value'] if optimal else None,
                    'is_granger_causal': optimal['is_significant'] if optimal else False,
                    'lag_details': lag_details,
                    'conclusion': (
                        f'{cause_name} Granger-gây ra {effect_name} (p={optimal["p_value"]:.4f} < α={alpha})'
                        if optimal and optimal['is_significant']
                        else f'{cause_name} KHÔNG Granger-gây ra {effect_name}'
                    ),
                })
            except Exception as e:
                granger_results.append({
                    'cause': cause_name,
                    'effect': effect_name,
                    'error': str(e),
                })

        # Hausman-type heuristic: Correlation between DuPont residuals and D/E
        hausman_result = None
        loglog = self._build_loglog_data()
        if loglog is not None:
            try:
                residuals = loglog['residuals']
                # Match length (residuals from regression may be same length as years)
                de_clean = de_ratio[:len(residuals)]
                mask = ~(np.isnan(de_clean) | np.isinf(de_clean))
                if mask.sum() >= 5:
                    corr = float(np.corrcoef(residuals[mask], de_clean[mask])[0, 1])
                    hausman_result = {
                        'correlation_resid_de': round(corr, 4),
                        'abs_correlation': round(abs(corr), 4),
                        'is_endogenous': bool(abs(corr) > 0.3),
                        'conclusion': (
                            f'Nghi ngờ nội sinh (|ρ|={abs(corr):.4f} > 0.3)'
                            if abs(corr) > 0.3
                            else f'Không có bằng chứng nội sinh (|ρ|={abs(corr):.4f} ≤ 0.3)'
                        ),
                    }
            except Exception:
                pass

        self.results['ENDOGENEITY'] = {
            'granger_tests': granger_results,
            'hausman_heuristic': hausman_result,
            'max_lag': max_lag,
            'alpha': alpha,
            'method_note': (
                f'Mô hình tự động chọn độ trễ tối ưu (Lag = k) dựa trên '
                f'tiêu chuẩn thiểu hóa AIC/BIC nhằm bảo toàn tối đa bậc tự do. '
                f'Lag_max = {max_lag}.'
            ),
        }

    # =====================================================================
    # RUN ALL
    # =====================================================================
    def run_all(self, alpha=None, use_covid_dummy=True):
        """Chạy tất cả 8 nhóm kiểm định."""
        alpha = alpha or self.alpha
        print("  [Diag 1/8] Stationarity (ADF + Cointegration)...")
        self.test_stationarity(alpha)
        print("  [Diag 2/8] Heteroskedasticity (Breusch-Pagan)...")
        self.test_heteroskedasticity(alpha)
        print("  [Diag 3/8] Autocorrelation (Durbin-Watson + Ljung-Box)...")
        self.test_autocorrelation(alpha)
        print("  [Diag 4/8] Normality (Jarque-Bera)...")
        self.test_normality(alpha)
        print("  [Diag 5/8] Backtesting (Expanding Window)...")
        self.test_backtesting(use_covid_dummy=use_covid_dummy, alpha=alpha)
        print("  [Diag 6/8] Distributional Assumptions (Oil & FX)...")
        self.test_distributional(alpha)
        print("  [Diag 7/8] Singularity Detection (WACC-g)...")
        self.test_singularity()
        print("  [Diag 8/8] Endogeneity (Granger Causality)...")
        self.test_endogeneity(alpha=alpha)
        print("  → Hoàn thành tất cả kiểm định.")
        return self.results

    def save_outputs(self, out_dir="output/2.5_diagnostics"):
        """Lưu kết quả kiểm định ra JSON files."""
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        for key, data in self.results.items():
            filepath = os.path.join(out_dir, f"{key}.json")
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4, default=str)
                print(f"  Saved: {filepath}")
            except Exception as e:
                print(f"  Error saving {key}: {e}")

        # Also save combined results
        combined_path = os.path.join(out_dir, "ALL_DIAGNOSTICS.json")
        try:
            with open(combined_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=4, default=str)
            print(f"  Saved combined: {combined_path}")
        except Exception as e:
            print(f"  Error saving combined: {e}")

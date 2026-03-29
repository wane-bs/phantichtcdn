"""
forecaster.py — Module Dự báo & Mô phỏng cho HVN Dashboard
==============================================================
Bao gồm:
  - STL Decomposition (Trend / Seasonal / Residual)
  - Valuation Bands (mean ± 1σ, ±2σ)
  - DCF Sensitivity Heatmap (WACC × g)
  - What-if ROE Simulator (3 kịch bản)

Triết lý: Không dự báo điểm. Tập trung vào bóc tách cấu trúc
và mô phỏng kịch bản để giải thích "tại sao".
"""

import numpy as np
import pandas as pd

try:
    from statsmodels.tsa.seasonal import STL, seasonal_decompose
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False


class Forecaster:
    def __init__(self, dfs_dict=None, in_dir=None):
        import os
        import pandas as pd
        if in_dir and os.path.exists(in_dir):
            self.dfs = {}
            for f in os.listdir(in_dir):
                if f.endswith('.csv'):
                    name = f.replace('.csv', '')
                    self.dfs[name] = pd.read_csv(os.path.join(in_dir, f))
        else:
            self.dfs = dfs_dict or {}

    def _get_row(self, df, pattern):
        row = df[df['Khoản mục'].str.contains(pattern, case=False, na=False, regex=True)]
        if not row.empty:
            return row.iloc[0]
        return None

    def _get_years(self, df):
        return [c for c in df.columns if c != 'Khoản mục']

    # =========================================================================
    # STL Decomposition
    # =========================================================================
    def stl_decomposition(self, series_name='Doanh thu'):
        """
        Bóc tách chuỗi thời gian thành Trend / Seasonal / Residual.
        Dùng STL nếu N >= 6, fallback sang seasonal_decompose nếu N < 6.
        
        Trả về dict {'trend': Series, 'seasonal': Series, 'residual': Series, 'original': Series}
        """
        is_df = self.dfs.get('INCOME STATEMENT')
        cf_df = self.dfs.get('CASH FLOW STATEMENT')
        bs_df = self.dfs.get('BALANCE SHEET')

        # Map tên → (df, pattern)
        series_map = {
            'Doanh thu thuần': (is_df, r'^Doanh số thuần$'),
            'Giá vốn hàng bán': (is_df, r'^Giá vốn hàng bán$'),
            'Lãi gộp': (is_df, r'^Lãi gộp$'),
            'EBIT': (is_df, r'^EBIT$'),
            'EBITDA': (is_df, r'^EBITDA$'),
            'Lợi nhuận ròng': (is_df, r'^Lãi/\(lỗ\) thuần sau thuế$'),
            'OCF (Hoạt động KD)': (cf_df, r'^Lưu chuyển tiền thuần từ các hoạt động sản xuất kinh doanh$'),
            'Tổng Tài sản': (bs_df, r'^TỔNG TÀI SẢN$'),
        }

        target = series_map.get(series_name)
        if target is None:
            return None
        df_target, pattern = target
        if df_target is None:
            return None

        row = self._get_row(df_target, pattern)
        if row is None:
            return None

        years = self._get_years(df_target)
        values = row[years].astype(float).values

        # Loại bỏ NaN
        valid_mask = ~np.isnan(values)
        valid_values = values[valid_mask]
        valid_years = [y for y, m in zip(years, valid_mask) if m]

        n = len(valid_values)
        if n < 2:
            return None

        original = pd.Series(valid_values, index=valid_years)

        try:
            if STATSMODELS_AVAILABLE and n >= 6:
                # Dùng STL với period=1 cho dữ liệu năm (không có seasonality thực)
                # period=2 là minimum; với dữ liệu năm, trend là phần quan trọng nhất
                result = STL(original, period=2, robust=True).fit()
                return {
                    'trend': result.trend,
                    'seasonal': result.seasonal,
                    'residual': result.resid,
                    'original': original,
                    'method': 'STL'
                }
            elif STATSMODELS_AVAILABLE and n >= 4:
                result = seasonal_decompose(original, model='additive', period=2, extrapolate_trend='freq')
                return {
                    'trend': pd.Series(result.trend, index=valid_years),
                    'seasonal': pd.Series(result.seasonal, index=valid_years),
                    'residual': pd.Series(result.resid, index=valid_years),
                    'original': original,
                    'method': 'seasonal_decompose'
                }
            else:
                # Fallback: moving average trend, no seasonal
                trend = original.rolling(window=min(3, n), center=True, min_periods=1).mean()
                residual = original - trend
                seasonal = pd.Series([0.0] * n, index=valid_years)
                return {
                    'trend': trend,
                    'seasonal': seasonal,
                    'residual': residual,
                    'original': original,
                    'method': 'moving_average'
                }
        except Exception as e:
            print(f"STL error: {e}")
            trend = original.rolling(window=min(3, n), center=True, min_periods=1).mean()
            residual = original - trend
            return {
                'trend': trend,
                'seasonal': pd.Series([0.0] * n, index=valid_years),
                'residual': residual,
                'original': original,
                'method': 'fallback'
            }

    def get_stl_series_options(self):
        """Trả về danh sách tên chuỗi có thể phân rã."""
        return [
            'Doanh thu thuần', 'Giá vốn hàng bán', 'Lãi gộp',
            'EBIT', 'EBITDA', 'Lợi nhuận ròng',
            'OCF (Hoạt động KD)', 'Tổng Tài sản'
        ]

    # =========================================================================
    # Valuation Bands
    # =========================================================================
    def valuation_bands(self, pe_series=None):
        """
        Tính dải định giá lịch sử dựa trên P/E hoặc P/B.
        Band = mean ± 1σ, ±2σ
        Band Position = (current - lower) / (upper - lower)
        """
        fi = self.dfs.get('FINANCIAL INDEX')
        if fi is None:
            return None

        years = self._get_years(fi)

        if pe_series is None:
            pe_row = self._get_row(fi, r'^P/E$')
            if pe_row is None:
                return None
            pe_series = pe_row[years].astype(float)

        pe_vals = pe_series.replace(0, np.nan).dropna()
        if len(pe_vals) < 2:
            return None

        mean_pe = pe_vals.mean()
        std_pe = pe_vals.std()

        bands = {
            'original': pe_series,
            'mean': mean_pe,
            'upper_1s': mean_pe + std_pe,
            'lower_1s': mean_pe - std_pe,
            'upper_2s': mean_pe + 2 * std_pe,
            'lower_2s': mean_pe - 2 * std_pe,
            'years': list(pe_series.index),
        }

        # Band Position = (current - lower_1s) / (upper_1s - lower_1s)
        if std_pe != 0:
            current = float(pe_series.iloc[-1])
            bands['band_position'] = (current - bands['lower_1s']) / (bands['upper_1s'] - bands['lower_1s'])
        else:
            bands['band_position'] = 0.5

        return bands

    # =========================================================================
    # DCF Sensitivity Heatmap
    # =========================================================================
    def dcf_sensitivity(self, fcff_base=None, wacc_range=(0.08, 0.16, 0.005),
                         g_range=(0.0, 0.06, 0.005)):
        """
        Ma trận WACC × g → Giá trị nội tại (Gordon Growth Model simplified).
        
        Công thức: V = FCFF / (WACC - g)
        
        wacc_range: (start, stop, step)
        g_range: (start, stop, step)
        """
        is_df = self.dfs.get('INCOME STATEMENT')
        cf_df = self.dfs.get('CASH FLOW STATEMENT')

        # Tính FCFF base nếu chưa có
        if fcff_base is None:
            if cf_df is not None:
                ocf_row = self._get_row(cf_df, r'^Lưu chuyển tiền thuần từ các hoạt động sản xuất')
                if ocf_row is not None:
                    years = self._get_years(cf_df)
                    fcff_base = float(ocf_row[years[-1]])  # dùng năm gần nhất
                else:
                    fcff_base = 1000.0  # fallback (1000 tỷ)
            else:
                fcff_base = 1000.0

        wacc_vals = np.arange(wacc_range[0], wacc_range[1] + wacc_range[2] / 2, wacc_range[2])
        g_vals = np.arange(g_range[0], g_range[1] + g_range[2] / 2, g_range[2])

        matrix = np.zeros((len(wacc_vals), len(g_vals)))
        for i, wacc in enumerate(wacc_vals):
            for j, g in enumerate(g_vals):
                if wacc > g:
                    matrix[i, j] = round(fcff_base / (wacc - g), 1)
                else:
                    matrix[i, j] = np.nan

        return {
            'matrix': matrix,
            'wacc_labels': [f'{w*100:.1f}%' for w in wacc_vals],
            'g_labels': [f'{g_*100:.1f}%' for g_ in g_vals],
            'wacc_vals': wacc_vals,
            'g_vals': g_vals,
            'fcff_base': fcff_base,
        }

    # =========================================================================
    # What-if ROE Simulator
    # =========================================================================
    def what_if_roe(self, target_roe_delta=0.10):
        """
        Giữ 2 nhân tố DuPont, tính nhân tố thứ 3 cần thiết để ROE tăng target_roe_delta.
        
        target_roe_delta: float, ví dụ 0.10 = tăng 10%
        
        3 kịch bản:
          1. Cải thiện ROS: AT_cần = ROE_mục_tiêu / (NM × EM)
          2. Cải thiện AT:  ROS_cần = ROE_mục_tiêu / (AT × EM)
          3. Cải thiện Lev: ...
        """
        dupont = self.dfs.get('DUPONT')
        if dupont is None:
            return None

        years = self._get_years(dupont)
        if not years:
            return None

        latest = years[-1]

        ros_row = dupont[dupont['Khoản mục'].str.contains(r'^ROS', regex=True)]
        at_row  = dupont[dupont['Khoản mục'].str.contains(r'^Asset Turnover', regex=True)]
        lev_row = dupont[dupont['Khoản mục'].str.contains(r'^Financial Leverage', regex=True)]
        roe_row = dupont[dupont['Khoản mục'].str.contains(r'^ROE', regex=True)]

        if any(df.empty for df in [ros_row, at_row, lev_row, roe_row]):
            return None

        ros = float(ros_row.iloc[0][latest]) / 100
        at  = float(at_row.iloc[0][latest])
        lev = float(lev_row.iloc[0][latest])
        roe_current = float(roe_row.iloc[0][latest]) / 100

        roe_target = roe_current + target_roe_delta

        def safe_div(num, den):
            if abs(den) < 1e-9:
                return None
            return round(num / den, 4)

        result = {
            'roe_current_pct': round(roe_current * 100, 2),
            'roe_target_pct': round(roe_target * 100, 2),
            'delta_pct': round(target_roe_delta * 100, 2),
            'current_ros': round(ros * 100, 2),
            'current_at': round(at, 4),
            'current_lev': round(lev, 4),
            # Kịch bản 1: Cải thiện ROS, giữ AT và Lev
            'scenario_ros': {
                'name': 'Cải thiện ROS (giữ AT & Lev)',
                'need_ros_pct': round(safe_div(roe_target, at * lev) * 100, 2) if safe_div(roe_target, at * lev) else None,
                'fix_at': round(at, 4),
                'fix_lev': round(lev, 4),
            },
            # Kịch bản 2: Cải thiện AT, giữ ROS và Lev
            'scenario_at': {
                'name': 'Cải thiện AT (giữ ROS & Lev)',
                'need_at': safe_div(roe_target, ros * lev) if ros * lev != 0 else None,
                'fix_ros_pct': round(ros * 100, 2),
                'fix_lev': round(lev, 4),
            },
            # Kịch bản 3: Cải thiện Lev, giữ ROS và AT
            'scenario_lev': {
                'name': 'Điều chỉnh Đòn bẩy (giữ ROS & AT)',
                'need_lev': safe_div(roe_target, ros * at) if ros * at != 0 else None,
                'fix_ros_pct': round(ros * 100, 2),
                'fix_at': round(at, 4),
            },
            'latest_year': latest,
        }
        return result

    def save_outputs(self, results, out_dir="output/4_advanced"):
        import os
        import json
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # Trích xuất và lưu riêng rẽ các components để đáp ứng yêu cầu CSV, JSON
        if 'STL_REVENUE' in results:
            stl = results['STL_REVENUE']
            stl_df = pd.DataFrame({
                'original': stl['original'],
                'trend': stl['trend'],
                'seasonal': stl['seasonal'],
                'residual': stl['residual']
            })
            stl_df.index.name = 'Year'
            stl_df.to_csv(os.path.join(out_dir, "stl_revenue.csv"))
            with open(os.path.join(out_dir, "stl_method.json"), 'w') as f:
                json.dump({'method': stl['method']}, f)
                
        if 'VALUATION_BANDS' in results:
            vb = results['VALUATION_BANDS']
            bands_df = pd.DataFrame({
                'original': vb['original'],
                'mean': [vb['mean']] * len(vb['years']),
                'upper_1s': [vb['upper_1s']] * len(vb['years']),
                'lower_1s': [vb['lower_1s']] * len(vb['years']),
                'upper_2s': [vb['upper_2s']] * len(vb['years']),
                'lower_2s': [vb['lower_2s']] * len(vb['years'])
            }, index=vb['years'])
            bands_df.index.name = 'Year'
            bands_df.to_csv(os.path.join(out_dir, "valuation_bands.csv"))
            with open(os.path.join(out_dir, "valuation_meta.json"), 'w') as f:
                json.dump({'band_position': vb['band_position']}, f)

        if 'DCF_MATRIX' in results:
            dcf = results['DCF_MATRIX']
            # Save matrix as CSV
            dcf_df = pd.DataFrame(dcf['matrix'], index=dcf['wacc_labels'], columns=dcf['g_labels'])
            dcf_df.index.name = 'WACC / g'
            dcf_df.to_csv(os.path.join(out_dir, "dcf_matrix.csv"))
            # Save meta as JSON
            meta = {
                'wacc_vals': list(dcf['wacc_vals']),
                'g_vals': list(dcf['g_vals']),
                'fcff_base': dcf['fcff_base']
            }
            with open(os.path.join(out_dir, "dcf_meta.json"), 'w') as f:
                json.dump(meta, f)

        if 'WHATIF_ROE' in results:
            wi = results['WHATIF_ROE']
            with open(os.path.join(out_dir, "whatif_roe.json"), 'w', encoding='utf-8') as f:
                json.dump(wi, f, ensure_ascii=False, indent=4)
                
        print(f"Forecaster outputs saved to {out_dir}")

    # =========================================================================
    # RUN ALL
    # =========================================================================
    def run_all(self):
        """Chạy các phân tích và trả về dict kết quả."""
        results = {}

        # STL cho Doanh thu
        stl = self.stl_decomposition('Doanh thu thuần')
        if stl:
            results['STL_REVENUE'] = stl

        # Valuation Bands
        vb = self.valuation_bands()
        if vb:
            results['VALUATION_BANDS'] = vb

        # DCF Matrix
        dcf = self.dcf_sensitivity()
        if dcf:
            results['DCF_MATRIX'] = dcf

        # What-if ROE
        whatif = self.what_if_roe()
        if whatif:
            results['WHATIF_ROE'] = whatif

        return results

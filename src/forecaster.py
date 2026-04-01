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
    def valuation_bands(self, series_name=r'^EV/EBITDA$'):
        """
        Tính dải định giá lịch sử dựa trên phân phối của EV/EBITDA.
        Band = mean ± 1σ, ±2σ
        """
        fi = self.dfs.get('FINANCIAL INDEX')
        if fi is None:
            return None

        years = self._get_years(fi)
        row = self._get_row(fi, series_name)
        if row is None:
            return None
            
        series = row[years].astype(float)
        vals = series.replace(0, np.nan).dropna()
        if len(vals) < 2:
            return None

        mean_val = vals.mean()
        std_val = vals.std()

        bands = {
            'original': series,
            'mean': mean_val,
            'upper_1s': mean_val + std_val,
            'lower_1s': mean_val - std_val,
            'upper_2s': mean_val + 2 * std_val,
            'lower_2s': mean_val - 2 * std_val,
            'years': list(series.index),
        }

        if std_val != 0:
            current = float(series.iloc[-1])
            bands['band_position'] = (current - bands['lower_1s']) / (bands['upper_1s'] - bands['lower_1s'])
        else:
            bands['band_position'] = 0.5

        return bands

    # =========================================================================
    # DCF Sensitivity Heatmap
    # =========================================================================
    def dcf_sensitivity(self, fcff_base=None, ebitda_base=None, ev_ebitda_multiple=None,
                        wacc_range=(0.08, 0.16, 0.005), ebitda_growth_range=(-0.02, 0.08, 0.005)):
        """
        Ma trận Terminal Value Integration DCF:
        - Tích hợp dự phóng FCFF 5 năm và Terminal Value dựa trên EBITDA_n × Mean(EV/EBITDA).
        """
        is_df = self.dfs.get('INCOME STATEMENT')
        cf_df = self.dfs.get('CASH FLOW STATEMENT')
        fi = self.dfs.get('FINANCIAL INDEX')

        if fcff_base is None:
            if cf_df is not None:
                ocf_row = self._get_row(cf_df, r'^Lưu chuyển tiền thuần từ các hoạt động sản xuất')
                capex_row = self._get_row(cf_df, r'^Tiền mua tài sản cố định')
                if ocf_row is not None and capex_row is not None:
                    years = self._get_years(cf_df)
                    fcff_base = float(ocf_row[years[-1]]) + float(capex_row[years[-1]])
                else:
                    fcff_base = 1000.0
            else:
                fcff_base = 1000.0

        if ebitda_base is None:
            if is_df is not None:
                ebitda_row = self._get_row(is_df, r'^EBITDA$')
                if ebitda_row is not None:
                    years = self._get_years(is_df)
                    ebitda_base = float(ebitda_row[years[-1]])
                else:
                    ebitda_base = 2000.0
            else:
                ebitda_base = 2000.0
                
        if ev_ebitda_multiple is None:
            if fi is not None:
                ev_ebitda_row = self._get_row(fi, r'^EV/EBITDA$')
                if ev_ebitda_row is not None:
                    years = self._get_years(fi)
                    ev_ebitda_multiple = float(ev_ebitda_row[years].astype(float).mean())
                    if pd.isna(ev_ebitda_multiple): ev_ebitda_multiple = 8.0
                else:
                    ev_ebitda_multiple = 8.0
            else:
                ev_ebitda_multiple = 8.0

        wacc_vals = np.arange(wacc_range[0], wacc_range[1] + wacc_range[2] / 2, wacc_range[2])
        g_vals = np.arange(ebitda_growth_range[0], ebitda_growth_range[1] + ebitda_growth_range[2] / 2, ebitda_growth_range[2])

        matrix = np.zeros((len(wacc_vals), len(g_vals)))
        n_years = 5
        
        for i, wacc in enumerate(wacc_vals):
            for j, g in enumerate(g_vals):
                ev = 0
                current_fcff = fcff_base
                for t in range(1, n_years + 1):
                    current_fcff *= (1 + g)
                    ev += current_fcff / ((1 + wacc) ** t)
                
                ebitda_terminal = ebitda_base * ((1 + g) ** n_years)
                tv = ebitda_terminal * ev_ebitda_multiple
                ev += tv / ((1 + wacc) ** n_years)
                matrix[i, j] = round(ev, 1)

        return {
            'matrix': matrix,
            'wacc_labels': [f'{w*100:.1f}%' for w in wacc_vals],
            'g_labels': [f'{g_*100:.1f}%' for g_ in g_vals],
            'wacc_vals': wacc_vals,
            'g_vals': g_vals,
            'fcff_base': fcff_base,
            'ebitda_base': ebitda_base,
            'ev_ebitda_multiple': ev_ebitda_multiple
        }

    # =========================================================================
    # Structural Sensitivity (Oil & FX)
    # =========================================================================
    def structural_sensitivity(self, base_oil=90.0, base_fx=25000.0, 
                               fuel_opex_ratio=0.375, usd_debt_ratio=0.8,
                               oil_range=(70, 110, 5), fx_range=(24500, 26000, 100)):
        """
        Ma trận nhạy cảm dựa trên cấu trúc chi phí và nợ:
        - Biến 1: Giá dầu Jet A1
        - Biến 2: Tỷ giá USD/VND
        - Output: EV/EBITDA
        """
        is_df = self.dfs.get('INCOME STATEMENT')
        bs_df = self.dfs.get('BALANCE SHEET')
        fi = self.dfs.get('FINANCIAL INDEX')
        
        if is_df is None or bs_df is None or fi is None:
            return None

        years = self._get_years(is_df)
        latest = years[-1]
        
        # Base Values from Data
        ebitda_row = self._get_row(is_df, r'^EBITDA$')
        rev_row = self._get_row(is_df, r'^Doanh số thuần$')
        
        if ebitda_row is None or rev_row is None:
            return None
            
        ebitda_base = float(ebitda_row[latest])
        rev_base = float(rev_row[latest])
        opex_base = rev_base - ebitda_base
        
        # Cost Breakdown
        fuel_cost_base = opex_base * fuel_opex_ratio
        non_fuel_opex_base = opex_base * (1 - fuel_opex_ratio)
        
        # Debt & Equity
        mc_row = self._get_row(fi, r'^Vốn hóa$|Market Cap')
        if mc_row is None:
            return None
        mc_base = float(mc_row[latest])
        
        nnh = self._get_row(bs_df, r'^Nợ ngắn hạn$')
        ndh = self._get_row(bs_df, r'^Nợ dài hạn$')
        if nnh is None or ndh is None:
            debt_total_base = 0.0
        else:
            debt_total_base = float(nnh[latest]) + float(ndh[latest])
        
        cash_row = self._get_row(bs_df, r'^Tiền và các khoản tương đương tiền$|^Tiền và tương đương tiền$')
        cash_base = float(cash_row[latest]) if cash_row is not None else 0.0
        
        # 3. Income Statement / Cash Impact Base
        ni_row = self._get_row(is_df, r'^Lãi/\(lỗ\) thuần sau thuế$')
        ni_base = float(ni_row[latest]) if ni_row is not None else 0.0
        interest_row = self._get_row(is_df, r'^Chi phí lãi vay$')
        interest_base = abs(float(interest_row[latest])) if interest_row is not None else 0.0

        # Ranges
        oil_vals = np.arange(oil_range[0], oil_range[1] + oil_range[2] / 2, oil_range[2])
        fx_vals = np.arange(fx_range[0], fx_range[1] + fx_range[2] / 2, fx_range[2])
        
        matrix_ev = np.zeros((len(fx_vals), len(oil_vals)))
        matrix_ni = np.zeros((len(fx_vals), len(oil_vals)))
        
        # We also want to return the 'deltas' for the exact sliders provided
        # (Though the heatmap covers the range, these components are useful for the 'Live Impact' UI)
        
        for i, fx in enumerate(fx_vals):
            for j, oil in enumerate(oil_vals):
                # A. EBITDA Impact (Impacts Operating Profit)
                fuel_new = fuel_cost_base * (oil / base_oil) * (fx / base_fx)
                non_fuel_new = non_fuel_opex_base * (fx / base_fx)
                new_ebitda = rev_base - (fuel_new + non_fuel_new)
                
                # B. Financial / Net Profit Impact
                # 1. Fuel cost delta
                fuel_delta = fuel_new - fuel_cost_base
                # 2. Interest cost delta (assume interest scales with FX if debt is USD)
                interest_new = interest_base * (1 - usd_debt_ratio) + (interest_base * usd_debt_ratio * fx / base_fx)
                int_delta = interest_new - interest_base
                # 3. FX Revaluation Loss (Non-cash but hits NI)
                debt_usd = (float(nnh[latest]) + float(ndh[latest])) * usd_debt_ratio
                fx_reval_loss = debt_usd * (fx / base_fx - 1)
                
                new_ni = ni_base - fuel_delta - int_delta - fx_reval_loss
                matrix_ni[i, j] = round(new_ni, 1)

                # C. EV calculation
                debt_total_base = float(nnh[latest]) + float(ndh[latest])
                new_debt = (debt_total_base * (1 - usd_debt_ratio)) + (debt_total_base * usd_debt_ratio * fx / base_fx)
                new_ev = mc_base + new_debt - cash_base
                
                if new_ebitda > 0:
                    matrix_ev[i, j] = round(new_ev / new_ebitda, 2)
                else:
                    matrix_ev[i, j] = np.nan
                    
        return {
            'matrix': matrix_ev,
            'ni_matrix': matrix_ni,
            'oil_labels': [f'${o}' for o in oil_vals],
            'fx_labels': [f'{f:,.0f}' for f in fx_vals],
            'oil_vals': oil_vals,
            'fx_vals': fx_vals,
            'base_data': {
                'ebitda': ebitda_base,
                'revenue': rev_base,
                'debt': float(nnh[latest]) + float(ndh[latest]),
                'mc': mc_base,
                'cash': cash_base,
                'ni': ni_base,
                'fuel_cost': fuel_cost_base,
                'interest': interest_base
            }
        }

    # =========================================================================
    # Scenario Analysis (Line Chart)
    # =========================================================================
    def scenario_analysis(self):
        """
        Dự phóng 3 kịch bản EV/EBITDA từ 2023 - 2028:
        - Kịch bản Cơ sở: Jet Fuel $85-90, tăng trưởng ổn định.
        - Kịch bản Tiêu cực: Sốc giá dầu/tỷ giá, EBITDA sụt giảm.
        - Kịch bản Tích cực: Long Thành (2026), Trung Quốc phục hồi, Yield tối ưu.
        """
        is_df = self.dfs.get('INCOME STATEMENT')
        fi_df = self.dfs.get('FINANCIAL INDEX')
        bs_df = self.dfs.get('BALANCE SHEET')
        
        if is_df is None or fi_df is None or bs_df is None:
            return None

        years_hist = self._get_years(is_df)
        latest_year = int(years_hist[-1])
        proj_years = [str(y) for y in range(latest_year, latest_year + 6)] # 2023 to 2028
        
        # Base values from latest year
        ebitda_row = self._get_row(is_df, r'^EBITDA$')
        if ebitda_row is None: return None
        ebitda_latest = float(ebitda_row[str(latest_year)])
        
        ev_row = self._get_row(fi_df, r'^EV \(Enterprise Value\)')
        if ev_row is None:
             # Fallback calculation if EV row missing
             mc_row = self._get_row(fi_df, r'^Vốn hóa$|Market Cap')
             nnh_row = self._get_row(bs_df, r'^Nợ ngắn hạn$')
             ndh_row = self._get_row(bs_df, r'^Nợ dài hạn$')
             cash_row = self._get_row(bs_df, r'^Tiền và tương đương tiền$|^Tiền và các khoản tương đương tiền$')
             
             if any(r is None for r in [mc_row, nnh_row, ndh_row, cash_row]):
                 ev_latest = 0.0
             else:
                 ev_latest = float(mc_row[str(latest_year)]) + float(nnh_row[str(latest_year)]) + float(ndh_row[str(latest_year)]) - float(cash_row[str(latest_year)])
        else:
            ev_latest = float(ev_row[str(latest_year)])

        if ebitda_latest <= 0: # Avoid division by zero, use a small proxy if needed or cap
            ebitda_latest = 1000.0 # Placeholder for distressed recovery start

        # Scenario Projections
        ebitda_base = [ebitda_latest]
        ebitda_neg = [ebitda_latest]
        ebitda_pos = [ebitda_latest]
        
        ev_base = [ev_latest]
        ev_neg = [ev_latest]
        ev_pos = [ev_latest]

        for i in range(1, 6): # years 1 to 5
            # Base Scenario: 7% EBITDA growth, 3% EV growth
            ebitda_base.append(ebitda_base[-1] * 1.07)
            ev_base.append(ev_base[-1] * 1.03)
            
            # Negative Scenario: Year 1 shock (-20% EBITDA), then 2% recovery. EV increases 10% (debt burden)
            if i == 1:
                ebitda_neg.append(ebitda_neg[-1] * 0.8)
                ev_neg.append(ev_neg[-1] * 1.15)
            else:
                ebitda_neg.append(ebitda_neg[-1] * 1.02)
                ev_neg.append(ev_neg[-1] * 1.01)
                
            # Positive Scenario: Year 1-2 (12% recovery), Year 3+ (Long Thành + Yield: 35% jump)
            if i < 3:
                ebitda_pos.append(ebitda_pos[-1] * 1.12)
                ev_pos.append(ev_pos[-1] * 1.02)
            else:
                ebitda_pos.append(ebitda_pos[-1] * 1.35)
                ev_pos.append(ev_pos[-1] * 0.97) # Significant FCFF reduces Net Debt

        # Calculate EV/EBITDA ratios
        ratio_base = [ev / eb for ev, eb in zip(ev_base, ebitda_base)]
        ratio_neg = [ev / eb for ev, eb in zip(ev_neg, ebitda_neg)]
        ratio_pos = [ev / eb for ev, eb in zip(ev_pos, ebitda_pos)]
        
        return {
            'years': proj_years,
            'base': [round(r, 2) for r in ratio_base],
            'negative': [round(r, 2) for r in ratio_neg],
            'positive': [round(r, 2) for r in ratio_pos]
        }

    # =========================================================================
    # What-if ROE Simulator
    # =========================================================================
    def football_field_data(self, valuation_bands_res, dcf_matrix_res):
        """
        Tổng hợp dải giá trị từ các phương pháp định giá:
        1. EV/EBITDA History (1 std dev)
        2. DCF Terminal Value Integration
        3. Current Enterprise Value
        """
        bs_df = self.dfs.get('BALANCE SHEET')
        fi = self.dfs.get('FINANCIAL INDEX')
        
        current_ev = 0.0
        if fi is not None and bs_df is not None:
            years = self._get_years(bs_df)
            latest = years[-1]
            mc_row = self._get_row(fi, r'^Vốn hóa$')
            nnh = self._get_row(bs_df, r'^Nợ ngắn hạn$')
            ndh = self._get_row(bs_df, r'^Nợ dài hạn$')
            cash = self._get_row(bs_df, r'^Tiền và tương đương tiền$')
            if cash is None:
                cash = pd.Series([0]*len(years), index=years)
                c_row = self._get_row(bs_df, r'^Tiền và các khoản tương đương tiền$')
                if c_row is not None:
                    cash = c_row

            if mc_row is not None and nnh is not None and ndh is not None:
                try:
                    mc_val = float(mc_row[latest])
                    debt_val = float(nnh[latest]) + float(ndh[latest])
                    cash_val = float(cash[latest])
                    net_debt = debt_val - cash_val
                    current_ev = mc_val + net_debt
                except:
                    current_ev = 0.0

        ev_ebitda_min = 0.0
        ev_ebitda_max = 0.0
        if valuation_bands_res is not None and dcf_matrix_res is not None:
            ebitda_base = dcf_matrix_res.get('ebitda_base', 0)
            ev_ebitda_min = ebitda_base * valuation_bands_res.get('lower_1s', 0)
            ev_ebitda_max = ebitda_base * valuation_bands_res.get('upper_1s', 0)
        
        dcf_min = 0.0
        dcf_max = 0.0
        if dcf_matrix_res is not None:
            mat = dcf_matrix_res.get('matrix')
            if mat is not None:
                dcf_min = np.nanmin(mat)
                dcf_max = np.nanmax(mat)
                
        return {
            'current_ev': round(current_ev, 1),
            'ev_ebitda_min': round(ev_ebitda_min, 1),
            'ev_ebitda_max': round(ev_ebitda_max, 1),
            'dcf_min': round(dcf_min, 1),
            'dcf_max': round(dcf_max, 1)
        }

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

        if 'FOOTBALL_FIELD' in results:
            ff = results['FOOTBALL_FIELD']
            with open(os.path.join(out_dir, "football_field.json"), 'w', encoding='utf-8') as f:
                json.dump(ff, f, ensure_ascii=False, indent=4)
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

        # Football Field Data
        football = self.football_field_data(vb, dcf)
        if football:
            results['FOOTBALL_FIELD'] = football

        return results

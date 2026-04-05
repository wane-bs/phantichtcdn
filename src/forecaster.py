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
        if df is None: return []
        # Filter: Only keep columns that can be cast to int (numeric years)
        years = []
        for c in df.columns:
            if c != 'Khoản mục':
                try:
                    int(str(c).split('.')[0])
                    years.append(c)
                except ValueError:
                    continue
        # Sort years numerically to ensure years[-1] is the latest
        return sorted(years, key=lambda x: int(str(x).split('.')[0]))

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
    def valuation_bands(self, series_name='EV/EBITDA'):
        """
        Tính dải định giá lịch sử dựa trên phân phối của EV/EBITDA.
        Band = mean ± 1σ, ±2σ
        Lưu ý: Loại bỏ các giá trị âm (do EBITDA âm) và loại bỏ những năm Vốn chủ sở hữu âm.
        """
        fi = self.dfs.get('FINANCIAL INDEX')
        bs = self.dfs.get('BALANCE SHEET')
        if fi is None:
            return None

        years = self._get_years(fi)
        row = self._get_row(fi, series_name)
        if row is None:
            return None
            
        series = row[years].astype(float)
        # Bắt đầu với các năm có EV/EBITDA dương
        vals = series[series > 0].dropna()
        
        # Lọc bỏ những năm Vốn chủ sở hữu âm
        if bs is not None:
            vcsh_row = self._get_row(bs, r'^VỐN CHỦ SỞ HỮU$')
            if vcsh_row is not None:
                vcsh_series = vcsh_row[years].astype(float)
                positive_vcsh_years = vcsh_series[vcsh_series > 0].index
                vals = vals[vals.index.isin(positive_vcsh_years)]
                
        if len(vals) < 2:
            return None

        mean_val = vals.mean()
        std_val = vals.std()

        bands = {
            'original': series,
            'mean': mean_val,
            'upper_1s': mean_val + std_val,
            'lower_1s': max(0.1, mean_val - std_val), 
            'upper_2s': mean_val + 2 * std_val,
            'lower_2s': max(0.1, mean_val - 2 * std_val),
            'years': list(series.index),
        }

        if std_val != 0:
            current = float(series.iloc[-1])
            # Normalize current pos between lower_1s and upper_1s
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
                    # Lấy mean của các EV/EBITDA dương (Loại bỏ các năm crisis)
                    hist_multiples = ev_ebitda_row[years].astype(float)
                    ev_ebitda_multiple = float(hist_multiples[hist_multiples > 0].mean())
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
    def scenario_analysis(self, base_oil=90.0, base_fx=26300.0,
                          fuel_opex_ratio=0.375, usd_debt_ratio=0.8):
        """
        Dự phóng 3 kịch bản EV/EBITDA tích hợp định lượng:
        - Neo kịch bản từ Ma trận Nhạy cảm Cấu trúc (3b) để tính EBITDA Year-1
        - Sử dụng độ co giãn Log-Log (MACRO_REGRESSION) để hiệu chỉnh tốc độ trôi chi phí dài hạn
        - Giữ nguyên logic EV projection cho nợ/vốn hóa

        3 kịch bản vĩ mô:
          Base:     Oil ổn định ($base), FX ổn định, tăng trưởng EBITDA tự nhiên ~7%
          Negative: Oil +$20 (sốc), FX +5% (mất giá VND), EBITDA bị ăn mòn theo cấu trúc
          Positive: Oil -$15, FX -2% (VND tăng giá), cộng hiệu ứng Long Thành từ năm 3
        """
        is_df = self.dfs.get('INCOME STATEMENT')
        fi_df = self.dfs.get('FINANCIAL INDEX')
        bs_df = self.dfs.get('BALANCE SHEET')
        
        if is_df is None or fi_df is None or bs_df is None:
            return None

        years_hist = self._get_years(is_df)
        latest_year = int(years_hist[-1])
        proj_years = [str(y) for y in range(latest_year, latest_year + 6)]
        
        # ── Lấy dữ liệu nền từ BCTC ──
        ebitda_row = self._get_row(is_df, r'^EBITDA$')
        rev_row = self._get_row(is_df, r'^Doanh số thuần$')
        if ebitda_row is None or rev_row is None: return None
        
        ebitda_latest = float(ebitda_row[str(latest_year)])
        rev_latest = float(rev_row[str(latest_year)])
        opex_latest = rev_latest - ebitda_latest
        fuel_cost_base = opex_latest * fuel_opex_ratio
        non_fuel_opex_base = opex_latest * (1 - fuel_opex_ratio)
        
        ev_row = self._get_row(fi_df, r'^EV \(Enterprise Value\)')
        if ev_row is None:
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

        if ebitda_latest <= 0:
            ebitda_latest = 1000.0

        # ── Lấy độ co giãn Log-Log từ pipeline (nếu có) ──
        macro_reg = self.dfs.get('MACRO_REGRESSION')
        if isinstance(macro_reg, dict):
            e_oil = macro_reg.get('elasticity_oil', 0.04)
            e_fx = macro_reg.get('elasticity_fx', 0.66)
        else:
            e_oil = 0.04
            e_fx = 0.66

        # ── Hàm tính EBITDA mới theo kịch bản Oil/FX (logic 3b) ──
        def _compute_ebitda(oil_price, fx_rate):
            fuel_new = fuel_cost_base * (oil_price / base_oil) * (fx_rate / base_fx)
            non_fuel_new = non_fuel_opex_base * (fx_rate / base_fx)
            return rev_latest - (fuel_new + non_fuel_new)

        # ── Định nghĩa 3 đường dẫn vĩ mô (Oil, FX) qua 5 năm ──
        # Mỗi năm: (oil_price, fx_rate)
        paths = {
            'base': [],      # Oil ổn định, FX ổn định
            'negative': [],  # Oil tăng sốc rồi neo cao, FX mất giá dần
            'positive': [],  # Oil giảm rồi ổn định, FX ổn định/tăng giá nhẹ
        }
        
        for i in range(6):  # year 0 (current) to year 5
            # Base: Oil dao động nhẹ quanh base, FX trượt tự nhiên ~1%/năm
            paths['base'].append((
                base_oil + i * 1.0,                # Oil tăng nhẹ $1/năm
                base_fx * (1 + 0.01 * i)           # FX trượt 1%/năm
            ))
            # Negative: Oil sốc +$20 năm 1, neo cao; FX trượt mạnh 3-5%/năm
            if i == 0:
                paths['negative'].append((base_oil, base_fx))
            elif i == 1:
                paths['negative'].append((base_oil + 20, base_fx * 1.05))  # Sốc năm 1
            else:
                prev_oil, prev_fx = paths['negative'][-1]
                paths['negative'].append((prev_oil - 2, prev_fx * 1.02))   # Hồi phục chậm
            # Positive: Oil giảm $15 năm 1, VND tăng giá nhẹ; Long Thành năm 3+
            if i == 0:
                paths['positive'].append((base_oil, base_fx))
            elif i <= 2:
                paths['positive'].append((base_oil - 15 + i * 3, base_fx * (1 - 0.01 * i)))
            else:
                prev_oil, prev_fx = paths['positive'][-1]
                paths['positive'].append((prev_oil + 2, prev_fx * 0.99))

        # ── Tính EBITDA trajectory cho từng kịch bản ──
        ebitda_series = {'base': [], 'negative': [], 'positive': []}
        ev_series = {'base': [], 'negative': [], 'positive': []}

        for scenario in ['base', 'negative', 'positive']:
            for i in range(6):
                oil_i, fx_i = paths[scenario][i]
                
                if i == 0:
                    ebitda_series[scenario].append(ebitda_latest)
                    ev_series[scenario].append(ev_latest)
                else:
                    # EBITDA = Structural shock (3b formula) + Revenue growth assumption
                    # Revenue growth: Base 5%, Neg 2%, Pos 8% (Year 1-2) / 12% (Year 3+ Long Thanh)
                    if scenario == 'base':
                        rev_growth = 1.05
                    elif scenario == 'negative':
                        rev_growth = 1.02 if i > 1 else 0.98
                    else:
                        rev_growth = 1.12 if i >= 3 else 1.08
                    
                    # Scale revenue for growth
                    rev_projected = rev_latest * (rev_growth ** i)
                    opex_projected = rev_projected - ebitda_latest  # Base opex structure
                    fuel_proj = opex_projected * fuel_opex_ratio
                    nonfuel_proj = opex_projected * (1 - fuel_opex_ratio)
                    
                    # Apply structural sensitivity shock from oil/fx
                    fuel_shocked = fuel_proj * (oil_i / base_oil) * (fx_i / base_fx)
                    nonfuel_shocked = nonfuel_proj * (fx_i / base_fx)
                    ebitda_i = rev_projected - (fuel_shocked + nonfuel_shocked)
                    
                    # Floor EBITDA to avoid nonsensical negative infinity
                    ebitda_i = max(ebitda_i, ebitda_latest * 0.1)
                    ebitda_series[scenario].append(ebitda_i)

                    # EV: Base stable, Neg increases (debt burden), Pos decreases (deleveraging)
                    prev_ev = ev_series[scenario][-1]
                    if scenario == 'base':
                        ev_series[scenario].append(prev_ev * 1.03)
                    elif scenario == 'negative':
                        # Nợ USD tăng giá trị khi FX mất giá
                        fx_ev_impact = (fx_i / base_fx - 1) * usd_debt_ratio * 0.3
                        ev_series[scenario].append(prev_ev * (1.02 + fx_ev_impact))
                    else:
                        ev_series[scenario].append(prev_ev * 0.98)  # Giảm nợ ròng

        # ── Tính EV/EBITDA ratios ──
        ratio_base = [ev / max(eb, 1) for ev, eb in zip(ev_series['base'], ebitda_series['base'])]
        ratio_neg = [ev / max(eb, 1) for ev, eb in zip(ev_series['negative'], ebitda_series['negative'])]
        ratio_pos = [ev / max(eb, 1) for ev, eb in zip(ev_series['positive'], ebitda_series['positive'])]
        
        # ── Build scenario descriptions dựa trên dữ liệu thực ──
        neg_oil_y1 = paths['negative'][1][0]
        neg_fx_y1 = paths['negative'][1][1]
        pos_oil_y1 = paths['positive'][1][0]
        neg_ebitda_y1_chg = (ebitda_series['negative'][1] / ebitda_latest - 1) * 100
        pos_ebitda_y1_chg = (ebitda_series['positive'][1] / ebitda_latest - 1) * 100

        return {
            'years': proj_years,
            'base': [round(r, 2) for r in ratio_base],
            'negative': [round(r, 2) for r in ratio_neg],
            'positive': [round(r, 2) for r in ratio_pos],
            # Metadata cho UI
            'scenario_params': {
                'neg_oil': neg_oil_y1,
                'neg_fx': neg_fx_y1,
                'neg_ebitda_chg': round(neg_ebitda_y1_chg, 1),
                'pos_oil': pos_oil_y1,
                'pos_ebitda_chg': round(pos_ebitda_y1_chg, 1),
                'e_oil': round(e_oil * 100, 2),
                'e_fx': round(e_fx * 100, 2),
            }
        }

    def ev_to_target_price(self, ev_val, year=None):
        """
        Quy đổi từ Enterprise Value (EV) sang Giá mục tiêu mỗi cổ phiếu.
        Công thức: Equity Value = EV - Nợ thuần - Lợi ích CĐ thiểu số
                   Giá mục tiêu = Equity Value / Số lượng cổ phiếu lưu hành
        """
        fi = self.dfs.get('FINANCIAL INDEX')
        if fi is None: return 0.0
        
        years = self._get_years(fi)
        target_year = year if year in years else years[-1]
        
        # Lấy các thành phần nợ và vốn
        net_debt_row = self._get_row(fi, r'^Net Debt \(Nợ ròng\)')
        mi_row = self._get_row(fi, r'^Lợi ích CĐ thiểu số')
        shares_row = self._get_row(fi, r'^Số CP lưu hành')
        
        if net_debt_row is None or shares_row is None:
            return 0.0
            
        net_debt = float(net_debt_row[target_year])
        mi = float(mi_row[target_year]) if mi_row is not None else 0.0
        shares = float(shares_row[target_year])
        
        if shares <= 0: return 0.0
        
        equity_value = ev_val - net_debt - mi
        target_price = equity_value / shares
        
        return round(target_price, 0)

    # =========================================================================
    # What-if ROE Simulator
    # =========================================================================
    def football_field_data(self, valuation_bands_res, dcf_matrix_res, discount=0.0):
        """
        Tổng hợp dải giá trị từ các phương pháp định giá:
        1. EV/EBITDA History (1 std dev) - Đã áp dụng chiết khấu
        2. DCF Terminal Value Integration
        3. Current Enterprise Value
        """
        fi = self.dfs.get('FINANCIAL INDEX')
        
        current_ev = 0.0
        if fi is not None:
            years = self._get_years(fi)
            latest = years[-1]
            
            # Sử dụng EV đã tính toán sẵn trong Calculator (đã bao gồm Nợ ròng chuẩn và MI)
            ev_row = self._get_row(fi, r'^EV \(Enterprise Value\)')
            if ev_row is not None:
                current_ev = float(ev_row[latest])
            else:
                # Fallback nếu chưa có dòng EV
                mc_row = self._get_row(fi, r'^Vốn hóa$|Market Cap')
                nd_row = self._get_row(fi, r'^Net Debt \(Nợ ròng\)')
                mi_row = self._get_row(fi, r'^Lợi ích CĐ thiểu số')
                if mc_row is not None and nd_row is not None:
                    mc_val = float(mc_row[latest])
                    nd_val = float(nd_row[latest])
                    mi_val = float(mi_row[latest]) if mi_row is not None else 0.0
                    current_ev = mc_val + nd_val + mi_val

        # EV/EBITDA History Band (±1 sigma)
        ev_ebitda_min = 0.0
        ev_ebitda_max = 0.0
        
        is_df = self.dfs.get('INCOME STATEMENT')
        if valuation_bands_res and is_df is not None:
            # Lấy EBITDA cơ sở năm cuối (thường là 2025) từ INCOME STATEMENT
            ebitda_row = self._get_row(is_df, r'^EBITDA$')
            if ebitda_row is not None:
                ebitda_base = float(ebitda_row[years[-1]])
                # Áp dụng EBITDA x (Mean ± 1s) * (1-discount)
                ev_ebitda_min = ebitda_base * valuation_bands_res['lower_1s'] * (1 - discount)
                ev_ebitda_max = ebitda_base * valuation_bands_res['upper_1s'] * (1 - discount)
        
        dcf_min = 0.0
        dcf_max = 0.0
        if dcf_matrix_res is not None:
            mat = dcf_matrix_res.get('matrix')
            if mat is not None:
                dcf_min = np.nanmin(mat)
                dcf_max = np.nanmax(mat)
        
        years = self._get_years(fi)
        latest = years[-1]
        
        return {
            'current_ev': round(current_ev, 1),
            'ev_ebitda_min': round(ev_ebitda_min, 1),
            'ev_ebitda_max': round(ev_ebitda_max, 1),
            'dcf_min': round(dcf_min, 1),
            'dcf_max': round(dcf_max, 1),
            # Thêm Giá mục tiêu tương ứng
            'price_current': self.ev_to_target_price(current_ev, latest),
            'price_ebitda_min': self.ev_to_target_price(ev_ebitda_min, latest),
            'price_ebitda_max': self.ev_to_target_price(ev_ebitda_max, latest),
            'price_dcf_min': self.ev_to_target_price(dcf_min, latest),
            'price_dcf_max': self.ev_to_target_price(dcf_max, latest)
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
    def run_all(self, discount=0.0):
        """Chạy các phân tích và trả về dict kết quả."""
        results = {}

        # STL cho Doanh thu
        stl = self.stl_decomposition('Doanh thu thuần')
        if stl:
            results['STL_REVENUE'] = stl

        # Valuation Bands (History - Pure)
        vb = self.valuation_bands()
        if vb:
            results['VALUATION_BANDS'] = vb

        # DCF Matrix
        dcf = self.dcf_sensitivity()
        if dcf:
            results['DCF_MATRIX'] = dcf

        # Football Field Data (Apply Discount here)
        football = self.football_field_data(vb, dcf, discount=discount)
        if football:
            results['FOOTBALL_FIELD'] = football

        return results

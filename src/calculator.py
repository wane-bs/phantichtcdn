import pandas as pd
import numpy as np
try:
    from sklearn.linear_model import ElasticNetCV
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Ma trận phân cấp BS: {Parent: [Children]}
BS_HIERARCHY = {
    'TỔNG TÀI SẢN': {
        'level1': ['TÀI SẢN NGẮN HẠN', 'TÀI SẢN DÀI HẠN'],
        'TÀI SẢN NGẮN HẠN': ['Tiền và tương đương tiền', 'Giá trị thuần đầu tư ngắn hạn',
                               'Các khoản phải thu', 'Hàng tồn kho, ròng', 'Tài sản lưu động khác'],
        'TÀI SẢN DÀI HẠN': ['Phải thu dài hạn', 'Tài sản cố định', 'Tài sản dở dang dài hạn',
                              'Đầu tư dài hạn', 'Tài sản dài hạn khác'],
    },
    'TỔNG CỘNG NGUỒN VỐN': {
        'level1': ['NỢ PHẢI TRẢ', 'VỐN CHỦ SỞ HỮU'],
        'NỢ PHẢI TRẢ': ['Nợ ngắn hạn', 'Nợ dài hạn'],
        'VỐN CHỦ SỞ HỮU': ['Vốn và các quỹ'],
    }
}

class Calculator:
    def __init__(self, dfs_dict):
        """
        Input: Dictionary of DataFrames {'BALANCE SHEET': df, 'INCOME STATEMENT': df, ...}
        """
        self.dfs = dfs_dict

    def _get_row(self, df, pattern):
        """Helper to get a row by regex pattern."""
        row = df[df['Khoản mục'].str.contains(pattern, case=False, na=False, regex=True)]
        if not row.empty:
            return row.iloc[0]
        return None

    def _get_years(self, df):
        return [col for col in df.columns if col != 'Khoản mục']

    # =========================================================================
    # METHOD 1: Back-calculate missing variables (DSO, DIO, Nợ vay có lãi)
    # =========================================================================
    def calculate_missing_variables(self):
        bs_df = self.dfs.get('BALANCE SHEET')
        fi_df = self.dfs.get('FINANCIAL INDEX')
        is_df = self.dfs.get('INCOME STATEMENT')

        if bs_df is None or fi_df is None or is_df is None:
            print("Missing required sheets for calculations.")
            return

        years = self._get_years(bs_df)
        new_rows = []

        try:
            # 1. Back-calculate Interest-bearing Debt
            total_cap_row = self._get_row(bs_df, r'^TỔNG CỘNG NGUỒN VỐN$|^TỔNG TÀI SẢN$')
            debt_ratio_row = self._get_row(fi_df, r'Vốn vay.*Tổng vốn|Vốn vay/Tổng vốn')

            if total_cap_row is not None and debt_ratio_row is not None:
                debt_vals = total_cap_row[years] * debt_ratio_row[years]
                row = {'Khoản mục': 'Nợ vay có lãi (Back-calculated)'}
                row.update(debt_vals.to_dict())
                new_rows.append(row)

            # 2. DSO from turnover
            rec_turnover = self._get_row(fi_df, r'Vòng quay các khoản phải thu')
            if rec_turnover is not None:
                trn = rec_turnover[years].replace(0, np.nan)
                dso = 365 / trn
                row = {'Khoản mục': 'DSO (Số ngày phải thu)'}
                row.update(dso.fillna(0).to_dict())
                new_rows.append(row)

            # 3. DIO from turnover
            inv_turnover = self._get_row(fi_df, r'Vòng quay hàng tồn kho')
            if inv_turnover is not None:
                inv = inv_turnover[years].replace(0, np.nan)
                dio = 365 / inv
                row = {'Khoản mục': 'DIO (Số ngày tồn kho)'}
                row.update(dio.fillna(0).to_dict())
                new_rows.append(row)

            if new_rows:
                new_df = pd.DataFrame(new_rows)
                self.dfs['FINANCIAL INDEX'] = pd.concat([fi_df, new_df], ignore_index=True)

        except Exception as e:
            print(f"Error in calculate_missing_variables: {e}")

    # =========================================================================
    # METHOD 2: Vertical Analysis (Tỷ trọng Cấp 1,2 cho BS; Common-Size cho IS)
    # =========================================================================
    def vertical_analysis(self):
        bs = self.dfs.get('BALANCE SHEET')
        is_df = self.dfs.get('INCOME STATEMENT')
        if bs is None or is_df is None:
            return

        years = self._get_years(bs)

        # --- BS Vertical ---
        rows = []
        for root_name, children_map in BS_HIERARCHY.items():
            root_row = self._get_row(bs, f'^{root_name}$')
            if root_row is None:
                continue
            root_vals = root_row[years].astype(float)

            # Level 1
            for lv1_name in children_map.get('level1', []):
                lv1_row = self._get_row(bs, f'^{lv1_name}$')
                if lv1_row is None:
                    continue
                lv1_vals = lv1_row[years].astype(float)
                pct1 = np.where(root_vals != 0, lv1_vals / root_vals * 100, 0)
                row = {'Khoản mục': f'{lv1_name} (% {root_name})'}
                row.update(dict(zip(years, pct1)))
                rows.append(row)

                # Level 2
                for lv2_name in children_map.get(lv1_name, []):
                    lv2_row = self._get_row(bs, f'^{lv2_name}')
                    if lv2_row is None:
                        continue
                    lv2_vals = lv2_row[years].astype(float)
                    pct2 = np.where(lv1_vals != 0, lv2_vals / lv1_vals * 100, 0)
                    row = {'Khoản mục': f'  {lv2_name} (% {lv1_name})'}
                    row.update(dict(zip(years, pct2)))
                    rows.append(row)

        self.dfs['BS_VERTICAL'] = pd.DataFrame(rows)

        # --- IS Common-Size ---
        revenue_row = self._get_row(is_df, r'^Doanh số thuần$')
        if revenue_row is not None:
            rev_vals = revenue_row[years].astype(float)
            cs_rows = []
            for _, r in is_df.iterrows():
                item = r['Khoản mục']
                vals = r[years].astype(float)
                pct = np.where(rev_vals != 0, vals / rev_vals * 100, 0)
                row = {'Khoản mục': item}
                row.update(dict(zip(years, pct)))
                cs_rows.append(row)
            self.dfs['IS_VERTICAL'] = pd.DataFrame(cs_rows)

    # =========================================================================
    # METHOD 3: Horizontal Analysis (YoY% cho BS, IS, CF)
    # =========================================================================
    def horizontal_analysis(self):
        for key, suffix in [('BALANCE SHEET', 'BS_YOY'),
                            ('INCOME STATEMENT', 'IS_YOY'),
                            ('CASH FLOW STATEMENT', 'CF_YOY')]:
            df = self.dfs.get(key)
            if df is None:
                continue

            years = self._get_years(df)
            if len(years) < 2:
                continue

            yoy_rows = []
            for _, r in df.iterrows():
                item = r['Khoản mục']
                row = {'Khoản mục': item}
                for i in range(1, len(years)):
                    prev_val = float(r[years[i - 1]])
                    curr_val = float(r[years[i]])
                    if abs(prev_val) > 0:
                        yoy = (curr_val - prev_val) / abs(prev_val) * 100
                    else:
                        yoy = 0.0
                    row[f'{years[i]} YoY%'] = round(yoy, 2)
                yoy_rows.append(row)

            self.dfs[suffix] = pd.DataFrame(yoy_rows)

    # =========================================================================
    # METHOD 4: DPO & Cash Conversion Cycle
    # =========================================================================
    def calculate_dpo_ccc(self):
        fi_df = self.dfs.get('FINANCIAL INDEX')
        if fi_df is None:
            return

        years = self._get_years(fi_df)
        new_rows = []

        # DPO
        pay_turnover = self._get_row(fi_df, r'Vòng quay các khoản phải trả')
        if pay_turnover is not None:
            trn = pay_turnover[years].astype(float).replace(0, np.nan)
            dpo = 365 / trn
            row = {'Khoản mục': 'DPO (Số ngày phải trả)'}
            row.update(dpo.fillna(0).to_dict())
            new_rows.append(row)

            # CCC = DIO + DSO - DPO
            dso_row = self._get_row(fi_df, r'^DSO')
            dio_row = self._get_row(fi_df, r'^DIO')
            if dso_row is not None and dio_row is not None:
                ccc = dso_row[years].astype(float) + dio_row[years].astype(float) - dpo.fillna(0)
                row = {'Khoản mục': 'CCC (Chu kỳ tiền tính toán)'}
                row.update(ccc.to_dict())
                new_rows.append(row)

        if new_rows:
            new_df = pd.DataFrame(new_rows)
            self.dfs['FINANCIAL INDEX'] = pd.concat([fi_df, new_df], ignore_index=True)

    # =========================================================================
    # METHOD 5: Net Debt / EBITDA
    # =========================================================================
    def calculate_net_debt_ebitda(self):
        fi_df = self.dfs.get('FINANCIAL INDEX')
        bs_df = self.dfs.get('BALANCE SHEET')
        is_df = self.dfs.get('INCOME STATEMENT')
        if fi_df is None or bs_df is None or is_df is None:
            return

        years = self._get_years(bs_df)
        new_rows = []

        debt_row = self._get_row(fi_df, r'^Nợ vay có lãi')
        cash_row = self._get_row(bs_df, r'^Tiền và tương đương tiền')
        ebitda_row = self._get_row(is_df, r'^EBITDA$')

        if debt_row is not None and cash_row is not None and ebitda_row is not None:
            net_debt = debt_row[years].astype(float) - cash_row[years].astype(float)
            row_nd = {'Khoản mục': 'Net Debt (Nợ ròng)'}
            row_nd.update(net_debt.to_dict())
            new_rows.append(row_nd)

            ebitda_vals = ebitda_row[years].astype(float).replace(0, np.nan)
            ratio = net_debt / ebitda_vals
            row_r = {'Khoản mục': 'Net Debt / EBITDA'}
            row_r.update(ratio.fillna(0).to_dict())
            new_rows.append(row_r)

        if new_rows:
            new_df = pd.DataFrame(new_rows)
            self.dfs['FINANCIAL INDEX'] = pd.concat([fi_df, new_df], ignore_index=True)

    # =========================================================================
    # METHOD 6a: Cash Inflow / Outflow Analysis (VAS 24)
    # =========================================================================
    def calculate_cash_inflow_outflow(self):
        """Phân loại dòng tiền thu/chi từ IS + ΔBS + CF theo VAS 24."""
        is_df = self.dfs.get('INCOME STATEMENT')
        bs_df = self.dfs.get('BALANCE SHEET')
        cf_df = self.dfs.get('CASH FLOW STATEMENT')
        if is_df is None or bs_df is None or cf_df is None:
            return

        years = self._get_years(bs_df)
        inflow_rows = []
        outflow_rows = []

        def _safe_vals(row, yrs):
            return row[yrs].astype(float) if row is not None else pd.Series([0.0]*len(yrs), index=yrs)

        # --- INFLOW (Thu) ---
        # IS sources
        rev = _safe_vals(self._get_row(is_df, r'^Doanh số thuần$'), years)
        fin_income = _safe_vals(self._get_row(is_df, r'^Thu nhập tài chính$'), years)
        other_income_row = self._get_row(is_df, r'^Thu nhập khác, ròng$')
        other_income = _safe_vals(other_income_row, years).clip(lower=0)

        inflow_rows.append({'Khoản mục': '[Thu] Doanh thu thuần (IS)', **rev.to_dict()})
        inflow_rows.append({'Khoản mục': '[Thu] Thu nhập tài chính (IS)', **fin_income.to_dict()})
        inflow_rows.append({'Khoản mục': '[Thu] Thu nhập khác ròng (IS, >0)', **other_income.to_dict()})

        # CF investment inflows
        cf_asset_sale = _safe_vals(self._get_row(cf_df, r'^Tiền thu được từ thanh lý'), years).clip(lower=0)
        cf_loan_recv = _safe_vals(self._get_row(cf_df, r'^Tiền thu từ cho vay'), years).clip(lower=0)
        cf_div_recv = _safe_vals(self._get_row(cf_df, r'^Cổ tức và tiền lãi nhận'), years).clip(lower=0)
        cf_invest_sell = _safe_vals(self._get_row(cf_df, r'^Tiền thu từ việc bán các khoản đầu tư'), years).clip(lower=0)

        inflow_rows.append({'Khoản mục': '[Thu] Thanh lý TSCĐ (CF)', **cf_asset_sale.to_dict()})
        inflow_rows.append({'Khoản mục': '[Thu] Thu hồi cho vay (CF)', **cf_loan_recv.to_dict()})
        inflow_rows.append({'Khoản mục': '[Thu] Cổ tức/lãi nhận (CF)', **cf_div_recv.to_dict()})
        inflow_rows.append({'Khoản mục': '[Thu] Bán khoản đầu tư (CF)', **cf_invest_sell.to_dict()})

        # CF financing inflows
        cf_equity = _safe_vals(self._get_row(cf_df, r'^Tiền thu từ phát hành cổ phiếu'), years).clip(lower=0)
        cf_borrow = _safe_vals(self._get_row(cf_df, r'^Tiền thu được các khoản đi vay'), years).clip(lower=0)

        inflow_rows.append({'Khoản mục': '[Thu] Phát hành CP/vốn góp (CF)', **cf_equity.to_dict()})
        inflow_rows.append({'Khoản mục': '[Thu] Tiền vay mới (CF)', **cf_borrow.to_dict()})

        total_inflow = rev + fin_income + other_income + cf_asset_sale + cf_loan_recv + cf_div_recv + cf_invest_sell + cf_equity + cf_borrow

        # --- OUTFLOW (Chi) ---
        cogs = _safe_vals(self._get_row(is_df, r'^Giá vốn hàng bán$'), years).abs()
        fin_cost = _safe_vals(self._get_row(is_df, r'^Chi phí tài chính$'), years).abs()
        sell_exp = _safe_vals(self._get_row(is_df, r'^Chi phí bán hàng$'), years).abs()
        admin_exp = _safe_vals(self._get_row(is_df, r'^Chi phí quản lý'), years).abs()
        tax_exp = _safe_vals(self._get_row(is_df, r'^Chi phí thuế thu nhập'), years).abs()
        other_cost_row = self._get_row(is_df, r'^Thu nhập khác, ròng$')
        other_cost = (_safe_vals(other_cost_row, years).clip(upper=0)).abs()

        outflow_rows.append({'Khoản mục': '[Chi] Giá vốn hàng bán (IS)', **cogs.to_dict()})
        outflow_rows.append({'Khoản mục': '[Chi] Chi phí tài chính (IS)', **fin_cost.to_dict()})
        outflow_rows.append({'Khoản mục': '[Chi] Chi phí bán hàng (IS)', **sell_exp.to_dict()})
        outflow_rows.append({'Khoản mục': '[Chi] Chi phí QLDN (IS)', **admin_exp.to_dict()})
        outflow_rows.append({'Khoản mục': '[Chi] Thuế TNDN (IS)', **tax_exp.to_dict()})
        outflow_rows.append({'Khoản mục': '[Chi] Chi phí khác ròng (IS, <0)', **other_cost.to_dict()})

        # CF investment outflows
        cf_capex = _safe_vals(self._get_row(cf_df, r'^Tiền mua tài sản cố định'), years).abs()
        cf_loan_out = _safe_vals(self._get_row(cf_df, r'^Tiền cho vay hoặc mua công cụ nợ'), years).abs()
        cf_invest_buy = _safe_vals(self._get_row(cf_df, r'^Đầu tư vào các doanh nghiệp'), years).abs()

        outflow_rows.append({'Khoản mục': '[Chi] Mua TSCĐ (CF)', **cf_capex.to_dict()})
        outflow_rows.append({'Khoản mục': '[Chi] Cho vay/mua công cụ nợ (CF)', **cf_loan_out.to_dict()})
        outflow_rows.append({'Khoản mục': '[Chi] Đầu tư DN khác (CF)', **cf_invest_buy.to_dict()})

        # CF financing outflows
        cf_repay = _safe_vals(self._get_row(cf_df, r'^Tiển trả các khoản đi vay$'), years).abs()
        cf_lease = _safe_vals(self._get_row(cf_df, r'^Tiền thanh toán vốn gốc'), years).abs()
        cf_div_paid = _safe_vals(self._get_row(cf_df, r'^Cổ tức đã trả$'), years).abs()

        outflow_rows.append({'Khoản mục': '[Chi] Trả nợ vay (CF)', **cf_repay.to_dict()})
        outflow_rows.append({'Khoản mục': '[Chi] Trả vốn gốc thuê TC (CF)', **cf_lease.to_dict()})
        outflow_rows.append({'Khoản mục': '[Chi] Cổ tức đã trả (CF)', **cf_div_paid.to_dict()})

        total_outflow = cogs + fin_cost + sell_exp + admin_exp + tax_exp + other_cost + cf_capex + cf_loan_out + cf_invest_buy + cf_repay + cf_lease + cf_div_paid
        net_flow = total_inflow - total_outflow

        # Build summary DataFrame
        summary_rows = inflow_rows + [
            {'Khoản mục': '═══ TỔNG THỰC THU', **total_inflow.to_dict()},
        ] + outflow_rows + [
            {'Khoản mục': '═══ TỔNG THỰC CHI', **total_outflow.to_dict()},
            {'Khoản mục': '═══ DÒNG TIỀN RÒNG (Thu − Chi)', **net_flow.to_dict()},
        ]
        self.dfs['CASH_INOUT'] = pd.DataFrame(summary_rows)

    # =========================================================================
    # METHOD 6b: Anomaly Scores (Beneish, Altman, Sloan)
    # =========================================================================
    def calculate_anomaly_scores(self):
        """Tính Beneish M-Score, Altman Z''-Score, Sloan Accruals."""
        is_df = self.dfs.get('INCOME STATEMENT')
        bs_df = self.dfs.get('BALANCE SHEET')
        cf_df = self.dfs.get('CASH FLOW STATEMENT')
        if is_df is None or bs_df is None or cf_df is None:
            return

        years = self._get_years(bs_df)
        if len(years) < 2:
            return

        def _v(row, yr):
            return float(row[yr]) if row is not None else 0.0

        # Fetch all needed rows
        rev_row = self._get_row(is_df, r'^Doanh số thuần$')
        cogs_row = self._get_row(is_df, r'^Giá vốn hàng bán$')
        recv_row = self._get_row(bs_df, r'^Các khoản phải thu$')
        ta_row = self._get_row(bs_df, r'^TỔNG TÀI SẢN$')
        ca_row = self._get_row(bs_df, r'^TÀI SẢN NGẮN HẠN$')
        ppe_row = self._get_row(bs_df, r'^Tài sản cố định$')
        depr_row = self._get_row(cf_df, r'^Khấu hao TSCĐ$')
        sell_row = self._get_row(is_df, r'^Chi phí bán hàng$')
        admin_row = self._get_row(is_df, r'^Chi phí quản lý')
        ni_row = self._get_row(is_df, r'^Lãi/\(lỗ\) thuần sau thuế$')
        ocf_row = self._get_row(cf_df, r'^Lưu chuyển tiền thuần từ các hoạt động sản xuất')
        npt_row = self._get_row(bs_df, r'^NỢ PHẢI TRẢ$')
        nnh_row = self._get_row(bs_df, r'^Nợ ngắn hạn$')
        ndh_row = self._get_row(bs_df, r'^Nợ dài hạn$')
        vcsh_row = self._get_row(bs_df, r'^VỐN CHỦ SỞ HỮU$')
        ebit_row = self._get_row(is_df, r'^EBIT$')
        icf_row = self._get_row(cf_df, r'^Lưu chuyển tiền tệ ròng từ hoạt động đầu tư$')

        score_rows = []
        beneish_components = {k: [] for k in ['DSRI','GMI','AQI','SGI','DEPI','SGAI','TATA','LVGI','M-Score']}
        altman_components = {k: [] for k in ['X1','X2','X3','X4','Z-Score']}
        sloan_vals = []
        impact_years = years[1:]  # Beneish cần t-1

        for i in range(1, len(years)):
            yp, yc = years[i-1], years[i]

            # --- BENEISH M-SCORE ---
            rev_c = _v(rev_row, yc); rev_p = _v(rev_row, yp)
            recv_c = _v(recv_row, yc); recv_p = _v(recv_row, yp)
            cogs_c = abs(_v(cogs_row, yc)); cogs_p = abs(_v(cogs_row, yp))
            ta_c = _v(ta_row, yc); ta_p = _v(ta_row, yp)
            ca_c = _v(ca_row, yc); ca_p = _v(ca_row, yp)
            ppe_c = _v(ppe_row, yc); ppe_p = _v(ppe_row, yp)
            depr_c = abs(_v(depr_row, yc)); depr_p = abs(_v(depr_row, yp))
            sga_c = abs(_v(sell_row, yc)) + abs(_v(admin_row, yc))
            sga_p = abs(_v(sell_row, yp)) + abs(_v(admin_row, yp))
            ni_c = _v(ni_row, yc)
            ocf_c = _v(ocf_row, yc)
            nnh_c = _v(nnh_row, yc); nnh_p = _v(nnh_row, yp)
            ndh_c = _v(ndh_row, yc); ndh_p = _v(ndh_row, yp)

            # DSRI
            dsri = ((recv_c / rev_c) / (recv_p / rev_p)) if rev_c != 0 and rev_p != 0 and recv_p != 0 else 1.0
            # GMI
            gm_p = (rev_p - cogs_p) / rev_p if rev_p != 0 else 0
            gm_c = (rev_c - cogs_c) / rev_c if rev_c != 0 else 0
            gmi = gm_p / gm_c if gm_c != 0 else 1.0
            # AQI
            aq_c = 1 - (ca_c + ppe_c) / ta_c if ta_c != 0 else 0
            aq_p = 1 - (ca_p + ppe_p) / ta_p if ta_p != 0 else 0
            aqi = aq_c / aq_p if aq_p != 0 else 1.0
            # SGI
            sgi = rev_c / rev_p if rev_p != 0 else 1.0
            # DEPI
            dep_p = depr_p / (ppe_p + depr_p) if (ppe_p + depr_p) != 0 else 0
            dep_c = depr_c / (ppe_c + depr_c) if (ppe_c + depr_c) != 0 else 0
            depi = dep_p / dep_c if dep_c != 0 else 1.0
            # SGAI
            sga_ratio_c = sga_c / rev_c if rev_c != 0 else 0
            sga_ratio_p = sga_p / rev_p if rev_p != 0 else 0
            sgai = sga_ratio_c / sga_ratio_p if sga_ratio_p != 0 else 1.0
            # TATA
            tata = (ni_c - ocf_c) / ta_c if ta_c != 0 else 0
            # LVGI
            lev_c = (nnh_c + ndh_c) / ta_c if ta_c != 0 else 0
            lev_p = (nnh_p + ndh_p) / ta_p if ta_p != 0 else 0
            lvgi = lev_c / lev_p if lev_p != 0 else 1.0

            m_score = (-4.84 + 0.92*dsri + 0.528*gmi + 0.404*aqi + 0.892*sgi
                       + 0.115*depi - 0.172*sgai + 4.679*tata - 0.327*lvgi)

            for k, v in [('DSRI',dsri),('GMI',gmi),('AQI',aqi),('SGI',sgi),
                         ('DEPI',depi),('SGAI',sgai),('TATA',tata),('LVGI',lvgi),('M-Score',m_score)]:
                beneish_components[k].append(round(v, 4))

            # --- ALTMAN Z''-SCORE (EM, non-manufacturing) ---
            wc = ca_c - nnh_c
            x1 = wc / ta_c if ta_c != 0 else 0
            x2 = _v(vcsh_row, yc) / ta_c if ta_c != 0 else 0  # VCSH proxy for RE/TA
            x3 = _v(ebit_row, yc) / ta_c if ta_c != 0 else 0
            npt_c = _v(npt_row, yc)
            x4 = _v(vcsh_row, yc) / npt_c if npt_c != 0 else 0

            z_score = 3.25 + 6.56*x1 + 3.26*x2 + 6.72*x3 + 1.05*x4

            for k, v in [('X1',x1),('X2',x2),('X3',x3),('X4',x4),('Z-Score',z_score)]:
                altman_components[k].append(round(v, 4))

            # --- SLOAN ACCRUALS ---
            icf_c = _v(icf_row, yc)
            sloan = (ni_c - ocf_c - icf_c) / ta_c if ta_c != 0 else 0
            sloan_vals.append(round(sloan * 100, 2))  # percent

        # Build output DataFrame
        anomaly_rows = []
        anomaly_rows.append({'Khoản mục': '── BENEISH M-SCORE ──', **{y: '' for y in impact_years}})
        for k in ['DSRI','GMI','AQI','SGI','DEPI','SGAI','TATA','LVGI','M-Score']:
            anomaly_rows.append({'Khoản mục': f'  {k}', **dict(zip(impact_years, beneish_components[k]))})
        anomaly_rows.append({'Khoản mục': '  Ngưỡng: M > −2.22 → Nghi ngờ', **{y: '' for y in impact_years}})

        anomaly_rows.append({'Khoản mục': '── ALTMAN Z\'\'-SCORE ──', **{y: '' for y in impact_years}})
        for k in ['X1','X2','X3','X4','Z-Score']:
            anomaly_rows.append({'Khoản mục': f'  {k}', **dict(zip(impact_years, altman_components[k]))})
        anomaly_rows.append({'Khoản mục': '  Ngưỡng: Z<1.1 Nguy hiểm; 1.1-2.6 Xám; >2.6 An toàn', **{y: '' for y in impact_years}})

        anomaly_rows.append({'Khoản mục': '── SLOAN ACCRUALS (%) ──', **{y: '' for y in impact_years}})
        anomaly_rows.append({'Khoản mục': '  Sloan Ratio (%)', **dict(zip(impact_years, sloan_vals))})
        anomaly_rows.append({'Khoản mục': '  Ngưỡng: |Sloan|>10% Cảnh báo; >25% Nghiêm trọng', **{y: '' for y in impact_years}})

        self.dfs['ANOMALY_SCORES'] = pd.DataFrame(anomaly_rows)

        # Store numeric values separately for charting
        self.dfs['ANOMALY_NUMERIC'] = {
            'years': impact_years,
            'beneish': beneish_components['M-Score'],
            'altman': altman_components['Z-Score'],
            'sloan': sloan_vals,
            'beneish_components': beneish_components,
            'altman_components': altman_components,
        }

    # =========================================================================
    # METHOD 7: Dupont 3 bước (ROE) + ROA 4 nhân tố + ROIC 2 nhân tố
    # =========================================================================
    def dupont_analysis(self):
        is_df = self.dfs.get('INCOME STATEMENT')
        bs_df = self.dfs.get('BALANCE SHEET')
        fi_df = self.dfs.get('FINANCIAL INDEX')
        if is_df is None or bs_df is None:
            return

        years = self._get_years(bs_df)
        
        ni_row = self._get_row(is_df, r'^Lãi/\(lỗ\) thuần sau thuế$')
        rev_row = self._get_row(is_df, r'^Doanh số thuần$')
        ta_row = self._get_row(bs_df, r'^TỔNG TÀI SẢN$')
        eq_row = self._get_row(bs_df, r'^VỐN CHỦ SỞ HỮU$')
        ebit_row = self._get_row(is_df, r'^EBIT$')
        ebt_row = self._get_row(is_df, r'^Lãi/\(lỗ\) ròng trước thuế$')
        tax_row = self._get_row(is_df, r'^Chi phí thuế thu nhập')

        if any(r is None for r in [ni_row, rev_row, ta_row, eq_row]):
            return

        ni = ni_row[years].astype(float)
        rev = rev_row[years].astype(float).replace(0, np.nan)
        ta = ta_row[years].astype(float).replace(0, np.nan)
        eq = eq_row[years].astype(float).replace(0, np.nan)

        # === ROE DuPont (3 nhân tố) ===
        ros = (ni / rev * 100).fillna(0)
        at = (rev / ta).fillna(0)
        leverage = (ta / eq).fillna(0)
        roe_dupont = (ros / 100 * at * leverage * 100).fillna(0)

        dupont_rows = [
            {'Khoản mục': 'ROS (Biên LN ròng %)', **ros.to_dict()},
            {'Khoản mục': 'Asset Turnover (Vòng quay TS)', **at.to_dict()},
            {'Khoản mục': 'Financial Leverage (Đòn bẩy TC)', **leverage.to_dict()},
            {'Khoản mục': 'ROE (Dupont) %', **roe_dupont.to_dict()},
        ]
        self.dfs['DUPONT'] = pd.DataFrame(dupont_rows)

        # === ROA DuPont (4 nhân tố): Tax Burden × Interest Burden × EBIT Margin × AT ===
        if ebit_row is not None and ebt_row is not None:
            ebit = ebit_row[years].astype(float).replace(0, np.nan)
            ebt = ebt_row[years].astype(float).replace(0, np.nan)

            tax_burden = (ni / ebt).fillna(0)           # NI / EBT
            interest_burden = (ebt / ebit).fillna(0)     # EBT / EBIT
            ebit_margin = (ebit / rev * 100).fillna(0)   # EBIT / Revenue (%)
            # ROA_dupont = tax_burden × interest_burden × ebit_margin/100 × at × 100
            roa_dupont = (tax_burden * interest_burden * ebit_margin / 100 * at * 100).fillna(0)

            roa_rows = [
                {'Khoản mục': 'Tax Burden (NI/EBT)', **tax_burden.to_dict()},
                {'Khoản mục': 'Interest Burden (EBT/EBIT)', **interest_burden.to_dict()},
                {'Khoản mục': 'EBIT Margin (%)', **ebit_margin.to_dict()},
                {'Khoản mục': 'Asset Turnover (Vòng quay TS)', **at.to_dict()},
                {'Khoản mục': 'ROA (Dupont) %', **roa_dupont.to_dict()},
            ]
            self.dfs['DUPONT_ROA'] = pd.DataFrame(roa_rows)

        # === ROIC DuPont (2 nhân tố): NOPAT Margin × IC Turnover ===
        if ebit_row is not None and ebt_row is not None:
            # Tax Rate = Tax Expense / EBT
            tax_exp = tax_row[years].astype(float).abs() if tax_row is not None else pd.Series([0.0]*len(years), index=years)
            tax_rate = (tax_exp / ebt.abs()).fillna(0).clip(0, 1)
            nopat = (ebit * (1 - tax_rate)).fillna(0)

            # Invested Capital = VCSH + Nợ vay có lãi (back-calculated)
            debt_row = self._get_row(self.dfs.get('FINANCIAL INDEX', pd.DataFrame()), r'^Nợ vay có lãi')
            if debt_row is not None:
                ib_debt = debt_row[years].astype(float)
            else:
                ib_debt = pd.Series([0.0]*len(years), index=years)
            ic = eq.fillna(0) + ib_debt
            ic = ic.replace(0, np.nan)

            nopat_margin = (nopat / rev * 100).fillna(0)
            ic_turnover = (rev / ic).fillna(0)
            roic_dupont = (nopat_margin / 100 * ic_turnover * 100).fillna(0)

            roic_rows = [
                {'Khoản mục': 'NOPAT Margin (%)', **nopat_margin.to_dict()},
                {'Khoản mục': 'IC Turnover (Vòng quay IC)', **ic_turnover.to_dict()},
                {'Khoản mục': 'ROIC (Dupont) %', **roic_dupont.to_dict()},
            ]
            self.dfs['DUPONT_ROIC'] = pd.DataFrame(roic_rows)

    # =========================================================================
    # METHOD 8: Dupont Factor Impact — OLS Best-fit only (Shapley removed)
    #           Applies to ROE (3 factors), ROA (4 factors), ROIC (2 factors)
    # =========================================================================
    def _generic_factor_impact(self, dupont_df, factors, metric_name):
        """Generic OLS best-fit chain substitution for any DuPont decomposition.
        
        factors: list of (row_pattern, factor_label, is_pct) tuples
        Returns (impact_df, betas_dict) or (None, None)
        """
        from itertools import permutations as _permutations

        if dupont_df is None:
            return None, None

        dp_years = self._get_years(dupont_df)
        if len(dp_years) < 2:
            return None, None

        # Get factor rows and metric row
        fac_data = {}
        for pattern, label, is_pct in factors:
            row = dupont_df[dupont_df['Khoản mục'].str.contains(pattern, regex=True)]
            if row.empty:
                return None, None
            vals = row.iloc[0][dp_years].astype(float)
            fac_data[label] = vals / 100 if is_pct else vals

        # Get the metric (ROE/ROA/ROIC)
        metric_row = dupont_df[dupont_df['Khoản mục'].str.contains(metric_name, regex=True)]
        if metric_row.empty:
            return None, None
        metric_vals = metric_row.iloc[0][dp_years].astype(float) / 100

        impact_years = dp_years[1:]
        fac_labels = [f[1] for f in factors]
        ALL_PERMS = list(_permutations(fac_labels))

        def _chain_sub(v0, v1, order):
            cur = dict(v0)
            effects = {}
            for fac in order:
                prod_old = 1.0
                for k in fac_labels:
                    prod_old *= cur[k]
                cur[fac] = v1[fac]
                prod_new = 1.0
                for k in fac_labels:
                    prod_new *= cur[k]
                effects[fac] = prod_new - prod_old
            return effects

        perm_effects = {p: [] for p in ALL_PERMS}
        delta_actual = []
        deltas_by_fac = {f: [] for f in fac_labels}

        for i in range(1, len(dp_years)):
            yp, yc = dp_years[i-1], dp_years[i]
            v0 = {f: fac_data[f][yp] for f in fac_labels}
            v1 = {f: fac_data[f][yc] for f in fac_labels}
            for perm in ALL_PERMS:
                perm_effects[perm].append(_chain_sub(v0, v1, perm))
            delta_actual.append((metric_vals[yc] - metric_vals[yp]) * 100)
            for f in fac_labels:
                deltas_by_fac[f].append(fac_data[f][yc] - fac_data[f][yp])

        n_t = len(impact_years)

        # OLS β
        X_ols = np.column_stack([deltas_by_fac[f] for f in fac_labels])
        y_ols = np.array(delta_actual)
        try:
            ols_betas, _, _, _ = np.linalg.lstsq(X_ols, y_ols, rcond=None)
        except Exception:
            ols_betas = np.ones(len(fac_labels))

        # Best-fit permutation
        best_perm = ALL_PERMS[0]
        best_score = np.inf
        for perm in ALL_PERMS:
            eff_betas = []
            for idx, fac in enumerate(fac_labels):
                eff = np.array([perm_effects[perm][t][fac] * 100 for t in range(n_t)])
                d = np.array(deltas_by_fac[fac])
                var_d = np.var(d)
                eff_beta = float(np.cov(eff, d)[0, 1] / var_d) if var_d > 1e-12 else 0.0
                eff_betas.append(eff_beta)
            score = float(np.linalg.norm(np.array(eff_betas) - ols_betas))
            if score < best_score:
                best_score = score
                best_perm = perm

        best_label = ' → '.join(best_perm)
        ols_parts = ' | '.join([f'{f}={ols_betas[i]:.3f}' for i, f in enumerate(fac_labels)])
        ols_str = f"OLS β: {ols_parts} | Best-fit: {best_label}"

        # Build impact rows - Best-fit only (no Shapley)
        bf = {fac: [perm_effects[best_perm][t][fac] * 100 for t in range(n_t)]
              for fac in fac_labels}

        impact_rows = []
        for fac in fac_labels:
            impact_rows.append({
                'Khoản mục': f'[Best: {best_label}] {fac} (%pts)',
                **dict(zip(impact_years, bf[fac]))
            })
        impact_rows.append({
            'Khoản mục': f'Δ{metric_name.replace("(Dupont)", "").strip()} Thực tế (%)',
            **dict(zip(impact_years, delta_actual))
        })
        impact_rows.append({
            'Khoản mục': ols_str,
            **dict(zip(impact_years, [0.0] * n_t))
        })

        betas = {'best_perm': best_label}
        for i, f in enumerate(fac_labels):
            betas[f'ols_{f}'] = round(float(ols_betas[i]), 4)

        return pd.DataFrame(impact_rows), betas

    def dupont_factor_impact(self):
        """Phân rã ảnh hưởng nhân tố cho ROE, ROA, ROIC — chỉ Best-fit OLS."""

        # ROE: 3 nhân tố
        roe_impact, roe_betas = self._generic_factor_impact(
            self.dfs.get('DUPONT'),
            [(r'^ROS', 'ROS', True), (r'^Asset Turnover', 'AT', False),
             (r'^Financial Leverage', 'Lev', False)],
            r'ROE'
        )
        if roe_impact is not None:
            self.dfs['DUPONT_IMPACT'] = roe_impact
            self.dfs['DUPONT_BETAS'] = roe_betas

        # ROA: 4 nhân tố
        roa_impact, roa_betas = self._generic_factor_impact(
            self.dfs.get('DUPONT_ROA'),
            [(r'^Tax Burden', 'TaxB', False), (r'^Interest Burden', 'IntB', False),
             (r'^EBIT Margin', 'EBIT_M', True), (r'^Asset Turnover', 'AT', False)],
            r'ROA'
        )
        if roa_impact is not None:
            self.dfs['DUPONT_IMPACT_ROA'] = roa_impact
            self.dfs['DUPONT_BETAS_ROA'] = roa_betas

        # ROIC: 2 nhân tố
        roic_impact, roic_betas = self._generic_factor_impact(
            self.dfs.get('DUPONT_ROIC'),
            [(r'^NOPAT Margin', 'NOPAT_M', True), (r'^IC Turnover', 'IC_T', False)],
            r'ROIC'
        )
        if roic_impact is not None:
            self.dfs['DUPONT_IMPACT_ROIC'] = roic_impact
            self.dfs['DUPONT_BETAS_ROIC'] = roic_betas

    # =========================================================================
    # RUN ALL
    # =========================================================================
    def run_all(self):
        """
        Output: Dictionary containing all processed DataFrames
        """
        self.calculate_missing_variables()
        self.vertical_analysis()
        self.horizontal_analysis()
        self.calculate_dpo_ccc()
        self.calculate_net_debt_ebitda()
        self.calculate_cash_inflow_outflow()
        self.calculate_anomaly_scores()
        self.dupont_analysis()
        self.dupont_factor_impact()
        return self.dfs

if __name__ == "__main__":
    from data_processor import DataProcessor
    processor = DataProcessor("data/hvn data.xlsx")
    dfs = processor.load_and_normalize()
    calc = Calculator(dfs)
    result = calc.run_all()
    
    print("=== Available DataFrames ===")
    for k in result:
        print(f"  {k}: {len(result[k])} rows")
    
    print("\n=== BS Vertical (preview) ===")
    if 'BS_VERTICAL' in result:
        print(result['BS_VERTICAL'].head(8).to_string())
    
    print("\n=== IS YoY (preview) ===")
    if 'IS_YOY' in result:
        print(result['IS_YOY'].head(5).to_string())
    
    print("\n=== DUPONT ===")
    if 'DUPONT' in result:
        print(result['DUPONT'].to_string())

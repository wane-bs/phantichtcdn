import pandas as pd
import numpy as np

def _get(df, pattern, years):
    row = df[df.iloc[:, 0].str.contains(pattern, case=False, na=False, regex=True)]
    if not row.empty:
        available_years = [y for y in years if y in df.columns]
        res = pd.Series(0.0, index=years)
        if available_years:
            res[available_years] = pd.to_numeric(row.iloc[0][available_years], errors='coerce').fillna(0.0)
        return res
    return pd.Series(0.0, index=years)

def _get_sheet(xls, options):
    for opt in options:
        if opt in xls.sheet_names:
            return pd.read_excel(xls, sheet_name=opt)
    raise ValueError(f"None of the sheets {options} found in Excel file. Available: {xls.sheet_names}")

def fix_dataset(raw_file='data/hvn.xlsx', wrong_file='data/hvn_data.xlsx', output_file='data/hvn_fixed.xlsx'):
    raw_xls = pd.ExcelFile(raw_file)
    bs = _get_sheet(raw_xls, ['BALANCE SHEEET', 'BALANCE SHEET', 'bs'])
    cf = _get_sheet(raw_xls, ['CASH FLOW STATEMENT', 'cf'])
    is_df = _get_sheet(raw_xls, ['INCOME STATEMENT', 'is'])
    
    wrong_xls = pd.ExcelFile(wrong_file)
    wrong_fi = _get_sheet(wrong_xls, ['FINANCIAL INDEX', 'fi'])
    
    # Identify year columns (numeric headers)
    years = [c for c in bs.columns if str(c).strip().isdigit() or (isinstance(c, (int, float)) and not np.isnan(c))]
    print(f"Detected years: {years}")
    
    fi_rows = []
    
    # 1. Market Data
    shares = _get(wrong_fi, '^Số CP lưu hành', years)
    market_cap = _get(wrong_fi, '^Vốn hóa', years)
    fi_rows.append({'Chỉ số': 'Số CP lưu hành', **shares.to_dict()})
    fi_rows.append({'Chỉ số': 'Vốn hóa', **market_cap.to_dict()})
    
    # 2. Extract Data for calculations
    ni = _get(is_df, '^Lãi/\\(lỗ\\) thuần sau thuế', years)
    revenue = _get(is_df, '^Doanh số thuần', years)
    cogs = _get(is_df, '^Giá vốn hàng bán', years).abs()
    ta = _get(bs, '^TỔNG TÀI SẢN', years)
    eq = _get(bs, '^VỐN CHỦ SỞ HỮU', years)
    ca = _get(bs, '^TÀI SẢN NGẮN HẠN', years)
    cl = _get(bs, '^Nợ ngắn hạn', years)
    inv = _get(bs, '^Hàng tồn kho', years)
    cash = _get(bs, '^Tiền và tương đương tiền', years)
    tl = _get(bs, '^NỢ PHẢI TRẢ', years)
    ebit = _get(is_df, '^EBIT$', years)
    ebitda = _get(is_df, '^EBITDA$', years)
    if ebitda.sum() == 0:  # Calculate EBITDA if not explicitly named
        ebt = _get(is_df, 'Lãi/\\(lỗ\\) ròng trước thuế', years)
        int_exp = _get(is_df, 'Chi phí lãi vay', years).abs()
        ebit_calc = ebt + int_exp
        depr = _get(cf, 'Khấu hao TSCĐ', years).abs()
        ebitda = ebit_calc + depr
        ebit = ebit_calc
        
    ocf = _get(cf, '^Lưu chuyển tiền thuần từ các hoạt động sản xuất', years)
    int_exp = _get(is_df, 'Chi phí lãi vay', years).abs()
    
    recv = _get(bs, '^Các khoản phải thu корот hạn$|^Các khoản phải thu', years)
    pay = _get(bs, 'Phải trả người bán ngắn hạn', years)
    
    st_debt = _get(bs, 'Vay và nợ thuê.*?ngắn hạn', years)
    lt_debt = _get(bs, 'Vay và nợ thuê.*?dài hạn', years)
    total_debt = st_debt + lt_debt
    
    fi_rows.append({'Chỉ số': 'Nợ vay có lãi', **total_debt.to_dict()})
    
    # 3. Margins & Profitability
    roe = (ni / eq * 100).replace([np.inf, -np.inf], np.nan).fillna(0)
    roa = (ni / ta * 100).replace([np.inf, -np.inf], np.nan).fillna(0)
    
    tax_exp = _get(is_df, 'Chi phí thuế thu nhập', years).abs()
    ebt = _get(is_df, 'Lãi/\\(lỗ\\) ròng trước thuế', years)
    tax_rate = (tax_exp / ebt.abs()).clip(0, 1).fillna(0)
    nopat = ebit * (1 - tax_rate)
    ic = eq + total_debt
    roic = (nopat / ic * 100).replace([np.inf, -np.inf], np.nan).fillna(0)
    
    fi_rows.append({'Chỉ số': 'ROE (%)', **roe.to_dict()})
    fi_rows.append({'Chỉ số': 'ROA (%)', **roa.to_dict()})
    fi_rows.append({'Chỉ số': 'ROIC (%)', **roic.to_dict()})
    
    # 4. Valuation
    eps = (ni / shares).replace([np.inf, -np.inf], np.nan).fillna(0)
    pe = (market_cap / ni).replace([np.inf, -np.inf], np.nan).fillna(0)
    pb = (market_cap / eq).replace([np.inf, -np.inf], np.nan).fillna(0)
    ps = (market_cap / revenue).replace([np.inf, -np.inf], np.nan).fillna(0)
    ev = market_cap + total_debt - cash
    ev_ebitda = (ev / ebitda).replace([np.inf, -np.inf], np.nan).fillna(0)
    p_cf = (market_cap / ocf).replace([np.inf, -np.inf], np.nan).fillna(0)
    
    fi_rows.append({'Chỉ số': 'EPS (VND)', **eps.to_dict()})
    fi_rows.append({'Chỉ số': 'P/E', **pe.to_dict()})
    fi_rows.append({'Chỉ số': 'P/B', **pb.to_dict()})
    fi_rows.append({'Chỉ số': 'P/S', **ps.to_dict()})
    fi_rows.append({'Chỉ số': 'EV/EBITDA', **ev_ebitda.to_dict()})
    fi_rows.append({'Chỉ số': 'P/Cash Flow', **p_cf.to_dict()})
    
    # 5. Liquidity
    cr = (ca / cl).replace([np.inf, -np.inf], np.nan).fillna(0)
    qr = ((ca - inv) / cl).replace([np.inf, -np.inf], np.nan).fillna(0)
    cash_r = (cash / cl).replace([np.inf, -np.inf], np.nan).fillna(0)
    
    fi_rows.append({'Chỉ số': 'Chỉ số thanh toán hiện thời', **cr.to_dict()})
    fi_rows.append({'Chỉ số': 'Chỉ số thanh toán nhanh', **qr.to_dict()})
    fi_rows.append({'Chỉ số': 'Chỉ số thanh toán tiền mặt', **cash_r.to_dict()})
    
    # 6. Solvency
    de = (tl / eq).replace([np.inf, -np.inf], np.nan).fillna(0)
    lev = (ta / eq).replace([np.inf, -np.inf], np.nan).fillna(0)
    icr = (ebit / int_exp).replace([np.inf, -np.inf], np.nan).fillna(0)
    
    fi_rows.append({'Chỉ số': 'Nợ phải trả / Vốn chủ sở hữu', **de.to_dict()})
    fi_rows.append({'Chỉ số': 'Đòn bẩy tài chính', **lev.to_dict()})
    fi_rows.append({'Chỉ số': 'Khả năng chi trả lãi vay', **icr.to_dict()})
    
    # 7. Efficiency (Turnovers) - Using revenue and cogs
    recv_t = (revenue / recv.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).fillna(0)
    inv_t = (cogs / inv.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).fillna(0)
    pay_t = (cogs / pay.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).fillna(0)
    
    fi_rows.append({'Chỉ số': 'Vòng quay các khoản phải thu', **recv_t.to_dict()})
    fi_rows.append({'Chỉ số': 'Vòng quay hàng tồn kho', **inv_t.to_dict()})
    fi_rows.append({'Chỉ số': 'Vòng quay các khoản phải trả', **pay_t.to_dict()})
    
    fi_df = pd.DataFrame(fi_rows)
    
    # Output
    with pd.ExcelWriter(output_file) as writer:
        bs.to_excel(writer, sheet_name='BALANCE SHEEET', index=False)
        cf.to_excel(writer, sheet_name='CASH FLOW STATEMENT', index=False)
        is_df.to_excel(writer, sheet_name='INCOME STATEMENT', index=False)
        fi_df.to_excel(writer, sheet_name='FINANCIAL INDEX', index=False)

    print(f"Success: Generated {output_file} successfully.")
    return output_file

if __name__ == "__main__":
    fix_dataset()

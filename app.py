import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

st.set_page_config(page_title="Hệ thống Phân tích Tài chính Tự động", layout="wide")

def safe_divide(num, den):
    try:
        n = float(num) if pd.notnull(num) else 0
        d = float(den) if pd.notnull(den) else 0
        if d == 0 or pd.isna(d):
            return "N/A"
        return n / d
    except:
        return "N/A"

def get_val(df, var_name, year):
    try:
        val = df[df['Biến số'] == var_name][year].values[0]
        return float(val) if pd.notnull(val) else None
    except:
        return None

def process_uploaded_file(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    target_sheets = ['BALANCE SHEEET', 'INCOME STATEMENT', 'CASH FLOW STATEMENT']
    
    all_data = []
    for sheet in target_sheets:
        if sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            if 'Năm' in df.columns:
                df['Năm'] = df['Năm'].astype(str).str.replace(r'\.0$', '', regex=True)
                df.set_index('Năm', inplace=True)
                df_t = df.T
                df_t.reset_index(inplace=True)
                df_t.rename(columns={'index': 'Biến số'}, inplace=True)
                df_t['Sheet'] = sheet
                all_data.append(df_t)

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        cols = ['Sheet', 'Biến số'] + [c for c in final_df.columns if c not in ['Sheet', 'Biến số']]
        final_df = final_df[cols]
        return final_df
    return None

def calculate_metrics(df):
    years = [str(c) for c in df.columns if c.isdigit()]
    results = {}
    
    for year in years:
        res = {"A. Định giá": {}, "B. Hiệu quả hoạt động": {}, "C. Thanh khoản & Chu kỳ": {}, "D. Cấu trúc vốn": {}}
        
        # 1. Base Variables Extract
        total_assets = get_val(df, 'TỔNG TÀI SẢN', year)
        equity = get_val(df, 'VỐN CHỦ SỞ HỮU', year)
        current_assets = get_val(df, 'TÀI SẢN NGẮN HẠN', year)
        inventory = get_val(df, 'Hàng tồn kho', year) or get_val(df, 'Hàng tồn kho, ròng', year)
        cash = get_val(df, 'Tiền và tương đương tiền', year)
        receivables = get_val(df, 'Các khoản phải thu', year)
        fixed_assets = get_val(df, 'Tài sản cố định', year)
        current_liabilities = get_val(df, 'Nợ ngắn hạn', year)
        st_debt = get_val(df, 'Vay ngắn hạn', year)
        lt_debt = get_val(df, 'Vay dài hạn', year)
        payables = get_val(df, 'Phải trả người bán', year)
        paid_in_capital = get_val(df, 'Vốn góp', year)
        
        revenue = get_val(df, 'Doanh số thuần', year) or get_val(df, 'Doanh số', year)
        gross_profit = get_val(df, 'Lãi gộp', year)
        net_income = get_val(df, 'Lãi/(lỗ) thuần sau thuế', year)
        ebit = get_val(df, 'EBIT', year)
        cogs = abs(get_val(df, 'Giá vốn hàng bán', year)) if get_val(df, 'Giá vốn hàng bán', year) else None
        
        int_exp_val = get_val(df, 'Trong đó: Chi phí lãi vay', year)
        interest_expense = abs(int_exp_val) if pd.notnull(int_exp_val) else None
        tax_exp = get_val(df, 'Chi phí thuế thu nhập doanh nghiệp', year)
        pre_tax_inc = get_val(df, 'Lãi/(lỗ) ròng trước thuế', year)
        eps_basic = get_val(df, 'Lãi cơ bản trên cổ phiếu', year)

        # -- Target Calculations --
        res["A. Định giá"]["EPS"] = eps_basic if eps_basic is not None else "N/A"
        shares_out = safe_divide(paid_in_capital, 10000)
        res["A. Định giá"]["BVPS"] = safe_divide(equity, shares_out) if shares_out != "N/A" else "N/A"

        res["B. Hiệu quả hoạt động"]["Doanh thu"] = revenue if revenue is not None else "N/A"
        res["B. Hiệu quả hoạt động"]["Biên LN Gộp"] = safe_divide(gross_profit, revenue)
        res["B. Hiệu quả hoạt động"]["Biên LN Ròng"] = safe_divide(net_income, revenue)
        res["B. Hiệu quả hoạt động"]["ROE"] = safe_divide(net_income, equity)
        res["B. Hiệu quả hoạt động"]["ROA"] = safe_divide(net_income, total_assets)
        res["B. Hiệu quả hoạt động"]["Vòng quay tài sản"] = safe_divide(revenue, total_assets)
        
        res["C. Thanh khoản & Chu kỳ"]["Tỷ số thanh toán hiện hành"] = safe_divide(current_assets, current_liabilities)
        res["C. Thanh khoản & Chu kỳ"]["Tỷ số thanh toán nhanh"] = safe_divide(current_assets - inventory, current_liabilities) if current_assets and inventory else "N/A"
        res["C. Thanh khoản & Chu kỳ"]["Tỷ số thanh toán tiền mặt"] = safe_divide(cash, current_liabilities)
        
        dso = safe_divide(receivables, safe_divide(revenue, 365))
        dio = safe_divide(inventory, safe_divide(cogs, 365))
        dpo = safe_divide(payables, safe_divide(cogs, 365))
        if all(x != "N/A" for x in [dso, dio, dpo]):
            res["C. Thanh khoản & Chu kỳ"]["Chu kỳ tiền"] = float(dio) + float(dso) - float(dpo)
        else:
            res["C. Thanh khoản & Chu kỳ"]["Chu kỳ tiền"] = "N/A"

        total_debt = (st_debt or 0) + (lt_debt or 0)
        res["D. Cấu trúc vốn"]["Nợ/VCSH"] = safe_divide(total_debt, equity)
        res["D. Cấu trúc vốn"]["Khả năng chi trả lãi vay"] = safe_divide(ebit, interest_expense)
        res["D. Cấu trúc vốn"]["Đòn bẩy tài chính"] = safe_divide(total_assets, equity)

        results[year] = res
    return results

def draw_metric_chart(results, group, metric_name, title):
    years = list(results.keys())
    values = []
    
    for y in years:
        val = results[y][group].get(metric_name, "N/A")
        if val != "N/A":
            values.append(val)
        else:
            values.append(0)
            
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years,
        y=values,
        name=metric_name,
        marker_color='indianred'
    ))
    fig.update_layout(title=title, xaxis_title="Năm", yaxis_title="Chỉ số")
    return fig

def draw_line_chart(results, group, metric_list, title):
    years = list(results.keys())
    fig = go.Figure()
    
    for metric_name in metric_list:
        values = []
        for y in years:
            val = results[y][group].get(metric_name, "N/A")
            if val != "N/A":
                values.append(val)
            else:
                values.append(0)
        fig.add_trace(go.Scatter(x=years, y=values, mode='lines+markers', name=metric_name))

    fig.update_layout(title=title, xaxis_title="Năm")
    return fig

st.title("Phân tích Chỉ số Tài chính (Automated FA Dashboard)")
st.markdown("Hệ thống xử lý Tự động dữ liệu Excel chuẩn hóa trích xuất ra 25 chỉ số và biểu đồ đồ họa chuyên nghiệp.")

uploaded_file = st.file_uploader("Vui lòng tải lên file báo cáo tài chính (.xlsx)", type=["xlsx"])
if uploaded_file is not None:
    with st.spinner("Agent DE đang làm sạch dữ liệu..."):
        clean_df = process_uploaded_file(uploaded_file)
        
    if clean_df is not None:
        st.success("Tải và chuẩn hóa dữ liệu vòng lặp DE thành công!")
        
        with st.spinner("Agent FA đang tính toán chỉ số tài chính..."):
            metrics_results = calculate_metrics(clean_df)
            
        st.subheader("Bảng Tổng Hợp Chỉ Số 5 Năm")
        
        # Format the display dataset
        display_data = []
        for year, groups in metrics_results.items():
            for group_name, group_data in groups.items():
                for m_name, m_val in group_data.items():
                    display_data.append({
                        "Năm": year,
                        "Nhóm": group_name,
                        "Chỉ số": m_name,
                        "Giá trị": f"{m_val:,.4f}" if isinstance(m_val, (int, float)) else "N/A"
                    })
        
        df_display = pd.DataFrame(display_data)
        st.dataframe(df_display.pivot(index=["Nhóm", "Chỉ số"], columns="Năm", values="Giá trị"), use_container_width=True)
        
        st.divider()
        st.subheader("Trực quan hóa Dữ liệu (DVE Visualizations)")
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(draw_line_chart(metrics_results, "B. Hiệu quả hoạt động", ["ROE", "ROA", "Biên LN Ròng"], "Hiệu quả Sinh lời"), use_container_width=True)
            st.plotly_chart(draw_line_chart(metrics_results, "D. Cấu trúc vốn", ["Nợ/VCSH", "Đòn bẩy tài chính"], "Rủi ro Tài chính & Cấu trúc Vốn"), use_container_width=True)
        with col2:
            st.plotly_chart(draw_line_chart(metrics_results, "C. Thanh khoản & Chu kỳ", ["Tỷ số thanh toán hiện hành", "Tỷ số thanh toán nhanh", "Tỷ số thanh toán tiền mặt"], "Khả năng Thanh khoản"), use_container_width=True)
            st.plotly_chart(draw_line_chart(metrics_results, "C. Thanh khoản & Chu kỳ", ["Số ngày thu tiền bình quân", "Số ngày tồn kho bình quân"], "Chu kỳ Vốn"), use_container_width=True)
            
    else:
        st.error("Lỗi cấu trúc File! Hệ thống không tìm thấy các Sheet tiêu chuẩn (BALANCE SHEET, INCOME STATEMENT...). Hãy kiểm tra lại.")

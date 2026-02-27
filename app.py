import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

st.set_page_config(page_title="Hệ thống Phân tích Tài chính Tự động", layout="wide")

# ===================== UTILITY FUNCTIONS =====================

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

# ===================== DATA PROCESSING (DE) =====================

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

# ===================== FINANCIAL CALCULATIONS (FA) =====================

def calculate_metrics(df):
    years = [str(c) for c in df.columns if c.isdigit()]
    results = {}

    for year in years:
        res = {"A. Định giá": {}, "B. Hiệu quả hoạt động": {}, "C. Thanh khoản & Chu kỳ": {}, "D. Cấu trúc vốn": {}}

        # Base Variables Extract
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
        total_liabilities = get_val(df, 'NỢ PHẢI TRẢ', year)

        revenue = get_val(df, 'Doanh số thuần', year) or get_val(df, 'Doanh số', year)
        gross_profit = get_val(df, 'Lãi gộp', year)
        net_income = get_val(df, 'Lãi/(lỗ) thuần sau thuế', year)
        ebit = get_val(df, 'EBIT', year)
        cogs = abs(get_val(df, 'Giá vốn hàng bán', year)) if get_val(df, 'Giá vốn hàng bán', year) else None

        int_exp_val = get_val(df, 'Trong đó: Chi phí lãi vay', year)
        interest_expense = abs(int_exp_val) if pd.notnull(int_exp_val) else None
        depreciation = get_val(df, 'Khấu hao', year)
        eps_basic = get_val(df, 'Lãi cơ bản trên cổ phiếu', year)
        rent_cost = get_val(df, 'Chi phí thuê tài sản', year) or get_val(df, 'Chi phí hoạt động - thuê', year)

        # -- A. Định giá --
        res["A. Định giá"]["EPS"] = eps_basic if eps_basic is not None else "N/A"
        shares_out = safe_divide(paid_in_capital, 10000)
        res["A. Định giá"]["BVPS"] = safe_divide(equity, shares_out) if shares_out != "N/A" else "N/A"

        # EV/EBITDAR
        if ebit is not None and depreciation is not None:
            ebitda = ebit + abs(depreciation)
        elif ebit is not None:
            ebitda = ebit
        else:
            ebitda = None

        if ebitda is not None and rent_cost is not None:
            ebitdar = ebitda + abs(rent_cost)
            res["A. Định giá"]["EBITDAR"] = ebitdar
        else:
            ebitdar = None
            res["A. Định giá"]["EBITDAR"] = "N/A"

        # -- B. Hiệu quả hoạt động --
        res["B. Hiệu quả hoạt động"]["Doanh thu"] = revenue if revenue is not None else "N/A"
        res["B. Hiệu quả hoạt động"]["Biên LN Gộp"] = safe_divide(gross_profit, revenue)
        res["B. Hiệu quả hoạt động"]["Biên LN Ròng"] = safe_divide(net_income, revenue)
        res["B. Hiệu quả hoạt động"]["ROE"] = safe_divide(net_income, equity)
        res["B. Hiệu quả hoạt động"]["ROA"] = safe_divide(net_income, total_assets)
        res["B. Hiệu quả hoạt động"]["Vòng quay tài sản"] = safe_divide(revenue, total_assets)

        # -- C. Thanh khoản & Chu kỳ --
        res["C. Thanh khoản & Chu kỳ"]["Tỷ số thanh toán hiện hành"] = safe_divide(current_assets, current_liabilities)
        res["C. Thanh khoản & Chu kỳ"]["Tỷ số thanh toán nhanh"] = safe_divide(current_assets - inventory, current_liabilities) if current_assets and inventory else "N/A"
        res["C. Thanh khoản & Chu kỳ"]["Tỷ số thanh toán tiền mặt"] = safe_divide(cash, current_liabilities)

        dso = safe_divide(receivables, safe_divide(revenue, 365))
        dio = safe_divide(inventory, safe_divide(cogs, 365))
        dpo = safe_divide(payables, safe_divide(cogs, 365))
        res["C. Thanh khoản & Chu kỳ"]["DSO"] = dso
        res["C. Thanh khoản & Chu kỳ"]["DIO"] = dio
        res["C. Thanh khoản & Chu kỳ"]["DPO"] = dpo
        if all(x != "N/A" for x in [dso, dio, dpo]):
            res["C. Thanh khoản & Chu kỳ"]["Chu kỳ tiền"] = float(dio) + float(dso) - float(dpo)
        else:
            res["C. Thanh khoản & Chu kỳ"]["Chu kỳ tiền"] = "N/A"

        # -- D. Cấu trúc vốn --
        total_debt = (st_debt or 0) + (lt_debt or 0)
        res["D. Cấu trúc vốn"]["Nợ/VCSH"] = safe_divide(total_debt, equity)
        res["D. Cấu trúc vốn"]["Khả năng chi trả lãi vay"] = safe_divide(ebit, interest_expense)
        res["D. Cấu trúc vốn"]["Đòn bẩy tài chính"] = safe_divide(total_assets, equity)

        results[year] = res
    return results

# ===================== CHART HELPERS =====================

def draw_line_chart(results, group, metric_list, title):
    years = sorted(results.keys())
    fig = go.Figure()

    for metric_name in metric_list:
        values = []
        for y in years:
            val = results[y][group].get(metric_name, "N/A")
            values.append(val if val != "N/A" else None)
        fig.add_trace(go.Scatter(x=years, y=values, mode='lines+markers', name=metric_name, connectgaps=True))

    fig.update_layout(title=title, xaxis_title="Năm", hovermode="x unified")
    return fig

def build_risk_matrix(base_value):
    id_range = [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
    vmh_range = [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]

    matrix = []
    for vmh in vmh_range:
        row = []
        for iliq in id_range:
            adjusted = base_value * (1 - iliq) * (1 - vmh)
            row.append(round(adjusted, 2))
        matrix.append(row)

    df_matrix = pd.DataFrame(
        matrix,
        index=[f"VMH {int(v*100)}%" for v in vmh_range],
        columns=[f"ID {int(i*100)}%" for i in id_range]
    )
    return df_matrix

# =============================================================
#                      MAIN APP LAYOUT
# =============================================================

st.title("📊 Hệ thống Phân tích Tài chính Tự động")
st.markdown("Hệ thống xử lý tự động dữ liệu Excel → 28 chỉ số tài chính → Dashboard trực quan.")

uploaded_file = st.file_uploader("Tải lên file báo cáo tài chính (.xlsx)", type=["xlsx"])

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Dashboard Chính",
    "🗃️ Dữ liệu chi tiết",
    "📐 Phân tích cấu trúc",
    "📈 Biến động chỉ số",
    "📖 Phương pháp tính chỉ số",
    "⚠️ Định giá & Chiết khấu rủi ro"
])

clean_df = None
metrics_results = None

if uploaded_file is not None:
    with st.spinner("Agent DE đang làm sạch dữ liệu..."):
        clean_df = process_uploaded_file(uploaded_file)

    if clean_df is not None:
        with st.spinner("Agent FA đang tính toán chỉ số tài chính..."):
            metrics_results = calculate_metrics(clean_df)

# ===================== TAB 1: DASHBOARD CHÍNH =====================
with tab1:
    if uploaded_file is None:
        st.info("👈 Hãy tải lên file báo cáo (.xlsx) để xem phân tích.")
    elif clean_df is not None and metrics_results is not None:
        st.success("✅ Tải và chuẩn hóa dữ liệu thành công!")
        st.subheader("Bảng Tổng Hợp Chỉ Số theo Năm")

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
        pivoted_df = df_display.pivot(index=["Nhóm", "Chỉ số"], columns="Năm", values="Giá trị").reset_index()
        pivoted_df.columns.name = None
        st.dataframe(pivoted_df, use_container_width=True, hide_index=True)
    else:
        st.error("❌ Không tìm thấy Sheet tiêu chuẩn (BALANCE SHEEET, INCOME STATEMENT, CASH FLOW STATEMENT).")

# ===================== TAB 2: DỮ LIỆU CHI TIẾT =====================
with tab2:
    if uploaded_file is None:
        st.info("Vui lòng upload file để xem dữ liệu chi tiết.")
    elif clean_df is not None:
        st.subheader("Dữ liệu tài chính thô (Raw Data)")
        st.markdown("Toàn bộ chỉ tiêu tài chính đã được bóc tách từ 3 sheet: **Balance Sheet**, **Income Statement**, **Cash Flow Statement**.")

        sheets = clean_df['Sheet'].unique()
        for sheet_name in sheets:
            with st.expander(f"📄 {sheet_name}", expanded=True):
                sheet_df = clean_df[clean_df['Sheet'] == sheet_name].drop(columns=['Sheet'])
                st.dataframe(sheet_df, use_container_width=True, hide_index=True)
    else:
        st.warning("Không có dữ liệu sạch để hiển thị.")

# ===================== TAB 3: PHÂN TÍCH CẤU TRÚC =====================
with tab3:
    if uploaded_file is None:
        st.info("Vui lòng upload file để xem phân tích cấu trúc.")
    elif clean_df is not None:
        st.subheader("Phân tích cấu trúc Tài sản & Nguồn vốn (Vertical Analysis)")
        years = [str(c) for c in clean_df.columns if c.isdigit()]

        if years:
            selected_year = st.selectbox("Chọn năm phân tích:", years, index=len(years)-1)

            # Cơ cấu Tài sản
            asset_items = {
                "Tiền & tương đương tiền": get_val(clean_df, 'Tiền và tương đương tiền', selected_year),
                "Phải thu": get_val(clean_df, 'Các khoản phải thu', selected_year),
                "Hàng tồn kho": get_val(clean_df, 'Hàng tồn kho', selected_year) or get_val(clean_df, 'Hàng tồn kho, ròng', selected_year),
                "Tài sản cố định": get_val(clean_df, 'Tài sản cố định', selected_year),
                "Tài sản khác": None
            }
            total_a = get_val(clean_df, 'TỔNG TÀI SẢN', selected_year)
            known_sum = sum(v for v in asset_items.values() if v is not None and v > 0)
            if total_a and total_a > known_sum:
                asset_items["Tài sản khác"] = total_a - known_sum

            asset_data = {k: v for k, v in asset_items.items() if v is not None and v > 0}
            if asset_data:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Cơ cấu Tài sản — Năm {selected_year}**")
                    fig_asset = px.treemap(
                        names=list(asset_data.keys()),
                        parents=[""] * len(asset_data),
                        values=list(asset_data.values()),
                        title=f"Cơ cấu Tài sản ({selected_year})"
                    )
                    st.plotly_chart(fig_asset, use_container_width=True)

                # Cơ cấu Nguồn vốn
                equity_val = get_val(clean_df, 'VỐN CHỦ SỞ HỮU', selected_year)
                st_liab = get_val(clean_df, 'Nợ ngắn hạn', selected_year)
                lt_liab = get_val(clean_df, 'Nợ dài hạn', selected_year)

                source_data = {}
                if st_liab and st_liab > 0: source_data["Nợ ngắn hạn"] = st_liab
                if lt_liab and lt_liab > 0: source_data["Nợ dài hạn"] = lt_liab
                if equity_val and equity_val > 0: source_data["VCSH"] = equity_val

                with col_b:
                    if source_data:
                        st.markdown(f"**Cơ cấu Nguồn vốn — Năm {selected_year}**")
                        fig_source = px.treemap(
                            names=list(source_data.keys()),
                            parents=[""] * len(source_data),
                            values=list(source_data.values()),
                            title=f"Cơ cấu Nguồn vốn ({selected_year})"
                        )
                        st.plotly_chart(fig_source, use_container_width=True)
    else:
        st.warning("Không có dữ liệu sạch để phân tích.")

# ===================== TAB 4: BIẾN ĐỘNG CHỈ SỐ =====================
with tab4:
    if uploaded_file is None:
        st.info("Vui lòng upload file để xem biến động chỉ số.")
    elif metrics_results is not None:
        st.subheader("Biến động Chỉ số Tài chính theo Năm (Trend Analysis)")

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                draw_line_chart(metrics_results, "B. Hiệu quả hoạt động", ["ROE", "ROA", "Biên LN Ròng", "Biên LN Gộp"], "Hiệu quả Sinh lời"),
                use_container_width=True
            )
            st.plotly_chart(
                draw_line_chart(metrics_results, "D. Cấu trúc vốn", ["Nợ/VCSH", "Đòn bẩy tài chính"], "Rủi ro Tài chính & Cấu trúc Vốn"),
                use_container_width=True
            )
        with col2:
            st.plotly_chart(
                draw_line_chart(metrics_results, "C. Thanh khoản & Chu kỳ", ["Tỷ số thanh toán hiện hành", "Tỷ số thanh toán nhanh", "Tỷ số thanh toán tiền mặt"], "Khả năng Thanh khoản"),
                use_container_width=True
            )
            st.plotly_chart(
                draw_line_chart(metrics_results, "C. Thanh khoản & Chu kỳ", ["DSO", "DIO", "DPO", "Chu kỳ tiền"], "Chu kỳ Vốn lưu động"),
                use_container_width=True
            )
    else:
        st.warning("Chưa có kết quả tính toán.")

# ===================== TAB 5: PHƯƠNG PHÁP TÍNH CHỈ SỐ =====================
with tab5:
    st.subheader("📖 Phương pháp tính toán 28 Chỉ số tài chính")
    st.markdown("---")

    st.markdown("### A. Chỉ số Định giá (Valuation)")
    st.markdown("""
| # | Chỉ số | Cách tính trong chương trình |
|:--|:---|:---|
| 1 | **EPS** | Trích xuất trực tiếp "Lãi cơ bản trên cổ phiếu" từ Báo cáo KQKD |
| 2 | **BVPS** | Vốn chủ sở hữu / (Vốn góp / 10.000) |
| 3 | **EV/EBITDA** | Giá trị doanh nghiệp (EV) / EBITDA — cần nhập giá thị trường |
| 4 | **EV/EBITDAR** | EV / (EBITDA + Chi phí thuê tài sản). Áp dụng cho DN thuê nhiều tài sản (hàng không, bán lẻ...) |
    """)

    st.markdown("### B. Hiệu quả Hoạt động & Sinh lời")
    st.markdown("""
| # | Chỉ số | Cách tính trong chương trình |
|:--|:---|:---|
| 5 | **Doanh thu** | Trích xuất trực tiếp "Doanh số thuần" từ KQKD |
| 6 | **Gross Margin** | Lợi nhuận gộp / Doanh thu *(ratio thập phân)* |
| 7 | **EBIT Margin** | EBIT / Doanh thu *(ratio thập phân)* |
| 8 | **Net Margin** | Lợi nhuận sau thuế / Doanh thu *(ratio thập phân)* |
| 9 | **ROE** | Lợi nhuận sau thuế / Vốn chủ sở hữu *(Cuối kỳ)* |
| 10 | **ROA** | Lợi nhuận sau thuế / Tổng tài sản *(Cuối kỳ)* |
| 11 | **ROIC** | EBIT × (1 – Thuế suất) / Vốn đầu tư (Nợ + VCSH) |
| 12 | **Asset Turnover** | Doanh thu / Tổng tài sản *(Cuối kỳ)* |
| 13 | **Fixed Asset Turnover** | Doanh thu / Tài sản cố định *(Cuối kỳ)* |
    """)

    st.markdown("### C. Thanh khoản & Chu kỳ tiền")
    st.markdown("""
| # | Chỉ số | Cách tính trong chương trình |
|:--|:---|:---|
| 14 | **Current Ratio** | Tài sản ngắn hạn / Nợ ngắn hạn |
| 15 | **Quick Ratio** | (Tài sản NH – Hàng tồn kho) / Nợ ngắn hạn |
| 16 | **Cash Ratio** | Tiền & tương đương / Nợ ngắn hạn |
| 17 | **DSO** | Phải thu / (Doanh thu / 365) |
| 18 | **DIO** | Hàng tồn kho / (COGS / 365) |
| 19 | **DPO** | Phải trả người bán / (COGS / 365) |
| 20 | **Cash Cycle** | DIO + DSO – DPO |
    """)

    st.markdown("### D. Cấu trúc Vốn & Rủi ro")
    st.markdown("""
| # | Chỉ số | Cách tính trong chương trình |
|:--|:---|:---|
| 21 | **Nợ/VCSH** | (Vay ngắn hạn + Vay dài hạn) / Vốn chủ sở hữu |
| 22 | **Interest Coverage** | EBIT / Chi phí lãi vay |
| 23 | **Financial Leverage** | Tổng tài sản *(Cuối kỳ)* / VCSH *(Cuối kỳ)* |
    """)

    st.markdown("---")
    st.caption("⚠️ Lưu ý: Tất cả chỉ số sử dụng số cuối kỳ thay cho bình quân do file BCTC 5 năm không có số đầu kỳ năm đầu tiên. Các biên lợi nhuận output dạng hệ số thập phân (ratio), không nhân 100%.")

# ===================== TAB 6: ĐỊNH GIÁ & CHIẾT KHẤU RỦI RO =====================
with tab6:
    st.subheader("⚠️ Định giá & Ma trận Chiết khấu Rủi ro")

    st.markdown("---")
    st.markdown("### Phương pháp luận EV/EBITDAR")
    st.markdown(r"""
**Công thức:**

$$EV/EBITDAR = \frac{EV}{EBITDA + R}$$

Trong đó:
- **EV (Enterprise Value):** Vốn hóa thị trường + Tổng nợ vay – Tiền & tương đương tiền
- **EBITDA:** Lợi nhuận trước lãi vay, thuế, khấu hao
- **R (Rent/Lease Cost):** Chi phí thuê tài sản (Operating Lease) phát sinh trong kỳ

**Lý do áp dụng:** Chỉ số EV/EBITDA bị méo khi so sánh DN sở hữu tài sản vs. thuê tài sản. Ngành hàng không (HVN, VJC) thuê tàu bay thay vì mua, khiến EBITDA "nhỏ hơn thực". Cộng thêm chi phí thuê `R` vào mẫu số giúp chuẩn hóa bội số định giá.
    """)

    if metrics_results is not None:
        latest_year = sorted(metrics_results.keys())[-1]
        ebitdar_val = metrics_results[latest_year]["A. Định giá"].get("EBITDAR", "N/A")
        if ebitdar_val != "N/A":
            st.metric(f"EBITDAR ({latest_year})", f"{ebitdar_val:,.0f}")
        else:
            st.warning(f"Không tìm thấy dữ liệu Chi phí thuê tài sản trong year {latest_year}. EBITDAR = N/A.")

    st.markdown("---")
    st.markdown("### Ma trận Chiết khấu Rủi ro trên Định giá")
    st.markdown("""
**Bối cảnh:** Khi cổ phiếu nằm trong **danh sách hạn chế giao dịch** (trading restriction), bội số định giá thị trường (P/E, P/B, EV/EBITDA…) không phản ánh đúng giá trị do phần bù rủi ro thanh khoản chưa được tính.

**Phương pháp:** Ma trận 2 chiều điều chỉnh đồng thời:
- **Trục ngang (ID — Illiquidity Discount):** Phần bù rủi ro do hạn chế giao dịch. Biểu diễn mức giảm giá thanh khoản: **0% → 40%** (bước 5%)
- **Trục dọc (VMH — Valuation Multiple Haircut):** Mức cắt giảm bội số định giá: **0% → 30%** (bước 5%)

**Công thức:**

$$\\text{Giá trị điều chỉnh} = \\text{Giá trị gốc} \\times (1 - ID) \\times (1 - VMH)$$
    """)

    base_val = st.number_input(
        "Nhập giá trị định giá gốc (VD: từ EV/EBITDA hoặc P/B, đơn vị: tỷ đồng hoặc VNĐ/cổ phiếu):",
        min_value=0.0, value=10000.0, step=100.0
    )

    if base_val > 0:
        df_matrix = build_risk_matrix(base_val)

        st.markdown(f"**Ma trận Giá trị điều chỉnh** (Giá trị gốc = **{base_val:,.0f}**)")

        fig_heatmap = go.Figure(data=go.Heatmap(
            z=df_matrix.values,
            x=df_matrix.columns.tolist(),
            y=df_matrix.index.tolist(),
            colorscale='RdYlGn',
            reversescale=False,
            text=[[f"{val:,.0f}" for val in row] for row in df_matrix.values],
            texttemplate="%{text}",
            hovertemplate="ID: %{x}<br>VMH: %{y}<br>Giá trị: %{z:,.0f}<extra></extra>"
        ))
        fig_heatmap.update_layout(
            title="Ma trận Chiết khấu Rủi ro (Xanh = Cao, Đỏ = Chiết khấu mạnh)",
            xaxis_title="Illiquidity Discount (ID)",
            yaxis_title="Valuation Multiple Haircut (VMH)",
            height=450
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)

        st.markdown("**Gợi ý kịch bản tham khảo:**")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            bull = base_val * (1 - 0.05) * (1 - 0.05)
            st.metric("🟢 Bull Case (ID 5%, VMH 5%)", f"{bull:,.0f}")
        with col_b:
            base = base_val * (1 - 0.15) * (1 - 0.10)
            st.metric("🟡 Base Case (ID 15%, VMH 10%)", f"{base:,.0f}")
        with col_c:
            bear = base_val * (1 - 0.30) * (1 - 0.20)
            st.metric("🔴 Bear Case (ID 30%, VMH 20%)", f"{bear:,.0f}")

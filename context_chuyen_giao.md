# Context Chuyển Giao: Hệ thống Phân tích Tài chính HVN

> **Ngày tạo:** 2026-03-23  
> **Dự án:** Framework phân tích & trực quan hóa tài chính doanh nghiệp  
> **Doanh nghiệp mục tiêu:** Vietnam Airlines (HVN)  
> **Thư mục dự án:** `c:\chương_trình_phân_tich\hvn\`

---

## 1. Bối cảnh & Mục tiêu

Xây dựng một hệ thống **tự động hóa phân tích tài chính** dựa trên:
- **Tài liệu thiết kế gốc:** [giúp tôi lập 1 bảng ma trận phân cấp và logic tín....md](file:///c:/chương_trình_phân_tich/giúp%20tôi%20lập%201%20bảng%20ma%20trận%20phân%20cấp%20và%20logic%20tín....md) — Chứa ma trận phân cấp (BS/IS/CF), 5 module kiến trúc, 5 nhóm chỉ số tài chính (~30 công thức), và logic kiểm định.
- **Dữ liệu:** [hvn data.xlsx](file:///c:/chương_trình_phân_tich/hvn/hvn%20data.xlsx) — 4 sheets: `BALANCE SHEET`, `INCOME STATEMENT`, `CASH FLOW STATEMENT`, `FINANCIAL INDEX`. Dữ liệu 5 năm (2021–2025).

---

## 2. Kiến trúc Hệ thống Hiện tại

```
c:\chương_trình_phân_tich\hvn\
├── hvn data.xlsx          ← Dữ liệu gốc (4 sheets, 2021-2025)
├── data_processor.py      ← Module A: Đọc Excel, chuẩn hóa cột, xử lý NaN
├── calculator.py          ← Module B+C: 6 methods tính toán
├── validator.py           ← Module D: 4 checks kiểm định kế toán
├── app.py                 ← Module E: Streamlit Dashboard (4 tabs)
└── huong_dan_doc_chi_so.md ← Tài liệu hướng dẫn đọc chỉ số
```

### 2.1 `data_processor.py` — DataProcessor class
- Đọc Excel bằng `pd.ExcelFile`, tự động xử lý lỗi tên sheet (`BALANCE SHEEET` → `BALANCE SHEET`).
- Đổi tên cột đầu tiên (`Năm`/`Chỉ số`) → `Khoản mục`.
- Output: `dict` of 4 DataFrames sạch.

### 2.2 `calculator.py` — Calculator class (6 methods)

| # | Method | Chức năng | Output |
|---|---|---|---|
| 1 | `calculate_missing_variables()` | Back-calculate Nợ vay có lãi, DSO, DIO | Append vào `FINANCIAL INDEX` |
| 2 | `vertical_analysis()` | Tỷ trọng Cấp 1/2 BS + Common-Size IS | `BS_VERTICAL`, `IS_VERTICAL` |
| 3 | `horizontal_analysis()` | YoY% cho BS, IS, CF | `BS_YOY`, `IS_YOY`, `CF_YOY` |
| 4 | `calculate_dpo_ccc()` | DPO + CCC | Append vào `FINANCIAL INDEX` |
| 5 | `calculate_net_debt_ebitda()` | Net Debt, ND/EBITDA | Append vào `FINANCIAL INDEX` |
| 6 | `dupont_analysis()` | ROS × AT × Leverage = ROE | `DUPONT` |

### 2.3 `validator.py` — 4 Checks (tất cả PASSED)
1. Tổng Tài Sản == Tổng Nguồn Vốn
2. TS ngắn hạn + TS dài hạn == Tổng Tài Sản
3. Nợ phải trả + Vốn CSH == Tổng Nguồn Vốn
4. Tiền cuối kỳ (CF) == Tiền (BS)

### 2.4 `app.py` — Streamlit Dashboard (4 tabs)

| Tab | Nội dung |
|---|---|
| 🛡️ Survival | Stacked Bar Nợ/VCSH, **100% Stacked Area** dòng tiền OCF/ICF/FCF, **100% Stacked Bar** cấu trúc tài sản, Net Debt/EBITDA |
| ⚙️ Operating | Area Chart DT vs GVHB, Line Chart biên LN (gộp/EBIT/ròng) |
| 📊 Financial Ratios | 5 nhóm: Valuation, Profitability+Dupont, Liquidity, Solvency, Efficiency |
| 📋 Data Tables | 7 bảng interactive + Download CSV |

---

## 3. Các Quyết Định Thiết Kế Quan Trọng

| Vấn đề | Quyết định | Lý do |
|---|---|---|
| DSO, DIO | Tính từ $365 / \text{Vòng quay}$ thay vì tính trực tiếp | Dữ liệu FI sheet đã có sẵn Vòng quay |
| Nợ vay có lãi | Back-calculate = Tổng vốn × Hệ số "Vốn vay/Tổng vốn" | BS không tách Nợ vay và Nợ chiếm dụng |
| Tên cột `Năm` → `Khoản mục` | Rename ở bước Normalization | Tránh nhầm lẫn với các cột năm (2021–2025) |
| Waterfall OCF → 100% Stacked Area | Theo yêu cầu điều chỉnh của user | Thể hiện tỷ trọng dòng tiền rõ hơn qua trend |
| Treemap → 100% Stacked Bar | Chuyển vào tab Survival | Phù hợp hơn cho so sánh tỷ trọng đa năm |

---

## 4. Đặc thù Dữ liệu HVN Cần Lưu Ý

- **VCSH âm** (2022–2024): Do lỗ lũy kế. ROE, P/B, D/E sẽ vô nghĩa hoặc đảo chiều.
- **CCC luôn âm** (-83 đến -107 ngày): Đặc thù ngành hàng không (thu tiền trước, trả sau).
- **Khấu hao lớn**: LNST có thể âm nhưng OCF dương → Ưu tiên phân tích dòng tiền.
- **Phục hồi 2025**: VCSH + 6.8T, OCF + 12.2T, Doanh thu 121T — HVN đã qua điểm hòa vốn.

---

## 5. Giai Đoạn Tiếp Theo (Gợi ý)

- [ ] Tích hợp thêm nguồn dữ liệu (SSI, FiinTrade)
- [ ] Mở rộng sang phân tích so sánh ngành (VJC, Bamboo)
- [ ] Thêm module dự báo (Forecasting) bằng ARIMA/ML
- [ ] Tạo PDF/Report tự động export từ Dashboard
- [ ] Deploy lên server (Railway/Streamlit Cloud) để truy cập từ xa

---

## 6. Cách Chạy

```bash
cd c:\chương_trình_phân_tich\hvn
streamlit run app.py
# Mở trình duyệt tại http://localhost:8501
```

**Dependencies:** `pandas`, `numpy`, `openpyxl`, `streamlit`, `plotly`

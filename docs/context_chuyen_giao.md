# Context Chuyển Giao: Hệ thống Phân tích Tài chính HVN

> **Ngày tạo:** 2026-03-23  
> **Dự án:** Framework phân tích & trực quan hóa tài chính doanh nghiệp  
> **Doanh nghiệp mục tiêu:** Vietnam Airlines (HVN)  
> **Thư mục dự án:** `c:\chương_trình_phân_tich\hvn\`

---

## 1. Bối cảnh & Mục tiêu

Xây dựng một hệ thống **tự động hóa phân tích tài chính** dựa trên:
- **Tài liệu thiết kế gốc:** [giúp tôi lập 1 bảng ma trận phân cấp và logic tín....md](file:///c:/chương_trình_phân_tich/giúp%20tôi%20lập%201%20bảng%20ma%20trận%20phân%20cấp%20và%20logic%20tín....md) — Chứa ma trận phân cấp (BS/IS/CF), 5 module kiến trúc, 5 nhóm chỉ số tài chính (~30 công thức), và logic kiểm định.
- **Data Flow và Logic Flow:** Chương trình xử lý dữ liệu theo phương pháp tuyến tính qua từng module tuần tự. Mỗi module đảm nhiệm một chức năng, vai trò độc lập nhưng tuân thủ quy tắc kiến trúc pipeline chặt chẽ.

### 1.1 Quy tắc Phát triển Module (Core Rules)

Nhằm đảm bảo tính đồng bộ, tách bạch và dễ dàng trong việc bảo trì hệ thống, tất cả các logic pipeline phải tuân thủ nghiêm ngặt quy tắc sau:

1. **Chuỗi cung ứng dữ liệu (I/O Chain):** Output của module này bắt buộc phải là Input của module kế tiếp trong chuỗi pipeline phân tích.
2. **Định dạng Output Tiêu chuẩn:** Mỗi một module khi thực thi chức năng thay đổi trạng thái dữ liệu **bắt buộc phải sinh ra file output với định dạng cụ thể** (chủ yếu là `.csv` đối với dữ liệu bảng hoặc `.json` đối với dữ liệu object/metadata) và lưu vào thư mục `output/` ở từng phân luồng (`1_processed`, `2_calculated`, v.v). Tuyệt đối hạn chế việc truyền state trung gian qua bộ nhớ RAM mà không lưu lại dấu vết file.
3. **Trường hợp Ngoại lệ:** Quy tắc chuỗi I/O khép kín này sẽ TỰ ĐỘNG được miễn trừ cho các trường hợp:
   - Các module mang tính chất đặc thù, chạy độc lập để crawl báo cáo hoặc set up môi trường (vd: Data Scraper).
   - Các module được thiết kế kiến trúc để chạy song song (Parallel tasks).
   - Các module mang nhiệm vụ kiểm tra chéo hệ thống, monitor độc lập (vd: `validator.py`).

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
| 🛡️ Survival | Stacked Bar Nợ/VCSH, **100% Stacked Area** dòng tiền, **100% Stacked Bar** cấu trúc tài sản, Net Debt/EBITDA, **DSCR & Liquidity Runway** (Mới) |
| ⚙️ Operating | Area Chart DT vs GVHB, Line Chart biên LN (gộp/EBIT/ròng) |
| 📊 Financial Ratios | 5 nhóm: Valuation, Profitability+Dupont, Liquidity, Solvency, Efficiency |
| 💡 Model Conclusion | **Business Model Timeline** (Mới), Phân loại mô hình định lượng |
| ⚡ Model Performance | **Operating Leverage (DOL)** (Mới), Phân tích điểm hòa vốn |
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
| Trục X Categorical (Prefix Năm/FY) | Fix lỗi clustering (chồng chéo) trong Plotly | Plotly tự nhận '2011' là số; thêm prefix + `type='category'` để trải đều 15 năm |
| Đơn vị Nghìn tỷ VND | Chia raw VND cho 10^12 | Phù hợp với quy mô doanh thu/tài sản 100k tỷ của HVN, giúp số liệu trên biểu đồ gọn gàng |

---

## 4. Đặc thù Dữ liệu HVN Cần Lưu Ý

- **VCSH âm** (2022–2024): Do lỗ lũy kế. ROE, P/B, D/E sẽ vô nghĩa hoặc đảo chiều. Hệ thống tự động khống chế và lọc bỏ các năm này khỏi mô hình tính toán Dải Định giá EV/EBITDA để tạo ra biểu đồ Football Field Chart có độ chính xác cao.
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

**Dependencies:** `pandas`, `numpy`, `openpyxl`, `streamlit`, `plotly`, `scikit-learn`, `statsmodels`

---

## 7. Chi tiết danh mục Trực quan hóa (Visualizations)

Dưới đây là thống kê các loại biểu đồ và chỉ số tương ứng được triển khai trong `src/app.py`:

### 7.1 Tab: Survival (Khả năng sinh tồn)
- **Cơ cấu Nợ vs Vốn Chủ Sở Hữu**: `Grouped Bar Chart` (Nợ Phải Trả, Vốn Chủ Sở Hữu).
- **Dòng tiền theo hoạt động**: `100% Stacked Area Chart` (OCF, ICF, FCF).
- **Cấu trúc Tài sản**: `100% Stacked Bar Chart` (Các khoản mục tài sản ngắn hạn & dài hạn).
- **Net Debt / EBITDA**: `Bar Chart` (Tỷ lệ Nợ ròng / EBITDA).
- **Dòng tiền Thực Thu vs Thực Chi**: `Line + Marker + Bar Overlaid Chart` (Tổng Thu, Tổng Chi, Dòng tiền Ròng).

### 7.2 Tab: Operating (Hiệu suất kinh doanh)
- **Doanh thu vs Giá vốn**: `Line + Area Chart` (Doanh số thuần, Giá vốn hàng bán).
- **Biên lợi nhuận qua các năm**: `Multi-Line Chart` (Biên LN gộp, Biên EBIT, Biên LN ròng).

### 7.3 Tab: Financial Ratios (Chỉ số Tài chính)
- **Hệ số định giá**: `Multi-Line Chart` (P/E, P/B, P/S).
- **EV/EBITDA & P/CF**: `Multi-Line Chart` (EV/EBITDA, P/CF).
- **ROE / ROA / ROIC (%)**: `Multi-Line Chart` (ROE, ROA, ROIC).
- **DuPont 3 nhân tố ROE**: `Combo Bar-Line Chart` (ROS, AT, Lev dạng Bar vs ROE dạng Line).
- **Phân rã ΔROE/ΔROA/ΔROIC**: `Grouped Bar Chart + Line` (Tác động nhân tố so với Δ Thực tế).
- **DuPont ROA 4 nhân tố**: `4-Subplot Bar Charts` (Tax Burden, Interest Burden, EBIT Margin, AT).
- **DuPont ROIC 2 nhân tố**: `2-Subplot Bar Charts` (NOPAT Margin, IC Turnover).
- **Hệ số thanh khoản**: `Multi-Line Chart` (Current, Quick, Cash Ratios).
- **Hệ số nợ**: `Multi-Line Chart` (D/E, Financial Leverage).
- **Khả năng trả nợ**: `Multi-Line Chart` (Net Debt/EBITDA, ICR).
- **Chu kỳ tiền tính toán (CCC)**: `Multi-Line Chart` (DSO, DIO, DPO, CCC).
- **DSCR (Hệ số khả năng trả nợ)**: `Line Chart` với ngưỡng an toàn (1.0x).
- **Liquidity Runway (Tháng)**: `Bar Chart` thể hiện số tháng cầm cự được với lượng tiền mặt hiện tại.

### 7.4 Tab: 💡 Kết luận Mẫu hình
- **Diễn biến Mô hình Kinh doanh**: `Horizontal Timeline Scatter` với annotations staggered (xen kẽ) mô tả sự dịch chuyển mô hình qua 15 năm.

### 7.5 Tab: ⚡ Hiệu suất Mẫu hình
- **Đòn bẩy Hoạt động (Operating Leverage)**: `Combo Bar-Line Chart`. Bar: Doanh thu vs Định phí (nghìn tỷ); Line: Biên EBIT %; Annotations: DOL (x).
- **Ngưỡng Hòa vốn (Break-even)**: `Horizontal Dash Line` cố định tại 121,000 tỷ VND.

### 7.4 Tab: Anomaly (Phân tích Bất thường)
- **Beneish M-Score**: `Gauge Chart` (Hiện tại) & `Line Chart` (Lịch sử).
- **Altman Z''-Score**: `Gauge Chart` (Hiện tại) & `Line Chart` (Lịch sử).
- **Sloan Accruals %**: `Gauge Chart` (Hiện tại) & `Bar Chart` (Lịch sử).

### 7.5 Tab: Dự báo & ML (Advanced Analysis)
- **Phân rã Chu kỳ STL**: `Line (Trend)`, `Bar (Seasonal)`, `Bar (Residual)`.
- **Dải Định giá (Valuation Bands)**: `Line Chart with Bands` (Mean, ±1σ, ±2σ, Actual EV/EBITDA). Tích hợp logic lọc dữ liệu chuyên sâu: Tự động loại bỏ các năm Vốn chủ sở hữu âm và EV/EBITDA âm nhằm kiến tạo biểu đồ Football Field đạt chuẩn.
- **Ma trận Độ nhạy DCF**: `Heatmap` (WACC vs g). Tích hợp Bội số mục tiêu (Terminal Multiple) cấu hình tự động trích xuất từ trung bình dữ liệu lịch sử chuẩn hóa.
- **What-if ROE Simulator**: `Metric Delta Indicators` (Yêu cầu thay đổi ROS, AT, Lev).
- **Lead-Lag Tương quan chéo**: `Heatmap` (Tương quan các nhân tố qua các độ trễ).
- **Trọng số Nhân tố**: `Horizontal Bar Char` (PLSR VIP Scores, ElasticNet Coefficients).
- **Sensitivity Line**: `Multi-Line Chart` (ROA hiện tại vs Kịch bản Tích cực/Tiêu cực).

---

## 8. Kế hoạch Tu chỉnh & Nâng cấp (Phase 2)

Dưới đây là kế hoạch chi tiết để chuyển đổi hệ thống sang kiến trúc **Business Model-driven Dashboard**, đảm bảo giữ nguyên toàn bộ dữ liệu trực quan hiện có (`~30 charts`) và tuân thủ logic thiết lập trước đó.

### 8.1 Chuẩn hóa Logic Tính toán
- **Tính vòng quay (Turnover)**: Chuyển đổi toàn bộ công thức sang số dư bình quân 2 kỳ (`Average Balance`) — Áp dụng cho FAT, ITO, RTO, PTO, WCT, TAT.
- **Tỷ suất sinh lời**: Cập nhật mẫu số là Vốn bình quân (Equity Average, Total Assets Average, Invested Capital Average) để phản ánh chính xác hiệu suất ROE, ROA, ROIC.

### 8.2 Tái cấu trúc Module & Luồng dữ liệu (Data Flow)
- **Module `business_classifier.py`**: Chạy sau `calculator.py` để nhận diện mẫu hình từ metrics định lượng.
- **Module `ui_architect.py` & `ui_templates.py`**: Điều phối việc chọn `Template` hiển thị dựa trên mẫu hình được phân loại.

### 8.3 Cơ cấu lại Nhóm/Thẻ Biểu đồ (Reorganization) — KHÔNG XÓA BIỂU ĐỒ
Toàn bộ biểu đồ hiện có trong Tab Survival, Operating, Ratios sẽ được phân phối lại vào 3 Tab bắt buộc và các Tab chuyên biệt động:

1.  **Tab 1: 📊 Cơ cấu Tài chính (Bắt buộc)**
    - Giữ nguyên: `Cấu trúc tài sản (100% Stacked Bar)`, `Nợ/VCSH (Grouped Bar)`, `Net Debt/EBITDA (Bar)`.
    - Di chuyển từ Survival: `Thực thu - Thực chi (Line/Bar Overlaid)`.
    
2.  **Tab 2: 🔍 Chất lượng BCTC (Bắt buộc)**
    - Tập trung tất cả: `Gauge Charts` (Beneish, Altman, Sloan) và `Line/Bar Charts` (Historical Scores) từ Tab Anomaly.
    
3.  **Tab 3: 💡 Kết luận Mẫu hình & Dẫn chứng (Bắt buộc)**
    - Hiển thị kết luận phân loại doanh nghiệp.
    - Dẫn chứng bằng các biểu đồ `Indicator/Delta` hoặc `Metrics` (PPE/TA, Gross Margin, v.v.) hiện đang phân tán.

4.  **Tab 4: ⚡/🛒 Hiệu suất Mẫu hình (Chuyên biệt - Theo Mẫu hình)**
    - Di chuyển các biểu đồ Ratios tương ứng từ Tab Operating và Financial Ratios vào đây:
        - *Thâm dụng vốn*: `FAT (Line)`, `D/E (Line)`, `ROE (3-factor DuPont Combo)`.
        - *Bán lẻ*: `ITO (Line)`, `Quick Ratio (Line)`, `CCC (Line)`.
        - *Nhẹ tài sản*: `NPM (Line/Area)`, `ROE (Line)`, `AT (Line)`.

5.  **Tab 5: 🤖 Phân tích Nâng cao (Giữ nguyên cấu trúc ML)**
    - STL, Valuation Bands, DCF Heatmap, ROE What-if, Lead-lag, VIP/ElasticNet, Sensitivity Line.

6.  **Tab 6: 📁 Bảng dữ liệu (Giữ nguyên)**

### 8.4 Logic chọn Biểu đồ (Guidelines)
Tiếp tục tuân thủ các nguyên tắc đã thống nhất trong Mục 3 và Mục 7:
- **100% Stacked Bar**: Dành cho cấu trúc tỷ trọng BS (Assets/Capital structure).
- **100% Stacked Area**: Dành cho tỷ trọng dòng tiền qua các năm.
- **Multi-Line + Marker**: Dành cho các tỷ số biên lợi nhuận, định giá và khả năng trả nợ.
- **Gauge Chart**: Dành cho đánh giá rủi ro tức thời (năm mới nhất).
- **Đơn vị tính**: Đảm bảo 100% biểu đồ có đơn vị rõ ràng (`tỷ VND`, `%`, `vòng`, `x`).

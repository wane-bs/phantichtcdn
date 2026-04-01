# Báo cáo Phương pháp Tính toán Chỉ số Tài chính (calculator.py)

Tài liệu này chi tiết hóa toàn bộ các công thức và logic tính toán được triển khai trong module `src/calculator.py` cho hệ thống phân tích tài chính Vietnam Airlines (HVN).

---

## 1. Nhóm Chỉ số Thanh khoản & Dòng tiền (Liquidity & Cash Flow)
Đây là nhóm chỉ số trọng tâm để đánh giá khả năng sinh tồn của HVN.

| Chỉ số | Công thức tính toán | Nguồn dữ liệu |
| :--- | :--- | :--- |
| **DSCR** | $CFO / (Lãi\ vay + Nợ\ ngắn\ hạn)$ | CF, IS, BS |
| **Stressed DSCR** | $(CFO \times 0.7) / (Lãi\ vay \times 1.2 + Nợ\ ngắn\ hạn)$ | Giả lập kịch bản sốc |
| **Liquidity Runway** | $Tiền\ mặt / (SG\&A + Lãi\ vay) / 12$ | BS, IS (Số tháng sinh tồn) |
| **FCFF** | $CFO - Tiền\ mua\ TSCĐ\ (Capex)$ | CF |
| **FCFE** | $FCFF - Lãi\ vay + (Vay\ mới - Trả\ nợ\ gốc)$ | CF, IS |
| **CFO / Gross Debt** | $CFO / (Nợ\ ngắn\ hạn + Nợ\ dài\ hạn)$ | CF, BS |
| **Net Debt / EBITDA** | $(Nợ\ vay\ có\ lãi - Tiền\ mặt) / EBITDA$ | FI, BS, IS |

> [!NOTE]
> **Nợ vay có lãi (Interest-bearing Debt):** Do dữ liệu thô không tách biệt, hệ thống tính ngược bằng công thức: `Tổng tài sản * (Hệ số Vốn vay/Tổng vốn)`.

---

## 2. Phân tích DuPont (Profitability Decomposition)
Hệ thống triển khai 3 cấp độ phân rã lợi nhuận để tìm nguyên nhân thay đổi hiệu suất.

### 2.1. ROE (3 bước)
$$ROE = ROS \times Asset\ Turnover \times Financial\ Leverage$$
*   **ROS (Biên LN ròng):** LNST / Doanh thu
*   **Asset Turnover (Vòng quay TS):** Doanh thu / Tổng TS bình quân
*   **Financial Leverage (Đòn bẩy):** Tổng TS bình quân / VCSH bình quân

### 2.2. ROA (4 bước)
$$ROA = Tax\ Burden \times Interest\ Burden \times EBIT\ Margin \times Asset\ Turnover$$
*   **Tax Burden:** LNST / Lợi nhuận trước thuế
*   **Interest Burden:** Lợi nhuận trước thuế / EBIT

### 2.3. ROIC (2 bước)
$$ROIC = NOPAT\ Margin \times IC\ Turnover$$
*   **NOPAT Margin:** $EBIT \times (1 - Thuế\ suất)$ / Doanh thu
*   **IC Turnover:** Doanh thu / Vốn đầu tư (Invested Capital) bình quân

---

## 3. Chỉ số Cảnh báo Bất thường (Anomaly Scores)
Đo lường rủi ro gian lận và xác suất phá sản.

| Chỉ số | Mô hình | Ý nghĩa |
| :--- | :--- | :--- |
| **Beneish M-Score** | 8 nhân tố (DSRI, GMI, AQI, SGI, DEPI, SGAI, TATA, LVGI) | Phát hiện thao túng lợi nhuận. Ngưỡng cảnh báo: $M > -2.22$ |
| **Altman Z''-Score** | Mô hình 4 nhân tố cho thị trường mới nổi | Dự báo rủi ro phá sản. Ngưỡng nguy hiểm: $Z < 1.1$ |
| **Sloan Accruals** | $(NI - OCF - ICF) / Tổng\ TS$ | Đo lường chất lượng lợi nhuận qua dồn tích. Rủi ro khi $> 25\%$ |

---

## 4. Hiệu quả Hoạt động (Efficiency)
Tính toán các vòng quay dựa trên **Số dư bình quân** để đảm bảo tính chính xác.

*   **DSO (Số ngày phải thu):** $365 / (Doanh\ thu / Phải\ thu\ bình\ quân)$
*   **DIO (Số ngày tồn kho):** $365 / (Giá\ vốn / Tồn\ kho\ bình\ quân)$
*   **DPO (Số ngày phải trả):** $365 / (Giá\ vốn / Phải\ trả\ bình\ quân)$
*   **CCC (Chu kỳ tiền):** $DSO + DIO - DPO$

---

## 5. Phân tích Tỷ trọng & Xu hướng (Vertical & Horizontal)
*   **Vertical (Dọc):** Tính tỷ trọng từng khoản mục so với Tổng tài sản (BS) hoặc Doanh thu thuần (IS).
*   **Horizontal (Ngang):** Tính tốc độ tăng trưởng so với năm trước (YoY%).
*   **Cash Inflow/Outflow (VAS 24):** Phân loại chi tiết toàn bộ dòng tiền vào/ra từ mọi hoạt động để đối soát với Dòng tiền ròng thực tế.

---

## 6. Logic Xử lý Đặc biệt
Hệ thống có cơ chế **"Cạch mặt dữ liệu nhiễu"** (hàm `_clean_distorted_metrics`):
*   **Khi VCSH âm:** Tự động gán `NaN` cho ROE, P/B, D/E và Đòn bẩy tài chính để tránh các con số dương "ảo" do mẫu số âm gây ra.
*   **Khi Lợi nhuận âm:** Tự động cô lập chỉ số P/E.

> [!IMPORTANT]
> Toàn bộ các chỉ số được lưu trữ dưới dạng file `.csv` trong thư mục `output/2_calculated/` sau khi pipeline kết thúc.

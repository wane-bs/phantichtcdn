# Báo cáo Phương pháp Phân tích Tài chính & Dự báo (HVN)

Tài liệu này chi tiết hóa toàn bộ các công thức, logic tính toán và mô hình dự báo được triển khai trong module `src/calculator.py` và `src/forecaster.py` cho hệ thống phân tích Vietnam Airlines (HVN).

---

# PHẦN I: TÍNH TOÁN CHỈ SỐ (calculator.py)

## 1. Nhóm Chỉ số Thanh khoản & Dòng tiền (Liquidity & Cash Flow)
Đây là nhóm chỉ số trọng tâm để đánh giá khả năng sinh tồn của HVN.

| Chỉ số | Công thức tính toán | Nguồn dữ liệu |
| :--- | :--- | :--- |
| **DSCR** | $CFO / (Lãi\ vay + Nợ\ ngắn\ hạn)$ | CF, IS, BS |
| **Stressed DSCR** | $(CFO \times 0.7) / (Lãi\ vay \times 1.2 + Nợ\ ngắn\ hạn)$ | Giả lập kịch bản sốc |
| **Liquidity Runway** | $(Tiền\ mặt + ĐT\ ngắn\ hạn) /( (SG\&A + Lãi\ vay) / 12 )$ | BS, IS (Số tháng sinh tồn) |
| **FCFF** | $CFO - Tiền\ mua\ TSCĐ\ (Capex)$ | CF |
| **FCFE** | $FCFF - Lãi\ vay + (Vay\ mới - Trả\ nợ\ gốc)$ | CF, IS |
| **CFO / Gross Debt** | $CFO / (Nợ\ ngắn\ hạn + Nợ\ dài\ hạn)$ | CF, BS |
| **Net Debt / EBITDA** | $(Nợ\ vay\ có\ lãi - Tiền\ mặt) / EBITDA$ | FI, BS, IS |
| **EV (Enterprise Value)** | $Vốn\ hóa + Nợ\ ròng + Lợi\ ích\ CĐ\ thiểu\ số$ | FI, BS, IS |

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
Đo lường rủi ro gian lận và xác suất phá sản. Hệ thống áp dụng 3 mô hình định lượng chuẩn quốc tế:

### 3.1. Beneish M-Score (Phát hiện Thao túng Lợi nhuận)
Phương trình hồi quy tuyến tính với 8 biến số:
$$M = -4.84 + 0.92 \cdot DSRI + 0.528 \cdot GMI + 0.404 \cdot AQI + 0.892 \cdot SGI + 0.115 \cdot DEPI - 0.172 \cdot SGAI + 4.679 \cdot TATA - 0.327 \cdot LVGI$$

**Trong đó:**
- **DSRI (Days Sales in Receivables Index):** Tỷ lệ Phải thu/Doanh thu kỳ này so với kỳ trước. ($>1$ chỉ ra khả năng ghi nhận doanh thu ảo).
- **GMI (Gross Margin Index):** Tỷ lệ Biên lãi gộp kỳ trước so với kỳ này. ($>1$ cho thấy biên lợi nhuận đang suy giảm, tạo áp lực "làm mượt" con số).
- **AQI (Asset Quality Index):** Tỷ lệ tài sản không sinh lời (ngoài TSCĐ và TSNH) so với Tổng TS.
- **SGI (Sales Growth Index):** Tốc độ tăng trưởng doanh thu.
- **DEPI (Depreciation Index):** Tỷ lệ khấu hao kỳ trước so với kỳ này. ($>1$ chỉ ra việc kéo dài thời gian khấu hao để tăng lợi nhuận).
- **SGAI (SGA Expenses Index):** Tỷ lệ chi phí bán hàng & quản lý trên doanh thu.
- **LVGI (Leverage Index):** Tỷ lệ nợ trên tổng tài sản.
- **TATA (Total Accruals to Total Assets):** $(LNST - CFO) / Tổng\ TS$.

> [!WARNING]
> **Ngưỡng:** $M > -2.22$ cho thấy khả năng cao báo cáo tài chính đã bị thao túng.

### 3.2. Altman Z''-Score (Mô hình cho Thị trường Mới nổi)
Áp dụng phiên bản dành cho doanh nghiệp phi sản xuất và thị trường mới nổi (Emerging Markets):
$$Z'' = 3.25 + 6.56 \cdot X_1 + 3.26 \cdot X_2 + 6.72 \cdot X_3 + 1.05 \cdot X_4$$

**Trong đó:**
- **$X_1$ (Working Capital / Total Assets):** Khả năng thanh khoản.
- **$X_2$ (Retained Earnings / Total Assets):** Tích lũy lợi nhuận (Hệ thống dùng VCSH làm đại diện do đặc thù dữ liệu).
- **$X_3$ (EBIT / Total Assets):** Hiệu suất sinh lời trên tài sản.
- **$X_4$ (Equity / Total Liabilities):** Cấu trúc vốn (VCSH / Tổng nợ phải trả).

> [!IMPORTANT]
> **Phân vùng rủi ro:**
> - **$Z < 1.1$:** Vùng Nguy hiểm (Distressed) - Nguy cơ phá sản cao.
> - **$1.1 \leq Z \leq 2.6$:** Vùng Xám (Grey) - Cần theo dõi chặt chẽ.
> - **$Z > 2.6$:** Vùng An toàn (Safe).

### 3.3. Sloan Accruals (Chất lượng Dòng tiền)
Đo lường mức độ chênh lệch giữa lợi nhuận kế toán và dòng tiền thực tế:
$$Sloan\ Ratio = \frac{NI - OCF - ICF}{Total\ Assets}$$
- **NI:** Lợi nhuận thuần.
- **OCF:** Dòng tiền từ HĐKD.
- **ICF:** Dòng tiền từ HĐ Đầu tư.

> [!NOTE]
> **Ngưỡng:** Tỷ lệ tuyệt đối $> 10\%$ bắt đầu có dấu hiệu cảnh báo; $> 25\%$ là rủi ro nghiêm trọng về chất lượng lợi nhuận.

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
*   **Cash Inflow/Outflow (VAS 24):** Phân loại chi tiết toàn bộ dòng tiền vào/ra từ mọi hoạt động (Thu từ thanh lý, vay mới, phát hành CP... và Chi mua TSCĐ, trả nợ gốc, cổ tức...) để đối soát với Dòng tiền ròng thực tế.

---

## 6. Phân tích Tác động Nhân tố (Factor Impact)
Sử dụng thuật toán **OLS Best-fit chain substitution** để cô lập tác động của từng nhân tố lên sự thay đổi của ROE, ROA, ROIC giữa hai kỳ báo cáo. Phương pháp này giải quyết bài toán "điểm dư" trong các mô hình nhân tính truyền thống bằng cách tối ưu hóa thứ tự thay thế biến.

---

## 7. Đòn bẩy Hoạt động & Điểm hòa vốn (Operating Leverage & Break-even)
Phân tích mối quan hệ giữa doanh thu, cấu trúc chi phí và lợi nhuận hoạt động (EBIT).

| Chỉ số | Công thức tính toán | Nguồn dữ liệu |
| :--- | :--- | :--- |
| **Doanh thu thuần** | Doanh số bán hàng và cung cấp dịch vụ sau giảm trừ | `IS` (Dòng 4) |
| **Biến phí (VC)** | $Giá\ vốn\ hàng\ bán - Khấu\ hao$ (Ước tính cốt lõi) | `IS`, `CF` |
| **Định phí (FC)** | $Chi\ phí\ Bán\ hàng + Chi\ phí\ Quản\ lý + Khấu\ hao$ | `IS`, `CF` |
| **Biên đóng góp (CM)** | $Doanh\ thu\ thuần - Biến\ phí$ | Tính toán |
| **BEP (Hoạt động)** | $FC / (CM / Doanh\ thu\ thuần)$ | EBIT-based BEP |
| **BEP (Phục vụ nợ)** | $(FC + Nợ\ ngắn\ hạn) / (CM / Doanh\ thu\ thuần)$ | Debt-Service BEP |
| **DOL** | $\% \Delta EBIT / \% \Delta Doanh\ thu$ | Operating Leverage |

### 7.1. Bản chất Toán học của Đòn bẩy & Biên EBIT
Để giải thích tại sao lợi nhuận không tăng vọt vô hạn và DOL biến động mạnh, hệ thống áp dụng các mô hình hàm số sau:

#### A. Hàm Tiệm cận của Biên EBIT
Phương trình mô phỏng biên lợi nhuận hoạt động:
$$EBIT\ Margin = (1 - v) - \frac{F}{R}$$
*Trong đó:* $v$ là tỷ lệ biến phí biên, $F$ là định phí, $R$ là doanh thu.

*   **Giai đoạn hòa vốn:** Khi $R$ tăng nhẹ thoát khỏi điểm hòa vốn, giá trị $\frac{F}{R}$ giảm nhanh, khiến Biên EBIT bứt phá mạnh từ số 0.
*   **Giai đoạn bão hòa:** Khi $R$ tiến ra rất xa điểm hòa vốn (ví dụ dự phóng 2025), phân số $\frac{F}{R}$ tiến dần về 0. Lúc này, Biên EBIT sẽ **tiệm cận kịch kim** về mức $(1 - v)$. Đây là lý do tại sao sau khi vượt ngưỡng hòa vốn, tốc độ tăng của biên lợi nhuận sẽ phẳng dần theo đường cong logarit.

#### B. Sự hội tụ của hệ số DOL
Công thức DOL dưới dạng hàm phân thức:
$$DOL = \frac{1}{1 - \frac{F}{R(1-v)}}$$

*   **Tại điểm hòa vốn ($EBIT \approx 0$):** Mẫu số tiến về 0, khiến **DOL tiến về vô cực (+∞)**. Đây là lý do năm 2024 HVN có DOL cực cao (23.1x).
*   **Khi doanh thu rất lớn:** Cụm $\frac{F}{R(1-v)}$ tiến về 0, dẫn đến **DOL tiến dần về 1.0**.
*   **Ý nghĩa:** Khi doanh nghiệp cực kỳ có lãi, đòn bẩy hoạt động sẽ mất dần tác dụng khuếch đại (bão hòa), và mỗi 1% doanh thu tăng thêm sẽ chỉ mang lại xấp xỉ 1% lợi nhuận tăng thêm.

#### C. Biến động DOL âm
DOL âm xảy ra khi tử số ($\% \Delta EBIT$) và mẫu số ($\% \Delta Doanh\ thu$) ngược chiều:
*   **Trường hợp 2015 (DOL -6.1x):** Doanh thu giảm nhưng EBIT tăng mạnh nhờ biến phí (giá dầu) giảm sâu.
*   **Trường hợp 2019 (DOL -16.7x):** Doanh thu tăng nhưng EBIT giảm mạnh do cạnh tranh làm giảm Yield (giá vé) hoặc chi phí cấu trúc tăng nhanh hơn doanh thu.

### 7.2. Hồi quy Log-Log & Bóc tách Đòn bẩy Cốt lõi
Để bóc tách chính xác Đòn bẩy hoạt động/tài chính cốt lõi (Core DOL & DFL) khỏi những nhiễu loạn từ cú sốc nhiên liệu, tỷ giá và sự đứt gãy kinh tế (như đại dịch Covid-19), hệ thống vận hành thuật toán Hồi quy đa biến Log-Log:
$$\ln(Total\ Cost) = \alpha + \beta_Q \ln(Revenue) + \beta_{Oil} \ln(Oil) + \beta_{FX} \ln(FX) + \gamma \cdot Covid\_Dummy$$

*   **Ý nghĩa các hệ số đo lường:** $\beta_{Oil}$ ($\varepsilon_{oil}$) và $\beta_{FX}$ ($\varepsilon_{fx}$) chính là độ co giãn của chi phí đối với biến động dài hạn (15 năm).
*   **Cơ chế Đòn bẩy Cốt lõi (Core DOL/DFL):** 
    *   $DOL_{core} = \frac{Q - \beta_Q \cdot TC}{EBIT}$ (Trong đó $\beta_Q$ là độ co giãn chi phí theo quy mô).
    *   Giúp loại bỏ hoàn toàn các "nhiễu" vĩ mô để nhìn thấy sức mạnh vận hành thực chất của bộ máy HVN.
*   **Data Pipeline (Luồng cấp dữ liệu tự động):** Các biến số vĩ mô lịch sử được xử lý từ đầu vào gốc `oil&exchange_rate.xlsx` bằng `data_processor.py`. Hệ thống tự động đồng bộ hóa kết quả hồi quy vào các biểu đồ nhạy cảm (3b) và kịch bản (3c).

---


> [!IMPORTANT]
> **Lưu ý về Doanh thu:** Hệ thống phân biệt rõ:
> - **Doanh thu thuần (~106 nghìn tỷ năm 2024):** Dùng để tính DOL và biên lợi nhuận cốt lõi.
> - **Tổng thu nhập (~113 nghìn tỷ năm 2024):** Là con số thường được HVN dùng trong báo cáo thường niên (bao gồm doanh thu tài chính và thu nhập bất thường từ tái cơ cấu nợ).

---

# PHẦN II: DỰ BÁO & MÔ PHỎNG (forecaster.py)

## 7. Phân rã Chuỗi thời gian (STL Decomposition)
Bóc tách các chỉ số tài chính (Doanh thu, EBITDA, OCF) thành 3 thành phần:
*   **Trend (Xu hướng):** Hướng đi dài hạn của doanh nghiệp.
*   **Seasonal (Mùa vụ):** Các biến động lặp lại theo chu kỳ năm (đặc thù hàng không).
*   **Residual (Nhiễu):** Các cú sốc bất thường không thuộc xu hướng hay mùa vụ.

## 8. Dải Định giá Lịch sử (Valuation Bands)
Xác định vùng giá trị "Rẻ - Đắt" của HVN dựa trên phân phối xác suất của chỉ số `EV/EBITDA` thu thập từ `calculator.py`.
*   **Thành phần cơ sở (từ `calculator.py`):**
    *   $EBITDA = EBIT + Khấu\ hao$
    *   $EV = Vốn\ hóa + (Nợ\ vay - Tiền\ mặt) + Lợi\ ích\ CĐ\ thiểu\ số$
*   **Công thức thống kê (từ `forecaster.py`):**
    *   **Mean Line ($\mu$):** Giá trị trung bình mẫu của chuỗi $EV/EBITDA$ lịch sử.
    *   **Độ lệch chuẩn ($\sigma$):** $\sigma = \sqrt{\frac{\sum_{i=1}^{n} (x_i - \mu)^2}{n-1}}$
    *   **Bands:** Vùng lệch chuẩn $\pm 1\sigma$ (68% xác suất) và $\pm 2\sigma$ (95% xác suất).
    *   **Vị trí tương đối (Band Position):** $\frac{Current - (\mu - \sigma)}{(\mu + \sigma) - (\mu - \sigma)}$ (vị trí trong dải $1\sigma$).

### 9. Định giá DCF & Ma trận Nhạy cảm WACC-g
Mô hình chiết khấu dòng tiền kết hợp Terminal Value:
*   **Giai đoạn 1 (5 năm):** Dự phóng FCFF dựa trên tốc độ tăng trưởng giả định.
*   **Giai đoạn 2 (Terminal Value):** Tính dựa trên `EBITDA_n * Mean(EV/EBITDA)`.
    *   *Lưu ý:* Hệ số Bội số mục tiêu (Terminal Multiple) được tính toán **tự động**, là giá trị trung bình lịch sử của EV/EBITDA (chỉ lấy các năm có EV/EBITDA dương, loại bỏ các năm khủng hoảng) nhằm mang lại tính co giãn linh hoạt và khách quan cho ma trận kết quả định giá.
*   **Công thức tổng quát:**
    $$EV = \sum_{t=1}^{5} \frac{FCFF_{base} \times (1+g)^t}{(1+WACC)^t} + \frac{EBITDA_{base} \times (1+g)^5 \times Multiplier_{hist}}{(1+WACC)^5}$$
*   **Sensitivity Matrix:** Ma trận giá trị doanh nghiệp tương ứng với các cặp (WACC, g).

## 10. Mô hình Nhạy cảm Cấu trúc (Oil & FX Impact)
Mô phỏng tác động trực tiếp của hai biến số vĩ mô quan trọng nhất lên HVN:
1.  **Giá dầu Jet A1:** Tác động trực tiếp lên chi phí nhiên liệu (chiếm ~37.5% Opex).
2.  **Tỷ giá USD/VND:** Tác động lên chi phí vận hành USD, lãi vay USD và **Lỗ chênh lệch tỷ giá chưa thực hiện**.
*   **Công thức thành phần:**
    *   **EBITDA mới:** $EBITDA_{new} = Revenue_{base} - [Fuel_{base} \cdot \frac{Oil_{new}}{Oil_{base}} \cdot \frac{FX_{new}}{FX_{base}} + NonFuel_{base} \cdot \frac{FX_{new}}{FX_{base}}]$
    *   **Lợi nhuận ròng mới:** $NI_{new} = NI_{base} - \Delta Fuel - \Delta Interest - FX_{RevalLoss}$
    *   **Giá trị doanh nghiệp mới:** $EV_{new} = MarketCap + [Debt_{base} \cdot (1-r_{USD}) + Debt_{base} \cdot r_{USD} \cdot \frac{FX_{new}}{FX_{base}}] - Cash$
    *   *Trong đó:* $r_{USD} \approx 80\%$ (tỷ lệ nợ USD), $FX_{RevalLoss}$ là lỗ đánh giá lại nợ gốc vay USD.
*   **Đầu ra:** Ma trận biến động EV/EBITDA và Lợi nhuận ròng (Net Profit) theo lưới (Oil, FX).

## 11. Dự phóng Kịch bản (Scenario Analysis)
Hệ thống thoát bỏ cơ chế dự báo định tính (hardcode) bằng cách thiết lập cấu trúc **Dự báo Hội tụ (Quantitative Convergence Analysis)**:
*   **Điểm neo (Anchor points):** Dữ liệu EBITDA năm đầu ($T+1$) của kịch bản được lấy trực tiếp từ **Ma trận Nhạy cảm Cấu trúc (Mục 10)**. Ví dụ: Kịch bản Tiêu cực tự động kéo số liệu sụt giảm EBITDA từ ô (Oil +$20, FX +5%) trong ma trận.
*   **Quỹ đạo (Paths):** Toàn bộ quỹ đạo 5 năm được tính toán lại theo biên lợi nhuận cấu trúc (Log-Log) và giả định dịch chuyển vĩ mô:
    *   **Cơ sở (Base):** Dầu và Tỷ giá biến động theo kỳ vọng trung bình, doanh thu tăng trưởng tự nhiên.
    *   **Tiêu cực (Negative):** Hiệu ứng "kép" từ sốc chi phí tức thời và gánh nặng nợ vay gia tăng do VND mất giá (hiệu chỉnh theo $\varepsilon_{fx}$).
    *   **Tích cực (Positive):** Tận dụng "Trần lợi nhuận" mới khi giá dầu giảm và cú hích công suất từ hạ tầng Long Thành (từ 2026).

## 13. Quy đổi Giá mục tiêu (Target Price Conversion)
Hệ thống thực hiện phép tính quy đổi ngược từ Giá trị Doanh nghiệp (EV) sang giá mỗi cổ phiếu để đưa ra khuyến nghị cụ thể.

*   **Bước 1: Tính Giá trị vốn cổ phần (Equity Value)**
    $$EV_{Mục\ tiêu} = (EBITDA_{Dự\ phóng} \times EV/EBITDA_{Lịch\ sử}) \times (1 - Chiết\ khấu\ rủi\ ro)$$
    $$Equity\ Value = EV_{Mục\ tiêu} - Nợ\ ròng - Lợi\ ích\ CĐ\ thiểu\ số$$
*   **Bước 2: Tính Giá mục tiêu (Target Price)**
    $$Target\ Price = Equity\ Value / Số\ CP\ lưu\ hành$$

> [!IMPORTANT]
> **Chiết khấu rủi ro tái cấu trúc (Restructuring Discount):** 
> HVN hiện tại đối mặt với "núi nợ" và gánh nặng tài chính lớn hơn nhiều so với giai đoạn hoàng kim. Hệ thống cho phép áp dụng mức chiết khấu (mặc định 40%) để điều chỉnh kỳ vọng định giá về mức an toàn, giúp đồng bộ hóa kết quả giữa phương pháp EV/EBITDA và DCF.

> [!IMPORTANT]
> **Xử lý dữ liệu nhiễu (Dữ liệu HVN):** 
> Trong giai đoạn khủng hoảng (2020-2022), HVN có EBITDA âm hoặc Vốn chủ sở hữu âm dẫn đến các hệ số EV/EBITDA lịch sử bị bóp méo, mất ý nghĩa. 
> Để đảm bảo Dải định giá (Valuation Bands) và Football Field Chart phản ánh đúng thực tế tương lai của doanh nghiệp bình thường, hệ thống đã cấu hình bộ lọc hai tầng: 
> 1) Loại bỏ các giá trị $EV/EBITDA \leq 0$.
> 2) Loại bỏ triệt để các năm có $VCSH \leq 0$.
> Các tập dữ liệu vi phạm bị loại bỏ hoàn toàn khỏi mẫu thống kê tính toán Mean và StdDev.

---

## Appendix: Logic Xử lý Đặc biệt
Hệ thống có cơ chế **"Cạch mặt dữ liệu nhiễu"** (hàm `_clean_distorted_metrics`):
*   **Khi VCSH âm:** Tự động gán `NaN` cho ROE, P/B, D/E và Đòn bẩy tài chính để tránh các con số dương "ảo" do mẫu số âm gây ra.
*   **Khi Lợi nhuận âm:** Tự động cô lập chỉ số P/E.

> [!IMPORTANT]
> Toàn bộ kết quả tính toán và dự báo được lưu trữ tại:
> - `output/2_calculated/`: Các file CSV chỉ số tài chính.
> - `output/4_advanced/`: Các file dữ liệu JSON/CSV phục vụ biểu đồ mô phỏng.

---

# PHẦN III: HỆ THỐNG BIỂU ĐỒ & DASHBOARD (app.py)

Hệ thống biểu đồ trên giao diện Streamlit (`app.py`) được thiết kế trực quan hóa các chỉ số tài chính, giúp nhận diện nhanh chóng rủi ro cấu trúc và mẫu hình kinh doanh. Dưới đây là phân loại biểu đồ, cùng với công thức, phương trình và mô hình hiển thị tương ứng cho từng tab:

## Tab 1: Khả năng sinh tồn (Cơ cấu Tài chính)
Trọng tâm: Đánh giá sức khỏe tài chính cơ bản, cơ cấu thanh khoản và biên độ sinh tồn dòng tiền.

1. **Cơ cấu Nguồn vốn (Bar Chart / Biểu đồ cột nhóm)**
   - **Chỉ tiêu:** Nợ ngắn hạn, Nợ dài hạn, Vốn Chủ Sở Hữu (VCSH).
   - **Mô hình:** Hiển thị số dư tuyệt đối (tỷ VND). Định dạng gộp nhóm cho phép đối sánh nhanh mức độ bao phủ bằng nguồn Vốn Chủ so với áp lực nợ phân bổ theo kỳ hạn.
2. **Tỷ trọng dòng tiền theo hoạt động (100% Stacked Area / Biểu đồ miền xếp chồng)**
   - **Mô hình:** Chuẩn hóa phần trăm theo trị tuyệt đối từng dòng tiền hoạt động nhằm xác định trọng tâm chiến lược luân chuyển tiền.
   - **Công thức:** $\%CF_i = \frac{|CF_i|}{|OCF| + |ICF| + |FCF|} \times 100$
3. **Cấu trúc Tài sản & Biến động Tài sản (100% Stacked Bar & Line Chart)**
   - **Công thức tải trọng tài sản:** $\frac{Khoản\ mục_{tương\ đối}}{Tổng\ tài\ sản} \times 100$ 
   - Đồng thời đối chiếu xu hướng dài hạn giữa Tài sản ngắn hạn, Tổng tài sản, Tài sản cố định bằng biểu đồ đường đa biến.
4. **Thực Thu − Thực Chi − Dòng tiền Ròng (Combo Series: Line & Marker)**
   - Phân rã dòng tiền (VAS 24) biểu thị mốc Thực Thu / Thực Chi, trong đó phần bù Dòng tiền Ròng (Bar Overlay) được quy ước xanh dương (+) hay đỏ (-).
5. **Cảnh báo biên độ an toàn (Liquidity DSCR & Runway Charts)**
   - **Diễn biến tự phục vụ nợ (DSCR Bars & Stress Line):** Căn cứ tỷ suất đảm bảo nợ, áp dụng kịch bản sốc 30% sụt giảm từ dòng tiền cốt lõi (CFO) kết hợp tăng 20% chi phí lãi vay (Interest).
   - **Khoảng cách sinh tồn (Liquidity Runway Bars):** 
     - **Công thức mô hình:** $Runway_{tháng} = \frac{Tiền\ mặt\ +\ Đầu\ tư\ ngắn\ hạn}{Chi\ phí\ cố\ định\ hàng\ tháng}$
      - *Trong đó:* Chi phí cố định hàng tháng = $(Chi\ phí\ Bán\ hàng + Chi\ phí\ QLDN + Lãi\ vay) / 12$. Cho biết doanh nghiệp có thể hấp thụ cú sốc doanh thu ngừng trệ trong bao nhiêu tháng tiếp nối.

## Tab 2: Chất lượng BCTC (Anomaly)
Trọng tâm: Đo lường chất lượng lợi nhuận và dấu hiệu rủi ro.

1. **Rủi ro Bất thường Tức thời (Gauge / Dashboard Đồng hồ đo)**
   - Đo lường chỉ số năm gần nhất phân vạch ngưỡng rủi ro:
     - **Beneish M-Score:** Phân loại cảnh báo gian lận hoặc "làm mượt" lợi nhuận. Ranh giới đỏ khi $M > -2.22$.
     - **Altman Z''-Score:** Cảnh báo nguy cơ phá sản, vùng xám ($1.1 - 2.6$).
     - **Sloan Accruals:** Đánh giá chất lượng dòng tiền dồn tích. Ranh giới $\pm 10$ đến $\pm 25\%$.
2. **Kịch bản Bất thường Lịch sử (Line Chart / Biểu đồ đường)**
   - Biểu thị chuỗi theo thời gian. Mức độ xuyên thủng ranh giới ngang (dash lines) biểu thị cấu hình thay đổi chất lượng BCTC và mức độ rủi ro hệ đối chiếu.

## Tab 3: Kết luận Mẫu hình
Trọng tâm: Đúc kết phương hướng kinh doanh và đưa ra khuyến nghị hệ thống.

1. **Diễn biến Mô hình Kinh doanh Qua các năm (Timeline Scatter Chart / Chuỗi trượt phân loại)**
   - Sử dụng các hình thoi hiển thị quy tắc kinh doanh năm (ví dụ: Bán lẻ, Thâm dụng vốn) thông qua engine phân loại tự động sử dụng cấu trúc tỷ trọng của nhóm chỉ tiêu "chìa khóa" (Asset ratio, Profit margins, ...).
2. **Quản trị Tín hiệu Báo cáo**
   - Chỉ số định lượng đặc trưng tại chu kỳ cuối cùng biểu thị tỷ trọng phần khối (ví dụ: `TSCĐ/Tổng TS %`, `Hàng tồn kho/Tổng TS %`).

## Tab 4: Hiệu suất Mẫu hình (Operating)
Trọng tâm: Đánh giá biên lợi nhuận ròng, mô hình chi phí và cơ cấu phân tách DuPont.

1. **Đòn bẩy Hoạt động (Operating Leverage & Margin Gap)**
   - **Khoảng hở hòa vốn (Filled Area Chart):** Trực quan hóa phần đệm an toàn giữa Doanh thu và Giá vốn.
   - **Đòn bẩy Hoạt động (Combo Bar-Line):** Kết hợp Doanh thu, Định phí và EBIT thực tế. Hiển thị DOL annotations tại từng năm để nhận diện vùng rủi ro.
2. **Ma trận Nhạy cảm: Dịch chuyển Điểm hòa vốn & Đòn bẩy (Macro Sensitivity)**
   - **Mô hình Mỏ neo (Base 2025):** Sử dụng các tham số nền: Giá dầu Jet A1 ($90) và Tỷ giá USD/VND ($26,300$).
   - **Cơ chế truyền dẫn:**
     - Sốc Giá dầu $\rightarrow$ Biến phí (Variable Costs) thông qua $\varepsilon_{oil}$.
     - Sốc Tỷ giá $\rightarrow$ Định phí (Fixed Costs - Leases/Debt) thông qua $\varepsilon_{fx}$.
   - **Đầu ra:** Mô phỏng sự dịch chuyển của đường cong Biên EBIT và Điểm hòa vốn dưới tác động của các cú sốc vĩ mô.
3. **Phân rã Biên lợi nhuận cấu trúc (DuPont Subplots)**
   - Trực quan hóa đóng góp vào ROA, ROIC.
   - **Lưu ý:** Hệ thống tự động vô hiệu hóa phân rã ROE khi VCSH âm để bảo vệ tính chính xác của báo cáo.
4. **Phân tách Thay đổi Chuỗi (Best-fit OLS Factor Impact)**
   - Sử dụng thuật toán OLS để định lượng mức đóng góp (%pts) của từng nhân tố tài chính vào sự thay đổi lợi nhuận ròng.

## Tab 5: Định giá Doanh nghiệp (Enterprise Value Framework)
Trọng tâm: Trực quan hóa giá trị doanh nghiệp, quy hoạch kỳ vọng cơ sở và mô phỏng tác động vi mô/vĩ mô. Bằng phương pháp **Định giá Doanh nghiệp EV** thay vì vốn dĩ truyền thống (DCF thuần) để giải quyết bất ổn cho HVN.

1. **Phân rã Chu kỳ Thời gian STL (Decomposition Subplots / Scatter Line & Bar)**
   - **Mô hình chuẩn:** $Y_t = Trend_t + Seasonal_t + Residual_t$. Chuỗi nguyên bản được chia tách, cho phép nhìn nhận yếu tố năng lực cốt lõi tách biệt khỏi dao động ngoại cảnh và yếu tố chu kỳ ngắn.
2. **Dải Định giá Lịch sử (Valuation Bands / Multi-Line)**
   - **Phương trình mô phỏng:** 
     - Dải đắt đỏ: $+1\sigma\ \&\ +2\sigma$. Mức kỳ vọng chung (Mean). Dải giá trũng: $-1\sigma\ \&\ -2\sigma$.
     - Khối tham số **Band Position**: $\frac{EV/EBITDA\ hiện\ tại - (\mu - \sigma)}{2\sigma}$
3. **Ma trận Định giá DCF (WACC-g Heatmap)**
   - Heatmap độ nhạy Enterprise Value khi thay đổi giả định tăng trưởng và chi phí vốn.
   - **Hệ số Bội số mục tiêu (Terminal Multiple):** Tự động đồng bộ hóa với giá trị Trung vị (Median) lịch sử để đảm bảo tính khách quan.
4. **Ma trận Nhạy cảm Cấu trúc - Vĩ mô Oil & FX (Live Score & Heatmap Grid)**
   - Lõi tham số bù dịch $VND/USD$ theo nợ dư USD hiện diện thực. Lõi rủi ro Giá dầu Jet A1 phân vùng theo Opex. 
   - **Live Impact Output:** Kịch bản biến động $\pm 1\%$ FX hay $\pm\$10$ Jet A1 trực tiếp báo lãi/lỗ kỳ hạn qua Indicator Metric, bổ trợ bảng đo định mức (EV/EBITDA hoặc Lợi nhuận ròng).
5. **Kịch bản Định giá Phân kỳ (Scenario Analysis / Multi-line Area)**
   - Dự kiến 3 lộ trình tiến hóa chuẩn xác: Base/Positive/Negative ($EV/EBITDA$) chạy tiến định hướng đến $2028$. 
   - **Đặc trưng:** Toàn bộ kịch bản được "neo" (quant-anchored) vào Ma trận Nhạy cảm 3b và kết quả Hồi quy Log-Log. Người dùng có thể quan sát sự phân kỳ của hệ số định giá khi cấu trúc chi phí thay đổi theo kịch bản vĩ mô.
6. **Football Field Chart (Horizontal Oriented Bar / Biểu đồ hộp trục ngang)**
   - **Cấu trúc:** Nhóm hợp nhất dải định giá biên độ Min-Max theo các công cụ đo lường quy hồi lịch sử (EV/EBITDA $\pm1\sigma$) và DCF Valuation. Biểu diễn độ vươn (Gap) Min-Max nằm trên lưới ngang giá trị Enterprise Value tuyệt đối. 
   - **Tích phân Mục tiêu:** Hiển thị mốc "EV Hiện Tại" song song với bộ chuyển hóa (Conversion Metric Card) ra $Target\ Price\ (VND/cổ phiếu)$ tại phân vùng giao diện UI, dựa theo phép trừ Nợ ròng và Lợi ích cổ đông thiểu số khỏi Enterprise Value.

---

# PHẦN IV: TRIẾT LÝ QUẢN TRỊ TRUNG TÂM

Để giải thích các biến động ngược chiều và giới hạn biên lợi nhuận, hệ thống áp dụng bộ khung lý thuyết **"Convergence to Margin Ceiling"**:

1. **Sự dịch chuyển BEP:** Điểm hòa vốn không cố định mà dịch chuyển "tịnh tiến sang phải" khi Định phí ($F$) tăng (đội bay mới) hoặc Biến phí ($v$) tăng (Tỷ giá/Dầu).
2. **Hệ số DOL động:** Đòn bẩy cao nhất khi doanh nghiệp tiệm cận BEP (vùng dốc trên biểu đồ) và giảm dần về 1.0x khi doanh thu vượt xa BEP (vùng thoải).
3. **Trần Lợi nhuận (Margin Ceiling):** Biên EBIT không tăng vô hạn mà tiệm cận mốc $(1 - v)$. Tại HVN, do biến phí chiếm trọng số lớn, trần này thường giới hạn ở mức 20-25%.
4. **Chiến lược "Nâng trần":** Nâng đường cong biên lợi nhuận thông qua quản trị Yield, tối ưu hóa Fleet và sử dụng các công cụ Hedging để bảo vệ cấu trúc chi phí trước rủi ro vĩ mô.

# BÁO CÁO QUẢN TRỊ: ĐÒN BẨY HOẠT ĐỘNG & ĐIỂM HÒA VỐN (HVN)

Tài liệu này giải thích bản chất động của Điểm hòa vốn (BEP), cơ chế truyền dẫn của Đòn bẩy hoạt động (DOL), và các chiến lược nâng cao trần lợi nhuận cho Vietnam Airlines (HVN).
Các phương trình và thông số đã được đồng bộ hóa với chương trình phân tích thực tế (`app.py`, `calculator.py`, `forecaster.py`).

---

## I. TẠI SAO ĐIỂM HÒA VỐN (BEP) BIẾN ĐỘNG LIÊN TỤC?

Điểm hòa vốn không phải là một con số tĩnh. Nó là kết quả của sự tương tác giữa ba biến số nền tảng:

$$BEP = \frac{F}{1 - v} = \frac{F}{CM\_Ratio}$$

Trong đó $F$ là Định phí, $v = VC / Revenue$ là Tỷ lệ biến phí biên.

1.  **F (Định phí - Fixed Costs):**
    - Trong hệ thống: $FC \approx Khấu\ hao\ TSCĐ + Chi\ phí\ Bán\ hàng + Chi\ phí\ Quản\ lý\ (QLDN)$
    - Khi HVN mở rộng đội bay, $F$ phình to, đẩy BEP sang phải.

2.  **v (Tỷ lệ biến phí biên):**
    - Trong hệ thống: $VC \approx Giá\ vốn\ hàng\ bán - Khấu\ hao$
    - Giá dầu Jet A1 và chi phí USD chiếm phần lớn biến phí. Tỷ giá tăng → $v$ tăng → BEP tăng.

3.  **Tham số Mỏ neo (Base 2025) của hệ thống:**
    - **BEP Hoạt động (EBIT):** ~72.519 tỷ VND
    - **Giá dầu Jet A1 gốc:** ~$90/thùng
    - **Tỷ giá gốc:** ~26.300 VND/USD
    - **Tỷ lệ nhiên liệu/Opex ($r_{fuel}$):** ~37.5%
    - **Tỷ lệ nợ vay USD ($r_{USD}$):** ~80%

---

## II. HAI CẤP ĐỘ PHÂN TÍCH HÒA VỐN

Hệ thống tích hợp hai chế độ phân tích (Toggle Mode) để nhìn từ hai góc độ khác nhau:

### Chế độ 1 — Hòa vốn Hoạt động (EBIT-based BEP)
Rào cản chỉ bao gồm chi phí vận hành cốt lõi:

$$BEP_{EBIT} = \frac{F}{1 - v}$$

**Câu hỏi trả lời:** "Doanh nghiệp cần đạt bao nhiêu doanh thu để hòa vốn vận hành thuần túy?"

### Chế độ 2 — Hòa vốn Phục vụ Nợ (Debt-Service BEP)
Rào cản được cộng thêm gánh nặng nợ ngắn hạn và lãi vay:

$$BEP_{Debt} = \frac{F + Nợ\ ngắn\ hạn + Lãi\ vay}{1 - v}$$

**Câu hỏi trả lời:** "Doanh nghiệp cần đạt bao nhiêu doanh thu để vừa vận hành vừa không vỡ nợ kỹ thuật?"

> [!IMPORTANT]
> Khoảng cách $(BEP_{Debt} - BEP_{EBIT})$ là "vùng nguy hiểm" – nơi doanh nghiệp có lợi nhuận hoạt động nhưng vẫn có thể vỡ nợ nếu dòng tiền không đủ.

---

## III. CÔNG THỨC TRUYỀN DẪN CÚ SỐC VĨ MÔ

Hệ thống tính toán lại BEP và EBIT khi có cú sốc đầu vào theo hai kênh tác động riêng biệt:

### Kênh 1: Sốc Giá Dầu → Biến Phí
Mỗi $1 tăng giá dầu Jet A1 làm tăng Tổng chi phí:
$$\Delta VC_{oil} = \Delta Oil_{price} \times 452.4\ tỷ\ VND$$

$$VC_{mới} = VC_{cũ} + \Delta VC_{oil}$$

### Kênh 2: Sốc Tỷ Giá → Định Phí (Leases và Nợ USD)
Mỗi 1% mất giá VND làm tăng Định phí (chi phí thuê tàu và trả nợ USD):
$$\Delta FC_{fx} = \Delta FX\% \times 533\ tỷ\ VND$$

$$FC_{mới} = FC_{cũ} + \Delta FC_{fx}$$

### Trạng thái sau Cú Sốc
Sau khi có sốc, hệ thống tính lại toàn bộ:

$$v_{mới} = \frac{VC_{mới}}{Revenue_{base}}$$

$$BEP_{mới} = \frac{FC_{mới}}{1 - v_{mới}}$$

$$EBIT_{mới} = Revenue_{base} - VC_{mới} - FC_{mới}$$

$$DOL_{mới} = \frac{Revenue_{base} \times (1 - v_{mới})}{EBIT_{mới}}$$

---

## IV. HƯỚNG DẪN ĐỌC MA TRẬN & BIỂU ĐỒ TRÊN DASHBOARD

### 1. Biểu đồ Đòn bẩy Hoạt động (Tab 4)
| Thành phần | Ý nghĩa |
|---|---|
| **Cột Xanh (Doanh thu)** | Quy mô thực tế (nghìn tỷ VND). |
| **Cột Đỏ (Định phí FC)** | Rào cản chi phí cố định phải vượt qua. |
| **Đường Vàng (EBIT)** | Lợi nhuận thực tế (tỷ VND, trục phải). |
| **DOL annotation** | Khuếch đại: 1% tăng DT → bao nhiêu % tăng EBIT. |

**DOL âm** xảy ra khi tử số và mẫu số ngược chiều:
- *2015 (DOL âm):* Doanh thu giảm nhưng EBIT tăng nhờ giá dầu giảm sâu.
- *2019 (DOL âm):* Doanh thu tăng nhưng EBIT giảm do chi phí cấu trúc tăng nhanh hơn.

### 2. Biểu đồ Dịch chuyển Trần Lợi nhuận (Dual Curve)
Biểu đồ trực quan hóa phương trình:

$$EBIT\ Margin = \underbrace{(1 - v)}_{\text{Trần lý thuyết}} - \underbrace{\frac{F}{R}}_{\text{Gánh định phí}}$$

Mỗi cú sốc (dầu hoặc FX) dịch chuyển **toàn bộ đường cong xuống** và **BEP sang phải**.

---

## V. BẢN CHẤT TOÁN HỌC CỦA ĐÒN BẨY

### A. Hàm tiệm cận của Biên EBIT
Khi $R$ tăng, $\frac{F}{R}$ giảm — nhưng không bao giờ về 0:

$$EBIT\ Margin \xrightarrow{R \to \infty} (1 - v)$$

### B. Sự hội tụ của DOL

$$DOL = \frac{1}{1 - \frac{F}{R(1-v)}} \xrightarrow{R\ lớn} 1.0x$$

- **Gần BEP:** DOL tiến về $+\infty$ → lợi nhuận cực nhạy với doanh thu.
- **Xa BEP:** DOL tiến về $1.0x$ → tác dụng khuếch đại bão hòa.
- **Năm 2024:** HVN có DOL ~23.1x do mới thoát khỏi vùng lỗ.

### C. Đòn bẩy Cốt lõi (Hệ thống Hồi quy Trực giao FWL)
Để bóc tách chính xác tác động của Dầu và Tỷ giá mà không bị nhiễu bởi xu hướng tăng trưởng doanh thu (Multicollinearity), hệ thống áp dụng định lý **Frisch-Waugh-Lovell (FWL)** qua 3 bước:

1.  **Trích xuất Cú sốc thuần túy (Orthogonalization):**
    - Hồi quy phụ: $\ln(FX) \sim \ln(Q)$ và $\ln(Oil) \sim \ln(Q)$.
    - Lấy phần dư (Residuals): $resid\_fx$ và $resid\_oil$. Đây là những biến động "lọc" sạch tầm ảnh hưởng của chu kỳ kinh doanh.
2.  **Mô hình Log-Log đa biến chính xác:**
    $$\ln(TC) = \alpha + \beta_{Q} \ln(Q) + \varepsilon_{oil} \cdot resid\_oil + \varepsilon_{fx} \cdot resid\_fx + \gamma \cdot Covid$$
3.  **Hệ số Đòn bẩy Cốt lõi (Core DOL):**
    $$DOL_{core} = \frac{Q - \beta_{Q} \cdot TC}{EBIT}$$

**Thông số đo lường thực tế (Cập nhật FWL):**
- **$\varepsilon_{oil} \approx 3.84\%$:** Mỗi 1% cú sốc giá dầu "thuần túy" làm phình Tổng chi phí thêm ~3.84%.
- **$\varepsilon_{fx} \approx 66.26\%$:** Mỗi 1% biến động tỷ giá "ngoại sinh" cực kỳ nguy hiểm, làm tăng chi phí tới ~66.26% (phản ánh đòn bẩy nợ USD rất lớn).
- **$\beta_{Q} \approx 0.78$:** Hiệu quả quy mô (Scale economy) – khi doanh thu tăng 1%, chi phí vận hành chỉ tăng 0.78%.

---

## VI. GIẢI ĐÁP CÁC CÂU HỎI QUẢN TRỊ

### 1. "Phân tích tại một thời điểm có vô nghĩa khi tham số liên tục thay đổi?"

**KHÔNG** — Có ba tầng phân tích bổ trợ nhau:

| Tầng | Công cụ | BEP biến động có ảnh hưởng? |
|---|---|---|
| **Tác chiến** (1 quý) | Sliders Cú sốc (Tab 4) | Không — BEP quý này đã xác định |
| **Chiến lược** (3-5 năm) | Ma trận Nhạy cảm 3b | Có — What-if toàn dải kịch bản |
| **Dài hạn** (15 năm) | Hồi quy Log-Log | Có — Phân tích xu hướng cấu trúc |

### 2. "Tại sao biên lợi nhuận không tăng vọt sau khi hòa vốn?"

Vì $EBIT\ Margin$ tiệm cận **trần cứng** $(1 - v)$. Tại HVN:
- $v \approx 75-80\%$ (nhiên liệu + phí sân bay + lương)
- → Trần lý thuyết `~20-25%` — **không thể vượt qua dù doanh thu tăng vô hạn**

---

## VII. CHIẾN LƯỢC NÂNG TRẦN LỢI NHUẬN

Để kéo đường cong biên lợi nhuận lên cao (nâng trần $(1-v)$) hoặc dịch BEP sang trái:

| Đòn bẩy | Tác động toán học | Biểu hiện trên Dashboard |
|---|---|---|
| **Tăng Yield (giá vé/km)** | Tăng Revenue mà không tăng $v$ | Điểm 2025 dịch sang phải trên đường cong |
| **Revenue Mix** | Giảm $v$ thuần (ancillary thấp chi phí) | Trần lý thuyết $(1-v)$ dịch lên trên |
| **Tái cấu trúc Định phí** | Giảm $F$ → BEP dịch sang trái | Đường BEP dịch trái, EBIT dương sớm hơn |
| **Hedging Giá dầu/FX** | Khóa $v$ thấp, giảm biến động | Đường cong Sốc gần sát đường cong Base |

---

> [!TIP]
> **Kết luận:** Quản trị HVN không phải là chờ đợi một điểm cố định, mà là **chủ động quản lý cấu trúc chi phí** để dịch chuyển BEP sang trái và nâng trần $(1-v)$ của đường cong lợi nhuận trước các biến số vĩ mô.

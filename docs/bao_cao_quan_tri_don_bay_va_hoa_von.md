# BÁO CÁO QUẢN TRỊ: ĐÒN BẨY HOẠT ĐỘNG & ĐIỂM HÒA VỐN
## Vietnam Airlines (HVN) — Phiên bản FWL Log-Log v2.0

> **Phạm vi:** Phân tích cấu trúc chi phí, Điểm hòa vốn, Đòn bẩy hoạt động và Nhạy cảm Vĩ mô cho HVN qua 15 năm (2010–2024).  
> **Phương pháp:** Hồi quy Log-Log với Trực giao hóa Frisch-Waugh-Lovell (FWL-OLS).  
> **Đồng bộ với:** `calculator.py` → `MACRO_REGRESSION.json`, `app.py` (Tab 4).

---

## I. TÓM TẮT QUẢN TRỊ (EXECUTIVE SUMMARY)

| Chỉ số cốt lõi | Giá trị thực tế | Diễn giải |
|---|---|---|
| **ε_oil (Độ co giãn Dầu)** | **3.84%** | +1% giá dầu → Tổng chi phí tăng thêm 3.84% |
| **ε_fx (Độ co giãn Tỷ giá)** | **66.26%** | +1% tỷ giá → Tổng chi phí tăng thêm 66.26% |
| **β_Q (Hệ số Sản lượng)** | **0.783** | Scale economy — chi phí tăng chậm hơn doanh thu |
| **DOL Cốt lõi** | **3.64x** | 1% tăng DT → EBIT tăng 3.64% (sau khi lọc nhiễu vĩ mô) |
| **DFL Cốt lõi** | **1.10x** | Đòn bẩy tài chính thấp, nợ không khuếch đại quá mức |
| **DTL (Đòn bẩy Tổng hợp)** | **4.00x** | DTL = DOL × DFL |
| **R² Mô hình** | **98.68%** | Mô hình giải thích 98.68% biến động chi phí lịch sử |
| **BEP Mỏ neo (Base 2025)** | **~72.519 tỷ VND** | Ngưỡng hòa vốn tại điều kiện vĩ mô cơ sở |

> [!IMPORTANT]
> **Phát hiện chiến lược:** HVN nhạy cảm với Tỷ giá cao gấp **17 lần** so với Giá dầu (66.26% vs 3.84%). Rủi ro ngoại hối — không phải nhiên liệu — mới là mối đe dọa lợi nhuận hàng đầu.

---

## II. NỀN TẢNG LÝ THUYẾT: ĐIỂM HÒA VỐN & ĐÒN BẨY

### 1. Phương trình Điểm hòa vốn (BEP)

$$BEP = \frac{F}{1 - v} = \frac{F}{CM\_Ratio}$$

| Biến số | Định nghĩa | Thực tế HVN 2024 |
|---|---|---|
| **F (Định phí)** | Khấu hao TSCĐ + Chi phí Bán hàng + QLDN | ~49.000 tỷ VND |
| **v (Tỷ lệ biến phí biên)** | $v = VC / Revenue$ | ~75–80% |
| **CM Ratio** | $1 - v$ = Biên đóng góp | ~20–25% |
| **BEP** | Doanh thu tối thiểu để EBIT ≥ 0 | ~72.519 tỷ VND |

Việc phân tách này rất quan trọng: hệ thống **không** đọc trực tiếp từ báo cáo tài chính vì báo cáo không phân chia Định phí/Biến phí. Thay vào đó, hệ thống suy ngược:
$$VC_{base} = R_{base} - EBIT_{base} - F_{base}$$

### 2. Hai cấp độ BEP

**Chế độ 1 — Hòa vốn Hoạt động (EBIT-based):**
$$BEP_{EBIT} = \frac{F}{1 - v}$$
→ Ngưỡng HVN bắt đầu có lãi vận hành.

**Chế độ 2 — Hòa vốn Phục vụ Nợ (Debt-Service):**
$$BEP_{Debt} = \frac{F + Nợ\ ngắn\ hạn + Lãi\ vay}{1 - v}$$
→ Ngưỡng HVN không vỡ nợ kỹ thuật dù đang lãi vận hành.

> [!IMPORTANT]
> Khoảng cách $(BEP_{Debt} - BEP_{EBIT})$ là **"vùng nguy hiểm"** — doanh nghiệp có lợi nhuận hoạt động nhưng vẫn có thể vỡ nợ nếu dòng tiền không đủ trả nghĩa vụ tài chính.

### 3. Tính chất toán học của Đòn bẩy

**Hàm tiệm cận của Biên EBIT:**
$$EBIT\ Margin \xrightarrow{R \to \infty} (1 - v) \approx 20-25\%$$
HVN có trần lợi nhuận lý thuyết ~20–25% và **không thể vượt qua dù doanh thu tăng vô hạn**.

**Hàm hội tụ của DOL:**
$$DOL = \frac{R \cdot (1-v)}{EBIT} = \frac{1}{1 - \frac{F}{R(1-v)}} \xrightarrow{R \to \infty} 1.0x$$

| Khoảng cách tới BEP | DOL | Ý nghĩa |
|---|---|---|
| Gần BEP (vừa hòa vốn) | → +∞ | 1% tăng DT → lợi nhuận tăng vô hạn lần |
| Xa BEP (doanh thu cao) | → 1.0x | Đòn bẩy bão hòa, mất tác dụng khuếch đại |
| **HVN 2024** | **~23.1x** | Mới thoát khỏi vùng lỗ — rất nhạy với doanh thu |
| **HVN 2025 (dự phóng)** | **~3.64x (core)** | Ổn định hơn sau khi đã xa BEP |

---

## III. MÔ HÌNH HỒI QUY KINH TẾ LƯỢNG (FWL LOG-LOG)

### 1. Vấn đề: Đa cộng tuyến trong hồi quy thông thường

Trong giai đoạn 2010–2024, cả 3 chuỗi số liệu đều có xu hướng tăng dài hạn:
- Revenue ($Q$): tăng theo quy mô đội bay
- Oil Price: biến động theo chu kỳ kinh tế toàn cầu
- FX Rate: mất giá dần theo lạm phát tích lũy

Hồi quy OLS thông thường trên chuỗi non-stationary này dẫn đến **Spurious Regression** — hệ số có thể đạt đến -930.000% (như đã quan sát được), hoàn toàn vô nghĩa về kinh tế học.

### 2. Giải pháp: Định lý Frisch-Waugh-Lovell (FWL)

**Cơ chế nguyên lý:** Thay vì dùng $\ln(FX)$ và $\ln(Oil)$ trực tiếp (chứa cả xu hướng tăng trưởng lẫn cú sốc ngoại sinh), hệ thống trích xuất phần "cú sốc thuần túy" — hoàn toàn độc lập với Revenue.

**Bước 1 — Trích xuất Cú sốc thuần túy:**

$$\ln(FX) = a_1 + b_1 \cdot \ln(Q) + \tilde{\varepsilon}_{fx} \quad \Rightarrow \quad resid_{fx} = \tilde{\varepsilon}_{fx}$$

$$\ln(Oil) = a_2 + b_2 \cdot \ln(Q) + \tilde{\varepsilon}_{oil} \quad \Rightarrow \quad resid_{oil} = \tilde{\varepsilon}_{oil}$$

> **Kiểm chứng tính trực giao:** $corr(resid_{fx}, \ln Q) = 0.0000$ ✅ — FX đã hoàn toàn độc lập với Revenue.

**Bước 2 — Hồi quy chính thức:**

$$\boxed{\ln(TC) = \alpha + \beta_{Q}\ln(Q) + \varepsilon_{oil} \cdot resid_{oil} + \varepsilon_{fx} \cdot resid_{fx} + \gamma \cdot D_{Covid}}$$

**Bước 3 — Tính Đòn bẩy Cốt lõi:**

$$DOL_{core} = \frac{Q - \beta_{Q} \cdot TC}{EBIT}$$

### 3. Kết quả Hồi quy Chính thức (FWL-OLS)

**Bảng Hệ số Hồi quy:**

| Biến số | Ký hiệu | Hệ số | Diễn giải kinh tế |
|---|---|---|---|
| Intercept | $\alpha$ | — | Hằng số cơ sở |
| Sản lượng Doanh thu | $\beta_Q$ | **0.7833** | Scale economy: DT +1% → TC +0.78% |
| Cú sốc Giá Dầu (resid) | $\varepsilon_{oil}$ | **0.03835** | Oil shock +1% → TC +3.84% |
| Cú sốc Tỷ giá (resid) | $\varepsilon_{fx}$ | **0.66263** | FX shock +1% → TC +66.26% |
| Biến giả Covid | $\gamma$ | — | Loại bỏ nhiễu 2020-2022 |

**Bảng Chẩn đoán Chất lượng Mô hình:**

| Chỉ tiêu chẩn đoán | Giá trị | Đánh giá |
|---|---|---|
| R² (Hệ số xác định) | **98.68%** | ✅ Rất cao — mô hình fit tốt |
| corr(resid_fx ⊥ Q) | **0.0000** | ✅ FWL trực giao hoàn hảo |
| corr(resid_oil ⊥ Q) | **0.0000** | ✅ FWL trực giao hoàn hảo |
| max_corr (giữa các biến X) | **0.69** | ✅ Dưới ngưỡng nguy hiểm (0.85) |
| Phương pháp | FWL-OLS | ✅ Không cần Ridge regularization |
| Số quan sát hợp lệ | 15 năm (2010–2024) | ✅ Đủ bậc tự do |

**Kết quả Đòn bẩy Cốt lõi:**

| Đòn bẩy | Giá trị | Công thức |
|---|---|---|
| DOL Cốt lõi | **3.636x** | $(Q - \beta_Q \cdot TC) / EBIT$ |
| DFL Cốt lõi | **1.100x** | $EBIT / (EBIT - IntExp)$ |
| DTL (Tổng hợp) | **4.000x** | $DOL_{core} \times DFL_{core}$ |

---

## IV. CÔNG THỨC TRUYỀN DẪN CÚ SỐC VĨ MÔ

HVN chịu tác động vĩ mô theo **2 kênh tách biệt**, gắn với từng loại chi phí khác nhau:

### Kênh 1: Sốc Giá Dầu → Biến Phí (Variable Cost)
Nhiên liệu Jet A1 là thành phần biến phí lớn nhất.

$$\Delta VC_{oil} = \Delta Oil_{USD} \times 452.4 \text{ tỷ VND}$$

$$VC_{mới} = VC_{cũ} + \Delta VC_{oil}$$

> **Ví dụ:** Giá dầu tăng +$10/thùng → Tổng chi phí tăng thêm 4.524 nghìn tỷ VND.

**Cơ chế lan truyền sang BEP:**
$$v_{mới} = \frac{VC_{mới}}{R_{base}} \uparrow \quad \Rightarrow \quad (1-v_{mới}) \downarrow \quad \Rightarrow \quad BEP_{mới} = \frac{FC}{1-v_{mới}} \uparrow$$

### Kênh 2: Sốc Tỷ Giá → Định Phí (Fixed Cost)
Nghĩa vụ thuê tàu DAMP (Operating Lease) và lãi vay nợ USD được thanh toán bằng ngoại tệ — là chi phí cố định theo hợp đồng.

$$\Delta FC_{fx} = \Delta FX\% \times 533 \text{ tỷ VND}$$

$$FC_{mới} = FC_{cũ} + \Delta FC_{fx}$$

> **Ví dụ:** VND mất giá 2% → Định phí tăng thêm 1.066 nghìn tỷ VND.

**Cơ chế lan truyền sang BEP:**
$$FC_{mới} \uparrow \quad \Rightarrow \quad BEP_{mới} = \frac{FC_{mới}}{1-v} \uparrow$$

### Trạng thái Hoàn chỉnh Sau Cú Sốc

$$EBIT_{mới} = R_{base} - VC_{mới} - FC_{mới}$$

$$BEP_{mới} = \frac{FC_{mới}}{1 - v_{mới}}$$

$$DOL_{mới} = \frac{R_{base} \times (1 - v_{mới})}{EBIT_{mới}}$$

---

## V. MA TRẬN NHẠY CẢM: KẾT QUẢ SỐ LIỆU

### Trạng thái Mỏ neo (Base 2025)
| Tham số | Giá trị |
|---|---|
| Doanh thu cơ sở ($R_{base}$) | ~121.213 tỷ VND |
| Điểm hòa vốn EBIT ($BEP_{base}$) | **~72.519 tỷ VND** |
| Giá Jet A1 gốc | $90/thùng |
| Tỷ giá gốc | 26.300 VND/USD |
| Tỷ lệ nhiên liệu/Opex ($r_{fuel}$) | ~37.5% |
| Tỷ lệ nợ USD ($r_{USD}$) | ~80% |

### Ma trận Dịch chuyển BEP (∆BEP so với Base)

**Chiều Tỷ giá (hàng) vs Giá Dầu (cột), đơn vị: tỷ VND**

| FX \ Oil | −$20 | −$10 | **Base ($90)** | +$10 | +$20 | +$30 |
|---|---|---|---|---|---|---|
| **−2%** | ↓ Tích cực | ↓ Tích cực | ↓ Tích cực | ↑ Nhẹ | ↑ Nhẹ | ↑ Vừa |
| **−1%** | ↓ Tích cực | ↓ Nhẹ | ↓ Nhẹ | ≈ Bình thường | ↑ Nhẹ | ↑ Vừa |
| **Base (0%)** | ↓ Tích cực | ↓ Nhẹ | **~72.519 tỷ** | ↑ 4.524 tỷ | ↑ 9.048 tỷ | ↑ 13.572 tỷ |
| **+1%** | ↑ Nhẹ | ↑ Nhẹ | ↑ 533 tỷ | ↑↑ Nghiêm trọng | ↑↑ | ↑↑ |
| **+2%** | ↑ Vừa | ↑ Vừa | ↑ 1.066 tỷ | ↑↑↑ Nguy hiểm | ↑↑↑ | ↑↑↑ |
| **+5%** | ↑ Nghiêm trọng | ↑ Nghiêm trọng | ↑ 2.665 tỷ | 🔴 Rủi ro cao | 🔴 | 🔴 |

> [!WARNING]
> **Ma trận cho thấy:** Tỷ giá mất giá 1% tạo ra cú sốc chi phí (~533 tỷ) tương đương giá dầu tăng +$1.18/thùng. Kịch bản FX tăng +5% cộng Oil +$20 có thể đẩy BEP lên ~86.000–90.000 tỷ VND — vượt xa doanh thu thực tế.

### Bảng Kịch bản Định lượng Cụ thể

| Kịch bản | ∆Oil | ∆FX | ∆BEP (tỷ VND) | ∆EBIT (tỷ VND) | Mức độ Rủi ro |
|---|---|---|---|---|---|
| **Base** | 0 | 0% | 0 | 0 | — |
| Dầu tăng nhẹ | +$5 | 0% | +2.262 | −2.262 | 🟡 Thấp |
| Dầu tăng vừa | +$10 | 0% | +4.524 | −4.524 | 🟡 Trung bình |
| FX mất giá nhẹ | 0 | +1% | +533 | −533 | 🟡 Thấp |
| FX mất giá vừa | 0 | +2% | +1.066 | −1.066 | 🟡 Trung bình |
| **Kịch bản kép nhẹ** | +$10 | +1% | +5.057 | −5.057 | 🟠 Đáng lo |
| **Kịch bản kép vừa** | +$20 | +2% | +10.114 | −10.114 | 🔴 Nghiêm trọng |
| **Cú sốc cực đoan** | +$30 | +5% | +15.837 | −15.837 | 🔴 Nguy hiểm |

---

## VI. HƯỚNG DẪN ĐỌC DASHBOARD (TAB 4)

### 1. Trục Hồi quy Log-Log (Core Elasticity & Macro Shocks)
| Chỉ số | Giá trị | Cách đọc |
|---|---|---|
| **ε_oil** | 3.84% | Dầu +1% → TC tăng 3.84% (của tổng chi phí) |
| **ε_fx** | 66.26% | Tỷ giá +1% → TC tăng 66.26% (cú sốc ngoại sinh) |
| **DOL Cốt lõi** | 3.64x | 1% ∆DT → 3.64% ∆EBIT (đã loại nhiễu vĩ mô) |
| **DFL Cốt lõi** | 1.10x | Đòn bẩy tài chính ổn định, nợ không khuếch đại bất thường |
| **Phương pháp** | FWL-OLS | ✅ Không cần Ridge — đa cộng tuyến đã được triệt tiêu |

### 2. Biểu đồ Đòn bẩy Hoạt động (Operating Leverage)
| Thành phần | Ý nghĩa |
|---|---|
| **Cột Xanh (Doanh thu)** | Quy mô thực tế (nghìn tỷ VND) |
| **Cột Đỏ (Định phí FC)** | Rào cản chi phí cố định phải vượt qua (Khấu hao + SG&A) |
| **Đường Vàng (EBIT)** | Lợi nhuận thực tế (tỷ VND, trục phải) |

---

### 3. Biểu đồ Dịch chuyển Trần Lợi nhuận (Dual Curve)
Biểu đồ trực quan hóa:
$$EBIT\ Margin = \underbrace{(1 - v)}_{\text{Trần lý thuyết}} - \underbrace{\frac{F}{R}}_{\text{Gánh định phí}}$$

Mỗi cú sốc vĩ mô dịch chuyển **toàn bộ đường cong xuống** và **BEP sang phải**.

---

## VII. PHÂN TẦNG PHÂN TÍCH — CÁCH HỆ THỐNG HOẠT ĐỘNG

| Tầng | Công cụ | Câu hỏi trả lời |
|---|---|---|
| **Tác chiến** (quý) | Sliders Cú sốc (Tab 4) | Nếu hôm nay dầu tăng $X, EBIT thay đổi bao nhiêu? |
| **Chiến lược** (3-5 năm) | Ma trận Nhạy cảm | Kịch bản nào doanh nghiệp không thể hòa vốn? |
| **Dài hạn** (15 năm) | Hồi quy FWL Log-Log | Cấu trúc co giãn chi phí thực sự là gì? |

---

## VIII. CHIẾN LƯỢC QUẢN TRỊ — NÂNG TRẦN LỢI NHUẬN

| Đòn bẩy chiến lược | Tác động toán học | Mức độ ưu tiên |
|---|---|---|
| **Hedging Tỷ giá FX** | Triệt tiêu $\Delta FC_{fx}$ — BEP không bị đẩy khi VND mất giá | 🔴 Ưu tiên số 1 |
| **Cấu trúc lại Nợ USD** | Giảm tỷ lệ $r_{USD}$ → Giảm hệ số 533 tỷ/1% | 🔴 Ưu tiên số 1 |
| **Hedging Giá dầu** | Khóa $v$ thấp → Biên đóng góp ổn định | 🟠 Ưu tiên số 2 |
| **Tăng Yield (giá vé/km)** | Tăng $R$ không tăng $v$ → Điểm xa BEP hơn | 🟠 Ưu tiên số 2 |
| **Revenue Mix Ancillary** | Giảm $v$ thuần → Nâng trần $(1-v)$ | 🟡 Dài hạn |
| **Tái cấu trúc Định phí** | Giảm $F$ → BEP dịch trái, EBIT dương sớm hơn | 🟡 Dài hạn |

---

> [!TIP]
> **Kết luận Quản trị:** HVN đang ở vị trí rủi ro tỷ giá **bất cân xứng**. Với ε_fx = 66.26% — cao gấp 17 lần ε_oil = 3.84% — ưu tiên chiến lược phòng ngừa ngoại hối và tái cấu trúc nợ USD sẽ tạo ra impact lớn hơn nhiều so với hedging nhiên liệu. Mỗi 1% VND giảm giá dẫn tới gánh nặng 533 tỷ VND phụ trội — gần bằng tác động của việc giá dầu tăng +$1.18/thùng.

---

*Tài liệu được đồng bộ tự động với kết quả pipeline: `output/2_calculated/MACRO_REGRESSION.json`*  
*Cập nhật lần cuối: 2026-04-05 | FWL-OLS R²=98.68% | max_corr=0.69 | corr_fx⊥Q=0.0000*

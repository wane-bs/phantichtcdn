# Báo cáo Phương pháp Định giá — Vietnam Airlines (HVN)
**Hệ thống phân tích tài chính HVN | Phiên bản: Tháng 4/2026**

---

## Tổng quan triết lý định giá

> HVN là doanh nghiệp **Vốn chủ sở hữu (VCSH) âm** trong giai đoạn 2022–2024 do lỗ lũy kế hậu Covid. Điều này khiến các phương pháp định giá truyền thống dựa trên Equity (P/B, P/E, ROE) bị **vô hiệu hoá hoàn toàn**. Hệ thống áp dụng triết lý **định giá theo Giá trị Doanh nghiệp (EV — Enterprise Value)** thay vì Giá trị Vốn chủ sở hữu, nhằm bỏ qua nhiễu loạn từ cấu trúc vốn bất thường.

**Chuỗi quy đổi từ EV sang Giá mục tiêu:**

```
EV (Enterprise Value)
 = Vốn hóa thị trường (Market Cap) + Nợ thuần (Net Debt) + Lợi ích CĐ thiểu số

Equity Value = EV − Net Debt − Lợi ích CĐ thiểu số

Giá mục tiêu (VND/CP) = Equity Value / Số CP lưu hành
```

---

## Phương pháp 1: EV/EBITDA Mean Reversion (Dải định giá lịch sử)

### 1.1 Triết lý phương pháp

Phương pháp này dựa trên lý thuyết **hồi quy về giá trị trung bình (Mean Reversion)**: trong dài hạn, bội số EV/EBITDA của một doanh nghiệp sẽ có xu hướng quay về mức trung bình lịch sử khi các điều kiện vĩ mô và vận hành bình thường hóa. Với HVN đang phục hồi sau Covid, giả thuyết này mang tính hợp lý cao.

### 1.2 Thuật toán tính toán (từ `forecaster.py::valuation_bands()`)

**Bước 1–2: Thu thập và lọc chuỗi EV/EBITDA lịch sử**

```python
series = fi['EV/EBITDA'][years].astype(float)

# Lọc nhiễu: Loại bỏ năm EV/EBITDA <= 0 (do EBITDA âm trong Covid)
# và loại các năm VCSH âm (2022–2024) để tránh bội số bị méo
vals = series[(series > 0) & (VCSH > 0)]
```

**Bước 3: Tính phân phối thống kê**

```
μ (mean) = Trung bình chuỗi EV/EBITDA đã lọc
σ (std)  = Độ lệch chuẩn

Dải định giá:
  +2σ → Rất đắt (Overvalued)
  +1σ → Nóng
   μ  → Trung bình lịch sử (Anchor)
  -1σ → Hấp dẫn
  -2σ → Rất rẻ (Undervalued)
```

**Bước 4: Tính EV mục tiêu theo từng dải (có chiết khấu rủi ro)**

```python
EV_lower = EBITDA_2025 × (μ - σ) × (1 - discount)
EV_upper = EBITDA_2025 × (μ + σ) × (1 - discount)
```

> **Chiết khấu rủi ro tái cấu trúc (discount)**: Dashboard cho phép người dùng áp dụng chiết khấu 0–100%, mặc định **40%**, để phản ánh gánh nặng nợ và rủi ro tái cơ cấu VCSH hiện tại.

### 1.3 Dữ liệu lịch sử EV/EBITDA của HVN

| Năm | EV/EBITDA | VCSH | Được lọc vào |
|-----|-----------|------|-------------|
| 2012 | 19.90x | + | ✅ |
| 2015 | 14.42x | + | ✅ |
| 2016 | 12.97x | + | ✅ |
| 2017 | 9.76x | + | ✅ |
| 2018 | 8.08x | + | ✅ |
| 2019 | 8.23x | + | ✅ |
| 2020 | -8.13x | + | ❌ (EBITDA âm) |
| 2021 | -5.92x | + | ❌ (EBITDA âm) |
| 2022 | -12.54x | − | ❌ (Cả hai) |
| 2023 | 24.94x | − | ❌ (VCSH âm) |
| 2024 | 6.40x | − | ❌ (VCSH âm) |
| **2025** | **5.17x** | + | Điểm hiện tại |

**Kết quả phân phối** (7 điểm hợp lệ: 2012, 2015–2019, 2025):

> **Lưu ý:** Năm 2025 (VCSH dương, EV/EBITDA = 5.17x) đã được đưa vào bộ lọc. Cả hai hàm `valuation_bands()` và `dcf_sensitivity()` sử dụng cùng bộ lọc kép: **EV/EBITDA > 0** và **VCSH > 0**.

| Chỉ số | Giá trị |
|--------|---------|
| **μ (Mean)** | **≈ 11.22x** |
| **σ (Std)** | **≈ 4.74x** |
| +2σ | ≈ 20.70x |
| **+1σ** | **≈ 15.96x** |
| **-1σ** | **≈ 6.48x** |
| -2σ | ≈ 1.74x |
| **EV/EBITDA 2025** | **5.17x ← Dưới -1σ** |
| **Band Position** | **~0.15 (Vùng Rẻ, < 0.3)** |

---

## Phương pháp 2: DCF Terminal Value Integration (Ma trận Chiết khấu Dòng tiền)

### 2.1 Triết lý phương pháp

Không dự báo một điểm cụ thể. Xây dựng **ma trận nhạy cảm 2 chiều** (WACC × Tốc độ tăng trưởng EBITDA) để khám phá toàn bộ không gian giá trị hợp lý.

**Kiến trúc mô hình:** Dự phóng FCFF 5 năm *(phần ngắn hạn)* + Terminal Value neo vào **Mean(EV/EBITDA lịch sử)** *(không dùng Gordon Growth vì Terminal Growth vô hạn không phù hợp ngành hàng không)*.

### 2.2 Công thức chi tiết (từ `forecaster.py::dcf_sensitivity()`)

```python
# Tham số:
FCFF_base     = OCF − Capex  (từ LCTM 2025 thực tế)
EBITDA_base   = 14.054k tỷ VND (EBITDA 2025)
multiple      = Mean(EV/EBITDA | EV/EBITDA > 0 AND VCSH > 0) ≈ 11.22x
#               ↑ Đồng nhất bộ lọc với valuation_bands() — bao gồm 2025, loại 2023-2024

for wacc in [8%, 8.5%, ..., 16%]:
    for g in [-2%, -1.5%, ..., 8%]:
        # Tính EV bằng PV(FCFF 5 năm) + PV(Terminal Value)
```

---

## Phương pháp 3: So sánh tương đối — Hệ số P/S

### 3.1 Vì sao chọn P/S

Doanh thu luôn dương và ổn định hơn lợi nhuận trong giai đoạn phục hồi.

```
P/S 2025 = Vốn hóa / Doanh thu thuần ≈ 0.566x
```

### 3.2 Chuỗi lịch sử P/S

| Giai đoạn | P/S | Trạng thái |
|-----------|-----|------------|
| 2016 (Đỉnh) | 0.90x | Đắt |
| 2018-2019 | 0.45x | Rẻ |
| **2025** | **0.57x** | Trung bình |

---

## Phương pháp 4: Football Field Chart — Tổng hợp

Tổng hợp dải giá trị từ các phương pháp để xác định vùng đồng thuận định giá.

| Phương pháp | Giá ước tính (VND/CP) |
|-------------|-----------------------|
| EV/EBITDA -1σ | ~20.500 |
| **Thị trường hiện tại** | **~22.050** |
| EV/EBITDA +1σ | ~43.800 |

> **Kết luận**: Mức giá hiện tại (~22k) nằm ở cận dưới của dải định giá hợp lý, phản ánh sự thận trọng của thị trường trước các rủi ro tái cơ cấu.

---
*Báo cáo được trích xuất tự động từ hệ thống phân tích HVN.*

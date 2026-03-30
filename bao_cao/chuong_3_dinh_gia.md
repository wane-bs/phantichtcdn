# CHƯƠNG 3: Định giá Doanh nghiệp — Enterprise Value Framework

Việc định giá một hãng hàng không ngay sau khủng hoảng tồn vong là bài toán phức tạp hàng đầu trong phân tích tài chính. Phương pháp truyền thống (P/E, P/B) đã **hoàn toàn mất hiệu lực** do vốn chủ sở hữu âm và lợi nhuận ròng thất thường. Chương này áp dụng **khung định giá Enterprise Value (EV)** — chuẩn mực quốc tế cho doanh nghiệp Distress/Turnaround.

## 1. Tại sao P/E và P/B mất hiệu lực?

> [!CAUTION]
> **Các chỉ số bị cách ly (Neutralized Metrics)**
> - **P/B (Price-to-Book):** VCSH âm sâu từ 2022 đến 2024 khiến P/B mang giá trị âm — vô nghĩa về mặt toán học lẫn kinh tế. Năm 2025 dù BV dương trở lại, P/B vọt tới ~11.39x do mẫu số quá nhỏ.
> - **P/E (Price-to-Earnings):** Lợi nhuận ròng có tính chu kỳ cực mạnh (âm sâu 2020-2023, vọt dương 2024-2025). P/E ~7-9x tạo **ảo giác cổ phiếu rẻ** mà bỏ qua rủi ro cấu trúc.
> - **ROE:** Khi VCSH âm, ROE dương nghịch lý (chia số âm cho số âm), tạo **tín hiệu giả dương** cực kỳ nguy hiểm.
>
> → Hệ thống đã **tự động gán NaN** cho toàn bộ các chỉ số trên tại các năm bị ảnh hưởng.

## 2. Phương pháp Thay thế: EV/EBITDA Mean Reversion

**EBITDA** (Lợi nhuận trước lãi vay, thuế và khấu hao) bóc tách các yếu tố cấu trúc vốn và chính sách kế toán, phản ánh khả năng tạo tiền cốt lõi từ hoạt động bay. **EV** (Enterprise Value = Vốn hóa + Nợ vay thuần) đo lường giá trị toàn bộ doanh nghiệp — bao gồm cả phần thuộc về chủ nợ.

### Kết quả phân tích EV/EBITDA qua 12 năm:

| Giai đoạn | EV/EBITDA | Nhận định |
|---|---|---|
| 2012 – 2019 (Ổn định) | 8x – 20x | Mức bình thường cho ngành hàng không truyền thống |
| 2020 – 2023 (Khủng hoảng) | Âm / Bất thường | EBITDA âm làm bội số mất ý nghĩa |
| 2024 – 2025 (Phục hồi) | **5.2x – 6.4x** | Rẻ hơn đáng kể so với trung bình lịch sử |

Hệ thống sử dụng phương pháp **Mean Reversion** — giả định bội số sẽ hồi quy về giá trị trung bình (Mean) ± độ lệch chuẩn (σ) qua chuỗi 12 năm — để xác định dải định giá hợp lý.

## 3. Mô hình DCF — Terminal Value Integration

Thay vì áp dụng mô hình Gordon Growth cơ bản (V = FCFF/(WACC-g)) dễ gãy khi g ≈ WACC, hệ thống triển khai mô hình kết hợp:

**Bước 1:** Dự phóng dòng tiền tự do (FCFF) trong 5 năm tới dựa trên tốc độ tăng trưởng EBITDA.

**Bước 2:** Tính Terminal Value tại năm cuối:
$$TV_n = EBITDA_n \times Mean(EV/EBITDA_{lịch sử})$$

**Bước 3:** Chiết khấu toàn bộ các dòng FCFF và TV về hiện tại bằng WACC:
$$EV = \sum_{t=1}^{5} \frac{FCFF_t}{(1+WACC)^t} + \frac{TV_5}{(1+WACC)^5}$$

**Ưu điểm:** Giá trị doanh nghiệp vừa phản ánh khả năng tạo tiền nội tại, vừa phản ánh cách thị trường thường định giá HVN qua các chu kỳ.

Ma trận độ nhạy WACC × EBITDA Growth trên Dashboard cho phép nhà phân tích stress-test hàng trăm kịch bản định giá đồng thời.

## 4. Football Field Chart — Kết luận Dải Giá trị

Hai phương pháp trên được tổng hợp vào biểu đồ **Football Field Chart** — chuẩn mực của báo cáo Equity Research:

- **Thanh 1 (EV/EBITDA ±1σ):** Dải giá trị doanh nghiệp dựa trên chuẩn hóa bội số lịch sử.
- **Thanh 2 (DCF TV Integration):** Dải giá trị từ ma trận chiết khấu dòng tiền.
- **Đường neo (Current EV):** Enterprise Value thực tế hiện tại.

> [!IMPORTANT]
> **Quy tắc đọc Football Field:**
> - Nếu EV hiện tại nằm **dưới** vùng giao thoa → Tín hiệu **Undervalued** (định giá thấp)
> - Nếu EV hiện tại nằm **trên** vùng giao thoa → Tín hiệu **Overvalued** (định giá cao)
> - Vùng giao thoa = vùng đồng thuận giá trị hợp lý (Fair Value Zone)

## 5. Tiểu kết

Ở mức EV/EBITDA 5.2x – 6.4x, cổ phiếu HVN đang được đánh giá là **khá rẻ so với giá trị nội tại lịch sử và xu hướng phục hồi**. Tuy nhiên, đây là trường hợp **Turnaround Valuation** — toàn bộ kịch bản phục hồi đứng trên giả định dòng biên EBITDA vượt chi phí vốn và lộ trình tái cấu trúc Nợ.

Nhà đầu tư cần đồng thời tham chiếu **DSCR** (Chương 4) và **Liquidity Runway** để đánh giá liệu doanh nghiệp có đủ sức chịu đựng một cú sốc thanh khoản mới trước khi giá trị hội tụ về vùng Mean.

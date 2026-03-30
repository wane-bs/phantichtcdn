# CHƯƠNG 4: Đánh giá Rủi ro Tín dụng — Góc nhìn Người cho vay

Khi đứng trên cương vị của một ngân hàng hoặc trái chủ cấp vốn cho Vietnam Airlines, bức tranh tài chính mang nhiều màu sắc hỗn hợp: Băng qua bờ vực phá sản, nhưng cấu trúc bảo đảm rủi ro (Margin of Safety) vẫn rất mỏng.

Chương này tập trung đong đếm Rủi ro Tín dụng (Credit Risk) qua các chỉ số **dòng tiền cốt lõi** — thay vì dựa trên chỉ số bảng cân đối kế toán truyền thống (đã bị nhiễu bởi VCSH âm).

## 1. Khả năng Phục vụ Nợ — DSCR (Debt Service Coverage Ratio)

Chỉ số DSCR đo lường khả năng dòng tiền hoạt động (CFO) trang trải cho toàn bộ nghĩa vụ nợ gốc và lãi:

$$DSCR = \frac{CFO}{Nợ\_gốc\_đáo\_hạn + Lãi\_vay}$$

> [!NOTE]
> **Quy tắc đánh giá DSCR:**
> - DSCR > 1.5x: **An toàn** — dòng tiền thừa sức trả nợ
> - DSCR = 1.0x – 1.5x: **Biên mỏng** — cần theo dõi chặt
> - DSCR < 1.0x: **Nguy hiểm** — phải vay đảo nợ để tồn tại

Trong giai đoạn 2020-2023, DSCR của HVN thường trực dưới 1.0x (dòng tiền không đủ trả nợ), phản ánh chính xác mức độ phụ thuộc vào hỗ trợ tín dụng Nhà nước. Sự phục hồi về trên 1.0x từ 2024-2025 cho thấy hãng đã tự chủ được nghĩa vụ nợ từ hoạt động bay.

## 2. Stress-Test: DSCR dưới Kịch bản Sốc

Hệ thống thực hiện giả lập **kịch bản Sốc thanh khoản**: CFO giảm 30%, Lãi vay tăng 20%. Kết quả Stressed DSCR cho thấy biên an toàn thực sự của doanh nghiệp khi gặp biến cố (giá dầu tăng, tỷ giá bất lợi, sụt giảm sản lượng hành khách).

> [!WARNING]
> **Ranh giới DSCR = 1.0x**
> Trên Dashboard (Tab 1), đường DSCR nét liền (Bình thường) và nét đứt (Sốc) cho phép trực quan hóa mức độ dễ tổn thương. Nếu Stressed DSCR vẫn > 1.0x, doanh nghiệp có khả năng chống chịu. Ngược lại, chủ nợ cần thắt chặt hạn mức.

## 3. Cấu trúc Nợ Gộp (Gross Debt Analytics)

Thay vì chỉ nhìn Nợ/VCSH (đã bị nhiễu do VCSH âm), hệ thống chuyển sang 2 chỉ số chuẩn quốc tế:

### a. CFO / Gross Debt (%)
- Đo lường tốc độ "trả sạch" toàn bộ nợ vay bằng dòng tiền hoạt động.
- CFO/Gross Debt > 20%: Trả hết nợ trong ~5 năm bằng CFO.
- CFO/Gross Debt < 10%: Cấu trúc nợ quá nặng so với khả năng tạo tiền.

### b. Gross Debt / EBITDA (x)
- Đo lường "gánh nặng nợ" tương đối với hiệu suất vận hành.
- Gross Debt/EBITDA < 4x: Mức chấp nhận được cho ngành thâm dụng vốn.
- Gross Debt/EBITDA > 6x: Rủi ro tín dụng cao, khó tiếp cận thị trường vốn.

## 4. Liquidity Runway — Thước đo Sinh tồn tối thượng

Chỉ số Liquidity Runway trả lời câu hỏi: "**Nếu doanh nghiệp không tạo ra doanh thu nào nữa, số tháng tối đa hãng có thể tồn tại là bao nhiêu?**"

$$Runway = \frac{Tiền\_mặt + TSNH\_thanh\_khoản\_cao}{\chi_{Chi\_phí\_cố\_định\_hàng\_tháng}}$$

> [!IMPORTANT]
> **Ngưỡng sinh tồn:**
> - Runway > 12 tháng: Hãng có đệm an toàn cho 1 năm đóng cửa (chuẩn Basel).
> - Runway 6 – 12 tháng: Cần kế hoạch dự phòng thanh khoản khẩn cấp.
> - Runway < 6 tháng: **Nguy hiểm tức thời** — bất cứ cú sốc đột ngột nào cũng có thể dẫn đến mất thanh khoản.

## 5. Khả năng trang trải lãi vay (ICR)

Chỉ số ICR (EBIT / Chi phí lãi vay) vẫn là thước đo bổ trợ quan trọng:
- **Giai đoạn 2020-2023:** ICR âm sâu (thấp nhất -16.03x năm 2021). Hãng phải vay đảo nợ để trả lãi.
- **Giai đoạn 2024-2025:** ICR nhảy vọt lên **5.3x – 11.0x**. Doanh nghiệp tạo ra 11 đồng EBIT chỉ cần trả 1 đồng lãi vay.

## 6. Đề xuất cho Chủ nợ

1. **Tái cấu trúc kỳ hạn Nợ:** Nợ ngắn hạn chiếm ~84% tổng nợ → phát hành trái phiếu dài hạn để đảo kỳ hạn xuống dưới 40%.
2. **Xây dựng Cash Buffer:** Duy trì tỷ lệ Tiền mặt đủ cho 6 tháng chi phí cố định.
3. **Covenant dựa trên DSCR:** Thiết lập ngưỡng DSCR tối thiểu = 1.2x trong các hợp đồng tín dụng mới.

---

**Tiểu kết:** Từ góc nhìn tín dụng, HVN đã thoát khỏi vùng nguy hiểm với ICR và DSCR dương trở lại. Tuy nhiên, cấu trúc nợ ngắn hạn quá lớn là "quả bom nổ chậm" đối với rủi ro tái cấp vốn. Chủ nợ cần theo dõi **Stressed DSCR** và **Liquidity Runway** thay vì Nợ/VCSH truyền thống.

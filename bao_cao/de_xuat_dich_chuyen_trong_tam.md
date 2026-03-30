# BÁO CÁO ĐỀ XUẤT: NHÓM CHỈ SỐ DỊCH CHUYỂN TRỌNG TÂM ĐỊNH GIÁ

**Dự án:** Phân tích Tài chính HVN
**Đặc thù doanh nghiệp:** Kinh doanh vận tải hàng không (Airlines / Capital Intensive), hiện đang trong giai đoạn Vốn chủ sở hữu âm (Negative Equity) nhưng dòng tiền hoạt động (OCF) vẫn thặng dư do đặc thù khấu hao lớn và thu tiền vé trước (CCC âm).
**Tài liệu tham chiếu:** Best-practices về đo lường rủi ro tài chính nhóm Airlines Distress.

---

## 1. Cơ sở lập luận (Rationale)

Khi một hãng hàng không rơi vào trạng thái VCSH âm, các chỉ số định giá tài sản ròng gốc (P/B, ROE) hoàn toàn mất ý nghĩa do mẫu số bị lật ngược. Nhà đầu tư không còn mua "tài sản ròng hiện tại", mà họ đang mua:
1. **Khả năng sống sót qua cơn khủng hoảng (Runway / Liquidity).**
2. **Khả năng tạo dòng tiền để phục vụ nợ (Cash Flow for Debt Service).**
3. **Giá trị doanh nghiệp độc lập với cấu trúc vốn (EV/EBITDA).**

Do đó, hệ thống cần **dịch chuyển trọng tâm** từ nhóm *Định giá Cổ phiếu (Equity Valuation)* sang nhóm *Định giá Doanh nghiệp & Thanh khoản Động (Enterprise & Liquidity)*.

---

## 2. Nhóm Chỉ số ĐÃ CÓ trong hệ thống (Keep & Highlight)

Hệ thống hiện tại (trong `calculator.py`) đã tính toán một số chỉ báo phù hợp, cần được giữ nguyên và **chuyển lên highlight ở Tab 4**:

| Tên Mô tả | Ý nghĩa thay thế | Mapping gốc |
| :--- | :--- | :--- |
| **OCF (Dòng tiền thuần từ HĐKD)** | Thay thế cho LNST, phản ánh sức mạnh kiếm tiền thực để trả nợ. | `CASH FLOW STATEMENT` -> `Lưu chuyển tiền thuần từ các hoạt động sản xuất kinh doanh` |
| **FCFF (Free Cash Flow to Firm)** | Dòng tiền tự do để trả nợ. | Bằng `OCF - CAPEX` (`Tiền mua tài sản cố định`). |
| **Net Debt / EBITDA** | Số năm cần để EBITDA trả sạch nợ ròng. | Tự động tính ở Method 5 trong `calculator.py` |
| **Cash Ratio** | Đo lường khả năng thanh toán ngay lập tức không cần thanh lý tàu bay. | `FINANCIAL INDEX` -> `Chỉ số thanh toán tiền mặt` |

---

## 3. Nhóm Chỉ số CHƯA CÓ Cần Bổ Sung (Add & Build)

Dựa trên nghiên cứu chuẩn mực đánh giá rủi ro hàng không, đây là các chỉ báo lõi cần code bổ sung vào pipeline:

### 3.1. DSCR (Khả năng Tự phục vụ nợ bằng Dòng tiền)
Đo lường năng lực dùng tiền mặt kiếm được để trả lãi và nợ gốc đến hạn. Hệ số này < 1.0 nghĩa là hãng bay phải vay thêm nợ mới để trả nợ cũ.
- **Công thức:** `CFO / (Lãi vay + Nợ ngắn hạn)`
- **Mapping Data `hvn.xlsx`:**
  - Tử số: Giữ nguyên `CFO` (Lưu chuyển tiền thuần từ HĐKD)
  - Mẫu số 1: `INCOME STATEMENT` -> `Chi phí lãi vay` (Lấy trị tuyệt đối)
  - Mẫu số 2: `BALANCE SHEET` -> `Nợ ngắn hạn`

### 3.2. Gross Debt / EBITDA (Nợ Gộp / Sức mạnh HĐKD)
Net Debt / EBITDA dễ bị bóp méo nếu công ty tích trữ tiền mặt từ việc đi vay. Gross Debt phản ánh quy mô gánh nặng nợ chéo thực sự của cấu trúc máy bay.
- **Công thức:** `(Nợ ngắn hạn + Nợ dài hạn) / EBITDA`
- **Mapping Data `hvn.xlsx`:**
  - Tử số: `BALANCE SHEET` -> `Nợ ngắn hạn` + `Nợ dài hạn`
  - Mẫu số: `INCOME STATEMENT` -> `EBITDA` (Giá trị Back-calculated ở Method 1)

### 3.3. CFO to Total Debt (Lưu chuyển tiền HĐKD / Tổng nợ)
Cho biết mỗi năm dòng tiền lõi cover được bao nhiêu phần trăm tổng dư nợ. Tỷ lệ này < 15% là rủi ro cực cao.
- **Công thức:** `CFO / (Nợ ngắn hạn + Nợ dài hạn)`
- **Mapping Data `hvn.xlsx`:**
  - Như trên.

### 3.4. Liquidity Runway (Tháng Sinh Tồn)
Chỉ số stress-test độc quyền: Nếu máy bay hoàn toàn nằm đất (CFO = 0), HVN sống được bao nhiêu tháng với lượng tiền mặt hiện có.
- **Công thức:** `(Tiền mặt + Đầu tư ngắn hạn) / [ (Chi phí QLDN + Chi phí Bán hàng + Lãi vay) / 12 ]`
- **Mapping Data `hvn.xlsx`:**
  - Tử số: `BALANCE SHEET` -> `Tiền và tương đương tiền` + `Giá trị thuần đầu tư ngắn hạn`
  - Mẫu số: `INCOME STATEMENT` -> Tổng hợp `Chi phí quản lý` + `Chi phí bán hàng` + `Chi phí lãi vay` (quy ra chi phí cố định hàng tháng).

---

## 4. Kết luận Thiết kế UI (Trọng tâm cập nhật `app.py`)

1. **Với các năm tài chính bị gắn cờ VCSH Âm (VD 2022-2024):**
   - Hủy hoàn toàn cột/chart của P/E, P/B, ROE.
   - Thêm banner: *"Valuation Mode: DISTRESS (Chế độ tái cấu trúc)"*.
2. **Tab 4 (Hiệu suất Mẫu hình):**
   - Thay vì vẽ DuPont, hãy vẽ biểu đồ **"CFO to Debt"** và **"Runway"**.
   - Vẽ Combo Bar/Line cho DSCR, hiển thị đường Threshold y=1.0. Nếu vạch dưới 1 đỏ, HVN đang đốt tiền để gồng nợ.

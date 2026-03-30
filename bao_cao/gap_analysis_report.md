# Báo Cáo Phân Tích Hiện Trạng Hệ Thống HVN so với Tài Liệu Định Hướng

**Tài liệu tham chiếu:** 
- `ham_y_phan_tich.txt`
- `context_chuyen_giao.md`

Tài liệu này đánh giá mức độ hoàn thiện của code base hiện tại (`app.py`, `calculator.py`, `business_classifier.py`...) trong dự án phân tích tài chính HVN.

---

## 1. Mức Độ Đáp Ứng Điều Kiện Trong `ham_y_phan_tich.txt`

Tài liệu `ham_y_phan_tich.txt` đưa ra 3 hàm ý quan trọng dành cho doanh nghiệp đặc thù như HVN (vươn mình khỏi VCSH âm). Code hiện tại **hầu như chưa đáp ứng** trọn vẹn tinh thần này:

### 1.1. Phá vỡ tính liên tục của các chỉ số (Neutralize Data)
- **Đánh giá:** 🔴 **CHƯA ĐÁP ỨNG**
- **Thực trạng:** Trong module `calculator.py` (Method 1 tính P/E, P/B; Method 7 tính ROE DuPont), công thức chia tỷ số vẫn giữ nguyên.
- **Vấn đề:** Khi Vốn chủ sở hữu (VCSH) âm và Lợi nhuận âm, việc giữ công thức gốc khiến giá trị ROE có thể ra "dương giả tạo", P/B mang giá trị âm vô nghĩa. Tương tự, CCC luôn âm. Hệ thống hiện không có exception/logic bắt điều kiện `VCSH < 0` để null hoá hoặc gán nhãn `N/A` nhằm tránh làm nhiễu biểu đồ.
- **ý kiến:** quét các chỉ số gặp rủi ro dương giả - âm giả và tạo 1 báo cáo cảnh báo, với các chỉ số bị dương giả hay âm giả thì thông báo trên giao diện và không tạo biểu đồ phân tích hay các mô hình/ phương pháp phân tích sau.

### 1.2. Sự chuyển dịch trọng tâm Định giá sang Dòng tiền
- **Đánh giá:** 🟡 **ĐÁP ỨNG ĐƯỢC MỘT NỬA**
- **Thực trạng:** Hệ thống đã bắt đầu tập hợp các chỉ số `Net Debt / EBITDA`, `OCF / ICF / FCF` và Biến động `Thực thu - Thực chi` tại tab **Cơ cấu Tài chính** đúng như yêu cầu "Cash Flow for Debt Service".
- **Vấn đề:** Mặc dù đã tính toán nhóm dòng tiền, nhưng chưa nhóm (group) và làm nổi bật chúng như là "chỉ báo định giá thay thế". Dashboard hiện tại vẫn render nhóm Valuation cốt lõi (P/B, P/E) ở Tab "Hiệu suất Mẫu hình" đều đặn cho HVN dù chúng đang bị nhiễu.
- **ý kiến:** tạo báo cáo đề xuất nhóm chỉ số đáp ứng hàm ý dịch chuyển trọng tâm đã có và chưa có trong chương trình. các đề xuất đi kèm cơ sở lập luận, hàm ý và kết luận.

### 1.3. Nhận diện "Tín hiệu tái cấu trúc" (Chuyển giao vs Rủi ro tuyệt đối)
- **Đánh giá:** 🔴 **CHƯA ĐÁP ỨNG**
- **Thực trạng:** Ở dòng 154-178 file `business_classifier.py`, module xử lý rất rập khuôn. Nếu phát hiện VCSH âm hoặc Altman Z < 1.1, nó in ra cảnh báo: *"Khủng hoảng cơ cấu vốn (Rủi ro vỡ nợ cao)"* và *"KHÔNG NÊN ĐẦU TƯ"*.
- **Vấn đề:** Điều này sai hàm ý gốc của bài toán kinh tế. Hàm ý yêu cầu nhận diện đó là sự biến động của chu kỳ thâm dụng/khủng hoảng có tính chất **"chuyển giao"** và tái cấu trúc dài hạn, không phải gán cờ phá sản tuyệt đối vào doanh nghiệp (HVN).

---

## 2. Khoảng Gap So Với Phương Hướng Tại `context_chuyen_giao.md`

`context_chuyen_giao.md` (Phase 2) nhấn mạnh việc đưa giao diện sang mô hình "Business Model-driven Dashboard". Khoảng gap kiến trúc hiện tại khá lớn:

### 2.1. Gap Kiến trúc Module (Architectural Gap)
- **Kế hoạch Phase 2:** Build module `business_classifier.py` chạy trước, để hai module `ui_architect.py` & `ui_templates.py` đóng vai trò điều hướng Template tương ứng cho App.
- **Thực trạng:** **Vi phạm thiết kế tách lớp (Tight Coupling).** Hai file `ui_architect` và `ui_templates` không hề được tạo ra. Module `app.py` hiện tại là một file khổng lồ (>1000 lines), chứa toàn bộ lệnh logic UI tĩnh (`if/else` để render biểu đồ).

### 2.2. Gap Tổ chức Nhóm Biểu Đồ (UI/UX)
- Giao diện đã đổi tên 6 Tabs thành công (Cơ cấu Tài chính, Chất lượng BCTC...), tuy nhiên **chức năng điều hướng động thì thất bại**:
- Tại **Tab 4 (Hiệu suất Mẫu hình)**: Theo kế hoạch, Tab này chỉ được "chuyên biệt" hóa hiển thị biểu đồ tuỳ theo mẫu hình (VD: Thâm dụng vốn thì hẵng vẽ FAT, Bán lẻ hẵng vẽ ITO...). Nhưng code hiện tại vẫn chèn cứng tất cả Ratios (Valuation, Sinh lời DuPont, Liquidity, Solvency) vào Tab 4 không chừa một doanh nghiệp nào. Logic động duy nhất là đoạn code check ITO/FAT ở cuối thẻ.

### 2.3. Sự cải thiện về Logic Tính toán
- **Thực trạng (Tích cực):** Module `calculator.py` **đã thu hẹp gap mạnh mẽ** ở yêu cầu tính toán. Đã chuyển các mẫu số tỷ suất (Vòng quay, Biên LN, ROA, ROE) sang đo lường bằng Số dư bình quân hai kỳ (`_average_balance`), giúp phản ánh dòng tiền mượt mà và chính xác hơn hệ thống của Phase 1.

---

## 3. Tổng Kết & Hành Động Tiếp Theo (Action Items)

1. **Ở mức độ Dữ liệu (Backend):** 
   - Sửa `calculator.py` bổ sung logic bắt `VCSH < 0` tại method 1 và 7, loại bỏ triệt để các kết quả trả về vô lý cho P/E, P/B, ROE.
   - Sửa `business_classifier.py` để bổ sung nhãn "Tái cấu trúc / Chuyển Giao" thay vì kết luận "Phá sản/Rủi ro" ở case HVN.
2. **Ở mức độ Giao diện (Frontend):** 
   - Tách UI của `app.py` ra làm file `ui_templates.py` như định hướng của Phase 2.
   - Thay đổi logic hiển thị Tab 4 sang động 100% dựa trên core_model được return từ Classifier.

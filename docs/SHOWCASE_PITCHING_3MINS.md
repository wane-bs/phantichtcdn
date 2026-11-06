# KỊCH BẢN THUYẾT TRÌNH SHOWCASE BATTLE 3 PHÚT: NGHIÊN CONNECT #6
## Dự án: Enterprise Financial Intelligence Platform (Vietnam Airlines - HVN)
**Người trình bày**: Builder Mr.Híu (Nguyễn Trung Hiếu)  
**Thời lượng**: Đúng 180 giây (3 phút) | **Mục tiêu**: Thuyết phục Ban giám khảo & Cộng đồng Nghiên AI bình chọn Top 3 xuất sắc nhất.

---

### I. TIMELINE CHI TIẾT TỪNG GIÂY (THE 180-SECOND PITCH)

```mermaid
flowchart LR
    P1["00:00 - 00:40<br/>VẤN ĐỀ & BỐI CẢNH<br/>Nỗi đau C-Suite HVN"] --> P2["00:40 - 01:50<br/>LIVE DEMO TRÊN LOVABLE<br/>Thanh trượt Macro & EBIT"]
    P2 --> P3["01:50 - 02:30<br/>KIẾN TRÚC FULL-STACK<br/>Local Engine ↔ Lovable MCP"]
    P3 --> P4["02:30 - 03:00<br/>TẦM NHÌN & KẾT THÚC<br/>Kêu gọi bình chọn Top 3"]
```

---

#### ⏱️ [00:00 - 00:40] MỞ ĐẦU & VẤN ĐỀ (Hook & Problem)
- **Lời thoại gợi ý**:
  > *"Chào anh Khải Hoàn, các mentor và toàn thể anh em builder tại Nghiên Connect #6!  
  > Là một builder theo đuổi định hướng AI Finance Engineer, hôm nay tôi mang đến một bài toán thực chiến thuộc hàng khó nhất trên sàn chứng khoán Việt Nam: **Tổng công ty Hàng không Việt Nam (HVN)**.  
  > HVN có cơ cấu vốn cực kỳ đặc thù: vốn chủ sở hữu đang âm hơn 12.000 tỷ, và độ nhạy đòn bẩy hoạt động (DOL) lên tới hơn 4 lần. Một biến động nhỏ của giá dầu Jet A-1 hay tỷ giá USD/VND có thể lập tức xóa sổ hàng nghìn tỷ lợi nhuận.  
  > Vấn đề là: **Báo cáo tài chính truyền thống bằng file Excel tĩnh không thể giúp C-Suite và nhà đầu tư ra quyết định kịp thời**. Vì vậy, chỉ trong buổi sáng hôm nay, tôi đã dùng Lovable Pro để biến kho dữ liệu định lượng phức tạp này thành một **Enterprise Financial Intelligence Platform** thời gian thực."*

---

#### ⏱️ [00:40 - 01:50] LIVE DEMO TƯƠNG TÁC TRÊN LOVABLE (The WOW Factor)
*(Chuyển sang màn hình Web App đã deploy trên Lovable, thao tác trực tiếp)*
- **Lời thoại gợi ý**:
  > *"Đây là sản phẩm tôi vừa sprint hoàn thiện trên Lovable.  
  > 1. **Ở trang Executive Dashboard**: Toàn bộ bức tranh sức khỏe tài chính của HVN được hiển thị với tone màu Dark Slate chuẩn Bloomberg. Anh em có thể thấy ngay chỉ số quan trọng nhất: **Liquidity Runway** — HVN còn đủ thanh khoản để duy trì hoạt động trong bao nhiêu tháng.  
  > 2. **Điểm ăn tiền nhất nằm ở tab Macro Stress-Testing Simulator**:  
  > *(Vừa nói vừa kéo thanh trượt Slider trên màn hình)*  
  > Giả sử tối nay giá dầu thế giới leo thang từ mức 100 USD lên **120 USD/thùng Jet A-1**, và tỷ giá USD/VND bật lên **26.000**.  
  > Ngay khi tôi kéo slider, hệ thống lập tức tính toán lại chi phí nhiên liệu bổ sung, lỗ tỷ giá chưa thực hiện từ khoản nợ 1.8 tỷ USD, và cập nhật biểu đồ **EBIT dự phóng** cùng **Hệ số ghế hòa vốn (Break-even Load Factor)** trong tích tắc.  
  > 3. **Không chỉ là UI đẹp**: Toàn bộ logic đằng sau được bảo chứng bởi các thuật toán thống kê kiểm định chuỗi dừng ADF, kiểm định nhân quả Granger Causality và mô hình phát hiện bất thường Sloan Accruals."*

---

#### ⏱️ [01:50 - 02:30] KIẾN TRÚC KỸ THUẬT & VIBE CODE WORKFLOW (Clean Architecture)
*(Chỉ vào sơ đồ kiến trúc hoặc mở thoáng qua terminal / code)*
- **Lời thoại gợi ý**:
  > *"Bí quyết để tôi build và kiểm soát được hệ thống tài chính phức tạp này trong chưa đầy 45 phút là nhờ **Mô hình Vibe Coding 2 phân tầng (Clean Architecture)**:  
  > - **Local Quant Engine**: Chạy bằng Python với công cụ `uv` tốc độ cao, xử lý dữ liệu sạch, chạy kiểm toán và validate số liệu trong 1.6 giây.  
  > - **Cầu nối Lovable MCP Server**: Tôi kết nối trực tiếp IDE với Lovable qua giao thức MCP, đẩy toàn bộ bản đặc tả kiến trúc vào để Lovable Pro sinh ra giao diện React, Tailwind và biểu đồ tương tác chuẩn mực mà không bị hallucinate logic nghiệp vụ.  
  > Đây chính là tinh thần **From Lovable to Buildable** mà anh Khải Hoàn đã chia sẻ sáng nay: dùng AI để tăng tốc giao diện, nhưng làm chủ hoàn toàn logic nghiệp vụ cốt lõi."*

---

#### ⏱️ [02:30 - 03:00] KẾT BÀI & KÊU GỌI BÌNH CHỌN (Closing & Call to Action)
- **Lời thoại gợi ý**:
  > *"Từ một doanh nghiệp có nguy cơ hủy niêm yết vì âm vốn chủ, việc có một công cụ stress-testing trực quan thế này là cứu cánh cho cả ban điều hành lẫn các quỹ đầu tư.  
  > Dự án được xây dựng với tinh thần nghiên cứu học thuật minh bạch, dữ liệu công khai và zero-hardcoded secrets.  
  > Nếu anh em thấy giải pháp **Vibe Code một Bloomberg Platform thu nhỏ cho Vietnam Airlines** này hữu ích và ấn tượng, rất mong nhận được 1 phiếu vote của mọi người cho **Top 3 Showcase Battle** ngày hôm nay.  
  > Xin cảm ơn BTC Nghiên AI và toàn thể anh em!"*

---

### II. BỘ CÂU HỎI ĐỐI ĐÁP Q&A (CHEAT SHEET KHI BAN GIÁM KHẢO HỎI)

**Câu hỏi 1: Làm sao bạn đảm bảo số liệu tính toán trong slider không bị sai lệch?**
> *Trả lời*: Em sử dụng công thức tài chính hàng không chuẩn mực: mức tiêu thụ nhiên liệu cơ sở của HVN là khoảng 1.1 triệu tấn Jet A-1/năm (~8.2 triệu thùng). Khi giá dầu lệch $\Delta P$, chi phí biến đổi tăng tương ứng. Đồng thời tỷ giá tác động trực tiếp lên dư nợ ngoại tệ dài hạn (~1.8 tỷ USD). Mọi công thức đều được validate đối soát với BCTC kiểm toán qua bộ pipeline kiểm tra tự động trước khi nạp vào giao diện.

**Câu hỏi 2: Vai trò của Lovable MCP ở đây là gì so với việc tự viết code từ đầu?**
> *Trả lời*: Nếu code tay toàn bộ giao diện React, biểu đồ Recharts, cấu hình Tailwind Dark mode và responsive sliders từ đầu, một kỹ sư phải mất ít nhất 2 đến 3 ngày. Với Lovable MCP, em đóng vai trò Solution Architect: em chuẩn bị sẵn bộ Data Engine và đặc tả cấu trúc, sau đó điều khiển Lovable tự động dựng scaffold và tinh chỉnh giao diện chỉ trong 45 phút của buổi sprint sáng nay.

**Câu hỏi 3: Dự án này có tính năng bảo mật hay disclaimer gì không?**
> *Trả lời*: Dự án tuân thủ nghiêm ngặt Zero-Trust: không chứa bất kỳ secret hay dữ liệu bảo mật nội bộ nào; 100% dữ liệu là công khai từ BCTC kiểm toán và thị trường mở. Toàn bộ nền tảng đều có Disclaimer học thuật rõ ràng, không cấu thành lời khuyên đầu tư tài chính.

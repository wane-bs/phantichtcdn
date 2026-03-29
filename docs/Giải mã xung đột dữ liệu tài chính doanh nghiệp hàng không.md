Dựa trên việc đối chiếu chéo các bộ dữ liệu, báo cáo tự động và tài liệu hướng dẫn, dưới đây là những **bất đối xứng số liệu** và **xung đột luận điểm** nghiêm trọng được phát hiện trong hệ thống báo cáo:

### 1\. Xung đột luận điểm về Đặc thù Mô hình Kinh doanh (Kịch liệt nhất)

* **Kết luận của Báo cáo tự động:** Báo cáo Phân loại Mô hình Doanh nghiệp kết luận công ty thuộc nhóm **"Đa ngành / Thông thường (Diversified/Standard)"** và khẳng định **"Không có đặc trưng dị biệt đủ lớn, xếp vào nhóm chuẩn"** 1\.  
* **Xung đột với thực tế dữ liệu & Hướng dẫn:** Tài liệu hướng dẫn phân tích chỉ rõ đây là doanh nghiệp hàng không (HVN) với các đặc thù cực kỳ dị biệt: tỷ trọng tài sản cố định khổng lồ, Vốn chủ sở hữu (VCSH) bị âm nặng, và Chu kỳ tiền (CCC) luôn âm 2-4. Việc mô hình tự động xếp doanh nghiệp này vào nhóm "chuẩn/không dị biệt" là một sai lầm hoàn toàn về logic định tính.  
* Giải quyết: tích hợp phân tích chiều ngang theo thời gian để đưa ra kết luận về mô hình kinh doanh thực thế, nếu có điểm dị thường (sai lệch với mô hình kinh doanh) cảnh báo và đề xuất phương án phân tích để làm rõ nguyên nhân.

### 2\. Sự bất đối xứng (Ảo ảnh toán học) trong Chỉ số Sinh lời (ROE)

* **Sự bất thường của dữ liệu:** Bảng Financial Index báo cáo chỉ số **ROE năm 2022 là dương 2.24%** và **2023 là dương 0.4%** 5\.  
* **Nguyên nhân bất đối xứng:** Thực tế, Lợi nhuận sau thuế của cổ đông công ty mẹ năm 2022 là **âm 11.298 tỷ VNĐ** và 2023 là **âm 5.930 tỷ VNĐ** 6\. Đồng thời, Vốn chủ sở hữu các năm này cũng bị **âm lịch sử (âm 11.055 tỷ năm 2022 và âm 17.025 tỷ năm 2023\)** 6, 7\. Việc chia hai số âm tạo ra một tỷ suất ROE dương.  
* **Luận điểm xung đột:** Hướng dẫn đọc chỉ số đã cảnh báo rõ: *"Cảnh báo: ROE dương khi cả LNST và VCSH đều âm → ảo\!"* 8\. Nếu chỉ nhìn vào con số ROE \> 0 để đánh giá doanh nghiệp có lãi là hoàn toàn sai lệch thực tế.  
* Giải pháp: thay thế roe bằng các chỉ số đánh giá khác tập trung vào hiệu quả sử dụng nợ và hiệu quả kinh doanh.

### 3\. Biến dạng (Distortion) trong Cấu trúc Vốn và Đòn bẩy

* **Số liệu ghi nhận:** Chỉ số Nợ/VCSH (D/E) năm 2022, 2023, 2024 lần lượt mang giá trị âm: **\-6.48x, \-4.38x, \-7.22x** 5, 9\. Chỉ số Đòn bẩy tài chính (Leverage) cũng âm tương tự 10\.  
* **Phân tích sự bất đối xứng:** Trong tài chính thông thường, đòn bẩy âm hoặc giảm sâu thường ám chỉ doanh nghiệp ít nợ. Tuy nhiên ở đây, nguyên nhân là do **Mẫu số (VCSH) bị âm quá nặng**, trong khi Tử số (Tổng nợ/Tổng tài sản) vẫn rất khổng lồ 3, 7\. Sự bất đối xứng nằm ở chỗ các chỉ số đo lường rủi ro (Solvency ratios) bị vô hiệu hóa về mặt toán học, mất đi chức năng cảnh báo rủi ro thông thường.  
* Giải pháp: tìm kiếm các mô hình/ phương pháp/ chỉ số cảnh báo khác

### 4\. Xung đột giữa Mô hình Học máy (ElasticNet) và Tầm quan trọng của nhân tố (VIP)

* **Sự bất thường của thuật toán:** Mô hình ElasticNet đã "triệt tiêu" hoàn toàn trọng số của 4/5 biến số đưa vào. Nó chỉ giữ lại Hệ số của **Biên GP (0.0644)**, trong khi gán giá trị **0.0 (tuyệt đối)** cho Vòng quay TS, DSO, DIO, và Current Ratio 11\.  
* **Xung đột:** Bảng PLSR VIP Scores lại cho thấy các chỉ số như Current Ratio (0.951) và Vòng quay TS (0.924) vẫn có mức độ giải thích (Quan trọng) nhất định dù nằm dưới ngưỡng VIP=1 12\. Việc ElasticNet ép các hệ số này về 0.0 hoàn toàn cho thấy mô hình đang bị phạt (penalize \- L1) quá mức hoặc dữ liệu quá ít (chỉ 15 năm quan sát) khiến thuật toán bất ổn, đúng như rủi ro đã được cảnh báo trong tài liệu: *"Với N=5 (hoặc chuỗi ngắn), ElasticNet/PLSR có thể không ổn định"* 13\.  
* Giải pháp: loại bỏ phương án học máy.

### 5\. Xung đột Chất lượng Báo cáo: Các Tín hiệu Cảnh báo Thao túng (Anomaly Scores)

Hệ thống ghi nhận sự gián đoạn rất nghiêm trọng về chất lượng dòng tiền và lợi nhuận kế toán trong giai đoạn 2021-2022, làm suy yếu độ tin cậy của toàn bộ số liệu:

* **Sloan Accruals (Tỷ lệ dồn tích):** Đạt mức **\-32.28% vào năm 2021** 14\. (Vượt ngưỡng rủi ro \>25% / \<-25%, được phân loại là **"Nghiêm trọng"** 14).  
* **M-Score (Beneish):** Đạt giá trị dương **1.0372 vào năm 2021** 14\. (Vượt ngưỡng \> \-2.22, rơi vào trạng thái **"Nghi ngờ"** 14 thao túng thu nhập).  
* **Z-Score (Altman):** Rơi vào vùng "Nguy hiểm" (Dưới 1.1) liên tục từ 2020 đến 2024, đỉnh điểm là **\-3.51 (năm 2023\)** 14\.  
* Giải pháp: ghi nhận cảnh báo. Không thay đổi hay phản ứng gì khác.

**Kết luận tổng thể:** Báo cáo chứa những xung đột lớn giữa kết luận tự động (nhận định mô hình bình thường) và bản chất dữ liệu (doanh nghiệp hàng không đang khủng hoảng vốn chủ sở hữu). Toàn bộ các chỉ số liên quan đến ROE, P/E, P/B, và Đòn bẩy tài chính trong giai đoạn 2021 \- 2024 đều bị nhiễu do hiệu ứng "chia số âm", yêu cầu người phân tích phải bỏ qua các chỉ số bề mặt này và chỉ tập trung vào Dòng tiền (Cashflow) và Cấu trúc nợ gộp.

Định hướng kế tiếp: xây dựng khung phân tích Dòng tiền (Cashflow) và Cấu trúc nợ gộp. Tìm kiếm các chỉ số phân tích cơ bản và mô hình phân tích khoa học được dùng để phân tích Dòng tiền (Cashflow) và Cấu trúc nợ gộp.  

import os
import json
import pandas as pd
from datetime import datetime

class ReportGenerator:
    def __init__(self, calc_dir="output/2_calculated", class_dir="output/3_classification", out_dir="bao_cao"):
        self.calc_dir = calc_dir
        self.class_dir = class_dir
        self.out_dir = out_dir
        self.data = {}
        
        # Đảm bảo thư mục đầu ra tồn tại
        os.makedirs(self.out_dir, exist_ok=True)

    def _read_json(self, filepath):
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _read_csv(self, filepath):
        if os.path.exists(filepath):
            return pd.read_csv(filepath, index_col=0)
        return None

    def load_data(self):
        # Tải Business Model
        model_path = os.path.join(self.class_dir, "business_model.json")
        self.data['BUSINESS_MODEL'] = self._read_json(model_path)
        
        # Tải Dữ liệu Anomaly
        anomaly_path = os.path.join(self.calc_dir, "ANOMALY_NUMERIC.json")
        self.data['ANOMALY_NUMERIC'] = self._read_json(anomaly_path)
        
        # Tải Financial Index
        fi_path = os.path.join(self.calc_dir, "FINANCIAL INDEX.csv")
        self.data['FINANCIAL_INDEX'] = self._read_csv(fi_path)
        
        # Tải Dữ liệu Gốc thu gọn (nếu cần)
        cv_path = os.path.join(self.calc_dir, "CASH FLOW STATEMENT.csv")
        self.data['CASH_FLOW'] = self._read_csv(cv_path)
        
        return self.data

    def _get_metric(self, df, pattern, year):
        if df is None: return "N/A"
        try:
            # Tìm row theo regex
            row = df[df.index.astype(str).str.contains(pattern, case=False, regex=True)]
            if not row.empty:
                val = row[str(year)].values[0]
                return float(val)
        except Exception:
            pass
        return "N/A"

    def _format_val(self, val, unit=""):
        if val == "N/A": return "Không đủ dữ liệu"
        return f"{val:,.2f} {unit}".strip()

    def _format_ocf(self, val):
        """Format OCF value: auto-convert raw VND to tỷ VND if needed."""
        if val == "N/A": return "Không đủ dữ liệu"
        # Nếu giá trị tuyệt đối >= 1e9 thì đang ở đơn vị VND, chia về tỷ
        if abs(val) >= 1e9:
            val_billion = val / 1e9
            return f"{val_billion:,.0f} tỷ VND"
        # Nếu nhỏ hơn thì đã ở đơn vị tỷ rồi
        return f"{val:,.2f} tỷ VND"

    def generate_report(self):
        bm = self.data.get('BUSINESS_MODEL', {})
        if not bm:
            return "# Lỗi sinh báo cáo\nKhông tìm thấy dữ liệu phân loại mô hình (Stage 3)."
            
        latest_year = bm.get('Năm tham chiếu', 'Unknown')
        core_model = bm.get('Mô hình cốt lõi', 'Chưa xác định')
        health = bm.get('Sức khỏe Tài chính', 'Chưa đánh giá')
        recommendation = bm.get('Khuyến nghị Đầu tư', 'Theo dõi')
        shift = bm.get('Dịch chuyển', 'Không có dịch chuyển')
        core_logic = bm.get('Minh chứng', '')
        
        # Metrics từ Anomaly
        anom = self.data.get('ANOMALY_NUMERIC', {})
        altman = anom.get('altman', [])
        beneish = anom.get('beneish', [])
        
        altman_latest = altman[-1] if altman else "N/A"
        beneish_latest = beneish[-1] if beneish else "N/A"
        
        # Metrics từ Financial Index
        fi = self.data.get('FINANCIAL_INDEX')
        roe = self._get_metric(fi, r'^ROE', latest_year)
        roa = self._get_metric(fi, r'^ROA', latest_year)
        gross_margin = self._get_metric(fi, r'^Biên lợi nhuận gộp', latest_year)
        net_margin = self._get_metric(fi, r'^Biên lợi nhuận ròng', latest_year)
        
        # Nhận định về Z-score
        if altman_latest != "N/A":
            if altman_latest < 1.1:
                z_comment = f"Chỉ số Z-Score đạt {altman_latest:.2f}, nằm sâu trong vùng rủi ro phá sản. Doanh nghiệp đang đối mặt với nguy cơ mất thanh khoản nghiêm trọng hoặc cơ cấu vốn không bền vững."
            elif altman_latest > 2.6:
                z_comment = f"Chỉ số Z-Score đạt {altman_latest:.2f}, cho thấy cơ cấu vốn an toàn, khả năng chống chịu rủi ro của doanh nghiệp rất vững chắc."
            else:
                z_comment = f"Chỉ số Z-Score đạt {altman_latest:.2f}, nằm trong vùng xám (Grey Zone). Doanh nghiệp cần cải thiện dòng tiền hoặc đòn bẩy tài chính để thoát khỏi quỹ đạo rủi ro."
        else:
            z_comment = "Chưa thể đánh giá điểm Altman Z-Score do thiếu dữ liệu tỷ trọng."

        # Bắt đầu soạn văn bản
        md_lines = []
        md_lines.append(f"# BÁO CÁO PHÂN TÍCH TÀI CHÍNH TỔNG HỢP")
        md_lines.append(f"*Ngày trích xuất: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Năm phân tích: {latest_year}*")
        md_lines.append("\n---\n")
        
        # Phần 1
        md_lines.append("## 1. TỔNG QUAN CHỈ ĐẠO (EXECUTIVE SUMMARY)")
        md_lines.append(f"Dựa trên dữ liệu tài chính kết thúc năm {latest_year}, hệ thống Phân tích Đa chiều đã tự động đánh giá và đưa ra kết luận chiến lược đối với sức khỏe tài chính của doanh nghiệp. Cụ thể, hệ thống đưa ra khuyến nghị: **{recommendation}** đối với việc cân nhắc đầu tư tài sản.")
        md_lines.append(f"\nDoanh nghiệp được phân loại vào **{core_model}** dựa theo lịch sử hoạt động 5 năm gắn liền với đặc thù tỷ trọng tài sản và biên lợi nhuận. *({core_logic})*")
        md_lines.append(f"\n**Lưu ý về dòng dịch chuyển:** {shift}")
        md_lines.append(f"\n> *(Tham chiếu biểu đồ: Biểu đồ **Lịch sử Dịch chuyển Mô hình Cốt lõi** tại Tab 3 (Kết luận Mô hình) phản ánh sự thay đổi cấu trúc tài sản theo dòng thời gian).*")
        
        # Phần 2
        md_lines.append("\n## 2. KHẢ NĂNG SINH TỒN VÀ CHẤT LƯỢNG BCTC")
        md_lines.append("Một trong những trọng tâm quan trọng nhất trong việc định vị doanh nghiệp là đánh giá rủi ro đình chỉ hoạt động:")
        md_lines.append(f"\n- **Điểm sức khỏe:** Xếp loại **{health}**.")
        md_lines.append(f"- **Rủi ro tín dụng định lượng (Altman Z''-Score):** {z_comment}")
        if beneish_latest != "N/A":
            b_comment = "có rủi ro thao túng báo cáo tài chính (cần kiểm toán kỹ các khoản mục kế toán)." if beneish_latest > -2.22 else "nằm trong vùng an toàn, chưa phát hiện dấu hiệu bóp méo số liệu."
            md_lines.append(f"- **Chất lượng Báo cáo, Đạo đức Kế toán (Beneish M-Score):** Điểm M-Score đạt {beneish_latest:.2f}, {b_comment}")
        md_lines.append(f"\n> *(Tham chiếu biểu đồ: **Gauge Chart: Altman Z-Score & Beneish M-Score** tại Tab 2 (Chất lượng BCTC) cung cấp thước đo cường độ rủi ro trực quan).*")

        # Phần 3
        md_lines.append("\n## 3. HIỆU QUẢ HOẠT ĐỘNG (PROFITABILITY & EFFICIENCY)")
        md_lines.append("Hiệu năng tối ưu hóa lợi nhuận của doanh nghiệp trong kỳ phân tích đạt các kết quả sau:")
        md_lines.append(f"\n- **Hiệu quả Sinh lời:** Tỷ suất lợi nhuận trên vốn chủ sở hữu (ROE) là {self._format_val(roe, '%')} và Tỷ suất lợi nhuận trên tổng tài sản (ROA) đạt {self._format_val(roa, '%')}. Điều này thể hiện bức tranh tổng quát về hiệu quả phân bổ vốn.")
        md_lines.append(f"- **Khả năng sinh lời từ Doanh thu:** Biên lợi nhuận gộp đạt {self._format_val(gross_margin, '%')}, trong khi Biên lợi nhuận ròng đạt {self._format_val(net_margin, '%')}. Những con số này thể hiện mức rào cản chi phí mà doanh nghiệp đang gánh chịu từ giá vốn đến các khoản chi hoạt động.")
        
        # Logic đặc thù theo mẫu hình
        cf = self.data.get('CASH_FLOW')
        ocf = self._get_metric(cf, r'^Lưu chuyển tiền thuần từ các hoạt động sản xuất kinh doanh$', latest_year) if cf is not None else "N/A"
        
        md_lines.append("\n### Dấu hiệu nhận diện theo Mô hình Cốt lõi:")
        if "Thâm dụng vốn" in core_model:
            fat = self._get_metric(fi, r'Vòng quay tài sản cố định', latest_year)
            md_lines.append(f"Là một doanh nghiệp *Thâm dụng vốn*, khả năng xoay vòng tài sản cố định đóng vai trò sinh tử. Vòng quay tài sản cố định (FAT) năm nay ghi nhận ở mức {self._format_val(fat, 'vòng')}. Quản trị dòng tiền (OCF) tạo ra {self._format_ocf(ocf)} để đắp ứng nhu cầu tái đầu tư capex là yếu tố then chốt.")
            md_lines.append("> *(Tham chiếu: Phân tích **Vòng quay TSCĐ (FAT)** và **DuPont Combo** tại Tab 4: Hiệu suất Mẫu hình nhằm đánh giá đòn bẩy hoạt động).*")
        elif "Bán lẻ" in core_model:
            ito = self._get_metric(fi, r'Vòng quay hàng tồn kho', latest_year)
            md_lines.append(f"Với mô hình kinh doanh *Bán lẻ & Phân phối*, Vòng quay hàng tồn kho (ITO) là thước đo sức bán cốt lõi, hiện ghi nhận {self._format_val(ito, 'vòng')}. Tình trạng dòng tiền hoạt động OCF ghi nhận {self._format_ocf(ocf)} đóng vai trò nuôi dưỡng hệ sinh thái cung ứng.")
            md_lines.append("> *(Tham chiếu: Biểu đồ **Vòng quay Tồn kho (ITO)** tốc độ cao tại Tab 4).*")
        elif "Nhẹ tài sản" in core_model:
            at = self._get_metric(fi, r'Vòng quay tổng tài sản', latest_year)
            md_lines.append(f"Đối với mô hình *Nhẹ tài sản / Công nghệ*, Vòng quay tổng tài sản ghi nhận mức {self._format_val(at, 'vòng')}. Đặc sản của mô hình này nằm ở Biên lợi nhuận gộp khổng lồ, được cộng hưởng thêm với nền tảng quy mô khách hàng.")
            md_lines.append("> *(Tham chiếu: Xem biên LN khuếch đại ở **Biểu đồ tỷ suất sinh lời** Tab 4).*")
        else:
            md_lines.append(f"Đối với định dạng kinh doanh đa ngành, doanh nghiệp phải cân đối giữa khả năng sinh lợi ({self._format_val(roe, '%')} ROE) và quản trị rủi ro dòng tiền (hiện đang tạo ra {self._format_ocf(ocf)} lưu chuyển thuần từ HĐKD).")
            md_lines.append("> *(Tham chiếu biểu đồ: **100% Stacked Area Dòng tiền** tại Tab 1 tái hiện chu kỳ dòng máu doanh nghiệp).*")

        md_lines.append("\n## 4. TỔNG KẾT & GÓC KHUẤT LƯU Ý")
        md_lines.append("Dựa trên báo cáo chiết xuất từ hệ thống tự động, Ban Giám đốc và Nhà đầu tư cần cân nhắc các yếu tố bất lợi mang tính cấu trúc. Đặc biệt lưu tâm quy luật chu kỳ vĩ mô nếu doanh nghiệp đang trong nhóm Thâm dụng vốn/Nặng tài sản, hoặc rủi ro vỡ nợ ngắn hạn nếu Altman Z-score sụt giảm dưới ngưỡng cấu trúc an toàn.")
        md_lines.append("\n---")
        md_lines.append("\n*Báo cáo được khởi tạo tự động bởi Pipeline của Hệ thống Phân tích HVN. Các số liệu định tính và định lượng có liên kết trực tiếp với các phân trang (Tabs) được hiển thị trên Streamlit Dashboard.*")
        
        return "\n".join(md_lines)

    def save_report(self):
        report_content = self.generate_report()
        filepath = os.path.join(self.out_dir, "BaoCao_PhanTich_HVN.md")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"Report generated successfully at: {filepath}")
        return filepath

    def run_all(self):
        self.load_data()
        return self.save_report()

if __name__ == "__main__":
    gen = ReportGenerator()
    gen.run_all()

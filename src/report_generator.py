import os
import json
import pandas as pd
from datetime import datetime

class ReportGenerator:
    def __init__(self, calc_dir="output/2_calculated", class_dir="output/3_classification",
                 adv_dir="output/4_advanced", out_dir="bao_cao"):
        self.calc_dir = calc_dir
        self.class_dir = class_dir
        self.adv_dir = adv_dir
        self.out_dir = out_dir
        self.data = {}
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
        self.data['BUSINESS_MODEL'] = self._read_json(os.path.join(self.class_dir, "business_model.json"))
        self.data['ANOMALY_NUMERIC'] = self._read_json(os.path.join(self.calc_dir, "ANOMALY_NUMERIC.json"))
        self.data['DATA_WARNINGS'] = self._read_json(os.path.join(self.calc_dir, "data_warnings.json"))
        self.data['FINANCIAL_INDEX'] = self._read_csv(os.path.join(self.calc_dir, "FINANCIAL INDEX.csv"))
        self.data['CASH_FLOW'] = self._read_csv(os.path.join(self.calc_dir, "CASH FLOW STATEMENT.csv"))
        self.data['INCOME_STMT'] = self._read_csv(os.path.join(self.calc_dir, "INCOME STATEMENT.csv"))
        self.data['BALANCE_SHEET'] = self._read_csv(os.path.join(self.calc_dir, "BALANCE SHEET.csv"))
        self.data['LIQUIDITY'] = self._read_csv(os.path.join(self.calc_dir, "LIQUIDITY_CASHFLOW.csv"))
        self.data['FOOTBALL_FIELD'] = self._read_json(os.path.join(self.adv_dir, "football_field.json"))
        self.data['VALUATION_META'] = self._read_json(os.path.join(self.adv_dir, "valuation_meta.json"))
        return self.data

    def _get_metric(self, df, pattern, year):
        if df is None: return "N/A"
        try:
            row = df[df.index.astype(str).str.contains(pattern, case=False, regex=True)]
            if not row.empty:
                val = row[str(year)].values[0]
                return float(val)
        except Exception:
            pass
        return "N/A"

    def _fmt(self, val, unit="", precision=2):
        if val == "N/A": return "Không đủ dữ liệu"
        return f"{val:,.{precision}f} {unit}".strip()

    def _fmt_ty(self, val):
        if val == "N/A": return "Không đủ dữ liệu"
        if abs(val) >= 1e9:
            return f"{val / 1e9:,.0f} tỷ VND"
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

        # Data Warnings
        warnings = self.data.get('DATA_WARNINGS', {})
        neg_eq_years = warnings.get('negative_equity_years', [])
        neg_ni_years = warnings.get('negative_ni_years', [])

        # Anomaly scores
        anom = self.data.get('ANOMALY_NUMERIC', {})
        altman = anom.get('altman', [])
        beneish = anom.get('beneish', [])
        altman_latest = altman[-1] if altman else "N/A"
        beneish_latest = beneish[-1] if beneish else "N/A"

        # Financial Index
        fi = self.data.get('FINANCIAL_INDEX')
        ev_ebitda = self._get_metric(fi, r'^EV/EBITDA$', latest_year)
        ps = self._get_metric(fi, r'^P/S$', latest_year)
        icr = self._get_metric(fi, r'^Khả năng chi trả lãi vay$', latest_year)
        gross_margin_raw = self._get_metric(fi, r'^Biên lợi nhuận gộp', latest_year)
        ebit_margin_raw = self._get_metric(fi, r'^Biên EBIT', latest_year)
        at = self._get_metric(fi, r'^Quay vòng tài sản$', latest_year)
        
        gross_margin = round(gross_margin_raw * 100, 2) if gross_margin_raw != "N/A" else "N/A"
        ebit_margin = round(ebit_margin_raw * 100, 2) if ebit_margin_raw != "N/A" else "N/A"

        # Cash Flow
        cf = self.data.get('CASH_FLOW')
        ocf = self._get_metric(cf, r'^Lưu chuyển tiền thuần từ các hoạt động sản xuất kinh doanh$', latest_year) if cf is not None else "N/A"

        # Football Field
        ff = self.data.get('FOOTBALL_FIELD', {})
        current_ev = ff.get('current_ev', 0)

        # Z-Score comment
        if altman_latest != "N/A":
            if altman_latest < 1.1:
                z_comment = f"Z-Score = {altman_latest:.2f} → Vùng rủi ro phá sản. Cấu trúc vốn không bền vững."
            elif altman_latest > 2.6:
                z_comment = f"Z-Score = {altman_latest:.2f} → Cơ cấu vốn an toàn."
            else:
                z_comment = f"Z-Score = {altman_latest:.2f} → Vùng xám (Grey Zone), cần cải thiện."
        else:
            z_comment = "Chưa đủ dữ liệu để đánh giá Altman Z-Score."

        md = []
        md.append(f"# BÁO CÁO PHÂN TÍCH TÀI CHÍNH TỔNG HỢP — VIETNAM AIRLINES (HVN)")
        md.append(f"*Ngày trích xuất: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Năm phân tích: {latest_year}*")
        md.append(f"\n*Triết lý phân tích: Enterprise Value (EV) Framework — Tập trung Dòng tiền & Khả năng sinh tồn*")
        md.append("\n---\n")

        # ── CẢNH BÁO DỮ LIỆU ──
        if neg_eq_years or neg_ni_years:
            md.append("> [!WARNING]")
            md.append("> **CẢNH BÁO TÍN HIỆU GIẢ (Data Distortion Alert)**")
            if neg_eq_years:
                md.append(f"> - VCSH âm các năm: {', '.join(neg_eq_years)}. Các chỉ số ROE, P/B, Solvency bị cách ly.")
            if neg_ni_years:
                md.append(f"> - Lợi nhuận âm các năm: {', '.join(neg_ni_years)}. Chỉ số P/E bị cách ly.")
            md.append("> - Hệ thống đã tự động gán NaN và chuyển trọng tâm sang nhóm chỉ số EV/EBITDA, DSCR, CFO/Debt.\n")

        # ── PHẦN 1: EXECUTIVE SUMMARY ──
        md.append("## 1. TỔNG QUAN CHỈ ĐẠO (Executive Summary)")
        md.append(f"Doanh nghiệp được phân loại vào mô hình **{core_model}**. *({core_logic})*")
        md.append(f"\n- **Sức khỏe Tài chính:** {health}")
        md.append(f"- **Khuyến nghị Đầu tư:** {recommendation}")
        md.append(f"- **Dịch chuyển Mô hình:** {shift}")

        # ── PHẦN 2: KHẢ NĂNG SINH TỒN ──
        md.append("\n## 2. KHẢ NĂNG SINH TỒN & CHẤT LƯỢNG BCTC")
        md.append(f"- **Rủi ro Tín dụng (Altman Z-Score):** {z_comment}")
        if beneish_latest != "N/A":
            b_comment = "có rủi ro thao túng BCTC" if beneish_latest > -2.22 else "nằm trong vùng an toàn"
            md.append(f"- **Chất lượng Kế toán (Beneish M-Score):** M-Score = {beneish_latest:.2f} → {b_comment}.")
        md.append(f"- **Dòng tiền Hoạt động (CFO):** {self._fmt_ty(ocf)}")
        md.append(f"- **Khả năng trả lãi vay (ICR):** {self._fmt(icr, 'x')}")

        # ── PHẦN 3: ĐỊNH GIÁ ENTERPRISE VALUE ──
        md.append("\n## 3. ĐỊNH GIÁ DOANH NGHIỆP (Enterprise Value Framework)")
        md.append("Phương pháp: **EV/EBITDA Mean Reversion** + **DCF Terminal Value Integration** + **Football Field Chart**")
        md.append(f"\n- **EV/EBITDA hiện tại:** {self._fmt(ev_ebitda, 'x')}")
        md.append(f"- **P/S (Price-to-Sales):** {self._fmt(ps, 'x')}")
        if current_ev:
            md.append(f"- **Enterprise Value hiện tại:** {current_ev/1e12:,.1f} nghìn tỷ VND")

        ev_min = ff.get('ev_ebitda_min', 0)
        ev_max = ff.get('ev_ebitda_max', 0)
        dcf_min = ff.get('dcf_min', 0)
        dcf_max = ff.get('dcf_max', 0)
        if ev_max and dcf_max:
            md.append(f"\n| Phương pháp | Dải Giá trị (tỷ VND) |")
            md.append(f"|---|---|")
            md.append(f"| EV/EBITDA (±1σ) | {ev_min/1e9:,.0f} – {ev_max/1e9:,.0f} |")
            md.append(f"| DCF TV Integration | {dcf_min/1e9:,.0f} – {dcf_max/1e9:,.0f} |")
            md.append(f"| **EV hiện tại** | **{current_ev/1e9:,.0f}** |")

        # ── PHẦN 4: HIỆU QUẢ HOẠT ĐỘNG ──
        md.append("\n## 4. HIỆU QUẢ HOẠT ĐỘNG & BIÊN LỢI NHUẬN")
        md.append(f"- **Biên Lợi nhuận Gộp:** {self._fmt(gross_margin, '%')}")
        md.append(f"- **Biên EBIT:** {self._fmt(ebit_margin, '%')}")
        md.append(f"- **Vòng quay Tài sản:** {self._fmt(at, 'x')}")

        if "Thâm dụng vốn" in core_model:
            fat = self._get_metric(fi, r'Vòng quay tài sản cố định', latest_year)
            md.append(f"- **Vòng quay TSCĐ (FAT):** {self._fmt(fat, 'vòng')} *(đặc thù Thâm dụng vốn)*")

        # ── PHẦN 5: TỔNG KẾT ──
        md.append("\n## 5. KẾT LUẬN & KHUYẾN NGHỊ")
        md.append("Dựa trên khung phân tích Enterprise Value, doanh nghiệp được đánh giá trọng tâm qua:")
        md.append("1. **Dòng tiền thực** (CFO, FCFF) thay vì lợi nhuận kế toán")
        md.append("2. **Bội số EV/EBITDA** thay vì P/E, P/B bị nhiễu")
        md.append("3. **Khả năng sinh tồn** (DSCR, Runway, ICR) thay vì chỉ số thanh khoản truyền thống")
        md.append(f"\nBan Giám đốc và Nhà đầu tư cần đặc biệt theo dõi tỷ lệ Nợ ngắn hạn/Tổng nợ và lộ trình tái cấu trúc kỳ hạn nợ.")

        md.append("\n---")
        md.append("\n*Báo cáo được khởi tạo tự động bởi Pipeline (EV Framework). Tham chiếu chi tiết: Chương 1-5 tại `/bao_cao/`.*")

        return "\n".join(md)

    def save_report(self):
        report_content = self.generate_report()
        filepath = os.path.join(self.out_dir, "BaoCao_PhanTich_HVN.md")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"Report generated: {filepath}")
        return filepath

    def run_all(self):
        self.load_data()
        return self.save_report()

if __name__ == "__main__":
    gen = ReportGenerator()
    gen.run_all()

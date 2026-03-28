import pandas as pd
import numpy as np

class BusinessClassifier:
    """
    Phân loại doanh nghiệp tự động dựa trên Ma trận định lượng tỷ số tài chính.
    Đầu vào là bộ dfs (DataFrames) đã được DataProcessor và Calculator xử lý.
    """
    def __init__(self, dfs_dict):
        self.dfs = dfs_dict

    def _get_row(self, df, pattern):
        row = df[df['Khoản mục'].str.contains(pattern, case=False, na=False, regex=True)]
        if not row.empty:
            return row.iloc[0]
        return None

    def _get_years(self, df):
        return [col for col in df.columns if col != 'Khoản mục']

    def classify(self):
        bs_df = self.dfs.get('BALANCE SHEET')
        is_df = self.dfs.get('INCOME STATEMENT')
        cf_df = self.dfs.get('CASH FLOW STATEMENT')
        
        if bs_df is None or is_df is None:
            return None

        years = self._get_years(bs_df)
        if not years:
            return None

        latest_year = years[-1]  # Dùng mốc năm mới nhất để định lượng loại mô hình

        def _val(df, pattern):
            if df is None: return 0.0
            row = self._get_row(df, pattern)
            if row is not None:
                return float(row[latest_year])
            return 0.0

        ta = _val(bs_df, r'^TỔNG TÀI SẢN$')
        if ta == 0: ta = 1.0 # Tránh chia cho 0

        rev = _val(is_df, r'^Doanh số thuần$')
        if rev == 0: rev = 1.0 # Tránh chia cho 0

        cogs = abs(_val(is_df, r'^Giá vốn hàng bán$'))
        fa = _val(bs_df, r'^Tài sản cố định$')
        inv = _val(bs_df, r'^Hàng tồn kho')
        recv = _val(bs_df, r'phải thu ngắn hạn của khách hàng|^Các khoản phải thu$')
        cash = _val(bs_df, r'^Tiền và tương đương tiền')
        invest = _val(bs_df, r'^Giá trị thuần đầu tư ngắn hạn')
        sell_exp = abs(_val(is_df, r'^Chi phí bán hàng$'))
        
        # Lấy Khấu hao từ CF nếu có
        depr = abs(_val(cf_df, r'^Khấu hao TSCĐ$')) if cf_df is not None else 0.0

        # Metrics (Tính %)
        fa_to_ta = (fa / ta) * 100
        inv_to_ta = (inv / ta) * 100
        recv_to_ta = (recv / ta) * 100
        cash_invest_to_ta = ((cash + invest) / ta) * 100
        
        gross_margin = ((rev - cogs) / rev) * 100
        depr_to_rev = (depr / rev) * 100
        sell_to_rev = (sell_exp / rev) * 100

        metrics = {
            'fa_to_ta': fa_to_ta,
            'depr_to_rev': depr_to_rev,
            'gross_margin': gross_margin,
            'inv_to_ta': inv_to_ta,
            'recv_to_ta': recv_to_ta,
            'sell_to_rev': sell_to_rev,
            'cash_invest_to_ta': cash_invest_to_ta
        }

        # Bắt đầu phân loại (Theo Matrix Classification)
        model = "Đa ngành / Thông thường (Diversified/Standard)"
        logic = []

        if fa_to_ta > 40 or depr_to_rev > 10:
            model = "Thâm dụng vốn (Capital-Intensive)"
            logic = [f"Tỷ trọng TSCĐ/TTS = {fa_to_ta:.1f}% (>40%)", f"Khấu hao/Doanh thu = {depr_to_rev:.1f}% (>10%)"]
        elif recv_to_ta > 70 and fa_to_ta < 5:
            model = "Dịch vụ tài chính (Financial Services)"
            logic = [f"Phải thu/TTS = {recv_to_ta:.1f}% (>70%)", f"TSCĐ/TTS = {fa_to_ta:.1f}% (<5%)"]
        elif fa_to_ta < 10 and gross_margin > 60:
            model = "Nhẹ tài sản / Công nghệ (Asset-Light/SaaS)"
            logic = [f"TSCĐ/TTS = {fa_to_ta:.1f}% (<10%)", f"Biên LN Gộp = {gross_margin:.1f}% (>60%)"]
        elif inv_to_ta > 30 and gross_margin < 25:
            model = "Bán lẻ & Phân phối (Retail/Inventory-based)"
            logic = [f"Kho/TTS = {inv_to_ta:.1f}% (>30%)", f"Biên LN Gộp = {gross_margin:.1f}% (<25%)"]
        elif sell_to_rev > 20 and cash_invest_to_ta > 20: 
            # Giả định cho Platform/Thương mại điện tử cần đốt tiền marketing (CPBH lớn) & giữ tiền nhiều
            model = "Thương mại điện tử / Nền tảng (Platform)"
            logic = [f"Chi phí BH/Doanh thu = {sell_to_rev:.1f}%", f"Tiền & ĐTTC/TTS = {cash_invest_to_ta:.1f}%"]
            
        result = {
            'Mô hình': model,
            'Minh chứng': ' | '.join(logic) if logic else "Không có đặc trưng dị biệt đủ lớn, xếp vào nhóm chuẩn.",
            'Năm tham chiếu': latest_year,
            'Metrics': metrics
        }
        
        self.dfs['BUSINESS_MODEL'] = result
        return self.dfs

    def run_all(self):
        return self.classify()

if __name__ == "__main__":
    from data_processor import DataProcessor
    from calculator import Calculator
    dfs = DataProcessor("data/hvn.xlsx").load_and_normalize()
    dfs = Calculator(dfs).run_all()
    classifier = BusinessClassifier(dfs)
    dfs = classifier.run_all()
    
    print("=== Phân loại Doanh nghiệp ===")
    print(f"Mô hình: {dfs['BUSINESS_MODEL']['Mô hình']}")
    print(f"Minh chứng: {dfs['BUSINESS_MODEL']['Minh chứng']}")

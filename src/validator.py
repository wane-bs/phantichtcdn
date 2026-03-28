import pandas as pd

class Validator:
    def __init__(self, dfs_dict):
        self.dfs = dfs_dict
        
    def _get_row_vals(self, df, pattern, years):
        row = df[df['Khoản mục'].str.contains(pattern, case=False, na=False, regex=True)]
        if not row.empty:
            return row.iloc[0][years].fillna(0)
        return pd.Series(0, index=years)

    def run_checks(self):
        bs = self.dfs.get('BALANCE SHEET')
        cf = self.dfs.get('CASH FLOW STATEMENT')
        
        if bs is None or cf is None:
            print("Missing files for validation.")
            return
            
        years = [col for col in bs.columns if col != 'Khoản mục']
        
        print("\n--- KẾT QUẢ KIỂM ĐỊNH (INTEGRITY VALIDATION) ---")
        
        # Check 1: Tổng Tài Sản == Tổng Nguồn Vốn
        total_assets = self._get_row_vals(bs, r'^TỔNG TÀI SẢN$', years)
        total_capital = self._get_row_vals(bs, r'^TỔNG CỘNG NGUỒN VỐN$|^TỔNG NGUỒN VỐN$', years)
        check1 = (abs(total_assets - total_capital) < 1).all()
        print(f"Check 1 [Tổng Tài Sản == Tổng Nguồn Vốn]: {'PASSED' if check1 else 'FAILED'}")
        
        # Check 2: TS ngắn hạn + TS dài hạn == Tổng Tài Sản
        short_term = self._get_row_vals(bs, r'^TÀI SẢN NGẮN HẠN$', years)
        long_term = self._get_row_vals(bs, r'^TÀI SẢN DÀI HẠN$', years)
        check2 = (abs((short_term + long_term) - total_assets) < 1).all()
        print(f"Check 2 [TS ngắn hạn + TS dài hạn == Tổng Tài Sản]: {'PASSED' if check2 else 'FAILED'}")
        if not check2:
            print(f"  Sai số: \n{(short_term + long_term) - total_assets}")
            
        # Check 3: Nợ phải trả + Vốn Chủ Sở Hữu == Tổng Nguồn Vốn
        liabilities = self._get_row_vals(bs, r'^NỢ PHẢI TRẢ$', years)
        equity = self._get_row_vals(bs, r'^VỐN CHỦ SỞ HỮU$', years)
        check3 = (abs((liabilities + equity) - total_capital) < 1).all()
        print(f"Check 3 [Nợ phải trả + Vốn CSH == Tổng Nguồn Vốn]: {'PASSED' if check3 else 'FAILED'}")
        
        # Check 4: Tiền cuối kỳ CF == Tiền đầu tiên BS
        cf_cash = self._get_row_vals(cf, r'^Tiền và tương đương tiền cuối kỳ', years)
        bs_cash = self._get_row_vals(bs, r'^Tiền và tương đương tiền', years)
        check4 = (abs(cf_cash - bs_cash) < 1).all()
        print(f"Check 4 [Tiền (CF) == Tiền (BS)]: {'PASSED' if check4 else 'FAILED'}")
        
if __name__ == "__main__":
    from data_processor import DataProcessor
    processor = DataProcessor("data/hvn_fixed.xlsx")
    dfs = processor.load_and_normalize()
    validator = Validator(dfs)
    validator.run_checks()

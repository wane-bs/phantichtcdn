import pandas as pd
import numpy as np
import os

class DataProcessor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.sheets = ['BALANCE SHEET', 'CASH FLOW STATEMENT', 'INCOME STATEMENT', 'FINANCIAL INDEX']
        self.dataframes = {}

    def load_and_normalize(self):
        """Loads the excel file and normalizes columns and NaN values."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File không tồn tại: {self.file_path}")
            
        xls = pd.ExcelFile(self.file_path)
        
        for sheet in self.sheets:
            actual_sheet = sheet
            if sheet == 'BALANCE SHEET' and 'BALANCE SHEEET' in xls.sheet_names:
                actual_sheet = 'BALANCE SHEEET'
                
            if actual_sheet not in xls.sheet_names:
                print(f"Lưu ý: Sheet '{actual_sheet}' không tồn tại trong file Excel. Các sheet hiện có: {xls.sheet_names}")
                continue
                
            df = pd.read_excel(xls, sheet_name=actual_sheet)
            
            # Đổi tên cột đầu tiên thành 'Khoản mục'
            cols = df.columns.tolist()
            if len(cols) > 0:
                df.rename(columns={cols[0]: 'Khoản mục'}, inplace=True)
            
            # Strip whitespace in item names
            if 'Khoản mục' in df.columns:
                df['Khoản mục'] = df['Khoản mục'].astype(str).str.strip()
            
            # Fill NaN values with 0.0 for numeric calculation
            # Chú ý: Cột 'Khoản mục' không điền 0
            for col in df.columns:
                if col != 'Khoản mục':
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                    
            self.dataframes[sheet] = df
            
        return self.dataframes

if __name__ == "__main__":
    # Test read
    processor = DataProcessor(r"c:\chương_trình_phân_tich\hvn\hvn data.xlsx")
    dfs = processor.load_and_normalize()
    for name, df in dfs.items():
        print(f"--- {name} ---")
        print(f"Columns: {df.columns.tolist()}")
        print(df.head(3))
        print("\n")

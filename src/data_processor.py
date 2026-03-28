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
        
        # Mapping for resilience
        sheet_map = {
            'BALANCE SHEET': ['BALANCE SHEET', 'BALANCE SHEEET', 'bs'],
            'CASH FLOW STATEMENT': ['CASH FLOW STATEMENT', 'cf'],
            'INCOME STATEMENT': ['INCOME STATEMENT', 'is'],
            'FINANCIAL INDEX': ['FINANCIAL INDEX', 'fi']
        }
        
        for canonical_name, options in sheet_map.items():
            actual_sheet = None
            for opt in options:
                if opt in xls.sheet_names:
                    actual_sheet = opt
                    break
            
            if not actual_sheet:
                print(f"Lưu ý: Không tìm thấy sheet cho '{canonical_name}' (đã tìm: {options}). Các sheet hiện có: {xls.sheet_names}")
                continue
                
            df = pd.read_excel(xls, sheet_name=actual_sheet)
            
            # Collapse interleaved rows (Title row followed by 'HVN' value row)
            # Pattern: Row N has 'Doanh thu', Row N+1 has 'HVN'
            cleaned_rows = []
            skip_next = False
            
            # Rename first column to a standard name for processing
            first_col = df.columns[0]
            df.rename(columns={first_col: 'Khoản mục'}, inplace=True)
            df['Khoản mục'] = df['Khoản mục'].astype(str).str.strip()

            for i in range(len(df)):
                if skip_next:
                    skip_next = False
                    continue
                
                name = df.iloc[i]['Khoản mục']
                # If next row is 'HVN', it contains the values for current name
                if i < len(df) - 1:
                    next_item = str(df.iloc[i+1]['Khoản mục']).strip()
                    if next_item == 'HVN' and name != 'HVN':
                        # Use current name but next row's values
                        combined_row = df.iloc[i+1].copy()
                        combined_row['Khoản mục'] = name
                        cleaned_rows.append(combined_row)
                        skip_next = True
                        continue
                
                # If this is a normal row (not a header-value pair), keep it unless it's a standalone HVN
                if name != 'HVN':
                    cleaned_rows.append(df.iloc[i])
            
            df = pd.DataFrame(cleaned_rows)
            
            # Strip whitespace in item names again to be safe
            df['Khoản mục'] = df['Khoản mục'].astype(str).str.strip()
            
            # Fill NaN values with 0.0 for numeric columns
            for col in df.columns:
                if col != 'Khoản mục':
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                    
            self.dataframes[canonical_name] = df
            
        return self.dataframes

if __name__ == "__main__":
    # Test read
    processor = DataProcessor("data/hvn_fixed.xlsx")
    dfs = processor.load_and_normalize()
    for name, df in dfs.items():
        print(f"--- {name} ---")
        print(f"Columns: {df.columns.tolist()}")
        print(df.head(3))
        print("\n")

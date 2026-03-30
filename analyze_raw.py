import pandas as pd
import numpy as np

file_path = "c:/chương_trình_phân_tich/hvn/data/hvn.xlsx"
print(f"Reading {file_path} ...")
xls = pd.ExcelFile(file_path)

for sheet in xls.sheet_names:
    print(f"\n--- SHEET: {sheet} ---")
    df = pd.read_excel(xls, sheet)
    print(df.head())
    
    # We want to identify rows with negative values where they shouldn't be,
    # or find characteristics like negative Net Income, negative Equity, 
    # negative Cash Flow, always negative CCC, etc.
    if len(df.columns) > 1:
        years = df.columns[1:]
        for index, row in df.iterrows():
            item = str(row[df.columns[0]])
            try:
                vals = pd.to_numeric(row[years], errors='coerce')
                min_val = vals.min()
                max_val = vals.max()
                if min_val < 0:
                    # Print out any line that has negative values
                    print(f"[{item}] min: {min_val}, max: {max_val}")
            except:
                pass

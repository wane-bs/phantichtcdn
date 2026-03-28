import pandas as pd
import os

f = "data/hvn_data.xlsx"
output_file = "fi_items.txt"

with open(output_file, "w", encoding="utf-8") as out:
    xls = pd.ExcelFile(f)
    if 'FINANCIAL INDEX' in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name='FINANCIAL INDEX')
        out.write("=== FINANCIAL INDEX Items ===\n")
        for item in df.iloc[:, 0].tolist():
            out.write(f"{item}\n")
    else:
        out.write("Sheet FINANCIAL INDEX not found\n")

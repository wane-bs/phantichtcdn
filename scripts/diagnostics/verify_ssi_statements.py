import pandas as pd
import os

f = "data/SSI_HVN_Financial_statement_Income_Statement_12022026.xlsx"
output_file = "ssi_is_check.txt"

with open(output_file, "w", encoding="utf-8") as out:
    xls = pd.ExcelFile(f)
    out.write(f"Sheets: {xls.sheet_names}\n")
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet, nrows=50)
        out.write(f"\n--- Sheet: {sheet} ---\n")
        out.write(f"Columns: {df.columns.tolist()}\n")
        out.write(df.to_string())
        out.write("\n")

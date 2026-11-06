import pandas as pd
import os

f = "data/hvn_data.xlsx"
output_file = "market_data.txt"

with open(output_file, "w", encoding="utf-8") as out:
    xls = pd.ExcelFile(f)
    if 'FINANCIAL INDEX' in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name='FINANCIAL INDEX')
        market_items = ['Vốn hóa', 'Số CP lưu hành', 'P/E', 'P/B', 'P/S', 'EPS (VND)']
        df_market = df[df.iloc[:, 0].isin(market_items)]
        out.write(df_market.to_string())
    else:
        out.write("Sheet FINANCIAL INDEX not found\n")

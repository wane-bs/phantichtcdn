import pandas as pd
import os
import sys

files = ["data/hvn_data.xlsx", "data/hvn.xlsx"]
output_file = "inspect_results.txt"

with open(output_file, "w", encoding="utf-8") as out:
    cwd = os.getcwd()
    out.write(f"Current Working Directory: {cwd}\n")

    for f in files:
        full_path = os.path.join(cwd, f)
        out.write(f"\n{'='*50}\n")
        out.write(f"Inspecting: {full_path}\n")
        out.write(f"{'='*50}\n")
        
        if not os.path.exists(full_path):
            out.write(f"File not found: {full_path}\n")
            continue
            
        try:
            xls = pd.ExcelFile(full_path)
            out.write(f"Sheets: {xls.sheet_names}\n")
            
            for sheet in xls.sheet_names:
                out.write(f"\n--- Sheet: {sheet} ---\n")
                df = pd.read_excel(xls, sheet_name=sheet, nrows=10)
                out.write(f"Columns: {df.columns.tolist()}\n")
                out.write("First 5 rows (first 5 columns):\n")
                out.write(df.iloc[:5, :5].to_string())
                out.write("\n")
                
                # Check for specific expected patterns
                if 'Khoản mục' in df.columns:
                    out.write("Found 'Khoản mục' column.\n")
                else:
                    first_col = df.columns[0]
                    out.write(f"First column name: {first_col}\n")
                    
        except Exception as e:
            out.write(f"Error reading {f}: {e}\n")
            
print(f"Done. Results written to {output_file}")

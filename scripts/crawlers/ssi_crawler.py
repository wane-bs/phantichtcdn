"""
SSI Crawler - Module trích xuất BCTC và Chỉ số Tài chính SSI
Đọc và chuẩn hóa dữ liệu tài chính định kỳ của Vietnam Airlines (HVN).
"""

import os
import sys
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

def check_ssi_files():
    """
    Rà soát tính đầy đủ của bộ dữ liệu SSI trong data/
    """
    required_files = [
        "SSI_HVN_Financial_Ratio_26032026.xlsx",
        "SSI_HVN_Financial_Statement_Balance_Sheet_26032026.xlsx",
        "SSI_HVN_Financial_statement_Cash_Flow_26032026.xlsx",
        "SSI_HVN_Financial_statement_Income_Statement_26032026.xlsx"
    ]
    print("[SSI Crawler] Đang kiểm tra danh mục tệp BCTC SSI...")
    all_found = True
    for fname in required_files:
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.exists(fpath):
            print(f"  ✅ Tìm thấy: {fname} ({os.path.getsize(fpath):,} bytes)")
        else:
            print(f"  ❌ Thiếu: {fname}")
            all_found = False
    return all_found

def get_hvn_summary_metrics():
    """
    Trích xuất nhanh các chỉ số cốt lõi từ file tỷ số tài chính SSI.
    """
    ratio_file = os.path.join(DATA_DIR, "SSI_HVN_Financial_Ratio_26032026.xlsx")
    if not os.path.exists(ratio_file):
        print(f"[Cảnh báo] Chưa tìm thấy file tỷ số: {ratio_file}")
        return None

    try:
        df = pd.read_excel(ratio_file)
        print(f"[SSI Crawler] Đã trích xuất thông tin tỷ số ({df.shape[0]} chỉ số)")
        return df
    except Exception as e:
        print(f"[Lỗi] Đọc dữ liệu SSI: {e}")
        return None

if __name__ == "__main__":
    status = check_ssi_files()
    get_hvn_summary_metrics()
    sys.exit(0 if status else 1)

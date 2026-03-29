import time
import sys

def run_pipeline():
    print("=" * 40)
    print(" BẮT ĐẦU CHẠY PIPELINE TỪ DỮ LIỆU THÔ ")
    print("=" * 40)
    
    start_total = time.time()
    
    # STAGE 1
    print("\n[Stage 1] Processor - Đọc file hvn.xlsx")
    start = time.time()
    from data_processor import DataProcessor
    processor = DataProcessor("data/hvn.xlsx")
    processor.load_and_normalize()
    processor.save_outputs("output/1_processed")
    print(f"Hoàn thành Stage 1 ({time.time()-start:.2f}s)")

    # STAGE 2
    print("\n[Stage 2] Calculator - Chạy công thức rà soát & tính toán")
    start = time.time()
    from calculator import Calculator
    calc = Calculator(in_dir="output/1_processed")
    calc.run_all()
    calc.save_outputs("output/2_calculated")
    print(f"Hoàn thành Stage 2 ({time.time()-start:.2f}s)")
    
    # STAGE 3
    print("\n[Stage 3] Classifier - Phân loại Mô hình Doanh nghiệp")
    start = time.time()
    from business_classifier import BusinessClassifier
    classifier = BusinessClassifier(in_dir="output/2_calculated")
    classifier.run_all()
    classifier.save_outputs("output/3_classification")
    print(f"Hoàn thành Stage 3 ({time.time()-start:.2f}s)")
    
    # STAGE 4.1
    print("\n[Stage 4.1] Forecaster - Dự báo & Bóc tách")
    start = time.time()
    try:
        from forecaster import Forecaster
        forecaster = Forecaster(in_dir="output/2_calculated")
        fore_results = forecaster.run_all()
        forecaster.save_outputs(fore_results, "output/4_advanced")
        print(f"Hoàn thành Stage 4.1 ({time.time()-start:.2f}s)")
    except Exception as e:
        print(f"Lỗi Stage 4.1: {e}")
        
    # STAGE 5
    print("\n[Stage 5] Report Generator - Sinh Báo cáo Tự động (.md)")
    start = time.time()
    try:
        from report_generator import ReportGenerator
        reporter = ReportGenerator(calc_dir="output/2_calculated", class_dir="output/3_classification", out_dir="bao_cao")
        reporter.run_all()
        print(f"Hoàn thành Stage 5 ({time.time()-start:.2f}s)")
    except Exception as e:
        print(f"Lỗi Stage 5: {e}")
        
    print("\n" + "=" * 40)
    print(f" PIPELINE HOÀN TẤT THÀNH CÔNG ({time.time()-start_total:.2f}s)")
    print(" Dữ liệu đã sẵn sàng cho Streamlit tại thư mục output/")
    print(" Báo cáo phân tích đã được tạo tại thư mục bao_cao/")
    print("=" * 40)

if __name__ == "__main__":
    run_pipeline()

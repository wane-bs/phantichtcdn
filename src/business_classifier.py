import pandas as pd
import numpy as np

class BusinessClassifier:
    """
    Phân loại doanh nghiệp tự động dựa trên Ma trận định lượng tỷ số tài chính.
    Đầu vào là bộ dfs (DataFrames) đã được DataProcessor và Calculator xử lý.
    """
    def __init__(self, dfs_dict=None, in_dir=None):
        import os
        import pandas as pd
        if in_dir and os.path.exists(in_dir):
            self.dfs = {}
            for f in os.listdir(in_dir):
                if f.endswith('.csv'):
                    name = f.replace('.csv', '')
                    self.dfs[name] = pd.read_csv(os.path.join(in_dir, f))
        else:
            self.dfs = dfs_dict or {}

    def _get_row(self, df, pattern):
        row = df[df['Khoản mục'].str.contains(pattern, case=False, na=False, regex=True)]
        if not row.empty:
            return row.iloc[0]
        return None

    def _get_years(self, df):
        return [col for col in df.columns if col != 'Khoản mục']

    def classify(self):
        bs_df = self.dfs.get('BALANCE SHEET')
        is_df = self.dfs.get('INCOME STATEMENT')
        cf_df = self.dfs.get('CASH FLOW STATEMENT')
        
        if bs_df is None or is_df is None:
            return None

        years = self._get_years(bs_df)
        if not years:
            return None

        def _val(df, pattern, year):
            if df is None: return 0.0
            row = self._get_row(df, pattern)
            if row is not None:
                return float(row[year])
            return 0.0

        historical_models = {}
        for y in years:
            ta = _val(bs_df, r'^TỔNG TÀI SẢN$', y)
            if ta == 0: ta = 1.0 # Tránh chia cho 0

            rev = _val(is_df, r'^Doanh số thuần$', y)
            if rev == 0: rev = 1.0 # Tránh chia cho 0

            cogs = abs(_val(is_df, r'^Giá vốn hàng bán$', y))
            fa = _val(bs_df, r'^Tài sản cố định$', y)
            inv = _val(bs_df, r'^Hàng tồn kho', y)
            recv = _val(bs_df, r'phải thu ngắn hạn của khách hàng|^Các khoản phải thu$', y)
            cash = _val(bs_df, r'^Tiền và tương đương tiền', y)
            invest = _val(bs_df, r'^Giá trị thuần đầu tư ngắn hạn', y)
            sell_exp = abs(_val(is_df, r'^Chi phí bán hàng$', y))
            
            # Lấy Khấu hao từ CF nếu có
            depr = abs(_val(cf_df, r'^Khấu hao TSCĐ$', y)) if cf_df is not None else 0.0

            # Metrics (Tính %)
            fa_to_ta = (fa / ta) * 100
            inv_to_ta = (inv / ta) * 100
            recv_to_ta = (recv / ta) * 100
            cash_invest_to_ta = ((cash + invest) / ta) * 100
            
            gross_margin = ((rev - cogs) / rev) * 100
            depr_to_rev = (depr / rev) * 100
            sell_to_rev = (sell_exp / rev) * 100

            metrics = {
                'fa_to_ta': fa_to_ta,
                'depr_to_rev': depr_to_rev,
                'gross_margin': gross_margin,
                'inv_to_ta': inv_to_ta,
                'recv_to_ta': recv_to_ta,
                'sell_to_rev': sell_to_rev,
                'cash_invest_to_ta': cash_invest_to_ta
            }

            model = "Đa ngành / Thông thường (Diversified/Standard)"
            logic = []

            if fa_to_ta > 40 or depr_to_rev > 10:
                model = "Thâm dụng vốn (Capital-Intensive)"
                logic = [f"TSCĐ/TTS = {fa_to_ta:.1f}%", f"Khấu hao/Doanh thu = {depr_to_rev:.1f}%"]
            elif recv_to_ta > 70 and fa_to_ta < 5:
                model = "Dịch vụ tài chính (Financial Services)"
                logic = [f"Phải thu/TTS = {recv_to_ta:.1f}%", f"TSCĐ/TTS = {fa_to_ta:.1f}%"]
            elif fa_to_ta < 10 and gross_margin > 60:
                model = "Nhẹ tài sản / Công nghệ (Asset-Light/SaaS)"
                logic = [f"TSCĐ/TTS = {fa_to_ta:.1f}%", f"Biên LN Gộp = {gross_margin:.1f}%"]
            elif inv_to_ta > 30 and gross_margin < 25:
                model = "Bán lẻ & Phân phối (Retail/Inventory-based)"
                logic = [f"Kho/TTS = {inv_to_ta:.1f}%", f"Biên LN Gộp = {gross_margin:.1f}%"]
            elif sell_to_rev > 20 and cash_invest_to_ta > 20: 
                model = "Thương mại điện tử / Nền tảng (Platform)"
                logic = [f"Chi phí BH/Doanh thu = {sell_to_rev:.1f}%", f"Tiền/TTS = {cash_invest_to_ta:.1f}%"]
                
            historical_models[y] = {
                'Mô hình': model,
                'Minh chứng': ' | '.join(logic) if logic else "Không có đặc trưng dị biệt đủ lớn.",
                'Metrics': metrics
            }

        # LUẬT ĐA SỐ 5 KỲ (Tie-breaker rules)
        import collections

        last_5 = years[-5:]
        models_5 = [historical_models[y]['Mô hình'] for y in last_5]
        counter_5 = collections.Counter(models_5)
        
        most_common_5 = counter_5.most_common()
        if len(most_common_5) == 1 or most_common_5[0][1] > most_common_5[1][1]:
            core_model = most_common_5[0][0]
        else:
            if len(years) > 5:
                prev_5 = years[-10:-5]
                models_10 = [historical_models[y]['Mô hình'] for y in (prev_5 + last_5)]
                counter_10 = collections.Counter(models_10)
                most_common_10 = counter_10.most_common()
                if len(most_common_10) == 1 or most_common_10[0][1] > most_common_10[1][1]:
                    core_model = most_common_10[0][0]
                else:
                    scores = collections.defaultdict(float)
                    for m in models_10: scores[m] += 1.0
                    scores[historical_models[years[-1]]['Mô hình']] += 2.5
                    core_model = max(scores.items(), key=lambda x: x[1])[0]
            else:
                scores = collections.defaultdict(float)
                for m in models_5: scores[m] += 1.0
                scores[historical_models[years[-1]]['Mô hình']] += 2.5
                core_model = max(scores.items(), key=lambda x: x[1])[0]

        core_logic = historical_models[years[-1]]['Minh chứng'] if core_model == historical_models[years[-1]]['Mô hình'] else f"Xác định đại diện 5 năm. Counter: {counter_5.get(core_model, 0)}/{len(last_5)}"

        # NHẬN DIỆN DỊCH CHUYỂN
        shift_analysis = "Không có sự dịch chuyển mô hình trong thời gian gần đây."
        if len(years) >= 2:
            model_t = historical_models[years[-1]]['Mô hình']
            model_t1 = historical_models[years[-2]]['Mô hình']
            if model_t != model_t1:
                shift_analysis = f"Năm {years[-1]} có sự dịch chuyển cốt lõi từ '{model_t1}' sang '{model_t}'."
            elif model_t != core_model:
                shift_analysis = f"Dấu hiệu dịch chuyển khỏi mô hình cốt lõi '{core_model}' sang '{model_t}'."

        # KIỂM TRA SỨC KHỎE VÀ KHUYẾN NGHỊ ĐẦU TƯ
        eq_row = self._get_row(bs_df, r'^VỐN CHỦ SỞ HỮU$')
        negative_equity = False
        if eq_row is not None:
            eq_vals = eq_row[years].astype(float)
            negative_years = eq_vals[eq_vals < 0].index.tolist()
            if len(negative_years) > 0 and years[-1] in negative_years:
                negative_equity = True
        
        anomaly_numeric = self.dfs.get('ANOMALY_NUMERIC', {})
        altman_latest = anomaly_numeric.get('altman', [0])[-1] if anomaly_numeric.get('altman') else None
        
        health_eval = "Mạnh (Ổn định)"
        recommendation = "CÂN NHẮC ĐẦU TƯ / THEO DÕI"

        if negative_equity or (altman_latest is not None and altman_latest < 1.1):
            health_eval = "Khủng hoảng cơ cấu vốn (Rủi ro vỡ nợ cao)"
            recommendation = "KHÔNG NÊN ĐẦU TƯ (Rủi ro bao trùm)"
        else:
            if altman_latest is not None and altman_latest > 2.6:
                health_eval = "Mạnh (Cơ cấu vốn và thanh khoản an toàn)"
                recommendation = "CÓ THỂ XEM XÉT ĐẦU TƯ"
            else:
                health_eval = "Trung bình / Vùng xám"

        result = {
            'Lịch sử Mô hình': historical_models,
            'Mô hình cốt lõi': core_model,
            'Minh chứng': core_logic,
            'Dịch chuyển': shift_analysis,
            'Sức khỏe Tài chính': health_eval,
            'Khuyến nghị Đầu tư': recommendation,
            'Năm tham chiếu': years[-1]
        }
        
        self.dfs['BUSINESS_MODEL'] = result
        return self.dfs

    def run_all(self):
        return self.classify()

    def save_outputs(self, out_dir="output/3_classification"):
        import os
        import json
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        
        if 'BUSINESS_MODEL' in self.dfs:
            result = self.dfs['BUSINESS_MODEL']
            # Save JSON
            json_path = os.path.join(out_dir, "business_model.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            print(f"Saved: {json_path}")
            
            md_path = os.path.join(out_dir, "business_model_report.md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# Phân loại tự động Mô hình Doanh nghiệp\n\n")
                f.write(f"**Năm tham chiếu:** {result['Năm tham chiếu']}\n\n")
                f.write(f"**Mô hình Lõi (5 năm):** {result['Mô hình cốt lõi']}\n\n")
                f.write(f"**Minh chứng:** {result['Minh chứng']}\n\n")
                f.write(f"**Dịch chuyển:** {result['Dịch chuyển']}\n\n")
                f.write(f"## Đánh giá & Khuyến nghị\n")
                f.write(f"- Sức khỏe Tài chính: **{result['Sức khỏe Tài chính']}**\n")
                f.write(f"- Khuyến nghị: **{result['Khuyến nghị Đầu tư']}**\n\n")
                
                f.write(f"## Lịch sử Các Năm\n")
                hist = result['Lịch sử Mô hình']
                for y in sorted(hist.keys(), reverse=True):
                    f.write(f"- **{y}**: {hist[y]['Mô hình']} (Metrics: {hist[y].get('Metrics', {})})\n")
            print(f"Saved: {md_path}")

if __name__ == "__main__":
    from data_processor import DataProcessor
    from calculator import Calculator
    
    # Optional Test Flow reading directly from processed output
    calc = Calculator(in_dir="output/2_calculated")
    if not calc.dfs:
        print("Please run pipeline_runner.py to generate 2_calculated first.")
    else:
        classifier = BusinessClassifier(calc.dfs)
        dfs = classifier.run_all()
        classifier.save_outputs()
        
        print("=== Phân loại Doanh nghiệp ===")
        print(f"Mô hình: {dfs['BUSINESS_MODEL']['Mô hình']}")
        print(f"Minh chứng: {dfs['BUSINESS_MODEL']['Minh chứng']}")

"""
ml_analyzer.py — Module ML/Econometrics cho HVN Dashboard
==========================================================
Bao gồm:
  - Cross-Correlation Lead-Lag Heatmap
  - ElasticNet Impact Coefficients
  - PLSR VIP Scores
  - Sensitivity Line (What-if cơ cấu)

Triết lý: Không gọi .predict(). Chỉ trích xuất hệ số và trọng số
để giải thích "nhân tố nào ảnh hưởng mạnh nhất và theo chiều nào".
"""

import numpy as np
import pandas as pd

try:
    from sklearn.linear_model import ElasticNetCV
    from sklearn.cross_decomposition import PLSRegression
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def _compute_vip(pls_model, X):
    """Tính VIP Score cho mô hình PLSR."""
    t = pls_model.x_scores_
    w = pls_model.x_weights_
    q = pls_model.y_loadings_

    p, h = w.shape
    vips = np.zeros((p,))

    s = np.diag(t.T @ t @ q.T @ q).reshape(h, -1)
    total_s = np.sum(s)

    for i in range(p):
        weight = np.array([(w[i, j] / np.linalg.norm(w[:, j])) ** 2 for j in range(h)])
        vips[i] = np.sqrt(p * (s.T @ weight) / total_s)

    return vips


class MLAnalyzer:
    def __init__(self, dfs_dict):
        self.dfs = dfs_dict
        self._feature_df = None
        self._feature_names = None

    def _get_row(self, df, pattern):
        row = df[df['Khoản mục'].str.contains(pattern, case=False, na=False, regex=True)]
        if not row.empty:
            return row.iloc[0]
        return None

    def _get_years(self, df):
        return [c for c in df.columns if c != 'Khoản mục']

    def _build_feature_matrix(self):
        """
        Xây dựng ma trận đặc trưng từ các chỉ số tài chính chính.
        Trả về DataFrame với các biến đã chuẩn hóa và chuỗi target (ROA).
        """
        fi = self.dfs.get('FINANCIAL INDEX')
        is_df = self.dfs.get('INCOME STATEMENT')
        bs_df = self.dfs.get('BALANCE SHEET')

        if fi is None or is_df is None or bs_df is None:
            return None, None, None

        years = self._get_years(fi)

        def get_series(df, pattern):
            row = self._get_row(df, pattern)
            if row is None:
                return None
            vals = row[years].astype(float)
            return vals

        # Các biến đặc trưng (Features)
        features = {
            'Biên GP (%)': get_series(fi, r'Biên lợi nhuận gộp|Gross Margin'),
            'Vòng quay TS': get_series(fi, r'Vòng quay tổng tài sản|Asset Turnover'),
            'DSO (ngày)': get_series(fi, r'^DSO'),
            'DIO (ngày)': get_series(fi, r'^DIO'),
            'D/E Ratio': get_series(fi, r'Nợ phải trả / Vốn chủ sở hữu|D/E'),
            'Current Ratio': get_series(fi, r'Chỉ số thanh toán hiện thời|Current Ratio'),
            'Net Debt/EBITDA': get_series(fi, r'^Net Debt / EBITDA$'),
        }

        # Target: ROA
        target = get_series(fi, r'^ROA')
        if target is None:
            # Fallback: tính ROA từ LNST / Tổng TS
            ni_row = self._get_row(is_df, r'^Lãi/\(lỗ\) thuần sau thuế$')
            ta_row = self._get_row(bs_df, r'^TỔNG TÀI SẢN$')
            if ni_row is not None and ta_row is not None:
                ni = ni_row[years].astype(float)
                ta = ta_row[years].astype(float).replace(0, np.nan)
                target = (ni / ta * 100).fillna(0)

        # Lọc các feature có dữ liệu
        valid_features = {k: v for k, v in features.items() if v is not None}

        if not valid_features or target is None:
            return None, None, None

        feat_df = pd.DataFrame(valid_features, index=years).apply(pd.to_numeric, errors='coerce').fillna(0)
        target_series = target.reindex(years).fillna(0)

        self._feature_df = feat_df
        self._feature_names = list(feat_df.columns)

        return feat_df, target_series, years

    # =========================================================================
    # Cross-Correlation Lead-Lag
    # =========================================================================
    def cross_correlation_leadlag(self, target_name='ROA', max_lag=4):
        """
        Tính hệ số tương quan chéo giữa từng biến đặc trưng và biến mục tiêu
        tại các độ trễ k từ -max_lag đến +max_lag.
        
        Lag dương: biến dẫn trước target (leading indicator)
        Lag âm: biến theo sau target (lagging indicator)
        
        Trả về DataFrame shape (n_features, 2*max_lag+1)
        """
        feat_df, target_series, years = self._build_feature_matrix()
        if feat_df is None:
            return None

        lags = list(range(-max_lag, max_lag + 1))
        ccf_matrix = pd.DataFrame(index=self._feature_names, columns=[f'Lag {l:+d}' for l in lags])

        for feat in self._feature_names:
            x = feat_df[feat].values.astype(float)
            y = target_series.values.astype(float)
            n = len(x)

            for lag in lags:
                if lag >= 0:
                    x_lag = x[:n - lag] if lag > 0 else x
                    y_lag = y[lag:] if lag > 0 else y
                else:
                    x_lag = x[-lag:]
                    y_lag = y[:n + lag]

                if len(x_lag) < 3 or len(y_lag) < 3:
                    ccf_matrix.loc[feat, f'Lag {lag:+d}'] = 0.0
                    continue

                with np.errstate(invalid='ignore', divide='ignore'):
                    corr = np.corrcoef(x_lag, y_lag)[0, 1]
                ccf_matrix.loc[feat, f'Lag {lag:+d}'] = round(float(corr) if not np.isnan(corr) else 0.0, 3)

        ccf_matrix = ccf_matrix.astype(float)
        return ccf_matrix

    # =========================================================================
    # ElasticNet Impact
    # =========================================================================
    def elasticnet_impact(self, target_name='ROA'):
        """
        Fit ElasticNetCV trên features → target.
        Trả về hệ số hồi quy (KHÔNG gọi .predict()).
        Output: DataFrame với Feature, Coefficient, Direction
        """
        feat_df, target_series, years = self._build_feature_matrix()
        if feat_df is None or not SKLEARN_AVAILABLE:
            return None

        X = feat_df.values
        y = target_series.values

        if len(y) < 3:
            return None

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        try:
            model = ElasticNetCV(
                cv=min(3, len(y)),
                max_iter=10000,
                l1_ratio=[0.3, 0.5, 0.7, 0.9],
                alphas=np.logspace(-3, 1, 20)
            )
            model.fit(X_scaled, y)

            coefs = model.coef_
            result_df = pd.DataFrame({
                'Nhân tố': self._feature_names,
                'Hệ số ElasticNet': [round(c, 4) for c in coefs],
                'Chiều tác động': ['+' if c > 0 else ('-' if c < 0 else '0') for c in coefs],
                'Mức độ': [abs(round(c, 4)) for c in coefs],
            }).sort_values('Mức độ', ascending=False).reset_index(drop=True)

            return {
                'coef_df': result_df,
                'alpha': round(model.alpha_, 6),
                'l1_ratio': round(model.l1_ratio_, 2),
                'feature_names': self._feature_names,
                'coef_dict': dict(zip(self._feature_names, coefs.tolist())),
            }
        except Exception as e:
            print(f"ElasticNet error: {e}")
            return None

    # =========================================================================
    # PLSR VIP Scores
    # =========================================================================
    def plsr_vip(self, target_name='ROA', n_components=None):
        """
        Fit PLSR và tính VIP Score.
        VIP > 1: nhân tố quan trọng
        VIP < 1: nhân tố ít quan trọng
        
        Trả về DataFrame với Feature, VIP Score
        """
        feat_df, target_series, years = self._build_feature_matrix()
        if feat_df is None or not SKLEARN_AVAILABLE:
            return None

        X = feat_df.values
        y = target_series.values.reshape(-1, 1)

        if len(y) < 3:
            return None

        n_feat = X.shape[1]
        if n_components is None:
            n_components = min(2, n_feat, len(y) - 1)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        try:
            pls = PLSRegression(n_components=n_components, max_iter=1000)
            pls.fit(X_scaled, y)
            vip_scores = _compute_vip(pls, X_scaled)

            result_df = pd.DataFrame({
                'Nhân tố': self._feature_names,
                'VIP Score': [round(v, 3) for v in vip_scores],
                'Quan trọng': ['✅ Cao (VIP>1)' if v > 1 else '⚪ Thấp' for v in vip_scores],
            }).sort_values('VIP Score', ascending=False).reset_index(drop=True)

            return result_df
        except Exception as e:
            print(f"PLSR VIP error: {e}")
            return None

    # =========================================================================
    # Sensitivity Line
    # =========================================================================
    def sensitivity_line(self, target_name='ROA', delta_pct=0.20):
        """
        Tính ΔTarget = Σ ΔFeature_i × ElasticNet_Coef_i cho 3 kịch bản:
          - Kịch bản hiện tại (0% thay đổi)
          - Kịch bản tích cực (+delta_pct%)
          - Kịch bản tiêu cực (-delta_pct%)
        
        Chỉ dùng các nhân tố có VIP > 1.
        Trả về DataFrame để vẽ 3 đường trên cùng trục.
        """
        en_result = self.elasticnet_impact(target_name)
        vip_result = self.plsr_vip(target_name)

        if en_result is None:
            return None

        feat_df, target_series, years = self._build_feature_matrix()
        if feat_df is None:
            return None

        coef_dict = en_result['coef_dict']

        # Lọc nhân tố VIP > 1 nếu có
        important_features = list(coef_dict.keys())
        if vip_result is not None:
            high_vip = vip_result[vip_result['VIP Score'] > 1]['Nhân tố'].tolist()
            if high_vip:
                important_features = [f for f in important_features if f in high_vip]

        if not important_features:
            important_features = list(coef_dict.keys())

        baseline = target_series.values.copy()

        # Tính delta cho từng kịch bản
        delta_positive = np.zeros(len(years))
        delta_negative = np.zeros(len(years))

        for feat in important_features:
            coef = coef_dict.get(feat, 0.0)
            feat_vals = feat_df[feat].values if feat in feat_df.columns else np.zeros(len(years))
            delta_positive += feat_vals * delta_pct * coef
            delta_negative += feat_vals * (-delta_pct) * coef

        result_df = pd.DataFrame({
            'Năm': years,
            'Hiện tại': baseline,
            f'Tích cực (+{int(delta_pct*100)}%)': baseline + delta_positive,
            f'Tiêu cực (-{int(delta_pct*100)}%)': baseline + delta_negative,
        })

        return {
            'df': result_df,
            'years': years,
            'important_features': important_features,
            'target_name': target_name,
            'delta_pct': delta_pct,
        }

    # =========================================================================
    # RUN ALL
    # =========================================================================
    def run_all(self):
        """Chạy tất cả phân tích ML và trả về dict kết quả."""
        results = {}

        # Xây dựng feature matrix (cache)
        feat_df, target_series, years = self._build_feature_matrix()

        # Cross-Correlation
        ccf = self.cross_correlation_leadlag()
        if ccf is not None:
            results['CCF_MATRIX'] = ccf

        # ElasticNet
        en = self.elasticnet_impact()
        if en is not None:
            results['ELASTICNET'] = en

        # PLSR VIP
        vip = self.plsr_vip()
        if vip is not None:
            results['VIP_SCORES'] = vip

        # Sensitivity Lines
        sens = self.sensitivity_line()
        if sens is not None:
            results['SENSITIVITY'] = sens

        return results

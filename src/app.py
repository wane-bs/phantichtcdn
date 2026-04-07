import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from data_processor import DataProcessor
from calculator import Calculator
from validator import Validator
from forecaster import Forecaster
import os
from business_classifier import BusinessClassifier

# Lấy thư mục gốc ('hvn') thay vì thay đổi CWD toàn cục do dễ làm lỗi Streamlit Watchdog
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="HVN Financial Analytics", layout="wide", page_icon="✈️")

# ── Custom CSS ──
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 20px; border-radius: 12px;
        border: 1px solid #0f3460; margin-bottom: 10px;
    }
    .info-box {
        background: rgba(15, 52, 96, 0.3);
        border-left: 3px solid #0f3460;
        padding: 10px 14px;
        border-radius: 4px;
        font-size: 0.85em;
        margin-bottom: 8px;
    }
    h1 { color: #e94560; }
    h2 { color: #0f3460; }
</style>
""", unsafe_allow_html=True)

DARK_TEMPLATE = dict(
    template='plotly_dark',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
)

COLORS = {
    'red': '#e94560',
    'blue': '#0f3460',
    'purple': '#533483',
    'green': '#2b9348',
    'orange': '#ff6b35',
    'cyan': '#5dade2',
    'yellow': '#f9c74f',
    'teal': '#43aa8b',
}

@st.cache_data
def load_data(_v=8):  # bump _v to invalidate old cache
    import os
    import json
    dfs = {}
    calc_dir = os.path.join(PROJECT_ROOT, "output/2_calculated")
    
    if os.path.exists(calc_dir):
        for f in os.listdir(calc_dir):
            name = f.replace('.csv', '').replace('.json', '')
            if f.endswith('.csv'):
                dfs[name] = pd.read_csv(os.path.join(calc_dir, f))
            elif f.endswith('.json'):
                with open(os.path.join(calc_dir, f), 'r', encoding='utf-8') as file:
                    dfs[name] = json.load(file)
    else:
        # Fallback if pipeline not run yet
        st.warning("Dữ liệu chưa có sẵn trong output/. Vui lòng bấm 'Chạy Pipeline' ở sidebar.")
        
    cls_file = os.path.join(PROJECT_ROOT, "output/3_classification/business_model.json")
    if os.path.exists(cls_file):
        with open(cls_file, 'r', encoding='utf-8') as file:
            dfs['BUSINESS_MODEL'] = json.load(file)
            
    return dfs

@st.cache_data
def load_forecaster_data(_dfs):
    f = Forecaster(_dfs)
    return f.run_all(), f

def get_row_data(df, pattern):
    row = df[df['Khoản mục'].str.contains(pattern, case=False, na=False, regex=True)]
    if not row.empty:
        years = [c for c in df.columns if c != 'Khoản mục']
        return pd.Series(row.iloc[0][years].values, index=years, dtype=float)
    return None

def get_fi_row(fi, pattern):
    return get_row_data(fi, pattern)

def plot_line_multi(data_dict, title, years, y_suffix=''):
    fig = go.Figure()
    color_list = list(COLORS.values())
    for i, (name, vals) in enumerate(data_dict.items()):
        if vals is not None:
            fig.add_trace(go.Scatter(
                x=years, y=vals, name=name, mode='lines+markers',
                line=dict(color=color_list[i % len(color_list)], width=2.5),
                marker=dict(size=8)
            ))
    fig.update_layout(
        title=title, **DARK_TEMPLATE,
        font=dict(size=12), legend=dict(orientation='h', y=-0.15),
        yaxis_title=y_suffix
    )
    return fig


def main():
    # Custom Sidebar with Pipeline Runner
    with st.sidebar:
        st.header("⚙️ Quản lý Dữ liệu")
        st.markdown("Hệ thống hoạt động với kiến trúc File-based Pipeline.")
        if st.button("🚀 Chạy Pipeline Cập nhật Dữ liệu", use_container_width=True):
            import subprocess
            import sys
            with st.spinner("Đang chạy pipeline... (vui lòng đợi vài giây)"):
                try:
                    pipe_script = os.path.join(PROJECT_ROOT, "src", "pipeline_runner.py")
                    subprocess.run([sys.executable, pipe_script], cwd=PROJECT_ROOT, check=True)
                    st.success("Cập nhật dữ liệu thành công!")
                    load_data.clear() # Invalidate cache
                    load_forecaster_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi pipeline: {e}")

    st.title("Vietnam Airlines (HVN) — Financial Analytics Dashboard")

    try:
        dfs = load_data()
        if not dfs:
            return
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    warnings_info = dfs.get('data_warnings', {})
    if warnings_info.get('active'):
        st.error(f"🚨 **CẢNH BÁO TÍN HIỆU GIẢ (DATA ANOMALY ALERT)**\n\n"
                 f"- {warnings_info.get('equity_warning', '')}\n"
                 f"- {warnings_info.get('ni_warning', '')}\n\n"
                 "*(Khuyến nghị: Chuyển trọng tâm phân tích từ Định giá Cổ phiếu sang Dòng tiền & Thanh khoản)*")


    bs = dfs.get('BALANCE SHEET')
    is_df = dfs.get('INCOME STATEMENT')
    cf = dfs.get('CASH FLOW STATEMENT')
    fi = dfs.get('FINANCIAL INDEX')
    dupont = dfs.get('DUPONT')
    dupont_impact = dfs.get('DUPONT_IMPACT')
    dupont_betas = dfs.get('DUPONT_BETAS', {})
    dupont_roa = dfs.get('DUPONT_ROA')
    dupont_roic = dfs.get('DUPONT_ROIC')
    dupont_impact_roa = dfs.get('DUPONT_IMPACT_ROA')
    dupont_impact_roic = dfs.get('DUPONT_IMPACT_ROIC')
    dupont_betas_roa = dfs.get('DUPONT_BETAS_ROA', {})
    dupont_betas_roic = dfs.get('DUPONT_BETAS_ROIC', {})
    cash_inout = dfs.get('CASH_INOUT')
    liquidity_cf = dfs.get('LIQUIDITY_CASHFLOW')
    anomaly_numeric = dfs.get('ANOMALY_NUMERIC', {})
    years = [c for c in bs.columns if c != 'Khoản mục']

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📊 Cơ cấu Tài chính", "🔍 Chất lượng BCTC", "💡 Kết luận Mẫu hình",
        "⚡ Hiệu suất Mẫu hình", "🤖 Phân tích Nâng cao", "📁 Bảng dữ liệu", "📄 Báo cáo Tổng hợp",
        "🧪 Kiểm định Thống kê"
    ])
    
    bm_data = dfs.get('BUSINESS_MODEL', {})
    historical_models = bm_data.get('Lịch sử Mô hình', {})
    core_model = bm_data.get('Mô hình cốt lõi', 'Chưa phân loại')
    core_logic = bm_data.get('Minh chứng', '')
    shift_analysis = bm_data.get('Dịch chuyển', '')
    health_eval = bm_data.get('Sức khỏe Tài chính', 'Chưa đánh giá')
    recommendation = bm_data.get('Khuyến nghị Đầu tư', 'Chưa có khuyến nghị')
    ref_year = bm_data.get('Năm tham chiếu', years[-1] if years else '')
    metrics = historical_models.get(str(ref_year), {}).get('Metrics', {}) if historical_models else {}


    # ═══════════════════════════════════════════════════════════════════════
    # TAB 1: SURVIVAL DASHBOARD
    # ═══════════════════════════════════════════════════════════════════════
    with tab1:
        st.header("Khả năng sinh tồn (Dòng tiền & Cấu trúc vốn)")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Cơ cấu Nợ vs Vốn Chủ Sở Hữu")
            nnh = get_row_data(bs, r'^Nợ ngắn hạn$')
            ndh = get_row_data(bs, r'^Nợ dài hạn$')
            equity = get_row_data(bs, r'^VỐN CHỦ SỞ HỮU$')

            if nnh is not None and ndh is not None and equity is not None:
                fig = go.Figure(data=[
                    go.Bar(name='Nợ ngắn hạn', x=years, y=nnh,
                           marker_color=COLORS['red'], opacity=0.85,
                           offsetgroup=0),
                    go.Bar(name='Nợ dài hạn', x=years, y=ndh,
                           marker_color=COLORS['orange'], opacity=0.75,
                           offsetgroup=0, base=nnh),
                    go.Bar(name='Vốn Chủ Sở Hữu', x=years, y=equity,
                           marker_color=COLORS['purple'], opacity=0.85,
                           offsetgroup=1)
                ])
                fig.update_layout(
                    barmode='group', **DARK_TEMPLATE,
                    title="Cơ cấu Nguồn vốn: Nợ NH / Nợ DH / VCSH",
                    legend=dict(orientation='h', y=-0.15, font=dict(size=10)),
                )
                st.plotly_chart(fig, use_container_width=True)

#        with col2:
#            st.subheader("Dòng tiền theo hoạt động (100% Stacked Area)")
#            ocf = get_row_data(cf, r'^Lưu chuyển tiền thuần từ các hoạt động sản xuất kinh doanh$')
#            icf = get_row_data(cf, r'^Lưu chuyển tiền tệ ròng từ hoạt động đầu tư$')
#            fcf = get_row_data(cf, r'^Lưu chuyển tiền tệ từ hoạt động tài chính$')
#
#            if ocf is not None and icf is not None and fcf is not None:
#                abs_ocf = ocf.abs(); abs_icf = icf.abs(); abs_fcf = fcf.abs()
#                total = (abs_ocf + abs_icf + abs_fcf).replace(0, 1)
#                pct_ocf = abs_ocf / total * 100
#                pct_icf = abs_icf / total * 100
#                pct_fcf = abs_fcf / total * 100
#
#                fig2 = go.Figure()
#                fig2.add_trace(go.Scatter(x=years, y=pct_ocf, name='OCF (HĐKD)',
#                    mode='lines', stackgroup='one', groupnorm='percent',
#                    fillcolor='rgba(43,147,72,0.6)', line=dict(color=COLORS['green'], width=0.5)))
#                fig2.add_trace(go.Scatter(x=years, y=pct_icf, name='ICF (Đầu tư)',
#                    mode='lines', stackgroup='one',
#                    fillcolor='rgba(233,69,96,0.6)', line=dict(color=COLORS['red'], width=0.5)))
#                fig2.add_trace(go.Scatter(x=years, y=pct_fcf, name='FCF (Tài chính)',
#                    mode='lines', stackgroup='one',
#                    fillcolor='rgba(83,52,131,0.6)', line=dict(color=COLORS['purple'], width=0.5)))
#                fig2.update_layout(
#                    title="Tỷ trọng dòng tiền theo hoạt động",
#                    yaxis_title='%', yaxis=dict(range=[0, 100]),
#                    **DARK_TEMPLATE,
#                    legend=dict(orientation='h', y=-0.15)
#                )
#                st.plotly_chart(fig2, use_container_width=True)

        # Cấu trúc Tài sản
        st.subheader("Cấu trúc Tài sản (100% Stacked Bar)")
        items_short = ['Tiền và tương đương tiền', 'Giá trị thuần đầu tư ngắn hạn',
                       'Các khoản phải thu', 'Hàng tồn kho, ròng', 'Tài sản lưu động khác']
        items_long = ['Phải thu dài hạn', 'Tài sản cố định', 'Tài sản dở dang dài hạn',
                      'Đầu tư dài hạn', 'Tài sản dài hạn khác']
        colors_map = {
            'Tiền và tương đương tiền': '#2b9348', 'Giá trị thuần đầu tư ngắn hạn': '#55a630',
            'Các khoản phải thu': '#80b918', 'Hàng tồn kho, ròng': '#aacc00',
            'Tài sản lưu động khác': '#d4d700',
            'Phải thu dài hạn': '#0f3460', 'Tài sản cố định': '#1a508b',
            'Tài sản dở dang dài hạn': '#2e86c1', 'Đầu tư dài hạn': '#5dade2',
            'Tài sản dài hạn khác': '#85c1e9',
        }
        fig_asset = go.Figure()
        for item in items_short + items_long:
            row_data = get_row_data(bs, f'^{item}')
            ta_data = get_row_data(bs, r'^TỔNG TÀI SẢN$')
            if row_data is not None and ta_data is not None:
                pct = row_data.abs() / ta_data.abs() * 100
                fig_asset.add_trace(go.Bar(name=item, x=years, y=pct,
                    marker_color=colors_map.get(item, '#888')))
        fig_asset.update_layout(
            barmode='stack', **DARK_TEMPLATE,
            title='Tỷ trọng tài sản qua các năm (% Tổng TS)',
            yaxis_title='%', yaxis=dict(range=[0, 105]),
            legend=dict(orientation='h', y=-0.25, font=dict(size=10))
        )
        st.plotly_chart(fig_asset, use_container_width=True)

        # ── Biến động Tài sản qua các năm (Line Chart) ──
        st.subheader("Biến động Tài sản qua các năm (tỷ VND)")
        curr_assets = get_row_data(bs, r'^TÀI SẢN NGẮN HẠN$')
        total_assets = get_row_data(bs, r'^TỔNG TÀI SẢN$')
        fixed_assets = get_row_data(bs, f'^Tài sản cố định')
        
        if curr_assets is not None and total_assets is not None and fixed_assets is not None:
            # Scale to tỷ VND (÷ 1e9)
            SCALE_T = 1e9
            fig_trend = plot_line_multi({
                'Tài sản ngắn hạn': curr_assets / SCALE_T,
                'Tổng tài sản': total_assets / SCALE_T,
                'Tài sản cố định': fixed_assets / SCALE_T
            }, "Xu hướng biến động Tài sản (tỷ VND)", years, 'tỷ VND')
            
            fig_trend.update_layout(
                hovermode='x unified',
                legend=dict(orientation='h', y=-0.2)
            )
            st.plotly_chart(fig_trend, use_container_width=True)

        # Net Debt / EBITDA
        nd_ebitda = get_fi_row(fi, r'^Net Debt / EBITDA$')
        if nd_ebitda is not None:
            st.subheader("Net Debt / EBITDA (Số năm trả hết nợ)")
            fig_nd = go.Figure(go.Bar(
                x=years, y=nd_ebitda, marker_color=COLORS['orange'],
                text=[f'{v:.1f}x' for v in nd_ebitda], textposition='outside'
            ))
            fig_nd.update_layout(**DARK_TEMPLATE)
            st.plotly_chart(fig_nd, use_container_width=True)

        # Cash Inflow / Outflow Line & Marker
        # if cash_inout is not None:
        #     st.subheader("Thực Thu − Thực Chi − Dòng tiền Ròng")
        #     ci_years = [c for c in cash_inout.columns if c != 'Khoản mục']
        #     total_in = get_row_data(cash_inout, r'^═══ TỔNG THỰC THU')
        #     total_out = get_row_data(cash_inout, r'^═══ TỔNG THỰC CHI')
        #     net = get_row_data(cash_inout, r'^═══ DÒNG TIỀN RÒNG')
        #     if total_in is not None and total_out is not None:
        #         fig_ci = go.Figure()
        #         fig_ci.add_trace(go.Scatter(
        #             x=ci_years, y=total_in, name='Tổng Thu',
        #             mode='lines+markers', line=dict(color=COLORS['green'], width=3),
        #             marker=dict(size=10, symbol='triangle-up')))
        #         fig_ci.add_trace(go.Scatter(
        #             x=ci_years, y=total_out, name='Tổng Chi',
        #             mode='lines+markers', line=dict(color=COLORS['red'], width=3),
        #             marker=dict(size=10, symbol='triangle-down')))
        #         if net is not None:
        #             net_colors = [COLORS['green'] if v >= 0 else COLORS['red'] for v in net]
        #             fig_ci.add_trace(go.Bar(
        #                 x=ci_years, y=net, name='Dòng tiền Ròng',
        #                 marker_color=net_colors, opacity=0.5,
        #                 text=[f'{v:,.0f}' for v in net], textposition='outside'))
        #         fig_ci.update_layout(
        #             title='Thực Thu vs Thực Chi & Dòng tiền Ròng (tỷ VND)',
        #             **DARK_TEMPLATE,
        #             legend=dict(orientation='h', y=-0.15),
        #             barmode='overlay'
        #         )
        #         st.plotly_chart(fig_ci, use_container_width=True)

        # ── DSCR & Liquidity Runway ──
        if liquidity_cf is not None:
            st.divider()
            st.subheader("Diễn biến DSCR và Khoảng cách Sinh tồn (Liquidity Runway)")
            liq_years = [c for c in liquidity_cf.columns if c != 'Khoản mục']
            dscr_vals = get_row_data(liquidity_cf, r'^DSCR')
            stressed_dscr = get_row_data(liquidity_cf, r'^STRESS DSCR')
            runway_vals = get_row_data(liquidity_cf, r'^Liquidity Runway')

            col_dscr, col_runway = st.columns(2)

            with col_dscr:
                if dscr_vals is not None:
                    fig_dscr = go.Figure()
                    # DSCR bars – color coded
                    dscr_colors = [
                        COLORS['green'] if v >= 1.5 else (COLORS['yellow'] if v >= 1.0 else COLORS['red'])
                        for v in dscr_vals
                    ]
                    fig_dscr.add_trace(go.Bar(
                        x=liq_years, y=dscr_vals, name='DSCR',
                        marker_color=dscr_colors, opacity=0.85,
                        text=[f'{v:.2f}x' for v in dscr_vals], textposition='outside'
                    ))
                    # Stressed DSCR line
                    if stressed_dscr is not None:
                        fig_dscr.add_trace(go.Scatter(
                            x=liq_years, y=stressed_dscr, name='Stressed DSCR (CFO−30%)',
                            mode='lines+markers',
                            line=dict(color=COLORS['orange'], width=2.5, dash='dash'),
                            marker=dict(size=8, symbol='diamond')
                        ))
                    # Threshold lines
                    fig_dscr.add_hline(y=1.5, line_dash='dot', line_color=COLORS['green'],
                                       annotation_text='An toàn 1.5x', annotation_position='top left',
                                       annotation_font=dict(size=10, color=COLORS['green']))
                    fig_dscr.add_hline(y=1.0, line_dash='dash', line_color='white', line_width=2,
                                       annotation_text='Ranh giới 1.0x', annotation_position='bottom left',
                                       annotation_font=dict(size=11, color='white'))
                    fig_dscr.update_layout(
                        title='DSCR — Khả năng tự phục vụ nợ bằng Dòng tiền',
                        yaxis_title='DSCR (x)',
                        **DARK_TEMPLATE,
                        legend=dict(orientation='h', y=-0.2),
                        barmode='overlay'
                    )
                    st.plotly_chart(fig_dscr, use_container_width=True)
                    st.markdown(
                        '<div class="info-box">'
                        '<b>DSCR</b> = CFO / (Lãi vay + Nợ ngắn hạn). '
                        '<b>&gt; 1.5x</b>: An toàn. <b>1.0–1.5x</b>: Biên mỏng. '
                        '<b>&lt; 1.0x</b>: Phải vay đảo nợ để tồn tại. '
                        'Đường cam = Stressed DSCR (CFO giảm 30%, lãi vay tăng 20%).'
                        '</div>',
                        unsafe_allow_html=True
                    )

            with col_runway:
                if runway_vals is not None:
                    fig_rw = go.Figure()
                    rw_colors = [
                        COLORS['green'] if v >= 12 else (COLORS['yellow'] if v >= 6 else COLORS['red'])
                        for v in runway_vals
                    ]
                    fig_rw.add_trace(go.Bar(
                        x=liq_years, y=runway_vals, name='Runway (tháng)',
                        marker_color=rw_colors, opacity=0.85,
                        text=[f'{v:.1f}' for v in runway_vals], textposition='outside'
                    ))
                    # Threshold zones
                    fig_rw.add_hline(y=12, line_dash='dot', line_color=COLORS['green'],
                                     annotation_text='12 tháng (An toàn)', annotation_position='top left',
                                     annotation_font=dict(size=10, color=COLORS['green']))
                    fig_rw.add_hline(y=6, line_dash='dash', line_color=COLORS['yellow'],
                                     annotation_text='6 tháng (Cảnh báo)', annotation_position='bottom left',
                                     annotation_font=dict(size=10, color=COLORS['yellow']))
                    fig_rw.update_layout(
                        title='Liquidity Runway — Số tháng Sinh tồn nếu ngừng Doanh thu',
                        yaxis_title='Tháng',
                        **DARK_TEMPLATE,
                        legend=dict(orientation='h', y=-0.2)
                    )
                    st.plotly_chart(fig_rw, use_container_width=True)
                    st.markdown(
                        '<div class="info-box">'
                        '<b>Liquidity Runway</b> = Tiền mặt / Chi phí cố định hàng tháng. '
                        '<b>&gt; 12 tháng</b>: Đệm an toàn. <b>6–12 tháng</b>: Cần dự phòng. '
                        '<b>&lt; 6 tháng</b>: Nguy hiểm tức thời.'
                        '</div>',
                        unsafe_allow_html=True
                    )

    # ═══════════════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 3: KẾT LUẬN MẪU HÌNH
    # ═══════════════════════════════════════════════════════════════════════
    with tab3:
        st.header("💡 Kết luận Mô hình Cốt lõi (5 năm)")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if "Rủi ro bao trùm" in recommendation or "KHÔNG" in recommendation:
                st.error(f"🚨 **Khuyến nghị:** {recommendation}\n\n**Sức khỏe tài chính:** {health_eval}")
            elif "CÂN NHẮC" in recommendation or "THEO DÕI" in recommendation:
                st.warning(f"⚠️ **Khuyến nghị:** {recommendation}\n\n**Sức khỏe tài chính:** {health_eval}")
            else:
                st.success(f"✅ **Khuyến nghị:** {recommendation}\n\n**Sức khỏe tài chính:** {health_eval}")
        
        with col_c2:
            st.info(f"**Mô hình cốt lõi:** {core_model}\n\n**Minh chứng quy luật:** {core_logic}")
            st.info(f"**Dịch chuyển:** {shift_analysis}")

        st.subheader("Diễn biến Mô hình Kinh doanh Qua các năm")
        if historical_models:
            _tl_keys = sorted(list(historical_models.keys()))
            _tl_x = [f'Năm {y}' for y in _tl_keys]   # prefix để Plotly không parse thành số
            _tl_models = [historical_models[y]['Mô hình'] for y in _tl_keys]
            fig_tl = go.Figure(
                layout=go.Layout(
                    **DARK_TEMPLATE, height=320,
                    xaxis=dict(type='category', tickangle=-30),
                    yaxis=dict(visible=False, range=[-1.2, 1.2]),
                    margin=dict(l=20, r=20, t=20, b=60)
                )
            )
            fig_tl.add_trace(go.Scatter(
                x=_tl_x, y=[0] * len(_tl_x),
                mode='lines+markers',
                line=dict(color=COLORS['cyan'], width=2),
                marker=dict(size=10, color=COLORS['cyan'], symbol='square'),
                hovertemplate='<b>%{x}</b>: %{text}<extra></extra>',
                text=_tl_models, showlegend=False
            ))
            for idx, (xv, mod) in enumerate(zip(_tl_x, _tl_models)):
                _ay = -55 if idx % 2 == 0 else 45
                fig_tl.add_annotation(
                    x=xv, y=0,
                    text=f'<b>{_tl_keys[idx]}</b><br>{mod.split(" (")[0]}',
                    showarrow=True, arrowhead=0, arrowcolor=COLORS['cyan'],
                    ay=_ay, ax=0,
                    font=dict(color='white', size=10),
                    bgcolor='rgba(30,30,50,0.7)', bordercolor=COLORS['cyan'], borderwidth=1
                )
            st.plotly_chart(fig_tl, use_container_width=True)

        st.subheader(f"Chỉ số Định lượng Đặc trưng (Năm {ref_year})")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Tỷ trọng TSCĐ / Tổng TS", f"{metrics.get('fa_to_ta', 0):.1f}%")
        col_m2.metric("Biên LN Gộp", f"{metrics.get('gross_margin', 0):.1f}%")
        col_m3.metric("Chi phí BH / Doanh thu", f"{metrics.get('sell_to_rev', 0):.1f}%")
        
        col_m4, col_m5, col_m6 = st.columns(3)
        col_m4.metric("Khấu hao / Doanh thu", f"{metrics.get('depr_to_rev', 0):.1f}%")
        col_m5.metric("Hàng tồn kho / Tổng TS", f"{metrics.get('inv_to_ta', 0):.1f}%")
        col_m6.metric("Phải thu / Tổng TS", f"{metrics.get('recv_to_ta', 0):.1f}%")

    # TAB 4: HIỆU SUẤT MẪU HÌNH (Operating)
    # ═══════════════════════════════════════════════════════════════════════
    with tab4:
        st.header(f"Hiệu suất Mẫu hình: {core_model}")
        st.markdown(f"**Minh chứng cốt lõi:** {core_logic}")
        col3, col4 = st.columns(2)

        with col3:
            st.subheader("Doanh thu vs Giá vốn")
            revenue = get_row_data(is_df, r'^Doanh số thuần$')
            cogs = get_row_data(is_df, r'^Giá vốn hàng bán$')
            if revenue is not None and cogs is not None:
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(x=years, y=revenue, name='Doanh số thuần',
                    mode='lines+markers', fill='tozeroy',
                    line=dict(color=COLORS['green']), fillcolor='rgba(43,147,72,0.15)'))
                fig3.add_trace(go.Scatter(x=years, y=cogs.abs(), name='Giá vốn (Tuyệt đối)',
                    mode='lines+markers', fill='tonexty',
                    line=dict(color=COLORS['red']), fillcolor='rgba(233,69,96,0.15)'))
                fig3.update_layout(title="Khoảng hở hòa vốn (Margin Gap)", **DARK_TEMPLATE)
                st.plotly_chart(fig3, use_container_width=True)

        with col4:
            st.subheader("Biên lợi nhuận qua các năm")
            is_vert = dfs.get('IS_VERTICAL')
            if is_vert is not None:
                gross = get_row_data(is_vert, r'^Lãi gộp$')
                ebit = get_row_data(is_vert, r'^EBIT$')
                net = get_row_data(is_vert, r'^Lãi/\(lỗ\) thuần sau thuế$')
                vert_years = [c for c in is_vert.columns if c != 'Khoản mục']
                fig_margin = plot_line_multi({
                    'Biên LN gộp (%)': gross, 'Biên EBIT (%)': ebit, 'Biên LN ròng (%)': net
                }, "Biên lợi nhuận (% Doanh thu thuần)", vert_years, '%')
                st.plotly_chart(fig_margin, use_container_width=True)

        # ── OPERATING LEVERAGE CHART ──
        st.divider()
        st.subheader("⚡ Đòn bẩy Hoạt động (Operating Leverage) — Hiệu ứng Khuếch đại Lợi nhuận")
        if revenue is not None and cogs is not None and is_vert is not None:
            ebit_abs = get_row_data(is_df, r'^EBIT$')
            depr = get_row_data(cf, r'^Khấu hao TSCĐ$')
            sell_exp = get_row_data(is_df, r'^Chi phí bán hàng$')
            admin_exp = get_row_data(is_df, r'^Chi phí quản lý')

            if ebit_abs is not None:
                # x labels: thêm prefix để Plotly không parse thành số
                ol_x = [f'FY{y}' for y in years]

                # Extract plain lists
                rev_list = [float(revenue[y]) for y in years]
                ebit_list = [float(ebit_abs[y]) for y in years]

                fc_list = []
                for y in years:
                    v = 0.0
                    for _src in [depr, sell_exp, admin_exp]:
                        if _src is not None:
                            v += abs(float(_src[y]))
                    fc_list.append(v)

                # Đơn vị: raw VND → nghìn tỷ VND (÷ 1e12)
                SCALE = 1e12
                rev_ntt = [v / SCALE for v in rev_list]
                fc_ntt  = [v / SCALE for v in fc_list]
                

                # Tính DOL
                dol_labels = ['']
                for i in range(1, len(years)):
                    try:
                        pct_r = (rev_list[i] - rev_list[i-1]) / abs(rev_list[i-1]) * 100 if rev_list[i-1] else 0
                        pct_e = (ebit_list[i] - ebit_list[i-1]) / abs(ebit_list[i-1]) * 100 if ebit_list[i-1] else 0
                        dol = pct_e / pct_r if pct_r != 0 else 0
                        dol_labels.append(f'DOL={dol:.1f}x')
                    except Exception:
                        dol_labels.append('')

                # Lợi nhuận EBIT thực tế (tỷ VND)
                ebit_ty_list = [float(ebit_abs[y])/1e9 for y in years]

                # Vẽ chart với layout type='category' từ đầu
                fig_ol = go.Figure(
                    layout=go.Layout(
                        title='Đòn bẩy Hoạt động — Khi DT vượt Break-even, Lợi nhuận EBIT bứt phá',
                        barmode='overlay',
                        **DARK_TEMPLATE,
                        xaxis=dict(type='category', tickangle=-30),
                        yaxis=dict(title='Nghìn tỷ VND (Doanh thu & Định phí)', side='left'),
                        yaxis2=dict(title='Lợi nhuận EBIT (tỷ VND)', side='right',
                                    overlaying='y', showgrid=False),
                        legend=dict(orientation='h', y=-0.22, font=dict(size=10)),
                        height=480,
                    )
                )

                fig_ol.add_trace(go.Bar(
                    x=ol_x, y=rev_ntt,
                    name='Doanh thu (nghìn tỷ VND)',
                    marker_color='rgba(43,147,72,0.5)',
                ))
                fig_ol.add_trace(go.Bar(
                    x=ol_x, y=fc_ntt,
                    name='Định phí ước tính (nghìn tỷ VND)',
                    marker_color='rgba(233,69,96,0.6)',
                ))
                fig_ol.add_trace(go.Scatter(
                    x=ol_x, y=ebit_ty_list,
                    name='Lợi nhuận EBIT (tỷ VND)',
                    mode='lines+markers',
                    line=dict(color=COLORS['yellow'], width=3),
                    marker=dict(size=9), yaxis='y2'
                ))

                # Break-even line

                st.plotly_chart(fig_ol, use_container_width=True)
                st.markdown(
                    '<div class="info-box">'
                    '<b>Cột xanh</b> = Doanh thu. <b>Cột đỏ</b> = Định phí ước tính (Khấu hao + SG&A). <br>'
                    '<b>Đường vàng</b> = Lợi nhuận EBIT thực tế (tỷ VND), trục phải. '
                    '</div>',
                    unsafe_allow_html=True
                )

                # Khai thác Cấu trúc Giá thành cốt lõi cho Bước Tiếp theo
                ebit_margin_pct = get_row_data(is_vert, r'^EBIT$')
                if ebit_margin_pct is not None:
                    latest_r = float(revenue[years[-1]])/SCALE
                    latest_f = fc_list[-1]/SCALE
                    latest_e = ebit_list[-1]/SCALE
                    latest_vc = latest_r - latest_e - latest_f
                    latest_v_ratio = latest_vc / latest_r if latest_r > 0 else 0.85 # fallback

                    # ── HỒI QUY CẤU TRÚC LOG-LOG (CORE ELASTICITY & MACRO SHOCKS) ──
                    macro_reg = dfs.get('MACRO_REGRESSION')
                    if macro_reg:
                        st.subheader("Trục Hồi quy Log-Log (Core Elasticity & Macro Shocks)")
                        st.markdown("Xác định độ co giãn chi phí vận hành cốt lõi thông qua mô hình cấu trúc Logarit (Log-Log) qua 15 năm. Phương pháp này vô hiệu hóa sai lệch do gia tăng quy mô đội bay, đồng thời bóc tách hoàn toàn nhiễu từ Khủng hoảng Covid-19, cú sốc Tỷ giá và Giá dầu Jet A1.")
                        
                        r1, r2, r3, r4 = st.columns(4)
                        r1.metric("Độ co giãn Dầu (ε_oil)", f"{macro_reg['elasticity_oil']*100:.2f}%", "+1% USD/thùng", delta_color="off")
                        r2.metric("Độ co giãn Tỷ giá (ε_fx)", f"{macro_reg['elasticity_fx']*100:.2f}%", "+1% USD/VND", delta_color="off")
                        if not np.isnan(macro_reg['dol_core']):
                            r3.metric("DOL Cốt lõi", f"{macro_reg['dol_core']:.2f}x", "Core Operational Leverage", delta_color="off")
                        else:
                            r3.metric("DOL Cốt lõi", "N/A", "Core Operational Leverage", delta_color="off")
                            
                        if not np.isnan(macro_reg['dfl_core']):
                            r4.metric("DFL Cốt lõi", f"{macro_reg['dfl_core']:.2f}x", "Core Financial Leverage", delta_color="off")
                        else:
                            r4.metric("DFL Cốt lõi", "N/A", "Core Financial Leverage", delta_color="off")
                        
                        reg_method = macro_reg.get('reg_method', 'OLS')
                        max_corr = macro_reg.get('max_corr', 0.0)
                        method_color = "🔴" if max_corr > 0.95 else ("🟡" if max_corr > 0.85 else "🟢")
                        st.info(
                            f"💡 Hệ số ε_oil mô tả: Cứ giá dầu thế giới tăng lên 1%, thì Tổng chi phí của HVN sẽ phình lên thêm "
                            f"{macro_reg['elasticity_oil']*100:.2f}%. Mức độ đáng tin cậy của mô hình (R²) = {macro_reg['r_squared']*100:.1f}%.  \n"
                            f"{method_color} **Phương pháp hồi quy:** `{reg_method}` | "
                            f"**Tương quan chéo tối đa giữa biến:** `{max_corr:.2f}` "
                            f"({'Đa cộng tuyến cao — Ridge đã được kích hoạt' if max_corr > 0.85 else 'Ổn định — OLS hợp lệ'})"
                        )



                # ── MA TRẬN DỊCH CHUYỂN ĐIỂM HÒA VỐN & DOL (MACRO SENSITIVITY) ──
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.subheader("Ma trận Nhạy cảm: Dịch chuyển Điểm hòa vốn & Đòn bẩy Hoạt động")
                st.markdown("Mô phỏng tác động rủi ro của Biến số Vĩ mô (Giá dầu & Tỷ giá) lên Điểm hòa vốn và Lợi nhuận (EBIT) bằng Hệ số Co giãn ML Log-Log.<br>"
                            "<span style='color: #888888; font-size: 0.9em;'>"
                            "<b>Trạng thái Mỏ neo (Base 2025):</b> Điểm hòa vốn cốt lõi ~72.519 tỷ VND | Giá Jet A1 gốc ~90 USD/thùng | Tỷ giá ~26.300 VND/USD.<br>"
                            "<b>Cơ chế truyền dẫn rủi ro:</b> Sốc Giá nhiên liệu ăn mòn Biến phí theo <i>ε_oil</i> | Sốc Tỷ giá (nợ nước ngoài) ăn mòn Định phí theo <i>ε_fx</i>.</span>",
                            unsafe_allow_html=True)

                # Layout controls
                c_oil, c_fx = st.columns(2)
                with c_oil:
                    delta_oil = st.slider("Cú sốc: Giá nhiên liệu Jet A1 (USD/thùng)", min_value=-20.0, max_value=50.0, value=0.0, step=1.0)
                with c_fx:
                    delta_fx = st.slider("Cú sốc: Tỷ giá USD/VND (%)", min_value=-10.0, max_value=10.0, value=0.0, step=0.5)

                if ebit_margin_pct is not None:
                    # 1. Base State (2025 normalized)
                    base_r = latest_r  # from above (~121,213)
                    base_f = latest_f
                    base_vc = latest_vc
                    base_v_ratio = latest_v_ratio
                    base_bep = base_f / (1 - base_v_ratio) if (1 - base_v_ratio) > 0 else float('inf')
                    base_ebit = base_r - base_vc - base_f
                    base_dol = (base_r * (1 - base_v_ratio)) / base_ebit if base_ebit != 0 else float('nan')

                    # 2. Shock State
                    # As per user's table: 1 USD Jet A1 -> 452.4 tỷ cost increase (Variable Cost)
                    # 1% FX -> 533 tỷ cost increase (Fixed Cost / Leases)
                    shock_vc = delta_oil * 452.4 / 1000  # Convert to nghìn tỷ
                    shock_fc = delta_fx * 533.0 / 1000   # Convert to nghìn tỷ

                    new_vc = base_vc + shock_vc
                    new_f = base_f + shock_fc
                    new_v_ratio = new_vc / base_r if base_r > 0 else 0

                    if new_v_ratio >= 1:
                        new_bep = float('inf') # Margin is negative, cannot break even
                        new_dol = float('nan')
                        new_ebit = base_r - new_vc - new_f
                    else:
                        new_bep = new_f / (1 - new_v_ratio)
                        new_ebit = base_r - new_vc - new_f
                        new_dol = (base_r * (1 - new_v_ratio)) / new_ebit if new_ebit != 0 else float('nan')

                    # 3. Hiển thị Metrics Delta
                    st.markdown("##### Phân tích Tác động (So với Trạng thái Dự phóng 2025)")
                    m1, m2, m3 = st.columns(3)
                    
                    diff_ebit = new_ebit - base_ebit
                    m1.metric("Lợi nhuận EBIT mới (tỷ VND)", f"{new_ebit * 1000:,.0f}", f"{diff_ebit * 1000:,.0f}" if diff_ebit != 0 else "0")

                    if np.isinf(new_bep):
                        m2.metric("Điểm hòa vốn mới (tỷ VND)", "Vô cực (Vỡ trận)", "Không thể hòa vốn", delta_color="inverse")
                    else:
                        diff_bep = new_bep - base_bep
                        m2.metric("Điểm hòa vốn mới (tỷ VND)", f"{new_bep * 1000:,.0f}", f"{diff_bep * 1000:,.0f}" if diff_bep != 0 else "0", delta_color="inverse")

                    if np.isnan(new_dol):
                        m3.metric("Đòn bẩy Hoạt động (DOL)", "Lỗ cốt lõi", delta_color="off")
                    else:
                        diff_dol = new_dol - base_dol
                        m3.metric("Hệ số DOL hiện hành", f"{new_dol:.2f}x", f"{diff_dol:+.2f}x" if diff_dol != 0 else "0.00x", delta_color="inverse")

                    # 4. Trực quan hóa Biểu đồ Sốc (Dual Curve)
                    fig_shock = go.Figure()

                    # Curve Base
                    theo_r_shock = np.linspace(10, 160, 100)
                    theo_margin_base = ((1 - base_v_ratio) - (base_f / theo_r_shock)) * 100
                    fig_shock.add_trace(go.Scatter(
                        x=theo_r_shock, y=theo_margin_base,
                        mode='lines', name='Cơ sở (Base)',
                        line=dict(color='rgba(255, 255, 255, 0.4)', width=3, dash='dot'),
                        hoverinfo='skip'
                    ))
                    
                    # Base BEP line
                    if np.isfinite(base_bep):
                        fig_shock.add_vline(x=base_bep, line_dash='dash', line_color='rgba(255, 255, 255, 0.3)')
                        fig_shock.add_annotation(
                            x=base_bep, y=0, text=f'BEP Gốc: {base_bep:.0f}k', 
                            showarrow=False, yshift=15, font=dict(color='rgba(255, 255, 255, 0.5)', size=10)
                        )

                    # Curve Shock
                    if new_v_ratio < 1 and (delta_oil != 0 or delta_fx != 0):
                        theo_margin_shock = ((1 - new_v_ratio) - (new_f / theo_r_shock)) * 100
                        color_shock = COLORS['red'] if (new_ebit < base_ebit) else COLORS['green']
                        
                        fig_shock.add_trace(go.Scatter(
                            x=theo_r_shock, y=theo_margin_shock,
                            mode='lines', name='Sau Cú Sốc (Stressed)',
                            line=dict(color=color_shock, width=4)
                        ))
                        
                        # Shifted BEP line
                        fig_shock.add_vline(x=new_bep, line_dash='dash', line_color=color_shock)
                        fig_shock.add_annotation(x=new_bep, y=0, text=f'BEP Mới: {new_bep:.0f}k', showarrow=False, yshift=-15, font=dict(color=color_shock))
                    
                    # Highlight 2025 point Base vs New
                    b_margin = base_ebit/base_r*100
                    n_margin = new_ebit/base_r*100
                    
                    if np.isfinite(b_margin) and np.isfinite(n_margin):
                        fig_shock.add_trace(go.Scatter(
                            x=[base_r, base_r], y=[b_margin, n_margin],
                            mode='markers+lines', name='Dịch chuyển Lợi nhuận',
                            marker=dict(color=['white', COLORS['orange']], size=12, symbol=['circle', 'circle-open']),
                            line=dict(color=COLORS['orange'], width=2, dash='dot')
                        ))

                    fig_shock.update_layout(
                        title='Ma trận Dịch chuyển Trần Lợi nhuận & Điểm hòa vốn',
                        xaxis_title='Doanh thu Tuyệt đối (nghìn tỷ VND)',
                        yaxis_title='Biên EBIT (%)',
                        **DARK_TEMPLATE,
                        hovermode='closest',
                        height=400,
                        margin=dict(t=50, b=30)
                    )
                    st.plotly_chart(fig_shock, use_container_width=True)

    # ═══════════════════════════════════════════════════════════════════════
    # Tiếp tục TAB 4
    # ═══════════════════════════════════════════════════════════════════════
        st.divider()
        st.header("Chỉ số Tài chính Tổng hợp")


        # --- 3.1 Valuation ---
        st.subheader("1. Định giá (Valuation)")
        c1, c2 = st.columns(2)
        with c1:
            ps = get_fi_row(fi, r'^P/S$')
            fig_val = plot_line_multi({'P/S': ps}, "Hệ số định giá P/S", years, 'x')
            st.plotly_chart(fig_val, use_container_width=True)
            st.info("Đã ẩn P/E, P/B do HVN có VCSH âm gây nhiễu.")
        with c2:
            ev_ebitda = get_fi_row(fi, r'^EV/EBITDA$')
            ev_rev = get_fi_row(fi, r'^EV/Revenue$')
            p_cf = get_fi_row(fi, r'^P/Cash Flow$|^P/CF$')
            fig_val2 = plot_line_multi({
                'EV/EBITDA': ev_ebitda, 
                'EV/Revenue': ev_rev,
                'P/Cash Flow': p_cf
            }, "EV/EBITDA, EV/Revenue & P/CF", years, 'x')
            
            # Thêm vùng ngưỡng trung bình
            fig_val2.add_hrect(y0=5.0, y1=7.5, fillcolor="rgba(255,107,53,0.1)", line_width=0, 
                               annotation_text="EV/EBITDA Zone (5.0x-7.5x)", annotation_position="top left",
                               annotation_font=dict(size=10, color="#ff6b35"))
            fig_val2.add_hrect(y0=0.9, y1=1.4, fillcolor="rgba(43,147,72,0.1)", line_width=0,
                               annotation_text="EV/Revenue Zone (0.9x-1.4x)", annotation_position="bottom left",
                               annotation_font=dict(size=10, color="#2b9348"))
                               
            st.plotly_chart(fig_val2, use_container_width=True)

        # --- 3.2 Profitability + DuPont (CLUSTERED BAR) ---
        st.subheader("2. Khả năng sinh lời (Profitability)")
        c3, c4 = st.columns(2)
        with c3:
            # Ưu tiên lấy từ DuPont ROA/ROIC vì đã được tính theo số dư bình quân và nhân 100
            roa = get_row_data(dupont_roa, r'ROA') if dupont_roa is not None else None
            if roa is None:
                roa = get_fi_row(fi, r'^ROA')
                if roa is not None and roa.abs().max() <= 1.0: # Nếu là số thập phân (max <= 1)
                     roa = roa * 100
            
            roic = get_row_data(dupont_roic, r'ROIC') if dupont_roic is not None else None
            if roic is None:
                roic = get_fi_row(fi, r'^ROIC')
                if roic is not None and roic.abs().max() <= 1.0:
                    roic = roic * 100

            fig_prof = plot_line_multi({'ROA': roa, 'ROIC': roic},
                                       "Tỷ suất Sinh lời Lõi: ROA / ROIC (%)", years, '%')
            st.plotly_chart(fig_prof, use_container_width=True)

        with c4:
            st.info("Khu vực Phân rã 3 nhân tố DuPont ROE đã bị vô hiệu hóa tự động. (Vốn chủ sở hữu âm gây nhiễu).")

        # --- DuPont Impact (OLS Best-fit only — Shapley removed) ---
        def _render_dupont_impact(impact_df, betas_dict, metric_label):
            if impact_df is None:
                st.info(f"Đang tính toán {metric_label} IMPACT...")
                return
            impact_yrs = [c for c in impact_df.columns if c != 'Khoản mục']
            best_label = betas_dict.get('best_perm', '?') if betas_dict else '?'
            fig_imp = go.Figure()
            color_cycle = [COLORS['green'], COLORS['cyan'], COLORS['orange'], COLORS['purple'], COLORS['teal']]
            best_rows = impact_df[impact_df['Khoản mục'].str.startswith('[Best:')]
            for idx, (_, row) in enumerate(best_rows.iterrows()):
                vals = row[impact_yrs].astype(float).values
                short_name = row['Khoản mục'].split('] ')[1] if '] ' in row['Khoản mục'] else row['Khoản mục']
                fig_imp.add_trace(go.Bar(name=short_name, x=impact_yrs, y=vals,
                    marker_color=color_cycle[idx % len(color_cycle)],
                    text=[f'{v:+.1f}' for v in vals], textposition='outside'))
            actual_row = impact_df[impact_df['Khoản mục'].str.contains('Thực tế', regex=False)]
            if not actual_row.empty:
                actual_vals = actual_row.iloc[0][impact_yrs].astype(float).values
                fig_imp.add_trace(go.Scatter(name=f'Δ{metric_label} Thực tế (%)', x=impact_yrs, y=actual_vals,
                    mode='lines+markers', line=dict(color=COLORS['yellow'], width=2.5, dash='dot'),
                    marker=dict(size=10, symbol='diamond')))
            ols_keys = [k for k in betas_dict if k.startswith('ols_')]
            ols_info = ' | '.join([f'{k[4:]}={betas_dict[k]:.3f}' for k in ols_keys])
            fig_imp.update_layout(barmode='group', **DARK_TEMPLATE,
                title=f'Δ{metric_label} · Best-fit: {best_label} · OLS β: {ols_info}',
                yaxis_title='%pts', legend=dict(orientation='h', y=-0.2, font=dict(size=10)))
            st.plotly_chart(fig_imp, use_container_width=True)

        # st.subheader("Phân rã ΔROE (Best-fit OLS)")
        # _render_dupont_impact(dupont_impact, dupont_betas, 'ROE')
        st.subheader("Phân rã ΔROA — 4 nhân tố (Best-fit OLS)")
        _render_dupont_impact(dupont_impact_roa, dupont_betas_roa, 'ROA')
        st.subheader("Phân rã ΔROIC — 2 nhân tố (Best-fit OLS)")
        _render_dupont_impact(dupont_impact_roic, dupont_betas_roic, 'ROIC')

        # --- DuPont ROA 4 nhân tố chart ---
        st.subheader("DuPont ROA 4 nhân tố")
        if dupont_roa is not None:
            dp_yrs = [c for c in dupont_roa.columns if c != 'Khoản mục']
            tb_d = get_row_data(dupont_roa, r'^Tax Burden')
            ib_d = get_row_data(dupont_roa, r'^Interest Burden')
            em_d = get_row_data(dupont_roa, r'^EBIT Margin')
            at_d2 = get_row_data(dupont_roa, r'^Asset Turnover')
            fig_roa = make_subplots(rows=2, cols=2,
                subplot_titles=('Tax Burden (NI/EBT)', 'Interest Burden (EBT/EBIT)',
                                'EBIT Margin (%)', 'Asset Turnover (x)'),
                horizontal_spacing=0.12, vertical_spacing=0.15)
            for idx, (data, color) in enumerate([(tb_d, COLORS['purple']), (ib_d, COLORS['cyan']),
                                                  (em_d, COLORS['green']), (at_d2, COLORS['orange'])]):
                r, c_idx = divmod(idx, 2)
                if data is not None:
                    fig_roa.add_trace(go.Bar(x=dp_yrs, y=data, marker_color=color,
                        text=[f'{v:.2f}' for v in data], textposition='outside', showlegend=False
                    ), row=r+1, col=c_idx+1)
            fig_roa.update_layout(height=450, **DARK_TEMPLATE,
                title='DuPont ROA: Tax Burden × Int Burden × EBIT Margin × AT')
            st.plotly_chart(fig_roa, use_container_width=True)

        # --- DuPont ROIC 2 nhân tố chart ---
        if dupont_roic is not None:
            st.subheader("DuPont ROIC 2 nhân tố")
            dp_yrs_r = [c for c in dupont_roic.columns if c != 'Khoản mục']
            nm_d = get_row_data(dupont_roic, r'^NOPAT Margin')
            ict_d = get_row_data(dupont_roic, r'^IC Turnover')
            roic_d = get_row_data(dupont_roic, r'^ROIC')
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                if nm_d is not None:
                    fig_nm = go.Figure(go.Bar(
                        x=dp_yrs_r, y=nm_d, marker_color=COLORS['teal'],
                        text=[f'{v:.1f}%' for v in nm_d], textposition='outside'))
                    fig_nm.update_layout(title='NOPAT Margin (%)', **DARK_TEMPLATE, height=300)
                    st.plotly_chart(fig_nm, use_container_width=True)
            with col_r2:
                if ict_d is not None:
                    fig_ict = go.Figure(go.Bar(
                        x=dp_yrs_r, y=ict_d, marker_color=COLORS['orange'],
                        text=[f'{v:.2f}x' for v in ict_d], textposition='outside'))
                    fig_ict.update_layout(title='IC Turnover (x)', **DARK_TEMPLATE, height=300)
                    st.plotly_chart(fig_ict, use_container_width=True)


    # ═══════════════════════════════════════════════════════════════════════
    # TAB 3 (continued): Liquidity, Solvency, Efficiency
    # ═══════════════════════════════════════════════════════════════════════
        st.subheader("3. Thanh khoản (Liquidity)")
        cr = get_fi_row(fi, r'Chỉ số thanh toán hiện thời|Current Ratio')
        qr = get_fi_row(fi, r'Chỉ số thanh toán nhanh|Quick Ratio')
        cash_r = get_fi_row(fi, r'Chỉ số thanh toán tiền mặt|Cash Ratio')
        fig_liq = plot_line_multi({'Current Ratio': cr, 'Quick Ratio': qr, 'Cash Ratio': cash_r},
                                   "Hệ số thanh khoản", years, 'x')
        st.plotly_chart(fig_liq, use_container_width=True)

        st.subheader("4. Cấu trúc vốn & Khả năng trả nợ (Solvency)")
        c5, c6 = st.columns(2)
        with c5:
            de = get_fi_row(fi, r'Nợ phải trả / Vốn chủ sở hữu|D/E')
            leverage_r = get_fi_row(fi, r'Đòn bẩy tài chính')
            fig_solv = plot_line_multi({'D/E': de, 'Đòn bẩy TC': leverage_r}, "Hệ số nợ", years, 'x')
            st.plotly_chart(fig_solv, use_container_width=True)
        with c6:
            nd = get_fi_row(fi, r'^Net Debt / EBITDA$')
            icr = get_fi_row(fi, r'Khả năng chi trả lãi vay')
            fig_solv2 = plot_line_multi({'Net Debt/EBITDA': nd, 'ICR (EBIT/Lãi vay)': icr},
                                         "Khả năng trả nợ", years, 'x')
            st.plotly_chart(fig_solv2, use_container_width=True)

        st.subheader("5. Hiệu quả hoạt động (Efficiency)")
        dso = get_fi_row(fi, r'^DSO')
        dio = get_fi_row(fi, r'^DIO')
        dpo = get_fi_row(fi, r'^DPO')
        ccc = get_fi_row(fi, r'^Chu kỳ tiền$|^CCC')
        fig_eff = plot_line_multi({'DSO (ngày)': dso, 'DIO (ngày)': dio, 'DPO (ngày)': dpo, 'CCC (ngày)': ccc},
                                   "Cash Conversion Cycle & Components", years, 'ngày')
        st.plotly_chart(fig_eff, use_container_width=True)

        st.subheader("Chỉ số Vòng quay (Turnovers) - Theo Mẫu hình")
        ito = get_fi_row(fi, r'Vòng quay hàng tồn kho')
        fat = get_fi_row(fi, r'Vòng quay tài sản cố định')
        at = get_fi_row(fi, r'Vòng quay tổng tài sản')
        
        if 'Bán lẻ' in core_model and ito is not None:
            st.plotly_chart(plot_line_multi({'ITO': ito}, "Vòng quay Tồn kho (ITO)", years, 'vòng'), use_container_width=True)
        elif 'Thâm dụng vốn' in core_model and fat is not None:
            st.plotly_chart(plot_line_multi({'FAT': fat}, "Vòng quay TSCĐ (FAT)", years, 'vòng'), use_container_width=True)
        elif 'Nhẹ tài sản' in core_model and at is not None:
            st.plotly_chart(plot_line_multi({'AT': at}, "Vòng quay Tổng TS (AT)", years, 'vòng'), use_container_width=True)
        else:
            if at is not None:
                st.plotly_chart(plot_line_multi({'AT': at, 'FAT': fat, 'ITO': ito}, "Các chỉ số vòng quay chính", years, 'vòng'), use_container_width=True)


    # ═══════════════════════════════════════════════════════════════════════
    # TAB 2: CHẤT LƯỢNG BCTC (Anomaly)
    # ═══════════════════════════════════════════════════════════════════════
    with tab2:
        st.header("🔍 Chất lượng BCTC (Beneish · Altman · Sloan)")

        if anomaly_numeric:
            anom_years = anomaly_numeric.get('years', [])
            beneish = anomaly_numeric.get('beneish', [])
            altman = anomaly_numeric.get('altman', [])
            sloan = anomaly_numeric.get('sloan', [])

            # Gauge charts for latest year
            st.subheader("Kết quả năm mới nhất")
            gc1, gc2, gc3 = st.columns(3)

            with gc1:
                m_val = beneish[-1] if beneish else 0
                m_color = COLORS['red'] if m_val > -2.22 else COLORS['green']
                m_text = 'NGHI NGỜI' if m_val > -2.22 else 'BÌNH THƯỜNG'
                fig_g1 = go.Figure(go.Indicator(
                    mode='gauge+number', value=m_val, title={'text': f'Beneish M-Score ({anom_years[-1] if anom_years else ""})'},
                    gauge=dict(axis=dict(range=[-5, 0]),
                               bar=dict(color=m_color),
                               threshold=dict(line=dict(color='white', width=3), thickness=0.8, value=-2.22),
                               steps=[dict(range=[-5, -2.22], color='rgba(43,147,72,0.3)'),
                                      dict(range=[-2.22, 0], color='rgba(233,69,96,0.3)')])
                ))
                fig_g1.update_layout(height=250, **DARK_TEMPLATE,
                    annotations=[dict(text=m_text, x=0.5, y=0, showarrow=False, font=dict(size=14, color=m_color))])
                st.plotly_chart(fig_g1, use_container_width=True)

            with gc2:
                z_val = altman[-1] if altman else 0
                z_color = COLORS['red'] if z_val < 1.1 else (COLORS['yellow'] if z_val < 2.6 else COLORS['green'])
                z_text = 'NGUY HIỂM' if z_val < 1.1 else ('XÁM' if z_val < 2.6 else 'AN TOÀN')
                fig_g2 = go.Figure(go.Indicator(
                    mode='gauge+number', value=z_val, title={'text': f"Altman Z''-Score ({anom_years[-1] if anom_years else ''})"},
                    gauge=dict(axis=dict(range=[0, 6]),
                               bar=dict(color=z_color),
                               steps=[dict(range=[0, 1.1], color='rgba(233,69,96,0.3)'),
                                      dict(range=[1.1, 2.6], color='rgba(249,199,79,0.3)'),
                                      dict(range=[2.6, 6], color='rgba(43,147,72,0.3)')])
                ))
                fig_g2.update_layout(height=250, **DARK_TEMPLATE,
                    annotations=[dict(text=z_text, x=0.5, y=0, showarrow=False, font=dict(size=14, color=z_color))])
                st.plotly_chart(fig_g2, use_container_width=True)

            with gc3:
                s_val = sloan[-1] if sloan else 0
                s_color = COLORS['red'] if abs(s_val) > 25 else (COLORS['yellow'] if abs(s_val) > 10 else COLORS['green'])
                s_text = 'NGHIÊM TRỌNG' if abs(s_val) > 25 else ('CẢNH BÁO' if abs(s_val) > 10 else 'AN TOÀN')
                fig_g3 = go.Figure(go.Indicator(
                    mode='gauge+number', value=s_val, title={'text': f'Sloan Accruals % ({anom_years[-1] if anom_years else ""})'},
                    number=dict(suffix='%'),
                    gauge=dict(axis=dict(range=[-50, 50]),
                               bar=dict(color=s_color),
                               steps=[dict(range=[-50, -25], color='rgba(233,69,96,0.3)'),
                                      dict(range=[-25, -10], color='rgba(249,199,79,0.3)'),
                                      dict(range=[-10, 10], color='rgba(43,147,72,0.3)'),
                                      dict(range=[10, 25], color='rgba(249,199,79,0.3)'),
                                      dict(range=[25, 50], color='rgba(233,69,96,0.3)')])
                ))
                fig_g3.update_layout(height=250, **DARK_TEMPLATE,
                    annotations=[dict(text=s_text, x=0.5, y=0, showarrow=False, font=dict(size=14, color=s_color))])
                st.plotly_chart(fig_g3, use_container_width=True)

            # Line charts over time
            st.subheader("Diễn biến qua các năm")
            lc1, lc2, lc3 = st.columns(3)
            with lc1:
                fig_b = go.Figure()
                fig_b.add_trace(go.Scatter(x=anom_years, y=beneish, mode='lines+markers',
                    line=dict(color=COLORS['red'], width=2.5), marker=dict(size=8), name='M-Score'))
                fig_b.add_hline(y=-2.22, line_dash='dash', line_color='white', annotation_text='Ngưỡng -2.22')
                fig_b.update_layout(title='Beneish M-Score', **DARK_TEMPLATE, height=280)
                st.plotly_chart(fig_b, use_container_width=True)
            with lc2:
                fig_z = go.Figure()
                fig_z.add_trace(go.Scatter(x=anom_years, y=altman, mode='lines+markers',
                    line=dict(color=COLORS['cyan'], width=2.5), marker=dict(size=8), name="Z''-Score"))
                fig_z.add_hline(y=2.6, line_dash='dash', line_color=COLORS['green'], annotation_text='An toàn 2.6')
                fig_z.add_hline(y=1.1, line_dash='dash', line_color=COLORS['red'], annotation_text='Nguy hiểm 1.1')
                fig_z.update_layout(title="Altman Z''-Score", **DARK_TEMPLATE, height=280)
                st.plotly_chart(fig_z, use_container_width=True)
            with lc3:
                fig_s = go.Figure()
                s_bar_colors = [COLORS['red'] if abs(v) > 25 else (COLORS['yellow'] if abs(v) > 10 else COLORS['green']) for v in sloan]
                fig_s.add_trace(go.Bar(x=anom_years, y=sloan, marker_color=s_bar_colors, name='Sloan %'))
                fig_s.add_hline(y=10, line_dash='dash', line_color=COLORS['yellow'])
                fig_s.add_hline(y=-10, line_dash='dash', line_color=COLORS['yellow'])
                fig_s.update_layout(title='Sloan Accruals (%)', **DARK_TEMPLATE, height=280)
                st.plotly_chart(fig_s, use_container_width=True)

            st.markdown(
                '<div class="info-box">'
                '<b>Beneish M-Score:</b> > −2.22 → nghi ngờ thao túng lợi nhuận. '
                '<b>Altman Z\'\'-Score:</b> < 1.1 → nguy cơ phá sản; 1.1–2.6 → vùng xám; > 2.6 → an toàn. '
                '<b>Sloan:</b> |%| > 10% → cảnh báo chất lượng lợi nhuận; > 25% → nghiêm trọng.'
                '</div>',
                unsafe_allow_html=True
            )

            # --- BENEISH DECOMPOSITION ---
            beneish_comp = anomaly_numeric.get('beneish_components', {})
            if beneish_comp:
                st.divider()
                st.subheader("1. Bóc tách Chỉ số Beneish M-Score")
                
                # Nhóm 1: DSRI, GMI, SGI, TATA (Các chỉ số cốt lõi về doanh thu/lợi nhuận)
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    fig_b1 = plot_line_multi({
                        'DSRI (Phải thu)': beneish_comp.get('DSRI', []),
                        'GMI (Biên lãi gộp)': beneish_comp.get('GMI', []),
                        'SGI (Tăng trưởng DT)': beneish_comp.get('SGI', []),
                        'TATA (Dồn tích)': beneish_comp.get('TATA', [])
                    }, "Beneish: Doanh thu & Dồn tích", anom_years)
                    fig_b1.add_hline(y=1.0, line_dash='dot', line_color='white', opacity=0.3)
                    st.plotly_chart(fig_b1, use_container_width=True)
                
                # Nhóm 2: AQI, DEPI, SGAI, LVGI (Các chỉ số về tài sản & chi phí)
                with col_b2:
                    fig_b2 = plot_line_multi({
                        'AQI (Chất lượng TS)': beneish_comp.get('AQI', []),
                        'DEPI (Khấu hao)': beneish_comp.get('DEPI', []),
                        'SGAI (Chi phí QL)': beneish_comp.get('SGAI', []),
                        'LVGI (Đòn bẩy)': beneish_comp.get('LVGI', [])
                    }, "Beneish: Tài sản & Chi phí", anom_years)
                    fig_b2.add_hline(y=1.0, line_dash='dot', line_color='white', opacity=0.3)
                    st.plotly_chart(fig_b2, use_container_width=True)
                
                st.markdown(
                    '<div class="info-box">'
                    '<b>DSRI > 1:</b> Tăng trưởng phải thu nhanh hơn doanh thu. '
                    '<b>GMI > 1:</b> Biên lãi gộp suy giảm. '
                    '<b>AQI > 1:</b> Tỷ lệ tài sản không sinh lời tăng. '
                    '<b>SGI > 1:</b> Tăng trưởng doanh thu nóng. '
                    '<b>DEPI > 1:</b> Tỷ lệ khấu hao giảm (kéo dài thời gian khấu hao để tăng lãi). '
                    '<b>TATA:</b> Chênh lệch giữa LN ròng và Dòng tiền (Accruals).'
                    '</div>',
                    unsafe_allow_html=True
                )

            # --- ALTMAN DECOMPOSITION ---
            altman_comp = anomaly_numeric.get('altman_components', {})
            if altman_comp:
                st.divider()
                st.subheader("2. Bóc tách Chỉ số Altman Z''-Score")
                fig_altman = plot_line_multi({
                    'X1 (WC/Total Assets)': altman_comp.get('X1', []),
                    'X2 (RE/Total Assets)': altman_comp.get('X2', []),
                    'X3 (EBIT/Total Assets)': altman_comp.get('X3', []),
                    'X4 (Equity/Liabilities)': altman_comp.get('X4', [])
                }, "Các thành phần Altman Z''-Score", anom_years)
                st.plotly_chart(fig_altman, use_container_width=True)
                st.markdown(
                    '<div class="info-box">'
                    '<b>X1 (Vốn lưu động / Tổng TS):</b> Phản ánh thanh khoản ròng. <br>'
                    '<b>X2 (Lợi nhuận giữ lại / Tổng TS):</b> Phản ánh mức độ tích lũy lãi. (HVN âm do lỗ lũy kế). <br>'
                    '<b>X3 (EBIT / Tổng TS):</b> Hiệu suất sinh lời của tài sản. <br>'
                    '<b>X4 (VCSH / Tổng Nợ):</b> Đòn bẩy tài chính (Vốn chủ / Nợ phải trả).'
                    '</div>',
                    unsafe_allow_html=True
                )

            # --- SLOAN ANALYSIS ---
            st.divider()
            st.subheader("3. Phân tích Dồn tích Sloan (Sloan Accruals)")
            st.info("Chỉ số Sloan đo lường sự khác biệt giữa Lợi nhuận kế toán và Dòng tiền thực tế (bao gồm cả dòng tiền đầu tư). "
                    "Sloan > 10%: lợi nhuận có tỷ trọng dồn tích lớn — cần cẩn trọng về chất lượng thực thu. Sloan > 25%: mức nghiêm trọng.")
            if sloan and anom_years:
                fig_sloan_full = go.Figure()
                sloan_colors_full = [
                    COLORS['red'] if abs(v) > 25 else (COLORS['yellow'] if abs(v) > 10 else COLORS['green'])
                    for v in sloan
                ]
                fig_sloan_full.add_trace(go.Bar(
                    x=anom_years, y=sloan,
                    marker_color=sloan_colors_full, name='Sloan Accruals (%)',
                    text=[f'{v:+.2f}%' for v in sloan], textposition='outside'
                ))
                fig_sloan_full.add_hline(y=25, line_dash='dot', line_color=COLORS['red'],
                    annotation_text='Nghiêm trọng +25%', annotation_position='top left',
                    annotation_font=dict(size=10, color=COLORS['red']))
                fig_sloan_full.add_hline(y=10, line_dash='dash', line_color=COLORS['yellow'],
                    annotation_text='Cảnh báo +10%', annotation_position='top left',
                    annotation_font=dict(size=10, color=COLORS['yellow']))
                fig_sloan_full.add_hline(y=0, line_color='white', line_width=1, opacity=0.3)
                fig_sloan_full.add_hline(y=-10, line_dash='dash', line_color=COLORS['yellow'],
                    annotation_text='Cảnh báo −10%', annotation_position='bottom left',
                    annotation_font=dict(size=10, color=COLORS['yellow']))
                fig_sloan_full.add_hline(y=-25, line_dash='dot', line_color=COLORS['red'],
                    annotation_text='Nghiêm trọng −25%', annotation_position='bottom left',
                    annotation_font=dict(size=10, color=COLORS['red']))
                fig_sloan_full.update_layout(
                    title='Sloan Accruals (%) — Chất lượng Lợi nhuận Kế toán',
                    yaxis_title='Sloan Accrual Ratio (%)',
                    xaxis_title='Năm',
                    **DARK_TEMPLATE,
                    height=420,
                    legend=dict(orientation='h', y=-0.15)
                )
                st.plotly_chart(fig_sloan_full, use_container_width=True)
                st.markdown(
                    '<div class="info-box">'
                    '<b>Công thức Sloan:</b> (Lãi ròng − Dòng tiền HĐKD − Dòng tiền đầu tư) / Tổng tài sản. <br>'
                    '<b>Màu xanh:</b> |Sloan| ≤ 10% — Chất lượng lợi nhuận tốt. '
                    '<b>Màu vàng:</b> 10%–25% — Cảnh báo: lợi nhuận có phần dồn tích. '
                    '<b>Màu đỏ:</b> > 25% — Nghiêm trọng: lợi nhuận kế toán tách rời dòng tiền thực tế.'
                    '</div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("Không đủ dữ liệu để tính Anomaly Scores.")

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 6: DATA TABLES
    # ═══════════════════════════════════════════════════════════════════════
    with tab6:
        st.header("📁 Bảng dữ liệu chi tiết")
        table_choice = st.selectbox("Chọn bảng dữ liệu:", [
            'BS — Tỷ trọng (Vertical)',
            'IS — Common-Size (Vertical)',
            'BS — Biến động YoY%',
            'IS — Biến động YoY%',
            'CF — Biến động YoY%',
            'Dupont ROE',
            'Dupont ROA (4 nhân tố)',
            'Dupont ROIC (2 nhân tố)',
            'Dupont Factor Impact (ROE)',
            'Dupont Factor Impact (ROA)',
            'Dupont Factor Impact (ROIC)',
            'Thực Thu / Thực Chi',
            'Anomaly Scores',
            'Financial Index (Full)',
        ])
        table_map = {
            'BS — Tỷ trọng (Vertical)': 'BS_VERTICAL',
            'IS — Common-Size (Vertical)': 'IS_VERTICAL',
            'BS — Biến động YoY%': 'BS_YOY',
            'IS — Biến động YoY%': 'IS_YOY',
            'CF — Biến động YoY%': 'CF_YOY',
            'Dupont ROE': 'DUPONT',
            'Dupont ROA (4 nhân tố)': 'DUPONT_ROA',
            'Dupont ROIC (2 nhân tố)': 'DUPONT_ROIC',
            'Dupont Factor Impact (ROE)': 'DUPONT_IMPACT',
            'Dupont Factor Impact (ROA)': 'DUPONT_IMPACT_ROA',
            'Dupont Factor Impact (ROIC)': 'DUPONT_IMPACT_ROIC',
            'Thực Thu / Thực Chi': 'CASH_INOUT',
            'Anomaly Scores': 'ANOMALY_SCORES',
            'Financial Index (Full)': 'FINANCIAL INDEX',
        }
        key = table_map.get(table_choice)
        if key and key in dfs:
            df_show = dfs[key].copy()
            st.dataframe(df_show, use_container_width=True, height=500)
            csv = df_show.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(label="📥 Tải xuống CSV", data=csv,
                               file_name=f"HVN_{key.replace(' ', '_')}.csv", mime="text/csv")
        else:
            st.warning(f"Không tìm thấy dữ liệu cho '{table_choice}'.")

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 5: ĐỊNH GIÁ DOANH NGHIỆP (Enterprise Value)
    # ═══════════════════════════════════════════════════════════════════════
    with tab5:
        st.header("📈 Định giá Doanh nghiệp — Enterprise Value Framework")
        st.markdown("""
<div class="info-box">
Triết lý: Định giá theo <b>Giá trị Doanh nghiệp (EV)</b> thay vì Giá trị Vốn chủ sở hữu — phù hợp với doanh nghiệp có VCSH âm hoặc đang tái cấu trúc.
Phương pháp: <b>EV/EBITDA Mean Reversion</b> + <b>DCF Terminal Value Integration</b> + <b>Football Field Chart</b>.
</div>""", unsafe_allow_html=True)

        try:
            forecaster_obj = Forecaster(dfs)
            
            # --- Tích hợp Chiết khấu Rủi ro tái cấu trúc ---
            st.markdown("##### ⚙️ Thiết lập Tham số Định giá")
            col_d1, col_d2 = st.columns([2, 3])
            with col_d1:
                discount_val = st.slider(
                    "Chiết khấu Rủi ro tái cấu trúc (%)", 
                    0, 100, 40, 5,
                    help="Chiết khấu giá trị định giá lịch sử để phản ánh gánh nặng nợ vay và rủi ro tái cấu trúc hiện tại (Gợi ý: 30-40%)."
                )
                discount = discount_val / 100.0
            with col_d2:
                st.info(f"Đang áp dụng mức chiết khấu **{discount_val}%** vào mô hình EV/EBITDA History.")

            f_results = forecaster_obj.run_all(discount=discount)
        except Exception as e:
            st.error(f"Lỗi khởi tạo module Forecaster: {e}")
            f_results = {}
            forecaster_obj = Forecaster(dfs)

        # ---- 5.1 STL DECOMPOSITION (giữ nguyên) ----
        st.subheader("1. Phân rã Chu kỳ STL (Trend / Seasonal / Residual)")
        stl_options = forecaster_obj.get_stl_series_options()
        sel_series = st.selectbox("Chọn chỉ số để phân rã:", stl_options, key='stl_select')

        stl_result = forecaster_obj.stl_decomposition(sel_series)
        if stl_result:
            method_tag = stl_result.get('method', '')
            stl_years = list(stl_result['original'].index)

            col_stl1, col_stl2, col_stl3 = st.columns(3)
            with col_stl1:
                fig_trend = go.Figure(go.Scatter(
                    x=stl_years, y=stl_result['trend'],
                    mode='lines+markers', name='Trend',
                    line=dict(color=COLORS['cyan'], width=2.5), marker=dict(size=8)
                ))
                fig_trend.update_layout(title=f'Xu hướng dài hạn ({method_tag})', **DARK_TEMPLATE, height=260)
                col_stl1.plotly_chart(fig_trend, use_container_width=True)
            with col_stl2:
                fig_seas = go.Figure(go.Bar(
                    x=stl_years, y=stl_result['seasonal'],
                    name='Seasonal', marker_color=COLORS['purple']
                ))
                fig_seas.update_layout(title='Thành phần Mùa vụ', **DARK_TEMPLATE, height=260)
                col_stl2.plotly_chart(fig_seas, use_container_width=True)
            with col_stl3:
                resid_vals = stl_result['residual'].values
                resid_colors = [COLORS['red'] if v < 0 else COLORS['green'] for v in resid_vals]
                fig_resid = go.Figure(go.Bar(
                    x=stl_years, y=resid_vals,
                    name='Residual', marker_color=resid_colors
                ))
                fig_resid.update_layout(title='Phần dư (Nhiễu / Bất thường)', **DARK_TEMPLATE, height=260)
                col_stl3.plotly_chart(fig_resid, use_container_width=True)

            st.markdown(
                '<div class="info-box"><b>Đọc kết quả:</b> Residual lớn (±) = biến động bất thường. '
                'Seasonal ≈ 0 với dữ liệu năm là bình thường. Trend = năng lực lõi dài hạn.</div>',
                unsafe_allow_html=True
            )
        else:
            st.warning(f"Không đủ dữ liệu để phân rã STL cho '{sel_series}'.")

        st.divider()

        # ---- 5.2 EV/EBITDA VALUATION BANDS ----
        st.subheader("2. Dải Định giá Lịch sử (EV/EBITDA Mean Reversion)")
        vb = f_results.get('VALUATION_BANDS')
        if vb:
            vb_years = vb['years']
            fig_vb = go.Figure()
            fig_vb.add_trace(go.Scatter(x=vb_years, y=[vb['upper_2s']] * len(vb_years),
                name='+2σ (Đắt)', line=dict(color='rgba(233,69,96,0.4)', dash='dot', width=1), mode='lines'))
            fig_vb.add_trace(go.Scatter(x=vb_years, y=[vb['upper_1s']] * len(vb_years),
                name='+1σ', line=dict(color='rgba(255,107,53,0.6)', dash='dot', width=1.5), mode='lines'))
            fig_vb.add_trace(go.Scatter(x=vb_years, y=[vb['mean']] * len(vb_years),
                name='Mean', line=dict(color='white', dash='dash', width=1.5), mode='lines'))
            fig_vb.add_trace(go.Scatter(x=vb_years, y=[vb['lower_1s']] * len(vb_years),
                name='-1σ', line=dict(color='rgba(255,107,53,0.6)', dash='dot', width=1.5), mode='lines'))
            fig_vb.add_trace(go.Scatter(x=vb_years, y=[vb['lower_2s']] * len(vb_years),
                name='-2σ (Rẻ)', line=dict(color='rgba(233,69,96,0.4)', dash='dot', width=1), mode='lines'))
            fig_vb.add_trace(go.Scatter(x=vb_years, y=vb['original'].values,
                name='EV/EBITDA thực tế', mode='lines+markers',
                line=dict(color=COLORS['yellow'], width=2.5), marker=dict(size=10)))
            band_pos = vb.get('band_position', 0.5)
            fig_vb.update_layout(
                title=f'EV/EBITDA Valuation Bands  ·  Band Position: {band_pos:.2f} (0=rẻ, 1=đắt)',
                **DARK_TEMPLATE, yaxis_title='EV/EBITDA (x)',
                legend=dict(orientation='h', y=-0.15)
            )
            st.plotly_chart(fig_vb, use_container_width=True)
            st.markdown(
                '<div class="info-box"><b>Ý nghĩa:</b> EV/EBITDA đo lường giá trị doanh nghiệp theo hiệu quả vận hành, '
                'không bị ảnh hưởng bởi cấu trúc vốn. Band Position < 0.3 = vùng rẻ, > 0.7 = vùng đắt.</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("Không có dữ liệu EV/EBITDA trong FINANCIAL INDEX để vẽ Valuation Bands.")

        st.divider()

        # ---- 5.3 DCF TERMINAL VALUE INTEGRATION ----
        st.subheader("🌡️ 3. Ma trận Định giá DCF (Terminal Value Integration)")
        st.markdown(
            '<div class="info-box"><b>Mô hình:</b> Dự phóng FCFF 5 năm + Terminal Value = EBITDA<sub>n</sub> × Mean(EV/EBITDA lịch sử). '
            'Chiết khấu toàn bộ về hiện tại bằng WACC.</div>',
            unsafe_allow_html=True
        )
        col_dcf1, col_dcf2 = st.columns([1, 3])
        with col_dcf1:
            wacc_min = st.slider("WACC tối thiểu (%)", 6, 12, 8, step=1) / 100
            wacc_max = st.slider("WACC tối đa (%)", 12, 20, 16, step=1) / 100
            g_min = st.slider("EBITDA Growth tối thiểu (%)", -5, 3, -2, step=1) / 100
            g_max = st.slider("EBITDA Growth tối đa (%)", 3, 15, 8, step=1) / 100

        dcf_result = forecaster_obj.dcf_sensitivity(
            wacc_range=(wacc_min, wacc_max, 0.005),
            ebitda_growth_range=(g_min, g_max, 0.005)
        )
        with col_dcf2:
            if dcf_result and dcf_result['matrix'] is not None:
                mat = dcf_result['matrix']
                fig_dcf = go.Figure(go.Heatmap(
                    z=mat,
                    x=dcf_result['g_labels'],
                    y=dcf_result['wacc_labels'],
                    colorscale='RdYlGn',
                    text=[[f'{v/1e9:.0f}' if not np.isnan(v) else 'N/A' for v in row] for row in mat],
                    texttemplate='%{text}',
                    showscale=True,
                    colorbar=dict(title='EV (tỷ VND)')
                ))
                ev_multiple = dcf_result.get('ev_ebitda_multiple', 0)
                fig_dcf.update_layout(
                    title=f'Enterprise Value (tỷ VND) · EV/EBITDA Mean = {ev_multiple:.1f}x',
                    xaxis_title='Tăng trưởng EBITDA dài hạn',
                    yaxis_title='Chi phí vốn WACC',
                    **DARK_TEMPLATE
                )
                st.plotly_chart(fig_dcf, use_container_width=True)

        st.divider()

        # ---- 5.3b STRUCTURAL SENSITIVITY (OIL & FX) ----
        st.subheader("🌡️ 3b. Ma trận Nhạy cảm Cấu trúc (Oil Price & FX Rate)")
        st.markdown(
            '<div class="info-box"><b>Mô hình:</b> Phân tích độ nhạy của định giá (EV/EBITDA) và Lợi nhuận ròng (Net Profit) '
            'dựa trên biến động chi phí nhiên liệu (Oil) và tỷ giá (FX). '
            'Mô hình tính toán tác động trực tiếp từ chi phí vận hành và đánh giá lại chênh lệch tỷ giá nợ vay USD.</div>',
            unsafe_allow_html=True
        )
        
        col_str1, col_str2 = st.columns([1, 3])
        with col_str1:
            # Sliders for parameters
            st.write("### 🛠️ Tham số đầu vào")
            s_base_oil = st.number_input("Giá dầu Jet A1 nền ($/thùng)", value=90.0, step=1.0, help="Giá dầu tham chiếu để tính biến động")
            s_base_fx = st.number_input("Tỷ giá USD/VND nền", value=26300.0, step=100.0, help="Tỷ giá tham chiếu để tính biến động")
            s_fuel_ratio = st.slider("Tỷ trọng Nhiên liệu/Opex (%)", 20, 60, 38) / 100
            s_debt_ratio = st.slider("Tỷ lệ Nợ USD/Tổng nợ (%)", 50, 100, 80) / 100
            
            st.divider()
            sensitivity_mode = st.radio("Chọn chỉ số hiển thị trên Ma trận:", ["Định giá (EV/EBITDA)", "Lợi nhuận ròng (Net Profit)"], index=0)
            
            st.caption("Cấu hình dải chạy Ma trận:")
            o_min, o_max = st.slider("Dải giá Dầu ($)", 50, 150, (70, 110))
            f_min, f_max = st.slider("Dải tỷ giá (VND)", 24000, 28000, (25000, 27500), step=100)

        struct_result = forecaster_obj.structural_sensitivity(
            base_oil=s_base_oil, base_fx=s_base_fx,
            fuel_opex_ratio=s_fuel_ratio, usd_debt_ratio=s_debt_ratio,
            oil_range=(o_min, o_max, 5), fx_range=(f_min, f_max, 100)
        )
        
        with col_str2:
            if struct_result:
                # --- LIVE IMPACT INDICATORS ---
                st.write("### 🔦 Cảnh báo & Tác động tức thời (Live Scenario Impact)")
                base = struct_result['base_data']
                
                # Calculate "Live Impact" based on slider's current single view vs a hypothetical small shift
                # or just use the current base as context.
                # Actually, let's create a "Current Scenario" summary based on slider values
                debt_in_usd = base['debt'] * s_debt_ratio / s_base_fx
                
                # Visual Alert for FX Revaluation
                fx_shift_pct = (s_base_fx / 24500.0 - 1) * 100 # Change from a fixed 'stable' rate if desired
                # Let's use user inputs as the 'target' and show impact if those were true
                
                c_m1, c_m2, c_m3 = st.columns(3)
                
                # We can calculate an 'estimated loss/gain' if FX moves +1% from current s_base_fx
                fx_1pct_loss = (base['debt'] * s_debt_ratio) * 0.01 / 1e9
                fuel_10d_loss = (base['fuel_cost'] * (10 / s_base_oil)) / 1e9
                
                c_m1.metric("Độ nhạy Tỷ giá", f"±1% USD/VND", f"{fx_1pct_loss:+.0f} tỷ VND", delta_color="inverse")
                c_m2.metric("Độ nhạy Giá dầu", f"±$10 Jet A1", f"{fuel_10d_loss:+.0f} tỷ VND", delta_color="inverse")
                
                # Logic cho "Cảnh báo tự động lãi/lỗ"
                # Giả định nếu s_base_fx thay đổi 1% so với mốc lịch sử ~24,500
                historical_fx = 24500
                total_fx_impact = (base['debt'] * s_debt_ratio) * (s_base_fx / historical_fx - 1) / 1e9
                c_m3.metric("Ước tính Lỗ tỷ giá lũy kế", f"vs mốc {historical_fx}", f"{total_fx_impact:,.0f} tỷ", delta_color="inverse")

                # --- THE HEATMAP ---
                if sensitivity_mode == "Định giá (EV/EBITDA)":
                    mat_s = struct_result['matrix']
                    title_s = 'Định giá EV/EBITDA theo kịch bản Chi phí & Tỷ giá'
                    z_label = 'EV/EBITDA (x)'
                    colorscale = 'RdYlGn_r'
                    text_vals = [[f'{v:.1f}x' if not np.isnan(v) else 'N/A' for v in row] for row in mat_s]
                else:
                    mat_s = struct_result['ni_matrix'] / 1e9 # Scale to tỷ VND
                    title_s = 'Lợi nhuận ròng (Ước tính tỷ VND) theo biến động vĩ mô'
                    z_label = 'NI (tỷ VND)'
                    colorscale = 'RdYlGn'
                    text_vals = [[f'{v:+.0f}t' if not np.isnan(v) else 'N/A' for v in row] for row in mat_s]

                fig_struct = go.Figure(go.Heatmap(
                    z=mat_s,
                    x=struct_result['oil_labels'],
                    y=struct_result['fx_labels'],
                    colorscale=colorscale,
                    text=text_vals,
                    texttemplate='%{text}',
                    showscale=True,
                    colorbar=dict(title=z_label)
                ))
                fig_struct.update_layout(
                    title=title_s,
                    xaxis_title='Giá dầu Jet A1 ($/thùng)',
                    yaxis_title='Tỷ giá USD/VND',
                    **DARK_TEMPLATE, height=550
                )
                st.plotly_chart(fig_struct, use_container_width=True)
                
                if sensitivity_mode == "Lợi nhuận ròng (Net Profit)":
                    st.warning("⚠️ **Lưu ý:** Lợi nhuận ròng bao gồm tác động từ chi phí nhiên liệu và đánh giá lại chênh lệch tỷ giá nợ vay. "
                               "HVN cực kỳ nhạy cảm với tỷ giá do dư nợ USD lớn.")

        st.divider()

        # ---- 5.3c SCENARIO ANALYSIS (LINE CHART) ----
        st.subheader("📈 3c. Kịch bản Định giá Phân kỳ (Scenario Analysis)")
        st.markdown(
            '<div class="info-box"><b>Tích hợp định lượng:</b> Kịch bản được neo trực tiếp từ '
            'Ma trận Nhạy cảm Cấu trúc (3b) và Độ co giãn Log-Log. '
            'Mỗi năm dự phóng tính toán EBITDA dựa trên quỹ đạo giá dầu & tỷ giá thực tế, '
            'không sử dụng hệ số tăng trưởng giả định.</div>',
            unsafe_allow_html=True
        )
        
        scenario_data = forecaster_obj.scenario_analysis(
            base_oil=s_base_oil, base_fx=s_base_fx,
            fuel_opex_ratio=s_fuel_ratio, usd_debt_ratio=s_debt_ratio
        )
        if scenario_data:
            sp = scenario_data.get('scenario_params', {})
            col_sc1, col_sc2 = st.columns([1, 2])
            with col_sc1:
                st.markdown(f"""
                **Kịch bản Cơ sở (Base):**
                - Dầu ~${s_base_oil:.0f}/thùng, FX trượt ~1%/năm.
                - Doanh thu tăng 5%/năm, EBITDA theo cấu trúc.
                - Định giá hội tụ: **{scenario_data['base'][-1]:.1f}x**.
                
                **Kịch bản Tiêu cực (Negative):**
                - Dầu sốc lên **${sp.get('neg_oil', 0):.0f}**, VND mất giá **5%** năm 1.
                - EBITDA năm 1: **{sp.get('neg_ebitda_chg', 0):+.1f}%** (từ Ma trận 3b).
                - EV/EBITDA: **{scenario_data['negative'][-1]:.1f}x** (cuối kỳ).
                
                **Kịch bản Tích cực (Positive):**
                - Dầu giảm về **${sp.get('pos_oil', 0):.0f}**, VND tăng giá nhẹ.
                - EBITDA năm 1: **{sp.get('pos_ebitda_chg', 0):+.1f}%**, Long Thành năm 3+.
                - EV/EBITDA: **{scenario_data['positive'][-1]:.1f}x** (cuối kỳ).
                
                ---
                *ε_oil = {sp.get('e_oil', 0):.2f}% · ε_fx = {sp.get('e_fx', 0):.2f}%*
                """)
                
            with col_sc2:
                fig_sc = go.Figure()
                fig_sc.add_trace(go.Scatter(x=scenario_data['years'], y=scenario_data['base'], 
                                            name='Cơ sở', line=dict(color=COLORS['cyan'], width=3),
                                            mode='lines+markers', marker=dict(size=7)))
                fig_sc.add_trace(go.Scatter(x=scenario_data['years'], y=scenario_data['negative'], 
                                            name='Tiêu cực', line=dict(color=COLORS['red'], width=3, dash='dot'),
                                            mode='lines+markers', marker=dict(size=7, symbol='triangle-down')))
                fig_sc.add_trace(go.Scatter(x=scenario_data['years'], y=scenario_data['positive'], 
                                            name='Tích cực', line=dict(color=COLORS['green'], width=4),
                                            mode='lines+markers', marker=dict(size=7, symbol='triangle-up')))
                
                latest_yr = scenario_data['years'][0]
                fig_sc.update_layout(
                    title=f'Dự phóng EV/EBITDA tích hợp Ma trận 3b + Log-Log ({latest_yr}–{scenario_data["years"][-1]})',
                    xaxis_title='Năm', yaxis_title='EV/EBITDA (x)',
                    **DARK_TEMPLATE,
                    legend=dict(orientation='h', y=-0.2)
                )
                st.plotly_chart(fig_sc, use_container_width=True)

        st.divider()

        # ---- 5.4 FOOTBALL FIELD CHART ----
        st.subheader("⚽ 4. Football Field Chart — So sánh Dải Giá trị & Giá mục tiêu")
        ff = f_results.get('FOOTBALL_FIELD')
        if ff:
            methods = ['EV/EBITDA (±1σ)', 'DCF TV Integration']
            mins = [ff['ev_ebitda_min'] / 1e9, ff['dcf_min'] / 1e9]
            maxs = [ff['ev_ebitda_max'] / 1e9, ff['dcf_max'] / 1e9]
            current_ev_b = ff['current_ev'] / 1e9
            
            # Giá mục tiêu tương ứng (VND/cổ phiếu)
            prices_min = [ff['price_ebitda_min'], ff['price_dcf_min']]
            prices_max = [ff['price_ebitda_max'], ff['price_dcf_max']]
            price_curr = ff['price_current']

            fig_ff = go.Figure()
            bar_colors = [COLORS['teal'], COLORS['purple']]
            for i, method in enumerate(methods):
                fig_ff.add_trace(go.Bar(
                    y=[method], x=[maxs[i] - mins[i]],
                    base=[mins[i]],
                    orientation='h',
                    name=method,
                    marker_color=bar_colors[i],
                    opacity=0.75,
                    text=[f'{mins[i]:,.0f} – {maxs[i]:,.0f} tỷ EV<br>({prices_min[i]:,.0f} – {prices_max[i]:,.0f} VND/cp)'],
                    textposition='inside',
                    textfont=dict(size=12, color='white')
                ))

            fig_ff.add_vline(
                x=current_ev_b, line_dash='dash', line_color=COLORS['yellow'], line_width=2.5,
                annotation_text=f'EV hiện tại: {current_ev_b:,.0f} tỷ (Giá: {price_curr:,.0f})',
                annotation_position='top right',
                annotation_font=dict(color=COLORS['yellow'], size=14)
            )

            fig_ff.update_layout(
                title='So sánh Dải Giá trị Doanh nghiệp & Giá mục tiêu tương ứng',
                xaxis_title='Enterprise Value (tỷ VND)',
                barmode='overlay',
                **DARK_TEMPLATE,
                height=350,
                showlegend=True,
                legend=dict(orientation='h', y=-0.25)
            )
            st.plotly_chart(fig_ff, use_container_width=True)
            
            st.markdown(f"""
            <div class="metric-card">
                <h4 style='color: white; margin-bottom: 10px;'>🎯 Tóm lược Giá mục tiêu (Target Price)</h4>
                <div style='display: flex; justify-content: space-around; align-items: center;'>
                    <div style='text-align: center; flex: 1;'>
                        <p style='color: #888; font-size: 0.85em; margin-bottom: 4px;'>Theo EV/EBITDA History (Đã chiết khấu)</p>
                        <p style='color: {COLORS["teal"]}; font-size: 1.6em; font-weight: bold;'>
                            {f"{ff['price_ebitda_min']:,.0f}" if ff['price_ebitda_min'] > 0 else "N/A"} – 
                            {f"{ff['price_ebitda_max']:,.0f}" if ff['price_ebitda_max'] > 0 else "N/A"}
                        </p>
                        <p style='color: #888; font-size: 0.75em;'>VND / cổ phiếu</p>
                    </div>
                    <div style='width: 1px; height: 50px; background: rgba(255,255,255,0.1);'></div>
                    <div style='text-align: center; flex: 1;'>
                        <p style='color: #888; font-size: 0.85em; margin-bottom: 4px;'>Theo DCF Integration</p>
                        <p style='color: {COLORS["purple"]}; font-size: 1.6em; font-weight: bold;'>
                            {f"{ff['price_dcf_min']:,.0f}" if ff['price_dcf_min'] > 0 else "N/A"} – 
                            {f"{ff['price_dcf_max']:,.0f}" if ff['price_dcf_max'] > 0 else "N/A"}
                        </p>
                        <p style='color: #888; font-size: 0.75em;'>VND / cổ phiếu</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(
                '<div class="info-box">'
                '<b>Cơ chế quy đổi:</b> Lượng tiền mặt khổng lồ gần 9.000 tỷ đồng huy động được từ đợt phát hành cổ phiếu '
                'đã làm giảm trực tiếp "Nợ thuần". Về mặt toán học, khi Nợ thuần giảm, Giá trị vốn cổ phần (Equity Value) '
                'sẽ tăng lên tương ứng, từ đó nâng đỡ giá mục tiêu của cổ phiếu.<br>'
                '<i>Công thức: Equity Value = EV - Nợ thuần - Lợi ích CĐ thiểu số</i>'
                '</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("Chưa có dữ liệu để vẽ Football Field Chart. Hãy chạy Pipeline trước.")
        

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 7: BÁO CÁO TỔNG HỢP
    # ═══════════════════════════════════════════════════════════════════════
    with tab7:
        st.header("📄 Báo cáo Phân tích Tài chính Tổng hợp")
        
        report_path = os.path.join(PROJECT_ROOT, "bao_cao", "BaoCao_PhanTich_HVN.md")
        
        col_r1, col_r2 = st.columns([3, 1])
        with col_r2:
            if st.button("🔄 Tạo lại Báo cáo", use_container_width=True,
                         help="Chạy lại Stage 5 (Report Generator) để cập nhật dữ liệu"):
                import subprocess, sys
                with st.spinner("Generating report..."):
                    try:
                        rg_script = os.path.join(PROJECT_ROOT, "src", "report_generator.py")
                        subprocess.run(
                            [sys.executable, rg_script],
                            cwd=PROJECT_ROOT, check=True
                        )
                        st.success("✅ Đã tạo lại báo cáo thành công!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")
        
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                report_md = f.read()
            
            with col_r1:
                # Đọc metadata từ dòng đầu của file
                first_lines = report_md.split('\n')[:3]
                date_line = next((l for l in first_lines if 'Ngày trích xuất' in l), '')
                st.caption(date_line.strip('*') if date_line else "")
            
            # Hiển thị báo cáo trong một khung đẹp
            st.markdown("""
<style>
.report-container {
    background: linear-gradient(135deg, rgba(15,52,96,0.15) 0%, rgba(26,26,46,0.3) 100%);
    border: 1px solid rgba(15,52,96,0.4);
    border-radius: 12px;
    padding: 28px 36px;
    margin-top: 8px;
    line-height: 1.75;
    font-size: 0.97em;
}
</style>""", unsafe_allow_html=True)
            
            st.markdown(f'<div class="report-container">', unsafe_allow_html=True)
            st.markdown(report_md)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Nút tải xuống
            st.download_button(
                label="📥 Tải xuống Báo cáo (.md)",
                data=report_md,
                file_name="BaoCao_PhanTich_HVN.md",
                mime="text/markdown",
                use_container_width=False
            )
        else:
            st.info("Chưa có báo cáo nào. Hãy nhấn **🔄 Tạo lại Báo cáo** hoặc chạy Pipeline ở sidebar để tạo báo cáo tự động.")

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 8: KIỂM ĐỊNH THỐNG KÊ TOÀN DIỆN
    # ═══════════════════════════════════════════════════════════════════════
    with tab8:
        st.header("🧪 Kiểm định Thống kê Toàn diện — Econometric Diagnostics")
        st.markdown(
            '<div class="info-box">'
            '<b>Mục đích:</b> Kiểm tra tính hợp lệ thống kê của toàn bộ mô hình hồi quy Log-Log, '
            'ma trận nhạy cảm, và cấu trúc dữ liệu đầu vào. '
            'Bộ kiểm định bao gồm 8 nhóm test kinh tế lượng chuẩn.'
            '</div>',
            unsafe_allow_html=True
        )

        # ── Controls: Alpha level selector ──
        col_alpha, col_info = st.columns([1, 3])
        with col_alpha:
            alpha_choice = st.selectbox(
                "Mức ý nghĩa α (Significance Level)",
                options=[0.01, 0.05, 0.10],
                index=1,
                format_func=lambda x: f"{x*100:.0f}% ({['Rất nghiêm ngặt', 'Chuẩn', 'Nới lỏng'][{0.01:0, 0.05:1, 0.10:2}[x]]})",
                key='alpha_selector'
            )
        with col_info:
            st.info(f"🎯 Đang áp dụng mức ý nghĩa **α = {alpha_choice*100:.0f}%** cho tất cả kiểm định. "
                    f"p-value < {alpha_choice} → Bác bỏ H₀.")

        # ── Load diagnostics data ──
        # Try loading from pipeline output first, then run on-the-fly
        diag_data = {}
        diag_dir = os.path.join(PROJECT_ROOT, "output/2.5_diagnostics")
        if os.path.exists(diag_dir):
            import json as _json
            combined_path = os.path.join(diag_dir, "ALL_DIAGNOSTICS.json")
            if os.path.exists(combined_path):
                with open(combined_path, 'r', encoding='utf-8') as _f:
                    diag_data = _json.load(_f)

        # Fallback: check dfs keys prefixed with DIAG_
        if not diag_data:
            for k, v in dfs.items():
                if k.startswith('DIAG_'):
                    diag_data[k.replace('DIAG_', '')] = v

        # If still no data, offer to run diagnostics
        if not diag_data:
            st.warning("⚠️ Chưa có kết quả kiểm định. Hãy **Chạy Pipeline** ở sidebar hoặc nhấn nút bên dưới.")
            if st.button("🔬 Chạy Bộ Kiểm định Ngay", use_container_width=True):
                with st.spinner("Đang chạy 8 nhóm kiểm định..."):
                    try:
                        from diagnostics import DiagnosticsEngine
                        diag_engine = DiagnosticsEngine(dfs, alpha=alpha_choice)
                        diag_data = diag_engine.run_all(alpha=alpha_choice)
                        diag_engine.save_outputs(diag_dir)
                        st.success("✅ Hoàn thành kiểm định!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

        if diag_data:
            # ════════════════════════════════════════════════════════════════
            # PANEL 1: STATIONARITY & COINTEGRATION
            # ════════════════════════════════════════════════════════════════
            st.divider()
            st.subheader("① Kiểm định Tính dừng (ADF) & Đồng liên kết (Engle-Granger)")
            stat_data = diag_data.get('STATIONARITY', {})

            if 'error' in stat_data:
                st.warning(f"Không thể chạy: {stat_data['error']}")
            else:
                adf_tests = stat_data.get('adf_tests', [])
                if adf_tests:
                    # Summary badges
                    cols_adf = st.columns(len(adf_tests))
                    for idx, test in enumerate(adf_tests):
                        with cols_adf[idx]:
                            series_name = test.get('series', '?')
                            is_stat = test.get('is_stationary')
                            p_val = test.get('p_value', 'N/A')
                            adf_stat = test.get('adf_stat', 'N/A')

                            if is_stat is True:
                                st.success(f"**{series_name}**\n\n✅ Dừng I(0)\n\nADF = {adf_stat}\n\np = {p_val}")
                            elif is_stat is False:
                                diff_stat = test.get('first_diff_stationary')
                                diff_label = '(Δ dừng)' if diff_stat else '(Δ không dừng)'
                                st.error(f"**{series_name}**\n\n⚠️ Không dừng I(1) {diff_label}\n\nADF = {adf_stat}\n\np = {p_val}")
                            else:
                                st.info(f"**{series_name}**\n\n{test.get('conclusion', 'N/A')}")

                    # Detailed table
                    with st.expander("📋 Chi tiết ADF Test", expanded=False):
                        adf_rows = []
                        for test in adf_tests:
                            crit = test.get('critical_values', {})
                            adf_rows.append({
                                'Chuỗi': test.get('series', ''),
                                'ADF Stat': test.get('adf_stat', 'N/A'),
                                'p-value': test.get('p_value', 'N/A'),
                                'Lag': test.get('used_lag', 'N/A'),
                                'CV 1%': crit.get('1%', 'N/A'),
                                'CV 5%': crit.get('5%', 'N/A'),
                                'CV 10%': crit.get('10%', 'N/A'),
                                'Kết luận': test.get('conclusion', ''),
                                'Δ ADF': test.get('first_diff_adf', ''),
                                'Δ p-value': test.get('first_diff_p', ''),
                            })
                        st.dataframe(pd.DataFrame(adf_rows), use_container_width=True)

                # Cointegration results
                coint_tests = stat_data.get('cointegration', [])
                if coint_tests:
                    st.markdown("##### Kiểm định Đồng liên kết Engle-Granger")
                    for ct in coint_tests:
                        if 'error' in ct:
                            st.warning(f"{ct['pair']}: {ct['error']}")
                        else:
                            is_coint = ct.get('is_cointegrated', False)
                            if is_coint:
                                st.success(f"✅ **{ct['pair']}**: {ct['conclusion']} (p={ct['p_value']})")
                            else:
                                st.error(f"⚠️ **{ct['pair']}**: {ct['conclusion']} (p={ct['p_value']})")
                elif stat_data.get('any_nonstationary'):
                    st.info("Không đủ dữ liệu để chạy kiểm định đồng liên kết.")

            # ════════════════════════════════════════════════════════════════
            # PANEL 2: REGRESSION DIAGNOSTICS (BP, DW, JB)
            # ════════════════════════════════════════════════════════════════
            st.divider()
            st.subheader("② Chẩn đoán Hồi quy Log-Log (Trục Regression Diagnostics)")
            st.markdown(
                '<div class="info-box">'
                'Kiểm tra 3 giả định cốt lõi của OLS: '
                '<b>Phương sai đồng nhất</b> (Breusch-Pagan) · '
                '<b>Không tự tương quan</b> (Durbin-Watson & Ljung-Box) · '
                '<b>Phần dư phân phối chuẩn</b> (Jarque-Bera).'
                '</div>',
                unsafe_allow_html=True
            )

            col_bp, col_dw, col_jb = st.columns(3)

            # Breusch-Pagan
            with col_bp:
                het_data = diag_data.get('HETEROSKEDASTICITY', {})
                if 'error' in het_data:
                    st.warning(f"BP: {het_data['error']}")
                else:
                    bp_pass = het_data.get('is_homoskedastic', False)
                    bp_p = het_data.get('lm_p_value', 'N/A')
                    bp_stat = het_data.get('lm_statistic', 'N/A')

                    fig_bp = go.Figure(go.Indicator(
                        mode='gauge+number',
                        value=bp_p if isinstance(bp_p, (int, float)) else 0,
                        title={'text': 'Breusch-Pagan'},
                        number={'suffix': '', 'valueformat': '.4f'},
                        gauge=dict(
                            axis=dict(range=[0, 1]),
                            bar=dict(color=COLORS['green'] if bp_pass else COLORS['red']),
                            threshold=dict(line=dict(color='white', width=3), thickness=0.8, value=alpha_choice),
                            steps=[
                                dict(range=[0, alpha_choice], color='rgba(233,69,96,0.3)'),
                                dict(range=[alpha_choice, 1], color='rgba(43,147,72,0.3)'),
                            ],
                        ),
                    ))
                    badge = '✅ PASS' if bp_pass else '⚠️ FAIL'
                    fig_bp.update_layout(
                        height=220, **DARK_TEMPLATE,
                        annotations=[dict(text=badge, x=0.5, y=-0.05, showarrow=False,
                                         font=dict(size=14, color=COLORS['green'] if bp_pass else COLORS['red']))],
                        margin=dict(t=60, b=40)
                    )
                    st.plotly_chart(fig_bp, use_container_width=True)
                    st.caption(f"LM={bp_stat} | p={bp_p}")

            # Durbin-Watson
            with col_dw:
                ac_data = diag_data.get('AUTOCORRELATION', {})
                if 'error' in ac_data:
                    st.warning(f"DW: {ac_data['error']}")
                else:
                    dw_info = ac_data.get('durbin_watson', {})
                    dw_val = dw_info.get('statistic', 2.0)
                    dw_pass = dw_info.get('pass', True)

                    fig_dw = go.Figure(go.Indicator(
                        mode='gauge+number',
                        value=dw_val,
                        title={'text': 'Durbin-Watson'},
                        number={'valueformat': '.3f'},
                        gauge=dict(
                            axis=dict(range=[0, 4]),
                            bar=dict(color=COLORS['green'] if dw_pass else COLORS['red']),
                            steps=[
                                dict(range=[0, 1.5], color='rgba(233,69,96,0.3)'),
                                dict(range=[1.5, 2.5], color='rgba(43,147,72,0.3)'),
                                dict(range=[2.5, 4], color='rgba(233,69,96,0.3)'),
                            ],
                        ),
                    ))
                    badge_dw = '✅ PASS' if dw_pass else '⚠️ FAIL'
                    fig_dw.update_layout(
                        height=220, **DARK_TEMPLATE,
                        annotations=[dict(text=badge_dw, x=0.5, y=-0.05, showarrow=False,
                                         font=dict(size=14, color=COLORS['green'] if dw_pass else COLORS['red']))],
                        margin=dict(t=60, b=40)
                    )
                    st.plotly_chart(fig_dw, use_container_width=True)

                    lb_info = ac_data.get('ljung_box', {})
                    st.caption(f"DW={dw_val:.3f} | Ljung-Box p={lb_info.get('p_value', 'N/A')}")

            # Jarque-Bera
            with col_jb:
                norm_data = diag_data.get('NORMALITY', {})
                if 'error' in norm_data:
                    st.warning(f"JB: {norm_data['error']}")
                else:
                    jb_info = norm_data.get('jarque_bera', {})
                    jb_pass = jb_info.get('pass', False)
                    jb_p = jb_info.get('p_value', 0)
                    jb_skew = jb_info.get('skewness', 0)
                    jb_kurt = jb_info.get('kurtosis', 0)

                    fig_jb = go.Figure(go.Indicator(
                        mode='gauge+number',
                        value=jb_p if isinstance(jb_p, (int, float)) else 0,
                        title={'text': 'Jarque-Bera'},
                        number={'valueformat': '.4f'},
                        gauge=dict(
                            axis=dict(range=[0, 1]),
                            bar=dict(color=COLORS['green'] if jb_pass else COLORS['red']),
                            threshold=dict(line=dict(color='white', width=3), thickness=0.8, value=alpha_choice),
                            steps=[
                                dict(range=[0, alpha_choice], color='rgba(233,69,96,0.3)'),
                                dict(range=[alpha_choice, 1], color='rgba(43,147,72,0.3)'),
                            ],
                        ),
                    ))
                    badge_jb = '✅ PASS' if jb_pass else '⚠️ FAIL'
                    fig_jb.update_layout(
                        height=220, **DARK_TEMPLATE,
                        annotations=[dict(text=badge_jb, x=0.5, y=-0.05, showarrow=False,
                                         font=dict(size=14, color=COLORS['green'] if jb_pass else COLORS['red']))],
                        margin=dict(t=60, b=40)
                    )
                    st.plotly_chart(fig_jb, use_container_width=True)
                    st.caption(f"Skew={jb_skew:.3f} | Kurt={jb_kurt:.3f}")

                    # Residual histogram
                    residuals_list = norm_data.get('residuals', [])
                    if residuals_list:
                        with st.expander("📊 Phân phối Phần dư (Histogram)"):
                            fig_hist = go.Figure(go.Histogram(
                                x=residuals_list, nbinsx=12,
                                marker_color=COLORS['cyan'], opacity=0.7,
                                name='Residuals'
                            ))
                            fig_hist.update_layout(
                                title='Phân phối Phần dư Mô hình Log-Log',
                                xaxis_title='Residual', yaxis_title='Frequency',
                                **DARK_TEMPLATE, height=280
                            )
                            st.plotly_chart(fig_hist, use_container_width=True)

            # ════════════════════════════════════════════════════════════════
            # PANEL 3: BACKTESTING
            # ════════════════════════════════════════════════════════════════
            st.divider()
            st.subheader("③ Kiểm định Sai số Dự báo — Backtesting (Expanding Window)")

            bt_data = diag_data.get('BACKTESTING', {})
            if 'error' in bt_data:
                st.warning(f"Backtesting: {bt_data['error']}")
            else:
                bt_config = bt_data.get('config', {})
                bt_metrics = bt_data.get('metrics', {})
                bt_results = bt_data.get('results', [])

                st.markdown(
                    f'<div class="info-box"><b>Phương pháp:</b> {bt_config.get("method", "")}. '
                    f'COVID Dummy: {"Bật" if bt_config.get("use_covid_dummy") else "Tắt"}. '
                    f'Tổng {bt_metrics.get("n_tests", 0)} năm kiểm tra.</div>',
                    unsafe_allow_html=True
                )

                if bt_results:
                    # Metrics badges
                    m1, m2, m3 = st.columns(3)
                    m1.metric("MAE (Sai số tuyệt đối TB)", f"{bt_metrics.get('MAE', 0):,.0f}")
                    m2.metric("RMSE (Căn bậc 2 sai số)", f"{bt_metrics.get('RMSE', 0):,.0f}")
                    mape_val = bt_metrics.get('MAPE', 0)
                    mape_color = 'normal' if mape_val < 10 else 'inverse'
                    m3.metric("MAPE (Sai số % TB)", f"{mape_val:.1f}%",
                              delta='Tốt' if mape_val < 10 else 'Cần cải thiện',
                              delta_color=mape_color)

                    # Chart: Actual vs Predicted
                    bt_years = [r['year'] for r in bt_results]
                    bt_actual = [r['actual_tc'] for r in bt_results]
                    bt_predicted = [r['predicted_tc'] for r in bt_results]
                    bt_errors = [r['error_pct'] for r in bt_results]

                    col_bt1, col_bt2 = st.columns([2, 1])
                    with col_bt1:
                        fig_bt = go.Figure()
                        fig_bt.add_trace(go.Scatter(
                            x=bt_years, y=bt_actual, name='Thực tế',
                            mode='lines+markers', line=dict(color=COLORS['cyan'], width=3),
                            marker=dict(size=10)
                        ))
                        fig_bt.add_trace(go.Scatter(
                            x=bt_years, y=bt_predicted, name='Dự báo',
                            mode='lines+markers', line=dict(color=COLORS['orange'], width=3, dash='dash'),
                            marker=dict(size=10, symbol='diamond')
                        ))
                        fig_bt.update_layout(
                            title='Backtesting: Tổng Chi phí Thực tế vs Dự báo',
                            xaxis_title='Năm', yaxis_title='Tổng Chi phí (VND)',
                            **DARK_TEMPLATE, height=350,
                            legend=dict(orientation='h', y=-0.2)
                        )
                        st.plotly_chart(fig_bt, use_container_width=True)

                    with col_bt2:
                        err_colors = [COLORS['green'] if e < 5 else (COLORS['yellow'] if e < 10 else COLORS['red'])
                                      for e in bt_errors]
                        fig_err = go.Figure(go.Bar(
                            x=bt_years, y=bt_errors,
                            marker_color=err_colors,
                            text=[f'{e:.1f}%' for e in bt_errors],
                            textposition='outside'
                        ))
                        fig_err.update_layout(
                            title='Sai số Dự báo (%)',
                            yaxis_title='%', **DARK_TEMPLATE, height=350
                        )
                        st.plotly_chart(fig_err, use_container_width=True)

            # ════════════════════════════════════════════════════════════════
            # PANEL 4: DISTRIBUTIONAL ANALYSIS (Oil & FX)
            # ════════════════════════════════════════════════════════════════
            st.divider()
            st.subheader("④ Kiểm định Cấu trúc Phân phối — Oil Price & FX Rate")

            dist_data = diag_data.get('DISTRIBUTIONAL', {})
            if 'error' in dist_data:
                st.warning(f"Distributional: {dist_data['error']}")
            else:
                dist_tests = dist_data.get('tests', {})
                col_oil, col_fx = st.columns(2)

                for col_target, var_name, display_name in [(col_oil, 'Oil_Price', 'Giá Dầu Jet A1'), (col_fx, 'FX_Rate', 'Tỷ giá USD/VND')]:
                    with col_target:
                        var_data = dist_tests.get(var_name, {})
                        if 'error' in var_data:
                            st.warning(f"{display_name}: {var_data['error']}")
                            continue

                        stats = var_data.get('statistics', {})
                        dist_type = var_data.get('distribution_type', 'N/A')
                        ks = var_data.get('ks_test', {})
                        sw = var_data.get('shapiro_wilk', {})

                        # Distribution badge
                        if 'Normal' in dist_type or 'chuẩn' in dist_type:
                            st.success(f"**{display_name}**: {dist_type}")
                        elif 'Fat' in dist_type:
                            st.error(f"**{display_name}**: {dist_type}")
                        else:
                            st.warning(f"**{display_name}**: {dist_type}")

                        # Stats table
                        st.markdown(
                            f"- **KS test:** stat={ks.get('statistic', 'N/A')}, p={ks.get('p_value', 'N/A')} "
                            f"{'✅' if ks.get('is_normal') else '❌'}\n"
                            f"- **Shapiro-Wilk:** stat={sw.get('statistic', 'N/A')}, p={sw.get('p_value', 'N/A')} "
                            f"{'✅' if sw.get('is_normal') else '❌'}\n"
                            f"- **Skewness:** {stats.get('skewness', 'N/A')} | "
                            f"**Excess Kurtosis:** {stats.get('excess_kurtosis', 'N/A')}\n"
                            f"- **Mean Return:** {stats.get('mean_return', 'N/A')}% | "
                            f"**Std Return:** {stats.get('std_return', 'N/A')}%"
                        )

                        # Histogram of log-returns
                        log_returns = var_data.get('log_returns', [])
                        if log_returns:
                            fig_dist = go.Figure(go.Histogram(
                                x=[r * 100 for r in log_returns],
                                nbinsx=10,
                                marker_color=COLORS['teal'] if var_name == 'Oil_Price' else COLORS['purple'],
                                opacity=0.75, name='Log-Returns'
                            ))
                            # Overlay normal curve
                            x_norm = np.linspace(min(log_returns)*100, max(log_returns)*100, 50)
                            from scipy.stats import norm as _norm
                            y_norm = _norm.pdf(x_norm, loc=stats.get('mean_return', 0), scale=stats.get('std_return', 1))
                            y_norm_scaled = y_norm * len(log_returns) * (max(log_returns) - min(log_returns)) * 100 / 10
                            fig_dist.add_trace(go.Scatter(
                                x=x_norm, y=y_norm_scaled,
                                mode='lines', name='Normal fit',
                                line=dict(color='white', width=2, dash='dash')
                            ))
                            fig_dist.update_layout(
                                title=f'{display_name} — Log-Returns Distribution',
                                xaxis_title='Log-Return (%)', yaxis_title='Frequency',
                                **DARK_TEMPLATE, height=280,
                                showlegend=False
                            )
                            st.plotly_chart(fig_dist, use_container_width=True)

            # ════════════════════════════════════════════════════════════════
            # PANEL 5: WACC-g SINGULARITY MAP
            # ════════════════════════════════════════════════════════════════
            st.divider()
            st.subheader("⑤ Điểm Kỳ dị Toán học — Ma trận WACC-g (Singularity Detection)")

            sing_data = diag_data.get('SINGULARITY', {})
            if 'error' in sing_data:
                st.warning(f"Singularity: {sing_data['error']}")
            else:
                n_sing = sing_data.get('n_singular', 0)
                n_near = sing_data.get('n_near_singular', 0)
                total = sing_data.get('total_cells', 1)
                cond = sing_data.get('condition_number', 'N/A')
                stability = sing_data.get('stability', 'N/A')

                s1, s2, s3 = st.columns(3)
                s1.metric("Ô Kỳ dị (WACC ≤ g)", f"{n_sing}", f"{n_sing/total*100:.1f}% ma trận")
                s2.metric("Ô Gần Kỳ dị (gap < 0.5%)", f"{n_near}")
                if stability == 'Ổn định (Well-conditioned)':
                    s3.metric("Condition Number", f"{cond}", stability)
                else:
                    s3.metric("Condition Number", f"{cond}", stability, delta_color='inverse')

                # Singularity heatmap
                sing_map = sing_data.get('singularity_map', [])
                if sing_map:
                    wacc_labels = sing_data.get('wacc_labels', [])
                    g_labels = sing_data.get('g_labels', [])

                    # Custom colorscale: 0=Safe(green), 1=Near(yellow), 2=Singular(red)
                    fig_sing = go.Figure(go.Heatmap(
                        z=sing_map,
                        x=g_labels,
                        y=wacc_labels,
                        colorscale=[
                            [0, 'rgba(43,147,72,0.4)'],
                            [0.45, 'rgba(43,147,72,0.4)'],
                            [0.5, 'rgba(249,199,79,0.6)'],
                            [0.75, 'rgba(249,199,79,0.6)'],
                            [0.76, 'rgba(233,69,96,0.8)'],
                            [1.0, 'rgba(233,69,96,0.8)'],
                        ],
                        text=[[('SINGULAR' if v == 2 else ('NEAR' if v == 1 else '')) for v in row] for row in sing_map],
                        texttemplate='%{text}',
                        showscale=False,
                        hovertemplate='WACC=%{y}, g=%{x}<br>Zone: %{text}<extra></extra>'
                    ))
                    fig_sing.update_layout(
                        title='Bản đồ Vùng Kỳ dị: WACC vs g (Xanh=An toàn, Vàng=Gần kỳ dị, Đỏ=Kỳ dị)',
                        xaxis_title='Tốc độ tăng trưởng (g)',
                        yaxis_title='Chi phí vốn (WACC)',
                        **DARK_TEMPLATE, height=450
                    )
                    st.plotly_chart(fig_sing, use_container_width=True)

                st.markdown(
                    '<div class="info-box">'
                    '<b>Giải thích:</b> Khi WACC ≤ g, mẫu số trong mô hình Gordon Growth tiến về 0, '
                    'tạo ra giá trị Terminal Value tiệm cận vô cực (singularity). '
                    'Các ô <b>NEAR</b> (gap < 0.5%) là vùng nhạy cảm cực đoan — '
                    'biến động nhỏ trong WACC hoặc g có thể gây thay đổi lớn trong định giá.'
                    '</div>',
                    unsafe_allow_html=True
                )

            # ════════════════════════════════════════════════════════════════
            # PANEL 6: ENDOGENEITY DIAGNOSTICS
            # ════════════════════════════════════════════════════════════════
            st.divider()
            st.subheader("⑥ Kiểm định Nội sinh — Cấu trúc Vốn (Endogeneity Check)")

            endo_data = diag_data.get('ENDOGENEITY', {})
            if 'error' in endo_data:
                st.warning(f"Endogeneity: {endo_data['error']}")
            else:
                method_note = endo_data.get('method_note', '')
                if method_note:
                    st.info(f"💡 {method_note}")

                # Granger Causality results
                granger_tests = endo_data.get('granger_tests', [])
                if granger_tests:
                    st.markdown("##### Kiểm định Granger Causality")

                    gc_rows = []
                    for gc in granger_tests:
                        if 'error' in gc:
                            gc_rows.append({
                                'Nhân quả': f"{gc['cause']} → {gc['effect']}",
                                'Lag tối ưu': 'N/A',
                                'F-stat': 'N/A',
                                'p-value': 'N/A',
                                'Kết luận': gc['error'],
                            })
                        else:
                            is_causal = gc.get('is_granger_causal', False)
                            gc_rows.append({
                                'Nhân quả': f"{gc['cause']} → {gc['effect']}",
                                'Lag tối ưu': gc.get('optimal_lag', 'N/A'),
                                'F-stat': gc.get('f_statistic', 'N/A'),
                                'p-value': gc.get('p_value', 'N/A'),
                                'Kết luận': gc.get('conclusion', ''),
                                'Nội sinh?': '⚠️ CÓ' if is_causal else '✅ KHÔNG',
                            })

                    gc_df = pd.DataFrame(gc_rows)
                    st.dataframe(gc_df, use_container_width=True, hide_index=True)

                    # Visualize Granger relationships
                    valid_gc = [gc for gc in granger_tests if 'error' not in gc]
                    if valid_gc:
                        fig_gc = go.Figure()
                        gc_names = [f"{gc['cause']}→{gc['effect']}" for gc in valid_gc]
                        gc_pvals = [gc.get('p_value', 1) for gc in valid_gc]
                        gc_colors = [COLORS['red'] if p < alpha_choice else COLORS['green'] for p in gc_pvals]

                        fig_gc.add_trace(go.Bar(
                            x=gc_names, y=gc_pvals,
                            marker_color=gc_colors, opacity=0.8,
                            text=[f'{p:.4f}' for p in gc_pvals],
                            textposition='outside'
                        ))
                        fig_gc.add_hline(
                            y=alpha_choice, line_dash='dash', line_color='white',
                            annotation_text=f'α = {alpha_choice}',
                            annotation_font=dict(size=12, color='white')
                        )
                        fig_gc.update_layout(
                            title=f'Granger Causality p-values (Đỏ = Nội sinh tại α={alpha_choice*100:.0f}%)',
                            yaxis_title='p-value', **DARK_TEMPLATE, height=350,
                            xaxis_tickangle=-15
                        )
                        st.plotly_chart(fig_gc, use_container_width=True)

                    with st.expander("📋 Chi tiết Lag Selection (AIC/BIC)"):
                        for gc in granger_tests:
                            if 'lag_details' in gc:
                                st.markdown(f"**{gc['cause']} → {gc['effect']}** (Lag tối ưu: {gc.get('optimal_lag', '?')})")
                                lag_df = pd.DataFrame(gc['lag_details'])
                                st.dataframe(lag_df, use_container_width=True, hide_index=True)

                # Hausman heuristic
                hausman = endo_data.get('hausman_heuristic')
                if hausman:
                    st.markdown("##### Hausman-type Heuristic (Tương quan Phần dư — D/E)")
                    corr_val = hausman.get('abs_correlation', 0)
                    is_endo = hausman.get('is_endogenous', False)

                    if is_endo:
                        st.error(f"⚠️ {hausman['conclusion']} — Tương quan giữa phần dư mô hình Log-Log và hệ số D/E vượt ngưỡng 0.3, "
                                 f"nghi ngờ nội sinh trong cấu trúc vốn.")
                    else:
                        st.success(f"✅ {hausman['conclusion']} — Biến đòn bẩy tài chính có thể coi là ngoại sinh.")

                    fig_h = go.Figure(go.Indicator(
                        mode='gauge+number',
                        value=corr_val,
                        title={'text': '|ρ(Residual, D/E)|'},
                        number={'valueformat': '.4f'},
                        gauge=dict(
                            axis=dict(range=[0, 1]),
                            bar=dict(color=COLORS['red'] if is_endo else COLORS['green']),
                            threshold=dict(line=dict(color='white', width=3), thickness=0.8, value=0.3),
                            steps=[
                                dict(range=[0, 0.3], color='rgba(43,147,72,0.3)'),
                                dict(range=[0.3, 1.0], color='rgba(233,69,96,0.3)'),
                            ],
                        ),
                    ))
                    fig_h.update_layout(height=220, **DARK_TEMPLATE, margin=dict(t=60, b=20))
                    st.plotly_chart(fig_h, use_container_width=True)


if __name__ == "__main__":
    main()

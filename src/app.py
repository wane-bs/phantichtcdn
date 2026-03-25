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
from ml_analyzer import MLAnalyzer

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
def load_data(_v=3):  # bump _v to invalidate old cache
    processor = DataProcessor("data/hvn_data.xlsx")
    dfs = processor.load_and_normalize()
    calc = Calculator(dfs)
    return calc.run_all()

@st.cache_data
def load_forecaster_data(_dfs):
    f = Forecaster(_dfs)
    return f.run_all(), f

@st.cache_data
def load_ml_data(_dfs):
    m = MLAnalyzer(_dfs)
    return m.run_all(), m

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
    st.title("Vietnam Airlines (HVN) — Financial Analytics Dashboard")

    try:
        dfs = load_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

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
    anomaly_numeric = dfs.get('ANOMALY_NUMERIC', {})
    years = [c for c in bs.columns if c != 'Khoản mục']

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Survival", "Operating", "Financial Ratios", "Anomaly",
        "Data Tables", "Dự báo & ML"
    ])

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 1: SURVIVAL DASHBOARD
    # ═══════════════════════════════════════════════════════════════════════
    with tab1:
        st.header("Khả năng sinh tồn (Dòng tiền & Cấu trúc vốn)")
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Cơ cấu Nợ vs Vốn Chủ Sở Hữu")
            liabilities = get_row_data(bs, r'^NỢ PHẢI TRẢ$')
            equity = get_row_data(bs, r'^VỐN CHỦ SỞ HỮU$')

            if liabilities is not None and equity is not None:
                fig = go.Figure(data=[
                    go.Bar(name='Nợ Phải Trả', x=years, y=liabilities,
                           marker_color=COLORS['red'], opacity=0.85),
                    go.Bar(name='Vốn Chủ Sở Hữu', x=years, y=equity,
                           marker_color=COLORS['purple'], opacity=0.85)
                ])
                fig.update_layout(
                    barmode='group', **DARK_TEMPLATE,
                    title="VCSH âm nặng 2022-2024, phục hồi 2025",
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Dòng tiền theo hoạt động (100% Stacked Area)")
            ocf = get_row_data(cf, r'^Lưu chuyển tiền thuần từ các hoạt động sản xuất kinh doanh$')
            icf = get_row_data(cf, r'^Lưu chuyển tiền tệ ròng từ hoạt động đầu tư$')
            fcf = get_row_data(cf, r'^Lưu chuyển tiền tệ từ hoạt động tài chính$')

            if ocf is not None and icf is not None and fcf is not None:
                abs_ocf = ocf.abs(); abs_icf = icf.abs(); abs_fcf = fcf.abs()
                total = (abs_ocf + abs_icf + abs_fcf).replace(0, 1)
                pct_ocf = abs_ocf / total * 100
                pct_icf = abs_icf / total * 100
                pct_fcf = abs_fcf / total * 100

                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=years, y=pct_ocf, name='OCF (HĐKD)',
                    mode='lines', stackgroup='one', groupnorm='percent',
                    fillcolor='rgba(43,147,72,0.6)', line=dict(color=COLORS['green'], width=0.5)))
                fig2.add_trace(go.Scatter(x=years, y=pct_icf, name='ICF (Đầu tư)',
                    mode='lines', stackgroup='one',
                    fillcolor='rgba(233,69,96,0.6)', line=dict(color=COLORS['red'], width=0.5)))
                fig2.add_trace(go.Scatter(x=years, y=pct_fcf, name='FCF (Tài chính)',
                    mode='lines', stackgroup='one',
                    fillcolor='rgba(83,52,131,0.6)', line=dict(color=COLORS['purple'], width=0.5)))
                fig2.update_layout(
                    title="Tỷ trọng dòng tiền theo hoạt động",
                    yaxis_title='%', yaxis=dict(range=[0, 100]),
                    **DARK_TEMPLATE,
                    legend=dict(orientation='h', y=-0.15)
                )
                st.plotly_chart(fig2, use_container_width=True)

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
        if cash_inout is not None:
            st.subheader("Thực Thu − Thực Chi − Dòng tiền Ròng")
            ci_years = [c for c in cash_inout.columns if c != 'Khoản mục']
            total_in = get_row_data(cash_inout, r'^═══ TỔNG THỰC THU')
            total_out = get_row_data(cash_inout, r'^═══ TỔNG THỰC CHI')
            net = get_row_data(cash_inout, r'^═══ DÒNG TIỀN RÒNG')
            if total_in is not None and total_out is not None:
                fig_ci = go.Figure()
                fig_ci.add_trace(go.Scatter(
                    x=ci_years, y=total_in, name='Tổng Thu',
                    mode='lines+markers', line=dict(color=COLORS['green'], width=3),
                    marker=dict(size=10, symbol='triangle-up')))
                fig_ci.add_trace(go.Scatter(
                    x=ci_years, y=total_out, name='Tổng Chi',
                    mode='lines+markers', line=dict(color=COLORS['red'], width=3),
                    marker=dict(size=10, symbol='triangle-down')))
                if net is not None:
                    net_colors = [COLORS['green'] if v >= 0 else COLORS['red'] for v in net]
                    fig_ci.add_trace(go.Bar(
                        x=ci_years, y=net, name='Dòng tiền Ròng',
                        marker_color=net_colors, opacity=0.5,
                        text=[f'{v:,.0f}' for v in net], textposition='outside'))
                fig_ci.update_layout(
                    title='Thực Thu vs Thực Chi & Dòng tiền Ròng (tỷ VND)',
                    **DARK_TEMPLATE,
                    legend=dict(orientation='h', y=-0.15),
                    barmode='overlay'
                )
                st.plotly_chart(fig_ci, use_container_width=True)

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 2: OPERATING DASHBOARD
    # ═══════════════════════════════════════════════════════════════════════
    with tab2:
        st.header("Hiệu suất kinh doanh")
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

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 3: FINANCIAL RATIOS
    # ═══════════════════════════════════════════════════════════════════════
    with tab3:
        st.header("Chỉ số Tài chính Tổng hợp")

        # --- 3.1 Valuation ---
        st.subheader("1. Định giá (Valuation)")
        c1, c2 = st.columns(2)
        with c1:
            pe = get_fi_row(fi, r'^P/E$')
            pb = get_fi_row(fi, r'^P/B$')
            ps = get_fi_row(fi, r'^P/S$')
            fig_val = plot_line_multi({'P/E': pe, 'P/B': pb, 'P/S': ps}, "Hệ số định giá", years, 'x')
            st.plotly_chart(fig_val, use_container_width=True)
        with c2:
            ev_ebitda = get_fi_row(fi, r'^EV/EBITDA$')
            p_cf = get_fi_row(fi, r'^P/Cash Flow$|^P/CF$')
            fig_val2 = plot_line_multi({'EV/EBITDA': ev_ebitda, 'P/Cash Flow': p_cf},
                                       "EV/EBITDA & P/CF", years, 'x')
            st.plotly_chart(fig_val2, use_container_width=True)

        # --- 3.2 Profitability + DuPont (CLUSTERED BAR) ---
        st.subheader("2. Khả năng sinh lời (Profitability)")
        c3, c4 = st.columns(2)
        with c3:
            roe = get_fi_row(fi, r'^ROE')
            roa = get_fi_row(fi, r'^ROA')
            roic = get_fi_row(fi, r'^ROIC')
            fig_prof = plot_line_multi({'ROE': roe, 'ROA': roa, 'ROIC': roic},
                                       "ROE / ROA / ROIC (%)", years, '%')
            st.plotly_chart(fig_prof, use_container_width=True)

        with c4:
            st.markdown("**Ph\u00e2n t\u00edch DuPont 3 nh\u00e2n t\u1ed1 (Combo Bar\u2013Line)**")
            if dupont is not None:
                dp_years = [c for c in dupont.columns if c != 'Kho\u1ea3n m\u1ee5c']
                ros_d = get_row_data(dupont, r'^ROS')
                at_d  = get_row_data(dupont, r'^Asset Turnover')
                lev_d = get_row_data(dupont, r'^Financial Leverage')
                roe_d = get_row_data(dupont, r'^ROE')

                fig_dup = make_subplots(
                    rows=1, cols=3,
                    subplot_titles=('ROS \u2014 Bi\u00ean LN r\u00f2ng (%)', 'Asset Turnover (x)', '\u0110\u00f2n b\u1ea9y TC (x)'),
                    horizontal_spacing=0.08,
                    specs=[[{"secondary_y": True}]*3]
                )
                # ROS bar + ROE line
                if ros_d is not None:
                    fig_dup.add_trace(go.Bar(
                        name='ROS (%)', x=dp_years, y=ros_d,
                        marker_color=COLORS['green'],
                        text=[f'{v:.1f}%' for v in ros_d], textposition='outside',
                        showlegend=True
                    ), row=1, col=1, secondary_y=False)
                if roe_d is not None:
                    fig_dup.add_trace(go.Scatter(
                        name='ROE (%)', x=dp_years, y=roe_d,
                        mode='lines+markers',
                        line=dict(color=COLORS['yellow'], width=2, dash='dot'),
                        marker=dict(size=6), showlegend=True
                    ), row=1, col=1, secondary_y=True)
                # AT bar + ROE line
                if at_d is not None:
                    fig_dup.add_trace(go.Bar(
                        name='AT (x)', x=dp_years, y=at_d,
                        marker_color=COLORS['cyan'],
                        text=[f'{v:.2f}x' for v in at_d], textposition='outside',
                        showlegend=True
                    ), row=1, col=2, secondary_y=False)
                if roe_d is not None:
                    fig_dup.add_trace(go.Scatter(
                        name='ROE', x=dp_years, y=roe_d,
                        mode='lines+markers',
                        line=dict(color=COLORS['yellow'], width=2, dash='dot'),
                        marker=dict(size=6), showlegend=False
                    ), row=1, col=2, secondary_y=True)
                # Lev bar + ROE line
                if lev_d is not None:
                    fig_dup.add_trace(go.Bar(
                        name='Lev (x)', x=dp_years, y=lev_d,
                        marker_color=COLORS['orange'],
                        text=[f'{v:.1f}x' for v in lev_d], textposition='outside',
                        showlegend=True
                    ), row=1, col=3, secondary_y=False)
                if roe_d is not None:
                    fig_dup.add_trace(go.Scatter(
                        name='ROE', x=dp_years, y=roe_d,
                        mode='lines+markers',
                        line=dict(color=COLORS['yellow'], width=2, dash='dot'),
                        marker=dict(size=6), showlegend=False
                    ), row=1, col=3, secondary_y=True)
                fig_dup.update_layout(
                    height=400, **DARK_TEMPLATE,
                    title='DuPont 3 nhân tố ROE (đường vàng chấm = ROE %)',
                    legend=dict(orientation='h', y=-0.15, font=dict(size=10))
                )
                for i in range(1, 4):
                    fig_dup.update_yaxes(title_text='', secondary_y=True, row=1, col=i)
                st.plotly_chart(fig_dup, use_container_width=True)

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

        st.subheader("Phân rã ΔROE (Best-fit OLS)")
        _render_dupont_impact(dupont_impact, dupont_betas, 'ROE')
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

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 4: ANOMALY ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════
    with tab4:
        st.header("Phân tích Bất thường (Beneish · Altman · Sloan)")

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
        else:
            st.info("Không đủ dữ liệu để tính Anomaly Scores.")

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 5: DATA TABLES
    # ═══════════════════════════════════════════════════════════════════════
    with tab5:
        st.header("Bảng dữ liệu chi tiết")
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
    # TAB 5: DỰ BÁO & ML
    # ═══════════════════════════════════════════════════════════════════════
    with tab6:
        st.header("Phân tích Nâng cao — Cấu trúc, Chu kỳ & ML")
        st.markdown("""
<div class="info-box">
Triết lý: Không dự báo điểm. Tập trung vào <b>bóc tách cấu trúc</b> và <b>mô phỏng kịch bản</b>
để trả lời "tại sao ROE thay đổi" và "nếu thay đổi nhân tố X thì Y sẽ ra sao".
</div>""", unsafe_allow_html=True)

        try:
            f_results, forecaster_obj = load_forecaster_data(dfs)
            ml_results, ml_obj = load_ml_data(dfs)
        except Exception as e:
            st.error(f"Lỗi khởi tạo module phân tích: {e}")
            f_results, ml_results = {}, {}
            forecaster_obj = Forecaster(dfs)
            ml_obj = MLAnalyzer(dfs)

        # ---- 5.1 STL DECOMPOSITION ----
        st.subheader("1. Phân rã Chu kỳ STL (Trend / Seasonal / Residual)")
        stl_options = forecaster_obj.get_stl_series_options()
        sel_series = st.selectbox("Chọn chỉ số để phân rã:", stl_options, key='stl_select')

        stl_result = forecaster_obj.stl_decomposition(sel_series)
        if stl_result:
            method_tag = stl_result.get('method', '')
            stl_years  = list(stl_result['original'].index)

            col_stl1, col_stl2, col_stl3 = st.columns(3)
            with col_stl1:
                fig_trend = go.Figure(go.Scatter(
                    x=stl_years, y=stl_result['trend'],
                    mode='lines+markers', name='Trend',
                    line=dict(color=COLORS['cyan'], width=2.5), marker=dict(size=8)
                ))
                fig_trend.update_layout(title=f'Xu hướng dài hạn ({method_tag})', **DARK_TEMPLATE,
                                        height=260)
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
                '<div class="info-box"><b>Đọc kết quả:</b> Residual lớn (±) = biến động bất thường không mang tính quy luật. '
                'Seasonal ≈ 0 với dữ liệu năm là bình thường. Trend = năng lực lõi dài hạn.</div>',
                unsafe_allow_html=True
            )
        else:
            st.warning(f"Không đủ dữ liệu để phân rã STL cho '{sel_series}'.")

        st.divider()

        # ---- 5.2 VALUATION BANDS ----
        st.subheader("2. Dải Định giá Lịch sử (Valuation Bands P/E)")
        vb = f_results.get('VALUATION_BANDS')
        if vb:
            vb_years = vb['years']
            fig_vb = go.Figure()
            fig_vb.add_trace(go.Scatter(x=vb_years, y=[vb['upper_2s']] * len(vb_years),
                name='+2σ', line=dict(color='rgba(233,69,96,0.4)', dash='dot', width=1), mode='lines'))
            fig_vb.add_trace(go.Scatter(x=vb_years, y=[vb['upper_1s']] * len(vb_years),
                name='+1σ', line=dict(color='rgba(255,107,53,0.6)', dash='dot', width=1.5), mode='lines'))
            fig_vb.add_trace(go.Scatter(x=vb_years, y=[vb['mean']] * len(vb_years),
                name='Mean', line=dict(color='white', dash='dash', width=1.5), mode='lines'))
            fig_vb.add_trace(go.Scatter(x=vb_years, y=[vb['lower_1s']] * len(vb_years),
                name='-1σ', line=dict(color='rgba(255,107,53,0.6)', dash='dot', width=1.5), mode='lines'))
            fig_vb.add_trace(go.Scatter(x=vb_years, y=[vb['lower_2s']] * len(vb_years),
                name='-2σ', line=dict(color='rgba(233,69,96,0.4)', dash='dot', width=1), mode='lines'))
            fig_vb.add_trace(go.Scatter(x=vb_years, y=vb['original'].values,
                name='P/E thực tế', mode='lines+markers',
                line=dict(color=COLORS['yellow'], width=2.5), marker=dict(size=10)))
            band_pos = vb.get('band_position', 0.5)
            fig_vb.update_layout(title=f'P/E Valuation Bands  ·  Band Position hiện tại: {band_pos:.2f} (0=rẻ, 1=đắt)',
                                 **DARK_TEMPLATE, yaxis_title='P/E (x)',
                                 legend=dict(orientation='h', y=-0.15))
            st.plotly_chart(fig_vb, use_container_width=True)
        else:
            st.info("Không có dữ liệu P/E trong FINANCIAL INDEX để vẽ Valuation Bands.")

        st.divider()

        # ---- 5.3 DCF SENSITIVITY HEATMAP ----
        st.subheader("🌡️ 3. Ma trận Độ nhạy DCF (WACC × g)")
        col_dcf1, col_dcf2 = st.columns([1, 3])
        with col_dcf1:
            wacc_min = st.slider("WACC tối thiểu (%)", 6, 12, 8, step=1) / 100
            wacc_max = st.slider("WACC tối đa (%)", 12, 20, 16, step=1) / 100
            g_min = st.slider("g tối thiểu (%)", 0, 3, 0, step=1) / 100
            g_max = st.slider("g tối đa (%)", 3, 8, 6, step=1) / 100
            st.markdown(f"""
<div class="info-box">
<b>OCF năm 2025</b> được dùng làm FCFF base.
<b>V = FCFF / (WACC - g)</b><br>
Gordon Growth Model đơn giản hóa.
</div>""", unsafe_allow_html=True)

        with col_dcf2:
            dcf_result = forecaster_obj.dcf_sensitivity(
                wacc_range=(wacc_min, wacc_max, 0.005),
                g_range=(g_min, g_max, 0.005)
            )
            if dcf_result and dcf_result['matrix'] is not None:
                mat = dcf_result['matrix']
                fig_dcf = go.Figure(go.Heatmap(
                    z=mat,
                    x=dcf_result['g_labels'],
                    y=dcf_result['wacc_labels'],
                    colorscale='RdYlGn',
                    text=[[f'{v:.0f}' if not np.isnan(v) else 'N/A' for v in row] for row in mat],
                    texttemplate='%{text}',
                    showscale=True,
                    colorbar=dict(title='Giá trị (tỷ VND)')
                ))
                fig_dcf.update_layout(
                    title=f'Giá trị nội tại (tỷ VND) · FCFF base = {dcf_result["fcff_base"]:.0f} tỷ',
                    xaxis_title='Tăng trưởng dài hạn g',
                    yaxis_title='Chi phí vốn WACC',
                    **DARK_TEMPLATE
                )
                st.plotly_chart(fig_dcf, use_container_width=True)

        st.divider()

        # ---- 5.4 WHAT-IF ROE SIMULATOR ----
        st.subheader("🎯 4. What-if ROE Simulator")
        col_wi1, col_wi2 = st.columns([1, 2])
        with col_wi1:
            roe_delta_pct = st.slider(
                "ΔROE mục tiêu (% pts)", -30, 30, 10, step=1,
                help="Dương = muốn ROE tăng thêm X%; Âm = chấp nhận ROE giảm X%"
            )
            roe_delta = roe_delta_pct / 100

        with col_wi2:
            wi_result = forecaster_obj.what_if_roe(target_roe_delta=roe_delta)
            if wi_result:
                st.markdown(f"""
<div class="info-box">
<b>ROE hiện tại ({wi_result['latest_year']}):</b> {wi_result['roe_current_pct']:.2f}% →
<b>ROE mục tiêu:</b> {wi_result['roe_target_pct']:.2f}% (Δ = {wi_result['delta_pct']:+.1f}%pts)
</div>""", unsafe_allow_html=True)

                wc1, wc2, wc3 = st.columns(3)
                def _fmt_val(val, unit='', precision=2):
                    if val is None:
                        return 'N/A (mẫu số ≈ 0)'
                    return f'{val:.{precision}f}{unit}'

                with wc1:
                    need_ros = wi_result['scenario_ros'].get('need_ros_pct')
                    st.metric("Kịch bản 1: Cải thiện ROS",
                              _fmt_val(need_ros, '%'),
                              delta=f"{(need_ros - wi_result['current_ros']):.1f}%pts" if need_ros else None)
                    st.caption(f"Giữ AT={wi_result['current_at']:.2f}x, Lev={wi_result['current_lev']:.2f}x")

                with wc2:
                    need_at = wi_result['scenario_at'].get('need_at')
                    st.metric("Kịch bản 2: Cải thiện AT",
                              _fmt_val(need_at, 'x', 3),
                              delta=f"{(need_at - wi_result['current_at']):.3f}x" if need_at else None)
                    st.caption(f"Giữ ROS={wi_result['current_ros']:.2f}%, Lev={wi_result['current_lev']:.2f}x")

                with wc3:
                    need_lev = wi_result['scenario_lev'].get('need_lev')
                    st.metric("Kịch bản 3: Điều chỉnh Lev",
                              _fmt_val(need_lev, 'x', 2),
                              delta=f"{(need_lev - wi_result['current_lev']):.2f}x" if need_lev else None)
                    st.caption(f"Giữ ROS={wi_result['current_ros']:.2f}%, AT={wi_result['current_at']:.2f}x")
            else:
                st.warning("Không đủ dữ liệu DuPont để mô phỏng What-if ROE.")

        st.divider()

        # ---- 5.5 CROSS-CORRELATION LEAD-LAG ----
        st.subheader("🔗 5. Lead-Lag Heatmap (Tương quan chéo)")
        ccf_result = ml_results.get('CCF_MATRIX')
        if ccf_result is not None and not ccf_result.empty:
            fig_ccf = go.Figure(go.Heatmap(
                z=ccf_result.values.astype(float),
                x=ccf_result.columns.tolist(),
                y=ccf_result.index.tolist(),
                colorscale='RdBu',
                zmid=0,
                text=ccf_result.values.round(2),
                texttemplate='%{text:.2f}',
                showscale=True,
                colorbar=dict(title='r (Pearson)')
            ))
            fig_ccf.update_layout(
                title='Tương quan giữa Đặc trưng & ROA tại các độ trễ (Lag)',
                xaxis_title='Độ trễ (Lag âm = biến dẫn trước target)',
                **DARK_TEMPLATE, height=350
            )
            st.plotly_chart(fig_ccf, use_container_width=True)
            st.markdown(
                '<div class="info-box"><b>Đọc kết quả:</b> Ô màu xanh đậm = tương quan thuận mạnh. '
                'Lag âm (cột bên trái) = biến dẫn trước ROA → đây là leading indicators. '
                'Lag 0 = đồng thời. Lag dương = biến phản ứng chậm hơn.</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("Không đủ dữ liệu để tính Cross-Correlation.")

        st.divider()

        # ---- 5.6 FACTOR IMPORTANCE ----
        st.subheader("⚖️ 6. Trọng số Nhân tố (PLSR VIP & ElasticNet)")
        col_fi1, col_fi2 = st.columns(2)

        with col_fi1:
            vip_result = ml_results.get('VIP_SCORES')
            if vip_result is not None and not vip_result.empty:
                colors_vip = [COLORS['green'] if v > 1 else '#555' for v in vip_result['VIP Score']]
                fig_vip = go.Figure(go.Bar(
                    x=vip_result['VIP Score'],
                    y=vip_result['Nhân tố'],
                    orientation='h',
                    marker_color=colors_vip,
                    text=[f'{v:.3f}' for v in vip_result['VIP Score']],
                    textposition='outside'
                ))
                fig_vip.add_vline(x=1.0, line_dash='dash', line_color=COLORS['red'],
                                   annotation_text='VIP=1 (ngưỡng quan trọng)', annotation_position='top right')
                fig_vip.update_layout(title='PLSR VIP Score (VIP > 1 = Quan trọng)',
                                      **DARK_TEMPLATE, xaxis_title='VIP Score', height=350)
                col_fi1.plotly_chart(fig_vip, use_container_width=True)
            else:
                col_fi1.info("Không đủ dữ liệu VIP.")

        with col_fi2:
            en_result = ml_results.get('ELASTICNET')
            if en_result is not None:
                coef_df = en_result['coef_df']
                coef_colors = [COLORS['green'] if d == '+' else (COLORS['red'] if d == '-' else '#555')
                               for d in coef_df['Chiều tác động']]
                fig_en = go.Figure(go.Bar(
                    x=coef_df['Hệ số ElasticNet'],
                    y=coef_df['Nhân tố'],
                    orientation='h',
                    marker_color=coef_colors,
                    text=[f"{r['Chiều tác động']}{r['Hệ số ElasticNet']:.4f}" for _, r in coef_df.iterrows()],
                    textposition='outside'
                ))
                fig_en.add_vline(x=0, line_dash='dash', line_color='white')
                fig_en.update_layout(
                    title=f'Hệ số ElasticNet (α={en_result["alpha"]:.4f}, L1={en_result["l1_ratio"]:.2f})',
                    **DARK_TEMPLATE, xaxis_title='Coefficient', height=350
                )
                col_fi2.plotly_chart(fig_en, use_container_width=True)
            else:
                col_fi2.info("Không đủ dữ liệu ElasticNet.")

        st.divider()

        # ---- 5.7 SENSITIVITY LINE ----
        st.subheader("📉 7. Sensitivity Line — Mô phỏng Tác động Cấu trúc")
        delta_pct_sel = st.select_slider(
            "Mức thay đổi giả định của nhân tố (%)",
            options=[5, 10, 15, 20, 25, 30], value=20,
            key='sens_delta'
        ) / 100

        sens_result = ml_obj.sensitivity_line(delta_pct=delta_pct_sel)
        if sens_result:
            sens_df = sens_result['df']
            fig_sens = go.Figure()
            col_map = {
                'Hiện tại': (COLORS['cyan'], 'solid', 3),
                f'Tích cực (+{int(delta_pct_sel*100)}%)': (COLORS['green'], 'dot', 2),
                f'Tiêu cực (-{int(delta_pct_sel*100)}%)': (COLORS['red'], 'dot', 2),
            }
            for col_name, (color, dash, width) in col_map.items():
                if col_name in sens_df.columns:
                    fig_sens.add_trace(go.Scatter(
                        x=sens_df['Năm'], y=sens_df[col_name],
                        name=col_name, mode='lines+markers',
                        line=dict(color=color, dash=dash, width=width),
                        marker=dict(size=8)
                    ))
            important = sens_result.get('important_features', [])
            fig_sens.update_layout(
                title=f'Sensitivity Line (±{int(delta_pct_sel*100)}%) · Nhân tố VIP cao: {", ".join(important[:3])}',
                yaxis_title='ROA (%)',
                **DARK_TEMPLATE,
                legend=dict(orientation='h', y=-0.15)
            )
            st.plotly_chart(fig_sens, use_container_width=True)
            st.markdown(
                f'<div class="info-box"><b>Nhân tố VIP > 1 được dùng:</b> {", ".join(important)} — '
                'Giả định tất cả nhân tố thay đổi đồng thời với cùng tỷ lệ. '
                'Kết quả là ước lượng cấu trúc, không phải dự báo điểm.</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("Không đủ dữ liệu để tính Sensitivity Line.")


if __name__ == "__main__":
    main()

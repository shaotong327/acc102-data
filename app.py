"""
Stock Risk-Return Analysis Tool
ACC102 Mini Assignment — Track 4
Data: WRDS CRSP Daily Stock File (loaded from pre-processed CSV)

CLOUD-HARDENED VERSION — extra logging and progressive loading
to help diagnose deployment issues on Streamlit Community Cloud.
"""

import sys
import os
import time
import streamlit as st


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG (must be the very first Streamlit call)
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Stock Risk Analyser",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ═══════════════════════════════════════════════════════════════════════════════
# IMPORT GUARD — show clear errors instead of crashing
# ═══════════════════════════════════════════════════════════════════════════════
import_status = st.empty()
import_status.info("🔄 Loading dependencies...")

try:
    import pandas as pd
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    import_status.empty()
except ModuleNotFoundError as e:
    import_status.empty()
    missing = str(e).split("'")[1] if "'" in str(e) else str(e)
    st.error(
        f"❌ **Missing dependency: `{missing}`**\n\n"
        "**For Streamlit Cloud:** Make sure your repo root contains `requirements.txt` with:\n"
        "```\n"
        "streamlit==1.39.0\n"
        "pandas==2.2.3\n"
        "numpy==2.1.3\n"
        "plotly==5.24.1\n"
        "```\n"
        "Then go to Manage app → Reboot.\n\n"
        f"Python version detected: `{sys.version.split()[0]}`"
    )
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# STYLING
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
    <style>
    .risk-high { background:#f8d7da; border-left:4px solid #dc3545;
                 padding:12px 16px; border-radius:6px; margin:8px 0; }
    .risk-mid  { background:#fff3cd; border-left:4px solid #ffc107;
                 padding:12px 16px; border-radius:6px; margin:8px 0; }
    .risk-ok   { background:#d4edda; border-left:4px solid #28a745;
                 padding:12px 16px; border-radius:6px; margin:8px 0; }
    </style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING — robust version with diagnostic info
# ═══════════════════════════════════════════════════════════════════════════════
def find_csv(filename):
    """Look for the CSV in several plausible locations."""
    candidates = [
        filename,                                # current dir
        os.path.join(os.path.dirname(__file__), filename),  # alongside app.py
        os.path.join('data', filename),          # data/ subdir
        os.path.join('..', filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


@st.cache_data(show_spinner="Loading WRDS data from CSV...")
def load_data():
    """Load CSV files. Cached so re-runs don't re-read disk."""
    p_path = find_csv('prices_wide.csv')
    r_path = find_csv('returns_wide.csv')

    if p_path is None or r_path is None:
        return None, None, "missing"

    try:
        prices  = pd.read_csv(p_path,  index_col='date', parse_dates=['date'])
        returns = pd.read_csv(r_path, index_col='date', parse_dates=['date'])
        return prices, returns, "ok"
    except Exception as e:
        return None, None, f"error: {e}"


prices_full, returns_full, status = load_data()

if status == "missing":
    st.error("⚠️ **Data files not found.**\n\n"
             "Expected `prices_wide.csv` and `returns_wide.csv` in the repo root, but neither was found.\n\n"
             "**Files currently in working directory:**")
    try:
        files_here = sorted(os.listdir('.'))
        st.code("\n".join(files_here) if files_here else "(empty)")
    except Exception as e:
        st.code(f"Could not list directory: {e}")
    st.markdown(
        "**To fix:**\n"
        "1. Run `stock_risk_analysis_fixed.ipynb` to generate the CSV files\n"
        "2. Push them to your GitHub repo root\n"
        "3. Click 'Manage app' → 'Reboot' on Streamlit Cloud"
    )
    st.stop()
elif status.startswith("error"):
    st.error(f"⚠️ Could not read CSV files: {status}")
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
def compute_metrics(returns_df: pd.DataFrame, rf_annual: float) -> pd.DataFrame:
    td = 252
    rf_daily = rf_annual / td
    stats = pd.DataFrame(index=returns_df.columns)
    stats['Ann. Return (%)']     = (returns_df.mean() * td * 100).round(2)
    stats['Ann. Volatility (%)'] = (returns_df.std() * np.sqrt(td) * 100).round(2)
    excess = returns_df.mean() - rf_daily
    stats['Sharpe Ratio']        = (excess / returns_df.std() * np.sqrt(td)).round(2)

    def max_dd(s):
        cum = (1 + s).cumprod()
        dd  = (cum - cum.cummax()) / cum.cummax()
        return round(dd.min() * 100, 2)

    stats['Max Drawdown (%)'] = returns_df.apply(max_dd)
    stats['Total Return (%)'] = ((returns_df + 1).prod() - 1).mul(100).round(2)
    return stats.sort_values('Sharpe Ratio', ascending=False)


def risk_classify(vol: float, sharpe: float, dd: float) -> tuple:
    if vol > 45 or dd < -60:
        return ("🔴 High Risk", "risk-high",
                "Extreme volatility or severe drawdown. Suitable only for "
                "experienced investors with strong risk tolerance.")
    if vol > 28 or sharpe < 0:
        return ("🟡 Moderate-High Risk", "risk-mid",
                "Meaningful volatility or weak risk-adjusted return. "
                "Consider position sizing and diversification.")
    if sharpe >= 1.0:
        return ("🟢 Strong Risk-Adjusted Return", "risk-ok",
                "Historical Sharpe ratio is strong. Past performance does "
                "not guarantee future results.")
    return ("🟢 Moderate Risk", "risk-ok",
            "Typical risk profile for large-cap equities. Maintain "
            "diversification across sectors.")


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
st.sidebar.header("🔧 Controls")

all_tickers = sorted(prices_full.columns.tolist())
default_sel = [t for t in all_tickers if t != 'SPY'][:5]

selected = st.sidebar.multiselect(
    "Select stocks to analyse",
    options=all_tickers,
    default=default_sel,
    help="Pick 1–10 tickers for comparison."
)

benchmark_options = [t for t in all_tickers if t not in selected] or all_tickers
benchmark = st.sidebar.selectbox(
    "Benchmark",
    options=benchmark_options,
    index=benchmark_options.index('SPY') if 'SPY' in benchmark_options else 0
)

min_d, max_d = prices_full.index.min().date(), prices_full.index.max().date()
date_range = st.sidebar.date_input(
    "Date range", value=(min_d, max_d),
    min_value=min_d, max_value=max_d
)
if len(date_range) != 2:
    st.sidebar.warning("Pick a start and end date.")
    st.stop()
start_date, end_date = date_range

risk_free = st.sidebar.slider(
    "Risk-free rate (annual %)", 0.0, 8.0, 4.5, 0.1
) / 100

# Sidebar diagnostics
with st.sidebar.expander("🩺 Diagnostics", expanded=False):
    st.write(f"Streamlit: `{st.__version__}`")
    st.write(f"Pandas: `{pd.__version__}`")
    st.write(f"Plotly: `{px.__version__ if hasattr(px, '__version__') else 'unknown'}`")
    st.write(f"Tickers loaded: `{len(all_tickers)}`")
    st.write(f"Trading days: `{len(prices_full)}`")
    st.write(f"Date range: `{min_d}` → `{max_d}`")

if not selected:
    st.warning("👈 Please select at least one stock.")
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# FILTER DATA
# ═══════════════════════════════════════════════════════════════════════════════
tickers_use = selected + ([benchmark] if benchmark not in selected else [])
prices  = prices_full.loc[str(start_date):str(end_date), tickers_use]
returns = returns_full.loc[str(start_date):str(end_date), tickers_use]


# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.title("📈 Stock Risk-Return Analyser")
st.caption("Interactive decision-support tool for investment beginners  ·  "
           "Data: WRDS CRSP Daily Stock File")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Stocks", len(selected))
c2.metric("Benchmark", benchmark)
c3.metric("Trading days", len(returns))
c4.metric("Period", f"{(end_date - start_date).days} days")
st.divider()


# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Performance",
    "⚠️ Risk",
    "🔗 Correlation",
    "🎯 vs Benchmark",
    "🔬 Deep-Dive (3 stocks)",
    "💾 Export"
])


# ─── TAB 1: PERFORMANCE ────────────────────────────────────────────────────────
with tab1:
    st.subheader("Cumulative Returns")
    st.caption("How $100 invested at the start date would have grown. "
               "Toggle log scale when one stock dwarfs the others.")

    log_scale = st.checkbox("Use log scale", value=False, key="perf_log")

    cum = (1 + returns).cumprod() * 100
    fig = go.Figure()
    for col in cum.columns:
        is_bench = (col == benchmark)
        fig.add_trace(go.Scatter(
            x=cum.index, y=cum[col],
            name=col + (" (benchmark)" if is_bench else ""),
            line=dict(width=2.5 if is_bench else 1.5,
                      dash="dash" if is_bench else "solid")
        ))
    fig.add_hline(y=100, line_dash="dot", line_color="black", opacity=0.3)
    fig.update_layout(
        height=460,
        xaxis_title="Date",
        yaxis_title="Cumulative Value (start = 100)",
        yaxis_type="log" if log_scale else "linear",
        hovermode="x unified",
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right")
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Performance Summary")
    summary = compute_metrics(returns[selected], risk_free)
    st.dataframe(summary, use_container_width=True)


# ─── TAB 2: RISK ──────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Risk-Return Scatter")
    st.caption("Upper-left is ideal: high return, low risk. Colour = Sharpe Ratio.")

    metrics = compute_metrics(returns[selected], risk_free)
    fig2 = px.scatter(
        metrics.reset_index().rename(columns={'index': 'ticker'}),
        x="Ann. Volatility (%)", y="Ann. Return (%)",
        text="ticker", color="Sharpe Ratio",
        color_continuous_scale="RdYlGn", size_max=30
    )
    fig2.update_traces(textposition="top center", marker=dict(size=16))
    fig2.add_hline(y=risk_free * 100, line_dash="dot", line_color="red",
                   annotation_text=f"Risk-free rate ({risk_free*100:.1f}%)")
    fig2.add_hline(y=0, line_dash="dash", line_color="grey")
    fig2.update_layout(height=500)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Drawdown Over Time")
    st.caption("How far each stock fell from its previous peak. "
               "Deep drawdowns test investor patience.")

    cum_r = (1 + returns[selected]).cumprod()
    dd    = (cum_r - cum_r.cummax()) / cum_r.cummax() * 100
    fig3 = go.Figure()
    for col in dd.columns:
        fig3.add_trace(go.Scatter(
            x=dd.index, y=dd[col], name=col,
            fill="tozeroy", mode="lines", line=dict(width=1)
        ))
    fig3.add_hline(y=-20, line_dash="dash", line_color="orange",
                   annotation_text="−20% bear market")
    fig3.update_layout(height=400, yaxis_title="Drawdown (%)",
                       xaxis_title="Date", hovermode="x unified")
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("🚨 Risk Assessment Per Stock")
    for t in selected:
        m = metrics.loc[t]
        label, css, msg = risk_classify(
            m["Ann. Volatility (%)"], m["Sharpe Ratio"], m["Max Drawdown (%)"]
        )
        st.markdown(
            f'<div class="{css}"><b>{t} — {label}</b><br>{msg}<br>'
            f'<small>Vol: {m["Ann. Volatility (%)"]}%  ·  '
            f'Sharpe: {m["Sharpe Ratio"]}  ·  '
            f'Max DD: {m["Max Drawdown (%)"]}%</small></div>',
            unsafe_allow_html=True
        )


# ─── TAB 3: CORRELATION ───────────────────────────────────────────────────────
with tab3:
    st.subheader("Correlation Matrix")
    st.caption("Values near 1.0 = stocks move together. Lower = better diversification.")

    corr = returns[selected].corr()
    fig4 = px.imshow(corr, text_auto=".2f",
                     color_continuous_scale="RdYlGn",
                     zmin=-1, zmax=1, aspect="auto")
    fig4.update_layout(height=max(400, 55 * len(selected) + 120))
    st.plotly_chart(fig4, use_container_width=True)

    if len(selected) >= 2:
        off = corr.where(~np.eye(len(corr), dtype=bool)).stack()
        avg = off.mean()
        if avg > 0.7:
            st.warning(f"⚠️ Average correlation: **{avg:.2f}** — highly correlated "
                       "basket. Consider stocks from different sectors.")
        elif avg > 0.4:
            st.info(f"ℹ️ Average correlation: **{avg:.2f}** — moderate diversification.")
        else:
            st.success(f"✅ Average correlation: **{avg:.2f}** — good diversification.")

        ca, cb = st.columns(2)
        ca.metric(
            f"Least correlated: {off.idxmin()[0]} — {off.idxmin()[1]}",
            f"{off.min():.3f}"
        )
        cb.metric(
            f"Most correlated: {off.idxmax()[0]} — {off.idxmax()[1]}",
            f"{off.max():.3f}"
        )


# ─── TAB 4: VS BENCHMARK ──────────────────────────────────────────────────────
with tab4:
    st.subheader(f"Performance vs. {benchmark}")
    bench = returns[benchmark]

    rows = []
    for t in selected:
        r     = returns[t]
        beta  = np.cov(r, bench)[0, 1] / np.var(bench)
        alpha = (r.mean() - beta * bench.mean()) * 252 * 100
        tr    = ((1 + r).prod() - 1) * 100
        br    = ((1 + bench).prod() - 1) * 100
        rows.append({
            "Stock": t,
            "Total Return (%)": round(tr, 2),
            f"{benchmark} Return (%)": round(br, 2),
            "Excess Return (%)": round(tr - br, 2),
            "Beta": round(beta, 2),
            "Alpha (%, ann.)": round(alpha, 2)
        })

    comp = pd.DataFrame(rows).sort_values("Excess Return (%)", ascending=False)
    st.dataframe(comp, hide_index=True, use_container_width=True)

    with st.expander("📖 What do these numbers mean?"):
        st.markdown("""
        - **Excess Return** — total return minus benchmark return. Positive = outperformed.
        - **Beta** — how much the stock moves when the benchmark moves 1%.
          Beta > 1 = more volatile than market.
        - **Alpha** — return beyond what beta predicts. Positive = genuine outperformance.
        """)

    st.subheader("Relative Performance")
    st.caption(f"Line above 100 = outperforming {benchmark}. Below 100 = underperforming.")
    rel = (1 + returns[selected]).cumprod().div(
        (1 + bench).cumprod(), axis=0) * 100
    fig5 = go.Figure()
    for col in rel.columns:
        fig5.add_trace(go.Scatter(x=rel.index, y=rel[col], name=col, mode="lines"))
    fig5.add_hline(y=100, line_dash="dash", line_color="black",
                   annotation_text=f"= {benchmark}")
    fig5.update_layout(height=420,
                       yaxis_title=f"Value ÷ {benchmark} Value (×100)",
                       xaxis_title="Date", hovermode="x unified")
    st.plotly_chart(fig5, use_container_width=True)


# ─── TAB 5: DEEP-DIVE ─────────────────────────────────────────────────────────
with tab5:
    st.subheader("Three-Stock Deep-Dive")
    st.caption("Focus on three stocks with contrasting profiles. "
               "Same analysis as Chart 6 in the notebook.")

    all_for_dive = sorted(all_tickers)
    default_dive = [t for t in ['NVDA', 'TSLA', 'XOM'] if t in all_for_dive]
    while len(default_dive) < 3:
        extra = [t for t in all_for_dive if t not in default_dive][0]
        default_dive.append(extra)

    c1, c2, c3 = st.columns(3)
    with c1:
        s1 = st.selectbox("Stock 1", all_for_dive,
                          index=all_for_dive.index(default_dive[0]), key="dd1")
    with c2:
        s2 = st.selectbox("Stock 2", all_for_dive,
                          index=all_for_dive.index(default_dive[1]), key="dd2")
    with c3:
        s3 = st.selectbox("Stock 3", all_for_dive,
                          index=all_for_dive.index(default_dive[2]), key="dd3")

    focus = list(dict.fromkeys([s1, s2, s3]))
    if len(focus) < 2:
        st.warning("Please pick at least two different stocks.")
    else:
        r_focus = returns_full.loc[str(start_date):str(end_date), focus]

        dd_log = st.checkbox("Log scale (useful when one stock dominates)",
                             value=True, key="dd_log")

        cum_f = (1 + r_focus).cumprod() * 100
        figA = go.Figure()
        for col in focus:
            figA.add_trace(go.Scatter(x=cum_f.index, y=cum_f[col],
                                       name=col, line=dict(width=2.5)))
        figA.add_hline(y=100, line_dash="dot", line_color="black", opacity=0.3)
        figA.update_layout(
            height=380,
            title="(a) Growth of $100",
            yaxis_title="Value ($)",
            yaxis_type="log" if dd_log else "linear",
            hovermode="x unified"
        )
        st.plotly_chart(figA, use_container_width=True)

        cum_abs = (1 + r_focus).cumprod()
        dd_focus = (cum_abs - cum_abs.cummax()) / cum_abs.cummax() * 100
        figB = go.Figure()
        for col in focus:
            figB.add_trace(go.Scatter(x=dd_focus.index, y=dd_focus[col],
                                       name=col, fill="tozeroy",
                                       mode="lines", line=dict(width=1)))
        figB.add_hline(y=-20, line_dash="dash", line_color="orange",
                       annotation_text="−20% bear market")
        figB.update_layout(
            height=350,
            title="(b) Drawdown Over Time",
            yaxis_title="Drawdown (%)",
            hovermode="x unified"
        )
        st.plotly_chart(figB, use_container_width=True)

        roll_vol = r_focus.rolling(60).std() * np.sqrt(252) * 100
        figC = go.Figure()
        for col in focus:
            figC.add_trace(go.Scatter(x=roll_vol.index, y=roll_vol[col],
                                       name=col, line=dict(width=2)))
        figC.update_layout(
            height=350,
            title="(c) Rolling 60-Day Annualised Volatility",
            yaxis_title="Volatility (%, ann.)",
            hovermode="x unified"
        )
        st.plotly_chart(figC, use_container_width=True)

        st.markdown("**(d) Metric Comparison**")
        metrics_focus = compute_metrics(r_focus, risk_free)
        st.dataframe(metrics_focus, use_container_width=True)


# ─── TAB 6: EXPORT ────────────────────────────────────────────────────────────
with tab6:
    st.subheader("Download Data")
    st.caption("Export your filtered data as CSV.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Price history**")
        st.download_button(
            "⬇️ Download prices CSV",
            prices.to_csv().encode(),
            f"prices_{start_date}_{end_date}.csv",
            "text/csv", use_container_width=True
        )
    with col2:
        st.markdown("**Daily returns**")
        st.download_button(
            "⬇️ Download returns CSV",
            returns.to_csv().encode(),
            f"returns_{start_date}_{end_date}.csv",
            "text/csv", use_container_width=True
        )
    with col3:
        st.markdown("**Summary metrics**")
        st.download_button(
            "⬇️ Download metrics CSV",
            compute_metrics(returns[selected], risk_free).to_csv().encode(),
            f"metrics_{start_date}_{end_date}.csv",
            "text/csv", use_container_width=True
        )

    st.divider()
    st.markdown("**Preview: latest prices**")
    st.dataframe(prices.tail(10).round(2), use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85rem;padding:0.5rem;'>"
    "ACC102 Mini Assignment — Track 4  ·  Xi'an Jiaotong-Liverpool University  ·  "
    "Data: WRDS CRSP Daily Stock File<br>"
    "<i>For educational purposes only. Not investment advice. "
    "Past performance does not guarantee future results.</i></div>",
    unsafe_allow_html=True
)

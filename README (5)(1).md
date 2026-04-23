# 📈 Stock Risk-Return Analysis Tool

> **ACC102 Mini Assignment — Track 4  ·  Xi'an Jiaotong-Liverpool University  ·  2024-25 Semester 2**

An interactive decision-support tool that helps investment beginners compare the return, volatility, drawdown, and correlation of US stocks using WRDS CRSP data.

🎥 **[Demo Video](YOUR_VIDEO_LINK_HERE)**
🌐 **[Live App](YOUR_STREAMLIT_LINK_HERE)**

---

## 1 · Problem & User

**Analytical Question.** When a beginner investor looks at two stocks on a chart, both showing an upward trend, how should they tell which one was actually the better investment? "Best" is never just about the final price — it's about how much risk was taken, how deep the drawdowns were, and how the stock moved alongside other stocks in the portfolio.

**Target User.** Finance students and individual investors who understand basic concepts but want a data-driven way to compare stocks on risk dimensions, not just price history.

---

## 2 · Data

| Item | Detail |
|---|---|
| **Source** | WRDS CRSP Daily Stock File (`crsp.dsf`) + `crsp.msenames` |
| **Method** | f-string SQL + LEFT JOIN on `permno` (ACC102 Week 6 technique) |
| **Stocks** | AAPL, MSFT, GOOGL, AMZN, META, TSLA, NVDA, JPM, XOM, JNJ, SPY |
| **Period** | 2020-01-01 → 2024-12-31 (≈1,258 trading days per ticker) |
| **Frequency** | Daily |
| **Access date** | April 2026 |

**The FB → META rebrand problem.** CRSP uses `permno` (permanent numeric ID) as its primary key, not ticker strings. Facebook rebranded to Meta on 28 October 2021, so its ticker switched from `FB` to `META`. A naïve query `WHERE ticker = 'META'` only returns data from late 2021 onwards. The notebook solves this by hard-coding Facebook/Meta's permno (`13407`) into the query and relabelling pre-rebrand rows during cleaning.

The notebook pulls data from WRDS and saves it as CSV. The Streamlit app reads those CSV files, so it can be deployed publicly without requiring WRDS credentials.

---

## 3 · Methods

### Notebook (`stock_risk_analysis_fixed.ipynb`)

1. **f-string SQL** with parameterised tickers, dates, and permnos
2. **LEFT JOIN** between `crsp.dsf` and `crsp.msenames` on `permno`
3. **Data cleaning** — rename columns, unify FB→META, fix CRSP negative-price quirk, drop missing returns
4. **Pivot to wide format** with data-coverage validation
5. `compute_metrics()` function — annualised return, volatility, Sharpe ratio, max drawdown, total return
6. **Full-basket visualisations** — 5 charts covering all 11 stocks
7. **Deep-dive function** — 2×2 comparison figure for any 3 focus stocks (NVDA/TSLA/XOM by default)

### Streamlit App (`app.py`)

**Six interactive tabs:**

| Tab | What it shows |
|---|---|
| 📊 **Performance** | Cumulative returns (with log-scale toggle) + summary metrics table |
| ⚠️ **Risk** | Risk-return scatter + drawdown over time + automated per-stock risk classification |
| 🔗 **Correlation** | Heatmap + average pairwise correlation + most/least correlated pair |
| 🎯 **vs Benchmark** | Beta/alpha/excess return vs. user-selected benchmark |
| 🔬 **Deep-Dive** | 3-stock focused comparison (4 sub-charts mirroring the notebook) |
| 💾 **Export** | CSV download for prices, returns, and metrics |

**Sidebar controls:** stock multi-select, benchmark, date range, risk-free rate slider.

---

## 4 · Key Findings

- **NVDA** topped the Sharpe ratio ranking (~1.5) — AI-driven returns large enough to justify its volatility
- **TSLA** delivered a high total return but the deepest drawdown (beyond −69%), which few investors would hold through
- **XOM** is the diversification anchor — lowest correlation with tech stocks, and the only major gainer in 2022
- **JNJ** shows a negative 5-year return despite being "defensive" — a reminder that capital-preservation stocks can underperform significantly in bull markets
- **Average pairwise correlation above 0.5** confirms that a portfolio of only US large-caps provides limited diversification — true diversification requires other asset classes

---

## 5 · How to Run

### Option A — Full pipeline (requires WRDS account)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/acc102-risk-tool.git
cd acc102-risk-tool

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate WRDS data (one-time)
jupyter notebook stock_risk_analysis_fixed.ipynb
# Run all cells — generates prices_wide.csv and returns_wide.csv

# 4. Launch the Streamlit app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

### Option B — App only (no WRDS needed)

The repository includes pre-generated CSV files, so you can skip step 3 and run `streamlit run app.py` directly. This is also what enables public deployment to Streamlit Community Cloud.

### Option C — Deploy to Streamlit Community Cloud

1. Push the repo (including the CSV files) to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io) and connect your GitHub account
3. Select the repo and `app.py` as the entry point
4. The app deploys in ~2 minutes with a public URL

---

## 6 · Repository Structure

```
acc102-risk-tool/
├── README.md                           ← this file
├── app.py                              ← Streamlit interactive tool (6 tabs)
├── stock_risk_analysis_fixed.ipynb     ← WRDS download + analysis notebook
├── requirements.txt
├── reflection_report.md                ← 500–800 word reflection
├── prices_wide.csv                     ← pre-generated from WRDS
├── returns_wide.csv                    ← pre-generated from WRDS
└── metrics_summary.csv                 ← pre-generated from WRDS
```

---

## 7 · Limitations & Next Steps

- **Snapshot data** — CSV reflects state at download time; rerun the notebook to refresh
- **Survivorship bias** — only currently listed stocks are in the basket
- **Constant risk-free rate** — real US Treasury yields moved from ~0% (2020–21) to >5% (2023–24); the slider lets users adjust but doesn't vary over time
- **No intraday data** — `crsp.dsf` contains end-of-day prices only
- **SPY as benchmark** — SPY tracks the S&P 500 closely but carries a small expense ratio

**Next steps:** rolling Sharpe ratio, Fama-French factor decomposition, Monte Carlo portfolio simulation, sector-level overlay.

---

*For educational purposes only. Not investment advice. Past performance does not guarantee future results.*

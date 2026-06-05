# 📊 Indian Mutual Fund Analyzer

An institutional-grade portfolio intelligence dashboard designed to discover, parse, and analyze over 15,000+ active Indian Mutual Funds in real-time. Built entirely with **Python**, **Streamlit**, and **Plotly**, this application merges separate datasets by establishing live streaming connections into official AMFI NAV text feeds and Yahoo Finance market telemetry.

Featuring a premium, low-light cyber-dark UI theme, it serves as an interactive spreadsheet interface that tracks performance records, automatically computes financial risk statistics, and highlights cross-portfolio equity overlap concentration metrics.

---

## ✨ Project Core Capabilities & Deliverables

The application functions as a unified analysis table. For every mutual fund selected, it constructs and displays a clean data spreadsheet directly on the user interface containing the following metrics exactly in sequence:

1. **Name of Fund**: Extracted dynamically from the live AMFI master registry list.
2. **Date of Begin (Inception)**: Automatically located using deep historical data tracking.
3. **Current NAV**: Live pricing pulled directly from database endpoints.
4. **Interval Returns & Charts**: 6-Month, 1-Year, 3-Year, 5-Year, and All-Time Compound Annual Growth Rates (CAGR) paired with interactive trend graphs.
5. **Equity Sector Allocation**: Percentage distributions mapped by active market industries.
6. **Portfolio P/E Ratio**: Asset-weighted Valuation Price-to-Earnings metric.
7. **Portfolio P/B Ratio**: Asset-weighted Valuation Price-to-Book metric.
8. **Alpha Coefficient**: Relative risk-adjusted outperformance calculated against the **Nifty 50** benchmark.
9. **Beta Coefficient**: Systematic volatility sensitivity ratio relative to the broader Indian stock market.
10. **Sharpe Ratio**: Excess reward-to-total-volatility efficiency indicator.
11. **Sortino Ratio**: Downside deviation efficiency indicator (unpenalized by upside volatility).
12. **Common Holdings**: A cross-portfolio intersection module isolating overlapping stock equities among all loaded funds.
13. **Percent of Capital in Common Holdings**: Concentration risk index calculating exactly how much total fund capital resides in overlapping assets.

---

## 📁 Repository Directory Structure

Maintain your project files within this structured workspace arrangement to ensure correct package import paths:
```text
Mutual_Fund/
├── app.py             # Application Entry Point: Main UI layouts, custom CSS styling, & KPI tables
├── analytics.py       # Core Math Modules: Statelessly computes financial risk statistics & holding intersections
├── data_fetcher.py    # Master Data Pipeline: Live AMFI web scrapers, yFinance proxies, and data caching loops
├── config.py          # Central Configuration: Color tokens, global constants, risk-free bounds & presets
└── requirements.txt   # Pinpointed Dependencies: Streamlit, Pandas, NumPy, and Plotly core packages

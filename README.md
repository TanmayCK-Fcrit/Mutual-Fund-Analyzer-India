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



⚙️ Installation & Execution ManualFollow these sequential terminal commands to construct an isolated virtual environment and launch the analyzer cleanly on your machine.Step 1: Open Your Terminal & NavigateOpen Command Prompt / PowerShell (Windows) or Terminal (macOS/Linux) and change directories into your root project folder:Bashcd path/to/your/folder/Mutual_Fund
Step 2: Initialize an Isolated Virtual WorkspaceGenerate a fresh Python virtual environment (venv) to keep package dependencies clean and separate from global installations:Bash# Windows
python -m venv venv

# macOS / Linux
python3 -m venv venv
Step 3: Activate Your WorkspaceYou must activate the virtual environment before installing packages. Once activated, your terminal command line will show a (venv) prefix.Bash# Windows (Command Prompt)
venv\Scripts\activate.bat

# Windows (PowerShell)
.\venv\Scripts\activate.ps1

# macOS / Linux
source venv/bin/activate
Step 4: Install Pinpoint Project DependenciesExecute the pip install command to configure the core libraries. Version constraints are relaxed to download pre-compiled binary versions automatically:Bashpip install -r requirements.txt
Step 5: Execute the Streamlit ApplicationLaunch your application server. The clearOnStart cache flag ensures that background data processing modules flush any old memory files instantly:Bashstreamlit run app.py --server.clearOnStart true
Your operating system will automatically open your default browser navigating to the local host address at http://localhost:8501.🕹️ Operational User GuideOnce the browser dashboard opens, you can toggle, search, and analyze data pools using the multi-channel sidebar:1. Analyzing Curated PresetsBy default, the application boots up with "Load Popular Funds" checked.Select or unselect items from the "Popular Funds" multi-select dropdown menu to quickly display, sort, and compare well-known Indian mutual funds side-by-side.2. Loading via Direct API URLIf you know a specific fund code or have an official mfapi.in URL, bypass name-matching entirely.Paste the absolute endpoint string (e.g., https://api.mfapi.in/mf/128032 for the Motilal Oswal Midcap Fund) into the "Paste mfapi.in URL" text bar.Click the "➕ Add URL Fund" button. The dashboard will scrape, parse, process, and append that explicit scheme code onto your running summary tables automatically.3. Searching via Tokenized PhrasesUse the "🔍 Search Any Fund" text block to lookup funds using simple keyword combinations.The smart search text-processor splits your phrase into separate word pieces (e.g., typing Quant Small or Nippon Small Growth) and looks for them across all 15,000+ entries, completely ignoring word sequence, case styles, or dashes.Select the closest match from the generated dropdown results and click "➕ Add Search Fund" to update your data frame.4. Interacting with Tables & HeatmapsDynamic Grid Sorting: Click any header inside the main UI spreadsheet to rank funds instantly by their current NAV, Alpha, or P/E valuation ratios.Removing Custom Selections: Review your active selections under the "Added Funds" sidebar group. Click the "✕" icon next to any fund name to remove its entry from your charts instantly.Concentration Analysis: Scroll to the bottom interface card to track the Portfolio Overlap Heatmap which flags exactly how much capital concentration is shared between your asset selections.🧮 Statistical FormulationsThe calculations powering your dashboard metrics are derived through the following stateless financial equations:1. Period Returns (CAGR)For calculation horizons greater than one year (3Y and 5Y), returns are annualized using a geometric compounding method. Periods under one year (6M, 1Y) report absolute holding returns:$$\text{CAGR} = \left( \frac{\text{NAV}_{\text{Latest}}}{\text{NAV}_{\text{Past}}} \right)^{\frac{365}{\text{Days Trailed}}} - 1$$2. Systematic Risk: Beta ($\beta$)Beta evaluates a fund's volatility sensitivity compared against the broader market index benchmark (Nifty 50), calculated over a rolling 3-year daily window:$$\beta = \frac{\text{Covariance}(R_{\text{fund}}, R_{\text{benchmark}})}{\text{Variance}(R_{\text{benchmark}})}$$3. Risk-Adjusted Return: Alpha ($\alpha$)Alpha represents the idiosyncratic outperformance a fund manager produces above its systematic benchmark exposure:$$\alpha = R_{\text{fund}} - \left[ R_f + \beta \times (R_{\text{benchmark}} - R_f) \right]$$(Where $R_f$ represents the default Indian Risk-Free baseline rate set at $6.5\%$ via the 91-Day Treasury Bill index).4. Asset Efficiency RatiosSharpe Ratio: Measures the portfolio's excess reward margin generated per unit of total standard deviation risk ($\sigma_{\text{fund}}$):$$\text{Sharpe} = \frac{R_{\text{fund}} - R_f}{\sigma_{\text{fund}}}$$Sortino Ratio: Refines asset risk profiles by isolating standard deviation into downside semi-deviation ($\sigma_{\text{down}}$), ensuring managers are not penalized for large upward gains:$$\text{Sortino} = \frac{R_{\text{fund}} - R_f}{\sigma_{\text{down}}}$$📝 Compliance & System DisclaimerThis software package is intended exclusively for educational demonstrations and pipeline architecture testing. All data models, asset distributions, and risk parameters generated by this application are processed from public feeds or synthetic category baselines. Nothing displayed within this application constitutes formalized investment advice, financial solicitation, or fiduciary execution recommendations.

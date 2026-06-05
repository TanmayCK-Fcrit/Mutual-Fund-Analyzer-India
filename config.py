"""
config.py
---------
Central configuration module for the Indian Mutual Fund Analyzer.
All constants, endpoints, and environment-driven settings live here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# App Identity
# ─────────────────────────────────────────────
APP_TITLE = "Indian Mutual Fund Analyzer"
APP_SUBTITLE = "Institutional-Grade Portfolio Intelligence"
APP_VERSION = "1.0.0"
APP_ICON = "📊"

# ─────────────────────────────────────────────
# Data Sources
# ─────────────────────────────────────────────
AMFI_NAV_URL = "https://www.amfiindia.com/spages/NAVAll.txt"
AMFI_SCHEME_URL = "https://api.mfapi.in/mf"
MF_API_BASE = "https://api.mfapi.in/mf"

# ─────────────────────────────────────────────
# Benchmark Configuration
# ─────────────────────────────────────────────
BENCHMARK_TICKER = "^NSEI"          # Nifty 50 Yahoo Finance ticker
BENCHMARK_NAME = "Nifty 50"
RISK_FREE_RATE = 0.065              # 6.5% annualised (approx. Indian 91-day T-bill)

# ─────────────────────────────────────────────
# Return Calculation Windows
# ─────────────────────────────────────────────
RETURN_WINDOWS = {
    "6M":  182,
    "1Y":  365,
    "3Y":  1095,
    "5Y":  1825,
}

# ─────────────────────────────────────────────
# Cache / Performance
# ─────────────────────────────────────────────
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 3600))   # 1 hour default
MAX_FUNDS_COMPARE = int(os.getenv("MAX_FUNDS_COMPARE", 10))

# ─────────────────────────────────────────────
# HTTP
# ─────────────────────────────────────────────
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 15))
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

# ─────────────────────────────────────────────
# UI / Charting
# ─────────────────────────────────────────────
CHART_HEIGHT = 420
PLOTLY_TEMPLATE = "plotly_dark"

BRAND_COLORS = [
    "#00D4FF",  # electric cyan
    "#FF6B35",  # vivid orange
    "#7B61FF",  # electric violet
    "#00FF9C",  # neon mint
    "#FFD600",  # golden yellow
    "#FF3CAC",  # hot pink
    "#2AFADF",  # turquoise
    "#FF9A3C",  # amber
    "#A8FF3E",  # lime
    "#FF4D6D",  # coral
]

# ─────────────────────────────────────────────
# Popular / Preset Fund Scheme Codes (AMFI)
# ─────────────────────────────────────────────
POPULAR_FUNDS = {
    "Mirae Asset Large Cap Fund - Direct Plan": "118989",
    "Axis Bluechip Fund - Direct Plan": "120503",
    "HDFC Mid-Cap Opportunities Fund - Direct Plan": "118560",
    "SBI Small Cap Fund - Direct Plan": "125497",
    "Parag Parikh Flexi Cap Fund - Direct Plan": "122639",
    "Kotak Emerging Equity Fund - Direct Plan": "120173",
    "UTI Nifty 50 Index Fund - Direct Plan": "120716",
    "ICICI Prudential Technology Fund - Direct Plan": "120586",
    "Nippon India Small Cap Fund - Direct Plan": "118778",
    "HDFC Flexi Cap Fund - Direct Plan": "100033",
}

# ─────────────────────────────────────────────
# Sector colour map (for pie / bar charts)
# ─────────────────────────────────────────────
SECTOR_COLORS = {
    "Financial Services": "#00D4FF",
    "Information Technology": "#7B61FF",
    "Consumer Goods": "#FF6B35",
    "Healthcare": "#00FF9C",
    "Energy": "#FFD600",
    "Automobile": "#FF3CAC",
    "Metals & Mining": "#A8FF3E",
    "Construction": "#FF9A3C",
    "Telecom": "#2AFADF",
    "FMCG": "#FF4D6D",
    "Cement": "#B8BCC8",
    "Chemicals": "#6EE7B7",
    "Others": "#64748B",
}

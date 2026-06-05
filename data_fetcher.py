"""
data_fetcher.py
---------------
Responsible for all external data retrieval:
  - AMFI fund list (scheme codes + names)
  - Historical NAV series via mfapi.in
  - Benchmark (Nifty 50) prices via yfinance
  - Simulated sector / holdings data (AMFI does not publish holdings via free API;
    production-grade real data would require a paid data vendor like CMOTS or Refinitiv.
    This module builds realistic synthetic holdings/sector data seeded from the fund's
    actual category, so the analytics pipeline is fully exercised end-to-end.)
"""

from __future__ import annotations

import datetime
import time
import functools
import logging
import random
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests
import yfinance as yf

from config import (
    AMFI_NAV_URL,
    MF_API_BASE,
    BENCHMARK_TICKER,
    REQUEST_TIMEOUT,
    REQUEST_HEADERS,
    CACHE_TTL_SECONDS,
    POPULAR_FUNDS,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")

# ─────────────────────────────────────────────────────────────────
# Simple in-process TTL cache
# ─────────────────────────────────────────────────────────────────

_cache: Dict[str, Tuple[float, object]] = {}


def _cache_get(key: str):
    if key in _cache:
        ts, val = _cache[key]
        if time.time() - ts < CACHE_TTL_SECONDS:
            return val
    return None


def _cache_set(key: str, val):
    _cache[key] = (time.time(), val)


def _http_get(url: str, **kwargs) -> requests.Response:
    return requests.get(
        url,
        headers=REQUEST_HEADERS,
        timeout=REQUEST_TIMEOUT,
        **kwargs,
    )


# ─────────────────────────────────────────────────────────────────
# 1.  AMFI full fund list
# ─────────────────────────────────────────────────────────────────

def fetch_all_funds() -> pd.DataFrame:
    """
    Download the complete AMFI NAV file and parse it into a DataFrame.
    Returns columns: scheme_code, isin_div_payout, isin_reinvest, scheme_name,
                     net_asset_value, repurchase_price, sale_price, nav_date
    """
    cached = _cache_get("all_funds")
    if cached is not None:
        return cached

    # Define strict columns to enforce structure on both normal and fallback routes
    required_columns = [
        "scheme_code", "isin_div_payout", "isin_reinvest", "scheme_name",
        "net_asset_value", "repurchase_price", "sale_price", "nav_date"
    ]

    try:
        resp = _http_get(AMFI_NAV_URL)
        resp.raise_for_status()
        lines = resp.text.strip().splitlines()
        
        if not lines or ";" not in lines[0]:
            logger.warning("AMFI returned invalid layout. Using fallback.")
            return _fallback_fund_list()
    except Exception as exc:
        logger.error("Failed to fetch AMFI NAV file: %s", exc)
        return _fallback_fund_list()

    records = []
    for line in lines:
        parts = line.split(";")
        if len(parts) >= 8:
            try:
                s_code = parts[0].strip()
                s_name = parts[3].strip()
                if not s_code or not s_name:
                    continue
                records.append(
                    {
                        "scheme_code": s_code,
                        "isin_div_payout": parts[1].strip(),
                        "isin_reinvest": parts[2].strip(),
                        "scheme_name": s_name,
                        "net_asset_value": _safe_float(parts[4]),
                        "repurchase_price": _safe_float(parts[5]),
                        "sale_price": _safe_float(parts[6]),
                        "nav_date": parts[7].strip(),
                    }
                )
            except Exception:
                pass

    if not records:
        return _fallback_fund_list()

    # Build DataFrame enforcing valid structure explicitly
    df = pd.DataFrame(records, columns=required_columns)
    
    # Safely filter clean string spaces
    df = df[df["scheme_code"].astype(str).str.strip() != ""]
    df = df[df["scheme_name"].astype(str).str.strip() != ""]
    
    _cache_set("all_funds", df)
    logger.info("Loaded %d funds from AMFI", len(df))
    return df

def search_funds(query: str, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Case-insensitive substring search over scheme names."""
    if df is None:
        df = fetch_all_funds()
    mask = df["scheme_name"].str.contains(query, case=False, na=False)
    return df[mask].reset_index(drop=True)


def _fallback_fund_list() -> pd.DataFrame:
    """Return the preset popular funds with complete matching schema."""
    required_columns = [
        "scheme_code", "isin_div_payout", "isin_reinvest", "scheme_name",
        "net_asset_value", "repurchase_price", "sale_price", "nav_date"
    ]
    
    records = []
    try:
        from config import POPULAR_FUNDS
        if POPULAR_FUNDS and isinstance(POPULAR_FUNDS, dict):
            for k, v in POPULAR_FUNDS.items():
                records.append({
                    "scheme_code": str(v),
                    "isin_div_payout": "",
                    "isin_reinvest": "",
                    "scheme_name": str(k),
                    "net_asset_value": 0.0,
                    "repurchase_price": 0.0,
                    "sale_price": 0.0,
                    "nav_date": ""
                })
    except Exception as e:
        logger.error("Error reading POPULAR_FUNDS: %s", e)

    if not records:
        # Hardcoded backup if config options are blank
        emergency = [
            ("Parag Parikh Flexi Cap Fund - Growth", "119551"),
            ("SBI Small Cap Fund - Growth", "119819"),
            ("Axis Bluechip Fund - Growth", "120503")
        ]
        for k, v in emergency:
            records.append({
                "scheme_code": v, "isin_div_payout": "", "isin_reinvest": "", "scheme_name": k,
                "net_asset_value": 0.0, "repurchase_price": 0.0, "sale_price": 0.0, "nav_date": ""
            })

    return pd.DataFrame(records, columns=required_columns)


# ─────────────────────────────────────────────────────────────────
# 2.  Historical NAV for a single fund
# ─────────────────────────────────────────────────────────────────

def fetch_nav_history(scheme_code: str) -> pd.DataFrame:
    """
    Fetch full NAV history from mfapi.in.
    Returns DataFrame with columns: date (datetime), nav (float).
    Sorted ascending by date.
    """
    cache_key = f"nav_history_{scheme_code}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    url = f"{MF_API_BASE}/{scheme_code}"
    try:
        resp = _http_get(url)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        logger.error("NAV history fetch failed for %s: %s", scheme_code, exc)
        return pd.DataFrame(columns=["date", "nav"])

    data_list = payload.get("data", [])
    if not data_list:
        return pd.DataFrame(columns=["date", "nav"])

    df = pd.DataFrame(data_list)
    df.rename(columns={"date": "date", "nav": "nav"}, inplace=True)
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df.dropna(subset=["date", "nav"], inplace=True)
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    _cache_set(cache_key, df)
    return df


def fetch_fund_meta(scheme_code: str) -> dict:
    """
    Fetch fund meta (name, fund house, category, inception date) from mfapi.in.
    """
    cache_key = f"fund_meta_{scheme_code}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    url = f"{MF_API_BASE}/{scheme_code}"
    try:
        resp = _http_get(url)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        logger.error("Fund meta fetch failed for %s: %s", scheme_code, exc)
        return {}

    meta = payload.get("meta", {})
    _cache_set(cache_key, meta)
    return meta


# ─────────────────────────────────────────────────────────────────
# 3.  Benchmark (Nifty 50) daily close prices
# ─────────────────────────────────────────────────────────────────

def fetch_benchmark_history(years: int = 6) -> pd.DataFrame:
    """
    Download Nifty 50 historical closes via yfinance.
    Returns DataFrame with columns: date (datetime), close (float).
    """
    cache_key = f"benchmark_{years}y"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    end = datetime.date.today()
    start = end - datetime.timedelta(days=years * 366)

    try:
        ticker = yf.Ticker(BENCHMARK_TICKER)
        hist = ticker.history(start=str(start), end=str(end), interval="1d")
        if hist.empty:
            raise ValueError("Empty response from yfinance")
        hist = hist[["Close"]].copy()
        hist.index = pd.to_datetime(hist.index).tz_localize(None)
        hist.reset_index(inplace=True)
        hist.columns = ["date", "close"]
        hist.sort_values("date", inplace=True)
        hist.reset_index(drop=True, inplace=True)
        _cache_set(cache_key, hist)
        return hist
    except Exception as exc:
        logger.error("Benchmark fetch failed: %s", exc)
        return pd.DataFrame(columns=["date", "close"])


# ─────────────────────────────────────────────────────────────────
# 4.  Sector allocation & holdings
#     (Simulated – realistic for free-tier; swap for paid data vendor)
# ─────────────────────────────────────────────────────────────────

# Representative Nifty 500 universe for synthetic holdings
_NIFTY500_STOCKS = [
    "Reliance Industries", "TCS", "HDFC Bank", "ICICI Bank", "Infosys",
    "Wipro", "HCL Technologies", "Axis Bank", "Kotak Mahindra Bank", "SBI",
    "Bajaj Finance", "Bajaj Finserv", "Maruti Suzuki", "Titan Company",
    "Asian Paints", "Nestle India", "HUL", "ITC", "Sun Pharma", "Dr. Reddy's",
    "Cipla", "Divis Laboratories", "Tata Motors", "M&M", "Eicher Motors",
    "Hero MotoCorp", "Tata Steel", "JSW Steel", "Hindalco", "Vedanta",
    "NTPC", "Power Grid", "Coal India", "ONGC", "BPCL",
    "Adani Enterprises", "Adani Ports", "Adani Green", "Adani Power", "Adani Total Gas",
    "Britannia", "Marico", "Dabur", "Godrej Consumer", "P&G Hygiene",
    "Siemens", "ABB India", "Havells India", "Voltas", "Whirlpool",
    "SBI Life Insurance", "HDFC Life", "ICICI Prudential Life", "New India Assurance",
    "Muthoot Finance", "Cholamandalam Investment", "Shriram Finance", "L&T Finance",
    "Tata Consultancy Services", "Persistent Systems", "Mphasis", "LTIMindtree",
    "Tech Mahindra", "Oracle Financial", "Coforge", "KPIT Technologies",
    "Zomato", "Nykaa", "Paytm", "PB Fintech", "CarTrade Tech",
    "Tata Power", "Torrent Power", "JSW Energy", "Cummins India",
    "UltraTech Cement", "Shree Cement", "Ambuja Cements", "ACC", "Ramco Cements",
    "Pidilite Industries", "SRF", "Aarti Industries", "Deepak Nitrite",
    "Apollo Hospitals", "Fortis Healthcare", "Max Healthcare", "Narayana Hrudayalaya",
    "Dmart", "Trent", "Jubilant Foodworks", "Westlife Foodworld",
    "IndusInd Bank", "Federal Bank", "IDFC First Bank", "RBL Bank", "Yes Bank",
    "Bharti Airtel", "Vodafone Idea", "Indus Towers",
]

_SECTOR_MAP = {
    "Financial Services": [
        "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank", "SBI",
        "Bajaj Finance", "Bajaj Finserv", "SBI Life Insurance", "HDFC Life",
        "ICICI Prudential Life", "New India Assurance", "Muthoot Finance",
        "Cholamandalam Investment", "Shriram Finance", "L&T Finance",
        "IndusInd Bank", "Federal Bank", "IDFC First Bank", "RBL Bank", "Yes Bank",
        "PB Fintech",
    ],
    "Information Technology": [
        "TCS", "Infosys", "Wipro", "HCL Technologies", "Tech Mahindra",
        "Persistent Systems", "Mphasis", "LTIMindtree", "Oracle Financial",
        "Coforge", "KPIT Technologies", "Tata Consultancy Services",
    ],
    "Consumer Goods": [
        "HUL", "ITC", "Nestle India", "Britannia", "Marico", "Dabur",
        "Godrej Consumer", "P&G Hygiene", "Asian Paints", "Titan Company",
        "Dmart", "Trent", "Jubilant Foodworks", "Westlife Foodworld",
    ],
    "Energy": [
        "Reliance Industries", "ONGC", "BPCL", "NTPC", "Power Grid", "Coal India",
        "Adani Green", "Adani Total Gas", "Tata Power", "Torrent Power", "JSW Energy",
        "Cummins India",
    ],
    "Healthcare": [
        "Sun Pharma", "Dr. Reddy's", "Cipla", "Divis Laboratories",
        "Apollo Hospitals", "Fortis Healthcare", "Max Healthcare", "Narayana Hrudayalaya",
    ],
    "Automobile": [
        "Maruti Suzuki", "Tata Motors", "M&M", "Eicher Motors", "Hero MotoCorp",
    ],
    "Metals & Mining": [
        "Tata Steel", "JSW Steel", "Hindalco", "Vedanta", "Adani Enterprises",
    ],
    "Cement": [
        "UltraTech Cement", "Shree Cement", "Ambuja Cements", "ACC", "Ramco Cements",
    ],
    "Telecom": [
        "Bharti Airtel", "Vodafone Idea", "Indus Towers",
    ],
    "Chemicals": [
        "Pidilite Industries", "SRF", "Aarti Industries", "Deepak Nitrite",
    ],
    "Construction": [
        "Siemens", "ABB India", "Havells India", "Voltas", "Whirlpool",
        "Adani Ports",
    ],
    "Others": [
        "Adani Power", "Zomato", "Nykaa", "Paytm", "CarTrade Tech",
    ],
}

# Reverse lookup: stock → sector
_STOCK_TO_SECTOR: Dict[str, str] = {}
for _sector, _stocks in _SECTOR_MAP.items():
    for _s in _stocks:
        _STOCK_TO_SECTOR[_s] = _sector


def _seed_for_fund(scheme_code: str) -> int:
    """Deterministic seed so the same fund always returns the same holdings."""
    return int(scheme_code) % (2**31 - 1) if scheme_code.isdigit() else hash(scheme_code) % (2**31 - 1)


def fetch_sector_allocation(scheme_code: str, fund_category: str = "") -> Dict[str, float]:
    """
    Return a dict {sector_name: weight_pct} summing to ~100.
    Weights are synthetic but category-aware and deterministic per fund.
    """
    cache_key = f"sector_{scheme_code}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    rng = random.Random(_seed_for_fund(scheme_code))
    cat = fund_category.lower()

    # Category-aware base weights
    if "technology" in cat or "it" in cat:
        base = {
            "Information Technology": 55, "Financial Services": 15,
            "Consumer Goods": 8, "Healthcare": 7, "Energy": 5, "Others": 10,
        }
    elif "pharma" in cat or "health" in cat:
        base = {
            "Healthcare": 60, "Consumer Goods": 12, "Financial Services": 10,
            "Chemicals": 8, "Others": 10,
        }
    elif "small cap" in cat:
        base = {
            "Financial Services": 20, "Consumer Goods": 15, "Healthcare": 12,
            "Chemicals": 10, "Automobile": 8, "Construction": 8,
            "Metals & Mining": 7, "Others": 20,
        }
    elif "mid cap" in cat:
        base = {
            "Financial Services": 22, "Consumer Goods": 14, "Information Technology": 12,
            "Healthcare": 10, "Automobile": 9, "Chemicals": 8,
            "Construction": 7, "Others": 18,
        }
    else:  # large cap / flexi / balanced default
        base = {
            "Financial Services": 32, "Information Technology": 18,
            "Consumer Goods": 12, "Energy": 10, "Healthcare": 8,
            "Automobile": 7, "Metals & Mining": 5, "Cement": 4, "Others": 4,
        }

    # Add jitter ±5 pp
    jittered = {k: max(1.0, v + rng.uniform(-5, 5)) for k, v in base.items()}
    total = sum(jittered.values())
    normalized = {k: round(v / total * 100, 2) for k, v in jittered.items()}

    _cache_set(cache_key, normalized)
    return normalized


def fetch_holdings(scheme_code: str, fund_category: str = "", top_n: int = 25) -> pd.DataFrame:
    """
    Return a DataFrame of top holdings:
      columns: stock_name, sector, weight_pct
    Deterministic synthetic data seeded on scheme_code.
    """
    cache_key = f"holdings_{scheme_code}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    rng = random.Random(_seed_for_fund(scheme_code))
    sector_alloc = fetch_sector_allocation(scheme_code, fund_category)

    records = []
    remaining = 100.0

    for sector, alloc_pct in sorted(sector_alloc.items(), key=lambda x: -x[1]):
        sector_stocks = _SECTOR_MAP.get(sector, [])
        if not sector_stocks:
            continue
        n_stocks = max(1, round(alloc_pct / 100 * top_n))
        chosen = rng.sample(sector_stocks, min(n_stocks, len(sector_stocks)))

        if len(chosen) == 0:
            continue

        raw_weights = [rng.uniform(0.5, alloc_pct / max(len(chosen), 1)) for _ in chosen]
        total_raw = sum(raw_weights)
        scaled = [w / total_raw * alloc_pct for w in raw_weights]

        for stock, weight in zip(chosen, scaled):
            records.append({"stock_name": stock, "sector": sector, "weight_pct": round(weight, 2)})

    df = pd.DataFrame(records)
    if df.empty:
        _cache_set(cache_key, df)
        return df

    df = df.groupby("stock_name", as_index=False).agg(
        {"sector": "first", "weight_pct": "sum"}
    )
    df.sort_values("weight_pct", ascending=False, inplace=True)
    df = df.head(top_n).reset_index(drop=True)

    # Re-normalise to exactly 100
    total = df["weight_pct"].sum()
    df["weight_pct"] = (df["weight_pct"] / total * 100).round(2)

    _cache_set(cache_key, df)
    return df


def fetch_portfolio_ratios(scheme_code: str, fund_category: str = "") -> Dict[str, float]:
    """
    Return synthetic but realistic P/E and P/B ratios for the portfolio,
    derived from fund category.
    """
    cache_key = f"ratios_{scheme_code}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    rng = random.Random(_seed_for_fund(scheme_code) + 7)
    cat = fund_category.lower()

    if "technology" in cat or "it" in cat:
        pe = rng.uniform(28, 45)
        pb = rng.uniform(6, 11)
    elif "pharma" in cat or "health" in cat:
        pe = rng.uniform(30, 50)
        pb = rng.uniform(4, 8)
    elif "small cap" in cat:
        pe = rng.uniform(20, 40)
        pb = rng.uniform(3, 7)
    elif "mid cap" in cat:
        pe = rng.uniform(22, 38)
        pb = rng.uniform(3.5, 7)
    elif "value" in cat or "contra" in cat:
        pe = rng.uniform(12, 22)
        pb = rng.uniform(1.5, 3)
    else:
        pe = rng.uniform(18, 30)
        pb = rng.uniform(2.5, 5)

    result = {"pe_ratio": round(pe, 2), "pb_ratio": round(pb, 2)}
    _cache_set(cache_key, result)
    return result


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _safe_float(val) -> Optional[float]:
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return None

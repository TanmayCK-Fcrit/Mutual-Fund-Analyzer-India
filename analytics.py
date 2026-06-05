"""
analytics.py
------------
Pure financial analytics functions.
All functions are stateless, deterministic, and unit-testable.

Covers:
  - Period returns (6M, 1Y, 3Y, 5Y, All-Time)
  - Annualised volatility
  - Alpha & Beta (vs benchmark)
  - Sharpe Ratio
  - Sortino Ratio
  - Portfolio overlap detection
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from config import RISK_FREE_RATE, RETURN_WINDOWS

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────
TRADING_DAYS_YEAR = 252
DAILY_RF = RISK_FREE_RATE / TRADING_DAYS_YEAR  # daily risk-free rate


# ─────────────────────────────────────────────────────────────────
# 1.  Return calculations
# ─────────────────────────────────────────────────────────────────

def calc_period_return(nav_series: pd.DataFrame, days: int) -> Optional[float]:
    """
    Calculate the simple return over `days` calendar days.
    nav_series must have columns: date, nav – sorted ascending.
    Returns percentage (e.g. 12.5 for 12.5%).
    """
    if nav_series.empty or len(nav_series) < 2:
        return None

    latest = nav_series.iloc[-1]
    cutoff = latest["date"] - pd.Timedelta(days=days)
    past = nav_series[nav_series["date"] <= cutoff]

    if past.empty:
        return None

    start_nav = past.iloc[-1]["nav"]
    end_nav = latest["nav"]

    if start_nav <= 0:
        return None

    raw = (end_nav - start_nav) / start_nav * 100

    # Annualise for periods >= 1 year
    if days >= 365:
        years = days / 365
        annualised = ((end_nav / start_nav) ** (1 / years) - 1) * 100
        return round(annualised, 2)

    return round(raw, 2)


def calc_all_time_return(nav_series: pd.DataFrame) -> Optional[float]:
    """Annualised return from inception."""
    if nav_series.empty or len(nav_series) < 2:
        return None

    start_nav = nav_series.iloc[0]["nav"]
    end_nav = nav_series.iloc[-1]["nav"]
    start_date = nav_series.iloc[0]["date"]
    end_date = nav_series.iloc[-1]["date"]

    years = (end_date - start_date).days / 365
    if years <= 0 or start_nav <= 0:
        return None

    annualised = ((end_nav / start_nav) ** (1 / years) - 1) * 100
    return round(annualised, 2)


def calc_all_returns(nav_series: pd.DataFrame) -> Dict[str, Optional[float]]:
    """Return dict with all period returns."""
    returns = {label: calc_period_return(nav_series, days) for label, days in RETURN_WINDOWS.items()}
    returns["All-Time"] = calc_all_time_return(nav_series)
    return returns


# ─────────────────────────────────────────────────────────────────
# 2.  Daily returns helper
# ─────────────────────────────────────────────────────────────────

def daily_returns(series: pd.Series) -> pd.Series:
    """
    Compute daily log returns from a price/NAV series.
    Drops the first NaN row automatically.
    """
    return np.log(series / series.shift(1)).dropna()


# ─────────────────────────────────────────────────────────────────
# 3.  Align fund NAV and benchmark to common dates
# ─────────────────────────────────────────────────────────────────

def align_series(
    nav_df: pd.DataFrame,
    bench_df: pd.DataFrame,
) -> Tuple[pd.Series, pd.Series]:
    """
    Inner-join fund NAV and benchmark on date.
    Returns (fund_prices, bench_prices) as aligned pd.Series.
    """
    fund = nav_df.set_index("date")["nav"]
    bench = bench_df.set_index("date")["close"]

    merged = pd.concat([fund, bench], axis=1, join="inner").dropna()
    merged.columns = ["fund", "bench"]
    merged.sort_index(inplace=True)
    return merged["fund"], merged["bench"]


# ─────────────────────────────────────────────────────────────────
# 4.  Alpha & Beta (OLS regression)
# ─────────────────────────────────────────────────────────────────

def calc_alpha_beta(
    nav_df: pd.DataFrame,
    bench_df: pd.DataFrame,
    years: int = 3,
) -> Tuple[Optional[float], Optional[float]]:
    """
    Compute annualised Jensen's Alpha and Beta vs the benchmark
    over the last `years` years using daily log returns.

    Returns (alpha, beta). Alpha is annualised (%).
    """
    try:
        fund_p, bench_p = align_series(nav_df, bench_df)

        if len(fund_p) < 60:  # need at least ~60 data points
            return None, None

        # Trim to last `years` years
        cutoff = fund_p.index[-1] - pd.DateOffset(years=years)
        fund_p = fund_p[fund_p.index >= cutoff]
        bench_p = bench_p[bench_p.index >= cutoff]

        if len(fund_p) < 30:
            return None, None

        r_fund = daily_returns(fund_p)
        r_bench = daily_returns(bench_p)

        # Align after differencing
        aligned = pd.concat([r_fund, r_bench], axis=1, join="inner").dropna()
        aligned.columns = ["fund", "bench"]

        if len(aligned) < 30:
            return None, None

        # OLS: r_fund = alpha_daily + beta * r_bench
        x = aligned["bench"].values
        y = aligned["fund"].values

        cov_matrix = np.cov(x, y)
        beta = cov_matrix[0, 1] / cov_matrix[0, 0]

        alpha_daily = np.mean(y) - beta * np.mean(x)

        # Annualise alpha: subtract daily rf contribution
        alpha_excess_daily = alpha_daily - (DAILY_RF * (1 - beta))
        alpha_annualised = alpha_excess_daily * TRADING_DAYS_YEAR * 100

        return round(alpha_annualised, 4), round(beta, 4)

    except Exception as exc:
        logger.warning("Alpha/Beta calculation failed: %s", exc)
        return None, None


# ─────────────────────────────────────────────────────────────────
# 5.  Sharpe Ratio
# ─────────────────────────────────────────────────────────────────

def calc_sharpe_ratio(
    nav_df: pd.DataFrame,
    years: int = 3,
) -> Optional[float]:
    """
    Annualised Sharpe Ratio over the last `years` years.
    Uses daily log returns.
    """
    try:
        fund_p = nav_df.set_index("date")["nav"]
        if len(fund_p) < 60:
            return None

        cutoff = fund_p.index[-1] - pd.DateOffset(years=years)
        fund_p = fund_p[fund_p.index >= cutoff]

        r = daily_returns(fund_p)
        if len(r) < 30:
            return None

        excess = r - DAILY_RF
        if excess.std() == 0:
            return None

        sharpe = (excess.mean() / excess.std()) * np.sqrt(TRADING_DAYS_YEAR)
        return round(sharpe, 4)

    except Exception as exc:
        logger.warning("Sharpe calculation failed: %s", exc)
        return None


# ─────────────────────────────────────────────────────────────────
# 6.  Sortino Ratio
# ─────────────────────────────────────────────────────────────────

def calc_sortino_ratio(
    nav_df: pd.DataFrame,
    years: int = 3,
) -> Optional[float]:
    """
    Annualised Sortino Ratio over the last `years` years.
    Uses downside deviation (returns below the daily risk-free rate).
    """
    try:
        fund_p = nav_df.set_index("date")["nav"]
        if len(fund_p) < 60:
            return None

        cutoff = fund_p.index[-1] - pd.DateOffset(years=years)
        fund_p = fund_p[fund_p.index >= cutoff]

        r = daily_returns(fund_p)
        if len(r) < 30:
            return None

        excess = r - DAILY_RF
        downside = excess[excess < 0]

        if len(downside) == 0:
            return None

        downside_dev = np.sqrt(np.mean(downside**2)) * np.sqrt(TRADING_DAYS_YEAR)
        if downside_dev == 0:
            return None

        sortino = (excess.mean() * TRADING_DAYS_YEAR) / downside_dev
        return round(sortino, 4)

    except Exception as exc:
        logger.warning("Sortino calculation failed: %s", exc)
        return None


# ─────────────────────────────────────────────────────────────────
# 7.  Portfolio Overlap
# ─────────────────────────────────────────────────────────────────

def find_common_holdings(
    holdings_map: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Given {fund_label: holdings_df}, identify stocks that appear in
    2 or more funds.

    Returns DataFrame:
      stock_name | sector | present_in_funds (list[str]) |
      fund_weights (dict) | avg_weight | overlap_score
    """
    if len(holdings_map) < 2:
        return pd.DataFrame()

    # Build stock → {fund: weight} map
    stock_fund_weight: Dict[str, Dict[str, float]] = {}
    for label, df in holdings_map.items():
        for _, row in df.iterrows():
            stock = row["stock_name"]
            weight = row["weight_pct"]
            if stock not in stock_fund_weight:
                stock_fund_weight[stock] = {}
            stock_fund_weight[stock][label] = weight

    records = []
    for stock, fw in stock_fund_weight.items():
        if len(fw) >= 2:  # common in at least 2 funds
            avg_w = np.mean(list(fw.values()))
            # Overlap score = harmonic mean of weights × number of funds
            overlap = len(fw) * avg_w
            records.append(
                {
                    "stock_name": stock,
                    "present_in_n_funds": len(fw),
                    "funds": list(fw.keys()),
                    "weights": fw,
                    "avg_weight_pct": round(avg_w, 2),
                    "overlap_score": round(overlap, 2),
                }
            )

    if not records:
        return pd.DataFrame()

    df_out = pd.DataFrame(records)
    df_out.sort_values("overlap_score", ascending=False, inplace=True)
    df_out.reset_index(drop=True, inplace=True)
    return df_out


def calc_overlap_concentration(
    holdings_map: Dict[str, pd.DataFrame],
) -> Dict[str, float]:
    """
    For each fund, compute the percentage of its capital that sits in
    stocks common with at least one other fund.

    Returns {fund_label: overlap_pct}
    """
    if len(holdings_map) < 2:
        return {}

    common_df = find_common_holdings(holdings_map)
    if common_df.empty:
        return {label: 0.0 for label in holdings_map}

    common_stocks = set(common_df["stock_name"].tolist())

    result = {}
    for label, df in holdings_map.items():
        overlap_weight = df[df["stock_name"].isin(common_stocks)]["weight_pct"].sum()
        result[label] = round(overlap_weight, 2)

    return result


# ─────────────────────────────────────────────────────────────────
# 8.  NAV index rebased for charting
# ─────────────────────────────────────────────────────────────────

def rebase_nav(nav_df: pd.DataFrame, base: float = 100.0) -> pd.DataFrame:
    """
    Return a copy of nav_df with NAV rebased to `base` at the start date,
    adding column 'rebased_nav'.
    """
    df = nav_df.copy()
    if df.empty:
        return df
    start = df.iloc[0]["nav"]
    df["rebased_nav"] = df["nav"] / start * base
    return df


def rebase_benchmark(bench_df: pd.DataFrame, ref_date: pd.Timestamp, base: float = 100.0) -> pd.DataFrame:
    """
    Rebase benchmark from ref_date to base=100.
    """
    df = bench_df.copy()
    df = df[df["date"] >= ref_date].copy()
    if df.empty:
        return df
    start = df.iloc[0]["close"]
    df["rebased_close"] = df["close"] / start * base
    return df

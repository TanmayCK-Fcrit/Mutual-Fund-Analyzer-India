"""
app.py
------
Indian Mutual Fund Analyzer — Main Streamlit Application Entry Point.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analytics as an
import data_fetcher as df_mod
from config import (
    APP_ICON,
    APP_SUBTITLE,
    APP_TITLE,
    BRAND_COLORS,
    CHART_HEIGHT,
    MAX_FUNDS_COMPARE,
    PLOTLY_TEMPLATE,
    POPULAR_FUNDS,
    SECTOR_COLORS,
)

# ─────────────────────────────────────────────────────────────────
# Page Config  (must be FIRST Streamlit call)
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────────
def _inject_css():
    st.markdown(
        """
        <style>
        /* ── Import fonts ── */
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

        /* ── Root variables ── */
        :root {
            --bg-deep:   #080c14;
            --bg-panel:  #0d1520;
            --bg-card:   #111c2e;
            --border:    #1e2d45;
            --accent:    #00d4ff;
            --accent2:   #7b61ff;
            --text:      #e2eaf4;
            --muted:     #64748b;
            --success:   #00ff9c;
            --danger:    #ff4d6d;
        }

        /* ── Global resets ── */
        html, body, [class*="css"] {
            font-family: 'DM Sans', sans-serif;
            background-color: var(--bg-deep) !important;
            color: var(--text) !important;
        }

        /* ── Sidebar ── */
        section[data-testid="stSidebar"] {
            background: var(--bg-panel) !important;
            border-right: 1px solid var(--border) !important;
        }
        section[data-testid="stSidebar"] * {
            color: var(--text) !important;
        }

        /* ── Headers ── */
        h1, h2, h3, h4 {
            font-family: 'Space Mono', monospace !important;
            letter-spacing: -0.5px;
        }

        /* ── Metric boxes ── */
        [data-testid="stMetric"] {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
            padding: 16px 20px !important;
        }
        [data-testid="stMetricLabel"] p {
            color: var(--muted) !important;
            font-size: 11px !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        [data-testid="stMetricValue"] {
            font-family: 'Space Mono', monospace !important;
            color: var(--accent) !important;
            font-size: 22px !important;
        }

        /* ── DataFrames / Tables ── */
        [data-testid="stDataFrame"] {
            border: 1px solid var(--border) !important;
            border-radius: 10px;
            overflow: hidden;
        }

        /* ── Buttons ── */
        .stButton > button {
            background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
            color: #000 !important;
            font-family: 'Space Mono', monospace !important;
            font-weight: 700 !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 10px 24px !important;
            letter-spacing: 0.5px;
            transition: opacity 0.2s;
        }
        .stButton > button:hover { opacity: 0.85; }

        /* ── Expanders ── */
        details {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 10px !important;
        }

        /* ── Tabs ── */
        [data-testid="stTabs"] button {
            font-family: 'Space Mono', monospace !important;
            font-size: 12px !important;
        }
        [data-testid="stTabs"] button[aria-selected="true"] {
            color: var(--accent) !important;
            border-bottom: 2px solid var(--accent) !important;
        }

        /* ── Dividers ── */
        hr { border-color: var(--border) !important; }

        /* ── Select / Input boxes ── */
        .stSelectbox > div > div,
        .stMultiSelect > div > div {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
        }

        /* ── Positive/negative colour helpers ── */
        .pos { color: #00ff9c !important; font-weight: 600; }
        .neg { color: #ff4d6d !important; font-weight: 600; }
        .neutral { color: #ffd600 !important; }

        /* ── Hero banner ── */
        .hero-banner {
            background: linear-gradient(135deg, #0d1520 0%, #0a1628 50%, #0f1d35 100%);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 32px 40px;
            margin-bottom: 24px;
            position: relative;
            overflow: hidden;
        }
        .hero-banner::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(0,212,255,0.06) 0%, transparent 70%);
            pointer-events: none;
        }
        .hero-title {
            font-family: 'Space Mono', monospace;
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #00d4ff, #7b61ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            line-height: 1.2;
        }
        .hero-subtitle {
            color: var(--muted);
            font-size: 14px;
            margin-top: 8px;
            letter-spacing: 2px;
            text-transform: uppercase;
        }

        /* ── Overlap badge ── */
        .overlap-badge {
            display: inline-block;
            background: rgba(123,97,255,0.15);
            border: 1px solid var(--accent2);
            color: var(--accent2);
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-family: 'Space Mono', monospace;
            font-weight: 700;
        }

        /* ── Section headers ── */
        .section-header {
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
            margin: 24px 0 16px;
        }
        .section-header span {
            font-family: 'Space Mono', monospace;
            font-size: 0.9rem;
            color: var(--accent);
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        /* ── Info cards ── */
        .info-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _fmt_pct(val: Optional[float], suffix: str = "%") -> str:
    if val is None:
        return "N/A"
    colour = "pos" if val >= 0 else "neg"
    sign = "+" if val > 0 else ""
    return f'<span class="{colour}">{sign}{val:.2f}{suffix}</span>'


def _fmt_ratio(val: Optional[float]) -> str:
    if val is None:
        return "N/A"
    colour = "pos" if val >= 0 else "neg"
    sign = "+" if val > 0 else ""
    return f'<span class="{colour}">{sign}{val:.3f}</span>'


def _fmt_nav(val: Optional[float]) -> str:
    if val is None:
        return "N/A"
    return f"₹{val:,.2f}"


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_all_funds():
    return df_mod.fetch_all_funds()


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_nav_history(scheme_code: str):
    return df_mod.fetch_nav_history(scheme_code)


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_benchmark():
    return df_mod.fetch_benchmark_history(years=6)


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_meta(scheme_code: str):
    return df_mod.fetch_fund_meta(scheme_code)


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_holdings(scheme_code: str, category: str):
    return df_mod.fetch_holdings(scheme_code, category)


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_sectors(scheme_code: str, category: str):
    return df_mod.fetch_sector_allocation(scheme_code, category)


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_ratios(scheme_code: str, category: str):
    return df_mod.fetch_portfolio_ratios(scheme_code, category)


# ─────────────────────────────────────────────────────────────────
# Plotly theme helper
# ─────────────────────────────────────────────────────────────────

def _dark_layout(fig: go.Figure, title: str = "", height: int = CHART_HEIGHT) -> go.Figure:
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=height,
        title=dict(text=title, font=dict(family="Space Mono", size=13, color="#e2eaf4")),
        paper_bgcolor="rgba(13,21,32,0)",
        plot_bgcolor="rgba(13,21,32,0)",
        margin=dict(l=10, r=10, t=40, b=30),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10, color="#94a3b8"),
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(30,45,69,0.8)",
            color="#64748b",
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(30,45,69,0.8)",
            color="#64748b",
            tickfont=dict(size=10),
        ),
    )
    return fig


# ─────────────────────────────────────────────────────────────────
# Individual fund analysis
# ─────────────────────────────────────────────────────────────────

def _analyse_fund(
    scheme_code: str,
    bench_df: pd.DataFrame,
) -> dict:
    """Run all analytics for a single fund. Returns a rich dict."""
    meta = _cached_meta(scheme_code)
    nav_df = _cached_nav_history(scheme_code)
    category = meta.get("scheme_category", "Custom Input")  # Fallback added

    current_nav = nav_df.iloc[-1]["nav"] if not nav_df.empty else None
    inception_date = nav_df.iloc[0]["date"].strftime("%d %b %Y") if not nav_df.empty else "N/A"

    returns = an.calc_all_returns(nav_df)
    alpha, beta = an.calc_alpha_beta(nav_df, bench_df)
    sharpe = an.calc_sharpe_ratio(nav_df)
    sortino = an.calc_sortino_ratio(nav_df)
    holdings = _cached_holdings(scheme_code, category)
    sectors = _cached_sectors(scheme_code, category)
    ratios = _cached_ratios(scheme_code, category)

    return {
        "scheme_code": scheme_code,
        "name": meta.get("scheme_name", f"Fund #{scheme_code}"),  # Fallback added
        "fund_house": meta.get("fund_house", "Unknown House"),   # Fallback added
        "category": category,
        "inception_date": inception_date,
        "current_nav": current_nav,
        "returns": returns,
        "alpha": alpha,
        "beta": beta,
        "sharpe": sharpe,
        "sortino": sortino,
        "holdings": holdings,
        "sectors": sectors,
        "pe_ratio": ratios.get("pe_ratio"),
        "pb_ratio": ratios.get("pb_ratio"),
        "nav_df": nav_df,
    }


# ─────────────────────────────────────────────────────────────────
# Chart builders
# ─────────────────────────────────────────────────────────────────

def _build_nav_chart(
    fund_data: List[dict],
    bench_df: pd.DataFrame,
    window_days: int = 365,
) -> go.Figure:
    fig = go.Figure()
    cutoff = pd.Timestamp.today() - pd.Timedelta(days=window_days)

    for i, fd in enumerate(fund_data):
        nav_df = fd["nav_df"]
        if nav_df.empty:
            continue
        nav_df = nav_df[nav_df["date"] >= cutoff]
        if nav_df.empty:
            continue

        rebased = an.rebase_nav(nav_df)
        short_name = fd["name"][:35] + ("…" if len(fd["name"]) > 35 else "")

        fig.add_trace(
            go.Scatter(
                x=rebased["date"],
                y=rebased["rebased_nav"],
                name=short_name,
                line=dict(color=BRAND_COLORS[i % len(BRAND_COLORS)], width=2),
                hovertemplate="%{x|%d %b %Y}<br>Rebased NAV: %{y:.2f}<extra></extra>",
            )
        )

    # Benchmark overlay
    if not bench_df.empty:
        bench_trimmed = bench_df[bench_df["date"] >= cutoff].copy()
        if not bench_trimmed.empty:
            ref = bench_trimmed.iloc[0]["close"]
            bench_trimmed["rebased"] = bench_trimmed["close"] / ref * 100
            fig.add_trace(
                go.Scatter(
                    x=bench_trimmed["date"],
                    y=bench_trimmed["rebased"],
                    name="Nifty 50",
                    line=dict(color="#ffffff", width=1.5, dash="dot"),
                    opacity=0.5,
                    hovertemplate="%{x|%d %b %Y}<br>Nifty 50: %{y:.2f}<extra></extra>",
                )
            )

    _dark_layout(fig, title="Performance (Rebased to 100)")
    return fig


def _build_returns_bar(fund_data: List[dict]) -> go.Figure:
    periods = ["6M", "1Y", "3Y", "5Y", "All-Time"]
    fig = go.Figure()

    for i, fd in enumerate(fund_data):
        values = [fd["returns"].get(p) for p in periods]
        short = fd["name"][:30] + ("…" if len(fd["name"]) > 30 else "")
        fig.add_trace(
            go.Bar(
                name=short,
                x=periods,
                y=values,
                marker_color=BRAND_COLORS[i % len(BRAND_COLORS)],
                text=[f"{v:.1f}%" if v is not None else "N/A" for v in values],
                textposition="outside",
                hovertemplate="%{x}: %{y:.2f}%<extra></extra>",
            )
        )

    _dark_layout(fig, title="Annualised Returns by Period (%)", height=360)
    fig.update_layout(barmode="group", yaxis_ticksuffix="%")
    return fig


def _build_sector_pie(sectors: dict, fund_name: str, color_i: int) -> go.Figure:
    labels = list(sectors.keys())
    values = list(sectors.values())
    colors = [SECTOR_COLORS.get(l, BRAND_COLORS[j % len(BRAND_COLORS)]) for j, l in enumerate(labels)]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(colors=colors, line=dict(color="#080c14", width=2)),
            textfont=dict(size=10),
            hovertemplate="%{label}: %{value:.1f}%<extra></extra>",
        )
    )
    short = fund_name[:40] + ("…" if len(fund_name) > 40 else "")
    _dark_layout(fig, title=f"Sector Allocation — {short}", height=340)
    return fig

def hex_to_rgba(hex_str: str, alpha: float = 0.12) -> str:
    """Converts #RRGGBB to rgba(R, G, B, A) cleanly for Plotly."""
    hex_str = hex_str.lstrip('#')
    # Convert hex to integer tuples
    r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {b}, {g}, {alpha})"

def _build_risk_radar(fund_data: List[dict]) -> go.Figure:
    """Spider / radar chart comparing risk metrics across funds."""
    categories = ["Sharpe", "Sortino", "Alpha", "Beta (inv)", "Returns 3Y"]

    def _norm(val, lo, hi):
        if val is None:
            return 0
        return max(0, min(10, (val - lo) / (hi - lo) * 10))

    fig = go.Figure()
    for i, fd in enumerate(fund_data):
        r3y = fd["returns"].get("3Y")
        values = [
            _norm(fd["sharpe"], -1, 3),
            _norm(fd["sortino"], -1, 4),
            _norm(fd["alpha"], -5, 10),
            _norm(2 - (fd["beta"] or 1), 0, 2),   # lower beta → higher score
            _norm(r3y, -5, 40),
        ]
        short = fd["name"][:28] + ("…" if len(fd["name"]) > 28 else "")
        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                name=short,
                line_color=BRAND_COLORS[i % len(BRAND_COLORS)],
                fillcolor=hex_to_rgba(BRAND_COLORS[i % len(BRAND_COLORS)], alpha=0.12),
                opacity=0.85,
            )
        )

    _dark_layout(fig, title="Risk-Return Radar (0–10 normalised)", height=380)
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(13,21,32,0.6)",
            radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(size=8), color="#64748b"),
            angularaxis=dict(tickfont=dict(size=10), color="#94a3b8"),
        )
    )
    return fig


def _build_overlap_heatmap(
    holdings_map: Dict[str, pd.DataFrame],
    fund_labels: List[str],
) -> go.Figure:
    n = len(fund_labels)
    matrix = np.zeros((n, n))

    for i, l1 in enumerate(fund_labels):
        stocks1 = set(holdings_map[l1]["stock_name"].tolist())
        w1 = holdings_map[l1].set_index("stock_name")["weight_pct"].to_dict()
        for j, l2 in enumerate(fund_labels):
            if i == j:
                matrix[i][j] = 100.0
                continue
            stocks2 = set(holdings_map[l2]["stock_name"].tolist())
            w2 = holdings_map[l2].set_index("stock_name")["weight_pct"].to_dict()
            common = stocks1 & stocks2
            if not common:
                matrix[i][j] = 0.0
            else:
                overlap = sum(min(w1.get(s, 0), w2.get(s, 0)) for s in common)
                matrix[i][j] = round(overlap, 2)

    short_labels = [l[:22] + "…" if len(l) > 22 else l for l in fund_labels]

    fig = go.Figure(
        go.Heatmap(
            z=matrix,
            x=short_labels,
            y=short_labels,
            colorscale=[[0, "#0d1520"], [0.5, "#1e3a5f"], [1, "#00d4ff"]],
            text=[[f"{v:.1f}%" for v in row] for row in matrix],
            texttemplate="%{text}",
            textfont=dict(size=10, color="white"),
            showscale=True,
            zmin=0,
            zmax=100,
        )
    )
    _dark_layout(fig, title="Portfolio Overlap Heatmap (% of capital in common stocks)", height=400)
    fig.update_layout(xaxis=dict(tickangle=-30))
    return fig


# ─────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────

def _render_sidebar(all_funds_df: pd.DataFrame) -> List[str]:
    with st.sidebar:
        st.markdown(
            '<div style="font-family:\'Space Mono\',monospace;font-size:18px;'
            'color:#00d4ff;font-weight:700;padding:8px 0 4px;">⚡ Fund Selector</div>',
            unsafe_allow_html=True,
        )
        st.caption("Add funds via presets, multi-word search, or direct API URLs.")

        st.divider()

        # ── 1. Preset funds ──
        use_presets = st.checkbox("Load Popular Funds", value=True)
        if use_presets:
            default_presets = list(POPULAR_FUNDS.keys())[:4]
            selected_presets = st.multiselect(
                "Popular Funds",
                options=list(POPULAR_FUNDS.keys()),
                default=default_presets,
                help="Pre-defined list of well-known Indian MFs.",
            )
        else:
            selected_presets = []

        st.divider()

        # ── 2. Direct mfapi.in URL Input ──
        st.markdown("**🔗 Add via Direct API URL**")
        url_input = st.text_input(
            "Paste mfapi.in URL", 
            placeholder="e.g., https://api.mfapi.in/mf/128032",
            key="url_input_field"
        )
        
        if url_input:
            url_cleaned = url_input.strip().rstrip('/')
            # Extract the last numeric segment of the URL path
            code_candidate = url_cleaned.split('/')[-1]
            
            if code_candidate.isdigit():
                if st.button("➕ Add URL Fund", key="add_url_btn"):
                    if code_candidate not in st.session_state.get("added_codes", []):
                        st.session_state.setdefault("added_codes", []).append(code_candidate)
                        st.success(f"Added scheme code: {code_candidate}!")
                        time.sleep(0.5)
                        st.rerun()
            else:
                st.error("Invalid URL format. Make sure it ends with the 6-digit scheme code.")

        st.divider()

        # ── 3. Search & add custom ──
        st.markdown("**🔍 Search Any Fund**")
        search_q = st.text_input("Fund name keyword", placeholder="e.g. Motilal Midcap")

        if search_q and len(search_q) >= 3:
            with st.spinner("Searching…"):
                search_tokens = search_q.lower().strip().split()
                mask = all_funds_df["scheme_name"].str.lower().apply(
                    lambda x: all(token in x for token in search_tokens)
                )
                results = all_funds_df[mask]

            if results.empty:
                st.warning("No funds found. Try shortening your keyword.")
            else:
                st.caption(f"Found {len(results)} results")
                choice = st.selectbox(
                    "Select a fund",
                    options=results["scheme_name"].tolist()[:50],
                    key="search_choice",
                )
                if st.button("➕ Add Search Fund"):
                    row = results[results["scheme_name"] == choice].iloc[0]
                    code = row["scheme_code"]
                    if code not in st.session_state.get("added_codes", []):
                        st.session_state.setdefault("added_codes", []).append(code)
                        st.rerun()

        if st.session_state.get("added_codes"):
            st.markdown("**Added Funds**")
            for code in st.session_state["added_codes"]:
                row = all_funds_df[all_funds_df["scheme_code"] == code]
                name = row.iloc[0]["scheme_name"] if not row.empty else f"Custom Fund (Code: {code})"
                cols = st.columns([4, 1])
                cols[0].caption(f"• {name[:40]}…" if len(name) > 40 else f"• {name}")
                if cols[1].button("✕", key=f"rm_{code}"):
                    st.session_state["added_codes"].remove(code)
                    st.rerun()

        st.divider()
        st.caption("💡 Data sourced from AMFI & mfapi.in. Holdings are illustrative.")

    # ── Compile final list of codes ──
    codes = []
    for name in selected_presets:
        codes.append(POPULAR_FUNDS[name])
    for code in st.session_state.get("added_codes", []):
        if code not in codes:
            codes.append(code)

    return codes[:MAX_FUNDS_COMPARE]


# ─────────────────────────────────────────────────────────────────
# Summary metrics table
# ─────────────────────────────────────────────────────────────────

def _render_summary_table(fund_data_list: List[dict]):
    st.markdown(
        '<div class="section-header"><span>📋 Fund Summary — All Metrics</span></div>',
        unsafe_allow_html=True,
    )

    rows = []
    for fd in fund_data_list:
        r = fd["returns"]
        rows.append(
            {
                "Fund Name": fd["name"],
                "Inception": fd["inception_date"],
                "NAV (₹)": f"{fd['current_nav']:,.2f}" if fd["current_nav"] else "N/A",
                "6M (%)": r.get("6M"),
                "1Y (%)": r.get("1Y"),
                "3Y (%)": r.get("3Y"),
                "5Y (%)": r.get("5Y"),
                "All-Time (%)": r.get("All-Time"),
                "P/E": fd["pe_ratio"],
                "P/B": fd["pb_ratio"],
                "Alpha": fd["alpha"],
                "Beta": fd["beta"],
                "Sharpe": fd["sharpe"],
                "Sortino": fd["sortino"],
            }
        )

    df_table = pd.DataFrame(rows)

    # Colour gradient on return columns
    return_cols = ["6M (%)", "1Y (%)", "3Y (%)", "5Y (%)", "All-Time (%)"]

    def _colour_ret(val):
        if pd.isna(val):
            return "color: #64748b"
        return "color: #00ff9c" if val >= 0 else "color: #ff4d6d"

    styled = (
        df_table.style
        .map(_colour_ret, subset=return_cols)
        .format(
            {c: lambda x: f"{x:.2f}" if isinstance(x, float) else str(x) for c in return_cols},
            na_rep="N/A",
        )
        .format(
            {
                "P/E": lambda x: f"{x:.2f}" if isinstance(x, float) else "N/A",
                "P/B": lambda x: f"{x:.2f}" if isinstance(x, float) else "N/A",
                "Alpha": lambda x: f"{x:+.3f}" if isinstance(x, float) else "N/A",
                "Beta": lambda x: f"{x:.3f}" if isinstance(x, float) else "N/A",
                "Sharpe": lambda x: f"{x:.3f}" if isinstance(x, float) else "N/A",
                "Sortino": lambda x: f"{x:.3f}" if isinstance(x, float) else "N/A",
            },
            na_rep="N/A",
        )
        .set_table_styles(
            [
                {
                    "selector": "thead th",
                    "props": [
                        ("background-color", "#0d1520"),
                        ("color", "#00d4ff"),
                        ("font-family", "Space Mono, monospace"),
                        ("font-size", "10px"),
                        ("text-transform", "uppercase"),
                        ("border-bottom", "2px solid #1e2d45"),
                        ("white-space", "nowrap"),
                    ],
                },
                {
                    "selector": "tbody tr:nth-child(even)",
                    "props": [("background-color", "#0d1520")],
                },
                {
                    "selector": "tbody tr:nth-child(odd)",
                    "props": [("background-color", "#111c2e")],
                },
                {
                    "selector": "td",
                    "props": [
                        ("font-size", "12px"),
                        ("padding", "8px 12px"),
                        ("border-bottom", "1px solid #1e2d45"),
                        ("white-space", "nowrap"),
                    ],
                },
                {
                    "selector": "tbody td:first-child",
                    "props": [
                        ("font-weight", "600"),
                        ("color", "#e2eaf4"),
                        ("max-width", "260px"),
                        ("overflow", "hidden"),
                        ("text-overflow", "ellipsis"),
                    ],
                },
            ]
        )
    )

    st.dataframe(df_table, use_container_width=True, height=min(60 + 40 * len(rows), 500))


# ─────────────────────────────────────────────────────────────────
# Individual fund detail cards
# ─────────────────────────────────────────────────────────────────

def _render_fund_card(fd: dict, bench_df: pd.DataFrame, idx: int):
    accent = BRAND_COLORS[idx % len(BRAND_COLORS)]
    short_name = fd["name"][:65] + ("…" if len(fd["name"]) > 65 else "")

    with st.expander(f"🏦  {short_name}", expanded=(idx == 0)):
        # ── Top row of metrics ──
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Current NAV", _fmt_nav(fd["current_nav"]))
        c2.metric("Inception", fd["inception_date"])
        c3.metric("Category", fd.get("category", "N/A")[:20] if fd.get("category") else "N/A")
        c4.metric("P/E Ratio", f"{fd['pe_ratio']:.2f}" if fd["pe_ratio"] else "N/A")
        c5.metric("P/B Ratio", f"{fd['pb_ratio']:.2f}" if fd["pb_ratio"] else "N/A")
        c6.metric("Fund House", fd.get("fund_house", "N/A")[:18] if fd.get("fund_house") else "N/A")

        st.markdown("---")

        # ── Return metrics ──
        ret = fd["returns"]
        rc1, rc2, rc3, rc4, rc5 = st.columns(5)
        for col, period in zip([rc1, rc2, rc3, rc4, rc5], ["6M", "1Y", "3Y", "5Y", "All-Time"]):
            val = ret.get(period)
            delta_str = f"{val:+.2f}%" if val is not None else None
            col.metric(
                f"{period} Return",
                f"{val:.2f}%" if val is not None else "N/A",
                delta=delta_str,
            )

        st.markdown("---")

        # ── Risk metrics ──
        rm1, rm2, rm3, rm4 = st.columns(4)
        rm1.metric("Alpha (3Y)", f"{fd['alpha']:+.3f}" if fd["alpha"] is not None else "N/A")
        rm2.metric("Beta (3Y)", f"{fd['beta']:.3f}" if fd["beta"] is not None else "N/A")
        rm3.metric("Sharpe (3Y)", f"{fd['sharpe']:.3f}" if fd["sharpe"] is not None else "N/A")
        rm4.metric("Sortino (3Y)", f"{fd['sortino']:.3f}" if fd["sortino"] is not None else "N/A")

        st.markdown("---")

        # ── NAV chart + sector allocation side by side ──
        ch1, ch2 = st.columns([3, 2])

        with ch1:
            nav_df = fd["nav_df"]
            if not nav_df.empty:
                window = st.select_slider(
                    "Chart window",
                    options=["6M", "1Y", "3Y", "5Y", "All"],
                    value="1Y",
                    key=f"window_{fd['scheme_code']}",
                )
                days_map = {"6M": 182, "1Y": 365, "3Y": 1095, "5Y": 1825, "All": 9999}
                days = days_map[window]
                cutoff = pd.Timestamp.today() - pd.Timedelta(days=days)

                nav_trim = nav_df[nav_df["date"] >= cutoff].copy()
                bench_trim = bench_df[bench_df["date"] >= cutoff].copy()

                if not nav_trim.empty:
                    rebased = an.rebase_nav(nav_trim)
                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatter(
                            x=rebased["date"],
                            y=rebased["rebased_nav"],
                            fill="tozeroy",
                            fillcolor=hex_to_rgba(BRAND_COLORS[idx % len(BRAND_COLORS)], alpha=0.08),
                            line=dict(color=accent, width=2),
                            name="Fund NAV",
                            hovertemplate="%{x|%d %b %Y}<br>%{y:.2f}<extra></extra>",
                        )
                    )
                    if not bench_trim.empty:
                        b_ref = bench_trim.iloc[0]["close"]
                        bench_trim["rebased"] = bench_trim["close"] / b_ref * 100
                        fig.add_trace(
                            go.Scatter(
                                x=bench_trim["date"],
                                y=bench_trim["rebased"],
                                line=dict(color="#ffffff", width=1, dash="dot"),
                                opacity=0.4,
                                name="Nifty 50",
                                hovertemplate="%{x|%d %b %Y}<br>%{y:.2f}<extra></extra>",
                            )
                        )
                    _dark_layout(fig, title=f"NAV Performance (rebased to 100)", height=300)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Historical NAV data unavailable.")

        with ch2:
            sectors = fd["sectors"]
            if sectors:
                fig_s = _build_sector_pie(sectors, fd["name"], idx)
                st.plotly_chart(fig_s, use_container_width=True)

        # ── Top holdings table ──
        st.markdown("**Top Holdings**")
        holdings = fd["holdings"]
        if not holdings.empty:
            disp = holdings[["stock_name", "sector", "weight_pct"]].copy()
            disp.columns = ["Stock", "Sector", "Weight (%)"]
            st.dataframe(disp, use_container_width=True, height=280, hide_index=True)
        else:
            st.info("Holdings data unavailable.")


# ─────────────────────────────────────────────────────────────────
# Overlap analysis section
# ─────────────────────────────────────────────────────────────────

def _render_overlap_section(fund_data_list: List[dict]):
    st.markdown(
        '<div class="section-header"><span>🔗 Portfolio Overlap Analysis</span></div>',
        unsafe_allow_html=True,
    )

    if len(fund_data_list) < 2:
        st.info("Add at least 2 funds to see overlap analysis.")
        return

    holdings_map = {fd["name"]: fd["holdings"] for fd in fund_data_list if not fd["holdings"].empty}

    if len(holdings_map) < 2:
        st.warning("Holdings data insufficient for overlap analysis.")
        return

    # Overlap heatmap
    labels = list(holdings_map.keys())
    fig_heat = _build_overlap_heatmap(holdings_map, labels)
    st.plotly_chart(fig_heat, use_container_width=True)

    # Common stocks table
    common_df = an.find_common_holdings(holdings_map)
    overlap_pcts = an.calc_overlap_concentration(holdings_map)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("**Common Holdings (stocks in 2+ funds)**")
        if not common_df.empty:
            disp = []
            for _, row in common_df.iterrows():
                w_str = " | ".join([f"{k[:18]}: {v:.1f}%" for k, v in row["weights"].items()])
                disp.append(
                    {
                        "Stock": row["stock_name"],
                        "Present in": f"{row['present_in_n_funds']} funds",
                        "Avg Weight (%)": f"{row['avg_weight_pct']:.2f}%",
                        "Fund Weights": w_str,
                    }
                )
            st.dataframe(pd.DataFrame(disp), use_container_width=True, height=320, hide_index=True)
        else:
            st.success("No common holdings detected across selected funds.")

    with col2:
        st.markdown("**Capital in Common Holdings (per fund)**")
        for fund_name, pct in overlap_pcts.items():
            short = fund_name[:35] + ("…" if len(fund_name) > 35 else "")
            colour = "#ff4d6d" if pct > 30 else "#ffd600" if pct > 15 else "#00ff9c"
            st.markdown(
                f"""
                <div style="background:#111c2e;border:1px solid #1e2d45;border-radius:10px;
                            padding:12px 16px;margin-bottom:10px;">
                  <div style="font-size:11px;color:#64748b;margin-bottom:4px;">{short}</div>
                  <div style="font-family:'Space Mono',monospace;font-size:20px;color:{colour};
                              font-weight:700;">{pct:.1f}%</div>
                  <div style="height:4px;background:#1e2d45;border-radius:2px;margin-top:8px;">
                    <div style="height:4px;width:{min(pct,100):.0f}%;
                                background:{colour};border-radius:2px;"></div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────────────────────
# Comparative charts section
# ─────────────────────────────────────────────────────────────────

def _render_compare_section(fund_data_list: List[dict], bench_df: pd.DataFrame):
    st.markdown(
        '<div class="section-header"><span>📈 Comparative Analysis</span></div>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["📉 Performance Chart", "📊 Returns Bar Chart", "🕸 Risk Radar"])

    with tab1:
        window = st.radio(
            "Time window",
            ["6M", "1Y", "3Y", "5Y", "All-Time"],
            index=1,
            horizontal=True,
            key="compare_window",
        )
        days_map = {"6M": 182, "1Y": 365, "3Y": 1095, "5Y": 1825, "All-Time": 9999}
        fig_nav = _build_nav_chart(fund_data_list, bench_df, window_days=days_map[window])
        st.plotly_chart(fig_nav, use_container_width=True)

    with tab2:
        fig_bar = _build_returns_bar(fund_data_list)
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab3:
        if len(fund_data_list) >= 2:
            fig_radar = _build_risk_radar(fund_data_list)
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("Add at least 2 funds to view the Risk Radar.")


# ─────────────────────────────────────────────────────────────────
# Main app
# ─────────────────────────────────────────────────────────────────

def main():
    _inject_css()

    # ── Hero banner ──
    st.markdown(
        f"""
        <div class="hero-banner">
          <p class="hero-title">{APP_ICON} {APP_TITLE}</p>
          <p class="hero-subtitle">{APP_SUBTITLE} · v1.0.0</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Load fund universe ──
    with st.spinner("Loading AMFI fund universe…"):
        all_funds_df = _cached_all_funds()

    # ── Sidebar – fund selection ──
    selected_codes = _render_sidebar(all_funds_df)

    if not selected_codes:
        st.info("👈 Select funds from the sidebar to begin analysis.")
        return

    # ── Load benchmark ──
    with st.spinner("Fetching Nifty 50 data…"):
        bench_df = _cached_benchmark()

    # ── Analyse each fund ──
    fund_data_list: List[dict] = []
    progress = st.progress(0, text="Analysing funds…")

    for i, code in enumerate(selected_codes):
        progress.progress((i + 1) / len(selected_codes), text=f"Fetching fund {i+1}/{len(selected_codes)}…")
        try:
            fd = _analyse_fund(code, bench_df)
            fund_data_list.append(fd)
        except Exception as exc:
            st.warning(f"Could not load fund {code}: {exc}")

    progress.empty()

    if not fund_data_list:
        st.error("No fund data could be loaded. Please check your network connection.")
        return

    # ── Top KPI strip ──
    st.markdown(
        '<div class="section-header"><span>⚡ Quick KPIs</span></div>',
        unsafe_allow_html=True,
    )
    kpi_cols = st.columns(min(len(fund_data_list), 5))
    for i, fd in enumerate(fund_data_list[:5]):
        with kpi_cols[i]:
            ret_1y = fd["returns"].get("1Y")
            delta = f"{ret_1y:+.2f}%" if ret_1y is not None else None
            st.metric(
                label=fd["name"][:28] + "…" if len(fd["name"]) > 28 else fd["name"],
                value=_fmt_nav(fd["current_nav"]),
                delta=delta,
            )

    # ── Summary table ──
    _render_summary_table(fund_data_list)

    # ── Comparative charts ──
    _render_compare_section(fund_data_list, bench_df)

    # ── Individual fund cards ──
    st.markdown(
        '<div class="section-header"><span>🏦 Individual Fund Deep Dive</span></div>',
        unsafe_allow_html=True,
    )
    for i, fd in enumerate(fund_data_list):
        _render_fund_card(fd, bench_df, idx=i)

    # ── Overlap analysis ──
    _render_overlap_section(fund_data_list)

    # ── Footer ──
    st.markdown("---")
    st.markdown(
        "<p style='text-align:center;color:#64748b;font-size:11px;'>"
        "Data sourced from AMFI (amfiindia.com) and mfapi.in. "
        "Holdings &amp; ratios are illustrative for demo purposes. "
        "Past performance is not indicative of future results. "
        "Not financial advice."
        "</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

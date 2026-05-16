"""Financial Dashboard Builder: local/hosted equity research dashboard."""

from __future__ import annotations

import math
import re
import traceback
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    import yfinance as yf
except Exception:
    yf = None

try:
    import requests
    from bs4 import BeautifulSoup
except Exception:
    requests = None
    BeautifulSoup = None



st.set_page_config(
    page_title="Financial Dashboard Builder",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DARK_CSS = """
<style>
:root {
  --bg: #060609;
  --surface: #0d0d14;
  --surface2: #12121c;
  --surface3: #181825;
  --border: rgba(255,255,255,0.08);
  --text: #e8e8f2;
  --muted: #8080a8;
  --up: #00e5a0;
  --down: #ff4d6d;
  --flat: #f7b955;
  --accent: #6c5ce7;
}
.stApp { background: var(--bg); color: var(--text); }
.block-container { padding-top: 7.25rem !important; max-width: 1480px; }
[data-testid="stSidebar"] { padding-top: 1rem; }
[data-testid="stMetricValue"] { color: var(--text); }
[data-testid="stMetricDelta"] { font-size: 0.85rem; }
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 12px;
}
.big-card {
  background: linear-gradient(135deg, rgba(108,92,231,.18), rgba(0,229,160,.08));
  border: 1px solid rgba(108,92,231,.35);
  border-radius: 16px;
  padding: 18px 20px;
  margin-bottom: 16px;
}
.ticker-badge {
  display: inline-block;
  background: var(--accent);
  padding: 4px 10px;
  border-radius: 6px;
  color: white;
  font-weight: 800;
  letter-spacing: 0.12em;
}
.subtle { color: var(--muted); font-size: 0.86rem; }
.good { color: var(--up); font-weight: 700; }
.bad { color: var(--down); font-weight: 700; }
.warn { color: var(--flat); font-weight: 700; }
.section-label {
  color: var(--muted);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: .1em;
  border-bottom: 1px solid var(--border);
  padding-bottom: 8px;
  margin: 20px 0 12px 0;
}
.small-table td, .small-table th { font-size: 0.85rem !important; }
hr { border-color: var(--border); }

/* Stronger dataframe readability */
[data-testid="stDataFrame"] {
  border-radius: 14px;
  overflow: hidden;
}


/* Terminal-style financial statement tables */
.fin-terminal-wrap {
  width: 100%;
  overflow-x: auto;
  border-radius: 12px;
  border: 1px solid rgba(162,155,254,.16);
  background: rgba(8,8,13,.92);
  box-shadow: 0 18px 50px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.04);
  margin: 8px 0 22px 0;
}
table.fin-terminal {
  width: 100%;
  border-collapse: collapse;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.86rem;
  color: #e8e8f2;
  table-layout: fixed;
}
.fin-terminal thead th {
  background: #12121c;
  color: #a29bfe;
  padding: 12px 14px;
  text-align: right;
  font-size: .74rem;
  text-transform: uppercase;
  letter-spacing: .13em;
  border-bottom: 1px solid rgba(162,155,254,.20);
  white-space: nowrap;
}
.fin-terminal thead th:first-child {
  text-align: left;
  width: 27%;
}
.fin-terminal tbody td {
  padding: 11px 14px;
  text-align: right;
  border-bottom: 1px solid rgba(255,255,255,.075);
  white-space: nowrap;
  font-weight: 650;
}
.fin-terminal tbody td:first-child {
  text-align: left;
  color: #9696bd;
  font-weight: 650;
  letter-spacing: .02em;
  padding-left: 24px;
}
.fin-terminal tbody tr.normal:hover td {
  background: rgba(255,255,255,.035);
}
.fin-terminal tbody tr.section-row td {
  background: linear-gradient(90deg, rgba(108,92,231,.18), rgba(18,18,28,.98));
  color: #a9a3df !important;
  font-size: .68rem;
  font-weight: 950 !important;
  text-transform: uppercase;
  letter-spacing: .18em;
  padding: 9px 14px 9px 16px;
  border-top: 1px solid rgba(162,155,254,.24);
  border-bottom: 1px solid rgba(162,155,254,.14);
}
.fin-terminal tbody tr.subtotal-row td {
  background: linear-gradient(90deg, rgba(108,92,231,.16), rgba(108,92,231,.055));
  color: #f1efff;
  font-weight: 900;
  border-top: 1px solid rgba(162,155,254,.22);
  border-bottom: 1px solid rgba(162,155,254,.15);
}
.fin-terminal tbody tr.subtotal-row td:first-child {
  color: #f1efff;
  padding-left: 16px;
}
.fin-terminal tbody tr.grand-row td {
  background: linear-gradient(90deg, rgba(108,92,231,.26), rgba(19,18,39,.82));
  color: #ffffff;
  font-weight: 1000;
  font-size: .92rem;
  border-top: 2px solid rgba(108,92,231,.75);
  border-bottom: 1px solid rgba(162,155,254,.28);
}
.fin-terminal tbody tr.grand-row td:first-child {
  color: #ffffff;
  padding-left: 16px;
  text-transform: uppercase;
  letter-spacing: .04em;
}
.fin-terminal tbody tr.grand-row td.current-period,
.fin-terminal tbody tr.grand-row td.margin-hot {
  color: #00e5a0 !important;
  text-shadow: 0 0 12px rgba(0,229,160,.08);
}
.fin-terminal td.current-period {
  color: #e8e8f2;
}
.fin-terminal .delta-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: .78rem;
  font-weight: 900;
  line-height: 1.05;
}
.fin-terminal .delta-pos {
  color: #00e5a0;
  background: rgba(0,229,160,.12);
}
.fin-terminal .delta-neg {
  color: #ff4d6d;
  background: rgba(255,77,109,.13);
}
.fin-terminal .delta-neu {
  color: #f7b955;
  background: rgba(247,185,85,.12);
}
@media (max-width: 900px) {
  table.fin-terminal { font-size: .76rem; min-width: 980px; }
  .fin-terminal thead th { font-size: .64rem; padding: 10px 9px; }
  .fin-terminal tbody td { padding: 9px 9px; }
}



/* Projection matrix page — matched to main financial table theme */
.proj-case-card {
  background: rgba(8,8,13,.94);
  border: 1px solid rgba(162,155,254,.16);
  border-radius: 14px;
  padding: 14px 14px 12px 14px;
  margin: 10px 0 18px 0;
  box-shadow: 0 18px 50px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.04);
}
.proj-case-card.base {
  border-top: 2px solid rgba(108,92,231,.85);
}
.proj-case-card.bull {
  border-top: 2px solid rgba(0,229,160,.72);
}
.proj-case-card.bear {
  border-top: 2px solid rgba(255,77,109,.72);
}
.proj-case-chip {
  display: inline-block;
  font-weight: 950;
  letter-spacing: .13em;
  font-size: .82rem;
  padding: 7px 13px;
  border-radius: 7px;
  color: #f6f4ff;
  margin-bottom: 10px;
  text-transform: uppercase;
  border: 1px solid rgba(255,255,255,.10);
}
.proj-case-chip.base {
  background: linear-gradient(90deg, rgba(108,92,231,.95), rgba(108,92,231,.58));
}
.proj-case-chip.bull {
  background: linear-gradient(90deg, rgba(0,229,160,.86), rgba(0,206,201,.36));
  color: #05140f;
}
.proj-case-chip.bear {
  background: linear-gradient(90deg, rgba(255,77,109,.88), rgba(255,77,109,.40));
}
.proj-case-note {
  color: #9696bd;
  font-size: .86rem;
  margin: 0 0 10px 2px;
}
.proj-table-wrap {
  width: 100%;
  overflow-x: auto;
  border-radius: 11px;
  border: 1px solid rgba(162,155,254,.14);
  background: rgba(8,8,13,.92);
}
table.proj-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: #e8e8f2;
  font-size: .86rem;
}
.proj-table th,
.proj-table td {
  border-right: 1px solid rgba(255,255,255,.075);
  border-bottom: 1px solid rgba(255,255,255,.075);
  padding: 10px 12px;
  text-align: right;
  background: rgba(7,7,12,.72);
  font-weight: 750;
  white-space: nowrap;
}
.proj-table thead th {
  background: #12121c;
  color: #a29bfe;
  font-size: .74rem;
  font-weight: 950;
  text-transform: uppercase;
  letter-spacing: .13em;
  border-bottom: 1px solid rgba(162,155,254,.22);
}
.proj-table th:first-child,
.proj-table td.metric-col {
  text-align: left;
  width: 205px;
}
.proj-table td.metric-col {
  background: linear-gradient(90deg, rgba(108,92,231,.18), rgba(18,18,28,.98));
  color: #a9a3df;
  font-weight: 950;
  letter-spacing: .08em;
  text-transform: uppercase;
  font-size: .76rem;
}
.proj-table tr.core-row td:not(.metric-col) {
  background: rgba(8,8,13,.92);
  color: #f1efff;
  font-weight: 850;
}
.proj-table tr.price-row td:not(.metric-col) {
  background: linear-gradient(90deg, rgba(108,92,231,.26), rgba(19,18,39,.82));
  color: #00e5a0;
  font-weight: 1000;
  text-shadow: 0 0 12px rgba(0,229,160,.08);
  border-top: 2px solid rgba(108,92,231,.72);
}
.proj-table tr.price-row td.metric-col {
  background: linear-gradient(90deg, rgba(108,92,231,.28), rgba(19,18,39,.98));
  color: #ffffff;
  border-top: 2px solid rgba(108,92,231,.72);
}
.proj-table tr.cagr-row td:not(.metric-col) {
  background: linear-gradient(90deg, rgba(0,229,160,.13), rgba(108,92,231,.08));
  color: #00e5a0;
  font-weight: 1000;
}
.proj-table tr.cagr-row td.metric-col {
  background: linear-gradient(90deg, rgba(0,229,160,.12), rgba(18,18,28,.98));
  color: #c7fff0;
}
.proj-table tbody tr:hover td:not(.metric-col) {
  background-color: rgba(255,255,255,.035);
  filter: brightness(1.06);
}
.proj-case-card.bear .proj-table tr.price-row td:not(.metric-col),
.proj-case-card.bear .proj-table tr.cagr-row td:not(.metric-col) {
  color: #ff6f8a;
}
.proj-case-card.bear .proj-table tr.cagr-row td.metric-col {
  color: #ffd3dc;
  background: linear-gradient(90deg, rgba(255,77,109,.13), rgba(18,18,28,.98));
}
@media (max-width: 900px) {
  table.proj-table { min-width: 1050px; font-size: .78rem; }
  .proj-table th, .proj-table td { padding: 9px 8px; }
}

</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)



def fmt_money_m(x: Any) -> str:
    if pd.isna(x):
        return "—"
    try:
        x = float(x)
    except Exception:
        return str(x)
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1000:
        return f"{sign}${x/1000:,.2f}B"
    return f"{sign}${x:,.0f}M"


def fmt_money_b(x: Any) -> str:
    if pd.isna(x):
        return "—"
    try:
        return f"${float(x):,.2f}B"
    except Exception:
        return str(x)


def fmt_pct(x: Any, decimals: int = 1) -> str:
    if pd.isna(x):
        return "—"
    try:
        return f"{float(x):+.{decimals}f}%"
    except Exception:
        return str(x)


def safe_div(a: float, b: float) -> float:
    return np.nan if b in (0, None) or pd.isna(b) else a / b


def calc_cagr(start: float, end: float, years: float) -> float:
    if start <= 0 or end <= 0 or years <= 0:
        return np.nan
    return (end / start) ** (1 / years) - 1


def style_delta(val: float) -> str:
    if pd.isna(val):
        return "—"
    arrow = "▲" if val >= 0 else "▼"
    cls = "good" if val >= 0 else "bad"
    return f'<span class="{cls}">{arrow} {val:+.1f}%</span>'


def classify_table_row(row: pd.Series) -> str:
    """Classify dashboard table rows for visual styling."""
    line_item = str(row.get("Line Item", "")).strip()
    if not line_item:
        return "normal"

    value_cols = [c for c in row.index if c != "Line Item"]
    empty_values = all(str(row.get(c, "")).strip() in ("", "—", "nan", "None") for c in value_cols)
    upper = line_item.upper()

    # Only rows with no financial values should become full-width section bands.
    # All-caps rows that contain values are real financial line items, not section headers.
    if empty_values:
        return "section"

    grand_rows = {
        "TOTAL REVENUE",
        "GROSS PROFIT",
        "GAAP OPERATING INCOME",
        "GAAP NET INCOME",
        "NET CASH FROM OPERATIONS",
        "ADJUSTED FREE CASH FLOW",
        "NET CHANGE IN CASH",
        "TOTAL ASSETS",
        "TOTAL LIABILITIES",
        "TOTAL STOCKHOLDERS' EQUITY",
        "TOTAL LIABILITIES & EQUITY",
    }
    if upper in grand_rows:
        return "grand"

    subtotal_rows = {
        "TOTAL U.S. REVENUE",
        "TOTAL INTERNATIONAL REVENUE",
        "TOTAL OPERATING EXPENSES",
        "TOTAL CASH & TREASURIES",
        "TOTAL CURRENT ASSETS",
        "NET CASH FROM INVESTING",
        "NET CASH FROM FINANCING",
        "GAAP FREE CASH FLOW",
    }
    if upper.startswith("TOTAL RETURNS") or upper in subtotal_rows or (upper.startswith("TOTAL ") and upper not in grand_rows):
        return "subtotal"

    return "normal"


def color_delta_cells(val: Any) -> str:
    """Color percent-change cells by sign for faster scanning."""
    text = str(val).strip()
    if not text or text == "—":
        return "color: #8080a8;"
    if text.startswith("+"):
        return "color: #00e5a0; font-weight: 800;"
    if text.startswith("-"):
        return "color: #ff4d6d; font-weight: 800;"
    return "color: #e8e8f2;"


def style_financial_rows(row: pd.Series) -> List[str]:
    """Streamlit/Pandas Styler row styles for the dashboard tables."""
    kind = classify_table_row(row)
    n = len(row)

    if kind == "section":
        return [
            "background: linear-gradient(90deg, rgba(108,92,231,.35), rgba(108,92,231,.08)); "
            "color: #cfc9ff; font-weight: 900; text-transform: uppercase; "
            "letter-spacing: .08em; border-top: 1px solid rgba(162,155,254,.45); "
            "border-bottom: 1px solid rgba(162,155,254,.35);"
        ] * n

    if kind == "grand":
        return [
            "background: linear-gradient(90deg, rgba(0,229,160,.20), rgba(0,229,160,.05)); "
            "color: #00e5a0; font-weight: 900; border-top: 1px solid rgba(0,229,160,.35); "
            "border-bottom: 1px solid rgba(0,229,160,.22);"
        ] * n

    if kind == "subtotal":
        return [
            "background: rgba(247,185,85,.10); color: #f7d58a; font-weight: 800; "
            "border-top: 1px solid rgba(247,185,85,.22);"
        ] * n

    return ["background: rgba(255,255,255,0.00); color: #e8e8f2;"] * n


def display_df(df: pd.DataFrame, height: Optional[int] = None, style_rows: bool = True) -> None:
    """Display a dataframe with dashboard-friendly styling."""
    dataframe_kwargs = {"use_container_width": True}
    if height is not None:
        dataframe_kwargs["height"] = height

    if style_rows and "Line Item" in df.columns:
        styled = (
            df.style
            .apply(style_financial_rows, axis=1)
            .set_properties(**{
                "font-family": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                "font-size": "0.86rem",
                "border-color": "rgba(255,255,255,.08)",
            })
            .set_properties(subset=["Line Item"], **{
                "font-weight": "800",
                "text-align": "left",
                "min-width": "260px",
            })
            .set_table_styles([
                {"selector": "thead th", "props": [
                    ("background", "#181825"),
                    ("color", "#a29bfe"),
                    ("font-weight", "900"),
                    ("text-transform", "uppercase"),
                    ("letter-spacing", ".06em"),
                    ("border-bottom", "1px solid rgba(162,155,254,.35)"),
                ]},
                {"selector": "tbody td", "props": [("padding", "8px 10px")]},
            ])
        )

        delta_cols = [c for c in ["YoY Δ", "QoQ Δ", "Upside / Downside", "Price CAGR"] if c in df.columns]
        if delta_cols:
            if hasattr(styled, "map"):
                styled = styled.map(color_delta_cells, subset=delta_cols)
            else:
                styled = styled.applymap(color_delta_cells, subset=delta_cols)

        st.dataframe(styled, **dataframe_kwargs)
    else:
        st.dataframe(df, **dataframe_kwargs)


def _html_escape(value: Any) -> str:
    import html
    return html.escape("" if value is None else str(value))


def _delta_badge(value: Any) -> str:
    text = str(value).strip()
    if not text or text == "—":
        return "—"
    cleaned = text.replace("%", "").replace("+", "").strip()
    try:
        num = float(cleaned)
    except Exception:
        num = 0.0
    if text.startswith("+") or num > 0:
        return f'<span class="delta-badge delta-pos">▲ {_html_escape(text)}</span>'
    if text.startswith("-") or num < 0:
        return f'<span class="delta-badge delta-neg">▼ {_html_escape(text)}</span>'
    return f'<span class="delta-badge delta-neu">{_html_escape(text)}</span>'


def render_financial_table(df: pd.DataFrame, height: Optional[int] = None) -> None:
    """Render a custom HTML financial statement table closer to the original dashboard aesthetic."""
    columns = list(df.columns)
    html_parts = ['<div class="fin-terminal-wrap">', '<table class="fin-terminal">', '<thead><tr>']
    for c in columns:
        html_parts.append(f'<th>{_html_escape(c)}</th>')
    html_parts.append('</tr></thead><tbody>')

    for _, row in df.iterrows():
        kind = classify_table_row(row)
        label = str(row.get("Line Item", "")).strip()
        if kind == "section":
            html_parts.append(f'<tr class="section-row"><td colspan="{len(columns)}">{_html_escape(label)}</td></tr>')
            continue

        cls = "grand-row" if kind == "grand" else "subtotal-row" if kind == "subtotal" else "normal"
        html_parts.append(f'<tr class="{cls}">')
        for c in columns:
            val = row.get(c, "")
            td_cls = []
            if c == "Q1 2026":
                td_cls.append("current-period")
            if c in ["Q1'26 Margin", "Q1’26 Margin"] and kind == "grand":
                td_cls.append("margin-hot")
            class_attr = f' class="{" ".join(td_cls)}"' if td_cls else ""
            if c in ["YoY Δ", "QoQ Δ", "Upside / Downside", "Price CAGR"]:
                content = _delta_badge(val)
            else:
                content = _html_escape(val)
            html_parts.append(f'<td{class_attr}>{content}</td>')
        html_parts.append('</tr>')

    html_parts.append('</tbody></table></div>')
    st.markdown(''.join(html_parts), unsafe_allow_html=True)


@st.cache_data(ttl=60 * 30, show_spinner=False)
def get_market_data(ticker: str) -> Dict[str, Any]:
    """Fetch quote/analyst/insider data. Gracefully degrade if unavailable."""
    result: Dict[str, Any] = {
        "ticker": ticker.upper(),
        "quote": {},
        "history": pd.DataFrame(),
        "analyst_price_targets": pd.DataFrame(),
        "recommendations": pd.DataFrame(),
        "recommendation_summary": pd.DataFrame(),
        "insider_transactions": pd.DataFrame(),
        "insider_roster": pd.DataFrame(),
        "errors": [],
    }
    if yf is None:
        result["errors"].append("yfinance is not installed. Run: pip install yfinance")
        return result

    try:
        t = yf.Ticker(ticker)
        try:
            fi = getattr(t, "fast_info", {}) or {}
            info = getattr(t, "info", {}) or {}
            result["quote"] = {
                "last_price": fi.get("last_price") or info.get("currentPrice") or info.get("regularMarketPrice"),
                "market_cap": fi.get("market_cap") or info.get("marketCap"),
                "previous_close": fi.get("previous_close") or info.get("previousClose"),
                "trailing_pe": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "shares": fi.get("shares") or info.get("sharesOutstanding"),
                "currency": info.get("currency", "USD"),
                "long_name": info.get("longName") or info.get("shortName") or ticker.upper(),
            }
        except Exception as e:
            result["errors"].append(f"Quote fetch failed: {e}")

        try:
            hist = t.history(period="5y", interval="1d", auto_adjust=True)
            if isinstance(hist, pd.DataFrame):
                result["history"] = hist.reset_index()
        except Exception as e:
            result["errors"].append(f"Price history fetch failed: {e}")

        # Analyst price targets can be a dict or DataFrame depending on yfinance version.
        try:
            apt = getattr(t, "analyst_price_targets", None)
            if isinstance(apt, dict):
                result["analyst_price_targets"] = pd.DataFrame([apt])
            elif isinstance(apt, pd.DataFrame):
                result["analyst_price_targets"] = apt.reset_index()
        except Exception as e:
            result["errors"].append(f"Analyst price target fetch failed: {e}")

        # Recommendation trend / ratings.
        for attr_name, out_key in [
            ("recommendations", "recommendations"),
            ("recommendations_summary", "recommendation_summary"),
        ]:
            try:
                obj = getattr(t, attr_name, None)
                if isinstance(obj, pd.DataFrame):
                    result[out_key] = obj.reset_index()
            except Exception as e:
                result["errors"].append(f"{attr_name} fetch failed: {e}")

        # Insider data: yfinance attributes vary by version.
        for attr_name, out_key in [
            ("insider_transactions", "insider_transactions"),
            ("insider_purchases", "insider_roster"),
            ("insiders", "insider_roster"),
        ]:
            try:
                obj = getattr(t, attr_name, None)
                if isinstance(obj, pd.DataFrame) and not obj.empty:
                    result[out_key] = obj.reset_index()
            except Exception as e:
                result["errors"].append(f"{attr_name} fetch failed: {e}")
    except Exception as e:
        result["errors"].append(f"Ticker object failed: {e}\n{traceback.format_exc(limit=1)}")

    return result


TICKER_DEFAULT = "PLTR"
COMPANY_NAME = "Selected Company"
REPORT_DATE = "Financial Dashboard Builder · USD unless noted"

KPI_DATA = [
    ("Revenue Q1'26", "$1,633M", "+84.7% YoY"),
    ("Gross Profit", "$1,417M", "+99.3% YoY"),
    ("GAAP Op. Income", "$754M", "+328.3% YoY"),
    ("GAAP Net Income", "$871M", "+306.7% YoY"),
    ("Adj. FCF", "$925M", "57% margin"),
    ("Rule of 40", "145%", "+18pp QoQ"),
]

income_rows = [
    ("REVENUE BREAKDOWN", None, None, None, None),
    ("U.S. Government Revenue", 373, 435, 687, "revenue"),
    ("U.S. Commercial Revenue", 255, 372, 595, "revenue"),
    ("Total U.S. Revenue", 628, 807, 1282, "subtotal"),
    ("International Government", 196, 178, 224, "revenue"),
    ("International Commercial", 60, 72, 127, "revenue"),
    ("Total International Revenue", 256, 250, 351, "subtotal"),
    ("TOTAL REVENUE", 884, 827, 1633, "grand"),
    ("GROSS PROFIT & COST OF REVENUE", None, None, None, None),
    ("Cost of Revenue", 173, 190, 216, "cost"),
    ("GROSS PROFIT", 711, 637, 1417, "grand"),
    ("OPERATING EXPENSES", None, None, None, None),
    ("Sales & Marketing", 182, 165, 244, "cost"),
    ("Research & Development", 113, 108, 141, "cost"),
    ("General & Administrative", 240, 221, 278, "cost"),
    ("Total Operating Expenses", 535, 494, 663, "subtotal"),
    ("GAAP OPERATING INCOME", 176, 143, 754, "grand"),
    ("NON-GAAP & BELOW THE LINE", None, None, None, None),
    ("Adj. Op. Income (ex-SBC)", 388, 403, 984, "grand"),
    ("Interest & Other Income", 60, 68, 83, "revenue"),
    ("Income Tax Provision", -23, -28, -34, "cost"),
    ("GAAP Diluted EPS", 0.08, 0.07, 0.34, "eps"),
    ("Adj. Diluted EPS", 0.13, 0.14, 0.33, "eps"),
    ("GAAP NET INCOME", 214, 187, 871, "grand"),
    ("SHAREHOLDER RETURNS", None, None, None, None),
    ("Total Returns (Divs + Buybacks)", 1770, 2440, 519, "subtotal"),
]

balance_rows = [
    ("CURRENT ASSETS", None, None, None),
    ("Cash & Cash Equivalents", 993, 1872, 2291),
    ("Short-Term U.S. Treasuries", 4284, 5371, 5709),
    ("Total Cash & Treasuries", 5277, 7243, 8000),
    ("Accounts Receivable, net", 282, 744, 501),
    ("Deferred Revenue (current asset table line)", 136, 183, 204),
    ("Prepaid & Other Current", 107, 121, 138),
    ("Total Current Assets", 5802, 8291, 8843),
    ("NON-CURRENT ASSETS", None, None, None),
    ("Property & Equipment, net", 68, 72, 74),
    ("Operating Lease ROU Assets", 196, 182, 178),
    ("Goodwill & Intangibles", 54, 51, 48),
    ("Other Non-Current Assets", 143, 161, 169),
    ("TOTAL ASSETS", 6263, 8757, 9312),
    ("LIABILITIES", None, None, None),
    ("Accounts Payable", 18, 26, 22),
    ("Accrued Liabilities", 198, 401, 231),
    ("Deferred Revenue (current)", 136, 183, 204),
    ("Customer Deposits", 62, 71, 88),
    ("Operating Lease (current)", 57, 60, 62),
    ("Operating Lease (non-current)", 162, 144, 138),
    ("Other Non-Current Liabilities", 583, 720, 895),
    ("TOTAL LIABILITIES", 1216, 1605, 1640),
    ("SHAREHOLDERS' EQUITY", None, None, None),
    ("Common Stock & APIC", 9168, 10419, 10858),
    ("Accumulated Deficit", -4183, -3340, -2267),
    ("Accumulated OCI", 62, 73, 81),
    ("TOTAL STOCKHOLDERS' EQUITY", 5047, 7152, 8672),
    ("TOTAL LIABILITIES & EQUITY", 6263, 8757, 9312),
]

cash_rows = [
    ("OPERATING ACTIVITIES", None, None, None),
    ("GAAP Net Income", 214, 187, 871),
    ("Stock-Based Compensation", 212, 260, 230),
    ("Depreciation & Amortization", 26, 26, 27),
    ("Changes in Working Capital", -142, 347, -229),
    ("— Accounts Receivable", -68, -344, 244),
    ("— Deferred Revenue", 89, 62, 54),
    ("Other Operating Adjustments", 0, 12, -44),
    ("NET CASH FROM OPERATIONS", 310, 832, 899),
    ("INVESTING ACTIVITIES", None, None, None),
    ("CapEx", -6, -7, -7),
    ("Purchases of U.S. Treasuries", -1829, -2041, -2388),
    ("Maturities of U.S. Treasuries", 1559, 1682, 2051),
    ("Net Cash from Investing", -318, -384, -358),
    ("FINANCING ACTIVITIES", None, None, None),
    ("Proceeds from Stock Options", 52, 41, 38),
    ("Tax Withholding on RSUs", -24, -77, -168),
    ("Net Cash from Financing", 21, -44, -138),
    ("FREE CASH FLOW SUMMARY", None, None, None),
    ("Cash from Operations", 310, 832, 899),
    ("Less: CapEx", -6, -7, -7),
    ("GAAP Free Cash Flow", 304, 825, 892),
    ("ADJUSTED FREE CASH FLOW", 373, 742, 925),
    ("NET CHANGE IN CASH", 13, 404, 403),
]

annual_metrics = pd.DataFrame(
    {
        "Year": ["FY2021", "FY2022", "FY2023", "FY2024", "FY2025", "FY2026E"],
        "Revenue": [1527, 1906, 2225, 2866, 4475, 7656],
        "Gross Profit": [1000, 1470, 1790, 2300, 3690, np.nan],
        "Adj. Op. Income": [308, 421, 633, 970, 2060, np.nan],
        "Adj. FCF": [321, 203, 697, 983, 2060, 4300],
        "GAAP Net Income": [-520, -374, 210, 462, 871, np.nan],
        "Revenue Growth %": [np.nan, 24.8, 16.8, 28.8, 56.2, 71.1],
        "Adj. Op Margin %": [20.2, 22.1, 28.4, 33.8, 46.0, np.nan],
        "FCF Margin %": [21.0, 10.7, 31.3, 34.3, 46.0, 56.0],
    }
)

segments = pd.DataFrame(
    {
        "Segment": ["U.S. Government", "U.S. Commercial", "International Government", "International Commercial"],
        "Q1 2025": [373, 255, 196, 60],
        "Q1 2026": [687, 595, 224, 127],
    }
)
segments["YoY Growth %"] = (segments["Q1 2026"] / segments["Q1 2025"] - 1) * 100
segments["Q1 2026 Mix %"] = segments["Q1 2026"] / segments["Q1 2026"].sum() * 100

GUIDANCE = pd.DataFrame(
    [
        ("Q2 2026 Revenue", "$1.797–1.801B", "+10% QoQ; above prior consensus in source dashboard"),
        ("FY2026 Revenue", "$7.650–7.662B", "+71% YoY; +10% vs prior guide"),
        ("FY2026 Adj. FCF", "$4.2–4.4B", "Raised from $3.93–4.13B"),
        ("U.S. Commercial FY2026", "≥$3.224B", "≥+120% YoY growth"),
    ],
    columns=["Metric", "Guidance", "Commentary"],
)

def statement_df(rows: List[Tuple], include_margins: bool = True) -> pd.DataFrame:
    out = []
    total_rev_q1_25 = 884
    total_rev_q1_26 = 1633
    for row in rows:
        name, q1_25, q4_25, q1_26, *rest = row
        if q1_25 is None:
            out.append({"Line Item": name, "Q1 2025": "", "Q4 2025": "", "Q1 2026": "", "YoY Δ": "", "QoQ Δ": "", "Q1'26 Margin": "", "Q1'25 Margin": ""})
            continue
        yoy = safe_div(q1_26, q1_25) - 1 if q1_25 != 0 else np.nan
        qoq = safe_div(q1_26, q4_25) - 1 if q4_25 != 0 else np.nan
        out.append(
            {
                "Line Item": name,
                "Q1 2025": f"${q1_25:,.2f}" if abs(q1_25) < 1 else fmt_money_m(q1_25),
                "Q4 2025": f"${q4_25:,.2f}" if abs(q4_25) < 1 else fmt_money_m(q4_25),
                "Q1 2026": f"${q1_26:,.2f}" if abs(q1_26) < 1 else fmt_money_m(q1_26),
                "YoY Δ": fmt_pct(yoy * 100),
                "QoQ Δ": fmt_pct(qoq * 100),
                "Q1'26 Margin": f"{safe_div(q1_26, total_rev_q1_26)*100:.1f}%" if include_margins and abs(q1_26) >= 1 else "—",
                "Q1'25 Margin": f"{safe_div(q1_25, total_rev_q1_25)*100:.1f}%" if include_margins and abs(q1_25) >= 1 else "—",
            }
        )
    return pd.DataFrame(out)


def simple_statement_df(rows: List[Tuple[str, Optional[float], Optional[float], Optional[float]]]) -> pd.DataFrame:
    out = []
    for name, q1_25, q4_25, q1_26 in rows:
        if q1_25 is None:
            out.append({"Line Item": name, "Q1 2025": "", "Q4 2025": "", "Q1 2026": "", "YoY Δ": "", "QoQ Δ": ""})
        else:
            yoy = safe_div(q1_26, q1_25) - 1 if q1_25 != 0 else np.nan
            qoq = safe_div(q1_26, q4_25) - 1 if q4_25 != 0 else np.nan
            out.append({"Line Item": name, "Q1 2025": fmt_money_m(q1_25), "Q4 2025": fmt_money_m(q4_25), "Q1 2026": fmt_money_m(q1_26), "YoY Δ": fmt_pct(yoy*100), "QoQ Δ": fmt_pct(qoq*100)})
    return pd.DataFrame(out)



def _clamp(value: float, low: float, high: float) -> float:
    if pd.isna(value):
        return low
    return max(low, min(high, float(value)))


def _historical_revenue_cagr_from_fundamentals(fundamentals: Dict[str, Any]) -> float:
    """Return revenue CAGR as a decimal from available annual yfinance history."""
    annual = build_live_annual_metrics(fundamentals)
    if annual is None or annual.empty or "Revenue" not in annual.columns:
        return np.nan

    clean = annual.dropna(subset=["Revenue"]).copy()
    clean = clean[clean["Revenue"] > 0]
    if len(clean) < 2:
        return np.nan

    start = float(clean["Revenue"].iloc[0])
    end = float(clean["Revenue"].iloc[-1])
    years = max(len(clean) - 1, 1)
    return calc_cagr(start, end, years)


def _recent_revenue_growth_from_fundamentals(fundamentals: Dict[str, Any]) -> float:
    """Return latest fiscal-year revenue growth as a decimal."""
    annual = build_live_annual_metrics(fundamentals)
    if annual is None or annual.empty or "Revenue" not in annual.columns:
        return np.nan

    clean = annual.dropna(subset=["Revenue"]).copy()
    clean = clean[clean["Revenue"] > 0]
    if len(clean) < 2:
        return np.nan

    prev = float(clean["Revenue"].iloc[-2])
    latest = float(clean["Revenue"].iloc[-1])
    return safe_div(latest, prev) - 1 if prev else np.nan


def get_default_projection_assumptions(
    current_price: float,
    fundamentals: Optional[Dict[str, Any]] = None,
    anchor: Optional[Dict[str, float]] = None,
    quote: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Build ticker-specific scenario assumptions from current valuation and historical growth."""
    fundamentals = fundamentals or {}
    quote = quote or {}
    anchor = anchor or {}

    hist_cagr = _historical_revenue_cagr_from_fundamentals(fundamentals)
    recent_growth = _recent_revenue_growth_from_fundamentals(fundamentals)

    if pd.isna(hist_cagr) and not pd.isna(recent_growth):
        base_growth = recent_growth
    elif pd.isna(recent_growth) and not pd.isna(hist_cagr):
        base_growth = hist_cagr
    elif not pd.isna(hist_cagr) and not pd.isna(recent_growth):
        base_growth = 0.60 * hist_cagr + 0.40 * recent_growth
    else:
        base_growth = 0.10

    base_growth = _clamp(base_growth, -0.05, 0.35)
    bear_growth = _clamp(base_growth * 0.45, -0.10, 0.18)
    bull_growth = _clamp(base_growth * 1.55 + 0.03, 0.03, 0.55)

    current_margin = float(anchor.get("net_margin", np.nan))
    if pd.isna(current_margin):
        current_margin = 0.10

    # Terminal margins move from current economics, but stay in realistic broad bounds.
    bear_margin = _clamp(current_margin * 0.75, -0.05, 0.30)
    base_margin = _clamp(current_margin + 0.04, 0.03, 0.35)
    bull_margin = _clamp(current_margin + 0.09, 0.06, 0.45)

    current_pe = anchor.get("current_pe", np.nan)
    forward_pe = quote.get("forward_pe") if isinstance(quote, dict) else np.nan
    trailing_pe = quote.get("trailing_pe") if isinstance(quote, dict) else np.nan

    pe_anchor_candidates = [x for x in [forward_pe, trailing_pe, current_pe] if x is not None and not pd.isna(x) and float(x) > 0]
    if pe_anchor_candidates:
        pe_anchor = float(pe_anchor_candidates[0])
    else:
        # Growth-sensitive fallback: mature low-growth names should not get software-style multiples.
        pe_anchor = 14 + max(base_growth, 0) * 85

    pe_anchor = _clamp(pe_anchor, 6, 90)

    # Terminal multiples are anchored to growth and current valuation, with compression built in.
    growth_multiple_base = 14 + max(base_growth, 0) * 95
    growth_multiple_bear = 10 + max(bear_growth, 0) * 65
    growth_multiple_bull = 18 + max(bull_growth, 0) * 110

    base_pe_mid = _clamp(0.55 * pe_anchor + 0.45 * growth_multiple_base, 8, 70)
    bear_pe_mid = _clamp(min(base_pe_mid * 0.65, growth_multiple_bear), 5, 45)
    bull_pe_mid = _clamp(max(base_pe_mid * 1.25, growth_multiple_bull), 12, 95)

    return pd.DataFrame(
        [
            {
                "Case": "Base",
                "Revenue Growth %": round(base_growth * 100, 1),
                "Terminal Net Margin %": round(base_margin * 100, 1),
                "Terminal PE Low": round(base_pe_mid * 0.85, 1),
                "Terminal PE High": round(base_pe_mid * 1.15, 1),
            },
            {
                "Case": "Bull",
                "Revenue Growth %": round(bull_growth * 100, 1),
                "Terminal Net Margin %": round(bull_margin * 100, 1),
                "Terminal PE Low": round(bull_pe_mid * 0.90, 1),
                "Terminal PE High": round(bull_pe_mid * 1.20, 1),
            },
            {
                "Case": "Bear",
                "Revenue Growth %": round(bear_growth * 100, 1),
                "Terminal Net Margin %": round(bear_margin * 100, 1),
                "Terminal PE Low": round(bear_pe_mid * 0.80, 1),
                "Terminal PE High": round(bear_pe_mid * 1.05, 1),
            },
        ]
    )


def _ttm_sum(raw: pd.DataFrame, possible_names: List[str]) -> float:
    if raw is None or raw.empty:
        return np.nan
    cols = list(raw.columns)
    try:
        cols = sorted(cols, key=lambda c: pd.to_datetime(c), reverse=True)
    except Exception:
        pass
    values = [_get_statement_value(raw, possible_names, c) for c in cols[:4]]
    values = [v for v in values if not pd.isna(v)]
    return float(sum(values)) if values else np.nan


def _latest_statement_value(raw: pd.DataFrame, possible_names: List[str]) -> float:
    if raw is None or raw.empty:
        return np.nan
    cols = list(raw.columns)
    try:
        cols = sorted(cols, key=lambda c: pd.to_datetime(c), reverse=True)
    except Exception:
        pass
    if not cols:
        return np.nan
    return _get_statement_value(raw, possible_names, cols[0])



def _shareholder_return_components(cashflow_raw: pd.DataFrame, col: Any) -> Tuple[float, float, float]:
    """Return dividends, buybacks, and total shareholder returns for a cash-flow period."""
    if cashflow_raw is None or cashflow_raw.empty or col is None:
        return np.nan, np.nan, np.nan

    dividends = _get_statement_value(
        cashflow_raw,
        ["Cash Dividends Paid", "Common Stock Dividend Paid", "Cash Dividend Paid"],
        col,
    )
    buybacks = _get_statement_value(
        cashflow_raw,
        ["Repurchase Of Capital Stock", "Repurchase Of Stock", "Stock Repurchase", "Repurchase Of Common Stock"],
        col,
    )

    div_abs = abs(dividends) if not pd.isna(dividends) else 0.0
    buyback_abs = abs(buybacks) if not pd.isna(buybacks) else 0.0
    total = div_abs + buyback_abs
    if total == 0:
        total = np.nan
    return div_abs, buyback_abs, total


def _shareholder_return_summary_from_cashflow(fundamentals: Dict[str, Any]) -> Tuple[float, float, float]:
    """Latest-quarter shareholder returns: dividends + buybacks."""
    cashflow = fundamentals.get("cashflow", pd.DataFrame()) if isinstance(fundamentals, dict) else pd.DataFrame()
    if cashflow is None or cashflow.empty:
        return np.nan, np.nan, np.nan
    cols = list(cashflow.columns)
    try:
        cols = sorted(cols, key=lambda c: pd.to_datetime(c), reverse=True)
    except Exception:
        pass
    latest_col = cols[0] if cols else None
    return _shareholder_return_components(cashflow, latest_col)



def get_projection_anchor(
    fundamentals: Dict[str, Any],
    quote: Dict[str, Any],
    fallback_revenue_b: float,
    fallback_shares_b: float,
    current_price: float,
) -> Dict[str, float]:
    income = fundamentals.get("income", pd.DataFrame()) if isinstance(fundamentals, dict) else pd.DataFrame()

    revenue_ttm_raw = _ttm_sum(income, ["Total Revenue", "Operating Revenue"])
    net_income_ttm_raw = _ttm_sum(income, ["Net Income", "Net Income Common Stockholders"])
    eps_ttm = _ttm_sum(income, ["Diluted EPS", "Diluted EPS Diluted"])
    diluted_shares_raw = _latest_statement_value(income, ["Diluted Average Shares", "Basic Average Shares"])

    revenue_b = revenue_ttm_raw / 1_000_000_000 if not pd.isna(revenue_ttm_raw) and revenue_ttm_raw > 0 else fallback_revenue_b
    net_income_b = net_income_ttm_raw / 1_000_000_000 if not pd.isna(net_income_ttm_raw) else np.nan

    shares_from_quote_b = quote.get("shares") / 1_000_000_000 if quote.get("shares") else np.nan
    shares_from_statement_b = diluted_shares_raw / 1_000_000_000 if not pd.isna(diluted_shares_raw) and diluted_shares_raw > 0 else np.nan
    shares_b = shares_from_statement_b if not pd.isna(shares_from_statement_b) else shares_from_quote_b
    if pd.isna(shares_b) or shares_b <= 0:
        shares_b = fallback_shares_b

    if pd.isna(eps_ttm) or eps_ttm <= 0:
        eps_ttm = net_income_b / shares_b if not pd.isna(net_income_b) and shares_b else np.nan

    if pd.isna(net_income_b) and not pd.isna(eps_ttm):
        net_income_b = eps_ttm * shares_b

    net_margin = safe_div(net_income_b, revenue_b)
    if pd.isna(net_margin):
        net_margin = 0.10

    current_pe = safe_div(current_price, eps_ttm)
    if pd.isna(current_pe) or current_pe <= 0:
        current_pe = np.nan

    return {
        "revenue_b": float(revenue_b),
        "net_income_b": float(net_income_b) if not pd.isna(net_income_b) else revenue_b * float(net_margin),
        "net_margin": float(net_margin),
        "eps": float(eps_ttm) if not pd.isna(eps_ttm) else safe_div(revenue_b * float(net_margin), shares_b),
        "shares_b": float(shares_b),
        "current_pe": float(current_pe) if not pd.isna(current_pe) else np.nan,
    }


def _attenuate(start: float, end: float, step: int, total_steps: int) -> float:
    if total_steps <= 0:
        return end
    weight = step / total_steps
    return start + (end - start) * weight


def build_projection_matrices(
    current_price: float,
    anchor: Dict[str, float],
    years: int,
    assumptions: pd.DataFrame,
    current_year: int = 2026,
) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
    """Build scenario tables anchored to current/TTM actual values, then project forward."""
    matrices: Dict[str, pd.DataFrame] = {}
    summary_rows: List[Dict[str, Any]] = []

    base_revenue_b = float(anchor.get("revenue_b", 0))
    base_net_income_b = float(anchor.get("net_income_b", 0))
    base_margin = float(anchor.get("net_margin", 0))
    base_eps = float(anchor.get("eps", np.nan))
    base_shares_b = float(anchor.get("shares_b", 0))
    current_pe = anchor.get("current_pe", np.nan)

    for _, r in assumptions.iterrows():
        case = str(r["Case"]).strip() or "Case"
        rev_growth = float(r["Revenue Growth %"]) / 100.0
        terminal_margin = float(r["Terminal Net Margin %"]) / 100.0
        terminal_pe_low = float(r["Terminal PE Low"])
        terminal_pe_high = float(r["Terminal PE High"])

        year_labels = [f"{current_year} Current"] + [str(current_year + i) for i in range(1, years + 1)]

        revenues = [base_revenue_b]
        rev_growth_row = [np.nan]
        net_incomes = [base_net_income_b]
        ni_growth_row = [np.nan]
        margins = [base_margin]
        eps_values = [base_eps]
        pe_low_values = [current_pe]
        pe_high_values = [current_pe]
        share_low = [current_price]
        share_high = [current_price]
        cagr_low = [np.nan]
        cagr_high = [np.nan]

        previous_revenue = base_revenue_b
        previous_net_income = base_net_income_b

        for step in range(1, years + 1):
            revenue_i = previous_revenue * (1 + rev_growth)
            margin_i = _attenuate(base_margin, terminal_margin, step, years)
            shares_i = base_shares_b
            net_income_i = revenue_i * margin_i
            eps_i = net_income_i / shares_i if shares_i else np.nan

            starting_pe_low = current_pe if not pd.isna(current_pe) and current_pe > 0 else terminal_pe_low
            starting_pe_high = current_pe if not pd.isna(current_pe) and current_pe > 0 else terminal_pe_high
            pe_low_i = _attenuate(starting_pe_low, terminal_pe_low, step, years)
            pe_high_i = _attenuate(starting_pe_high, terminal_pe_high, step, years)

            low_i = eps_i * pe_low_i
            high_i = eps_i * pe_high_i

            revenues.append(revenue_i)
            rev_growth_row.append(rev_growth)
            net_incomes.append(net_income_i)
            ni_growth_row.append(safe_div(net_income_i, previous_net_income) - 1 if previous_net_income else np.nan)
            margins.append(margin_i)
            eps_values.append(eps_i)
            pe_low_values.append(pe_low_i)
            pe_high_values.append(pe_high_i)
            share_low.append(low_i)
            share_high.append(high_i)
            cagr_low.append(calc_cagr(current_price, low_i, step) if current_price and low_i > 0 else np.nan)
            cagr_high.append(calc_cagr(current_price, high_i, step) if current_price and high_i > 0 else np.nan)

            previous_revenue = revenue_i
            previous_net_income = net_income_i

        row_map = {
            "REVENUE": revenues,
            "REV GROWTH": rev_growth_row,
            "NET INCOME": net_incomes,
            "NET INC. GROWTH": ni_growth_row,
            "NET INC. MARGINS": margins,
            "EPS": eps_values,
            "PE LOW EST": pe_low_values,
            "PE HIGH EST": pe_high_values,
            "SHARE PRICE LOW": share_low,
            "SHARE PRICE HIGH": share_high,
            "CAGR LOW": cagr_low,
            "CAGR HIGH": cagr_high,
        }

        matrix_df = pd.DataFrame({"Metric": list(row_map.keys())})
        for idx, year in enumerate(year_labels):
            matrix_df[year] = [values[idx] for values in row_map.values()]

        matrices[case] = matrix_df
        summary_rows.append(
            {
                "Case": case,
                "Final Year": year_labels[-1],
                "Revenue ($B)": revenues[-1],
                "Net Margin": margins[-1],
                "EPS": eps_values[-1],
                "Price Low": share_low[-1],
                "Price High": share_high[-1],
                "CAGR Low": cagr_low[-1],
                "CAGR High": cagr_high[-1],
            }
        )

    return matrices, pd.DataFrame(summary_rows)

def _format_projection_value(metric: str, value: Any) -> str:
    if pd.isna(value):
        return "—"
    metric_upper = metric.upper()
    try:
        v = float(value)
    except Exception:
        return _html_escape(value)

    if metric_upper in {"REVENUE", "NET INCOME"}:
        # Display full dollars for a richer dashboard feel.
        return f"${v * 1_000_000_000:,.0f}"
    if metric_upper in {"REV GROWTH", "NET INC. GROWTH", "NET INC. MARGINS", "CAGR LOW", "CAGR HIGH"}:
        return f"{v * 100:.0f}%"
    if metric_upper == "EPS":
        return f"${v:,.2f}"
    if metric_upper in {"PE LOW EST", "PE HIGH EST"}:
        return f"{v:,.0f}"
    if metric_upper in {"SHARE PRICE LOW", "SHARE PRICE HIGH"}:
        return f"${v:,.0f}"
    return f"{v:,.2f}"


def render_projection_case_table(case_name: str, df: pd.DataFrame, justification: str = "") -> None:
    case_key = case_name.strip().lower()
    theme = "base" if case_key == "base" else "bull" if case_key == "bull" else "bear"
    years = [c for c in df.columns if c != "Metric"]

    html_parts = [
        f'<div class="proj-case-card {theme}">',
        f'<div class="proj-case-chip {theme}">{_html_escape(case_name.upper())} CASE</div>',
    ]
    html_parts.append('<div class="proj-table-wrap"><table class="proj-table">')
    html_parts.append('<thead><tr><th>Metric</th>')
    for y in years:
        html_parts.append(f'<th>{_html_escape(y)}</th>')
    html_parts.append('</tr></thead><tbody>')

    for _, row in df.iterrows():
        metric = str(row["Metric"])
        row_key = metric.upper()
        row_class = ""
        if row_key in {"SHARE PRICE LOW", "SHARE PRICE HIGH"}:
            row_class = "price-row"
        elif row_key in {"CAGR LOW", "CAGR HIGH"}:
            row_class = "cagr-row"
        elif row_key in {"REVENUE", "NET INCOME", "EPS"}:
            row_class = "core-row"

        html_parts.append(f'<tr class="{row_class}"><td class="metric-col">{_html_escape(metric)}</td>')
        for y in years:
            html_parts.append(f'<td>{_format_projection_value(metric, row[y])}</td>')
        html_parts.append('</tr>')
    html_parts.append('</tbody></table></div></div>')
    st.markdown(''.join(html_parts), unsafe_allow_html=True)



@st.cache_data(ttl=60 * 60, show_spinner=False)
def get_yf_fundamentals(ticker: str) -> Dict[str, Any]:
    """Fetch generic yfinance financial statement data for non-PLTR tickers."""
    result: Dict[str, Any] = {
        "income": pd.DataFrame(),
        "balance": pd.DataFrame(),
        "cashflow": pd.DataFrame(),
        "annual_income": pd.DataFrame(),
        "annual_balance": pd.DataFrame(),
        "annual_cashflow": pd.DataFrame(),
        "errors": [],
    }
    if yf is None:
        result["errors"].append("yfinance is not installed.")
        return result
    try:
        t = yf.Ticker(ticker)
        for attr, key in [
            ("quarterly_financials", "income"),
            ("quarterly_balance_sheet", "balance"),
            ("quarterly_cashflow", "cashflow"),
            ("financials", "annual_income"),
            ("balance_sheet", "annual_balance"),
            ("cashflow", "annual_cashflow"),
        ]:
            try:
                df = getattr(t, attr)
                if isinstance(df, pd.DataFrame):
                    result[key] = df.copy()
            except Exception as e:
                result["errors"].append(f"{attr} fetch failed: {e}")
    except Exception as e:
        result["errors"].append(f"Fundamental fetch failed: {e}")
    return result


def _period_label(col: Any) -> str:
    try:
        ts = pd.to_datetime(col)
        return ts.strftime("%b %Y")
    except Exception:
        return str(col)


def _get_statement_value(raw: pd.DataFrame, possible_names: List[str], col: Any) -> float:
    if raw is None or raw.empty or col not in raw.columns:
        return np.nan
    lowered = {str(idx).lower().replace(" ", "").replace("_", ""): idx for idx in raw.index}
    for name in possible_names:
        key = name.lower().replace(" ", "").replace("_", "")
        if key in lowered:
            try:
                return float(raw.loc[lowered[key], col])
            except Exception:
                return np.nan
    # fallback fuzzy contains
    for name in possible_names:
        nk = name.lower().replace(" ", "")
        for idx in raw.index:
            ik = str(idx).lower().replace(" ", "")
            if nk in ik or ik in nk:
                try:
                    return float(raw.loc[idx, col])
                except Exception:
                    pass
    return np.nan


def _fmt_raw_money_to_m(x: Any) -> str:
    if pd.isna(x):
        return "—"
    try:
        return fmt_money_m(float(x) / 1_000_000)
    except Exception:
        return "—"


def _fmt_raw_number(x: Any, kind: str = "money") -> str:
    if pd.isna(x):
        return "—"
    try:
        v = float(x)
        if kind == "eps":
            return f"${v:,.2f}"
        return _fmt_raw_money_to_m(v)
    except Exception:
        return "—"


def _pct_change(latest: float, prior: float) -> str:
    if pd.isna(latest) or pd.isna(prior) or prior == 0:
        return "—"
    return fmt_pct(((latest / prior) - 1) * 100)


def build_live_statement_table(raw: pd.DataFrame, statement_type: str) -> pd.DataFrame:
    """Convert yfinance statement tables into the app's terminal table format."""
    if raw is None or raw.empty:
        return pd.DataFrame({"Line Item": ["NO LIVE STATEMENT DATA RETURNED"], "Status": ["Check ticker, internet connection, or yfinance availability"]})

    cols = list(raw.columns)
    # yfinance usually returns newest first, but sort defensively.
    try:
        cols = sorted(cols, key=lambda c: pd.to_datetime(c), reverse=True)
    except Exception:
        pass

    value_cols = cols[:5]  # latest, prior quarter, and enough for YoY when available
    display_cols = value_cols[:4]
    latest = value_cols[0] if value_cols else None
    prior_q = value_cols[1] if len(value_cols) > 1 else None
    prior_y = value_cols[4] if len(value_cols) > 4 else None

    if statement_type == "income":
        sections = [
            ("REVENUE & PROFITABILITY", [
                ("Total Revenue", ["Total Revenue", "Operating Revenue"], "money"),
                ("Cost of Revenue", ["Cost Of Revenue", "Cost Revenue"], "money"),
                ("Gross Profit", ["Gross Profit"], "money"),
            ]),
            ("OPERATING RESULTS", [
                ("Operating Expense", ["Operating Expense", "Total Operating Expenses"], "money"),
                ("Operating Income", ["Operating Income"], "money"),
                ("EBITDA", ["EBITDA", "Normalized EBITDA"], "money"),
            ]),
            ("NET INCOME & EPS", [
                ("Pretax Income", ["Pretax Income"], "money"),
                ("Tax Provision", ["Tax Provision"], "money"),
                ("Net Income", ["Net Income", "Net Income Common Stockholders"], "money"),
                ("Diluted EPS", ["Diluted EPS", "Diluted EPS Diluted"], "eps"),
            ]),
        ]
    elif statement_type == "balance":
        sections = [
            ("ASSETS", [
                ("Cash & Equivalents", ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"], "money"),
                ("Accounts Receivable", ["Accounts Receivable", "Receivables"], "money"),
                ("Current Assets", ["Current Assets", "Total Current Assets"], "money"),
                ("Total Assets", ["Total Assets"], "money"),
            ]),
            ("LIABILITIES", [
                ("Current Liabilities", ["Current Liabilities", "Total Current Liabilities"], "money"),
                ("Total Debt", ["Total Debt", "Long Term Debt And Capital Lease Obligation"], "money"),
                ("Total Liabilities", ["Total Liabilities Net Minority Interest", "Total Liab"], "money"),
            ]),
            ("EQUITY", [
                ("Stockholders' Equity", ["Stockholders Equity", "Total Stockholder Equity"], "money"),
                ("Common Stock Equity", ["Common Stock Equity"], "money"),
            ]),
        ]
    else:
        sections = [
            ("OPERATING CASH FLOW", [
                ("Operating Cash Flow", ["Operating Cash Flow", "Total Cash From Operating Activities"], "money"),
                ("Capital Expenditure", ["Capital Expenditure", "Capital Expenditures"], "money"),
                ("Free Cash Flow", ["Free Cash Flow"], "money"),
            ]),
            ("INVESTING & FINANCING", [
                ("Investing Cash Flow", ["Investing Cash Flow", "Total Cashflows From Investing Activities"], "money"),
                ("Financing Cash Flow", ["Financing Cash Flow", "Total Cash From Financing Activities"], "money"),
                ("Stock Repurchase", ["Repurchase Of Capital Stock", "Repurchase Of Stock"], "money"),
                ("Dividends Paid", ["Cash Dividends Paid", "Common Stock Dividend Paid"], "money"),
            ]),
            ("CASH POSITION", [
                ("Beginning Cash Position", ["Beginning Cash Position"], "money"),
                ("End Cash Position", ["End Cash Position"], "money"),
            ]),
        ]

    rows: List[Dict[str, Any]] = []
    for section_name, items in sections:
        rows.append({"Line Item": section_name, **{_period_label(c): "" for c in display_cols}, "YoY Δ": "", "QoQ Δ": ""})
        for label, possible, kind in items:
            vals = [_get_statement_value(raw, possible, c) for c in display_cols]
            if all(pd.isna(v) for v in vals):
                continue
            row = {"Line Item": label}
            for c, v in zip(display_cols, vals):
                row[_period_label(c)] = _fmt_raw_number(v, kind)
            latest_v = _get_statement_value(raw, possible, latest) if latest is not None else np.nan
            prior_q_v = _get_statement_value(raw, possible, prior_q) if prior_q is not None else np.nan
            prior_y_v = _get_statement_value(raw, possible, prior_y) if prior_y is not None else np.nan
            row["YoY Δ"] = _pct_change(latest_v, prior_y_v)
            row["QoQ Δ"] = _pct_change(latest_v, prior_q_v)
            rows.append(row)

    return pd.DataFrame(rows)



def build_live_statement_table_wide(fundamentals: Dict[str, Any], statement_type: str) -> pd.DataFrame:
    """Build a wider statement view: annual history plus latest quarter."""
    if statement_type == "income":
        annual_raw = fundamentals.get("annual_income", pd.DataFrame())
        quarter_raw = fundamentals.get("income", pd.DataFrame())
        annual_cashflow_raw = fundamentals.get("annual_cashflow", pd.DataFrame())
        quarter_cashflow_raw = fundamentals.get("cashflow", pd.DataFrame())
        sections = [
            ("REVENUE & PROFITABILITY", [
                ("Total Revenue", ["Total Revenue", "Operating Revenue"], "money", "margin_base"),
                ("Cost of Revenue", ["Cost Of Revenue", "Cost Revenue"], "money", None),
                ("Gross Profit", ["Gross Profit"], "money", "gross_margin"),
            ]),
            ("OPERATING RESULTS", [
                ("Operating Expense", ["Operating Expense", "Total Operating Expenses"], "money", None),
                ("Operating Income", ["Operating Income"], "money", "op_margin"),
                ("EBITDA", ["EBITDA", "Normalized EBITDA"], "money", "ebitda_margin"),
            ]),
            ("NET INCOME & EPS", [
                ("Pretax Income", ["Pretax Income"], "money", None),
                ("Tax Provision", ["Tax Provision"], "money", None),
                ("Net Income", ["Net Income", "Net Income Common Stockholders"], "money", "net_margin"),
                ("Diluted EPS", ["Diluted EPS", "Diluted EPS Diluted"], "eps", None),
            ]),
            ("SHAREHOLDER RETURNS", [
                ("Total Returns (Divs + Buybacks)", ["__SHAREHOLDER_RETURNS__"], "money", None),
            ]),
        ]
    elif statement_type == "balance":
        annual_cashflow_raw = pd.DataFrame()
        quarter_cashflow_raw = pd.DataFrame()
        annual_raw = fundamentals.get("annual_balance", pd.DataFrame())
        quarter_raw = fundamentals.get("balance", pd.DataFrame())
        sections = [
            ("ASSETS", [
                ("Cash & Equivalents", ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"], "money", None),
                ("Accounts Receivable", ["Accounts Receivable", "Receivables"], "money", None),
                ("Current Assets", ["Current Assets", "Total Current Assets"], "money", None),
                ("Total Assets", ["Total Assets"], "money", None),
            ]),
            ("LIABILITIES", [
                ("Current Liabilities", ["Current Liabilities", "Total Current Liabilities"], "money", None),
                ("Total Debt", ["Total Debt", "Long Term Debt And Capital Lease Obligation"], "money", None),
                ("Total Liabilities", ["Total Liabilities Net Minority Interest", "Total Liab"], "money", None),
            ]),
            ("EQUITY", [
                ("Stockholders' Equity", ["Stockholders Equity", "Total Stockholder Equity"], "money", None),
                ("Common Stock Equity", ["Common Stock Equity"], "money", None),
            ]),
        ]
    else:
        annual_cashflow_raw = pd.DataFrame()
        quarter_cashflow_raw = pd.DataFrame()
        annual_raw = fundamentals.get("annual_cashflow", pd.DataFrame())
        quarter_raw = fundamentals.get("cashflow", pd.DataFrame())
        sections = [
            ("OPERATING CASH FLOW", [
                ("Operating Cash Flow", ["Operating Cash Flow", "Total Cash From Operating Activities"], "money", None),
                ("Capital Expenditure", ["Capital Expenditure", "Capital Expenditures"], "money", None),
                ("Free Cash Flow", ["Free Cash Flow"], "money", None),
            ]),
            ("INVESTING & FINANCING", [
                ("Investing Cash Flow", ["Investing Cash Flow", "Total Cashflows From Investing Activities"], "money", None),
                ("Financing Cash Flow", ["Financing Cash Flow", "Total Cash From Financing Activities"], "money", None),
                ("Stock Repurchase", ["Repurchase Of Capital Stock", "Repurchase Of Stock"], "money", None),
                ("Dividends Paid", ["Cash Dividends Paid", "Common Stock Dividend Paid"], "money", None),
            ]),
            ("CASH POSITION", [
                ("Beginning Cash Position", ["Beginning Cash Position"], "money", None),
                ("End Cash Position", ["End Cash Position"], "money", None),
            ]),
        ]

    annual_cols = []
    if isinstance(annual_raw, pd.DataFrame) and not annual_raw.empty:
        annual_cols = list(annual_raw.columns)
        try:
            annual_cols = sorted(annual_cols, key=lambda c: pd.to_datetime(c))
        except Exception:
            pass
        annual_cols = annual_cols[-6:]

    q_cols = []
    if isinstance(quarter_raw, pd.DataFrame) and not quarter_raw.empty:
        q_cols = list(quarter_raw.columns)
        try:
            q_cols = sorted(q_cols, key=lambda c: pd.to_datetime(c), reverse=True)
        except Exception:
            pass

    latest_q = q_cols[0] if q_cols else None
    prior_q = q_cols[1] if len(q_cols) > 1 else None
    prior_y_q = q_cols[4] if len(q_cols) > 4 else None

    if not annual_cols and latest_q is None:
        return pd.DataFrame({"Line Item": ["NO LIVE STATEMENT DATA RETURNED"], "Status": ["Check ticker, internet connection, or yfinance availability"]})

    annual_labels = []
    for c in annual_cols:
        try:
            annual_labels.append(f"FY{pd.to_datetime(c).year}")
        except Exception:
            annual_labels.append(str(c))

    q_label = "Latest Qtr"
    if latest_q is not None:
        try:
            q_label = pd.to_datetime(latest_q).strftime("%b %Y")
        except Exception:
            q_label = str(latest_q)

    display_cols = annual_labels + ([q_label] if latest_q is not None else [])
    rows: List[Dict[str, Any]] = []

    def revenue_value(raw_df: pd.DataFrame, col: Any) -> float:
        return _get_statement_value(raw_df, ["Total Revenue", "Operating Revenue"], col)

    def margin_for(metric_tag: Optional[str], raw_df: pd.DataFrame, col: Any, value: float) -> str:
        if metric_tag is None or raw_df is None or raw_df.empty or col is None:
            return "—"
        rev = revenue_value(raw_df, col)
        if pd.isna(value) or pd.isna(rev) or rev == 0:
            return "—"
        return f"{safe_div(value, rev) * 100:.1f}%"

    for section_name, items in sections:
        rows.append({"Line Item": section_name, **{c: "" for c in display_cols}, "YoY Δ": "", "QoQ Δ": "", "Margin": ""})
        for label, possible, kind, metric_tag in items:
            is_shareholder_return = possible == ["__SHAREHOLDER_RETURNS__"]

            if is_shareholder_return:
                annual_vals = []
                annual_notes = {}
                for c in annual_cols:
                    divs, buybacks, total = _shareholder_return_components(annual_cashflow_raw, c)
                    annual_vals.append(total)
                    annual_notes[_period_label(c)] = (divs, buybacks)
                divs_q, buybacks_q, q_val = _shareholder_return_components(quarter_cashflow_raw, latest_q) if latest_q is not None else (np.nan, np.nan, np.nan)
            else:
                annual_vals = [_get_statement_value(annual_raw, possible, c) for c in annual_cols] if annual_cols else []
                q_val = _get_statement_value(quarter_raw, possible, latest_q) if latest_q is not None else np.nan

            if all(pd.isna(v) for v in annual_vals) and pd.isna(q_val):
                continue

            row = {"Line Item": label}
            for col_label, val in zip(annual_labels, annual_vals):
                row[col_label] = _fmt_raw_number(val, kind)
            if latest_q is not None:
                row[q_label] = _fmt_raw_number(q_val, kind)

            if is_shareholder_return:
                prior_y_val = np.nan
                prior_q_val = np.nan
                if prior_y_q is not None:
                    _, _, prior_y_val = _shareholder_return_components(quarter_cashflow_raw, prior_y_q)
                if prior_q is not None:
                    _, _, prior_q_val = _shareholder_return_components(quarter_cashflow_raw, prior_q)
                row["YoY Δ"] = _pct_change(q_val, prior_y_val)
                row["QoQ Δ"] = _pct_change(q_val, prior_q_val)
                if not pd.isna(divs_q) or not pd.isna(buybacks_q):
                    row["Margin"] = f"Divs {_fmt_raw_money_to_m(divs_q)} · Buybacks {_fmt_raw_money_to_m(buybacks_q)}"
                else:
                    row["Margin"] = "—"
            else:
                prior_y_val = _get_statement_value(quarter_raw, possible, prior_y_q) if prior_y_q is not None else np.nan
                prior_q_val = _get_statement_value(quarter_raw, possible, prior_q) if prior_q is not None else np.nan
                row["YoY Δ"] = _pct_change(q_val, prior_y_val)
                row["QoQ Δ"] = _pct_change(q_val, prior_q_val)
                row["Margin"] = margin_for(metric_tag, quarter_raw, latest_q, q_val)

            rows.append(row)

    return pd.DataFrame(rows)


def build_live_kpis(fundamentals: Dict[str, Any], quote: Dict[str, Any], market_cap_b: float) -> List[Tuple[str, str, str]]:
    income = fundamentals.get("income", pd.DataFrame())
    cashflow = fundamentals.get("cashflow", pd.DataFrame())
    if income is None or income.empty:
        return [
            ("Stock Price", f"${quote.get('last_price', 0):,.2f}" if quote.get("last_price") else "—", ""),
            ("Market Cap", f"${market_cap_b:,.1f}B", ""),
            ("Trailing P/E", f"{quote.get('trailing_pe'):,.1f}x" if quote.get("trailing_pe") else "—", ""),
            ("Forward P/E", f"{quote.get('forward_pe'):,.1f}x" if quote.get("forward_pe") else "—", ""),
            ("Shares", f"{(quote.get('shares') or 0)/1e9:,.2f}B" if quote.get("shares") else "—", ""),
            ("Currency", quote.get("currency", "USD"), ""),
        ]

    cols = list(income.columns)
    try:
        cols = sorted(cols, key=lambda c: pd.to_datetime(c), reverse=True)
    except Exception:
        pass
    latest = cols[0]
    prior_q = cols[1] if len(cols) > 1 else None
    prior_y = cols[4] if len(cols) > 4 else None

    def val(names):
        return _get_statement_value(income, names, latest)

    def delta(names):
        current = _get_statement_value(income, names, latest)
        base = _get_statement_value(income, names, prior_y) if prior_y is not None else (_get_statement_value(income, names, prior_q) if prior_q is not None else np.nan)
        label = "YoY" if prior_y is not None else "QoQ"
        return f"{_pct_change(current, base)} {label}" if _pct_change(current, base) != "—" else ""

    rev = val(["Total Revenue", "Operating Revenue"])
    gross = val(["Gross Profit"])
    op = val(["Operating Income"])
    ni = val(["Net Income", "Net Income Common Stockholders"])

    fcf = np.nan
    if cashflow is not None and not cashflow.empty:
        cf_cols = list(cashflow.columns)
        try:
            cf_cols = sorted(cf_cols, key=lambda c: pd.to_datetime(c), reverse=True)
        except Exception:
            pass
        if cf_cols:
            fcf = _get_statement_value(cashflow, ["Free Cash Flow"], cf_cols[0])

    return [
        (f"Revenue {_period_label(latest)}", _fmt_raw_money_to_m(rev), delta(["Total Revenue", "Operating Revenue"])),
        ("Gross Profit", _fmt_raw_money_to_m(gross), delta(["Gross Profit"])),
        ("Operating Income", _fmt_raw_money_to_m(op), delta(["Operating Income"])),
        ("Net Income", _fmt_raw_money_to_m(ni), delta(["Net Income", "Net Income Common Stockholders"])),
        ("Free Cash Flow", _fmt_raw_money_to_m(fcf), ""),
        ("Market Cap", f"${market_cap_b:,.1f}B", ""),
    ]


def compute_start_revenue_from_live(fundamentals: Dict[str, Any], fallback_b: float) -> float:
    """Use TTM revenue from quarterly financials when possible; otherwise keep fallback."""
    income = fundamentals.get("income", pd.DataFrame())
    if income is None or income.empty:
        return fallback_b
    cols = list(income.columns)
    try:
        cols = sorted(cols, key=lambda c: pd.to_datetime(c), reverse=True)
    except Exception:
        pass
    vals = [_get_statement_value(income, ["Total Revenue", "Operating Revenue"], c) for c in cols[:4]]
    vals = [v for v in vals if not pd.isna(v)]
    if vals:
        return float(sum(vals)) / 1_000_000_000
    return fallback_b


def live_mode_enabled(ticker: str, use_live: bool, fundamentals: Dict[str, Any]) -> bool:
    return ticker.upper() != TICKER_DEFAULT



def build_live_operating_profile(fundamentals: Dict[str, Any]) -> pd.DataFrame:
    income = fundamentals.get("income", pd.DataFrame())
    if income is None or income.empty:
        return pd.DataFrame({"Line Item": ["NO LIVE OPERATING PROFILE RETURNED"], "Status": ["Check ticker, internet connection, or yfinance availability"]})

    cols = list(income.columns)
    try:
        cols = sorted(cols, key=lambda c: pd.to_datetime(c), reverse=True)
    except Exception:
        pass
    cols = cols[:5]

    metrics = [
        ("REVENUE & PROFIT", None),
        ("Total Revenue", ["Total Revenue", "Operating Revenue"]),
        ("Gross Profit", ["Gross Profit"]),
        ("Operating Income", ["Operating Income"]),
        ("Net Income", ["Net Income", "Net Income Common Stockholders"]),
        ("MARGINS", None),
        ("Gross Margin", "gross_margin"),
        ("Operating Margin", "op_margin"),
        ("Net Margin", "net_margin"),
    ]

    rows = []
    for label, spec in metrics:
        if spec is None:
            rows.append({"Line Item": label, **{_period_label(c): "" for c in cols}, "QoQ Δ": ""})
            continue

        row = {"Line Item": label}
        values = []
        for c in cols:
            rev = _get_statement_value(income, ["Total Revenue", "Operating Revenue"], c)
            gross = _get_statement_value(income, ["Gross Profit"], c)
            op = _get_statement_value(income, ["Operating Income"], c)
            ni = _get_statement_value(income, ["Net Income", "Net Income Common Stockholders"], c)

            if spec == "gross_margin":
                v = safe_div(gross, rev)
                row[_period_label(c)] = f"{v*100:.1f}%" if not pd.isna(v) else "—"
            elif spec == "op_margin":
                v = safe_div(op, rev)
                row[_period_label(c)] = f"{v*100:.1f}%" if not pd.isna(v) else "—"
            elif spec == "net_margin":
                v = safe_div(ni, rev)
                row[_period_label(c)] = f"{v*100:.1f}%" if not pd.isna(v) else "—"
            else:
                v = _get_statement_value(income, spec, c)
                row[_period_label(c)] = _fmt_raw_money_to_m(v)
            values.append(v)

        row["QoQ Δ"] = _pct_change(values[0], values[1]) if len(values) > 1 and not isinstance(spec, str) else "—"
        rows.append(row)

    return pd.DataFrame(rows)


def build_live_annual_metrics(fundamentals: Dict[str, Any]) -> pd.DataFrame:
    income = fundamentals.get("annual_income", pd.DataFrame())
    cashflow = fundamentals.get("annual_cashflow", pd.DataFrame())
    if income is None or income.empty:
        return pd.DataFrame()

    cols = list(income.columns)
    try:
        cols = sorted(cols, key=lambda c: pd.to_datetime(c))
    except Exception:
        pass

    rows = []
    for c in cols[-6:]:
        rev = _get_statement_value(income, ["Total Revenue", "Operating Revenue"], c)
        gross = _get_statement_value(income, ["Gross Profit"], c)
        op = _get_statement_value(income, ["Operating Income"], c)
        ni = _get_statement_value(income, ["Net Income", "Net Income Common Stockholders"], c)
        fcf = np.nan
        if cashflow is not None and not cashflow.empty and c in cashflow.columns:
            fcf = _get_statement_value(cashflow, ["Free Cash Flow"], c)
        rows.append({
            "Year": _period_label(c),
            "Revenue": rev / 1_000_000 if not pd.isna(rev) else np.nan,
            "Gross Profit": gross / 1_000_000 if not pd.isna(gross) else np.nan,
            "Operating Income": op / 1_000_000 if not pd.isna(op) else np.nan,
            "Net Income": ni / 1_000_000 if not pd.isna(ni) else np.nan,
            "Free Cash Flow": fcf / 1_000_000 if not pd.isna(fcf) else np.nan,
            "Gross Margin %": safe_div(gross, rev) * 100 if not pd.isna(rev) else np.nan,
            "Operating Margin %": safe_div(op, rev) * 100 if not pd.isna(rev) else np.nan,
            "Net Margin %": safe_div(ni, rev) * 100 if not pd.isna(rev) else np.nan,
        })

    return pd.DataFrame(rows)


def _extract_price_targets(apt: pd.DataFrame) -> Dict[str, float]:
    out: Dict[str, float] = {}
    if apt is None or apt.empty:
        return out
    for col in apt.columns:
        if not pd.api.types.is_numeric_dtype(apt[col]):
            continue
        val = apt[col].dropna()
        if val.empty:
            continue
        name = str(col).lower()
        if "low" in name:
            out["Low Target"] = float(val.iloc[0])
        elif "mean" in name or "average" in name:
            out["Average Target"] = float(val.iloc[0])
        elif "median" in name:
            out["Median Target"] = float(val.iloc[0])
        elif "high" in name:
            out["High Target"] = float(val.iloc[0])
    return out


def build_live_forward_view(market_data: Dict[str, Any], quote: Dict[str, Any], current_price: float, market_cap_b: float, revenue_base_b: float) -> pd.DataFrame:
    rows = [
        {"Metric": "Current Price", "Value": f"${current_price:,.2f}", "Notes": "Live quote when available"},
        {"Metric": "Market Cap", "Value": f"${market_cap_b:,.1f}B", "Notes": "Live or calculated from shares"},
        {"Metric": "P/S on Revenue Base", "Value": f"{market_cap_b / revenue_base_b:,.1f}x" if revenue_base_b else "—", "Notes": "Market cap / TTM revenue base"},
        {"Metric": "Trailing P/E", "Value": f"{quote.get('trailing_pe'):,.1f}x" if quote.get("trailing_pe") else "—", "Notes": "Yahoo Finance field"},
        {"Metric": "Forward P/E", "Value": f"{quote.get('forward_pe'):,.1f}x" if quote.get("forward_pe") else "—", "Notes": "Yahoo Finance field"},
    ]

    targets = _extract_price_targets(market_data.get("analyst_price_targets", pd.DataFrame()))
    for name, target in targets.items():
        rows.append({
            "Metric": name,
            "Value": f"${target:,.2f}",
            "Notes": f"{(target / current_price - 1) * 100:+.1f}% vs current price" if current_price else "",
        })

    return pd.DataFrame(rows)



SEC_USER_AGENT = "FinancialDashboardBuilder/1.0 contact@example.com"
SEC_TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik10}.json"
SEC_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json"


def _sec_headers() -> Dict[str, str]:
    return {
        "User-Agent": SEC_USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
    }


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def sec_ticker_map() -> pd.DataFrame:
    """Official SEC ticker to CIK mapping."""
    if requests is None:
        return pd.DataFrame(columns=["ticker", "cik_str", "title", "cik10"])
    try:
        r = requests.get(SEC_TICKER_MAP_URL, headers=_sec_headers(), timeout=20)
        r.raise_for_status()
        data = r.json()
        rows = []
        for _, item in data.items():
            cik = int(item.get("cik_str"))
            rows.append({
                "ticker": str(item.get("ticker", "")).upper(),
                "cik_str": cik,
                "title": item.get("title", ""),
                "cik10": f"{cik:010d}",
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame(columns=["ticker", "cik_str", "title", "cik10"])


def sec_lookup_ticker(ticker: str) -> Dict[str, Any]:
    table = sec_ticker_map()
    if table.empty:
        return {}
    match = table[table["ticker"].astype(str).str.upper() == ticker.upper()]
    if match.empty:
        return {}
    return match.iloc[0].to_dict()


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def sec_submissions(cik10: str) -> Dict[str, Any]:
    if requests is None or not cik10:
        return {"errors": ["requests is not installed"]}
    try:
        r = requests.get(SEC_SUBMISSIONS_URL.format(cik10=cik10), headers=_sec_headers(), timeout=25)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"errors": [str(e)]}


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def sec_companyfacts(cik10: str) -> Dict[str, Any]:
    if requests is None or not cik10:
        return {"errors": ["requests is not installed"]}
    try:
        r = requests.get(SEC_COMPANYFACTS_URL.format(cik10=cik10), headers=_sec_headers(), timeout=35)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"errors": [str(e)]}


def sec_filings_table(submissions: Dict[str, Any], limit: int = 6) -> pd.DataFrame:
    recent = submissions.get("filings", {}).get("recent", {}) if isinstance(submissions, dict) else {}
    if not recent:
        return pd.DataFrame()

    rows = []
    forms = recent.get("form", [])
    accession = recent.get("accessionNumber", [])
    filed = recent.get("filingDate", [])
    periods = recent.get("reportDate", [])
    primary_docs = recent.get("primaryDocument", [])
    cik_no_zero = str(submissions.get("cik", "")).lstrip("0")

    for i, form in enumerate(forms):
        if form not in {"10-K", "10-Q"}:
            continue
        acc = accession[i] if i < len(accession) else ""
        primary = primary_docs[i] if i < len(primary_docs) else ""
        acc_no_dash = acc.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_no_zero}/{acc_no_dash}/{primary}" if cik_no_zero and acc and primary else ""
        rows.append({
            "Form": form,
            "Filing Date": filed[i] if i < len(filed) else "",
            "Period End": periods[i] if i < len(periods) else "",
            "Accession": acc,
            "Document": primary,
            "URL": url,
        })
        if len(rows) >= limit:
            break

    return pd.DataFrame(rows)


SEC_STATEMENT_MAP = {
    "income": [
        ("REVENUE & PROFITABILITY", None, None),
        ("Total Revenue", ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet"], "money"),
        ("Cost of Revenue", ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"], "money"),
        ("Gross Profit", ["GrossProfit"], "money"),
        ("OPERATING EXPENSES", None, None),
        ("Research & Development", ["ResearchAndDevelopmentExpense"], "money"),
        ("Sales & Marketing", ["SellingAndMarketingExpense"], "money"),
        ("SG&A", ["SellingGeneralAndAdministrativeExpense", "GeneralAndAdministrativeExpense"], "money"),
        ("Operating Expenses", ["OperatingExpenses"], "money"),
        ("Operating Income", ["OperatingIncomeLoss"], "money"),
        ("NET INCOME & EPS", None, None),
        ("Interest Expense", ["InterestExpenseNonOperating", "InterestExpense"], "money"),
        ("Pretax Income", ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest", "IncomeLossFromContinuingOperationsBeforeIncomeTaxes"], "money"),
        ("Tax Provision", ["IncomeTaxExpenseBenefit"], "money"),
        ("Net Income", ["NetIncomeLoss", "ProfitLoss"], "money"),
        ("Diluted EPS", ["EarningsPerShareDiluted"], "eps"),
        ("Diluted Shares", ["WeightedAverageNumberOfDilutedSharesOutstanding"], "shares"),
    ],
    "balance": [
        ("ASSETS", None, None),
        ("Cash & Equivalents", ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"], "money"),
        ("Short-Term Investments", ["ShortTermInvestments", "MarketableSecuritiesCurrent"], "money"),
        ("Accounts Receivable", ["AccountsReceivableNetCurrent", "AccountsReceivableNet"], "money"),
        ("Inventory", ["InventoryNet"], "money"),
        ("Current Assets", ["AssetsCurrent"], "money"),
        ("PP&E", ["PropertyPlantAndEquipmentNet"], "money"),
        ("Goodwill", ["Goodwill"], "money"),
        ("Intangible Assets", ["FiniteLivedIntangibleAssetsNet", "IntangibleAssetsNetExcludingGoodwill"], "money"),
        ("Total Assets", ["Assets"], "money"),
        ("LIABILITIES", None, None),
        ("Accounts Payable", ["AccountsPayableCurrent", "AccountsPayableTradeCurrent"], "money"),
        ("Current Liabilities", ["LiabilitiesCurrent"], "money"),
        ("Short-Term Debt", ["ShortTermBorrowings", "ShortTermDebtCurrent"], "money"),
        ("Long-Term Debt", ["LongTermDebtNoncurrent", "LongTermDebt"], "money"),
        ("Total Liabilities", ["Liabilities"], "money"),
        ("EQUITY", None, None),
        ("Common Stock & APIC", ["CommonStocksIncludingAdditionalPaidInCapital", "AdditionalPaidInCapital"], "money"),
        ("Retained Earnings", ["RetainedEarningsAccumulatedDeficit"], "money"),
        ("Shareholders' Equity", ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"], "money"),
        ("Total Liabilities & Equity", ["LiabilitiesAndStockholdersEquity"], "money"),
    ],
    "cashflow": [
        ("OPERATING CASH FLOW", None, None),
        ("Net Income", ["NetIncomeLoss", "ProfitLoss"], "money"),
        ("Depreciation & Amortization", ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization"], "money"),
        ("Stock-Based Compensation", ["ShareBasedCompensation"], "money"),
        ("Operating Cash Flow", ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"], "money"),
        ("INVESTING CASH FLOW", None, None),
        ("CapEx", ["PaymentsToAcquirePropertyPlantAndEquipment", "CapitalExpenditures"], "money"),
        ("Acquisitions", ["PaymentsToAcquireBusinessesNetOfCashAcquired"], "money"),
        ("Investing Cash Flow", ["NetCashProvidedByUsedInInvestingActivities"], "money"),
        ("FINANCING CASH FLOW", None, None),
        ("Dividends Paid", ["PaymentsOfDividends", "PaymentsOfDividendsCommonStock"], "money"),
        ("Share Repurchases", ["PaymentsForRepurchaseOfCommonStock", "PaymentsForRepurchaseOfEquity"], "money"),
        ("Debt Issuance", ["ProceedsFromIssuanceOfLongTermDebt", "ProceedsFromBorrowings"], "money"),
        ("Debt Repayment", ["RepaymentsOfLongTermDebt", "RepaymentsOfDebt"], "money"),
        ("Financing Cash Flow", ["NetCashProvidedByUsedInFinancingActivities"], "money"),
        ("FREE CASH FLOW", None, None),
        ("Free Cash Flow", ["__SEC_FCF__"], "money"),
        ("Net Change in Cash", ["CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect", "CashAndCashEquivalentsPeriodIncreaseDecrease"], "money"),
    ],
}


SEC_ANNUAL_HISTORY_YEARS = 6


def _calendar_quarter_label(end_value: Any) -> str:
    """Label quarter by calendar period end to avoid confusing fiscal labels."""
    try:
        ts = pd.to_datetime(end_value)
        return f"Q{ts.quarter} {ts.year}"
    except Exception:
        return str(end_value)


def _sec_prepare_fact_df(raw_rows: List[Dict[str, Any]], tag: str, unit: str) -> pd.DataFrame:
    df = pd.DataFrame(raw_rows)
    if df.empty or "val" not in df.columns:
        return pd.DataFrame()

    for col in ["fy", "fp", "form", "filed", "start", "end", "frame"]:
        if col not in df.columns:
            df[col] = np.nan

    df["tag"] = tag
    df["unit"] = unit
    df["filed_dt"] = pd.to_datetime(df["filed"], errors="coerce")
    df["start_dt"] = pd.to_datetime(df["start"], errors="coerce")
    df["end_dt"] = pd.to_datetime(df["end"], errors="coerce")
    df["duration_days"] = (df["end_dt"] - df["start_dt"]).dt.days
    df = df[df["form"].isin(["10-K", "10-Q", "10-K/A", "10-Q/A"])].copy()
    return df


def _sec_all_fact_records(companyfacts: Dict[str, Any], tags: List[str]) -> List[Tuple[str, str, pd.DataFrame]]:
    """Return all available SEC fact dataframes for candidate tags."""
    facts = companyfacts.get("facts", {}) if isinstance(companyfacts, dict) else {}
    us_gaap = facts.get("us-gaap", {})
    candidates: List[Tuple[str, str, pd.DataFrame]] = []

    for tag in tags:
        if tag not in us_gaap:
            continue

        units = us_gaap[tag].get("units", {})
        preferred_units = ["USD", "shares", "USD/shares", "pure"]
        unit = ""
        arr: List[Dict[str, Any]] = []

        for u in preferred_units:
            if u in units and isinstance(units[u], list):
                unit, arr = u, units[u]
                break

        if not arr:
            for u, candidate in units.items():
                if isinstance(candidate, list):
                    unit, arr = u, candidate
                    break

        df = _sec_prepare_fact_df(arr, tag, unit)
        if not df.empty:
            candidates.append((tag, unit, df))

    return candidates


def _sec_fact_records(companyfacts: Dict[str, Any], tags: List[str]) -> Tuple[str, str, pd.DataFrame]:
    """Return the single newest/richest SEC fact dataframe for backward compatibility."""
    candidates = []
    for tag, unit, df in _sec_all_fact_records(companyfacts, tags):
        max_end = df["end_dt"].max()
        usable_count = int(df["val"].notna().sum())
        candidates.append((tag, unit, df, max_end, usable_count))

    if not candidates:
        return "", "", pd.DataFrame()

    candidates = sorted(
        candidates,
        key=lambda x: (
            pd.Timestamp.min if pd.isna(x[3]) else x[3],
            x[4],
        ),
        reverse=True,
    )
    return candidates[0][0], candidates[0][1], candidates[0][2]


def _sec_format_value(value: Any, unit: str, kind: str) -> str:
    if value is None or pd.isna(value):
        return "—"
    try:
        v = float(value)
    except Exception:
        return "—"
    if unit == "USD/shares" or kind == "eps":
        return f"${v:,.2f}"
    if unit == "shares" or kind == "shares":
        if abs(v) >= 1_000_000_000:
            return f"{v / 1_000_000_000:,.2f}B"
        if abs(v) >= 1_000_000:
            return f"{v / 1_000_000:,.1f}M"
        return f"{v:,.0f}"
    return _fmt_raw_money_to_m(v)


def _sec_split_periods(df: pd.DataFrame, statement_type: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    if statement_type in {"income", "cashflow"}:
        annual = df[
            (df["fp"].astype(str).str.upper() == "FY")
            | (df["duration_days"] >= 300)
            | ((df["form"].isin(["10-K", "10-K/A"])) & (df["duration_days"].isna()))
        ].copy()
        quarterly = df[
            (df["form"].isin(["10-Q", "10-Q/A"]))
            & ((df["duration_days"].isna()) | (df["duration_days"] <= 125))
            & (df["fp"].astype(str).str.upper().isin(["Q1", "Q2", "Q3"]))
        ].copy()
    else:
        annual = df[(df["fp"].astype(str).str.upper() == "FY") | (df["form"].isin(["10-K", "10-K/A"]))].copy()
        quarterly = df[(df["form"].isin(["10-Q", "10-Q/A"])) & (df["fp"].astype(str).str.upper().isin(["Q1", "Q2", "Q3"]))].copy()

    annual = annual.sort_values(["end_dt", "filed_dt"], ascending=[True, True]).drop_duplicates(subset=["end"], keep="last")
    quarterly = quarterly.sort_values(["end_dt", "filed_dt"], ascending=[True, True]).drop_duplicates(subset=["end"], keep="last")
    return annual, quarterly


def _sec_period_labels(companyfacts: Dict[str, Any], statement_type: str) -> Tuple[List[str], List[str], Dict[str, str], Dict[str, str]]:
    """Collect recent annual and latest quarterly periods across every candidate tag.

    This is intentionally a union across tags, because companies frequently switch
    XBRL concepts over time. Example: older revenue years may use a different tag
    than the newest revenue years.
    """
    annual_periods: Dict[str, Tuple[pd.Timestamp, str]] = {}
    quarter_periods: Dict[str, Tuple[pd.Timestamp, str]] = {}

    for _, tags, _ in SEC_STATEMENT_MAP[statement_type]:
        if not tags or tags == ["__SEC_FCF__"]:
            continue

        for _, _, df in _sec_all_fact_records(companyfacts, tags):
            annual, quarterly = _sec_split_periods(df, statement_type)

            for _, r in annual.iterrows():
                end = str(r.get("end", ""))
                if not end:
                    continue
                end_dt = r.get("end_dt", pd.NaT)
                try:
                    label = f"FY{int(r['fy'])}" if not pd.isna(r.get("fy")) else f"FY{pd.to_datetime(end).year}"
                except Exception:
                    label = end
                annual_periods[end] = (end_dt, label)

            for _, r in quarterly.iterrows():
                end = str(r.get("end", ""))
                if not end:
                    continue
                end_dt = r.get("end_dt", pd.NaT)
                # Use calendar quarter label. SEC fiscal labels can show confusing rows like Q3 2026.
                label = _calendar_quarter_label(end)
                quarter_periods[end] = (end_dt, label)

    annual_sorted = sorted(
        annual_periods.items(),
        key=lambda kv: pd.Timestamp.min if pd.isna(kv[1][0]) else kv[1][0],
    )[-SEC_ANNUAL_HISTORY_YEARS:]
    quarter_sorted = sorted(
        quarter_periods.items(),
        key=lambda kv: pd.Timestamp.min if pd.isna(kv[1][0]) else kv[1][0],
    )[-1:]

    annual_ends = [k for k, _ in annual_sorted]
    quarter_ends = [k for k, _ in quarter_sorted]
    annual_labels = {k: v[1] for k, v in annual_sorted}
    quarter_labels = {k: v[1] for k, v in quarter_sorted}
    return annual_ends, quarter_ends, annual_labels, quarter_labels


def _sec_value_for_end(companyfacts: Dict[str, Any], tags: List[str], statement_type: str, end: str, period_type: str) -> Tuple[float, str]:
    """Find a value for a specific period by trying all candidate tags.

    This solves the missing older-year problem when the newest tag does not cover
    the company's full history.
    """
    best_value = np.nan
    best_unit = ""
    best_filed = pd.Timestamp.min

    for tag, unit, df in _sec_all_fact_records(companyfacts, tags):
        annual, quarterly = _sec_split_periods(df, statement_type)
        sub = annual if period_type == "annual" else quarterly
        if sub.empty:
            continue

        match = sub[sub["end"].astype(str) == str(end)].sort_values("filed_dt", ascending=True)
        if match.empty:
            continue

        rr = match.iloc[-1]
        filed_dt = rr.get("filed_dt", pd.Timestamp.min)
        if pd.isna(filed_dt):
            filed_dt = pd.Timestamp.min

        if pd.isna(best_value) or filed_dt >= best_filed:
            try:
                best_value = float(rr["val"])
                best_unit = str(rr.get("unit", unit))
                best_filed = filed_dt
            except Exception:
                pass

    return best_value, best_unit


def build_sec_statement_table(companyfacts: Dict[str, Any], statement_type: str) -> pd.DataFrame:
    """First SEC/XBRL consolidated statement builder using official SEC companyfacts."""
    if not isinstance(companyfacts, dict) or "facts" not in companyfacts:
        return pd.DataFrame({"Line Item": ["NO SEC COMPANYFACTS DATA RETURNED"], "Status": ["Check ticker/CIK or SEC availability"]})

    annual_ends, quarter_ends, annual_labels, quarter_labels = _sec_period_labels(companyfacts, statement_type)
    display_cols = [annual_labels[e] for e in annual_ends] + [quarter_labels[e] for e in quarter_ends]

    if not display_cols:
        return pd.DataFrame({"Line Item": ["NO MAPPED SEC STATEMENT DATA FOUND"], "Status": ["SEC facts loaded, but mapped tags were unavailable for this company"]})

    rows: List[Dict[str, Any]] = []
    for label, tags, kind in SEC_STATEMENT_MAP[statement_type]:
        if tags is None:
            rows.append({"Line Item": label, **{c: "" for c in display_cols}, "YoY Δ": "", "QoQ Δ": ""})
            continue

        row = {"Line Item": label}
        annual_values = []
        q_value = np.nan
        q_prior = np.nan
        unit_for_row = ""

        if tags == ["__SEC_FCF__"]:
            for end in annual_ends:
                ocf, unit = _sec_value_for_end(companyfacts, ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"], "cashflow", end, "annual")
                capex, _ = _sec_value_for_end(companyfacts, ["PaymentsToAcquirePropertyPlantAndEquipment", "CapitalExpenditures"], "cashflow", end, "annual")
                value = ocf - abs(capex) if not pd.isna(ocf) and not pd.isna(capex) else np.nan
                unit_for_row = unit
                annual_values.append(value)
                row[annual_labels[end]] = _sec_format_value(value, unit, kind)

            for end in quarter_ends:
                ocf, unit = _sec_value_for_end(companyfacts, ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"], "cashflow", end, "quarterly")
                capex, _ = _sec_value_for_end(companyfacts, ["PaymentsToAcquirePropertyPlantAndEquipment", "CapitalExpenditures"], "cashflow", end, "quarterly")
                q_value = ocf - abs(capex) if not pd.isna(ocf) and not pd.isna(capex) else np.nan
                unit_for_row = unit
                row[quarter_labels[end]] = _sec_format_value(q_value, unit, kind)
        else:
            for end in annual_ends:
                value, unit = _sec_value_for_end(companyfacts, tags, statement_type, end, "annual")
                unit_for_row = unit
                annual_values.append(value)
                row[annual_labels[end]] = _sec_format_value(value, unit, kind)

            for end in quarter_ends:
                q_value, unit = _sec_value_for_end(companyfacts, tags, statement_type, end, "quarterly")
                unit_for_row = unit
                row[quarter_labels[end]] = _sec_format_value(q_value, unit, kind)

        if len(annual_values) >= 2 and not pd.isna(annual_values[-1]) and not pd.isna(annual_values[-2]) and annual_values[-2] != 0:
            row["YoY Δ"] = fmt_pct(((annual_values[-1] / annual_values[-2]) - 1) * 100)
        else:
            row["YoY Δ"] = "—"

        row["QoQ Δ"] = "—"
        rows.append(row)

    return pd.DataFrame(rows)


def render_sec_source_box(ticker: str, sec_info: Dict[str, Any], filings_df: pd.DataFrame) -> None:
    if not sec_info:
        st.warning("SEC source unavailable for this ticker. Falling back to yfinance where available.")
        return

    filing_note = ""
    if isinstance(filings_df, pd.DataFrame) and not filings_df.empty:
        latest = filings_df.iloc[0]
        filing_note = f" Latest filing: {latest.get('Form', '')} filed {latest.get('Filing Date', '')}, period ended {latest.get('Period End', '')}."

    render_summary_box(
        "SEC filing source",
        f"{ticker.upper()} maps to CIK {sec_info.get('cik10', '')}. Statements below use official SEC companyfacts/XBRL where mapped tags are available. Quarter labels use calendar period-end quarters to avoid confusing fiscal-quarter labels.{filing_note}"
    )


def _coerce_money_from_display(value: Any) -> float:
    if value is None or pd.isna(value):
        return np.nan
    s = str(value).replace("$", "").replace(",", "").replace("(", "-").replace(")", "").strip()
    if s in {"", "—", "-"}:
        return np.nan
    mult = 1.0
    upper = s.upper()
    if upper.endswith("B"):
        mult = 1000.0
        s = s[:-1]
    elif upper.endswith("M"):
        mult = 1.0
        s = s[:-1]
    try:
        return float(s) * mult
    except Exception:
        return np.nan


def _latest_numeric_from_table(df: pd.DataFrame, line_item_keywords: List[str], exclude_keywords: Optional[List[str]] = None) -> float:
    if df is None or df.empty or "Line Item" not in df.columns:
        return np.nan

    exclude_keywords = exclude_keywords or []
    labels = df["Line Item"].astype(str).str.lower().str.strip()

    def is_match(label: str) -> bool:
        if any(ex.lower() in label for ex in exclude_keywords):
            return False
        return any(k.lower() in label for k in line_item_keywords)

    matches = df[labels.apply(is_match)]
    if matches.empty:
        return np.nan

    # Prefer the most direct revenue/profit line instead of accidentally taking cost-of-revenue.
    preferred_order = [
        "total revenue",
        "revenue",
        "gross profit",
        "operating income",
        "net income",
        "free cash flow",
        "operating cash flow",
        "total assets",
        "total debt",
        "stockholders' equity",
        "cash & equivalents",
    ]
    for preferred in preferred_order:
        preferred_matches = matches[matches["Line Item"].astype(str).str.lower().str.strip() == preferred]
        if not preferred_matches.empty:
            matches = preferred_matches
            break

    row = matches.iloc[0]
    for col in reversed(list(df.columns)):
        if col in {"Line Item", "YoY Δ", "QoQ Δ", "Margin", "Status"}:
            continue
        val = _coerce_money_from_display(row.get(col))
        if not pd.isna(val):
            return val
    return np.nan


def _latest_percent_from_table(df: pd.DataFrame, line_item_keywords: List[str], col_name: str = "Margin") -> float:
    if df is None or df.empty or "Line Item" not in df.columns or col_name not in df.columns:
        return np.nan
    matches = df[df["Line Item"].astype(str).str.lower().apply(lambda x: any(k.lower() in x for k in line_item_keywords))]
    if matches.empty:
        return np.nan
    s = str(matches.iloc[-1].get(col_name, "")).replace("%", "").replace("+", "").strip()
    try:
        return float(s)
    except Exception:
        return np.nan


def make_income_summary(df: pd.DataFrame) -> str:
    revenue = _latest_numeric_from_table(df, ["total revenue", "revenue"], exclude_keywords=["cost", "expense"])
    shareholder_returns = _latest_numeric_from_table(df, ["total returns", "divs + buybacks"])
    gross_margin = _latest_percent_from_table(df, ["gross profit"])
    op_margin = _latest_percent_from_table(df, ["operating income"])
    net_margin = _latest_percent_from_table(df, ["net income"])
    parts = []
    if not pd.isna(revenue):
        parts.append(f"Latest revenue shown is about ${revenue/1000:,.2f}B.")
    if not pd.isna(gross_margin):
        parts.append(f"Gross margin is {gross_margin:.1f}%, which frames the quality of the business model.")
    if not pd.isna(op_margin):
        parts.append(f"Operating margin is {op_margin:.1f}%, showing current operating leverage.")
    if not pd.isna(net_margin):
        parts.append(f"Net margin is {net_margin:.1f}%, the cleanest quick read on bottom-line conversion.")
    if not pd.isna(shareholder_returns):
        parts.append(f"Shareholder return: latest dividends plus buybacks were about ${shareholder_returns/1000:,.2f}B.")
    return " ".join(parts) if parts else "I could not calculate a clean income-statement read from the available rows."


def make_balance_summary(df: pd.DataFrame) -> str:
    cash = _latest_numeric_from_table(df, ["cash", "cash & equivalents"])
    debt = _latest_numeric_from_table(df, ["total debt"])
    assets = _latest_numeric_from_table(df, ["total assets"])
    equity = _latest_numeric_from_table(df, ["equity"])
    parts = []
    if not pd.isna(cash):
        parts.append(f"Cash and equivalents are about ${cash/1000:,.2f}B.")
    if not pd.isna(debt):
        parts.append(f"Total debt is about ${debt/1000:,.2f}B.")
    if not pd.isna(cash) and not pd.isna(debt):
        parts.append(f"Net cash/debt position is roughly ${(cash-debt)/1000:,.2f}B.")
    if not pd.isna(assets) and not pd.isna(equity) and assets:
        parts.append(f"Equity represents about {equity/assets*100:.1f}% of total assets.")
    return " ".join(parts) if parts else "I could not calculate a clean balance-sheet read from the available rows."


def make_cashflow_summary(df: pd.DataFrame) -> str:
    ocf = _latest_numeric_from_table(df, ["operating cash flow"])
    capex = _latest_numeric_from_table(df, ["capital expenditure"])
    fcf = _latest_numeric_from_table(df, ["free cash flow"])
    parts = []
    if not pd.isna(ocf):
        parts.append(f"Operating cash flow is about ${ocf/1000:,.2f}B.")
    if not pd.isna(capex):
        parts.append(f"Capex is about ${capex/1000:,.2f}B.")
    if not pd.isna(fcf):
        parts.append(f"Free cash flow is about ${fcf/1000:,.2f}B.")
    if not pd.isna(ocf) and not pd.isna(fcf) and ocf:
        parts.append(f"FCF conversion from operating cash flow is roughly {fcf/ocf*100:.1f}%.")
    return " ".join(parts) if parts else "I could not calculate a clean cash-flow read from the available rows."


def make_growth_summary(df: pd.DataFrame) -> str:
    if df is None or df.empty or "Revenue" not in df.columns:
        return "No annual financial history was returned for this ticker."
    clean = df.dropna(subset=["Revenue"]).copy()
    if len(clean) < 2:
        return "Not enough annual revenue history to judge the growth trend."
    start = float(clean["Revenue"].iloc[0])
    end = float(clean["Revenue"].iloc[-1])
    periods = max(len(clean) - 1, 1)
    cagr = calc_cagr(start, end, periods) * 100 if start > 0 and end > 0 else np.nan
    margin_note = ""
    if "Net Margin %" in clean.columns and not clean["Net Margin %"].dropna().empty:
        margin_note = f" Latest net margin is {clean['Net Margin %'].dropna().iloc[-1]:.1f}%."
    return f"Revenue moved from ${start/1000:,.2f}B to ${end/1000:,.2f}B over the available annual period, implying about {cagr:.1f}% CAGR.{margin_note}"


def render_summary_box(title: str, text_value: str) -> None:
    st.markdown(
        f"""
<div class="card">
  <div style="font-weight:800;color:#a29bfe;letter-spacing:.08em;text-transform:uppercase;font-size:.78rem;margin-bottom:6px">{_html_escape(title)}</div>
  <div style="color:#e8e8f2;line-height:1.65">{_html_escape(text_value)}</div>
</div>
""",
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def fetch_outlook_from_web(ticker: str, company_name: str) -> pd.DataFrame:
    if requests is None or BeautifulSoup is None:
        return pd.DataFrame([{"Source": "Unavailable", "Outlook Item": "requests/beautifulsoup are not installed.", "URL": ""}])

    query = f"{ticker} {company_name} latest earnings call transcript outlook guidance segments"
    headers = {"User-Agent": "Mozilla/5.0 FinancialDashboardBuilder/1.0"}
    rows = []

    try:
        r = requests.get("https://duckduckgo.com/html/", params={"q": query}, headers=headers, timeout=12)
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.select("a.result__a")[:6]:
            href = a.get("href", "")
            title = a.get_text(" ", strip=True)
            if href:
                links.append((title, href))

        keywords = ["outlook", "guidance", "segment", "segments", "revenue", "demand", "margin", "growth", "earnings call", "transcript"]
        for title, url in links[:4]:
            try:
                page = requests.get(url, headers=headers, timeout=12)
                page_soup = BeautifulSoup(page.text, "html.parser")
                text_blob = " ".join(p.get_text(" ", strip=True) for p in page_soup.find_all(["p", "li"])[:160])
                sentences = re.split(r"(?<=[.!?])\s+", text_blob)
                picked = []
                for s in sentences:
                    lower = s.lower()
                    if len(s) > 70 and any(k in lower for k in keywords):
                        picked.append(s[:450])
                    if len(picked) >= 4:
                        break
                if picked:
                    rows.append({"Source": title[:90], "Outlook Item": " ".join(picked), "URL": url})
            except Exception:
                continue
            if len(rows) >= 4:
                break
    except Exception as e:
        rows.append({"Source": "Web fetch failed", "Outlook Item": str(e), "URL": ""})

    if not rows:
        rows.append({"Source": "No transcript/outlook result found", "Outlook Item": "No clean public earnings-call or outlook text was found from the web search. Financial tables still use yfinance data.", "URL": ""})
    return pd.DataFrame(rows)


def build_business_mix_view(fundamentals: Dict[str, Any], market_data: Dict[str, Any], ticker: str, company_name: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    annual = build_live_annual_metrics(fundamentals)
    rows = []
    if not annual.empty and "Revenue" in annual.columns:
        clean = annual.dropna(subset=["Revenue"]).copy()
        if len(clean) >= 2:
            latest = clean.iloc[-1]
            prev = clean.iloc[-2]
            growth = safe_div(latest["Revenue"], prev["Revenue"]) - 1 if prev["Revenue"] else np.nan
            rows.append({"Metric": "Annual Revenue Growth", "Value": f"{growth*100:.1f}%" if not pd.isna(growth) else "—", "Read": "Latest fiscal year versus prior fiscal year"})
            for col in ["Gross Margin %", "Operating Margin %", "Net Margin %"]:
                if col in latest and not pd.isna(latest.get(col, np.nan)):
                    rows.append({"Metric": col.replace(" %", ""), "Value": f"{latest.get(col):.1f}%", "Read": "Latest fiscal year"})
    if not rows:
        rows.append({"Metric": "Business Mix", "Value": "—", "Read": "Segment-level revenue is not consistently available from free yfinance data."})
    outlook = fetch_outlook_from_web(ticker, company_name)
    return pd.DataFrame(rows), outlook


def _fmt_ratio_value(value: Any, suffix: str = "x", decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "—"
    try:
        v = float(value)
        if abs(v) >= 100:
            return f"{v:,.0f}{suffix}"
        return f"{v:,.{decimals}f}{suffix}"
    except Exception:
        return "—"


def _fmt_percent_value(value: Any, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "—"
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except Exception:
        return "—"


def _latest_annual_value(fundamentals: Dict[str, Any], statement_key: str, possible_names: List[str]) -> float:
    raw = fundamentals.get(statement_key, pd.DataFrame()) if isinstance(fundamentals, dict) else pd.DataFrame()
    if raw is None or raw.empty:
        return np.nan
    cols = list(raw.columns)
    try:
        cols = sorted(cols, key=lambda c: pd.to_datetime(c), reverse=True)
    except Exception:
        pass
    if not cols:
        return np.nan
    return _get_statement_value(raw, possible_names, cols[0])


def build_ratio_dashboard(
    fundamentals: Dict[str, Any],
    quote: Dict[str, Any],
    current_price: float,
    market_cap_b: float,
    shares_b: float,
    revenue_base_b: float,
    projection_anchor: Dict[str, float],
) -> pd.DataFrame:
    """Build a compact ratio dashboard with typical ranges and brief interpretation."""
    income_q = fundamentals.get("income", pd.DataFrame()) if isinstance(fundamentals, dict) else pd.DataFrame()
    balance_q = fundamentals.get("balance", pd.DataFrame()) if isinstance(fundamentals, dict) else pd.DataFrame()
    cash_q = fundamentals.get("cashflow", pd.DataFrame()) if isinstance(fundamentals, dict) else pd.DataFrame()

    current_price = float(current_price) if current_price is not None and not pd.isna(current_price) and float(current_price) > 0 else np.nan
    market_cap_b = float(market_cap_b) if market_cap_b is not None and not pd.isna(market_cap_b) and float(market_cap_b) > 0 else np.nan
    shares_b = float(shares_b) if shares_b is not None and not pd.isna(shares_b) and float(shares_b) > 0 else np.nan

    ttm_revenue_b = float(projection_anchor.get("revenue_b", np.nan))
    ttm_net_income_b = float(projection_anchor.get("net_income_b", np.nan))
    ttm_eps = float(projection_anchor.get("eps", np.nan))
    ttm_net_margin = float(projection_anchor.get("net_margin", np.nan))

    ttm_fcf_raw = _ttm_sum(cash_q, ["Free Cash Flow"])
    ttm_fcf_b = ttm_fcf_raw / 1_000_000_000 if not pd.isna(ttm_fcf_raw) else np.nan

    latest_assets_raw = _latest_statement_value(balance_q, ["Total Assets"])
    latest_equity_raw = _latest_statement_value(balance_q, ["Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity"])
    latest_debt_raw = _latest_statement_value(balance_q, ["Total Debt", "Long Term Debt And Capital Lease Obligation"])
    latest_cash_raw = _latest_statement_value(balance_q, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"])

    assets_b = latest_assets_raw / 1_000_000_000 if not pd.isna(latest_assets_raw) else np.nan
    equity_b = latest_equity_raw / 1_000_000_000 if not pd.isna(latest_equity_raw) else np.nan
    debt_b = latest_debt_raw / 1_000_000_000 if not pd.isna(latest_debt_raw) else np.nan
    cash_b = latest_cash_raw / 1_000_000_000 if not pd.isna(latest_cash_raw) else np.nan

    annual_growth = _historical_revenue_cagr_from_fundamentals(fundamentals)
    latest_growth = _recent_revenue_growth_from_fundamentals(fundamentals)
    growth_for_peg = latest_growth if not pd.isna(latest_growth) else annual_growth

    trailing_pe = quote.get("trailing_pe") if isinstance(quote, dict) else np.nan
    forward_pe = quote.get("forward_pe") if isinstance(quote, dict) else np.nan
    if trailing_pe is None or pd.isna(trailing_pe):
        trailing_pe = safe_div(current_price, ttm_eps)

    price_to_sales = safe_div(market_cap_b, ttm_revenue_b)
    price_to_fcf = safe_div(market_cap_b, ttm_fcf_b)
    price_to_book = safe_div(market_cap_b, equity_b)
    ev_b = market_cap_b + (0 if pd.isna(debt_b) else debt_b) - (0 if pd.isna(cash_b) else cash_b)
    ev_sales = safe_div(ev_b, ttm_revenue_b)
    ev_fcf = safe_div(ev_b, ttm_fcf_b)
    roe = safe_div(ttm_net_income_b, equity_b)
    roa = safe_div(ttm_net_income_b, assets_b)
    debt_to_equity = safe_div(debt_b, equity_b)
    net_cash_b = (cash_b - debt_b) if not pd.isna(cash_b) and not pd.isna(debt_b) else np.nan
    fcf_margin = safe_div(ttm_fcf_b, ttm_revenue_b)
    earnings_yield = safe_div(1, trailing_pe)
    fcf_yield = safe_div(ttm_fcf_b, market_cap_b)
    peg = safe_div(trailing_pe, growth_for_peg * 100) if not pd.isna(growth_for_peg) and growth_for_peg > 0 else np.nan

    rows = [
        {
            "Ratio": "P/E",
            "Value": _fmt_ratio_value(trailing_pe),
            "Typical Range": "10–25x mature; 25–50x growth",
            "What It Means": "How much investors pay for each dollar of earnings. Higher means more growth is priced in.",
        },
        {
            "Ratio": "Forward P/E",
            "Value": _fmt_ratio_value(forward_pe),
            "Typical Range": "10–25x mature; 25–45x growth",
            "What It Means": "P/E using expected future earnings. Useful when earnings are moving quickly.",
        },
        {
            "Ratio": "P/S",
            "Value": _fmt_ratio_value(price_to_sales),
            "Typical Range": "1–3x normal; 5–15x premium growth",
            "What It Means": "Market cap divided by sales. Helpful when earnings are temporarily depressed or scaling.",
        },
        {
            "Ratio": "PEG",
            "Value": _fmt_ratio_value(peg),
            "Typical Range": "<1 cheap vs growth; 1–2 fair; >2 expensive",
            "What It Means": "P/E divided by growth rate. Tries to adjust valuation for growth.",
        },
        {
            "Ratio": "EV/Sales",
            "Value": _fmt_ratio_value(ev_sales),
            "Typical Range": "1–4x normal; 6–15x premium growth",
            "What It Means": "Enterprise value divided by sales. Adjusts market cap for cash and debt.",
        },
        {
            "Ratio": "P/FCF",
            "Value": _fmt_ratio_value(price_to_fcf),
            "Typical Range": "10–25x normal; 25–50x growth",
            "What It Means": "Market cap divided by free cash flow. Often cleaner than P/E for cash-generative companies.",
        },
        {
            "Ratio": "EV/FCF",
            "Value": _fmt_ratio_value(ev_fcf),
            "Typical Range": "10–25x normal; 25–50x growth",
            "What It Means": "Enterprise value divided by free cash flow. Penalizes debt and rewards cash.",
        },
        {
            "Ratio": "P/B",
            "Value": _fmt_ratio_value(price_to_book),
            "Typical Range": "1–3x common; >5x asset-light/high ROE",
            "What It Means": "Market cap divided by book equity. More useful for banks/asset-heavy firms than software.",
        },
        {
            "Ratio": "Net Margin",
            "Value": _fmt_percent_value(ttm_net_margin),
            "Typical Range": "5–10% okay; 15–25% strong; >25% elite",
            "What It Means": "Net income as a percentage of revenue. Shows bottom-line conversion.",
        },
        {
            "Ratio": "FCF Margin",
            "Value": _fmt_percent_value(fcf_margin),
            "Typical Range": "5–10% okay; 15–25% strong; >25% elite",
            "What It Means": "Free cash flow as a percentage of revenue. Shows cash conversion quality.",
        },
        {
            "Ratio": "ROE",
            "Value": _fmt_percent_value(roe),
            "Typical Range": "10–15% good; >20% strong",
            "What It Means": "Net income divided by equity. Measures return generated on shareholder capital.",
        },
        {
            "Ratio": "ROA",
            "Value": _fmt_percent_value(roa),
            "Typical Range": "5–10% good; >10% strong",
            "What It Means": "Net income divided by total assets. Useful for capital intensity comparisons.",
        },
        {
            "Ratio": "Debt/Equity",
            "Value": _fmt_ratio_value(debt_to_equity),
            "Typical Range": "<0.5x conservative; 0.5–1.5x normal; >2x levered",
            "What It Means": "Debt relative to equity. Higher leverage increases financial risk.",
        },
        {
            "Ratio": "Net Cash / Debt",
            "Value": f"${net_cash_b:,.2f}B" if not pd.isna(net_cash_b) else "—",
            "Typical Range": "Positive is net cash; negative is net debt",
            "What It Means": "Cash minus debt. Positive means the company has more cash than debt.",
        },
        {
            "Ratio": "Earnings Yield",
            "Value": _fmt_percent_value(earnings_yield),
            "Typical Range": "4–8% common; higher may be cheaper/cyclical",
            "What It Means": "Inverse of P/E. Shows earnings as a percentage of stock price.",
        },
        {
            "Ratio": "FCF Yield",
            "Value": _fmt_percent_value(fcf_yield),
            "Typical Range": "3–6% okay; >6% attractive if durable",
            "What It Means": "Free cash flow divided by market cap. A cash-return lens on valuation.",
        },
        {
            "Ratio": "Revenue CAGR",
            "Value": _fmt_percent_value(annual_growth),
            "Typical Range": "0–5% slow; 5–15% solid; >20% high growth",
            "What It Means": "Historical annualized revenue growth over available years.",
        },
        {
            "Ratio": "Latest FY Growth",
            "Value": _fmt_percent_value(latest_growth),
            "Typical Range": "0–5% slow; 5–15% solid; >20% high growth",
            "What It Means": "Latest fiscal year revenue growth versus the prior fiscal year.",
        },
    ]

    return pd.DataFrame(rows)


def make_ratio_summary(ratios: pd.DataFrame) -> str:
    if ratios is None or ratios.empty:
        return "No ratio data was available."
    lookup = {str(r["Ratio"]): str(r["Value"]) for _, r in ratios.iterrows()}
    return (
        f"Key valuation snapshot: P/E {lookup.get('P/E', '—')}, P/S {lookup.get('P/S', '—')}, "
        f"PEG {lookup.get('PEG', '—')}, P/FCF {lookup.get('P/FCF', '—')}. "
        f"Quality snapshot: net margin {lookup.get('Net Margin', '—')}, FCF margin {lookup.get('FCF Margin', '—')}, "
        f"ROE {lookup.get('ROE', '—')}."
    )

def _parse_ratio_number(value: Any) -> float:
    if value is None or pd.isna(value):
        return np.nan
    s = str(value).strip().replace("$", "").replace(",", "").replace("x", "").replace("%", "")
    if s in {"", "—", "-", "nan"}:
        return np.nan
    multiplier = 1.0
    upper = s.upper()
    if upper.endswith("B"):
        multiplier = 1_000.0
        s = s[:-1]
    elif upper.endswith("M"):
        multiplier = 1.0
        s = s[:-1]
    try:
        return float(s) * multiplier
    except Exception:
        return np.nan


def _ratio_lookup(ratio_df: pd.DataFrame, ratio_name: str) -> str:
    if ratio_df is None or ratio_df.empty or "Ratio" not in ratio_df.columns:
        return "—"
    match = ratio_df[ratio_df["Ratio"].astype(str).str.lower() == ratio_name.lower()]
    if match.empty:
        return "—"
    return str(match.iloc[0].get("Value", "—"))


def _peer_metric_value(peer_row: Dict[str, Any], metric: str) -> float:
    return _parse_ratio_number(peer_row.get(metric, np.nan))


def _last_history_price(market_data: Dict[str, Any]) -> float:
    hist = market_data.get("history", pd.DataFrame()) if isinstance(market_data, dict) else pd.DataFrame()
    if isinstance(hist, pd.DataFrame) and not hist.empty and "Close" in hist.columns:
        close = pd.to_numeric(hist["Close"], errors="coerce").dropna()
        if not close.empty:
            return float(close.iloc[-1])
    return np.nan


def _shares_from_fundamentals(fundamentals: Dict[str, Any]) -> float:
    income = fundamentals.get("income", pd.DataFrame()) if isinstance(fundamentals, dict) else pd.DataFrame()
    annual_income = fundamentals.get("annual_income", pd.DataFrame()) if isinstance(fundamentals, dict) else pd.DataFrame()
    for raw in [income, annual_income]:
        shares_raw = _latest_statement_value(raw, ["Diluted Average Shares", "Basic Average Shares", "Ordinary Shares Number"])
        if not pd.isna(shares_raw) and shares_raw > 0:
            return float(shares_raw) / 1_000_000_000
    return np.nan


def _quote_with_fallbacks(peer_ticker: str, peer_market: Dict[str, Any], peer_fundamentals: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    quote = dict(peer_market.get("quote", {}) if isinstance(peer_market, dict) else {})
    status_parts = []

    price = quote.get("last_price")
    if price is None or pd.isna(price) or price <= 0:
        price = _last_history_price(peer_market)
        if not pd.isna(price):
            status_parts.append("price from history")

    shares_b = (quote.get("shares") / 1e9) if quote.get("shares") else np.nan
    if pd.isna(shares_b) or shares_b <= 0:
        shares_b = _shares_from_fundamentals(peer_fundamentals)
        if not pd.isna(shares_b):
            status_parts.append("shares from statements")

    market_cap_b = (quote.get("market_cap") / 1e9) if quote.get("market_cap") else np.nan
    if (pd.isna(market_cap_b) or market_cap_b <= 0) and not pd.isna(price) and not pd.isna(shares_b) and shares_b > 0:
        market_cap_b = price * shares_b
        status_parts.append("market cap estimated")

    if price is not None and not pd.isna(price) and price > 0:
        quote["last_price"] = float(price)
    if not pd.isna(shares_b) and shares_b > 0:
        quote["shares"] = float(shares_b) * 1_000_000_000
    if not pd.isna(market_cap_b) and market_cap_b > 0:
        quote["market_cap"] = float(market_cap_b) * 1_000_000_000

    if not quote.get("long_name"):
        quote["long_name"] = peer_ticker

    status = ", ".join(status_parts) if status_parts else "live quote"
    if not quote.get("last_price") or not quote.get("market_cap"):
        status = "partial data"
    return quote, status




@st.cache_data(ttl=60 * 45, show_spinner=False)
def get_peer_market_light(ticker: str) -> Dict[str, Any]:
    """Lightweight peer quote fetch for comparison tab.

    This intentionally avoids analyst targets, recommendations, insider data, and most of Ticker.info.
    Those calls are much more likely to trigger Yahoo/yfinance rate limits.
    """
    result: Dict[str, Any] = {
        "ticker": ticker.upper(),
        "quote": {},
        "history": pd.DataFrame(),
        "errors": [],
    }
    if yf is None:
        result["errors"].append("yfinance is not installed.")
        return result

    try:
        t = yf.Ticker(ticker)

        try:
            hist = t.history(period="5d", interval="1d", auto_adjust=False)
            if isinstance(hist, pd.DataFrame):
                result["history"] = hist.copy()
        except Exception as e:
            result["errors"].append(f"history fetch failed: {e}")

        try:
            fi = getattr(t, "fast_info", {}) or {}
            last_price = None
            market_cap = None
            shares = None

            for key in ["last_price", "lastPrice", "regular_market_price", "regularMarketPrice", "previous_close", "previousClose"]:
                try:
                    candidate = fi.get(key)
                    if candidate is not None and not pd.isna(candidate) and float(candidate) > 0:
                        last_price = float(candidate)
                        break
                except Exception:
                    pass

            for key in ["market_cap", "marketCap"]:
                try:
                    candidate = fi.get(key)
                    if candidate is not None and not pd.isna(candidate) and float(candidate) > 0:
                        market_cap = float(candidate)
                        break
                except Exception:
                    pass

            for key in ["shares", "shares_outstanding", "sharesOutstanding"]:
                try:
                    candidate = fi.get(key)
                    if candidate is not None and not pd.isna(candidate) and float(candidate) > 0:
                        shares = float(candidate)
                        break
                except Exception:
                    pass

            if last_price is None:
                hist_price = _last_history_price(result)
                if not pd.isna(hist_price):
                    last_price = float(hist_price)

            result["quote"] = {
                "last_price": last_price,
                "market_cap": market_cap,
                "shares": shares,
                "long_name": ticker.upper(),
                "trailing_pe": None,
                "forward_pe": None,
                "currency": "USD",
            }
        except Exception as e:
            result["errors"].append(f"fast_info fetch failed: {e}")

    except Exception as e:
        result["errors"].append(f"light peer market fetch failed: {e}")

    return result


@st.cache_data(ttl=60 * 45, show_spinner=False)
def build_single_peer_row(peer_ticker: str) -> Dict[str, Any]:
    """Fetch one peer so the UI can display real per-company progress."""
    peer_ticker = peer_ticker.upper().strip()

    peer_market = get_peer_market_light(peer_ticker)
    time.sleep(2.0)
    peer_fundamentals = get_yf_fundamentals(peer_ticker)
    peer_quote_raw = peer_market.get("quote", {}) if isinstance(peer_market, dict) else {}
    peer_quote, data_status = _quote_with_fallbacks(peer_ticker, peer_market, peer_fundamentals)

    peer_price = peer_quote.get("last_price") if peer_quote.get("last_price") else np.nan
    peer_shares_b = (peer_quote.get("shares") / 1e9) if peer_quote.get("shares") else _shares_from_fundamentals(peer_fundamentals)
    peer_market_cap_b = (peer_quote.get("market_cap") / 1e9) if peer_quote.get("market_cap") else np.nan

    peer_revenue_base_b = compute_start_revenue_from_live(peer_fundamentals, np.nan)
    peer_anchor = get_projection_anchor(
        peer_fundamentals,
        peer_quote,
        peer_revenue_base_b,
        peer_shares_b if not pd.isna(peer_shares_b) and peer_shares_b > 0 else np.nan,
        peer_price if not pd.isna(peer_price) else np.nan,
    )

    if (pd.isna(peer_market_cap_b) or peer_market_cap_b <= 0) and not pd.isna(peer_price) and not pd.isna(peer_anchor.get("shares_b", np.nan)):
        peer_market_cap_b = peer_price * peer_anchor.get("shares_b")

    peer_ratio_df = build_ratio_dashboard(
        peer_fundamentals,
        peer_quote,
        peer_price if not pd.isna(peer_price) else np.nan,
        peer_market_cap_b if not pd.isna(peer_market_cap_b) else np.nan,
        peer_anchor.get("shares_b", np.nan),
        peer_revenue_base_b if not pd.isna(peer_revenue_base_b) else np.nan,
        peer_anchor,
    )

    errors = []
    errors.extend(peer_market.get("errors", []) if isinstance(peer_market, dict) else [])
    errors.extend(peer_fundamentals.get("errors", []) if isinstance(peer_fundamentals, dict) else [])
    if errors and data_status == "live quote":
        data_status = "some fields rate-limited"

    return {
        "Ticker": peer_ticker,
        "Company": peer_quote.get("long_name") or peer_quote_raw.get("long_name") or peer_ticker,
        "Data Status": data_status,
        "Price": f"${peer_price:,.2f}" if not pd.isna(peer_price) else "—",
        "Market Cap": f"${peer_market_cap_b:,.1f}B" if not pd.isna(peer_market_cap_b) else "—",
        "Revenue TTM": f"${peer_anchor.get('revenue_b', np.nan):,.2f}B" if not pd.isna(peer_anchor.get("revenue_b", np.nan)) else "—",
        "Revenue CAGR": _ratio_lookup(peer_ratio_df, "Revenue CAGR"),
        "Latest FY Growth": _ratio_lookup(peer_ratio_df, "Latest FY Growth"),
        "Net Margin": _ratio_lookup(peer_ratio_df, "Net Margin"),
        "FCF Margin": _ratio_lookup(peer_ratio_df, "FCF Margin"),
        "ROE": _ratio_lookup(peer_ratio_df, "ROE"),
        "ROA": _ratio_lookup(peer_ratio_df, "ROA"),
        "P/E": _ratio_lookup(peer_ratio_df, "P/E"),
        "Forward P/E": _ratio_lookup(peer_ratio_df, "Forward P/E"),
        "P/S": _ratio_lookup(peer_ratio_df, "P/S"),
        "PEG": _ratio_lookup(peer_ratio_df, "PEG"),
        "P/FCF": _ratio_lookup(peer_ratio_df, "P/FCF"),
        "EV/Sales": _ratio_lookup(peer_ratio_df, "EV/Sales"),
        "Debt/Equity": _ratio_lookup(peer_ratio_df, "Debt/Equity"),
        "Net Cash / Debt": _ratio_lookup(peer_ratio_df, "Net Cash / Debt"),
        "FCF Yield": _ratio_lookup(peer_ratio_df, "FCF Yield"),
        "Earnings Yield": _ratio_lookup(peer_ratio_df, "Earnings Yield"),
    }


def build_peer_scorecard_from_rows(peer_df: pd.DataFrame) -> pd.DataFrame:
    """Build peer scorecard from already fetched rows."""
    if peer_df is None or peer_df.empty:
        return pd.DataFrame()

    score_rows = []
    for _, r in peer_df.iterrows():
        d = r.to_dict()
        growth_score = np.nanmean([_peer_metric_value(d, "Revenue CAGR"), _peer_metric_value(d, "Latest FY Growth")])
        profitability_score = np.nanmean([_peer_metric_value(d, "Net Margin"), _peer_metric_value(d, "FCF Margin"), _peer_metric_value(d, "ROE")])
        balance_score = np.nanmean([
            -_peer_metric_value(d, "Debt/Equity") if not pd.isna(_peer_metric_value(d, "Debt/Equity")) else np.nan,
            _peer_metric_value(d, "Net Cash / Debt"),
        ])
        valuation_score = np.nanmean([
            -_peer_metric_value(d, "P/E"),
            -_peer_metric_value(d, "Forward P/E"),
            -_peer_metric_value(d, "P/S"),
            -_peer_metric_value(d, "PEG"),
            -_peer_metric_value(d, "P/FCF"),
            _peer_metric_value(d, "FCF Yield"),
            _peer_metric_value(d, "Earnings Yield"),
        ])
        score_rows.append({
            "Ticker": d["Ticker"],
            "Growth Raw": growth_score,
            "Profitability Raw": profitability_score,
            "Valuation Raw": valuation_score,
            "Balance Sheet Raw": balance_score,
        })

    score_df = pd.DataFrame(score_rows)

    def percentile_score(series: pd.Series) -> pd.Series:
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().sum() <= 1:
            return pd.Series([50 if not pd.isna(x) else np.nan for x in numeric], index=series.index)
        return numeric.rank(pct=True, ascending=True) * 100

    score_df["Growth Score"] = percentile_score(score_df["Growth Raw"])
    score_df["Profitability Score"] = percentile_score(score_df["Profitability Raw"])
    score_df["Valuation Score"] = percentile_score(score_df["Valuation Raw"])
    score_df["Balance Sheet Score"] = percentile_score(score_df["Balance Sheet Raw"])
    score_df["Overall Score"] = score_df[["Growth Score", "Profitability Score", "Valuation Score", "Balance Sheet Score"]].mean(axis=1)
    score_df = score_df.sort_values("Overall Score", ascending=False)

    display_scores = score_df[["Ticker", "Growth Score", "Profitability Score", "Valuation Score", "Balance Sheet Score", "Overall Score"]].copy()
    for c in display_scores.columns:
        if c != "Ticker":
            display_scores[c] = display_scores[c].map(lambda x: f"{x:,.0f}" if not pd.isna(x) else "—")
    return display_scores


@st.cache_data(ttl=60 * 45, show_spinner=False)
def build_peer_comparison_data(ticker_list: Tuple[str, ...], request_delay_seconds: float = 0.0) -> Tuple[pd.DataFrame, pd.DataFrame]:
    peer_rows: List[Dict[str, Any]] = []

    for idx, peer_ticker in enumerate(ticker_list):
        peer_ticker = peer_ticker.upper().strip()
        if not peer_ticker:
            continue

        if idx > 0 and request_delay_seconds and request_delay_seconds > 0:
            time.sleep(float(request_delay_seconds))

        peer_market = get_market_data(peer_ticker)
        peer_fundamentals = get_yf_fundamentals(peer_ticker)
        peer_quote_raw = peer_market.get("quote", {}) if isinstance(peer_market, dict) else {}
        peer_quote, data_status = _quote_with_fallbacks(peer_ticker, peer_market, peer_fundamentals)

        peer_price = peer_quote.get("last_price") if peer_quote.get("last_price") else np.nan
        peer_shares_b = (peer_quote.get("shares") / 1e9) if peer_quote.get("shares") else _shares_from_fundamentals(peer_fundamentals)
        peer_market_cap_b = (peer_quote.get("market_cap") / 1e9) if peer_quote.get("market_cap") else np.nan

        peer_revenue_base_b = compute_start_revenue_from_live(peer_fundamentals, np.nan)
        peer_anchor = get_projection_anchor(
            peer_fundamentals,
            peer_quote,
            peer_revenue_base_b,
            peer_shares_b if not pd.isna(peer_shares_b) and peer_shares_b > 0 else np.nan,
            peer_price if not pd.isna(peer_price) else np.nan,
        )

        if (pd.isna(peer_market_cap_b) or peer_market_cap_b <= 0) and not pd.isna(peer_price) and not pd.isna(peer_anchor.get("shares_b", np.nan)):
            peer_market_cap_b = peer_price * peer_anchor.get("shares_b")

        peer_ratio_df = build_ratio_dashboard(
            peer_fundamentals,
            peer_quote,
            peer_price if not pd.isna(peer_price) else np.nan,
            peer_market_cap_b if not pd.isna(peer_market_cap_b) else np.nan,
            peer_anchor.get("shares_b", np.nan),
            peer_revenue_base_b if not pd.isna(peer_revenue_base_b) else np.nan,
            peer_anchor,
        )

        errors = []
        errors.extend(peer_market.get("errors", []) if isinstance(peer_market, dict) else [])
        errors.extend(peer_fundamentals.get("errors", []) if isinstance(peer_fundamentals, dict) else [])
        if errors and data_status == "live quote":
            data_status = "some fields rate-limited"

        row = {
            "Ticker": peer_ticker,
            "Company": peer_quote.get("long_name") or peer_quote_raw.get("long_name") or peer_ticker,
            "Data Status": data_status,
            "Price": f"${peer_price:,.2f}" if not pd.isna(peer_price) else "—",
            "Market Cap": f"${peer_market_cap_b:,.1f}B" if not pd.isna(peer_market_cap_b) else "—",
            "Revenue TTM": f"${peer_anchor.get('revenue_b', np.nan):,.2f}B" if not pd.isna(peer_anchor.get("revenue_b", np.nan)) else "—",
            "Revenue CAGR": _ratio_lookup(peer_ratio_df, "Revenue CAGR"),
            "Latest FY Growth": _ratio_lookup(peer_ratio_df, "Latest FY Growth"),
            "Net Margin": _ratio_lookup(peer_ratio_df, "Net Margin"),
            "FCF Margin": _ratio_lookup(peer_ratio_df, "FCF Margin"),
            "ROE": _ratio_lookup(peer_ratio_df, "ROE"),
            "ROA": _ratio_lookup(peer_ratio_df, "ROA"),
            "P/E": _ratio_lookup(peer_ratio_df, "P/E"),
            "Forward P/E": _ratio_lookup(peer_ratio_df, "Forward P/E"),
            "P/S": _ratio_lookup(peer_ratio_df, "P/S"),
            "PEG": _ratio_lookup(peer_ratio_df, "PEG"),
            "P/FCF": _ratio_lookup(peer_ratio_df, "P/FCF"),
            "EV/Sales": _ratio_lookup(peer_ratio_df, "EV/Sales"),
            "Debt/Equity": _ratio_lookup(peer_ratio_df, "Debt/Equity"),
            "Net Cash / Debt": _ratio_lookup(peer_ratio_df, "Net Cash / Debt"),
            "FCF Yield": _ratio_lookup(peer_ratio_df, "FCF Yield"),
            "Earnings Yield": _ratio_lookup(peer_ratio_df, "Earnings Yield"),
        }
        peer_rows.append(row)

    peer_df = pd.DataFrame(peer_rows)
    if peer_df.empty:
        return peer_df, pd.DataFrame()

    score_rows = []
    for _, r in peer_df.iterrows():
        d = r.to_dict()
        growth_score = np.nanmean([_peer_metric_value(d, "Revenue CAGR"), _peer_metric_value(d, "Latest FY Growth")])
        profitability_score = np.nanmean([_peer_metric_value(d, "Net Margin"), _peer_metric_value(d, "FCF Margin"), _peer_metric_value(d, "ROE")])
        balance_score = np.nanmean([
            -_peer_metric_value(d, "Debt/Equity") if not pd.isna(_peer_metric_value(d, "Debt/Equity")) else np.nan,
            _peer_metric_value(d, "Net Cash / Debt"),
        ])
        valuation_score = np.nanmean([
            -_peer_metric_value(d, "P/E"),
            -_peer_metric_value(d, "Forward P/E"),
            -_peer_metric_value(d, "P/S"),
            -_peer_metric_value(d, "PEG"),
            -_peer_metric_value(d, "P/FCF"),
            _peer_metric_value(d, "FCF Yield"),
            _peer_metric_value(d, "Earnings Yield"),
        ])
        score_rows.append({
            "Ticker": d["Ticker"],
            "Growth Raw": growth_score,
            "Profitability Raw": profitability_score,
            "Valuation Raw": valuation_score,
            "Balance Sheet Raw": balance_score,
        })

    score_df = pd.DataFrame(score_rows)

    def percentile_score(series: pd.Series) -> pd.Series:
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().sum() <= 1:
            return pd.Series([50 if not pd.isna(x) else np.nan for x in numeric], index=series.index)
        return numeric.rank(pct=True, ascending=True) * 100

    score_df["Growth Score"] = percentile_score(score_df["Growth Raw"])
    score_df["Profitability Score"] = percentile_score(score_df["Profitability Raw"])
    score_df["Valuation Score"] = percentile_score(score_df["Valuation Raw"])
    score_df["Balance Sheet Score"] = percentile_score(score_df["Balance Sheet Raw"])
    score_df["Overall Score"] = score_df[["Growth Score", "Profitability Score", "Valuation Score", "Balance Sheet Score"]].mean(axis=1)
    score_df = score_df.sort_values("Overall Score", ascending=False)

    display_scores = score_df[["Ticker", "Growth Score", "Profitability Score", "Valuation Score", "Balance Sheet Score", "Overall Score"]].copy()
    for c in display_scores.columns:
        if c != "Ticker":
            display_scores[c] = display_scores[c].map(lambda x: f"{x:,.0f}" if not pd.isna(x) else "—")

    return peer_df, display_scores


def build_peer_summary(peer_df: pd.DataFrame, score_df: pd.DataFrame) -> str:
    if peer_df is None or peer_df.empty:
        return "Enter two or more tickers to generate a peer comparison."

    parts = []
    if score_df is not None and not score_df.empty:
        leader = score_df.iloc[0]["Ticker"]
        parts.append(f"{leader} screens best overall on the current weighted scorecard.")

    def best_by(metric: str, lower_better: bool = False) -> str:
        vals = []
        for _, r in peer_df.iterrows():
            v = _parse_ratio_number(r.get(metric))
            if not pd.isna(v):
                vals.append((r["Ticker"], v))
        if not vals:
            return ""
        vals = sorted(vals, key=lambda x: x[1], reverse=not lower_better)
        return vals[0][0]

    growth_leader = best_by("Revenue CAGR")
    margin_leader = best_by("Net Margin")
    cheap_ps = best_by("P/S", lower_better=True)
    fcf_yield_leader = best_by("FCF Yield")

    if growth_leader:
        parts.append(f"{growth_leader} has the strongest available historical revenue CAGR.")
    if margin_leader:
        parts.append(f"{margin_leader} has the strongest net-margin profile.")
    if cheap_ps:
        parts.append(f"{cheap_ps} screens cheapest on price-to-sales.")
    if fcf_yield_leader:
        parts.append(f"{fcf_yield_leader} has the highest free-cash-flow yield.")

    return " ".join(parts) if parts else "Comparison generated, but some fields are blank because the source data was incomplete."


with st.sidebar:
    st.markdown("### Financial Dashboard Builder")
    ticker = st.text_input("Ticker", value=TICKER_DEFAULT).upper().strip() or TICKER_DEFAULT
    use_live = st.toggle("Use internet data when available", value=True)
    use_sec_statements = st.toggle("Use SEC filing statements when available", value=True)
    if st.button("Refresh live data"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Default ticker uses embedded sample data. Any other ticker switches to a generic live dashboard using yfinance when available.")

projection_years = 5
base_revenue_b = 7.656
fallback_price = 124.0
fallback_shares_b = 2.55

market_data = get_market_data(ticker) if use_live else {"quote": {}, "history": pd.DataFrame(), "errors": []}
fundamentals = get_yf_fundamentals(ticker) if use_live else {"income": pd.DataFrame(), "balance": pd.DataFrame(), "cashflow": pd.DataFrame(), "errors": []}

sec_info = sec_lookup_ticker(ticker) if use_live and use_sec_statements else {}
sec_subs = sec_submissions(sec_info.get("cik10", "")) if sec_info else {}
sec_facts = sec_companyfacts(sec_info.get("cik10", "")) if sec_info else {}
sec_filings = sec_filings_table(sec_subs) if sec_subs else pd.DataFrame()
sec_statements_available = bool(sec_info) and isinstance(sec_facts, dict) and "facts" in sec_facts

quote = market_data.get("quote", {}) if market_data else {}
current_price = quote.get("last_price") or fallback_price
shares_b = (quote.get("shares") / 1e9) if quote.get("shares") else fallback_shares_b
market_cap_b = (quote.get("market_cap") / 1e9) if quote.get("market_cap") else current_price * shares_b
long_name = quote.get("long_name") or (COMPANY_NAME if ticker == TICKER_DEFAULT else ticker)
is_live_generic = live_mode_enabled(ticker, use_live, fundamentals)
if is_live_generic:
    base_revenue_b = compute_start_revenue_from_live(fundamentals, base_revenue_b)



st.markdown("<h1 style='margin-bottom:0.1rem'>Financial Dashboard Builder</h1>", unsafe_allow_html=True)
st.caption("Build a clean financial dashboard from a ticker, with statements, valuation context, projections, and live outlook notes.")

col_left, col_right = st.columns([0.7, 0.3])
with col_left:
    st.markdown(f"<span class='ticker-badge'>{ticker}</span>", unsafe_allow_html=True)
    st.title(long_name)
    if ticker == TICKER_DEFAULT:
        st.caption(REPORT_DATE)
    else:
        st.caption("Live generic dashboard · USD unless noted · powered by yfinance when available")
with col_right:
    st.metric("Stock Price", f"${current_price:,.2f}", help="Live from yfinance if enabled; otherwise fallback.")
    st.caption(f"Market Cap: ~${market_cap_b:,.1f}B · Shares: ~{shares_b:,.2f}B")

display_kpis = build_live_kpis(fundamentals, quote, market_cap_b) if is_live_generic else KPI_DATA
kpi_cols = st.columns(6)
for col, (label, value, delta) in zip(kpi_cols, display_kpis):
    with col:
        st.metric(label, value, delta)

if is_live_generic:
    mode_title = "Live Company Dashboard" if use_live else "Ticker Dashboard"
    mode_detail = (
        f"Financial statement data is being pulled for {ticker} from yfinance. Generic statement, trend, forward-view, and projection sections update for the selected ticker."
        if use_live
        else f"{ticker} is selected, but live data is turned off. Turn on live data in the sidebar to populate statements."
    )
    st.markdown(
        f"""
<div class="big-card">
  <div style="font-size:1.35rem;font-weight:800;color:#00e5a0;line-height:1">{mode_title}</div>
  <div class="subtle">{mode_detail}</div>
  <div style="margin-top:10px">Projection revenue base: <span class="good">${base_revenue_b:,.2f}B</span></div>
</div>
""",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
<div class="big-card">
  <div style="font-size:2.2rem;font-weight:800;color:#00e5a0;line-height:1">145%</div>
  <div class="subtle">Rule of 40 — 11th consecutive quarter of expansion</div>
  <div style="margin-top:10px">Revenue growth <span class="good">+85%</span> · Adj. operating margin <span class="good">+60%</span> · GAAP net margin <span class="good">53%</span> · FY2026 Rule of 40 guided at <span class="good">129%</span></div>
</div>
""",
        unsafe_allow_html=True,
    )

tabs = st.tabs([
    "Overview",
    "Income Statement",
    "Balance Sheet",
    "Cash Flow",
    "Segments & Guidance",
    "Growth History",
    "Stock Projection",
    "Analyst & Insider Data",
    "Comparative Analysis",
    "Export Data",
])

with tabs[0]:
    st.markdown("<div class='section-label'>Executive View</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    if is_live_generic:
        live_kpis = build_live_kpis(fundamentals, quote, market_cap_b)
        for col, item in zip([c1, c2, c3, c4], live_kpis[:4]):
            col.metric(item[0], item[1], item[2])
    else:
        c1.metric("Q1'26 Revenue", "$1.633B", "+84.7% YoY")
        c2.metric("Gross Margin", "86.8%", "+6.4pp YoY")
        c3.metric("Adj. FCF Margin", "56.6%", "+14.4pp YoY")
        c4.metric("Cash + Treasuries", "$8.0B", "+51.6% YoY")

    st.markdown("<div class='section-label'>Price History</div>", unsafe_allow_html=True)
    hist = market_data.get("history", pd.DataFrame()) if use_live else pd.DataFrame()
    if isinstance(hist, pd.DataFrame) and not hist.empty and "Close" in hist.columns:
        fig = px.line(hist, x="Date", y="Close", title=f"{ticker} 5-Year Adjusted Close")
        fig.update_layout(template="plotly_dark", height=420, margin=dict(l=20, r=20, t=60, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Turn on internet data or install yfinance to show live 5-year price history.")

    st.markdown("<div class='section-label'>Valuation Context</div>", unsafe_allow_html=True)
    val_cols = st.columns(4)
    val_cols[0].metric("Market Cap", f"~${market_cap_b:,.1f}B")
    val_cols[1].metric("Trailing P/E", f"{quote.get('trailing_pe') or (640 if not is_live_generic else np.nan):,.1f}x" if quote.get('trailing_pe') or not is_live_generic else "—")
    val_cols[2].metric("P/S on Revenue Base", f"{market_cap_b / base_revenue_b:,.1f}x")
    val_cols[3].metric("Revenue Base", f"${base_revenue_b:,.2f}B")
    if is_live_generic:
        st.info("This ticker is using live yfinance financials where available. Some ratios may show blank if Yahoo does not return the required line item.")
    else:
        st.warning("Valuation note: the embedded sample fundamentals are strong, but the embedded expectations are also high. Use the Projection tab to stress-test bull/base/bear cases.")

    st.markdown("<div class='section-label'>Valuation, Profitability & Balance-Sheet Ratios</div>", unsafe_allow_html=True)
    overview_anchor = get_projection_anchor(fundamentals, quote, base_revenue_b, shares_b, current_price)
    ratio_df = build_ratio_dashboard(fundamentals, quote, current_price, market_cap_b, shares_b, base_revenue_b, overview_anchor)
    render_summary_box("Ratio read", make_ratio_summary(ratio_df))
    display_df(ratio_df, height=620, style_rows=False)

    if sec_info:
        st.markdown("<div class='section-label'>SEC Filing Metadata</div>", unsafe_allow_html=True)
        render_sec_source_box(ticker, sec_info, sec_filings)
        if isinstance(sec_filings, pd.DataFrame) and not sec_filings.empty:
            display_df(sec_filings, height=260, style_rows=False)

with tabs[1]:
    st.markdown("<div class='section-label'>Income Statement</div>", unsafe_allow_html=True)
    if sec_statements_available:
        df_income = build_sec_statement_table(sec_facts, "income")
        render_sec_source_box(ticker, sec_info, sec_filings)
        render_summary_box("Income statement read", make_income_summary(df_income))
        render_financial_table(df_income)
        st.caption("SEC/XBRL consolidated income statement. Falls back by mapped tag availability; yfinance remains available when SEC is toggled off.")
    elif is_live_generic:
        df_income = build_live_statement_table_wide(fundamentals, "income")
        render_summary_box("Income statement read", make_income_summary(df_income))
        render_financial_table(df_income)
        st.caption("Live income statement from yfinance. Line-item names vary by company and Yahoo availability.")
    else:
        df_income = statement_df(income_rows, include_margins=True)
        render_summary_box("Income statement read", make_income_summary(df_income))
        render_financial_table(df_income)

        chart_df = pd.DataFrame({"Metric": ["Revenue", "Gross Profit", "GAAP Operating Income", "GAAP Net Income"], "Q1 2025": [884, 711, 176, 214], "Q1 2026": [1633, 1417, 754, 871]})
        melted = chart_df.melt(id_vars="Metric", var_name="Period", value_name="USD Millions")
        fig = px.bar(melted, x="Metric", y="USD Millions", color="Period", barmode="group", title="Q1 2026 vs Q1 2025")
        fig.update_layout(template="plotly_dark", height=420)
        st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.markdown("<div class='section-label'>Balance Sheet</div>", unsafe_allow_html=True)
    if sec_statements_available:
        df_balance = build_sec_statement_table(sec_facts, "balance")
        render_sec_source_box(ticker, sec_info, sec_filings)
        render_summary_box("Balance sheet read", make_balance_summary(df_balance))
        render_financial_table(df_balance)
        st.caption("SEC/XBRL consolidated balance sheet. Falls back by mapped tag availability; yfinance remains available when SEC is toggled off.")
    elif is_live_generic:
        df_balance = build_live_statement_table_wide(fundamentals, "balance")
        render_summary_box("Balance sheet read", make_balance_summary(df_balance))
        render_financial_table(df_balance)
        st.caption("Live balance sheet from yfinance. Line-item availability varies by company.")
    else:
        df_balance = simple_statement_df(balance_rows)
        render_summary_box("Balance sheet read", make_balance_summary(df_balance))
        render_financial_table(df_balance)
        bs_chart = pd.DataFrame({"Metric": ["Assets", "Liabilities", "Equity", "Cash + Treasuries"], "Q1 2026": [9312, 1640, 8672, 8000]})
        fig = px.bar(bs_chart, x="Metric", y="Q1 2026", title="Q1 2026 Balance Sheet Snapshot", text_auto=True)
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    st.markdown("<div class='section-label'>Cash Flow</div>", unsafe_allow_html=True)
    if sec_statements_available:
        df_cash = build_sec_statement_table(sec_facts, "cashflow")
        render_sec_source_box(ticker, sec_info, sec_filings)
        render_summary_box("Cash-flow read", make_cashflow_summary(df_cash))
        render_financial_table(df_cash)
        st.caption("SEC/XBRL consolidated cash-flow statement. Falls back by mapped tag availability; yfinance remains available when SEC is toggled off.")
    elif is_live_generic:
        df_cash = build_live_statement_table_wide(fundamentals, "cashflow")
        render_summary_box("Cash-flow read", make_cashflow_summary(df_cash))
        render_financial_table(df_cash)
        st.caption("Live cash-flow statement from yfinance. Line-item availability varies by company.")
    else:
        df_cash = simple_statement_df(cash_rows)
        render_summary_box("Cash-flow read", make_cashflow_summary(df_cash))
        render_financial_table(df_cash)
        cf_chart = pd.DataFrame({"Metric": ["Net Cash from Ops", "GAAP FCF", "Adjusted FCF"], "Q1 2025": [310, 304, 373], "Q1 2026": [899, 892, 925]})
        melted = cf_chart.melt(id_vars="Metric", var_name="Period", value_name="USD Millions")
        fig = px.bar(melted, x="Metric", y="USD Millions", color="Period", barmode="group", title="Cash Flow Expansion")
        fig.update_layout(template="plotly_dark", height=420)
        st.plotly_chart(fig, use_container_width=True)

with tabs[4]:
    if is_live_generic:
        st.markdown("<div class='section-label'>Business Mix & Outlook</div>", unsafe_allow_html=True)
        mix_view, outlook_view = build_business_mix_view(fundamentals, market_data, ticker, long_name)
        render_summary_box("Outlook read", "This page combines available growth/margin data with a best-effort web pull for recent earnings-call, transcript, guidance, and outlook language.")
        display_df(mix_view, style_rows=False)

        annual_live = build_live_annual_metrics(fundamentals)
        if not annual_live.empty and "Revenue" in annual_live.columns:
            chart_annual = annual_live.copy()
            chart_annual["Revenue ($B)"] = chart_annual["Revenue"] / 1000
            fig = px.bar(chart_annual, x="Year", y="Revenue ($B)", title=f"{ticker} Annual Revenue Trend", text_auto=".2f")
            fig.update_layout(template="plotly_dark", height=390, yaxis_title="USD Billions")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("<div class='section-label'>Latest Earnings Call / Outlook Notes</div>", unsafe_allow_html=True)
        display_df(outlook_view, style_rows=False)

        st.markdown("<div class='section-label'>Forward View</div>", unsafe_allow_html=True)
        forward_view = build_live_forward_view(market_data, quote, current_price, market_cap_b, base_revenue_b)
        display_df(forward_view, style_rows=False)

        rec_sum = market_data.get("recommendation_summary", pd.DataFrame()) if use_live else pd.DataFrame()
        if isinstance(rec_sum, pd.DataFrame) and not rec_sum.empty:
            st.markdown("<div class='section-label'>Analyst Recommendation Trend</div>", unsafe_allow_html=True)
            display_df(rec_sum, height=260, style_rows=False)
    else:
        st.markdown("<div class='section-label'>Business Mix & Outlook</div>", unsafe_allow_html=True)
        render_summary_box("Outlook read", "The embedded sample view includes segment mix, forward guidance, and valuation context. Enter another ticker to switch to live generic data.")
        c1, c2 = st.columns([0.55, 0.45])
        with c1:
            display_df(segments.round(1))
        with c2:
            fig = px.pie(segments, values="Q1 2026", names="Segment", title="Revenue Mix")
            fig.update_layout(template="plotly_dark", height=390)
            st.plotly_chart(fig, use_container_width=True)

        fig = px.bar(segments, x="Segment", y="YoY Growth %", title="Segment YoY Growth", text="YoY Growth %")
        fig.update_traces(texttemplate="%{text:.1f}%")
        fig.update_layout(template="plotly_dark", height=420)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<div class='section-label'>Forward Guidance</div>", unsafe_allow_html=True)
        display_df(GUIDANCE)

with tabs[5]:
    if is_live_generic:
        st.markdown("<div class='section-label'>Historical Financial Trend</div>", unsafe_allow_html=True)
        live_annual = build_live_annual_metrics(fundamentals)
        if live_annual.empty:
            st.info("No annual financial history returned for this ticker.")
        else:
            render_summary_box("Growth read", make_growth_summary(live_annual))
            metric = st.selectbox("Chart metric", ["Revenue", "Gross Profit", "Operating Income", "Net Income", "Free Cash Flow"])
            chart_df = live_annual.copy()
            chart_metric = f"{metric} ($B)"
            chart_df[chart_metric] = chart_df[metric] / 1000
            fig = px.bar(chart_df, x="Year", y=chart_metric, title=f"{ticker} {metric} History", text_auto=".2f")
            fig.update_layout(template="plotly_dark", height=430, yaxis_title="USD Billions")
            st.plotly_chart(fig, use_container_width=True)

            margin_cols = [c for c in ["Gross Margin %", "Operating Margin %", "Net Margin %"] if c in live_annual.columns]
            if margin_cols:
                margin_df = live_annual[["Year"] + margin_cols].melt("Year", var_name="Metric", value_name="Percent")
                fig = px.line(margin_df, x="Year", y="Percent", color="Metric", markers=True, title=f"{ticker} Margin Trend")
                fig.update_layout(template="plotly_dark", height=430)
                st.plotly_chart(fig, use_container_width=True)

            live_display = live_annual.copy()
            for col in ["Revenue", "Gross Profit", "Operating Income", "Net Income", "Free Cash Flow"]:
                if col in live_display.columns:
                    live_display[col] = live_display[col].map(lambda x: f"${x/1000:,.2f}B" if not pd.isna(x) else "—")
            for col in ["Gross Margin %", "Operating Margin %", "Net Margin %"]:
                if col in live_display.columns:
                    live_display[col] = live_display[col].map(lambda x: f"{x:.1f}%" if not pd.isna(x) else "—")
            display_df(live_display, style_rows=False)
    else:
        st.markdown("<div class='section-label'>Five-Year Growth Story</div>", unsafe_allow_html=True)
        render_summary_box("Growth read", make_growth_summary(annual_metrics))
        st.info("Historical annual data plus forward estimate where available.")
        cagr_cols = st.columns(4)
        cagr_specs = [
            ("Revenue CAGR", 1527, 4475),
            ("Gross Profit CAGR", 1000, 3690),
            ("Adj. Op. Income CAGR", 308, 2060),
            ("Adj. FCF CAGR", 321, 2060),
        ]
        for col, (label, start, end) in zip(cagr_cols, cagr_specs):
            col.metric(label, f"{calc_cagr(start, end, 4)*100:.1f}%", f"{fmt_money_m(start)} → {fmt_money_m(end)}")

        metric = st.selectbox("Chart metric", ["Revenue", "Gross Profit", "Adj. Op. Income", "Adj. FCF", "GAAP Net Income"])
        chart_metrics = annual_metrics.copy()
        chart_col = f"{metric} ($B)"
        chart_metrics[chart_col] = chart_metrics[metric] / 1000
        fig = px.bar(chart_metrics, x="Year", y=chart_col, title=f"{metric} History", text_auto=".2f")
        fig.update_layout(template="plotly_dark", height=430, yaxis_title="USD Billions")
        st.plotly_chart(fig, use_container_width=True)

        margin_df = annual_metrics[["Year", "Revenue Growth %", "Adj. Op Margin %", "FCF Margin %"]].melt("Year", var_name="Metric", value_name="Percent")
        fig = px.line(margin_df, x="Year", y="Percent", color="Metric", markers=True, title="Growth and Margin Trend")
        fig.update_layout(template="plotly_dark", height=430)
        st.plotly_chart(fig, use_container_width=True)
        display_df(annual_metrics)

with tabs[6]:
    st.markdown("<div class='section-label'>Scenario Projection Matrix</div>", unsafe_allow_html=True)
    st.caption("Projection anchors to current/TTM revenue, net income margin, EPS, shares, and stock price. 2026 Current is the anchor column; 2027 onward is projected.")

    projection_years = st.slider("Projection years", 1, 10, projection_years)
    projection_anchor = get_projection_anchor(fundamentals, quote, base_revenue_b, shares_b, current_price)
    assumptions_default = get_default_projection_assumptions(current_price, fundamentals, projection_anchor, quote)

    default_key_parts = [
        ticker,
        f"{projection_anchor.get('revenue_b', 0):.2f}",
        f"{projection_anchor.get('net_margin', 0):.3f}",
        f"{projection_anchor.get('current_pe', 0) if not pd.isna(projection_anchor.get('current_pe', np.nan)) else 0:.1f}",
    ]
    assumption_editor_key = "projection_assumptions_" + "_".join(default_key_parts)

    with st.expander("Edit scenario assumptions", expanded=False):
        st.caption("Defaults recalculate whenever the ticker/current anchor changes. Editing is still allowed for manual what-if work.")
        assumptions = st.data_editor(
            assumptions_default,
            key=assumption_editor_key,
            num_rows="fixed",
            use_container_width=True,
            column_config={
                "Revenue Growth %": st.column_config.NumberColumn(format="%.1f%%"),
                "Terminal Net Margin %": st.column_config.NumberColumn(format="%.1f%%"),
                "Terminal PE Low": st.column_config.NumberColumn(format="%.1fx"),
                "Terminal PE High": st.column_config.NumberColumn(format="%.1fx"),
            },
        )

    stat1, stat2, stat3, stat4 = st.columns(4)
    stat1.metric("Current Price", f"${current_price:,.2f}")
    stat2.metric("2026 Revenue Base", f"${projection_anchor['revenue_b']:,.2f}B")
    stat3.metric("Current TTM EPS", f"${projection_anchor['eps']:,.2f}")
    stat4.metric("Projection Period", f"2027–{2026 + projection_years}")

    st.markdown("<div class='section-label'>Auto-Built Scenario Defaults</div>", unsafe_allow_html=True)
    display_df(assumptions_default, style_rows=False)

    matrices, proj_summary = build_projection_matrices(current_price, projection_anchor, projection_years, assumptions)

    if not proj_summary.empty:
        summary_fmt = proj_summary.copy()
        summary_fmt["Revenue ($B)"] = summary_fmt["Revenue ($B)"].map(lambda x: f"${x:,.2f}B")
        summary_fmt["Net Margin"] = summary_fmt["Net Margin"].map(lambda x: f"{x*100:.1f}%")
        summary_fmt["EPS"] = summary_fmt["EPS"].map(lambda x: f"${x:,.2f}")
        summary_fmt["Price Low"] = summary_fmt["Price Low"].map(lambda x: f"${x:,.0f}")
        summary_fmt["Price High"] = summary_fmt["Price High"].map(lambda x: f"${x:,.0f}")
        summary_fmt["CAGR Low"] = summary_fmt["CAGR Low"].map(lambda x: f"{x*100:.1f}%")
        summary_fmt["CAGR High"] = summary_fmt["CAGR High"].map(lambda x: f"{x*100:.1f}%")
        st.markdown("<div class='section-label'>Terminal-Year Summary</div>", unsafe_allow_html=True)
        display_df(summary_fmt, height=220, style_rows=False)

    st.markdown("<div class='section-label'>Scenario Tables</div>", unsafe_allow_html=True)
    st.caption(f"Current stock price is the CAGR starting point: ${current_price:,.2f}. The first column anchors 2026 current/TTM values; projections begin in 2027.")
    for case_name in ["Base", "Bull", "Bear"]:
        if case_name in matrices:
            render_projection_case_table(case_name, matrices[case_name])

    render_summary_box("Projection read", "The projection uses current fundamentals as the anchor, then auto-builds bear/base/bull defaults from historical revenue growth, current margins, and current valuation. Share count is held flat to keep the model simple.")
    st.info("Tip: open Edit scenario assumptions to tune growth, margins, and valuation ranges.")

with tabs[7]:
    st.markdown("<div class='section-label'>Analyst Price Targets</div>", unsafe_allow_html=True)
    apt = market_data.get("analyst_price_targets", pd.DataFrame()) if use_live else pd.DataFrame()
    if isinstance(apt, pd.DataFrame) and not apt.empty:
        display_df(apt)
        lower_cols = {c.lower(): c for c in apt.columns}
        numeric_items = []
        for key in ["low", "current", "mean", "median", "high"]:
            for col_lower, original in lower_cols.items():
                if key in col_lower and pd.api.types.is_numeric_dtype(apt[original]):
                    numeric_items.append((original, float(apt[original].dropna().iloc[0])))
                    break
        if numeric_items:
            plot_df = pd.DataFrame(numeric_items, columns=["Target", "Price"])
            fig = px.bar(plot_df, x="Target", y="Price", title="Analyst Price Target Range", text_auto=True)
            fig.add_hline(y=current_price, line_dash="dash", annotation_text="Current/Fallback Price")
            fig.update_layout(template="plotly_dark", height=420)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No analyst price target table was returned. This can happen when Yahoo/yfinance changes availability. Try upgrading yfinance or adding a paid API later.")

    st.markdown("<div class='section-label'>Recommendation Trend / Rating Changes</div>", unsafe_allow_html=True)
    rec_sum = market_data.get("recommendation_summary", pd.DataFrame()) if use_live else pd.DataFrame()
    rec = market_data.get("recommendations", pd.DataFrame()) if use_live else pd.DataFrame()
    if isinstance(rec_sum, pd.DataFrame) and not rec_sum.empty:
        display_df(rec_sum, height=260)
    elif isinstance(rec, pd.DataFrame) and not rec.empty:
        display_df(rec.tail(30), height=420)
    else:
        st.info("No recommendation data returned from yfinance.")

    st.markdown("<div class='section-label'>Insider Trading / Insider Holdings</div>", unsafe_allow_html=True)
    insider_tx = market_data.get("insider_transactions", pd.DataFrame()) if use_live else pd.DataFrame()
    insider_roster = market_data.get("insider_roster", pd.DataFrame()) if use_live else pd.DataFrame()
    if isinstance(insider_tx, pd.DataFrame) and not insider_tx.empty:
        display_df(insider_tx.head(100), height=480)
    elif isinstance(insider_roster, pd.DataFrame) and not insider_roster.empty:
        display_df(insider_roster.head(100), height=480)
    else:
        st.info("No insider transaction data returned from yfinance. A future improvement is adding SEC Form 4 parsing from sec-api, OpenInsider scraping, or Nasdaq insider feeds.")

    if use_live and market_data.get("errors"):
        with st.expander("Data fetch diagnostics"):
            for err in market_data["errors"]:
                st.write("-", err)

with tabs[8]:
    st.markdown("<div class='section-label'>Comparative Analysis</div>", unsafe_allow_html=True)
    st.caption("Enter peer tickers to compare valuation, growth, profitability, balance-sheet strength, and cash-flow quality side by side.")

    PEER_REQUEST_DELAY_SECONDS = 20.0
    PEER_MAX_COMPANIES = 10

    default_peers = ticker if ticker else TICKER_DEFAULT
    peer_input = st.text_input(
        "Peer tickers",
        value=default_peers,
        help="Comma-separated tickers, for example: NVDA, AMD, INTC, AVGO",
    )
    peer_tickers = tuple(dict.fromkeys([t.strip().upper() for t in peer_input.replace(";", ",").split(",") if t.strip()]))
    peer_tickers = peer_tickers[:PEER_MAX_COMPANIES]

    st.info(
        f"This tab fetches one company at a time with a fixed {PEER_REQUEST_DELAY_SECONDS:.0f}-second delay between companies. "
        f"Maximum companies per run is locked to {PEER_MAX_COMPANIES}. "
        "Peer comparison now uses a lightweight quote pull to avoid the heavier Yahoo endpoints that trigger rate limits."
    )

    if len(peer_tickers) < 2:
        st.info("Add at least two tickers separated by commas to build a peer comparison.")
    else:
        estimated_wait = max(len(peer_tickers) - 1, 0) * PEER_REQUEST_DELAY_SECONDS
        st.caption(f"Selected peers: {', '.join(peer_tickers)} · Intentional wait: ~{estimated_wait:.0f} seconds")

        fetch_col, clear_col = st.columns([0.25, 0.75])
        with fetch_col:
            run_comparison = st.button("Fetch peer comparison", type="primary")
        with clear_col:
            if st.button("Clear peer cache"):
                st.cache_data.clear()
                st.session_state.pop("peer_comparison_df", None)
                st.session_state.pop("peer_score_df", None)
                st.session_state.pop("peer_comparison_tickers", None)
                st.rerun()

        if run_comparison:
            progress = st.progress(0)
            status = st.empty()
            fetched_rows = []

            total = len(peer_tickers)
            for i, peer in enumerate(peer_tickers, start=1):
                if i > 1:
                    status.write(f"Waiting {PEER_REQUEST_DELAY_SECONDS:.0f} seconds before fetching {peer} ({i}/{total})...")
                    time.sleep(float(PEER_REQUEST_DELAY_SECONDS))

                status.write(f"Fetching {peer} ({i}/{total}) using lightweight quote + fundamentals pull...")
                progress.progress(int((i - 1) / max(total, 1) * 100))

                try:
                    row = build_single_peer_row(peer)
                    fetched_rows.append(row)
                    status.write(f"Completed {peer} ({i}/{total})")
                except Exception as e:
                    fetched_rows.append({
                        "Ticker": peer,
                        "Company": peer,
                        "Data Status": f"fetch failed: {e}",
                    })
                    status.write(f"Fetch failed for {peer}: {e}")

                progress.progress(int(i / max(total, 1) * 100))

            peer_df = pd.DataFrame(fetched_rows)
            score_df = build_peer_scorecard_from_rows(peer_df)

            progress.progress(100)
            status.write("Peer comparison complete.")
            st.session_state["peer_comparison_df"] = peer_df
            st.session_state["peer_score_df"] = score_df
            st.session_state["peer_comparison_tickers"] = peer_tickers

        peer_df = st.session_state.get("peer_comparison_df", pd.DataFrame())
        score_df = st.session_state.get("peer_score_df", pd.DataFrame())
        stored_tickers = st.session_state.get("peer_comparison_tickers", tuple())

        if not peer_df.empty and stored_tickers != peer_tickers:
            st.warning("Ticker list changed. Click 'Fetch peer comparison' again to refresh the peer table for the new list.")

        if peer_df.empty:
            st.warning("Click 'Fetch peer comparison' to pull peer data sequentially.")
        else:
            render_summary_box("Peer read", build_peer_summary(peer_df, score_df))

            st.markdown("<div class='section-label'>Peer Scorecard</div>", unsafe_allow_html=True)
            if score_df.empty:
                st.info("No scorecard could be generated. Check ticker symbols or data availability.")
            else:
                display_df(score_df, style_rows=False)

            st.markdown("<div class='section-label'>Side-by-Side Metrics</div>", unsafe_allow_html=True)
            display_df(peer_df, height=520, style_rows=False)

            numeric_plot = peer_df.copy()
            for col in ["P/S", "P/E", "Forward P/E", "Revenue CAGR", "Net Margin", "FCF Margin", "FCF Yield"]:
                if col in numeric_plot.columns:
                    numeric_plot[col + " Numeric"] = numeric_plot[col].map(_parse_ratio_number)

            st.markdown("<div class='section-label'>Growth vs Valuation</div>", unsafe_allow_html=True)
            if {"Revenue CAGR Numeric", "P/S Numeric"}.issubset(numeric_plot.columns):
                fig = px.scatter(
                    numeric_plot,
                    x="Revenue CAGR Numeric",
                    y="P/S Numeric",
                    text="Ticker",
                    hover_name="Company",
                    title="Revenue Growth vs Price/Sales",
                    labels={"Revenue CAGR Numeric": "Revenue CAGR (%)", "P/S Numeric": "Price / Sales (x)"},
                )
                fig.update_traces(textposition="top center")
                fig.update_layout(template="plotly_dark", height=430)
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("<div class='section-label'>Profitability Comparison</div>", unsafe_allow_html=True)
            profit_cols = []
            for col in ["Net Margin", "FCF Margin", "ROE"]:
                numeric_col = col + " Numeric"
                if numeric_col in numeric_plot.columns:
                    profit_cols.append(numeric_col)
            if profit_cols:
                chart_df = numeric_plot[["Ticker"] + profit_cols].copy()
                chart_df = chart_df.rename(columns={c: c.replace(" Numeric", "") for c in profit_cols})
                melted = chart_df.melt("Ticker", var_name="Metric", value_name="Percent")
                fig = px.bar(melted, x="Ticker", y="Percent", color="Metric", barmode="group", title="Profitability and Return Metrics")
                fig.update_layout(template="plotly_dark", height=430, yaxis_title="%")
                st.plotly_chart(fig, use_container_width=True)


with tabs[9]:
    st.markdown("<div class='section-label'>Export Dashboard Data</div>", unsafe_allow_html=True)
    if is_live_generic:
        export_tables = {
            "live_income_statement": build_sec_statement_table(sec_facts, "income") if sec_statements_available else build_live_statement_table_wide(fundamentals, "income"),
            "live_balance_sheet": build_sec_statement_table(sec_facts, "balance") if sec_statements_available else build_live_statement_table_wide(fundamentals, "balance"),
            "live_cash_flow": build_sec_statement_table(sec_facts, "cashflow") if sec_statements_available else build_live_statement_table_wide(fundamentals, "cashflow"),
            "live_operating_profile": build_live_operating_profile(fundamentals),
            "live_forward_view": build_live_forward_view(market_data, quote, current_price, market_cap_b, base_revenue_b),
            "live_annual_metrics": build_live_annual_metrics(fundamentals),
        }
    else:
        export_tables = {
            "income_statement": statement_df(income_rows, include_margins=True),
            "balance_sheet": simple_statement_df(balance_rows),
            "cash_flow": simple_statement_df(cash_rows),
            "segments": segments,
            "guidance": GUIDANCE,
            "annual_metrics": annual_metrics,
        }
    selected = st.selectbox("Select table", list(export_tables.keys()))
    display_df(export_tables[selected], style_rows=("Line Item" in export_tables[selected].columns))
    csv = export_tables[selected].to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", data=csv, file_name=f"{ticker}_{selected}.csv", mime="text/csv")

if is_live_generic:
    with st.expander("Live data diagnostics"):
        st.write(f"Ticker: {ticker}")
        st.write(f"Live data toggle: {use_live}")
        st.write(f"Income statement rows returned: {len(fundamentals.get('income', pd.DataFrame())) if isinstance(fundamentals.get('income', pd.DataFrame()), pd.DataFrame) else 0}")
        st.write(f"Balance sheet rows returned: {len(fundamentals.get('balance', pd.DataFrame())) if isinstance(fundamentals.get('balance', pd.DataFrame()), pd.DataFrame) else 0}")
        st.write(f"Cash-flow rows returned: {len(fundamentals.get('cashflow', pd.DataFrame())) if isinstance(fundamentals.get('cashflow', pd.DataFrame()), pd.DataFrame) else 0}")
        errors = []
        errors.extend(market_data.get("errors", []) if isinstance(market_data, dict) else [])
        errors.extend(fundamentals.get("errors", []) if isinstance(fundamentals, dict) else [])
        if errors:
            for err in errors:
                st.write("-", err)
        else:
            st.write("No fetch errors reported.")
st.caption(f"Last app refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · Local offline-capable dashboard with optional live market data.")

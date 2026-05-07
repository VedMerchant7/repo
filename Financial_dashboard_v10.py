"""Offline financial dashboard with optional live yfinance data."""

from __future__ import annotations

import math
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    import yfinance as yf
except Exception:
    yf = None



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
    if upper in subtotal_rows or (upper.startswith("TOTAL ") and upper not in grand_rows):
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

# Embedded PLTR dashboard data
# Values are USD millions unless noted.

TICKER_DEFAULT = "PLTR"
COMPANY_NAME = "Palantir Technologies"
REPORT_DATE = "Q1 2026 Earnings · May 4, 2026 · USD millions unless noted"

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

# Data builders

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



def get_default_projection_assumptions(current_price: float) -> pd.DataFrame:
    """Scenario assumptions for the revamped projection page."""
    return pd.DataFrame(
        [
            {
                "Case": "Base",
                "Revenue Growth %": 32.0,
                "Starting Net Margin %": 28.0,
                "Terminal Net Margin %": 36.0,
                "Dilution CAGR %": 2.0,
                "PE Low Start": 72.0,
                "PE Low End": 55.0,
                "PE High Start": 90.0,
                "PE High End": 70.0,
            },
            {
                "Case": "Bull",
                "Revenue Growth %": 42.0,
                "Starting Net Margin %": 30.0,
                "Terminal Net Margin %": 42.0,
                "Dilution CAGR %": 1.5,
                "PE Low Start": 85.0,
                "PE Low End": 70.0,
                "PE High Start": 105.0,
                "PE High End": 88.0,
            },
            {
                "Case": "Bear",
                "Revenue Growth %": 22.0,
                "Starting Net Margin %": 25.0,
                "Terminal Net Margin %": 28.0,
                "Dilution CAGR %": 2.5,
                "PE Low Start": 45.0,
                "PE Low End": 30.0,
                "PE High Start": 55.0,
                "PE High End": 38.0,
            },
        ]
    )


def build_projection_matrices(
    current_price: float,
    base_revenue_b: float,
    shares_b: float,
    years: int,
    assumptions: pd.DataFrame,
    start_year: int = 2027,
) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
    """Build year-by-year scenario tables similar to the requested layout."""
    matrices: Dict[str, pd.DataFrame] = {}
    summary_rows: List[Dict[str, Any]] = []

    for _, r in assumptions.iterrows():
        case = str(r["Case"]).strip() or "Case"
        rev_growth = float(r["Revenue Growth %"]) / 100.0
        start_margin = float(r["Starting Net Margin %"]) / 100.0
        terminal_margin = float(r["Terminal Net Margin %"]) / 100.0
        dilution = float(r["Dilution CAGR %"]) / 100.0
        pe_low_start = float(r["PE Low Start"])
        pe_low_end = float(r["PE Low End"])
        pe_high_start = float(r["PE High Start"])
        pe_high_end = float(r["PE High End"])

        year_labels = [str(start_year + i) for i in range(years)]
        margin_series = np.linspace(start_margin, terminal_margin, years)
        pe_low_series = np.linspace(pe_low_start, pe_low_end, years)
        pe_high_series = np.linspace(pe_high_start, pe_high_end, years)

        revenues = []
        net_incomes = []
        eps_values = []
        share_low = []
        share_high = []
        cagr_low = []
        cagr_high = []

        for i in range(years):
            horizon = i + 1
            revenue_i = base_revenue_b * ((1 + rev_growth) ** horizon)
            margin_i = float(margin_series[i])
            shares_i = shares_b * ((1 + dilution) ** horizon)
            net_income_i = revenue_i * margin_i
            eps_i = net_income_i / shares_i if shares_i else np.nan
            low_i = eps_i * pe_low_series[i]
            high_i = eps_i * pe_high_series[i]
            cagr_low_i = calc_cagr(current_price, low_i, horizon) if current_price and low_i > 0 else np.nan
            cagr_high_i = calc_cagr(current_price, high_i, horizon) if current_price and high_i > 0 else np.nan

            revenues.append(revenue_i)
            net_incomes.append(net_income_i)
            eps_values.append(eps_i)
            share_low.append(low_i)
            share_high.append(high_i)
            cagr_low.append(cagr_low_i)
            cagr_high.append(cagr_high_i)

        rev_growth_row = [np.nan] + [rev_growth] * (years - 1)
        ni_growth_row = [np.nan] + [safe_div(net_incomes[i], net_incomes[i-1]) - 1 if net_incomes[i-1] else np.nan for i in range(1, years)]

        row_map = {
            "REVENUE": revenues,
            "REV GROWTH": rev_growth_row,
            "NET INCOME": net_incomes,
            "NET INC. GROWTH": ni_growth_row,
            "NET INC. MARGINS": list(margin_series),
            "EPS": eps_values,
            "PE LOW EST": list(pe_low_series),
            "PE HIGH EST": list(pe_high_series),
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
                "Net Margin": margin_series[-1],
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
        ]
    elif statement_type == "balance":
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
            annual_vals = [_get_statement_value(annual_raw, possible, c) for c in annual_cols] if annual_cols else []
            q_val = _get_statement_value(quarter_raw, possible, latest_q) if latest_q is not None else np.nan

            if all(pd.isna(v) for v in annual_vals) and pd.isna(q_val):
                continue

            row = {"Line Item": label}
            for col_label, val in zip(annual_labels, annual_vals):
                row[col_label] = _fmt_raw_number(val, kind)
            if latest_q is not None:
                row[q_label] = _fmt_raw_number(q_val, kind)

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



with st.sidebar:
    st.markdown("### Dashboard Controls")
    ticker = st.text_input("Ticker", value=TICKER_DEFAULT).upper().strip() or TICKER_DEFAULT
    use_live = st.toggle("Use internet data when available", value=True)
    if st.button("Refresh live data"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Work in progress...")

projection_years = 5
base_revenue_b = 7.656
fallback_price = 124.0
fallback_shares_b = 2.55

market_data = get_market_data(ticker) if use_live else {"quote": {}, "history": pd.DataFrame(), "errors": []}
fundamentals = get_yf_fundamentals(ticker) if use_live else {"income": pd.DataFrame(), "balance": pd.DataFrame(), "cashflow": pd.DataFrame(), "errors": []}
quote = market_data.get("quote", {}) if market_data else {}
current_price = quote.get("last_price") or fallback_price
shares_b = (quote.get("shares") / 1e9) if quote.get("shares") else fallback_shares_b
market_cap_b = (quote.get("market_cap") / 1e9) if quote.get("market_cap") else current_price * shares_b
long_name = quote.get("long_name") or (COMPANY_NAME if ticker == TICKER_DEFAULT else ticker)
is_live_generic = live_mode_enabled(ticker, use_live, fundamentals)
if is_live_generic:
    base_revenue_b = compute_start_revenue_from_live(fundamentals, base_revenue_b)



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
    mode_title = "Live Generic Mode" if use_live else "Generic Ticker Mode"
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

# Tabs

tabs = st.tabs([
    "Overview",
    "Income Statement",
    "Balance Sheet",
    "Cash Flow",
    "Segments & Guidance",
    "Growth History",
    "Stock Projection",
    "Analyst & Insider Data",
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
        st.info("This ticker is using generic live yfinance financials. For a fully bespoke dashboard, the segment/guidance/growth-history tabs need company-specific inputs.")
    else:
        st.warning("Valuation note: the fundamentals are exceptional, but the embedded expectations are also extreme. Use the Projection tab to stress-test bull/base/bear cases.")

with tabs[1]:
    st.markdown("<div class='section-label'>Income Statement</div>", unsafe_allow_html=True)
    if is_live_generic:
        df_income = build_live_statement_table_wide(fundamentals, "income")
        render_financial_table(df_income)
        st.caption("Live generic income statement from yfinance. Line-item names vary by company and Yahoo availability.")
    else:
        df_income = statement_df(income_rows, include_margins=True)
        render_financial_table(df_income)

        chart_df = pd.DataFrame({"Metric": ["Revenue", "Gross Profit", "GAAP Operating Income", "GAAP Net Income"], "Q1 2025": [884, 711, 176, 214], "Q1 2026": [1633, 1417, 754, 871]})
        melted = chart_df.melt(id_vars="Metric", var_name="Period", value_name="USD Millions")
        fig = px.bar(melted, x="Metric", y="USD Millions", color="Period", barmode="group", title="Q1 2026 vs Q1 2025")
        fig.update_layout(template="plotly_dark", height=420)
        st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.markdown("<div class='section-label'>Balance Sheet</div>", unsafe_allow_html=True)
    if is_live_generic:
        df_balance = build_live_statement_table_wide(fundamentals, "balance")
        render_financial_table(df_balance)
        st.caption("Live generic balance sheet from yfinance. Line-item availability varies by company.")
    else:
        df_balance = simple_statement_df(balance_rows)
        render_financial_table(df_balance)
        bs_chart = pd.DataFrame({"Metric": ["Assets", "Liabilities", "Equity", "Cash + Treasuries"], "Q1 2026": [9312, 1640, 8672, 8000]})
        fig = px.bar(bs_chart, x="Metric", y="Q1 2026", title="Q1 2026 Balance Sheet Snapshot", text_auto=True)
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    st.markdown("<div class='section-label'>Cash Flow</div>", unsafe_allow_html=True)
    if is_live_generic:
        df_cash = build_live_statement_table_wide(fundamentals, "cashflow")
        render_financial_table(df_cash)
        st.caption("Live generic cash-flow statement from yfinance. Line-item availability varies by company.")
    else:
        df_cash = simple_statement_df(cash_rows)
        render_financial_table(df_cash)
        cf_chart = pd.DataFrame({"Metric": ["Net Cash from Ops", "GAAP FCF", "Adjusted FCF"], "Q1 2025": [310, 304, 373], "Q1 2026": [899, 892, 925]})
        melted = cf_chart.melt(id_vars="Metric", var_name="Period", value_name="USD Millions")
        fig = px.bar(melted, x="Metric", y="USD Millions", color="Period", barmode="group", title="Cash Flow Expansion")
        fig.update_layout(template="plotly_dark", height=420)
        st.plotly_chart(fig, use_container_width=True)

with tabs[4]:
    if is_live_generic:
        st.markdown("<div class='section-label'>Operating Profile</div>", unsafe_allow_html=True)
        profile = build_live_operating_profile(fundamentals)
        render_financial_table(profile)

        st.markdown("<div class='section-label'>Forward View</div>", unsafe_allow_html=True)
        forward_view = build_live_forward_view(market_data, quote, current_price, market_cap_b, base_revenue_b)
        display_df(forward_view, style_rows=False)

        annual_live = build_live_annual_metrics(fundamentals)
        if not annual_live.empty and "Revenue" in annual_live.columns:
            chart_annual = annual_live.copy()
            if "Revenue" in chart_annual.columns:
                chart_annual["Revenue ($B)"] = chart_annual["Revenue"] / 1000
                fig = px.bar(chart_annual, x="Year", y="Revenue ($B)", title=f"{ticker} Annual Revenue Trend", text_auto=".2f")
                fig.update_layout(template="plotly_dark", height=390, yaxis_title="USD Billions")
                st.plotly_chart(fig, use_container_width=True)

        rec_sum = market_data.get("recommendation_summary", pd.DataFrame()) if use_live else pd.DataFrame()
        if isinstance(rec_sum, pd.DataFrame) and not rec_sum.empty:
            st.markdown("<div class='section-label'>Analyst Recommendation Trend</div>", unsafe_allow_html=True)
            display_df(rec_sum, height=260, style_rows=False)
    else:
        st.markdown("<div class='section-label'>Segment Revenue</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([0.55, 0.45])
        with c1:
            display_df(segments.round(1))
        with c2:
            fig = px.pie(segments, values="Q1 2026", names="Segment", title="Q1 2026 Revenue Mix")
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
        st.info("FY2021–FY2025 actual history plus FY2026E guidance midpoint. FY2026E is forward-looking.")
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
    st.caption("Projection starts from the current stock price and the current revenue base. The first projection column is 2027.")

    projection_years = st.slider("Projection years", 1, 10, projection_years)
    assumptions_default = get_default_projection_assumptions(current_price)
    with st.expander("Edit scenario assumptions", expanded=False):
        assumptions = st.data_editor(
            assumptions_default,
            num_rows="fixed",
            use_container_width=True,
            column_config={
                "Revenue Growth %": st.column_config.NumberColumn(format="%.1f%%"),
                "Starting Net Margin %": st.column_config.NumberColumn(format="%.1f%%"),
                "Terminal Net Margin %": st.column_config.NumberColumn(format="%.1f%%"),
                "Dilution CAGR %": st.column_config.NumberColumn(format="%.1f%%"),
                "PE Low Start": st.column_config.NumberColumn(format="%.1fx"),
                "PE Low End": st.column_config.NumberColumn(format="%.1fx"),
                "PE High Start": st.column_config.NumberColumn(format="%.1fx"),
                "PE High End": st.column_config.NumberColumn(format="%.1fx"),
            },
        )

    stat1, stat2, stat3, stat4 = st.columns(4)
    stat1.metric("Current Price", f"${current_price:,.2f}")
    stat2.metric("2026 Revenue Base", f"${base_revenue_b:,.2f}B")
    stat3.metric("Diluted Shares", f"{shares_b:,.2f}B")
    stat4.metric("Projection Period", f"2027–{2026 + projection_years}")

    matrices, proj_summary = build_projection_matrices(current_price, base_revenue_b, shares_b, projection_years, assumptions_default if 'assumptions' not in locals() else assumptions)

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
    st.caption(f"Current stock price is the CAGR starting point: ${current_price:,.2f}. The first projection column is 2027, not the 2026 base year.")
    for case_name in ["Base", "Bull", "Bear"]:
        if case_name in matrices:
            render_projection_case_table(case_name, matrices[case_name])

    st.info("Tip: open Edit scenario assumptions to tune growth, margins, dilution, and valuation ranges.")

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
    st.markdown("<div class='section-label'>Export Dashboard Data</div>", unsafe_allow_html=True)
    if is_live_generic:
        export_tables = {
            "live_income_statement": build_live_statement_table_wide(fundamentals, "income"),
            "live_balance_sheet": build_live_statement_table_wide(fundamentals, "balance"),
            "live_cash_flow": build_live_statement_table_wide(fundamentals, "cashflow"),
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

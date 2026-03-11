"""
Deal History — browse and reload past analyses.
"""

import json
import os
import sys

import streamlit as st

# ── Shared path so we can import helpers from the main app ────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from dq_utils import (
    get_history_file,
    load_history,
    fmt_d,
    fmt_p,
    calc_payment,
    populate_sidebar_from_data,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="DealQuill — History", layout="wide", page_icon="🏢")

st.markdown("""
<style>
html, body, [class*="css"], .stApp, .stApp > div,
[data-testid="stAppViewContainer"], [data-testid="stHeader"],
[data-testid="stSidebar"], [data-testid="stSidebar"] > div,
[data-testid="stMain"], .main, .block-container {
    background-color: #ffffff !important;
    color: #000000 !important;
}
p, span, div, label, h1, h2, h3, h4, h5, h6,
.stMarkdown, .stText, [data-testid="stMarkdownContainer"] {
    color: #000000 !important;
}
[data-testid="metric-container"] {
    background: #ffffff !important;
    border: 1px solid #dddddd !important;
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 26px !important;
    font-weight: 700 !important;
    color: #000000 !important;
}
section[data-testid="stSidebar"] * {
    color: #000000 !important;
    background-color: #f8f8f8 !important;
}
header a[href*="github"],
[data-testid="stHeader"] a[href*="github"],
[data-testid="stToolbar"] a[href*="github"] {
    display: none !important;
}
.stButton button {
    color: #2F5496 !important;
    background-color: #2F5496 !important;
    border: none !important;
}
.dealquill-brand {
    position: fixed;
    top: 0;
    left: 60px;
    height: 48px;
    display: flex;
    align-items: center;
    z-index: 999999;
    pointer-events: none;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="dealquill-brand">
    <span style="font-size:20px;font-weight:800;color:#2F5496;letter-spacing:-0.5px;">Deal</span><span style="font-size:20px;font-weight:800;color:#111;letter-spacing:-0.5px;">Quill</span>
</div>
""", unsafe_allow_html=True)

# ── Auth check ────────────────────────────────────────────────────────────────
def _get_app_password():
    try:
        return st.secrets.get("APP_PASSWORD") or ""
    except Exception:
        import os
        return os.environ.get("APP_PASSWORD", "")

if not st.session_state.get("authenticated"):
    st.warning("Please sign in from the main page.")
    st.stop()

# ── Load history ──────────────────────────────────────────────────────────────
history = load_history()

st.title("Deal History")

if not history:
    st.info("No analyses saved yet. Run a deal on the main page to start building history.")
    st.stop()

# ── History list ──────────────────────────────────────────────────────────────
st.markdown(f"**{len(history)} saved {'analysis' if len(history) == 1 else 'analyses'}** — click any to view")
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# Search/filter
search = st.text_input("Search", placeholder="Filter by address or property name...")
if search:
    history = [h for h in history if search.lower() in h.get("label", "").lower()]

for entry in history:
    data  = entry.get("data", {})
    prop  = data.get("property", {})
    fin   = data.get("financing", {})

    price    = prop.get("purchase_price") or 0
    gmi      = prop.get("gross_monthly_income") or 0
    down_pct = prop.get("down_payment_pct") or 0.25
    rate     = fin.get("interest_rate") or 0.07
    amort    = fin.get("amortization_years") or 30
    loan     = fin.get("loan_amount") or (price * (1 - down_pct))
    vac      = prop.get("vacancy_rate") or 0.0

    monthly_payment = calc_payment(loan, rate, amort)
    eff_income = gmi * (1 - vac)

    # Quick opex estimate for the card
    taxes_v = float(prop.get("monthly_property_taxes") or prop.get("_taxes") or 0)
    ins_v   = float(prop.get("monthly_insurance")      or prop.get("_insurance") or 0)
    util_v  = float(prop.get("monthly_utilities")      or prop.get("_utilities") or 0)
    capex_p = float(prop.get("capex_pct")              or prop.get("_capex_pct") or 0)
    maint_p = float(prop.get("maintenance_pct")        or prop.get("_maint_pct") or 0)
    mgmt_p  = float(prop.get("management_pct")         or prop.get("_mgmt_pct")  or 0)
    line_total = taxes_v + ins_v + util_v + gmi * (capex_p + maint_p + mgmt_p)
    moe = prop.get("monthly_operating_expenses")
    if moe is not None:
        monthly_opex = float(moe)
    elif line_total > 0:
        monthly_opex = line_total
    else:
        monthly_opex = gmi * float(prop.get("operating_expenses_pct") or 0.45)

    monthly_noi = eff_income - monthly_opex
    monthly_cf  = monthly_noi - monthly_payment
    cap_rate    = (monthly_noi * 12) / price if price else 0
    down_payment = price * down_pct
    closing     = prop.get("closing_costs") or 0
    total_inv   = down_payment + closing
    coc         = (monthly_cf * 12) / total_inv if total_inv else 0

    cf_color = "#38A169" if monthly_cf >= 0 else "#E53E3E"
    badge    = ("↗ " if monthly_cf >= 0 else "↘ ") + fmt_d(monthly_cf) + "/mo"

    col_info, col_btn = st.columns([5, 1])
    with col_info:
        st.markdown(f"""
        <div style="background:#F9FAFB;border:1px solid #E2E8F0;border-radius:12px;
                    padding:18px 22px;margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;">
                <div>
                    <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:3px;">
                        {entry.get("timestamp","")}</div>
                    <div style="font-size:18px;font-weight:700;color:#000;margin-bottom:10px;">
                        {entry.get("address","Unknown")}</div>
                    <div style="display:flex;gap:24px;flex-wrap:wrap;">
                        <div><div style="font-size:11px;color:#888;">Purchase Price</div>
                             <div style="font-size:15px;font-weight:600;">{fmt_d(price)}</div></div>
                        <div><div style="font-size:11px;color:#888;">Cash Flow</div>
                             <div style="font-size:15px;font-weight:700;color:{cf_color};">{badge}</div></div>
                        <div><div style="font-size:11px;color:#888;">Cap Rate</div>
                             <div style="font-size:15px;font-weight:600;">{fmt_p(cap_rate)}</div></div>
                        <div><div style="font-size:11px;color:#888;">CoC ROI</div>
                             <div style="font-size:15px;font-weight:600;">{fmt_p(coc)}</div></div>
                        <div><div style="font-size:11px;color:#888;">Gross Income</div>
                             <div style="font-size:15px;font-weight:600;">{fmt_d(gmi)}/mo</div></div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_btn:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("View", key=f"load_{entry['id']}"):
            st.session_state["dashboard_data"] = data
            populate_sidebar_from_data(data)
            st.switch_page("Analyzer.py")

# ── Delete all ────────────────────────────────────────────────────────────────
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
if st.button("🗑 Clear all history", type="secondary"):
    try:
        os.remove(get_history_file())
    except Exception:
        pass
    st.rerun()

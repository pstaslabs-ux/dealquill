"""
Shared utilities imported by both claude_proforma_app.py and pages/1_History.py.
No Streamlit rendering here — only pure functions and session-state helpers.
"""

import json
import math
import os
import re

import streamlit as st


# ── History file (per-user) ────────────────────────────────────────────────────

_ROOT = os.path.dirname(os.path.abspath(__file__))


def get_history_file():
    username = st.session_state.get("username", "default")
    safe = "".join(c for c in username if c.isalnum() or c in "-_")
    return os.path.join(_ROOT, f"deal_history_{safe}.json")


def load_history():
    path = get_history_file()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []


# ── Formatters ────────────────────────────────────────────────────────────────

def fmt_d(v, short=False):
    if v is None:
        return "N/A"
    if short:
        if abs(v) >= 1_000_000:
            return "$" + str(round(v / 1_000_000, 1)) + "M"
        if abs(v) >= 1_000:
            return "$" + str(round(v / 1_000)) + "K"
    return "${:,.0f}".format(v)


def fmt_p(v):
    if v is None:
        return "N/A"
    return "{:.2f}%".format(v * 100)


# ── Finance math ──────────────────────────────────────────────────────────────

def calc_payment(loan, annual_rate, years):
    if annual_rate == 0 or years == 0:
        return loan / max(years * 12, 1)
    r = annual_rate / 12
    n = years * 12
    return loan * r * (1 + r) ** n / ((1 + r) ** n - 1)


# ── Sidebar population ────────────────────────────────────────────────────────

def infer_units_from_type(property_type):
    if not property_type:
        return None
    t = property_type.lower()
    if any(x in t for x in ("single family", "sfr", "single-family", "house", "townhouse", "townhome", "condo", "condominium", "manufactured", "mobile")):
        return 1
    if any(x in t for x in ("duplex", "2-unit", "2 unit", "two unit", "two-unit")):
        return 2
    if any(x in t for x in ("triplex", "3-unit", "3 unit", "three unit", "three-unit")):
        return 3
    if any(x in t for x in ("quadplex", "fourplex", "4-unit", "4 unit", "four unit", "four-unit", "quad")):
        return 4
    m = re.search(r'(\d+)\s*-?\s*unit', t)
    if m:
        return int(m.group(1))
    return None


def populate_sidebar_from_data(data):
    """Stage extracted values — applied at top of next rerun before widgets render."""
    prop = data.get("property", {})
    fin  = data.get("financing", {})

    def _g(d, key, default):
        v = d.get(key)
        return v if v is not None else default

    st.session_state["_sb_pending"] = {
        "sb_address": prop.get("address") or "",
        "sb_type":    prop.get("property_type") or "",
        "sb_sqft":    int(_g(prop, "square_feet", 0) or 0),
        "sb_price":   int(_g(prop, "purchase_price", 0) or 0),
        "sb_down":    round(float(_g(prop, "down_payment_pct", 0.25)) * 100, 2),
        "sb_closing": int(_g(prop, "closing_costs", None) or 0),
        "sb_gmi":     int(_g(prop, "gross_monthly_income", 0) or 0),
        "sb_vacancy": round(float(_g(prop, "vacancy_rate", 0.0)) * 100, 2),
        "sb_rate":    round(float(_g(fin, "interest_rate", 0.07)) * 100, 4),
        "sb_amort":   int(_g(fin, "amortization_years", 30)),
        "sb_appr":    round(float(_g(prop, "appreciation_rate", 0.03)) * 100, 2),
        "sb_rent_g":  round(float(_g(prop, "rent_growth_rate", 0.02)) * 100, 2),
        "sb_taxes":   int(_g(prop, "monthly_property_taxes", 0) or 0),
        "sb_insure":  int(_g(prop, "monthly_insurance", 0) or 0),
        "sb_util":    int(_g(prop, "monthly_utilities", 0) or 0),
        "sb_capex":   round(float(_g(prop, "capex_pct", 0.0) or 0) * 100, 2),
        "sb_maint":   round(float(_g(prop, "maintenance_pct", 0.0) or 0) * 100, 2),
        "sb_mgmt":    round(float(_g(prop, "management_pct", 0.0) or 0) * 100, 2),
        "sb_units":   int(_g(prop, "num_units", None) or infer_units_from_type(prop.get("property_type")) or 1),
    }

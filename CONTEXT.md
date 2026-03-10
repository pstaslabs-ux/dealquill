# DealQuill — Project Context & Session Handoff

Use this file to get Claude up to speed on this project instantly.

---

## What This App Is

**DealQuill** is a Streamlit-based commercial real estate deal analyzer.
- Live at: https://dealquill.streamlit.app
- GitHub repo: https://github.com/pstaslabs-ux/dealquill (public)
- Local project folder: `/Users/phillipbogan/Desktop/cre-proforma/`

Users upload deal documents or paste listing text → Claude (claude-opus-4-6) extracts deal data → live investment dashboard with cash flow, cap rate, CoC ROI, IRR, and 30-year projections.

---

## File Structure

```
cre-proforma/
├── claude_proforma_app.py   # Main Streamlit app (entry point)
├── dq_utils.py              # Shared utilities (fmt_d, fmt_p, calc_payment,
│                            #   get_history_file, load_history,
│                            #   populate_sidebar_from_data, infer_units_from_type)
├── pages/
│   └── 1_History.py         # Deal history page (imports from dq_utils, NOT claude_proforma_app)
├── .streamlit/
│   ├── config.toml          # Theme + toolbarMode = "minimal"
│   └── secrets.toml         # Gitignored — contains API keys + user credentials
├── requirements.txt
├── dq_utils.py
├── add_user.py              # CLI helper (not used in prod — users managed via secrets)
└── CONTEXT.md               # This file
```

---

## Authentication

Multi-user login using Streamlit secrets. Each user gets their own deal history file.

**How it works:**
- `_check_login()` in `claude_proforma_app.py` shows username + password form
- Credentials stored in Streamlit secrets under `[users]` table
- On login: `st.session_state["authenticated"] = True`, `st.session_state["username"] = username`
- History files named `deal_history_{username}.json` per user
- Sign Out button in sidebar shows "Signed in as **username**"
- History page checks `st.session_state.get("authenticated")` and blocks if not set

**To add a client:** Go to Streamlit Cloud → app → ⋮ → Settings → Secrets, add a line under `[users]`:
```toml
newclient = "theirpassword"
```

---

## Secrets (Streamlit Cloud)

Go to: share.streamlit.io → dealquill → ⋮ → Settings → Secrets

Current format:
```toml
ANTHROPIC_API_KEY = "sk-ant-api03-..."
HUD_TOKEN = "eyJ0eXAi..."

[users]
admin = "dealquill2024"
```

Local secrets at `.streamlit/secrets.toml` (gitignored, never committed).

**Known issue:** Streamlit Cloud secrets UI is finicky with long strings. If you get "Invalid format" errors, try typing the first line manually to confirm the UI is working, then paste the rest. Spaces around `=` are fine.

---

## Key Features

### Document Analysis
- Upload PDF, Excel, CSV, Word, images → Claude extracts deal data as JSON
- Paste listing text directly (Zillow, LoopNet, CoStar, MLS, etc.)
- Zillow URL fetch (often blocked by Zillow from cloud IPs — fallback to paste)

### When Zillow Is Blocked
- Address is auto-saved to sidebar
- User enters purchase price → HUD rent estimate and expense estimate buttons appear

### Sidebar — Manual Assumptions
- Address, property type, square feet, purchase price, down payment, closing costs
- **Income:** Number of units, bedrooms selector, HUD FMR rent estimate button
  - HUD rent × number of units = gross monthly income
- **Operating Expenses:** Estimate taxes/insurance/utilities button (Census geocoder + location-based estimates)
- Financing: interest rate, amortization years
- Growth assumptions: appreciation rate, rent growth rate
- "Run Deal" button triggers dashboard

### Dashboard Output
- Key metrics: cash flow, cap rate, CoC ROI, gross yield, break-even occupancy
- 50% Rule check
- Operating expense breakdown
- 30-year projection chart (property value, equity, cumulative cash flow)
- IRR calculation
- Missing info warnings

### Deal History
- Saved per user to `deal_history_{username}.json`
- History page (`/History`) shows all past deals with key metrics
- "View" button reloads a deal into the dashboard
- Search/filter by address
- "Clear all history" button

---

## API Integrations

| Service | Purpose | Token location |
|---|---|---|
| Anthropic Claude (claude-opus-4-6) | Document analysis, JSON extraction | `ANTHROPIC_API_KEY` in secrets |
| HUD Fair Market Rents API | Per-bedroom rent estimates by location | `HUD_TOKEN` in secrets |
| Census Geocoder | County-level lookup for tax/insurance/utility estimates | No key needed |

---

## Git / Deployment

- Remote: `https://pstaslabs-ux:{github_token}@github.com/pstaslabs-ux/dealquill.git`
- Branch: `main`
- Auto-deploys to Streamlit Cloud on every push to main
- GitHub token stored in git remote URL (not committed anywhere else)

To push changes:
```bash
cd /Users/phillipbogan/Desktop/cre-proforma
git add <files>
git commit -m "message"
git push origin main
```

---

## Important Architecture Note

**Do NOT import from `claude_proforma_app.py` in `pages/1_History.py`.**

`claude_proforma_app.py` has module-level side effects (calls `_check_login()`, `st.set_page_config()`, etc.) that break when imported. All shared functions live in `dq_utils.py` which is safe to import.

The History page imports: `get_history_file`, `load_history`, `fmt_d`, `fmt_p`, `calc_payment`, `populate_sidebar_from_data` — all from `dq_utils`.

---

## Known Issues / Decisions Made

- **Zillow scraping blocked:** Cloud server IPs get 403/blocked. Workaround: address auto-populates sidebar, user pastes listing text manually.
- **Streamlit toolbar GitHub button:** CSS hides it via `header a[href*="github"]` selector. Not 100% reliable — may need selector update if Streamlit updates.
- **Deal history is ephemeral on Streamlit Cloud:** The filesystem resets on redeploy. History is local to each server instance. A future fix would use a database (Supabase, etc.).
- **bcrypt hashes in TOML:** Caused "Invalid format" errors in Streamlit Cloud secrets UI due to `$` signs. Solved by using plaintext passwords stored directly in secrets (which are encrypted at rest by Streamlit Cloud).

---

## Passwords

- Admin login: username `admin`, password `dealquill2024`
- Change by updating the `[users]` section in Streamlit Cloud secrets

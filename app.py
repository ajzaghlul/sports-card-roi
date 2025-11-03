import streamlit as st
import requests
import pandas as pd
from urllib.parse import quote_plus

# ────────────────────────────── CONFIG ──────────────────────────────
# 1. Your eBay Partner Network Campaign ID (replace with yours)
EBAY_CAMPAIGN_ID = "YOUR_CAMPAIGN_ID"   # ← get from eBay Partner Network

# 2. PSA grading cost (bulk value tier – adjust if you use another tier)
PSA_COST = st.slider("PSA grading cost ($)", 10.0, 100.0, 21.99, 0.01)

# 3. SportsCardsPro API (free trial token – works for ~500 calls/day)
SCP_TOKEN = st.secrets.get("SCP_TOKEN", "")   # ← put in Streamlit secrets (see step 4)

# ──────────────────────── HELPER FUNCTIONS ───────────────────────
def search_sportscardspro(query: str):
    """Return ungraded & PSA-10 average sold prices."""
    if not SCP_TOKEN:
        return None, None, "⚠️ Add `SCP_TOKEN` in Streamlit secrets."
    url = "https://www.sportscardspro.com/api/products"
    params = {"t": SCP_TOKEN, "q": quote_plus(query)}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if data.get("status") != "success" or not data.get("products"):
            return None, None, "No card found – try a more specific name."
        prod = data["products"][0]
        ungraded = prod.get("loose-price", 0) / 100   # pennies → dollars
        psa10    = prod.get("manual-only-price", 0) / 100
        name     = prod.get("product-name", "Unknown")
        return ungraded, psa10, name
    except Exception as e:
        return None, None, f"API error: {e}"

def ebay_search_link(card_name: str):
    """Generate affiliate link for raw (ungraded) listings."""
    q = quote_plus(f'"{card_name}" -graded -psa -bgs -sgc')  # exclude graded
    return f"https://www.ebay.com/sch/i.html?_nkw={q}&_sop=15&rt=nc&campid={EBAY_CAMPAIGN_ID}"

# ──────────────────────── STREAMLIT UI ───────────────────────
st.set_page_config(page_title="Sports Card ROI", layout="centered")
st.title("🏀 Sports Card ROI + Flip Finder")

query = st.text_input(
    "Card name (e.g. *Michael Jordan 1986 Fleer #57*)",
    placeholder="Player Year Set #Number"
)

if st.button("Calculate ROI") and query:
    with st.spinner("Fetching price data…"):
        ungraded, psa10, msg = search_sportscardspro(query)

    if ungraded is None:
        st.error(msg)
    else:
        # ---- ROI math ----
        investment = ungraded + PSA_COST
        profit     = psa10 - investment
        roi_pct    = (profit / investment) * 100 if investment > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Ungraded Avg Sold", f"${ungraded:,.2f}")
        col2.metric("PSA-10 Avg Sold", f"${psa10:,.2f}")
        col3.metric("Grading Cost", f"${PSA_COST:,.2f}")

        st.subheader("ROI Breakdown")
        df = pd.DataFrame({
            "Metric": ["Total Investment", "Potential Profit", "ROI %", "Break-even PSA-10"],
            "Value": [
                f"${investment:,.2f}",
                f"${profit:,.2f}",
                f"{roi_pct:+.1f}%",
                f"${investment:,.2f}"
            ]
        })
        st.table(df)

        # ---- Flip color ----
        if roi_pct >= 100:
            st.success("🟢 **HIGH-FLIP OPPORTUNITY**")
        elif roi_pct >= 0:
            st.warning("🟡 Possible, but low margin")
        else:
            st.error("🔴 Likely loss after grading")

        # ---- eBay affiliate links ----
        st.subheader("📦 Cheapest Raw Listings on eBay")
        link = ebay_search_link(msg)
        st.markdown(f"[**Open eBay search → earn commission**]{link}")

        # optional: show a few live listings via eBay Finding API (free tier)
        # (omitted for brevity – you can add with your own eBay AppID)

# ──────────────────────── FOOTER ───────────────────────
st.markdown("---")
st.caption(
    "Data: SportsCardsPro (eBay sold aggregates). "
    "Affiliate clicks pay you via eBay Partner Network. "
    "Not financial advice – markets change."
)

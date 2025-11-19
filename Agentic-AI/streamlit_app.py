# streamlit_app.py — Owner-only dashboard (clean, dark theme)
import os
import time
import requests
import streamlit as st
import pandas as pd
import re
from typing import Optional
# -------------------------
from testing import OWNER_USERNAME as y
from testing import OWNER_PASSWORD as z
# --- config (use env or default) ---
API_BASE ="http://127.0.0.1:8000"
OWNER_USERNAME = y   # optional fallback
OWNER_PASSWORD = z

session = requests.Session()
st.set_page_config(page_title="Agentic Grocery — Owner Dashboard", layout="wide")

# --- style: dark blue background, white text ---
st.markdown(
    """
    <style>
    /* app background */
    .stApp {
        background: linear-gradient(180deg, #071a3a 0%, #0b3d91 100%);
        color: #ffffff;
    }
    /* card like container color */
    .stBlock {
        color: #ffffff;
    }
    /* headers */
    .big-header {
        color: #ffffff;
        font-size:20px;
        font-weight:700;
    }
    /* small badges */
    .badge-low {
        background-color: #ff4d4f;
        color: white;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-ok {
        background-color: #16a34a;
        color: white;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
    /* table styling wrapper */
    .dataframe th {
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# small helpers
# -------------------------
def api_get(path: str, params: Optional[dict] = None):
    url = f"{API_BASE}{path}"
    headers = {}
    token = st.session_state.get("auth_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = session.get(url, params=params or {}, timeout=20, headers=headers)
    r.raise_for_status()
    return r.json()


def api_post(path: str, json_body: Optional[dict] = None, require_auth=True):
    url = f"{API_BASE}{path}"
    headers = {}
    if require_auth:
        token = st.session_state.get("auth_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    r = session.post(url, json=json_body or {}, timeout=60, headers=headers)
    r.raise_for_status()
    return r.json()


def safe_api(action, *args, **kwargs):
    try:
        return action(*args, **kwargs)
    except Exception as e:
        st.error(f"API error: {e}")
        return None

# -------------------------
# login sidebar (owner only)
# -------------------------
from testing import OWNER_USERNAME as y
from testing import OWNER_PASSWORD as z
if "owner_logged_in" not in st.session_state:
    st.session_state["owner_logged_in"] = False
if "auth_token" not in st.session_state:
    st.session_state["auth_token"] = None

st.sidebar.markdown("## Owner Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
if st.sidebar.button("Login"):
    # try backend login
    try:
        resp = session.post(f"{API_BASE}/login", json={"username": username, "password": password}, timeout=10)
        if resp.ok:
            token = resp.json().get("access_token") or resp.json().get("token")
            if token:
                st.session_state["auth_token"] = token
                st.session_state["owner_logged_in"] = True
                st.sidebar.success("Logged in")
            else:
                st.sidebar.error("Login OK but no token returned. Check backend /login.")
        else:
            # fallback: if OWNER_USERNAME/PASSWORD set in env/testing, allow local login
            if OWNER_USERNAME and OWNER_PASSWORD and username == y and password == z:
                st.session_state["owner_logged_in"] = True
                st.sidebar.success("Demo login OK (fallback).")
            else:
                st.sidebar.error("Invalid credentials")
    except Exception as e:
        # network or other error — allow fallback if creds provided locally
        if OWNER_USERNAME and OWNER_PASSWORD and username == y and password == z:
            st.session_state["owner_logged_in"] = True
            st.sidebar.success("Demo login OK (network error fallback).")
        else:
            st.sidebar.error(f"Login failed: {e}")

if not st.session_state["owner_logged_in"]:
    st.markdown(
        """
        <div style="text-align:center; padding-top:100px;">
            <h1 style="color:#4CAF50;">Agentic Grocery Management</h1>
            <p style="font-size:18px;">Please log in from the sidebar to continue.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()

import streamlit as st
import pandas as pd
import os
import re

# Custom CSS for better UI
st.markdown("""
<style>
.stApp {
    background-color: #f9f9f9;
}
.big-header {
    font-size: 36px;
    font-weight: bold;
    color: #4CAF50;
    text-align: center;
    margin-bottom: 20px;
}
.section-header {
    font-size: 24px;
    font-weight: bold;
    margin-top: 30px;
    color: #333;
}
.badge-low {
    background-color: #ff4b4b;
    color: white;
    padding: 3px 8px;
    border-radius: 5px;
}
.badge-ok {
    background-color: #4CAF50;
    color: white;
    padding: 3px 8px;
    border-radius: 5px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Main UI Header
# -------------------------
st.markdown("<div class='big-header'>Agentic Grocery — Owner Dashboard</div>", unsafe_allow_html=True)
st.write("You are logged in as the store owner. Use the actions on the sidebar to manage inventory and pricing.")

# -------------------------
# Inventory Section (Full Width)
# -------------------------
st.markdown("<div class='section-header'>Inventory</div>", unsafe_allow_html=True)
items = safe_api(api_get, "/items") or []

if items:
    df = pd.DataFrame(items)
    display_cols = ["item_id", "name", "unit_price", "stock", "lead_time_days", "cost", "min_margin", "floor_price", "store_owner_whatsapp"]
    for c in display_cols:
        if c not in df.columns:
            df[c] = None

    default_thresh = int(os.getenv("DEFAULT_REORDER_THRESHOLD", "5"))
    df["status"] = df["stock"].apply(lambda s: "LOW" if (s is None or int(s) <= default_thresh) else "OK")
    df = df[display_cols + ["status"]]

    st.dataframe(df, use_container_width=True)

    low_df = df[df["status"] == "LOW"]
    if not low_df.empty:
        st.markdown("### Low Stock Items")
        for _, r in low_df.iterrows():
            st.markdown(f"- **{r['name']}** — stock: {r['stock']} — lead time: {r['lead_time_days']} days")
else:
    st.info("No items found. Seed the DB or call `/items` endpoint.")

# -------------------------
# Actions in Sidebar
# -------------------------
st.sidebar.subheader("Actions")
if st.sidebar.button("Trigger stock monitor now"):
    res = safe_api(api_post, "/monitor/trigger")
    if res is not None:
        st.sidebar.success("Stock monitor triggered")
        st.sidebar.json(res)

if st.sidebar.button("Run dynamic pricing on all items"):
    res = safe_api(api_post, "/apply_pricing_all")
    if res is not None:
        st.sidebar.success("Pricing run completed")
        st.sidebar.json(res)

if st.sidebar.button("Show recent pricing logs"):
    logs = safe_api(api_get, "/pricing_logs?limit=20")
    if logs is not None:
        st.sidebar.json(logs)


# --- Ensure API helpers are defined above this block ---
# def api_get(...), def api_post(...) must exist before running this code.

# Safe defaults
products = []
sel_name = None
sel_item = None

# Try to fetch products (defensive)
try:
    products = api_get("/items") or []
except Exception as e:
    # Log the error to the Streamlit UI but don't crash the app
    st.error(f"Failed to fetch products: {e}")
    products = []

# Build product selector UI safely
if not products:
    st.warning("No products available from backend. Check /items or seed DB.")
    # Keep sel_item None so downstream code knows nothing selected
    sel_name = None
    sel_item = None
else:
    # Normalize product names for the selectbox (avoid duplicates)
    product_names = [p.get("name") or f"Item {p.get('item_id')}" for p in products]
    # selectbox requires a non-empty list; we already have one
    sel_name = st.selectbox("Select product", product_names)
    # find selected item object (safe fallback to first element)
    sel_item = next(
        (
            p
            for p in products
            if (p.get("name") or f"Item {p.get('item_id')}") == sel_name
        ),
        products[0] if products else None,
    )

# Show basic info only if sel_item exists
if sel_item:
    st.write(f"**Selected:** {sel_item.get('name')}")
    st.write(f"**Stock:** {sel_item.get('stock','-')} units")
    st.write(f"**Lead time (days):** {sel_item.get('lead_time_days','-')}")
else:
    st.info("No product selected.")

# Suppliers Section (Full Width)
st.markdown("<div class='section-header'>Suppliers</div>", unsafe_allow_html=True)
# call backend for supplier rows (replace older call)
def fetch_supplier_rows(item_name):
    try:
        return api_get(f"/supplier_prices", params={"item": item_name})
    except Exception as e:
        st.error(f"Supplier fetch failed: {e}")
        return {"rows": []}

# usage
if sel_item:
    sp = fetch_supplier_rows(sel_item["name"])
    rows = sp.get("rows", [])
    if rows:
        df = pd.DataFrame(rows)
        # show key columns: supplier_name, parsed_price, parsed_eta, whatsapp_number, excerpt
        st.dataframe(df[["supplier_name","parsed_price","parsed_eta","whatsapp_number","excerpt"]].sort_values("parsed_price", na_position="last"), use_container_width=True)
    else:
        st.info("No supplier messages for this item.")

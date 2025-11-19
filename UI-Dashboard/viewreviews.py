import streamlit as st
import sqlite3
import pandas as pd

# -------------------------------------------------------
# 📦 Load Data from reviews.db
# -------------------------------------------------------
def load_reviews():
    try:
        conn = sqlite3.connect("reviews.db")
        df = pd.read_sql_query("SELECT * FROM reviews", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Error reading database: {e}")
        return pd.DataFrame()

# -------------------------------------------------------
# 🖥️ Streamlit UI
# -------------------------------------------------------
st.set_page_config(page_title="📊 Review Database Viewer", layout="wide")

st.title("📦 Review Database Viewer")
st.write("This tool lets you inspect the contents of `reviews.db`.")

if st.button("🔄 Load Reviews"):
    df = load_reviews()
    if not df.empty:
        st.success(f"✅ Loaded {len(df)} reviews from database.")
        st.dataframe(df)
        st.metric("Total Reviews", len(df))
        if "rating" in df.columns:
            try:
                avg_rating = pd.to_numeric(df["rating"], errors="coerce").mean()
                st.metric("Average Rating", round(avg_rating, 2))
            except:
                pass
    else:
        st.warning("⚠️ No data found in reviews.db yet. Run the scraper first.")
else:
    st.info("Click the button above to load reviews.")

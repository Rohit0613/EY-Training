# main.py
import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import subprocess
import re
from collections import Counter
from wordcloud import WordCloud
import time
import math

# Local imports (assumes these files are present)
from scraper.amazon_scraper import extract_asin, get_product_title
from scraper.flipkart_scraper import get_flipkart_title
from analysis.sentiment_engine import analyze_sentiment, summarize_reviews
from database.db_handler import (
    init_db, insert_review, fetch_reviews,
    add_to_watchlist, get_watchlist, remove_from_watchlist
)
from scheduler.scheduler import start_scheduler

# ---------------------------
# Page config, DB init, scheduler
# ---------------------------
st.set_page_config(page_title="Client Sentiment Radar", layout="wide")
init_db()
# start_scheduler()  # comment/uncomment based on dev needs
start_scheduler()

# ---------------------------
# Simple theme CSS
# ---------------------------
st.markdown("""
<style>
    .main { background-color: #0F1217; color: #EEEEEE; }
    div[data-testid="metric-container"] { background-color: #1C1F26; border-radius: 12px; padding: 12px; }
    h1,h2,h3,h4 { color: #4FC3F7 !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Utilities: phrase extraction + sentiment parsing
# ---------------------------

STOPWORDS = {
    "the","and","a","an","is","it","this","that","with","for","to","of","in","on",
    "was","are","as","but","i","you","they","we","he","she","my","our","its","at",
    "by","be","have","has","had","not","from","so","if","or","very","too","also"
}

def tokenize_text(s: str):
    tokens = re.findall(r"\b\w+\b", (s or "").lower())
    tokens = [t for t in tokens if len(t) > 2 and t not in STOPWORDS and not t.isdigit()]
    return tokens

def top_ngrams(texts, top_n=12):
    uni = Counter()
    bi = Counter()
    tri = Counter()
    for t in texts:
        toks = tokenize_text(t)
        uni.update(toks)
        for i in range(len(toks)-1):
            bi[" ".join(toks[i:i+2])] += 1
        for i in range(len(toks)-2):
            tri[" ".join(toks[i:i+3])] += 1
    combined = Counter()
    combined.update(bi)
    combined.update(tri)
    if not combined:
        return uni.most_common(top_n)
    return combined.most_common(top_n)

def safe_parse_sentiment(result):
    """Turn LLM result into dict {'sentiment':..., 'topics':[...]} with fallbacks."""
    if isinstance(result, dict):
        return result
    if isinstance(result, str):
        # Try JSON
        try:
            return json.loads(result)
        except:
            # Extract JSON substring
            m = re.search(r"\{.*\}", result, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except:
                    pass
            # heuristic
            low = result.lower()
            if "positive" in low:
                return {"sentiment":"Positive","topics":[]}
            if "negative" in low:
                return {"sentiment":"Negative","topics":[]}
            if "neutral" in low:
                return {"sentiment":"Neutral","topics":[]}
    return {"sentiment":"Unknown","topics":[]}

def safe_parse_summary(result):
    """Return summary string from LLM result (dict or text)."""
    if isinstance(result, dict):
        # support {"summary": "..."} or direct keys
        return result.get("summary") or result.get("text") or json.dumps(result)
    if isinstance(result, str):
        return result
    return "Summary unavailable."

# ---------------------------
# UI: Title and Watchlist Sidebar
# ---------------------------
st.title("🛒 Client Sentiment Radar — Product Review Insights")
st.caption("Analyze Amazon / Flipkart product reviews: sentiment, top complaints, churn risk & AI summary.")

with st.sidebar:
    st.header("⭐ Watchlist")
    watchlist_rows = get_watchlist()
    if watchlist_rows:
        for w in watchlist_rows:
            st.markdown(f"### [{w['product_name']}]({w['product_url']})")
            st.caption(f"🛍 {w['platform']} • Last updated: {w['last_updated']}")
            if st.button("Remove", key=f"rm_{w['product_id']}"):
                remove_from_watchlist(w['product_id'])
                st.rerun()
            st.divider()
    else:
        st.info("No products tracked yet. Add one using the main panel.")

# ---------------------------
# Main Input: URL + pages to scrape
# ---------------------------
url = st.text_input("Enter Amazon or Flipkart product URL:", key="product_url_input")
pages_to_scrape = st.slider("Pages to scrape (approx 10-20 reviews per page)", min_value=1, max_value=10, value=3, step=1)

# ---------------------------
# Analysis button — runs the scraper as a subprocess (run_scraper.py)
# ---------------------------
if st.button("Analyze Product", key="analyze_btn"):
    if not url or not url.strip():
        st.warning("Please paste a valid product URL.")
        st.stop()

    st.info("🔎 Starting analysis — scraper will run in a separate process (may take some time)...")

    # Call the external scraper which inserts into DB
    try:
        proc = subprocess.run(
            ["python", "run_scraper.py", url, str(pages_to_scrape)],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes; adjust if necessary
        )
    except subprocess.TimeoutExpired:
        st.error("❌ Scraper timed out. Try a smaller pages-to-scrape value or run scraper separately.")
        st.stop()

    if proc.returncode != 0:
        st.error("❌ Scraper failed. See console output below:")
        if proc.stderr:
            st.code(proc.stderr)
        if proc.stdout:
            st.code(proc.stdout)
        st.stop()

    st.success("✅ Scraper completed and saved reviews to database.")

    # Resolve platform + asin + product_name
    try:
        if "amazon" in url.lower():
            platform = "Amazon"
            asin = extract_asin(url)
            product_name = get_product_title(asin)
        elif "flipkart" in url.lower():
            platform = "Flipkart"
            asin = url.split("/")[-1][:10]
            product_name = get_flipkart_title(url)
        else:
            st.error("Unsupported platform.")
            st.stop()
    except Exception as e:
        st.error("Failed to extract product metadata.")
        st.exception(e)
        st.stop()

    # Add to watchlist (DB)
    try:
        add_to_watchlist(platform, asin, product_name, url)
    except Exception as e:
        st.warning("Watchlist add failed (non-fatal).")
        print("Watchlist error:", e)
    from database.db_handler import fetch_reviews as fetch_reviews_db

    rows = fetch_reviews_db(asin)
    if not rows:
        st.warning("Scraper finished but no reviews were saved — check debug logs or try increasing pages.")
    else:
        st.session_state["last_asin"] = asin
        st.session_state["last_name"] = product_name
        st.session_state["last_platform"] = platform
        st.rerun()

# ---------------------------
# Helper: generate & render AI summary with robust fallback
# ---------------------------
def generate_and_render_summary(df):
    """
    Attempt LLM summary, fall back to local summary if LLM fails/returns placeholder.
    Renders the summary to Streamlit and shows whether it was LLM or fallback.
    Assumes df already has 'sentiment_norm' canonicalized.
    """
    # Prepare combined text for LLM
    combined_text = "\n".join(df["text"].astype(str).tolist()[:60])
    llm_raw = None
    summary_text = None

    # Try LLM
    try:
        llm_raw = summarize_reviews(combined_text)  # should return a string (or diagnostic string)
        # Accept LLM output only if it's a non-empty string and doesn't contain known failure phrases
        if isinstance(llm_raw, str):
            s = llm_raw.strip()
            if s and not any(x in s.lower() for x in [
                "summary could not be generated",
                "key missing",
                "summary parse failed",
                "llm error",
                "fallback",
                "unavailable"
            ]):
                summary_text = s
            else:
                # helpful debug info in logs
                print("[MAIN] LLM returned fallback message or empty. Raw (truncated):", llm_raw[:400])
        else:
            print("[MAIN] summarize_reviews() returned non-str:", type(llm_raw))
            llm_raw = str(llm_raw)
    except Exception as e:
        print("[MAIN] summarize_reviews() exception:", e)
        try:
            import traceback; traceback.print_exc(limit=1)
        except:
            pass
        llm_raw = f"EXCEPTION: {e}"

    # Local fallback summary (if LLM didn't produce usable text)
    if not summary_text:
        def phrases_to_list(pairs):
            out = []
            for it in pairs:
                if isinstance(it, tuple):
                    out.append(it[0])
                else:
                    out.append(str(it))
            return out

        total = len(df) or 1
        pos = int((df['sentiment_norm'] == 'Positive').sum())
        neg = int((df['sentiment_norm'] == 'Negative').sum())
        neu = int((df['sentiment_norm'] == 'Neutral').sum())

        top_pos = phrases_to_list(top_ngrams(df[df['sentiment_norm'] == 'Positive']['text'].astype(str).tolist(), top_n=6))
        top_neg = phrases_to_list(top_ngrams(df[df['sentiment_norm'] == 'Negative']['text'].astype(str).tolist(), top_n=6))

        local_fallback_text = (
            f"Overall: {round(pos / total * 100, 1)}% positive, {round(neg / total * 100, 1)}% negative, {round(neu / total * 100, 1)}% neutral.\n\n"
            f"Top positives: {', '.join(top_pos) if top_pos else '—'}\n"
            f"Top negatives: {', '.join(top_neg) if top_neg else '—'}\n\n"
            "LLM summary unavailable — showing local fallback."
        )

        summary_text = local_fallback_text

    # Render summary and show small note if it came from LLM
    try:
        # If LLM provided exactly the same text (and it's non-empty), mark as LLM
        if llm_raw and isinstance(llm_raw, str) and summary_text == llm_raw.strip():
            st.success("AI summary (LLM)")
            st.info(summary_text)
        else:
            st.info(summary_text)
            if llm_raw:
                # keep caption tiny and truncated so UI stays tidy
                tr = (llm_raw[:300] + "...") if len(str(llm_raw)) > 300 else str(llm_raw)
                st.caption(f"LLM raw (truncated): {tr}")
    except Exception as e:
        print("[MAIN] Error rendering summary:", e)
        st.info(summary_text)

# ---------------------------
# Dashboard — show when last_asin present in session
# ---------------------------
if "last_asin" in st.session_state:
    asin = st.session_state["last_asin"]
    product_name = st.session_state.get("last_name", asin)
    platform = st.session_state.get("last_platform", "Unknown")

    st.markdown(f"## 📦 {product_name} ({platform}) — Sentiment Dashboard")

    # Fetch reviews for this ASIN
    raw = fetch_reviews(asin)
    if not raw:
        st.warning("No reviews stored for this product yet. Try increasing pages to scrape or run scraper separately to debug.")
    else:
        df = pd.DataFrame(raw, columns=["rating", "sentiment", "topics", "date", "text"])

        # KPIs
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Reviews", len(df))
        with col2:
            try:
                avg_rating = pd.to_numeric(df["rating"], errors="coerce").mean()
                st.metric("Average Rating", round(avg_rating, 2))
            except:
                st.metric("Average Rating", "N/A")
        with col3:
            try:
                # ensure canonical label for "dominant"
                df['sentiment_norm'] = df['sentiment'].fillna('Neutral').astype(str).str.strip().str.title()
                df['sentiment_norm'] = df['sentiment_norm'].replace({
                    'Pos': 'Positive', 'Neg': 'Negative', 'Neu': 'Neutral', 'Pending': 'Neutral', 'Unknown': 'Neutral',
                    '': 'Neutral'
                })
                dominant = df['sentiment_norm'].value_counts().idxmax()
            except Exception:
                dominant = "Unknown"
            st.metric("Dominant Sentiment", dominant)

        # ------------------ AI Summary + Churn Meter ------------------
        # ensure canonical sentiments exist for everything
        df['sentiment_norm'] = df['sentiment'].fillna('Neutral').astype(str).str.strip().str.title()
        df['sentiment_norm'] = df['sentiment_norm'].replace({
            'Pos': 'Positive', 'Neg': 'Negative', 'Neu': 'Neutral', 'Pending': 'Neutral', 'Unknown': 'Neutral',
            '': 'Neutral'
        })

        # generate and render summary (LLM first + fallback)
        st.subheader("🧠 AI Summary of Reviews")
        generate_and_render_summary(df)

        # ------------------ Churn meter (always render) ------------------
        st.subheader("🔥 Churn Risk Meter")

        def compute_churn_risk_v2(df_local):
            try:
                total = len(df_local)
                if total == 0:
                    return 0.0
                neg = int((df_local['sentiment_norm'] == 'Negative').sum())
                negative_ratio = neg / total
                avg_rating = pd.to_numeric(df_local['rating'], errors='coerce').mean()
                if pd.isna(avg_rating):
                    avg_rating = 4.5
                rating_gap = max(0, (4.5 - avg_rating) / 4.5)
                text_blob = " ".join(df_local["topics"].astype(str).tolist()).lower() + " " + " ".join(
                    df_local["text"].astype(str).tolist()).lower()
                critical_keywords = ["refund", "return", "broken", "heat", "heating", "battery", "fault", "dead",
                                     "smoke", "water", "crack"]
                hits = sum(text_blob.count(k) for k in critical_keywords)
                topic_score = min(1.0, hits / max(3, total * 0.15))
                w_neg = 0.40
                w_rad = 0.30
                w_topic = 0.30
                raw_score = (negative_ratio * w_neg) + (rating_gap * w_rad) + (topic_score * w_topic)
                return min(100, round(raw_score * 100, 1))
            except Exception as e:
                print("Churn compute error:", e)
                return 0.0

        risk_score = compute_churn_risk_v2(df)
        if risk_score is None or (isinstance(risk_score, float) and math.isnan(risk_score)):
            risk_score = 0.0

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score,
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "red" if risk_score > 60 else "orange" if risk_score > 30 else "green"},
                'steps': [
                    {'range': [0, 30], 'color': "lightgreen"},
                    {'range': [30, 60], 'color': "gold"},
                    {'range': [60, 100], 'color': "salmon"}
                ],
            },
            title={'text': "Churn Risk %"}
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

        # ------------------ Pie & KPIs (use canonical sentiment_norm) ------------------
        colA, colB = st.columns([1, 2])
        with colA:
            st.subheader("Sentiment Breakdown")
            df_plot = df.copy()
            fig1 = px.pie(df_plot, names="sentiment_norm", title="")
            st.plotly_chart(fig1, use_container_width=True)
            counts = df_plot["sentiment_norm"].value_counts()
            total_for_pct = len(df_plot) or 1
            st.metric("Positive %", f"{(counts.get('Positive', 0) / total_for_pct * 100):.1f}%")
            st.metric("Negative %", f"{(counts.get('Negative', 0) / total_for_pct * 100):.1f}%")
            st.metric("Neutral %", f"{(counts.get('Neutral', 0) / total_for_pct * 100):.1f}%")

        with colB:
            st.subheader("Top Phrases (bigram / trigram) — actionable complaints & positives")
            top_k = st.slider("Top N phrases to show", min_value=5, max_value=30, value=12, key="top_k_phrases")
            phrases = top_ngrams(df["text"].astype(str).tolist(), top_n=top_k)
            if phrases:
                labels = [p for p,c in phrases]
                counts = [c for p,c in phrases]
                bar_fig = px.bar(x=counts[::-1], y=labels[::-1], orientation='h', labels={'x':'Count','y':'Phrase'})
                st.plotly_chart(bar_fig, use_container_width=True)
                st.markdown("**Top phrases**")
                for p,c in phrases:
                    st.write(f"- **{p}** — {c} mentions")
            else:
                st.info("No strong phrases found.")

        # Optional wordcloud
        if st.checkbox("Show optional wordcloud (single words)", key="wc_opt"):
            try:
                text_for_wc = " ".join(df["text"].astype(str).tolist())
                wc = WordCloud(width=900, height=350, collocations=False).generate(text_for_wc)
                plt.imshow(wc, interpolation="bilinear")
                plt.axis("off")
                st.pyplot(plt)
            except Exception as e:
                st.warning("Wordcloud generation failed.")
                print("Wordcloud error:", e)

        # Recent reviews table
        st.subheader("Recent Reviews")
        st.dataframe(df[["date","rating","sentiment","text"]], use_container_width=True)

else:
    st.info("Paste a product URL and click Analyze to begin.")

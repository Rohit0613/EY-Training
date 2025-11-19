# analysis/sentiment_engine.py
import os
import time
import json
import re
import traceback
import requests

# try to import testing shim (optional). If not present, fall back to env vars.
try:
    from testing import OPENROUTER_API_KEY as a, OPENROUTER_BASE_URL as b
except Exception:
    a = None
    b = None

OPENROUTER_API_KEY = a or os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = (b or os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1").rstrip("/")

if not OPENROUTER_API_KEY:
    print("⚠️ Warning: OPENROUTER_API_KEY not set. LLM calls will fail or return placeholders.")


def _post_with_retries(url, headers, payload, retries=3, backoff_factor=1.5, timeout=60):
    """
    POST with retry/backoff handling for 429 / 503 and transient network errors.
    Returns the requests.Response (or None on permanent failure).
    """
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 503):
                sleep_for = backoff_factor * attempt
                print(f"[LLM] status {r.status_code}, retrying after {sleep_for}s (attempt {attempt})")
                time.sleep(sleep_for)
                continue
            # other non-200: return for caller to inspect
            return r
        except requests.RequestException as e:
            sleep_for = 0.8 * attempt
            print(f"[LLM] Request exception (attempt {attempt}): {e}. Sleeping {sleep_for}s then retrying.")
            time.sleep(sleep_for)
    print("[LLM] All retries exhausted.")
    return None


def _normalize_sentiment_label(s):
    """Normalize to one of: Positive, Negative, Neutral, Unknown"""
    if not s or not isinstance(s, str):
        return "Unknown"
    low = s.strip().lower()
    if "pos" in low or "good" in low or "love" in low or "great" in low:
        return "Positive"
    if "neg" in low or "bad" in low or "poor" in low or "hate" in low:
        return "Negative"
    if "neu" in low or "neutral" in low or "mixed" in low:
        return "Neutral"
    # fallback: if the string contains "positive"/"negative"/"neutral"
    if "positive" in low:
        return "Positive"
    if "negative" in low:
        return "Negative"
    if "neutral" in low:
        return "Neutral"
    return "Unknown"


def analyze_sentiment(text: str):
    """
    Uses Mistral (via OpenRouter) to extract sentiment and topics from a review.
    Returns a dict: {"sentiment": "Positive"/"Negative"/"Neutral"/"Unknown", "topics": [...]}
    Defensive: always returns a dict.
    """
    if not OPENROUTER_API_KEY:
        # graceful fallback for dev
        return {"sentiment": "Unknown", "topics": []}

    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}

    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an AI that analyzes product reviews. "
                    "Respond in JSON only (no extra text). Extract the following keys:\n"
                    "- sentiment: one of Positive, Negative, or Neutral\n"
                    "- topics: a JSON list of short topic strings (e.g. [\"battery\", \"display\"]).\n"
                    "If unsure, return sentiment 'Unknown' and an empty list for topics."
                )
            },
            {"role": "user", "content": text}
        ]
    }

    try:
        res = _post_with_retries(url, headers, payload, retries=3, backoff_factor=1.5, timeout=60)
        if res is None:
            return {"sentiment": "Unknown", "topics": []}

        if res.status_code != 200:
            print(f"⚠️ OpenRouter returned status {res.status_code}: {res.text[:800]}")
            return {"sentiment": "Unknown", "topics": []}

        body = res.json()
        # expected structure: {"choices":[{"message":{"content":"..."}}, ...], ...}
        try:
            content = body["choices"][0]["message"]["content"]
        except Exception:
            content = json.dumps(body)

        # Try to extract JSON object from the model output
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                sentiment_raw = parsed.get("sentiment", None)
                topics_raw = parsed.get("topics", [])
                sentiment = _normalize_sentiment_label(sentiment_raw)
                # ensure topics list
                if isinstance(topics_raw, list):
                    topics = [str(t).strip() for t in topics_raw if str(t).strip()]
                elif isinstance(topics_raw, str):
                    topics = [t.strip() for t in re.split(r"[,\n;]", topics_raw) if t.strip()]
                else:
                    topics = []
                return {"sentiment": sentiment, "topics": topics}
            except Exception as e:
                print("[LLM] JSON parse error:", e)
                # fall through to heuristics

        # heuristics on plain text
        low = (content or "").lower()
        if "positive" in low:
            return {"sentiment": "Positive", "topics": []}
        if "negative" in low:
            return {"sentiment": "Negative", "topics": []}
        if "neutral" in low:
            return {"sentiment": "Neutral", "topics": []}

        # final fallback
        return {"sentiment": "Unknown", "topics": []}

    except Exception as e:
        print("⚠️ Sentiment analysis failed:", e)
        traceback.print_exc(limit=1)
        return {"sentiment": "Unknown", "topics": []}


def summarize_reviews(text_batch: str, model="mistralai/mistral-7b-instruct") -> str:
    """
    Produce a short, structured human-readable summary for a batch of reviews.
    Returns a plain string (not JSON). Logs raw LLM response for debugging.
    """
    if not OPENROUTER_API_KEY:
        return "LLM key missing — summary unavailable."

    prompt = (
        "You are an assistant that summarizes user reviews. "
        "Produce a short (4-8 sentences) human-friendly summary with these sections:\n"
        "1) Overall sentiment (one sentence)\n"
        "2) Top positives (short phrases)\n"
        "3) Top negatives / complaints (short phrases)\n"
        "4) One short recommendation for the product team.\n\n"
        "Output plain text only (no JSON). Keep it concise.\n\nREVIEWS:\n"
    ) + (text_batch or "")[:20000]

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You summarize product reviews concisely for a product manager."},
            {"role": "user", "content": prompt}
        ]
    }
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    url = f"{OPENROUTER_BASE_URL}/chat/completions"

    res = _post_with_retries(url, headers, payload, retries=3, backoff_factor=1.5, timeout=60)
    if res is None:
        return "Summary could not be generated (LLM networking error)."

    try:
        print("[SUMMARY] LLM status:", res.status_code)
        print("[SUMMARY] Raw body (truncated 2000 chars):", (res.text or "")[:2000])
    except Exception:
        pass

    if res.status_code != 200:
        return f"Summary could not be generated (LLM status {res.status_code})."

    try:
        body = res.json()
        content = body["choices"][0]["message"]["content"]
        if isinstance(content, str) and content.strip():
            return content.strip()
        return str(body)[:3000]
    except Exception as e:
        print("Summary parse error:", e)
        return "Summary parse failed (LLM returned unexpected format)."

# scraper/amazon_scraper.py
import re
import time
import random
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha1
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from database.db_handler import insert_review

# -----------------------
# Config (tweak these)
# -----------------------
MAX_WORKERS = 2            # safer default for parallelism
REQUEST_RETRIES = 4
REQUEST_BACKOFF = (0.8, 1.8)
PAGE_FETCH_TIMEOUT = 25    # seconds
MAX_EMPTY_PAGES = 3        # stop early after N consecutive empty pages
MAX_PAGES_SAFE = 100       # absolute upper bound if last page detection fails
PLAYWRIGHT_PROFILE = str(Path.cwd() / "pw_profile")  # persistent profile dir for playwright fallback
ENABLE_PLAYWRIGHT_FALLBACK = True                   # set False to disable Playwright fallback

# Basic headers used for requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/121 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9,en-US;q=0.8",
}

# -----------------------
# Helpers
# -----------------------
def extract_asin(url: str) -> Optional[str]:
    """Robust ASIN extractor for common Amazon URL formats."""
    if not url:
        return None
    url = url.strip()
    patterns = [
        r"/dp/([A-Za-z0-9]{10})",
        r"/gp/product/([A-Za-z0-9]{10})",
        r"/product-reviews/([A-Za-z0-9]{10})",
        r"/([A-Za-z0-9]{10})(?:[/?]|$)"
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

def get_product_title(asin: str) -> str:
    """
    Fetch product title from the main product page.
    Used only for UI display / watchlist.
    """
    url = f"https://www.amazon.in/dp/{asin}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return f"Amazon Product {asin}"
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.select_one("#productTitle")
        if title:
            return title.get_text(strip=True)
    except:
        pass
    return f"Amazon Product {asin}"

def normalize_amazon_url(asin: str) -> str:
    """Return canonical product URL for display/watchlist."""
    return f"https://www.amazon.in/dp/{asin}" if asin else ""


def _safe_get(url: str, headers=None, timeout=PAGE_FETCH_TIMEOUT) -> Optional[requests.Response]:
    headers = headers or HEADERS
    last_exc = None
    for attempt in range(1, REQUEST_RETRIES + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp
            last_exc = Exception(f"Status {resp.status_code}")
        except Exception as e:
            last_exc = e
        sleep_for = 0.5 * attempt
        time.sleep(sleep_for)
    print(f"[WARN] Failed GET {url}: {last_exc}")
    return None


# -----------------------
# JSON endpoint fetch
# -----------------------
def fetch_reviews_page_json(asin: str, page: int) -> List[Dict]:
    """
    Try Amazon's reviews-render endpoint (fast) — defensive parsing.
    Returns list of reviews or empty list if unusable.
    """
    api_url = (
        "https://www.amazon.in/hz/reviews-render/ajax/reviews/get/"
        f"ref=cm_cr_dp_d_show_all_btm?asin={asin}&pageNumber={page}&reviewerType=all_reviews"
    )
    resp = _safe_get(api_url)
    if not resp:
        return []

    text = resp.text or ""
    soup = BeautifulSoup(text, "html.parser")
    blocks = soup.select("div[data-hook='review'], div.review, div[data-cel-widget^='customer_review-']")
    reviews = []
    for b in blocks:
        rating_el = b.select_one("i[data-hook='review-star-rating'] span") or b.select_one("span.a-icon-alt")
        text_el = b.select_one("span[data-hook='review-body'] span") or b.select_one("span.review-text-content span")
        date_el = b.select_one("span[data-hook='review-date']")

        rating = rating_el.get_text(strip=True).split("out of")[0].strip() if rating_el else None
        text_content = text_el.get_text(" ", strip=True) if text_el else None
        date = date_el.get_text(strip=True) if date_el else None

        if text_content:
            reviews.append({"rating": rating, "date": date, "text": text_content})
    return reviews


# -----------------------
# HTML page fetch (requests)
# -----------------------
def fetch_reviews_page_html(asin: str, page: int) -> List[Dict]:
    """
    Robust HTML fetch using requests.Session with Referer and cookies.
    Returns list of review dicts or [].
    """
    session = requests.Session()
    session.headers.update(HEADERS)
    product_url = f"https://www.amazon.in/dp/{asin}/"

    try:
        prod_resp = _safe_get(product_url)
        if prod_resp is not None:
            session.cookies.update(prod_resp.cookies)
    except Exception as e:
        print("[HTML FETCH] product page visit error:", e)

    review_url = f"https://www.amazon.in/product-reviews/{asin}/?pageNumber={page}"
    for attempt in range(1, REQUEST_RETRIES + 1):
        try:
            resp = session.get(review_url, timeout=PAGE_FETCH_TIMEOUT, allow_redirects=True)
            status = resp.status_code
            body = resp.text or ""
            print(f"[HTML FETCH] page {page} status={status} len={len(body)} (attempt {attempt})")

            low = body.lower()
            if status != 200 or any(x in low for x in ("captcha", "verify", "access to this page", "blocked", "sign in")):
                time.sleep(0.8 * attempt)
                continue

            soup = BeautifulSoup(body, "html.parser")
            blocks = soup.select(
                "div[data-hook='review'], div.review, div[data-cel-widget^='customer_review-'], div.a-section.review.aok-relative"
            )

            if not blocks:
                # save snippet for debug
                snippet = body[:2000].replace("\n", " ")
                fname = f"debug_html_{asin}_p{page}.html"
                try:
                    with open(fname, "w", encoding="utf8") as f:
                        f.write(body)
                    print(f"[HTML FETCH] WARNING: no review blocks on page {page}. saved {fname}")
                except Exception:
                    print("[HTML FETCH] WARNING: could not save debug snapshot.")
                return []

            results = []
            for b in blocks:
                rating_el = b.select_one("i[data-hook='review-star-rating'] span") or b.select_one("span.a-icon-alt")
                text_el = (
                    b.select_one("span[data-hook='review-body'] span")
                    or b.select_one("span.review-text-content span")
                    or b.select_one("div.reviewText span")
                )
                date_el = b.select_one("span[data-hook='review-date']")

                rating = rating_el.get_text(strip=True).split("out of")[0].strip() if rating_el else None
                text = text_el.get_text(" ", strip=True) if text_el else None
                date = date_el.get_text(strip=True) if date_el else None

                if text:
                    results.append({"rating": rating, "date": date, "text": text})
            return results

        except Exception as e:
            print(f"[HTML FETCH] Exception fetching page {page}: {e} (attempt {attempt})")
            time.sleep(0.8 * attempt)
            continue

    print(f"[HTML FETCH] All attempts failed for page {page}")
    return []


# -----------------------
# Playwright fallback (only when needed)
# -----------------------
from pathlib import Path

PROFILE_DIR = str(Path.cwd() / "pw_profile")   # <--- use SAME folder as login


def fetch_page_with_playwright(asin: str, page: int = 1, profile_dir: str = PLAYWRIGHT_PROFILE) -> List[Dict]:
    """Open a real browser (Playwright) and extract reviews — requires playwright installed."""
    if not ENABLE_PLAYWRIGHT_FALLBACK:
        print("[PW] Playwright fallback disabled.")
        return []

    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        print("[PW] Playwright not available:", e)
        return []

    url = f"https://www.amazon.in/product-reviews/{asin}/?pageNumber={page}"
    reviews = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(user_data_dir=profile_dir, headless=False)
            page_obj = browser.new_page()
            page_obj.goto(url, timeout=60000)
            page_obj.wait_for_load_state("networkidle")
            # scroll to force dynamic loading
            for _ in range(4):
                page_obj.mouse.wheel(0, 2000)
                time.sleep(0.8)
            html = page_obj.content()
            # save snapshot for debugging
            try:
                with open(f"pw_debug_{asin}_p{page}.html", "w", encoding="utf8") as f:
                    f.write(html)
                print(f"[PW] Saved pw_debug_{asin}_p{page}.html")
            except Exception:
                pass
            browser.close()

        soup = BeautifulSoup(html, "html.parser")
        blocks = soup.select("div[data-hook='review'], div.review, div[data-cel-widget^='customer_review-'], div.a-section.review.aok-relative")
        for b in blocks:
            rating_el = b.select_one("i[data-hook='review-star-rating'] span") or b.select_one("span.a-icon-alt")
            text_el = (
                b.select_one("span[data-hook='review-body'] span")
                or b.select_one("span.review-text-content span")
                or b.select_one("div.reviewText span")
            )
            date_el = b.select_one("span[data-hook='review-date']")
            rating = rating_el.get_text(strip=True).split("out of")[0].strip() if rating_el else None
            text = text_el.get_text(" ", strip=True) if text_el else None
            date = date_el.get_text(strip=True) if date_el else None
            if text:
                reviews.append({"rating": rating, "date": date, "text": text})
        print(f"[PW] Extracted {len(reviews)} reviews via Playwright (page {page})")
        return reviews

    except Exception as e:
        print("[PW] Playwright error:", e)
        return []


# -----------------------
# Utility: dedupe by review text
# -----------------------
def _unique_reviews(reviews: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for r in reviews:
        text = (r.get("text") or "").strip()
        if not text:
            continue
        h = sha1(text.encode("utf-8")).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        out.append(r)
    return out


# -----------------------
# Detect last page (best-effort)
# -----------------------
def detect_last_page(asin: str) -> Optional[int]:
    url = f"https://www.amazon.in/product-reviews/{asin}/"
    resp = _safe_get(url)
    if not resp:
        return None
    soup = BeautifulSoup(resp.text, "html.parser")
    paginator = soup.select_one("ul.a-pagination")
    if paginator:
        pages = []
        for li in paginator.select("li"):
            t = li.get_text(strip=True)
            if t.isdigit():
                pages.append(int(t))
        if pages:
            return max(pages)
    # fallback: look for "Page 1 of X"
    text = soup.get_text(" ", strip=True)
    m = re.search(r"Page\s*\d+\s*of\s*(\d+)", text, flags=re.IGNORECASE)
    if m:
        try:
            return int(m.group(1))
        except:
            return None
    return None


# -----------------------
# Worker: per-page fetch (JSON -> HTML -> Playwright)
# -----------------------
def _fetch_page_worker(asin: str, page: int, polite: bool = True) -> List[Dict]:
    if polite:
        time.sleep(random.uniform(*REQUEST_BACKOFF))

    # JSON
    reviews = fetch_reviews_page_json(asin, page)
    if reviews:
        return reviews

    # HTML
    reviews = fetch_reviews_page_html(asin, page)
    if reviews:
        return reviews

    # Playwright fallback (last resort)
    reviews = fetch_page_with_playwright(asin, page)
    return reviews

try:
    from analysis.sentiment_engine import analyze_sentiment, summarize_reviews
except Exception as e:
    print("[IMPORT] Could not import analyze_sentiment:", e)
    # define a tiny fallback to avoid NameError
    def analyze_sentiment(text):
        return {"sentiment": "Unknown", "topics": []}
# -----------------------
# Public API: scrape_reviews
# -----------------------
def safe_analyze_sentiment(text: str):
    """
    Safe wrapper around analyze_sentiment().
    Always returns a dict:
        { "sentiment": "...", "topics": [...] }
    even if LLM fails, times out, or returns junk.
    """
    try:
        raw = analyze_sentiment(text)
    except Exception as e:
        print("[LLM ERROR] analyze_sentiment crashed:", e)
        return {"sentiment": "Unknown", "topics": []}

    # Case 1: Already proper dict
    if isinstance(raw, dict):
        return {
            "sentiment": raw.get("sentiment", "Unknown"),
            "topics": raw.get("topics", []) or []
        }

    # Case 2: JSON string
    if isinstance(raw, str):
        import re, json
        # Try extract JSON
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group())
                return {
                    "sentiment": parsed.get("sentiment", "Unknown"),
                    "topics": parsed.get("topics", []) or []
                }
            except:
                pass

        # Fallback heuristics
        low = raw.lower()
        if "positive" in low:
            return {"sentiment": "Positive", "topics": []}
        if "negative" in low:
            return {"sentiment": "Negative", "topics": []}
        if "neutral" in low:
            return {"sentiment": "Neutral", "topics": []}

        return {"sentiment": "Unknown", "topics": []}

    # Final fallback
    return {"sentiment": "Unknown", "topics": []}

def scrape_reviews(asin: str, max_pages: Optional[int] = None, max_workers: int = MAX_WORKERS, polite: bool = True) -> List[Dict]:
    """
    Scrape reviews for an ASIN.
    - If max_pages is None: attempt to detect last page; otherwise iterate until empty pages.
    - Uses a thread pool for fetching pages, but inserts into DB single-threaded (at end).
    - For each unique review, calls analyze_sentiment() safely and inserts actual sentiment/topics.
    """
    if not asin:
        raise ValueError("ASIN required")

    print(f"[scraper] Starting: ASIN={asin} max_pages={max_pages} workers={max_workers} polite={polite}")

    # detect last page if not provided
    if max_pages is None:
        detected = detect_last_page(asin)
        if detected:
            max_pages = detected
            print(f"[scraper] Detected last page: {max_pages}")
        else:
            max_pages = MAX_PAGES_SAFE
            print(f"[scraper] Could not detect last page — will probe up to {max_pages} pages (stopping early on empty pages)")

    page_list = list(range(1, max_pages + 1))
    results_all: List[Dict] = []
    pages_processed = 0
    empty_page_count = 0

    # fetch pages (parallel)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_fetch_page_worker, asin, p, polite): p for p in page_list}
        for future in as_completed(futures):
            p = futures[future]
            try:
                page_reviews = future.result()
            except Exception as e:
                print(f"[scraper] Error fetching page {p}: {e}")
                page_reviews = []

            pages_processed += 1
            if not page_reviews:
                empty_page_count += 1
                print(f"[scraper] Page {p} returned 0 reviews (empty_count={empty_page_count})")
            else:
                empty_page_count = 0
                print(f"[scraper] Page {p} -> {len(page_reviews)} reviews")
                results_all.extend(page_reviews)

            if empty_page_count >= MAX_EMPTY_PAGES:
                print("[scraper] Stopping early due to consecutive empty pages.")
                break

    # dedupe collected reviews
    final = _unique_reviews(results_all)

    # -------------------------
    # Safe LLM wrapper (local)
    # -------------------------

    def _safe_analyze(text: str, retries: int = 2, pause: float = 1.2):
        """Call analyze_sentiment with retries and normalized return."""
        for attempt in range(1, retries + 1):
            try:
                out = safe_analyze_sentiment(text)
                # If dict, return normalized
                if isinstance(out, dict):
                    return {
                        "sentiment": out.get("sentiment", "Unknown"),
                        "topics": out.get("topics", []) or []
                    }
                # If string, try to extract JSON or do heuristic
                if isinstance(out, str):
                    import json, re
                    m = re.search(r"\{.*\}", out, re.DOTALL)
                    if m:
                        try:
                            parsed = json.loads(m.group())
                            return {"sentiment": parsed.get("sentiment", "Unknown"), "topics": parsed.get("topics", []) or []}
                        except Exception:
                            pass
                    low = out.lower()
                    if "positive" in low:
                        return {"sentiment": "Positive", "topics": []}
                    if "negative" in low:
                        return {"sentiment": "Negative", "topics": []}
                    if "neutral" in low:
                        return {"sentiment": "Neutral", "topics": []}
                    return {"sentiment": "Unknown", "topics": []}
                return {"sentiment": "Unknown", "topics": []}
            except Exception as e:
                print(f"[LLM] analyze_sentiment attempt {attempt} failed: {e}")
                if attempt < retries:
                    time.sleep(pause * attempt)
                else:
                    return {"sentiment": "Unknown", "topics": []}

    # -------------------------
    # single-threaded DB insert (with per-review sentiment)
    # -------------------------
    inserted = 0
    for i, r in enumerate(final, start=1):
        try:
            text = (r.get("text") or "").strip()
            rating = r.get("rating")
            date = r.get("date")

            # get sentiment & topics for this review safely
            si = _safe_analyze(text, retries=2, pause=1.2)
            # after receiving si from safe analyze
            sent_label = si.get("sentiment", "Neutral") or "Neutral"
            # normalize to canonical set
            sl = str(sent_label).strip().lower()
            if "pos" in sl:
                sent_label = "Positive"
            elif "neg" in sl:
                sent_label = "Negative"
            else:
                sent_label = "Neutral"

            topics_csv = ", ".join(si.get("topics", []) or [])

            insert_review({
                "platform": "Amazon",
                "asin": asin,
                "rating": rating,
                "date": date,
                "text": text,
                "sentiment": sent_label,
                "topics": topics_csv
            })
            inserted += 1

            # small polite pause to avoid hitting rate limits (tunable)
            time.sleep(0.35)

            if i % 10 == 0:
                print(f"[scraper] Processed & inserted {i} reviews...")

        except Exception as e:
            print(f"[scraper] DB insert / analyze error for review #{i}: {e}")

    print(f"[scraper] Finished. Collected {len(final)} unique reviews across ~{pages_processed} pages. Inserted {inserted} rows.")
    return final

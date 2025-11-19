# run_scraper.py
import sys
import json
import io

# Fix Windows stdout unicode if needed
try:
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

from scraper.amazon_scraper import extract_asin, scrape_reviews
from scraper.flipkart_scraper import scrape_flipkart
from analysis.sentiment_engine import analyze_sentiment
from database.db_handler import insert_review

def safe_parse(result):
    if isinstance(result, dict):
        return result
    if isinstance(result, str):
        try:
            return json.loads(result)
        except:
            return {"sentiment": "Unknown", "topics": []}
    return {"sentiment": "Unknown", "topics": []}

def main():
    if len(sys.argv) < 2:
        print("ERROR: Missing URL argument")
        sys.exit(2)

    url = sys.argv[1]
    max_pages = 3
    if len(sys.argv) >= 3:
        try:
            max_pages = int(sys.argv[2])
        except:
            max_pages = 3

    if "amazon" in url.lower():
        asin = extract_asin(url)
        reviews = scrape_reviews(asin, max_pages=max_pages)
        platform = "Amazon"

    elif "flipkart" in url.lower():
        asin = url.split("/")[-1][:10]
        reviews = scrape_flipkart(url, max_pages=max_pages)
        platform = "Flipkart"

    else:
        print("ERROR: Unsupported platform")
        sys.exit(1)

    for r in reviews:
        sentiment_raw = analyze_sentiment(r["text"])
        parsed = safe_parse(sentiment_raw)

        insert_review({
            "platform": platform,
            "asin": asin,
            "rating": r.get("rating"),
            "date": r.get("date"),
            "text": r.get("text"),
            "sentiment": parsed.get("sentiment", "Unknown"),
            "topics": ", ".join(parsed.get("topics", []))
        })

    print("OK")
    sys.exit(0)

if __name__ == "__main__":
    main()

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apscheduler.schedulers.background import BackgroundScheduler
from scraper.amazon_scraper import scrape_reviews
from scraper.flipkart_scraper import scrape_flipkart
from analysis.sentiment_engine import analyze_sentiment
from database.db_handler import get_watchlist, insert_review
import json, time

def daily_update_job():
    print("🔄 Running daily update job...")
    products = get_watchlist()
    for p in products:
        if p["platform"] == "Amazon":
            reviews = scrape_reviews(p["product_id"], max_pages=2)
        elif p["platform"] == "Flipkart":
            reviews = scrape_flipkart(p["product_url"])
        else:
            continue

        for r in reviews:
            result = analyze_sentiment(r["text"])
            parsed = json.loads(result)
            insert_review({
                "platform": p["platform"],
                "asin": p["product_id"],
                "rating": r["rating"],
                "date": r["date"],
                "text": r["text"],
                "sentiment": parsed.get("sentiment"),
                "topics": ", ".join(parsed.get("topics", []))
            })
        time.sleep(5)
    print("✅ Daily job complete.")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(daily_update_job, "cron", hour=2, minute=0)
    scheduler.start()

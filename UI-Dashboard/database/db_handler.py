import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.getcwd(), "reviews.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Reviews table
    c.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            asin TEXT,
            rating TEXT,
            date TEXT,
            text TEXT,
            sentiment TEXT,
            topics TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Watchlist table (FIXED)
    c.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            asin TEXT UNIQUE,          -- prevent duplicates
            product_name TEXT,
            product_url TEXT,
            last_updated TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized:", DB_PATH)


import sqlite3
import time

def insert_review(review, retries=3):
    for attempt in range(1, retries+1):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30)
            c = conn.cursor()
            c.execute("""
                INSERT INTO reviews (platform, asin, rating, date, text, sentiment, topics)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                review.get("platform"),
                review.get("asin"),
                review.get("rating"),
                review.get("date"),
                review.get("text"),
                review.get("sentiment", ""),
                review.get("topics", "")
            ))
            conn.commit()
            conn.close()
            return
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < retries:
                time.sleep(0.5 * attempt)
                continue
            print("DB insert error:", e)
            try:
                conn.close()
            except:
                pass
            break


def fetch_reviews(asin):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT rating, sentiment, topics, date, text
        FROM reviews
        WHERE asin = ?
        ORDER BY id DESC
    """, (asin,))
    rows = c.fetchall()
    conn.close()
    return rows


def add_to_watchlist(platform, asin, product_name, url):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        c.execute("""
            INSERT INTO watchlist (platform, asin, product_name, product_url, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(asin) DO UPDATE SET
                product_name = excluded.product_name,
                product_url = excluded.product_url,
                platform = excluded.platform,
                last_updated = excluded.last_updated
        """, (
            platform,
            asin,
            product_name,
            url,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))

        conn.commit()

    except Exception as e:
        print("❌ WATCHLIST INSERT ERROR:", e)

    finally:
        conn.close()


def get_watchlist():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT product_id, platform, asin, product_name, product_url, last_updated FROM watchlist")
    rows = c.fetchall()
    conn.close()

    columns = ["product_id", "platform", "asin", "product_name", "product_url", "last_updated"]
    return [dict(zip(columns, row)) for row in rows]


def remove_from_watchlist(product_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM watchlist WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()

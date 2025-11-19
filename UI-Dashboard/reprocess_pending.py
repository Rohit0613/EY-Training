# reprocess_pending.py
import sqlite3, time
from analysis.sentiment_engine import analyze_sentiment

DB="reviews.db"
conn=sqlite3.connect(DB)
cur=conn.cursor()

# select rows needing reprocessing (non-canonical labels)
cur.execute("SELECT id, text FROM reviews WHERE COALESCE(sentiment,'') NOT IN ('Positive','Negative','Neutral')")
rows=cur.fetchall()
print("Rows to reprocess:", len(rows))

for i,(rid, text) in enumerate(rows, start=1):
    try:
        out = analyze_sentiment(text or "")
        # robust normalisation
        s = (out.get("sentiment") if isinstance(out, dict) else None) or ""
        s = s.strip().lower()
        if "pos" in s:
            s = "Positive"
        elif "neg" in s:
            s = "Negative"
        else:
            s = "Neutral"
        topics = out.get("topics", []) if isinstance(out, dict) else []
        topics_csv = ", ".join(topics) if isinstance(topics, (list,tuple)) else str(topics)
        cur.execute("UPDATE reviews SET sentiment=?, topics=? WHERE id=?", (s, topics_csv, rid))
        if i % 10 == 0:
            conn.commit()
            print(f"Processed {i}/{len(rows)}")
        # polite pause
        time.sleep(0.3)
    except Exception as e:
        print("Error on id", rid, e)
        continue

conn.commit()
conn.close()
print("Done.")

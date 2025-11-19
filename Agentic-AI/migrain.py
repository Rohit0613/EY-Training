# migrate_add_columns.py
import sqlite3
from pathlib import Path

DB = "inventory.db"
if not Path(DB).exists():
    print("Database file not found:", DB)
    raise SystemExit(1)

con = sqlite3.connect(DB)
cur = con.cursor()

def has_column(table, col):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    return col in cols

to_add = []
if not has_column("items", "cost"):
    to_add.append(("cost", "NUMERIC"))
if not has_column("items", "min_margin"):
    # default 0.05
    to_add.append(("min_margin", "FLOAT DEFAULT 0.05"))
if not has_column("items", "floor_price"):
    to_add.append(("floor_price", "NUMERIC DEFAULT 0.0"))
if not has_column("items", "store_owner_whatsapp"):
    to_add.append(("store_owner_whatsapp", "TEXT"))

if not to_add:
    print("No missing columns detected in items table.")
else:
    print("Will add columns:", to_add)
    for col, coltype in to_add:
        sql = f"ALTER TABLE items ADD COLUMN {col} {coltype};"
        print("Executing:", sql)
        cur.execute(sql)
    con.commit()
    print("Columns added successfully.")

# Optionally ensure PriceChangeLog table exists (in case old DB lacks)
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='price_change_log';")
if not cur.fetchone():
    print("price_change_log table missing — creating minimal table.")
    cur.execute("""
    CREATE TABLE price_change_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        old_price NUMERIC,
        new_price NUMERIC,
        reason TEXT,
        agent_output TEXT,
        applied_by TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    con.commit()
    print("price_change_log created.")

con.close()
print("Migration script finished. Now re-run seed.py")

# seed_extended.py
"""
Seed DB with 7 suppliers, multiple items (rice, oil, wheat, bread, tomato), supplier messages with prices + ETA,
and some sales history. Replace whatsapp numbers with real/test numbers if you want to actually send messages.
"""
from decimal import Decimal
import datetime
from db import engine, SessionLocal
from MODELS import Base, Item, Supplier, SupplierMessage, SalesHistory, PriceChangeLog

# Ensure tables exist
Base.metadata.create_all(bind=engine)

SUPPLIERS = [
    {"name": "Suneeta Suppliers", "whatsapp": "+919307660352"},
    {"name": "Raj Wholesalers", "whatsapp": "+919307660352"},
    {"name": "Green Fields Co.", "whatsapp": "+919307660352"},
    {"name": "Harihar Traders", "whatsapp": "+919307660352"},
    {"name": "Metro Grocers Pvt Ltd", "whatsapp": "+919307660352"},
    {"name": "Asha Distributors", "whatsapp": "+919307660352"},
    {"name": "Bharat Fresh", "whatsapp": "+919307660352"},
]

# Items to insert (name, unit_price, stock, lead_time_days, cost)
ITEMS = [
    {"name": "Rice (1kg)", "unit_price": "42.00", "stock": 100, "lead_time_days": 2, "cost": "35.00"},
    {"name": "Oil (1L)",  "unit_price": "115.00", "stock": 50,  "lead_time_days": 1, "cost": "90.00"},
    {"name": "Wheat (1kg)", "unit_price": "38.00", "stock": 120, "lead_time_days": 2, "cost": "30.00"},
    {"name": "Bread (loaf)", "unit_price": "28.00", "stock": 40, "lead_time_days": 1, "cost": "18.00"},
    {"name": "Tomato (1kg)", "unit_price": "22.00", "stock": 80, "lead_time_days": 1, "cost": "15.00"},
]

# Example supplier message templates: each supplier will have messages about different items and prices + ETA
SUPPLIER_MESSAGES = {
    # supplier idx -> list of messages
    0: [
        "Rice wholesale price last month was ₹42 per kg. Delivery ETA: 2 days.",
        "Wheat available at ₹37 per kg. Delivery ETA: 3 days.",
        "Tomato fresh batch today — ₹21 per kg. Can deliver today."
    ],
    1: [
        "We have Rice at ₹43 per kg. Delivery in 1 day.",
        "Oil available at ₹115 per litre. Delivery ETA: tomorrow.",
        "Bread (fresh loaves) at ₹27 per loaf. Delivery ETA: 1 day."
    ],
    2: [
        "Wheat price ₹38 per kg. Fast delivery: 2 days.",
        "Tomato available at ₹22 per kg. Can deliver tomorrow.",
        "Rice bulk rate ₹41 per kg for orders > 100 kg. ETA: 2 days."
    ],
    3: [
        "Oil now stocked at ₹118 per litre. Delivery 1 day.",
        "Bread at ₹29 per loaf. Same-day delivery if ordered early.",
        "Tomato ₹20 per kg - limited stock, can deliver today."
    ],
    4: [
        "Rice ₹42 per kg. Delivery ETA 2 days.",
        "Wheat ₹39 per kg. Delivery 3 days.",
        "Oil ₹114 per litre. Delivery tomorrow."
    ],
    5: [
        "Bread discounted: ₹25 per loaf for repeat customers. Delivery 1 day.",
        "Tomato ₹23 per kg (next-day delivery).",
        "Rice available ₹44 per kg. ETA: 2 days."
    ],
    6: [
        "Wheat ₹36 per kg (best quality). Delivery in 2 days.",
        "Oil ₹116 per litre. Delivery 1 day.",
        "Tomato ₹22 per kg. Delivery: tomorrow."
    ],
}

def seed():
    db = SessionLocal()
    try:
        # If supplier table already has rows, do a safe skip-check for idempotency
        sup_count = db.query(Supplier).count()
        item_count = db.query(Item).count()
        if sup_count >= 7 and item_count >= len(ITEMS):
            print("DB already seeded with suppliers/items — skipping seed.")
            return

        # Insert suppliers
        suppliers = []
        for s in SUPPLIERS:
            sup = Supplier(name=s["name"], whatsapp_number=s["whatsapp"])
            suppliers.append(sup)
            db.add(sup)
        db.commit()

        # Insert items
        items_objs = []
        for it in ITEMS:
            item = Item(
                name=it["name"],
                unit_price=Decimal(it["unit_price"]),
                stock=it["stock"],
                lead_time_days=it["lead_time_days"],
                cost=Decimal(it["cost"]),
                min_margin=0.05,
                floor_price=(Decimal(it["cost"]) * Decimal("1.05"))
            )
            items_objs.append(item)
            db.add(item)
        db.commit()

        # Insert supplier messages: map supplier order to messages
        for sup_idx, msgs in SUPPLIER_MESSAGES.items():
            # supplier objects are in the order inserted
            sup_obj = db.query(Supplier).offset(sup_idx).limit(1).one()
            for m in msgs:
                sm = SupplierMessage(
                    supplier_id=sup_obj.supplier_id,
                    message_text=m,
                    created_at=datetime.datetime.utcnow()
                )
                db.add(sm)
        db.commit()

        # Add some sales history rows for forecasts
        now = datetime.datetime.utcnow()
        # Basic sales patterns
        for item in db.query(Item).all():
            # add 10 days of sales with random-ish small numbers
            for d in range(1, 11):
                sh = SalesHistory(
                    item_id=item.item_id,
                    sold_at=now - datetime.timedelta(days=d),
                    qty=(5 + (item.item_id + d) % 7)  # deterministic-ish numbers
                )
                db.add(sh)
        db.commit()
        print("✅ Seeded DB with suppliers, items, supplier messages, and sales history.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()

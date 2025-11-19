# create_and_seed.py
import os
from sqlalchemy import text
from db import engine  # your engine from db.py
from MODELS import Base, Item, Supplier, SupplierMessage  # adjust name if file differs
from sqlalchemy.orm import sessionmaker

DB_FILE = "inventory.db"

def reset_and_create_schema():
    # If DB file exists, remove it to ensure clean schema (dev only)
    if os.path.exists(DB_FILE):
        print("Removing existing DB file:", DB_FILE)
        os.remove(DB_FILE)
    # Ensure new DB file and schema created
    print("Creating database schema from models...")
    Base.metadata.create_all(bind=engine)
    print("Schema created.")

def seed():
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Clean any existing rows (should be empty after reset, but safe)
    print("Cleaning tables (if any)...")
    try:
        db.execute(text("DELETE FROM supplier_messages"))
        db.execute(text("DELETE FROM suppliers"))
        db.execute(text("DELETE FROM items"))
        db.commit()
    except Exception as e:
        # If tables don't exist (shouldn't happen after create_all), just continue
        print("Warning while cleaning tables (non-fatal):", e)
        db.rollback()

    print("Inserting items...")
    items = [
        Item(name="Rice", stock=8, lead_time_days=2, unit_price=42.0, store_owner_whatsapp="+917499591914"),
        Item(name="Wheat", stock=5, lead_time_days=1, unit_price=36.0, store_owner_whatsapp="+917499591914"),
        Item(name="Tomato", stock=12, lead_time_days=1, unit_price=28.0, store_owner_whatsapp="+917499591914"),
        Item(name="Bread", stock=4, lead_time_days=1, unit_price=22.0, store_owner_whatsapp="+917499591914"),
        Item(name="Oil", stock=9, lead_time_days=3, unit_price=110.0, store_owner_whatsapp="+917499591914"),
        Item(name="Sugar", stock=15, lead_time_days=2, unit_price=40.0, store_owner_whatsapp="+917499591914"),
        Item(name="Toor Dal", stock=10, lead_time_days=2, unit_price=96.0, store_owner_whatsapp="+917499591914"),
    ]
    db.add_all(items)
    db.commit()

    print("Inserting suppliers (7)...")
    OWNER_NUMBER = "+917499591914"
    suppliers = [
        Supplier(supplier_id=1, name="AgroFresh Traders", whatsapp_number=OWNER_NUMBER),
        Supplier(supplier_id=2, name="DailyMart Wholesale", whatsapp_number=OWNER_NUMBER),
        Supplier(supplier_id=3, name="Metro Agro LLP", whatsapp_number=OWNER_NUMBER),
        Supplier(supplier_id=4, name="Farm2Store Pvt Ltd", whatsapp_number=OWNER_NUMBER),
        Supplier(supplier_id=5, name="GrainHub Distributors", whatsapp_number=OWNER_NUMBER),
        Supplier(supplier_id=6, name="CityFresh Foods", whatsapp_number=OWNER_NUMBER),
        Supplier(supplier_id=7, name="Organic Valley Suppliers", whatsapp_number=OWNER_NUMBER),
    ]
    db.add_all(suppliers)
    db.commit()

    print("Inserting supplier messages...")
    messages = [
        SupplierMessage(supplier_id=1, message_text="Rice wholesale price is ₹42 per kg. Delivery ETA: 2 days."),
        SupplierMessage(supplier_id=2, message_text="Premium rice available at ₹45 per kg. Delivers tomorrow."),
        SupplierMessage(supplier_id=3, message_text="Raw rice ₹40/kg. Delivery 2–3 days."),
        SupplierMessage(supplier_id=4, message_text="Wheat price ₹28/kg. Can deliver today."),
        SupplierMessage(supplier_id=5, message_text="Wheat flour bulk at ₹30/kg. ETA 2 days."),
        SupplierMessage(supplier_id=6, message_text="Fresh bread ₹25 per pack. Delivery same day."),
        SupplierMessage(supplier_id=7, message_text="Brown bread ₹26 per pack. ETA 1 day."),
        SupplierMessage(supplier_id=1, message_text="Fresh tomatoes ₹32/kg. Delivery tomorrow."),
        SupplierMessage(supplier_id=3, message_text="Organic tomatoes ₹36/kg. ETA 1 day."),
        SupplierMessage(supplier_id=2, message_text="Sunflower oil ₹115 per litre. Can deliver tomorrow."),
        SupplierMessage(supplier_id=4, message_text="Sunflower oil ₹110/litre. ETA 2 days."),
        SupplierMessage(supplier_id=5, message_text="Sugar wholesale ₹40/kg. Delivery next day."),
    ]
    db.add_all(messages)
    db.commit()

    print("Seeding completed. Closing session.")
    db.close()

if __name__ == "__main__":
    reset_and_create_schema()
    seed()
    print("create_and_seed.py finished successfully.")

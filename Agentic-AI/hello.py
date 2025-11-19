# update_whatsapp_numbers.py
from sqlalchemy.orm import sessionmaker
from db import engine
from MODELS import Item, Supplier

SessionLocal = sessionmaker(bind=engine)

TARGET = "+917499591914"  # final normalized number to set

def run():
    db = SessionLocal()
    try:
        # Update items -> store_owner_whatsapp
        items = db.query(Item).all()
        for it in items:
            it.store_owner_whatsapp = TARGET

        # Update suppliers -> whatsapp_number
        suppliers = db.query(Supplier).all()
        for s in suppliers:
            s.whatsapp_number = TARGET

        db.commit()
        print(f"Updated {len(items)} items and {len(suppliers)} suppliers to {TARGET}")
    except Exception as e:
        db.rollback()
        print("Error updating numbers:", e)
    finally:
        db.close()

if __name__ == "__main__":
    run()

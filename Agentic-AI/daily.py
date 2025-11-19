from apscheduler.schedulers.background import BackgroundScheduler
from db import SessionLocal
from app import apply_pricing_helper
from MODELS import Item, SalesHistory

def run_daily_pricing():
    db = SessionLocal()
    items = db.query(Item).all()
    for it in items:
        # call apply_pricing logic programmatically (factor out into helper)
        apply_pricing_helper(it.item_id)

scheduler = BackgroundScheduler()
scheduler.add_job(run_daily_pricing, 'cron', hour=3)
scheduler.start()

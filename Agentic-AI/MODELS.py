# models.py
from db import Base
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, Numeric
from sqlalchemy.sql import func

# ---------- Orders (if you still need customer orders; keep for history) ----------
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    customer_phone = Column(String, nullable=False)
    customer_name = Column(String, nullable=True)
    item_id = Column(Integer, nullable=False)
    qty = Column(Integer, nullable=False)
    status = Column(String, default="placed")  # placed / confirmed / cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    provider_response = Column(Text, nullable=True)

# ---------- Inventory item ----------
class Item(Base):
    __tablename__ = "items"
    item_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    unit_price = Column(Numeric(10, 2), default=0.0)
    stock = Column(Integer, default=0)
    lead_time_days = Column(Integer, default=1)
    cost = Column(Numeric(10, 2), nullable=True)         # supplier cost if known
    min_margin = Column(Float, default=0.05)             # 5% default
    floor_price = Column(Numeric(10, 2), default=0.0)
    # default owner number requested earlier; can be overridden per-item in DB
    store_owner_whatsapp = Column(String, nullable=True, default="+917499591914")

# ---------- Pricing change log ----------
class PriceChangeLog(Base):
    __tablename__ = "price_change_log"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, index=True)
    old_price = Column(Numeric(10, 2))
    new_price = Column(Numeric(10, 2))
    reason = Column(Text)
    agent_output = Column(Text)
    applied_by = Column(String, nullable=True)  # 'agent' or username
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ---------- Suppliers & messages ----------
class Supplier(Base):
    __tablename__ = "suppliers"
    supplier_id = Column(Integer, primary_key=True)
    name = Column(String)
    whatsapp_number = Column(String)

class SupplierMessage(Base):
    __tablename__ = "supplier_messages"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer)
    message_text = Column(Text)
    created_at = Column(DateTime, default=func.now())

# ---------- Sales history ----------
class SalesHistory(Base):
    __tablename__ = "sales_history"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer)
    sold_at = Column(DateTime, default=func.now())
    qty = Column(Integer)

# ---------- Restock alert log (for monitor / audit) ----------
class RestockAlertLog(Base):
    __tablename__ = "restock_alert_log"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, index=True)
    supplier_id = Column(Integer, nullable=True)       # supplier we contacted
    alert_sent_at = Column(DateTime(timezone=True), server_default=func.now())
    qty = Column(Integer)  # current qty at alert time
    provider_sid = Column(String, nullable=True)  # Twilio message SID
    note = Column(Text, nullable=True)

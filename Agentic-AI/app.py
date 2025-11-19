# app.py
import os
import json
import time
import asyncio
from decimal import Decimal
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Body, Depends, Request, Response
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker

# DB + models (keep your actual file name; many of your snippets used MODELS)
from db import engine
from MODELS import (
    Item,
    SalesHistory,
    Supplier,
    SupplierMessage,
    RestockAlertLog,
    PriceChangeLog,
    Order,
)

# Keep the imports/assignments you insisted on exactly as-is
from auth_utils import create_access_token, get_current_user
from testing import STOCK_MONITOR_INTERVAL as j
from testing import DEFAULT_REORDER_THRESHOLD as k
from testing import ALERT_SUPPRESSION_SECONDS as l
from utils import recommend_supplier, score_supplier, parse_price, parse_eta
SessionLocal = sessionmaker(bind=engine)
STOCK_MONITOR_INTERVAL = j  # seconds
DEFAULT_REORDER_THRESHOLD = k
ALERT_SUPPRESSION_SECONDS = l

# LLM / RAG / WhatsApp helpers
from langchain_agents import (
    get_llm,
    make_retrieval_qa_chain,
    make_forecast_chain,
    make_pricing_chain,
    load_faiss,
    combine_docs,
)
from whatsapp import send_whatsapp, normalize_phone_number

# Twilio imports for webhook/sending (twilio client created conditionally)
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client as TwilioClient

# Try to import testing Twilio values (optional)
try:
    from testing import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, OWNER_USERNAME, OWNER_PASSWORD
except Exception:
    TWILIO_ACCOUNT_SID = None
    TWILIO_AUTH_TOKEN = None
    TWILIO_WHATSAPP_FROM = None
    OWNER_USERNAME = os.getenv("OWNER_USERNAME", "owner")
    OWNER_PASSWORD = os.getenv("OWNER_PASSWORD", "ownerpass")

# App init
app = FastAPI(title="Agentic Grocery — Owner Dashboard (LangChain)")

# LLM initialization
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
llm_rag = get_llm(model_name=LLM_MODEL, temperature=0.0)
llm_forecast = get_llm(model_name=LLM_MODEL, temperature=0.0)
llm_pricing = get_llm(model_name=LLM_MODEL, temperature=0.0)

forecast_chain = make_forecast_chain(llm_forecast)
pricing_chain = make_pricing_chain(llm_pricing)

# Twilio client (if creds provided)
tw_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        tw_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception as e:
        print("Twilio client init failed:", e)
        tw_client = None

# -----------------------
# Schemas
# -----------------------
class QueryIn(BaseModel):
    q: str
    k: int = 5


class ApplyPricingIn(BaseModel):
    item_id: int
    mode: str = "auto"
    force: bool = False


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

OWNER_USERNAME = "Rohit"
OWNER_PASSWORD = "Rohit123"

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(data: LoginRequest):
    if data.username == OWNER_USERNAME and data.password == OWNER_PASSWORD:
        return {"access_token": "demo-token"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
# -----------------------
# Helper: fetch supplier messages for an item name (simple DB search)
# -----------------------
def fetch_supplier_messages_for_item(db, item_name: str, k: int = 10):
    msgs = db.query(SupplierMessage).filter(SupplierMessage.message_text.ilike(f"%{item_name}%")).all()
    out = []
    for m in msgs:
        txt = (m.message_text or "").strip()
        price = parse_price(txt)
        eta = parse_eta(txt)
        out.append({"supplier_id": m.supplier_id, "excerpt": txt, "parsed_price": price, "parsed_eta": eta})
    return out


# -----------------------
# Stock monitor (background task)
# -----------------------
async def stock_monitor_loop():
    print("Stock monitor starting — will send restock orders to suppliers when needed.")
    while True:
        try:
            db = SessionLocal()
            items = db.query(Item).all()
            for it in items:
                cur_stock = int(it.stock or 0)
                reorder_thresh = getattr(it, "reorder_threshold", None) or DEFAULT_REORDER_THRESHOLD

                if cur_stock <= reorder_thresh:
                    # suppression check
                    recent = (
                        db.query(RestockAlertLog)
                        .filter(RestockAlertLog.item_id == it.item_id)
                        .order_by(RestockAlertLog.alert_sent_at.desc())
                        .first()
                    )
                    already_alerted = False
                    if recent and recent.alert_sent_at:
                        elapsed = time.time() - recent.alert_sent_at.timestamp()
                        if elapsed < ALERT_SUPPRESSION_SECONDS:
                            already_alerted = True

                    if already_alerted:
                        continue

                    # choose supplier candidates
                    cand_rows = fetch_supplier_messages_for_item(db, it.name, k=10)
                    if not cand_rows:
                        sups = db.query(Supplier).all()
                        cand_rows = [{"supplier_id": s.supplier_id, "excerpt": "", "parsed_price": None, "parsed_eta": None} for s in sups]

                    best = recommend_supplier(cand_rows) if cand_rows else None
                    chosen_supplier = None
                    if best:
                        chosen_supplier = db.query(Supplier).filter(Supplier.supplier_id == best["supplier_id"]).first()
                    else:
                        chosen_supplier = db.query(Supplier).first()

                    if not chosen_supplier:
                        print(f"No supplier found to order item {it.name} (id={it.item_id})")
                        log = RestockAlertLog(item_id=it.item_id, supplier_id=None, qty=cur_stock, note="no_supplier_found")
                        db.add(log)
                        db.commit()
                        continue

                    order_qty = it.reorder_qty if getattr(it, "reorder_qty", None) is not None else max(it.lead_time_days * 10, reorder_thresh * 3)
                    msg = (
                        f"Hello {chosen_supplier.name},\n"
                        f"This is an automated restock request for store item: {it.name}.\n"
                        f"Needed qty: {order_qty}\n"
                        f"Current stock: {cur_stock}\n"
                        f"Please confirm availability, price and ETA.\n"
                    )

                    try:
                        resp = send_whatsapp(chosen_supplier.whatsapp_number, msg)
                        provider_sid = resp.get("sid") if isinstance(resp, dict) else None
                        log = RestockAlertLog(item_id=it.item_id, supplier_id=chosen_supplier.supplier_id, qty=cur_stock, provider_sid=provider_sid, note=f"sent_to_supplier:{chosen_supplier.whatsapp_number}")
                        db.add(log)
                        db.commit()
                        print(f"Sent restock order for {it.name} to supplier {chosen_supplier.name} ({chosen_supplier.whatsapp_number}), sid={provider_sid}")
                    except Exception as e:
                        db.rollback()
                        print("Failed to send restock order:", e)
                        log = RestockAlertLog(item_id=it.item_id, supplier_id=chosen_supplier.supplier_id if chosen_supplier else None, qty=cur_stock, provider_sid=None, note=f"send_failed:{str(e)}")
                        db.add(log)
                        db.commit()

            db.close()
        except Exception as e:
            print("Stock monitor exception:", e)
        await asyncio.sleep(STOCK_MONITOR_INTERVAL)


@app.on_event("startup")
async def startup_event():
    # start background stock monitor
    asyncio.create_task(stock_monitor_loop())


@app.on_event("shutdown")
async def shutdown_event():
    print("App shutting down...")


# -----------------------
# Health
# -----------------------
@app.get("/health")
def health():
    return {"status": "OK", "llm_model": LLM_MODEL}


# -----------------------
# INVENTORY FORECAST
# -----------------------
@app.get("/inventory/check")
def inventory_check():
    db = SessionLocal()
    try:
        items = db.query(Item).all()
        results = []
        for item in items:
            history = (
                db.query(SalesHistory)
                .filter(SalesHistory.item_id == item.item_id)
                .order_by(SalesHistory.sold_at.desc())
                .limit(30)
                .all()
            )
            sales_ts = [h.qty for h in history][::-1]

            try:
                fc = forecast_chain.invoke(
                    {
                        "item_name": item.name,
                        "sales_history": sales_ts,
                        "stock": item.stock,
                        "lead_time": item.lead_time_days,
                    }
                )
            except Exception as e:
                fc = {"error": str(e)}

            results.append({"item": item.name, "stock": item.stock, "forecast": fc})

        return results
    finally:
        db.close()


# -----------------------
# Manual monitor trigger
# -----------------------
@app.post("/monitor/trigger")
def trigger_monitor_check():
    db = SessionLocal()
    try:
        items = db.query(Item).all()
        alerts = []
        for it in items:
            reorder_thresh = getattr(it, "reorder_threshold", None) or DEFAULT_REORDER_THRESHOLD
            cur_stock = int(it.stock or 0)
            if cur_stock <= reorder_thresh:
                owner_num = getattr(it, "store_owner_whatsapp", None)
                if owner_num:
                    try:
                        resp = send_whatsapp(owner_num, f"Manual Stock Alert — {it.name} current {cur_stock}, thresh {reorder_thresh}")
                        alerts.append({"item": it.name, "sent": True, "sid": resp.get("sid") if isinstance(resp, dict) else None})
                    except Exception as e:
                        alerts.append({"item": it.name, "error": str(e)})
        return {"alerts": alerts}
    finally:
        db.close()

# >>> Add /items (defensive) - put this once in your app.py
@app.get("/items")
def get_items_public():
    db = SessionLocal()
    try:
        items = db.query(Item).all()
        if not items:
            # return 404 to match your UI expectations; change to [] if you prefer
            raise HTTPException(status_code=404, detail="No items found. Seed the DB or call /items endpoint.")
        out = []
        for it in items:
            out.append({
                "item_id": it.item_id,
                "name": it.name,
                "unit_price": float(it.unit_price) if it.unit_price is not None else None,
                "stock": int(it.stock) if it.stock is not None else 0,
                "lead_time_days": int(it.lead_time_days) if it.lead_time_days is not None else None,
                "cost": float(it.cost) if it.cost is not None else None,
                "min_margin": float(it.min_margin) if it.min_margin is not None else None,
                "floor_price": float(it.floor_price) if it.floor_price is not None else None,
                "store_owner_whatsapp": it.store_owner_whatsapp,
            })
        return out
    finally:
        db.close()

# >>> New helper endpoint: returns supplier-excerpt rows for a given item name
@app.get("/supplier_prices")
def supplier_prices_for_item(item: str, k: int = 10):
    """
    Returns a list of supplier rows for `item` by scanning SupplierMessage records
    and mapping supplier names/numbers from suppliers table.
    """
    db = SessionLocal()
    try:
        # fetch messages containing the item name (case-insensitive)
        msgs = db.query(SupplierMessage).filter(SupplierMessage.message_text.ilike(f"%{item}%")).all()
        rows = []
        for m in msgs:
            sup = db.query(Supplier).filter(Supplier.supplier_id == m.supplier_id).first()
            excerpt = (m.message_text or "")[:400].replace("\n", " ")
            parsed_price = parse_price(excerpt) if 'parse_price' in globals() else None
            parsed_eta = parse_eta(excerpt) if 'parse_eta' in globals() else None
            rows.append({
                "supplier_id": m.supplier_id,
                "supplier_name": sup.name if sup else None,
                "whatsapp_number": sup.whatsapp_number if sup else None,
                "excerpt": excerpt,
                "parsed_price": parsed_price,
                "parsed_eta": parsed_eta,
                "message_id": m.id
            })
        # sort by parsed_price if present
        rows = sorted(rows, key=lambda r: (r["parsed_price"] is None, r["parsed_price"] or 1e12))
        return {"item": item, "rows": rows}
    finally:
        db.close()

# >>> New debug endpoint: recent stock changes + restock logs
@app.get("/stock_changes")
def stock_changes(item_id: int | None = None, limit: int = 50):
    db = SessionLocal()
    try:
        out = {"sales_history": [], "restock_alerts": []}
        qh = db.query(SalesHistory)
        if item_id:
            qh = qh.filter(SalesHistory.item_id == item_id)
        sales = qh.order_by(SalesHistory.sold_at.desc()).limit(limit).all()
        for s in sales:
            out["sales_history"].append({"item_id": s.item_id, "qty": s.qty, "sold_at": s.sold_at.isoformat() if s.sold_at else None})

        qr = db.query(RestockAlertLog)
        if item_id:
            qr = qr.filter(RestockAlertLog.item_id == item_id)
        alerts = qr.order_by(RestockAlertLog.alert_sent_at.desc()).limit(limit).all()
        for a in alerts:
            out["restock_alerts"].append({
                "item_id": a.item_id,
                "supplier_id": a.supplier_id,
                "qty_at_alert": a.qty,
                "provider_sid": a.provider_sid,
                "note": a.note,
                "alert_sent_at": a.alert_sent_at.isoformat() if a.alert_sent_at else None
            })
        return out
    finally:
        db.close()

# -----------------------
# PRICING ENGINE (preview)
# -----------------------
@app.post("/pricing/{item_id}")
def adjust_price(item_id: int):
    db = SessionLocal()
    try:
        item = db.query(Item).filter(Item.item_id == item_id).first()
        if not item:
            raise HTTPException(404, "Item not found.")

        history = (
            db.query(SalesHistory)
            .filter(SalesHistory.item_id == item_id)
            .order_by(SalesHistory.sold_at.desc())
            .limit(30)
            .all()
        )
        sales_ts = [h.qty for h in history][::-1]

        try:
            fc = forecast_chain.invoke(
                {
                    "item_name": item.name,
                    "sales_history": sales_ts,
                    "stock": item.stock,
                    "lead_time": item.lead_time_days,
                }
            )
            forecast_value = fc.get("forecast_3d") if isinstance(fc, dict) else None
        except Exception:
            forecast_value = None

        try:
            pc = pricing_chain.invoke(
                {
                    "item_name": item.name,
                    "current_price": float(item.unit_price) if item.unit_price is not None else 0.0,
                    "stock": item.stock,
                    "forecast": forecast_value,
                }
            )
        except Exception as e:
            pc = {"error": str(e)}

        return {"item": item.name, "forecast": fc, "pricing": pc}
    finally:
        db.close()


# -----------------------
# SUPPLIER QUERY — RAG
# -----------------------
@app.post("/supplier/query")
def supplier_query(body: QueryIn = Body(...)):
    q = body.q
    k = body.k

    try:
        qa = make_retrieval_qa_chain(llm_rag, persist_dir="langchain_faiss", k=k)
    except Exception as e:
        raise HTTPException(500, f"Error loading RAG chain: {e}")

    try:
        vs = load_faiss("langchain_faiss")
        if vs is None:
            raise RuntimeError("Vectorstore not found. Run ingest.py first.")
        docs = vs.similarity_search(q, k=k)
    except Exception as e:
        raise HTTPException(500, f"Error fetching docs from vectorstore: {e}")

    sources = []
    for i, d in enumerate(docs, start=1):
        excerpt = d.page_content[:240].replace("\n", " ")
        meta = d.metadata or {}
        supplier_name = meta.get("supplier_name") or meta.get("supplier_id")
        sources.append(
            {
                "tag": f"S{i}",
                "supplier_id": meta.get("supplier_id"),
                "supplier_name": supplier_name,
                "message_id": meta.get("message_id"),
                "excerpt": excerpt,
            }
        )

    try:
        answer = qa.invoke({"question": q})
        if isinstance(answer, (dict, list)):
            raw_llm = answer
            answer_text = json.dumps(answer)
        else:
            raw_llm = None
            answer_text = str(answer)
    except Exception as e:
        raise HTTPException(500, f"RAG execution failed: {e}")

    sources_line = None
    if "Sources:" in answer_text:
        parts = answer_text.split("Sources:", 1)
        answer_text = parts[0].strip()
        sources_line = parts[1].strip()

    response = {
        "answer": answer_text,
        "sources": sources,
        "sources_line": sources_line,
        "combined_context": combine_docs(docs) if len(docs) > 0 else "",
        "raw_llm": raw_llm,
    }

    return response


# -----------------------
# ORDER endpoint (owner places an order to supplier or recording a sale)
# -----------------------
@app.post("/order/{supplier_id}/{item_id}/{qty}")
def order_api(supplier_id: int, item_id: int, qty: int, customer_phone: Optional[str] = None, customer_name: Optional[str] = None):
    db = SessionLocal()
    try:
        supplier = db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
        item = db.query(Item).filter(Item.item_id == item_id).first()

        if not item:
            raise HTTPException(404, "Item not found.")

        if item.stock is None:
            item.stock = 0
        if item.stock < qty:
            raise HTTPException(400, f"Insufficient stock: {item.stock}")

        item.stock -= qty
        sh = SalesHistory(item_id=item_id, qty=qty)
        db.add(sh)
        db.commit()

        customer_resp = None
        if customer_phone:
            try:
                msg = f"Order recorded: {qty} x {item.name}. Remaining stock: {item.stock}."
                customer_resp = send_whatsapp(customer_phone, msg)
            except Exception as e:
                print("Owner/customer WH notify failed:", e)
                customer_resp = {"error": str(e)}

        return {"sent_to_customer": True, "customer_response": str(customer_resp)}
    finally:
        db.close()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from twilio.rest import Client
import re, requests
from testing import TWILIO_AUTH_TOKEN as c, TWILIO_ACCOUNT_SID as d, TWILIO_WHATSAPP_FROM as e

client = Client(d, c)
API_BASE = "http://127.0.0.1:8000"  # For internal calls if needed

@app.post("/webhook-endpoint")
async def webhook(request: Request):
    data = await request.form()
    incoming_msg = data.get("Body", "").strip().lower()
    sender = data.get("From")

    print(f"Incoming message: {incoming_msg} from {sender}")

    # Parse order
    match = re.search(r"(\d+)\s*(kg|g|ltr|l|pcs|pieces|units)?\s*(?:of\s*)?(.*)", incoming_msg)
    qty = int(match.group(1)) if match else 1
    item_name = match.group(3).strip() if match else incoming_msg

    # Lookup item
    try:
        items = requests.get(f"{API_BASE}/items").json()
        item_id = next((it["item_id"] for it in items if it["name"].lower() == item_name), None)
    except Exception:
        item_id = None

    if item_id:
        try:
            requests.post(f"{API_BASE}/order_to_supplier/{item_id}", json={"qty": qty})
            reply_text = f"✅ Order placed: {qty} units of {item_name}."
        except Exception as ex:
            reply_text = f"❌ Failed to place order: {ex}"
    else:
        reply_text = f"⚠ Item '{item_name}' not found in inventory."

    # Send reply via Twilio
    try:
        message = client.messages.create(
            body=reply_text,
            from_=e,  # Must be whatsapp:+14155238886
            to=sender
        )
        print(f"Reply sent successfully! SID: {message.sid}")
    except Exception as ex:
        print(f"Error sending reply: {ex}")

    return JSONResponse(content={"status": "processed", "reply": reply_text})


# -----------------------
# APPLY PRICING (owner-only)
# -----------------------
@app.post("/apply_pricing")
def apply_pricing(body: ApplyPricingIn, user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        item = db.query(Item).filter(Item.item_id == body.item_id).first()
        if not item:
            raise HTTPException(404, "Item not found")

        history = (
            db.query(SalesHistory)
            .filter(SalesHistory.item_id == item.item_id)
            .order_by(SalesHistory.sold_at.desc())
            .limit(30)
            .all()
        )
        sales_ts = [h.qty for h in history][::-1]

        try:
            fc = forecast_chain.invoke(
                {
                    "item_name": item.name,
                    "sales_history": sales_ts,
                    "stock": item.stock,
                    "lead_time": item.lead_time_days,
                }
            )
            forecast_3d = fc.get("forecast_3d") if isinstance(fc, dict) else None
        except Exception:
            forecast_3d = None

        try:
            pc = pricing_chain.invoke(
                {
                    "item_name": item.name,
                    "current_price": float(item.unit_price) if item.unit_price is not None else 0.0,
                    "stock": item.stock,
                    "forecast": forecast_3d,
                }
            )
        except Exception as e:
            raise HTTPException(500, f"Pricing chain failed: {e}")

        if isinstance(pc, str):
            try:
                pricing_json = json.loads(pc)
            except Exception:
                pricing_json = {"raw": pc}
        else:
            pricing_json = pc or {}

        new_price = pricing_json.get("new_price")
        apply_flag = pricing_json.get("apply", True)
        reason = pricing_json.get("reason", "") or pricing_json.get("explanation", "")
        promo = pricing_json.get("promo_text")

        if new_price is None:
            new_price = max(float(item.floor_price or 0.0), (float(item.cost or 0.0)) * (1 + float(item.min_margin or 0.05)))

        new_price = float(new_price)
        old_price = float(item.unit_price or 0.0)

        # validations
        min_margin = float(item.min_margin or 0.05)
        cost = float(item.cost) if item.cost is not None else None
        floor_price = float(item.floor_price or 0.0)

        failures = []
        if cost is not None and new_price < cost * (1 + min_margin):
            failures.append("violates_min_margin")
        if new_price < floor_price:
            failures.append("below_floor_price")
        max_delta_pct = 0.25
        if abs(new_price - old_price) / max(old_price, 1e-6) > max_delta_pct and not body.force:
            failures.append("change_too_large")

        if (not apply_flag) or (failures and not body.force):
            return {"applied": False, "validation_failures": failures, "pricing_json": pricing_json}

        try:
            log = PriceChangeLog(
                item_id=item.item_id,
                old_price=Decimal(str(old_price)),
                new_price=Decimal(str(new_price)),
                reason=reason,
                agent_output=json.dumps(pricing_json),
                applied_by=str(user) if user is not None else "agent",
            )
            db.add(log)
            item.unit_price = Decimal(str(new_price))
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(500, f"DB update failed: {e}")

        try:
            if item.store_owner_whatsapp:
                send_whatsapp(item.store_owner_whatsapp, f"Price updated for {item.name}: {old_price} -> {new_price}. Reason: {reason}")
                if promo:
                    send_whatsapp(item.store_owner_whatsapp, f"PROMO: {promo}")
        except Exception as e:
            print("Owner notify failed:", e)

        return {"applied": True, "item_id": item.item_id, "old_price": old_price, "new_price": new_price}
    finally:
        db.close()


# -----------------------
# Apply pricing helper & logs endpoints
# -----------------------
def apply_pricing_helper(item_id: int):
    db = SessionLocal()
    try:
        item = db.query(Item).filter(Item.item_id == item_id).first()
        if not item:
            return {"applied": False, "error": "Item not found"}

        history = (
            db.query(SalesHistory)
            .filter(SalesHistory.item_id == item.item_id)
            .order_by(SalesHistory.sold_at.desc())
            .limit(30)
            .all()
        )
        sales_ts = [h.qty for h in history][::-1]

        try:
            fc = forecast_chain.invoke(
                {
                    "item_name": item.name,
                    "sales_history": sales_ts,
                    "stock": item.stock,
                    "lead_time": item.lead_time_days,
                }
            )
        except Exception as e:
            return {"applied": False, "error": f"forecast failed: {e}"}

        forecast_value = fc.get("forecast_3d") if isinstance(fc, dict) else None

        try:
            pc = pricing_chain.invoke(
                {
                    "item_name": item.name,
                    "current_price": float(item.unit_price) if item.unit_price is not None else 0.0,
                    "stock": item.stock,
                    "forecast": forecast_value,
                }
            )
        except Exception as e:
            return {"applied": False, "error": f"pricing failed: {e}"}

        if isinstance(pc, str):
            try:
                pricing_json = json.loads(pc)
            except Exception:
                pricing_json = {"raw": pc}
        else:
            pricing_json = pc or {}

        new_price = pricing_json.get("new_price")
        if new_price is None:
            return {"applied": False, "error": "pricing agent returned no new_price"}

        new_price = float(new_price)
        old_price = float(item.unit_price or 0.0)

        item.unit_price = Decimal(str(new_price))
        db.commit()
        return {"applied": True, "old_price": old_price, "new_price": new_price}
    finally:
        db.close()


@app.post("/apply_pricing_all")
def apply_pricing_all():
    db = SessionLocal()
    try:
        items = db.query(Item).all()
        results = []
        for it in items:
            try:
                r = apply_pricing_helper(it.item_id)
                results.append({"item_id": it.item_id, "name": it.name, "result": r})
            except Exception as e:
                results.append({"item_id": it.item_id, "name": it.name, "error": str(e)})
        return {"results": results}
    finally:
        db.close()


@app.get("/pricing_logs")
def pricing_logs(limit: int = 50, user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        logs = db.query(PriceChangeLog).order_by(PriceChangeLog.created_at.desc()).limit(limit).all()
        out = []
        for l in logs:
            out.append(
                {
                    "id": l.id,
                    "item_id": l.item_id,
                    "old_price": float(l.old_price),
                    "new_price": float(l.new_price),
                    "reason": l.reason,
                    "applied_by": l.applied_by,
                    "created_at": l.created_at.isoformat(),
                }
            )
        return out
    finally:
        db.close()


@app.get("/suppliers")
def get_suppliers():
    db = SessionLocal()
    try:
        suppliers = db.query(Supplier).all()
        return [{"supplier_id": s.supplier_id, "name": s.name, "whatsapp_number": s.whatsapp_number} for s in suppliers]
    finally:
        db.close()


# -----------------------
# Twilio webhook (incoming WhatsApp messages)
# -----------------------
router = APIRouter()
import re
import difflib

QUANTITY_RE = re.compile(r"(?P<qty>\d+)\s*(?:kg|g|ltr|l|loaf|pcs|pieces|unit|units)?", re.I)


def parse_order_text(text: str):
    text = text.lower().strip()
    m = re.search(r"(\d+)\s*(kg|g|ltr|l|loaf|pcs|pieces|unit|units)?\s*(?:of\s*)?(.*)", text)
    if m:
        qty = int(m.group(1))
        rest = (m.group(3) or "").strip()
        if rest:
            return qty, rest
    m2 = re.search(r"([a-z\s]+)\s+(\d+)", text)
    if m2:
        name = m2.group(1).strip()
        qty = int(m2.group(2))
        return qty, name
    return 1, text


def find_item_by_name(db_session, text_name: str, cutoff=0.5):
    items = db_session.query(Item).all()
    for i in items:
        if text_name in i.name.lower():
            return i
    names = [i.name.lower() for i in items]
    candidates = difflib.get_close_matches(text_name, names, n=3, cutoff=cutoff)
    if candidates:
        matched_name = candidates[0]
        for i in items:
            if i.name.lower() == matched_name:
                return i
    return None

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from twilio.rest import Client
import os
import re
import requests
from testing import TWILIO_AUTH_TOKEN as c
from testing import TWILIO_ACCOUNT_SID as d
from testing import TWILIO_WHATSAPP_FROM as e


client = Client(d, c)
API_BASE = "http://127.0.0.1:8000"  # Your grocery backend API

@app.post("/webhook-endpoint")
async def webhook(request: Request):
    data = await request.form()
    incoming_msg = data.get("Body", "").strip().lower()
    sender = data.get("From")

    print(f"Incoming message: {incoming_msg} from {sender}")

    # Parse order command
    match = re.search(r"(\d+)\s*(kg|g|ltr|l|pcs|pieces|units)?\s*(?:of\s*)?(.*)", incoming_msg)
    if match:
        qty = int(match.group(1))
        item_name = match.group(3).strip()
    else:
        qty = 1
        item_name = incoming_msg

    # Lookup item in backend
    try:
        items = requests.get(f"{API_BASE}/items").json()
        item_id = next((it["item_id"] for it in items if it["name"].lower() == item_name), None)
    except Exception:
        item_id = None

    if item_id:
        try:
            res = requests.post(f"{API_BASE}/order_to_supplier/{item_id}", json={"qty": qty})
            reply_text = f"✅ Order placed: {qty} units of {item_name}."
        except Exception as ex:
            reply_text = f"❌ Failed to place order: {ex}"
    else:
        reply_text = f"⚠ Item '{item_name}' not found in inventory."

    # ✅ Always send reply via Twilio
    try:
        client.messages.create(
            body=reply_text,
            from_=e,
            to=sender
        )
        print("Reply sent successfully!")
    except Exception as ex:
        print(f"Error sending reply: {ex}")

    return JSONResponse(content={"status": "processed", "reply": reply_text})
# -----------------------
# Manual supplier order endpoint
# -----------------------
@app.post("/order_to_supplier/{item_id}")
def order_to_supplier(item_id: int, supplier_id: Optional[int] = None):
    db = SessionLocal()
    try:
        it = db.query(Item).filter(Item.item_id == item_id).first()
        if not it:
            raise HTTPException(404, "Item not found")

        if supplier_id:
            chosen = db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
        else:
            cand = fetch_supplier_messages_for_item(db, it.name)
            best = recommend_supplier(cand) if cand else None
            chosen = db.query(Supplier).filter(Supplier.supplier_id == (best["supplier_id"] if best else None)).first() or db.query(Supplier).first()

        if not chosen:
            raise HTTPException(404, "No supplier available")

        order_qty = max(it.lead_time_days * 10, DEFAULT_REORDER_THRESHOLD * 3)
        msg = f"Order request: {it.name}\nQty: {order_qty}\nCurrent stock: {it.stock}\nPlease confirm price & ETA."
        resp = send_whatsapp(chosen.whatsapp_number, msg)
        provider_sid = resp.get("sid") if isinstance(resp, dict) else None
        log = RestockAlertLog(item_id=it.item_id, supplier_id=chosen.supplier_id, qty=it.stock or 0, provider_sid=provider_sid, note="manual_order")
        db.add(log)
        db.commit()
        return {"sent": True, "supplier": chosen.name, "provider_sid": provider_sid}
    finally:
        db.close()

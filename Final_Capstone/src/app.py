import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
from agents.inventory_agent import InventoryAgent
from agents.pricing_agent import PricingAgent
from agents.supplier_hub import SupplierHub


app = FastAPI(title="Agentic Grocery OS")


inventory_agent = InventoryAgent(data_path="data/inventory.csv", orders_path="data/orders.csv")
pricing_agent = PricingAgent(data_path="data/inventory.csv")
supplier_hub = SupplierHub(purchases_path="data/purchases.csv")


class OrderRequest(BaseModel):
    days_ahead: int = 3


class ConfirmOrderRequest(BaseModel):
    orders: List[Dict[str, Any]]
    store_name: str = "My Store"


@app.get('/health')
async def health():
    return {'status': 'ok'}


@app.post('/order/preview')
async def preview_order(req: OrderRequest):
    """Preview order without sending to WhatsApp"""
    try:
        result = inventory_agent.preview_order(days_ahead=req.days_ahead)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/order/confirm')
async def confirm_order(req: ConfirmOrderRequest):
    """Send confirmed order via WhatsApp"""
    try:
        result = inventory_agent.send_confirmed_order(
            orders=req.orders,
            store_name=req.store_name
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/order/history')
async def get_order_history(limit: int = 50):
    """Get order history"""
    try:
        history = inventory_agent.get_order_history(limit=limit)
        return {'orders': history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/order/auto')
async def auto_order(req: OrderRequest):
    """Legacy endpoint - generates and sends order immediately"""
    try:
        message, order_list = inventory_agent.create_and_send_order(days_ahead=req.days_ahead)
        return {'message': message, 'order': order_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/pricing/adjust')
async def adjust_pricing():
    try:
        changes = pricing_agent.run_pricing_rules()
        return {'changes': changes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class QueryRequest(BaseModel):
    query: str


@app.post('/supplier/query')
async def supplier_query(req: QueryRequest):
    try:
        answer = supplier_hub.answer(req.query)
        return {'answer': answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    uvicorn.run('src.app:app', host='0.0.0.0', port=8000, reload=True)
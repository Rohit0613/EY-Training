import requests, os
from rag_store import RAGStore
from testing import OPENROUTER_API_KEY as a

store = RAGStore()

OPENROUTER_API_KEY = a
URL = "https://openrouter.ai/api/v1/chat/completions"
headers = {"Authorization": f"Bearer {a}"}

def llm(prompt):
    res = requests.post(URL, json={
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }, headers=headers)
    return res.json()["choices"][0]["message"]["content"]

def forecast(ts, stock, lead, name):
    prompt = f"""
    Sales history: {ts}
    Stock: {stock}
    Lead time: {lead}
    Give demand forecast and reorder qty for {name}. JSON only:
    {{ "forecast": num, "order_qty": num }}
    """
    return llm(prompt)

def pricing(item, price, stock, forecast):
    prompt = f"""
    Item: {item}, Current Price: {price}, Stock: {stock}, Forecast: {forecast}
    Give optimal new price and WhatsApp promo text.
    JSON:
    {{"new_price": num, "promo": "text"}}
    """
    return llm(prompt)

def supplier_chat(query):
    docs = store.search(query, k=5)
    ctx = "\n".join([d["text"] for d in docs])
    prompt = f"Context:\n{ctx}\n\nQuestion: {query}\nAnswer shortly."
    return llm(prompt)

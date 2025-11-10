import time
import json
import requests
import logging
from typing import Generator
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from testing import OPENROUTER_API_KEY as a
from testing import OPENROUTER_BASE_URL as b

# -----------------------------
# ⚙️ Config
# -----------------------------
OPENROUTER_API_KEY = a
OPENROUTER_BASE_URL = b
MODEL = "mistralai/mistral-7b-instruct"
REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 2

if not OPENROUTER_API_KEY:
    raise RuntimeError("❌ OPENROUTER_API_KEY not set in testing.py")

# -----------------------------
# 🚀 FastAPI App
# -----------------------------
app = FastAPI(title="🤖 Smart LLM Backend with Middleware & Logging")

# -----------------------------
# 🪵 Logging Setup
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# -----------------------------
# ⚙️ Middleware: Logging + Error Handling + Timing
# -----------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"➡️ {request.method} {request.url.path}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception(f"🔥 Internal error: {e}")
        return JSONResponse(
            {"error": "Internal Server Error", "details": str(e)}, status_code=500
        )

    duration = time.time() - start_time
    logger.info(f"✅ {request.method} {request.url.path} completed in {duration:.2f}s")
    return response

import re
from datetime import date

def handle_local_tasks(prompt: str) -> str | None:
    """Detect simple deterministic tasks and solve them locally."""
    p = prompt.lower().strip()

    # Math detection
    math_match = re.match(r"^(?:add|sum|what is|calculate)?\s*([\d\s\+\-\*/\(\)]+)$", p)
    if math_match:
        try:
            expr = math_match.group(1)
            result = eval(expr)
            return str(result)
        except Exception:
            pass

    # Reverse detection
    if "reverse" in p:
        # Extract word after 'reverse'
        words = p.split()
        if len(words) >= 2:
            target = words[-1]
            return target[::-1]

    # Date detection
    if "date" in p:
        return f"Today's date is {date.today()}"

    return None

# -----------------------------
# 🔁 Helper: Stream Mistral Response (LLM Streaming)
# -----------------------------
def stream_openrouter_response(prompt: str) -> Generator[str, None, None]:
    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an intelligent assistant capable of performing small math calculations, "
                    "reversing words, telling today's date, and answering general questions clearly. "
                    "If a query involves numbers, calculate it correctly. If it's text, respond naturally."
                ),
            },
            {"role": "user", "content": prompt},
        ],"temperature":0.3,
        "stream": True,
    }

    try:
        with requests.post(url, headers=headers, json=payload, stream=True, timeout=REQUEST_TIMEOUT) as r:
            if r.status_code != 200:
                logger.error(f"❌ OpenRouter Error: {r.status_code} - {r.text}")
                yield f"[Error {r.status_code}] {r.text}"
                return

            for line in r.iter_lines():
                if not line:
                    continue
                if line.startswith(b"data: "):
                    data_str = line[len(b"data: "):].decode("utf-8").strip()
                    if data_str == "[DONE]":
                        break  # ✅ End of stream
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except Exception as e:
                        logger.warning(f"⚠️ Skipping line: {data_str} ({e})")
                        continue
    except Exception as e:
        logger.exception(f"💥 Streaming failed: {e}")
        yield f"[Streaming Error] {str(e)}"

# -----------------------------
# 🚀 Endpoint: /query
# -----------------------------
@app.post("/query")
async def query(request: Request):
    try:
        body = await request.json()
        user_query = body.get("query")

        if not user_query:
            return JSONResponse({"error": "Missing 'query' field"}, status_code=400)

        # ✅ Local pre-processing for deterministic tasks
        local_result = handle_local_tasks(user_query)
        if local_result:
            logger.info("🧮 Handled locally (no LLM call).")
            return JSONResponse({"response": local_result})

        # Otherwise use the LLM for reasoning
        def event_stream():
            for chunk in stream_openrouter_response(user_query):
                yield chunk.encode("utf-8")

        return StreamingResponse(event_stream(), media_type="text/plain; charset=utf-8")

    except Exception as e:
        logger.exception(f"❗ Error in /query route: {e}")
        return JSONResponse({"error": "Internal Server Error", "details": str(e)}, status_code=500)

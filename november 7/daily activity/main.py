# main.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from langchain.messages import SystemMessage
from langchain_core.messages import HumanMessage

import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

llm = ChatOpenAI(
    model="meta-llama/llama-3-8b-instruct",
    temperature=0.4,
    max_tokens=512,
    api_key=api_key,
    base_url=base_url,
)

HISTORY_FILE = "QA_history.json"

def save_to_history(user_query: str, llm_response: str):
    data = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
    data.append({"user_query": user_query, "llm_response": llm_response})
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    # Show empty form on homepage
    return templates.TemplateResponse("index.html", {"request": request, "query": "", "result": ""})

@app.post("/ask", response_class=HTMLResponse)
async def ask_ai(request: Request, query: str = Form(...)):
    result = None
    try:
        response = llm.invoke(
            [
                SystemMessage(content="You are a helpful assistant."),
                HumanMessage(content=query),
            ]
        )
        save_to_history(query, response.content)
        result = response.content
    except Exception as e:
        result = f"Error: {str(e)}"

    return templates.TemplateResponse("index.html", {"request": request, "query": query, "result": result})


import os
import requests
import json
from typing import Optional, List, Mapping, Any

from testing import OPENROUTER_API_KEY as a

from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.runnables import RunnableParallel, RunnableLambda
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models.llms import LLM

OPENROUTER_API_KEY = a
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ---------- OpenRouter LLM wrapper for LangChain ----------
class OpenRouterLLM(LLM):
    """
    Minimal LangChain LLM wrapper that calls OpenRouter chat completions.
    Accepts dict prompts (converts to string) to be robust with Runnable pipelines.
    """

    model: str = "openai/gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 512

    def _call(self, prompt, stop: Optional[List[str]] = None) -> str:
        # Normalize prompt to string (LangChain may pass dicts/other types)
        if isinstance(prompt, dict):
            prompt = json.dumps(prompt, indent=2)
        if not isinstance(prompt, str):
            prompt = str(prompt)

        headers = {"Authorization": f"Bearer {a}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": float(self.temperature),
            "max_tokens": int(self.max_tokens),
        }
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"OpenRouter LLM call failed ({r.status_code}): {r.text}")
        data = r.json()
        if "choices" not in data or len(data["choices"]) == 0:
            raise RuntimeError(f"OpenRouter returned unexpected payload: {data}")
        # safe access
        return data["choices"][0]["message"]["content"]

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        # LangChain expects an attribute (mapping), not a method
        return {"model": self.model, "temperature": self.temperature, "max_tokens": self.max_tokens}

    @property
    def _llm_type(self) -> str:
        return "openrouter"


# ---------- Embeddings + Vectorstore setup ----------
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VSTORE_DIR = "langchain_faiss"


def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


# top-level helper: used by other modules too
def combine_docs(docs: List[Document]) -> str:
    texts: List[str] = []
    for d in docs:
        if not hasattr(d, "page_content"):
            raise RuntimeError(f"Invalid doc object passed to combine_docs: {type(d)}")
        texts.append(d.page_content)
    return "\n\n".join(texts)


def init_faiss_from_documents(documents: List[Document], persist_dir: str = VSTORE_DIR):
    embeddings = get_embeddings()
    vs = FAISS.from_documents(documents, embeddings)
    vs.save_local(persist_dir)
    return vs


def load_faiss(persist_dir: str = VSTORE_DIR):
    embeddings = get_embeddings()
    if not os.path.exists(persist_dir):
        return None
    return FAISS.load_local(persist_dir, embeddings, allow_dangerous_deserialization=True)


# small debug helper (safe)
def debug_inputs(inp):
    try:
        print("\n[DEBUG BEFORE PROMPT]")
        print("[DEBUG] inp type:", type(inp))
        if isinstance(inp, dict):
            print("[DEBUG] inp keys:", inp.keys())
            print("[DEBUG] context type:", type(inp.get("context")))
            print("[DEBUG] context value:", (inp.get("context")[:200] + "...") if isinstance(inp.get("context"), str) else inp.get("context"))
            print("[DEBUG] question type:", type(inp.get("question")))
            print("[DEBUG] question:", inp.get("question"))
    except Exception as e:
        print("Debug helper error:", e)
    return inp


def make_retrieval_qa_chain(llm, persist_dir: str = VSTORE_DIR, k: int = 5):
    """
    Build a Runnable-based RAG pipeline that:
      1) uses FAISS similarity_search directly (stable)
      2) combines docs into context string
      3) prompts LLM and parses string output
    """
    vs = load_faiss(persist_dir)
    if vs is None:
        raise RuntimeError("Vectorstore missing. Run ingest.py first.")

    def fetch_docs(inp):
        question = inp["question"]
        print("\n[DEBUG] fetch_docs got question:", question)
        docs = vs.similarity_search(question, k=k)
        print("[DEBUG] type returned by FAISS:", type(docs))
        # Validate
        if not isinstance(docs, list):
            raise RuntimeError(f"FAISS returned non-list object: {docs}")
        return docs

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""
You are a supplier-analytics assistant. Use the supplier context to answer concisely.
Cite only the chunks you used with tags like [S1], [S2] which correspond to the top retrieved documents.

Context:
{context}

Question: {question}

Answer briefly (1–2 sentences). At the end include a "Sources:" line listing the tags and the supplier ids, e.g.:
Sources: [S1] supplier_id=1, [S2] supplier_id=2
""",
    )

    parser = StrOutputParser()

    rag_chain = (
        RunnableParallel(
            {
                "question": RunnableLambda(lambda x: x["question"]),
                "context": RunnableLambda(fetch_docs) | RunnableLambda(combine_docs),
            }
        )
        | RunnableLambda(debug_inputs)
        | prompt
        | llm
        | parser
    )

    return rag_chain


# ---------- Forecasting / Pricing LLMChains ----------
def make_forecast_chain(llm):
    prompt = PromptTemplate(
        input_variables=["item_name", "sales_history", "stock", "lead_time"],
        template=(
            "You are an inventory forecasting assistant.\n"
            "Return a JSON with fields forecast_3d and recommended_order.\n\n"
            "Item: {item_name}\nSales: {sales_history}\nStock: {stock}\nLead: {lead_time}"
        ),
    )

    parser = JsonOutputParser()
    chain = prompt | llm | parser
    return chain


def make_pricing_chain(llm):
    prompt = PromptTemplate(
        input_variables=["item_name", "current_price", "stock", "forecast"],
        template=(
            "You are a pricing strategist.\n"
            "Return JSON with keys: new_price (number), apply (bool), reason (string), promo_text (string).\n\n"
            "Item: {item_name}\nCurrent price: {current_price}\nStock: {stock}\nForecast: {forecast}"
        ),
    )

    parser = JsonOutputParser()
    chain = prompt | llm | parser
    return chain


# ---------- Utility: create Document chunks from raw text ----------
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    out: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        chunk = text[i : i + chunk_size]
        out.append(chunk)
        i += chunk_size - overlap
    return out


# ---------- Public convenience functions ----------
def get_llm(model_name: str = "openai/gpt-4o-mini", temperature: float = 0.0, max_tokens: int = 512):
    llm = OpenRouterLLM()
    llm.model = model_name
    llm.temperature = temperature
    llm.max_tokens = max_tokens
    return llm

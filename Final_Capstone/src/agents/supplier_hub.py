import os
import pandas as pd
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
from litellm import max_tokens

# Load environment variables from .env file
load_dotenv()


class SupplierHub:
    def __init__(self, purchases_path='data/purchases.csv'):
        self.purchases_path = purchases_path
        self._build_index()

    def _build_index(self):
        df = pd.read_csv(self.purchases_path)
        docs = []
        for _, r in df.iterrows():
            txt = f"Date: {r['date']} | Supplier: {r['supplier']} | Item: {r['item']} | Qty: {r['qty']} | Price: {r['price']}"
            docs.append(
                Document(page_content=txt, metadata={"supplier": r['supplier'], 'item': r['item'], 'date': r['date']}))
        if docs:
            emb = SentenceTransformerEmbeddings(model_name='all-MiniLM-L6-v2')
            self.vs = FAISS.from_documents(docs, emb)
        else:
            self.vs = None

    def answer(self, query_text: str):
        if not self.vs:
            return 'No purchase history available.'
        retriever = self.vs.as_retriever(search_kwargs={'k': 5})

        # Configure OpenRouter
        llm = ChatOpenAI(
            model="anthropic/claude-3.5-sonnet",  # or any OpenRouter model
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0,
            max_tokens=1500
        )

        chain = ConversationalRetrievalChain.from_llm(llm, retriever)
        # one-shot (no memory) run
        result = chain({"question": query_text, "chat_history": []})
        return result['answer']
# ingest.py
import os
from sqlalchemy.orm import sessionmaker
from db import engine
from MODELS import SupplierMessage

from langchain_agents import chunk_text, init_faiss_from_documents
from langchain_core.documents import Document

SessionLocal = sessionmaker(bind=engine)

def build_documents_from_db():
    db = SessionLocal()
    messages = db.query(SupplierMessage).all()
    docs = []

    for msg in messages:
        # Build base text for embedding
        base_text = f"[supplier_id:{msg.supplier_id}] {msg.message_text}"

        # Chunk it for FAISS
        chunks = chunk_text(base_text, chunk_size=500, overlap=50)

        for c in chunks:
            docs.append(
                Document(
                    page_content=c,
                    metadata={
                        "supplier_id": msg.supplier_id,
                        "message_id": msg.id,
                    }
                )
            )

    db.close()
    return docs


def run_ingest(persist_dir="langchain_faiss"):
    docs = build_documents_from_db()
    if not docs:
        print("⚠️ No supplier messages in DB — nothing to ingest.")
        return

    init_faiss_from_documents(docs, persist_dir)
    print(f"✅ Ingested {len(docs)} chunks into FAISS → {persist_dir}")


if __name__ == "__main__":
    run_ingest()

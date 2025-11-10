from openai import OpenAI
import numpy as np
import faiss
import json
import os
from testing import OPENROUTER_API_KEY

a = OPENROUTER_API_KEY
client = OpenAI(api_key=f"{a}", base_url="https://openrouter.ai/api/v1")

# File paths
DATA_FILE = os.path.join(os.path.dirname(__file__), "ipc_sections.json")
CRPC_FILE = os.path.join(os.path.dirname(__file__), "crpc_sections.json")
INDEX_FILE = os.path.join(os.path.dirname(__file__), "ipc_index.faiss")
META_FILE = os.path.join(os.path.dirname(__file__), "ipc_data.json")

def load_json(file_path):

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_index():

    print("📘 Loading IPC and CrPC datasets...")

    ipc_data = load_json(DATA_FILE)
    crpc_data = load_json(CRPC_FILE)

    # Process IPC data
    ipc_texts = [f"{d['section']} - {d['Offense']}: {d['description']}" for d in ipc_data]

    # Process CrPC data (normalize field names)
    crpc_texts = [f"{d['Section']} - {d.get('Section_name', d.get('Section _name', ''))}: {d['Description']}" for d in crpc_data]

    texts = ipc_texts + crpc_texts
    embeddings = []
    total = len(texts)
    print(f"🔢 Total records to embed: {total}")

    # Generate embeddings
    for i, text in enumerate(texts, start=1):
        try:
            emb_resp = client.embeddings.create(model="text-embedding-3-small", input=text)
            embeddings.append(np.array(emb_resp.data[0].embedding, dtype="float32"))

            if i % 10 == 0 or i == total:
                print(f"✅ Embedded {i}/{total}")
        except Exception as e:
            print(f"⚠️ Error embedding record {i}: {e}")
            continue

    if not embeddings:
        raise RuntimeError("No embeddings were created. Check API key or input data.")

    # Create FAISS index with ID mapping
    dim = embeddings[0].shape[0]
    index = faiss.IndexFlatL2(dim)           # L2 distance
    index = faiss.IndexIDMap(index)          # Map embeddings to IDs

    emb_arr = np.vstack(embeddings).astype("float32")
    ids = np.arange(len(emb_arr)).astype("int64")
    index.add_with_ids(emb_arr, ids)

    # Save index and metadata
    faiss.write_index(index, INDEX_FILE)
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(ipc_data + crpc_data, f, ensure_ascii=False, indent=2)

    print("\n✅ FAISS index and metadata saved successfully!")

def load_index():
    """Load FAISS index and metadata."""
    if not os.path.exists(INDEX_FILE) or not os.path.exists(META_FILE):
        raise FileNotFoundError("Index or metadata files are missing.")
    index = faiss.read_index(INDEX_FILE)
    with open(META_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return index, data

if __name__ == "__main__":
    try:
        build_index()
    except Exception as e:
        print(f"❌ Error building index: {e}")
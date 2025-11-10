import numpy as np
from openai import OpenAI
import asyncio
from testing import OPENROUTER_API_KEY
a= OPENROUTER_API_KEY


client = OpenAI(api_key=f"{a}", base_url="https://openrouter.ai/api/v1")


def retrieve(query, index, data, k=3):
    emb = client.embeddings.create(model="text-embedding-3-small", input=query)
    query_vec = np.array(emb.data[0].embedding, dtype="float32").reshape(1, -1)
    distances, indices = index.search(query_vec, k)
    return [data[i] for i in indices[0]]

def explain_law(query, retrieved):
    context_lines = []

    for r in retrieved:
        # IPC format
        if "Offense" in r:
            context_lines.append(
                f"{r.get('section')} - {r.get('Offense')}: {r.get('description')} "
                f"(Punishment: {r.get('punishment', 'N/A')})"
            )
        # CrPC format (handle both field variations)
        crpc_name = r.get("Section_name") or r.get("Section _name")
        if crpc_name:
            context_lines.append(
                f"Section {r.get('Section')} - {crpc_name}: {r.get('Description')}"
            )

    context = "\n".join(context_lines) if context_lines else "No relevant legal sections found."

    prompt = f"""
A user described: "{query}".
Based on the following Indian legal sections (IPC & CrPC), explain which ones are relevant and summarize punishments or procedures clearly.

{context}
"""

    resp = client.chat.completions.create(
        model="mistralai/mistral-7b-instruct",
        messages=[{"role": "user", "content": prompt}])

    # Access content safely (adjust if your SDK version needs it)
    return resp.choices[0].message.content.strip()

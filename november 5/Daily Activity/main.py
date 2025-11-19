import spacy
from fastapi import FastAPI, Query
from embeddings import load_index
from rag_engine import retrieve, explain_law
import gradio as gr
from fastapi.middleware.cors import CORSMiddleware
from gradio.routes import mount_gradio_app
import asyncio
# -----------------------------
# ⚙️ Load Models and Index
# -----------------------------
nlp = spacy.load("en_core_web_sm")
index, data = load_index()

# -----------------------------
# 🚀 FastAPI Setup
# -----------------------------
app = FastAPI(title="AI Legal Advisor (Indian Law)")

# Allow frontend requests (if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# 🧠 NLP-based Query Handling
# -----------------------------
def extract_crime_entities(query):
    """Extract entities using spaCy (future extensibility)."""
    doc = nlp(query)
    return [ent.text for ent in doc.ents]


def normalize_query(query):
    """Normalize user terms for better matching."""
    crime_mappings = {
        "stealing": "theft",
        "online fraud": "cybercrime",
        "hacking": "cybercrime",
        "causing hurt": "ipc 323",
        "assault": "ipc 351",
        "murder": "ipc 302",
    }
    for phrase, mapped in crime_mappings.items():
        if phrase in query.lower():
            return mapped
    return query


# -----------------------------
# FastAPI Endpoints
# -----------------------------
@app.get("/")
def home():
    return {"message": "Welcome to the AI Legal Advisor for Indian Laws!"}

@app.get("/query")
async def get_law_info(query: str = Query(..., description="Describe the crime or act")):
    normalized = normalize_query(query)
    crimes = extract_crime_entities(normalized) or [normalized]

    # Define async helper inside the route
    async def process_crime(crime):
        retrieved = await retrieve(crime, index, data)
        explanation = await explain_law(crime, retrieved)
        return {"crime": crime, "explanation": explanation}

    # Create and gather tasks concurrently
    tasks = [asyncio.create_task(process_crime(c)) for c in crimes]
    results = await asyncio.gather(*tasks)

    return {
        "query": query,
        "normalized_query": normalized,
        "results": results
    }


# -----------------------------
# 💻 Gradio UI
# -----------------------------
def gradio_interface(query):
    response = get_law_info(query)
    results = response["results"]

    display_text = f"### ⚖️ Query: {response['query']}\n"
    display_text += f"**Normalized Query:** {response['normalized_query']}\n\n"

    for res in results:
        display_text += f"#### 🧩 Crime: {res['crime']}\n"
        display_text += f"{res['explanation']}\n\n---\n"

    return display_text
with gr.Blocks(
    theme=gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="slate",
        neutral_hue="gray",
        font=["Inter", "sans-serif"],
    ),
    css="""
        body { display: flex; justify-content: center; }
        #main-container { max-width: 800px; width: 100%; margin-top: 30px; }
        #chatbox {height: 450px; overflow-y: auto; border: 1px solid #ddd; padding: 12px; border-radius: 12px;}
        .law-card {background-color: #f8fafc; padding: 14px; border-radius: 12px; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);}
        .crime-title {font-weight: 600; color: #1e293b; font-size: 1.05rem;}
        .response-text {color: #334155; line-height: 1.5;}
        .copy-btn {background-color: #e2e8f0; border: none; padding: 4px 8px; border-radius: 8px; cursor: pointer; float: right;}
        .copy-btn:hover {background-color: #cbd5e1;}
    """,
) as iface:

    with gr.Column(elem_id="main-container"):
        gr.Markdown(
            """
            <div style="text-align: center;">
                <h1>⚖️ <b>AI Legal Advisor</b></h1>
                <p style="color: gray;">Ask about any Indian law section.</p>
            </div>
            """
        )

        # Input on top
        with gr.Row():
            query_box = gr.Textbox(
                placeholder="e.g., What is the punishment for theft under IPC?",
                show_label=False,
            )
            submit_btn = gr.Button("🔍 Ask", variant="primary")

        # Output below input
        chatbot = gr.Chatbot(
            height=450,
            type="messages",
            bubble_full_width=False,
            avatar_images=("https://cdn-icons-png.flaticon.com/512/327/327155.png", None),
        )

        status = gr.Markdown("", elem_id="status-text")

        gr.Markdown("---")
        gr.Markdown(
            "💡 *Built with OpenRouter + FastAPI + Gradio"
        )

        # ------------------------
        # ⚙️ Chat handler function
        # ------------------------
        def chat_law(query, history):
            status_text = "⏳ Processing..."
            response = asyncio.run(get_law_info(query))
            results = response["results"]

            html = f"<div id='chatbox'>"
            html += f"<div class='law-card'><div class='crime-title'>🧭 Query: {response['query']}</div>"
            html += f"<p><b>Normalized:</b> {response['normalized_query']}</p></div>"

            for res in results:
                html += f"""
                    <div class='law-card'>
                        <div class='crime-title'>🧩 {res['crime']}
                            <button class='copy-btn' onclick="navigator.clipboard.writeText(`{res['explanation']}`)">📋 Copy</button>
                        </div>
                        <div class='response-text'>{res['explanation']}</div>
                    </div>
                """
            html += "</div>"

            status_text = "✅ Done"
            history = history + [{"role": "user", "content": query}, {"role": "assistant", "content": html}]
            return history, status_text

        submit_btn.click(
            fn=chat_law,
            inputs=[query_box, chatbot],
            outputs=[chatbot, status],
        )

# 🧩 Mount inside FastAPI
app = mount_gradio_app(app, iface, path="/gradio")
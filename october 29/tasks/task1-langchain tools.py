# AI Productivity Assistant - LangChain + Mistral (OpenRouter)
# ------------------------------------------------------------

from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI

# Initialize memory (for chat + notes)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
notes = []  # simple in-memory note storage

# Initialize Mistral (via OpenRouter)
llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key="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"
)

# ------------------------------------------------------------
# 1. Summarizer Tool
# ------------------------------------------------------------
def summarize_text(text: str) -> str:
    prompt = f"Summarize this text in one concise sentence:\n\n{text}"
    response = llm.invoke(prompt)
    return response.content.strip()

# ------------------------------------------------------------
# 2. Sentiment Analyzer Tool
# ------------------------------------------------------------
def analyze_sentiment(text: str) -> str:
    prompt = f"Classify the sentiment (positive, neutral, or negative) of this text:\n\n{text}"
    response = llm.invoke(prompt)
    sentiment = response.content.strip()
    return f"The sentiment is {sentiment}."

# ------------------------------------------------------------
# 3. NoteKeeper Tool
# ------------------------------------------------------------
def add_note(note: str) -> str:
    notes.append(note)
    return f"Noted: “{note}”."

def get_notes() -> str:
    if not notes:
        return "You currently have no notes."
    joined_notes = "; ".join([f"“{n}”" for n in notes])
    return f"You currently have {len(notes)} note(s): {joined_notes}"

# ------------------------------------------------------------
# 4. Text Improver Tool
# ------------------------------------------------------------
def improve_text(text: str) -> str:
    prompt = f"Improve the clarity and professionalism of this text, suggest a rewrite:\n\n{text}"
    response = llm.invoke(prompt)
    return response.content.strip()

# ------------------------------------------------------------
# 5. Task Priority Classifier
# ------------------------------------------------------------
def classify_priority(task: str) -> str:
    high_keywords = ["urgent", "tonight", "immediately", "submit", "deadline"]
    low_keywords = ["later", "snack", "coffee", "clean", "remind"]

    if any(word in task.lower() for word in high_keywords):
        priority = "HIGH"
    elif any(word in task.lower() for word in low_keywords):
        priority = "LOW"
    else:
        # fallback to LLM reasoning
        prompt = f"Classify this task into HIGH, MEDIUM, or LOW priority: {task}"
        response = llm.invoke(prompt)
        priority = response.content.strip().upper()

    return f'Task “{task}” marked as {priority} priority.'

# ------------------------------------------------------------
# Conversational Loop
# ------------------------------------------------------------
print("\n=== AI Productivity Assistant ===")
print("Available Commands: summarize, analyze, note, get notes, improve, priority, history, exit\n")

while True:
    user_input = input("You: ").strip()
    if user_input.lower() == "exit":
        print("\nConversation ended.")
        break

    # History Command
    if user_input.lower() == "history":
        chat_history = memory.load_memory_variables({}).get("chat_history", [])
        if not chat_history:
            print("Agent: No previous chat history found.")
        else:
            print("\n--- Conversation History ---")
            for msg in chat_history:
                print(f"{msg.type.title()}: {msg.content}")
        continue

    # Summarize Command
    if user_input.lower().startswith("summarize"):
        text = user_input[len("summarize "):].strip()
        if not text:
            print("Agent: Please provide text to summarize.")
            continue
        result = summarize_text(text)
        print("Agent:", result)
        memory.save_context({"input": user_input}, {"output": result})
        continue

    # Analyze Sentiment
    if user_input.lower().startswith("analyze"):
        text = user_input[len("analyze "):].strip()
        if not text:
            print("Agent: Please provide text to analyze sentiment.")
            continue
        result = analyze_sentiment(text)
        print("Agent:", result)
        memory.save_context({"input": user_input}, {"output": result})
        continue

    # Add Note
    if user_input.lower().startswith("note"):
        note_text = user_input[len("note "):].strip()
        if not note_text:
            print("Agent: Please provide a note to remember.")
            continue
        result = add_note(note_text)
        print("Agent:", result)
        memory.save_context({"input": user_input}, {"output": result})
        continue

    # Get Notes
    if user_input.lower() == "get notes":
        result = get_notes()
        print("Agent:", result)
        memory.save_context({"input": user_input}, {"output": result})
        continue

    # Improve Text
    if user_input.lower().startswith("improve"):
        text = user_input[len("improve "):].strip()
        if not text:
            print("Agent: Please provide text to improve.")
            continue
        result = improve_text(text)
        print("Agent:", result)
        memory.save_context({"input": user_input}, {"output": result})
        continue

    # Task Priority
    if user_input.lower().startswith("priority"):
        task = user_input[len("priority "):].strip()
        if not task:
            print("Agent: Please provide a task to classify priority.")
            continue
        result = classify_priority(task)
        print("Agent:", result)
        memory.save_context({"input": user_input}, {"output": result})
        continue

    # Fallback: use LLM as general assistant
    print("Agent (LLM): Thinking...")
    response = llm.invoke(user_input)
    print("Agent:", response.content)
    memory.save_context({"input": user_input}, {"output": response.content})

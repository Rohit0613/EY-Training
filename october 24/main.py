import os
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# ------------------------------------------------------
# 1. Load environment variables
# ------------------------------------------------------
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY missing in .env")

# ------------------------------------------------------
# 2. Initialize LangChain model (Mistral via OpenRouter)
# ------------------------------------------------------
llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct",
    temperature=0.7,
    max_tokens=256,
    api_key=api_key,
    base_url=base_url,
)

# ------------------------------------------------------
# 3. Define prompt and run model
# ------------------------------------------------------
messages = [
    SystemMessage(content="You are a concise and helpful AI assistant."),
    HumanMessage(content="<s>[INST] Explain reinforcement learning in simple terms. [/INST]"),
]

response = llm.invoke(messages)
output_text = response.content.strip()
print("Assistant:", output_text)

# ------------------------------------------------------
# 4. Logging the interaction
# ------------------------------------------------------
log_data = {
    "timestamp": datetime.utcnow().isoformat(),
    "model": "mistralai/mistral-7b-instruct",
    "prompt": messages[-1].content,
    "response": output_text,
    "feedback": None  # will be filled later by user
}

os.makedirs("logs", exist_ok=True)
log_file = "logs/mistral_feedback_log.jsonl"

with open(log_file, "a", encoding="utf-8") as f:
    f.write(json.dumps(log_data) + "\n")

print(f"Logged to {log_file}")

# ------------------------------------------------------
# 5. Feedback loop (user rating)
# ------------------------------------------------------
feedback = input("\nWas this response helpful? (yes / no / partial): ").strip().lower()
comment = input("Any additional comments? (press Enter to skip): ").strip()

# update feedback
log_data["feedback"] = {
    "rating": feedback,
    "comment": comment,
    "timestamp": datetime.utcnow().isoformat()
}

# update log file
with open(log_file, "a", encoding="utf-8") as f:
    f.write(json.dumps(log_data) + "\n")

print("\nFeedback recorded. Thank you!")

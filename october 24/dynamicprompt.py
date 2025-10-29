import os
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ----------------------------------------------------------
# 1. Load environment variables
# ----------------------------------------------------------
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY missing in .env")

# ----------------------------------------------------------
# 2. Initialize model (Mistral via OpenRouter)
# ----------------------------------------------------------
llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct",
    temperature=0.7,
    max_tokens=512,
    api_key=api_key,
    base_url=base_url,
)

# ----------------------------------------------------------
# 3. Define prompt templates
# ----------------------------------------------------------
explain_prompt = ChatPromptTemplate.from_template(
    "<s>[INST] You are a concise assistant. Explain {topic} in simple terms for a beginner. [/INST]"
)

quiz_prompt = ChatPromptTemplate.from_template(
    "<s>[INST] Create a short quiz (3 to 5 questions) for a beginner about the topic '{topic}'. "
    "Use simple language and include multiple-choice options (A, B, C, D). "
    "Do not provide the answers. [/INST]"
)

parser = StrOutputParser()

# ----------------------------------------------------------
# 4. Generate explanation and quiz
# ----------------------------------------------------------
def generate_content(topic):
    explain_chain = explain_prompt | llm | parser
    quiz_chain = quiz_prompt | llm | parser

    explanation = explain_chain.invoke({"topic": topic})
    quiz = quiz_chain.invoke({"topic": topic})

    return explanation, quiz

# ----------------------------------------------------------
# 5. User interaction & logging
# ----------------------------------------------------------
user_topic = input("Enter a topic: ").strip()

explanation, quiz = generate_content(user_topic)

print("\n--- Explanation ---\n")
print(explanation)
print("\n--- Quiz ---\n")
print(quiz)

# ----------------------------------------------------------
# 6. Logging
# ----------------------------------------------------------
os.makedirs("logs", exist_ok=True)
log_entry = {
    "timestamp": datetime.now().isoformat(),
    "topic": user_topic,
    "explanation": explanation,
    "quiz": quiz,
}

with open("logs/prompt_log.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

print("\nResponse logged to logs/prompt_log.jsonl ✅")

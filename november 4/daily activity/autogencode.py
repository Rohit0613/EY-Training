from autogen import AssistantAgent

from langchain_openai import ChatOpenAI
from datetime import datetime
from testing import OPENROUTER_API_KEY
from testing import OPENROUTER_BASE_URL
a = OPENROUTER_API_KEY
b = OPENROUTER_BASE_URL

llm_config = {
    "model": "meta-llama/llama-3-8b-instruct",
    "api_key": f"{a}",
    "base_url": f"{b}",
    "temperature": 0.7,
    "max_tokens": 700,
}

researcher = AssistantAgent(
    name="Researcher",
    llm_config=llm_config,
    system_message="You are a research assistant. Research the given topic and provide factual, clear insights in about 10 concise bullet points.",
)

summarizer = AssistantAgent(
    name="Summarizer",
    llm_config=llm_config,
    system_message="You are a summarizer. Create a short summary (3–5 sentences) and 5 key bullet points from the given research notes.",
)

def notifier_agent(summary: str, filename: str = "summary_log.txt"):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(summary)
        f.write(f"Autogen:- Notified and saved to {filename}")
        print("Notified")

def run_pipeline(topic: str):
    research = researcher.generate_reply(
        messages=[{"role": "user", "content": f"Research this topic: {topic}"}]
    )
    summary = summarizer.generate_reply(
        messages=[{"role": "user", "content": f"Summarize this research:\n{research}"}]
    )
    print(summary)
    notifier_agent(summary)

if __name__ == "__main__":
    topic = "Impact of Artificial Intelligence on Healthcare"
    run_pipeline(topic)
from autogen import AssistantAgent
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY missing in .env")

llm_config = {
    "model": "meta-llama/llama-3-8b-instruct",
    "api_key": api_key,
    "base_url": base_url,
    "temperature": 0.7,
    "max_tokens": 500,
}

researcher = AssistantAgent(
    name="Researcher",
    llm_config=llm_config,
    system_message="You are a research expert. Your job is to find and summarize useful information about any given topic in bullet points."
)

writer = AssistantAgent(
    name="Writer",
    llm_config=llm_config,
    system_message="You are a professional content writer. You will take research summaries and write a clear, engaging 3-paragraph report."
)

reviewer = AssistantAgent(
    name="Reviewer",
    llm_config=llm_config,
    system_message="You are an editor and critic. Your job is to review the writer's report, check for clarity, grammar, and completeness, and suggest improvements."
)

topic = "Impact of Artificial Intelligence on Education"

research = researcher.generate_reply(
    messages=[{"role": "user", "content": f"Please research the topic: {topic}."}]
)

print("\nResearch Summary:\n", research, "\n")

report = writer.generate_reply(
    messages=[{"role": "user", "content": f"Write a report based on this research:\n{research}"}]
)

print("Draft Report:\n", report, "\n")

review = reviewer.generate_reply(
    messages=[{"role": "user", "content": f"Please review and improve this report:\n{report}"}]
)

print("Final Reviewed Report:\n", review)

from autogen import AssistantAgent, UserProxyAgent
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
os.environ["AUTOGEN_USE_DOCKER"] = "False"

if not api_key:
    raise ValueError("OPENROUTER_API_KEY missing in .env")

llm_config = {
    "model": "meta-llama/llama-3-8b-instruct",
    "api_key": api_key,
    "base_url": base_url,
    "temperature": 0.7,
    "max_tokens": 256,
}



# 2️⃣ Create the Assistant Agent (the AI)
assistant = AssistantAgent(
    name="assistant",
    llm_config=llm_config,
    system_message="You are a helpful AI assistant."
)

# 3️⃣ Create the User Proxy Agent (represents the human)
user = UserProxyAgent(
    name="user",
    human_input_mode="NEVER",
    code_execution_config={"use_docker": False}  # ✅ disable Docker execution
)

# 4️⃣ Start a simple conversation
response = user.initiate_chat(
    assistant,
    message="Explain quantum computing in simple words."
)

# 5️⃣ Print the final AI reply
print("\n🤖 AI Response:\n", response)

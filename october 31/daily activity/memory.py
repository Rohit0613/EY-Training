import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory


# 1️⃣ Load environment variables
load_dotenv()

# 2️⃣ Fetch credentials
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# 3️⃣ Initialize ChatOpenAI via LangChain
llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct",
    temperature=0.2,
    openai_api_key=OPENROUTER_KEY,
    openai_api_base=OPENROUTER_BASE,
)

# 4️⃣ Add memory
memory = ConversationBufferMemory(memory_key="history", return_messages=True)


# 5️⃣ Create conversation chain
conv = ConversationChain(llm=llm, memory=memory)

# 6️⃣ Test conversation
print(conv.predict(input="Hi — remember my name is Rohit."))
print(conv.predict(input="What's my name?"))
print(conv.predict(input="Summarize our chat so far."))

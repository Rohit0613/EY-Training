import os
from dotenv import load_dotenv
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

if not api_key:
    st.error("OPENROUTER_API_KEY not found in .env file")
    st.stop()

# Initialize model
llm = ChatOpenAI(
    model="meta-llama/llama-3.3-8b-instruct:free",
    temperature=0.7,
    max_tokens=256,
    api_key=api_key,
    base_url=base_url,
)

# Streamlit UI
st.title("🧠 AI Chat")
st.markdown("Ask me anything below:")

user_input = st.text_area("Your question:", placeholder="e.g. Explain CNNs in simple terms")

if st.button("Get Answer"):
    if user_input.strip():
        with st.spinner("Thinking..."):
            try:
                messages = [
                    SystemMessage(content="You are a helpful and concise AI assistant."),
                    HumanMessage(content=f"<s>[INST] {user_input} [/INST]"),
                ]
                response = llm.invoke(messages)
                st.success("Response:")
                st.write(response.content.strip() or "(no content returned)")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please enter a question first.")

import streamlit as st
import requests

# ----------------------------
# 🌟 Streamlit Page Config
# ----------------------------
st.set_page_config(page_title="🤖AI Assistant", page_icon="💬", layout="centered")

st.title("💬 AI Assistant")
st.caption("Powered by FastAPI + OpenRouter + Streamlit")

# ----------------------------
# 💬 User Input
# ----------------------------
query = st.text_input("Type your query (e.g., 45 + 35, reverse Rohit, today's date):")
submit = st.button("Submit")

# ----------------------------
# 🚀 Backend Call + Live Stream Display
# ----------------------------
if submit and query:
    with st.chat_message("user"):
        st.markdown(f"**You:** {query}")

    with st.chat_message("assistant"):
        placeholder = st.empty()
        response_text = ""

        try:

            with requests.post(
                "http://localhost:8000/query",
                json={"query": query},
                stream=True,
                timeout=60,
            ) as r:
                if r.status_code != 200:
                    st.error(f"Backend Error: {r.status_code}")
                else:
                    # Read streamed plain text chunks
                    for chunk in r.iter_content(chunk_size=None):
                        if chunk:
                            text = chunk.decode("utf-8")
                            response_text += text
                            placeholder.markdown(response_text + "▌")

            placeholder.markdown(response_text.strip())  # final output
            st.success("✅ Response complete!")
        except Exception as e:
            st.error(f"Error: {e}")

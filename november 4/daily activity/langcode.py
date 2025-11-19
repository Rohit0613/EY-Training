
from langchain_openai import ChatOpenAI
from datetime import datetime
from testing import OPENROUTER_API_KEY
from testing import OPENROUTER_BASE_URL
a = OPENROUTER_API_KEY
b = OPENROUTER_BASE_URL

llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct",
    temperature=0.4,
    max_tokens=512,
    openai_api_key=f"{a}",
    openai_api_base=f"{b}",
)


# Memory
# memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# # Weather Agent
# def weather(city: str) -> str:
#     url = f"http://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={city}&aqi=no"
#     response = requests.get(url)
#     if response.status_code == 200:
#         data = response.json()
#         temp_c = data["current"]["temp_c"]
#         temp_f = data["current"]["temp_f"]
#         return f"The temperature in {city} is {temp_c}°C ({temp_f}°F)."
#     else:
#         return f"Error fetching weather: {response.status_code}"


# Researcher Agent
def research_topic(topic: str) -> str:
    prompt = f"""
You are a research assistant tasked with gathering comprehensive, factual, and insightful information on the topic: "{topic}". Your goal is to produce a detailed report that includes:
1. Definition and background
2. Key developments and trends
3. Relevant statistics or expert opinions
4. Real-world applications
5. Challenges or controversies
6. Future outlook
"""
    return llm.invoke(prompt).content


# Summarizer Agent
def summarize_text(text: str) -> str:
    prompt = f"""
You are a summarization expert. Summarize the following research into key insights and takeaways:

{text}

Instructions:
- Keep it under 300 words
- Use bullet points or short paragraphs
- Avoid jargon
"""
    return llm.invoke(prompt).content


# Logger Agent
# Notifier Agent
def Notifier(summary: str, filename: str = "summary_log.txt"):
    # Print the summary in the terminal
    print("Agent (Summary):", summary)

    # Log the summary to the file
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - Langchain: Notified and saved to {filename}\n")
        f.write(f"{summary}\n\n")

    print("Summary has been logged.")
    return {}


# Notifier Agent

# Main loop
print("\n=== Start chatting with your Agent ===")
print("Type 'exit' to quit.\n")

while True:
    user_input = input("You: ").strip()
    if user_input.lower() == "exit":
        print("\nConversation ended.")
        break

    # Weather flow
    if "weather" in user_input.lower():
        try:
            city = user_input.split("in")[-1].strip()
            if not city:
                print("Agent: Please specify a city name.")
                continue
            city_weather = weather(city)
            print("Agent:", city_weather)
            # memory.save_context({"input": user_input}, {"output": city_weather})
            continue
        except Exception as e:
            print("Agent: Could not find the temperature:", e)
            continue

    # Research flow
    if user_input.lower().startswith("research"):
        topic = user_input.replace("research", "").strip()
        if not topic:
            print("Agent: Please specify a topic.")
            continue
        try:
            research = research_topic(topic)
            summary = summarize_text(research)
            Notifier(summary)
            print("Agent (Summary):", summary)

            # memory.save_context({"input": user_input}, {"output": summary})
        except Exception as e:
            print("Agent: Error during research flow:", e)
        continue

    # Default LLM response
    try:
        response = llm.invoke(user_input)
        print("Agent:", response.content)
        # memory.save_context({"input": user_input}, {"output": response.content})
    except Exception as e:
        print("Error:", e)

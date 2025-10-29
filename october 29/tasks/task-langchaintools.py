# ------------------------------------------------------------
# Mini Language Utility Bot using LangChain + Mistral (OpenRouter)
# ------------------------------------------------------------

from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI

# Initialize memory and LLM
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct",
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key="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"
)

# ------------------------------------------------------------
# Utility Functions (Tools)
# ------------------------------------------------------------

def count_words(sentence: str) -> str:
    words = sentence.split()
    return f"Your sentence has {len(words)} words."

def reverse_text(sentence: str) -> str:
    return " ".join(sentence.split()[::-1])

def change_case(sentence: str, to_upper=True) -> str:
    return sentence.upper() if to_upper else sentence.lower()

def repeat_word(word: str, times: int) -> str:
    try:
        times = int(times)
        return " ".join([word] * times)
    except ValueError:
        return "Please specify a valid number."

def define_word(word: str) -> str:
    """Uses Mistral LLM to define a word"""
    prompt = f"Give a short, simple definition for the word '{word}' in one sentence."
    response = llm.invoke(prompt)
    return response.content.strip()

# ------------------------------------------------------------
# Conversational Loop
# ------------------------------------------------------------
print("\n=== Mini Language Utility Bot ===")
print("Available Commands: count, reverse, define, upper, lower, repeat, history, exit\n")

while True:
    user_input = input("You: ").strip()
    if user_input.lower() == "exit":
        print("\nConversation ended.")
        break

    # History command
    if user_input.lower() == "history":
        chat_history = memory.load_memory_variables({}).get("chat_history", [])
        if not chat_history:
            print("Agent: No previous conversation history found.")
        else:
            print("\n--- Conversation History ---")
            for msg in chat_history:
                print(f"{msg.type.title()}: {msg.content}")
        continue

    # Count command
    if user_input.lower().startswith("count"):
        text = user_input[len("count "):].strip()
        if not text:
            print("Agent: Please provide a sentence to count words.")
            continue
        result = count_words(text)
        print("Agent:", result)
        memory.save_context({"input": user_input}, {"output": result})
        continue

    # Reverse command
    if user_input.lower().startswith("reverse"):
        text = user_input[len("reverse "):].strip()
        if not text:
            print("Agent: Please provide text to reverse.")
            continue
        result = reverse_text(text)
        print("Agent:", result)
        memory.save_context({"input": user_input}, {"output": result})
        continue

    # Uppercase command
    if user_input.lower().startswith("upper"):
        text = user_input[len("upper "):].strip()
        if not text:
            print("Agent: Please provide text to convert to uppercase.")
            continue
        result = change_case(text, to_upper=True)
        print("Agent:", result)
        memory.save_context({"input": user_input}, {"output": result})
        continue

    # Lowercase command
    if user_input.lower().startswith("lower"):
        text = user_input[len("lower "):].strip()
        if not text:
            print("Agent: Please provide text to convert to lowercase.")
            continue
        result = change_case(text, to_upper=False)
        print("Agent:", result)
        memory.save_context({"input": user_input}, {"output": result})
        continue

    # Repeat command
    if user_input.lower().startswith("repeat"):
        parts = user_input.split()
        if len(parts) < 3:
            print("Agent: Please use 'repeat <word> <times>' format.")
            continue
        word, times = parts[1], parts[2]
        result = repeat_word(word, times)
        print("Agent:", result)
        memory.save_context({"input": user_input}, {"output": result})
        continue

    # Define command (uses Mistral)
    if user_input.lower().startswith("define"):
        word = user_input[len("define "):].strip()
        if not word:
            print("Agent: Please provide a word to define.")
            continue
        result = define_word(word)
        print("Agent:", result)
        memory.save_context({"input": user_input}, {"output": result})
        continue

    # Default: Use LLM for generic response
    print("Agent (LLM): Thinking...")
    response = llm.invoke(user_input)
    print("Agent:", response.content)
    memory.save_context({"input": user_input}, {"output": response.content})

import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI  # Updated import
from langchain.agents import initialize_agent, AgentType, Tool

# Load environment variables
load_dotenv()

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Controller LLM (uses OpenRouter)
controller_llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct",
    temperature=0,
    openai_api_key=OPENROUTER_KEY,
    openai_api_base=OPENROUTER_BASE
)


# A tiny subagent implemented as a function that itself calls the LLM (also via OpenRouter)
def summarizer_subagent(text: str) -> str:
    sub_llm = ChatOpenAI(
        model="openai/gpt-4o",
        temperature=0,
        openai_api_key=OPENROUTER_KEY,
        openai_api_base=OPENROUTER_BASE
    )
    # Generate a summary using a structured prompt
    result = sub_llm.invoke([{"role": "user", "content": f"Summarize the following text in two sentences:\n\n{text}"}])

    # Access content correctly from the result (AIMessage)
    return result['choices'][0].message.content  # Directly access content from the message


# Wrap the subagent as a Tool (so controller can call it)
summ_tool = Tool.from_function(func=summarizer_subagent, name="summarizer_agent",
                               description="Summarizes long text to 2 sentences.")

# Set up the agent with the controller LLM and tool
agent = initialize_agent([summ_tool], controller_llm, agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

# Test the agent
big_text = ("Artificial intelligence is advancing rapidly. "
            "Edge devices are getting more compute, allowing models to run locally. "
            "This leads to lower latency and better privacy.")

prompt = f"Analyze the article below and call summarizer_agent to return a 2-sentence summary:\n\n{big_text}"
out = agent.run(prompt)
print("\nController output:\n", out)

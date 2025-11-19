import wikipedia
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.tools.python import PythonREPLTool

# Simple function to get Wikipedia summary
def get_wikipedia_summary(query):
    try:
        return wikipedia.summary(query)
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Disambiguation Error: {e.options}"
    except wikipedia.exceptions.HTTPTimeoutError:
        return "Timeout error occurred."
    except wikipedia.exceptions.RedirectError as e:
        return f"Redirect Error: {str(e)}"

# Custom Wikipedia tool for LangChain
wikipedia_tool = Tool(
    name="Wikipedia Search",
    func=get_wikipedia_summary,  # The function to call
    description="Fetches Wikipedia summary for a given query."
)

# Initialize the OpenAI model using LangChain
llm = ChatOpenAI(model="mistralai/mistral-7b-instruct", temperature=0)

# Create the tools (Wikipedia and Python REPL)
python_tool = PythonREPLTool()

# Initialize the agent with both tools
tools = [wikipedia_tool, python_tool]
agent = initialize_agent(tools, llm, agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

# Example prompt: Search for a topic and compute a percentage
prompt = (
    "Search for the population of Japan in 2025, then compute 1% of that population and show it as per-1000 people."
)

# Run agent
result = agent.run(prompt)
print(result)

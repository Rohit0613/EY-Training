import os

# ---------------------------------------------------------------------
# 1️⃣ Set your OpenRouter API key and base URL for LiteLLM
# ---------------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
from crewai import Agent, Task, Crew, Process

# ---------------------------------------------------------------------
# 2️⃣ Define your agents
# ---------------------------------------------------------------------
researcher = Agent(
    role="AI Research Specialist",
    goal="Gather insights on a given AI topic in a clear and concise way",
    backstory="You are an expert AI researcher skilled in summarizing key points from complex topics.",
    verbose=True,
    allow_delegation=False,
    model="mistralai/mistral-7b-instruct",
)

writer = Agent(
    role="Technical Writer",
    goal="Convert research insights into a structured article or summary.",
    backstory="You are a professional technical writer who creates engaging, educational articles from research content.",
    verbose=True,
    allow_delegation=False,
    model="mistralai/mistral-7b-instruct",
)

# ---------------------------------------------------------------------
# 3️⃣ Define your tasks
# ---------------------------------------------------------------------
task1 = Task(
    description="Research the topic: Applications of Artificial Intelligence in Healthcare. Gather 3–4 key insights in bullet points.",
    agent=researcher,
    expected_output="List of 3-4 key insights in bullet points"  # Use a simple string
)

task2 = Task(
    description="Write a short summary article (approx 200 words) based on the research insights from Task 1.",
    agent=writer,
    context=[task1],
    expected_output="200-word summary article"  # Use a simple string
)

# ---------------------------------------------------------------------
# 4️⃣ Create and run your crew
# ---------------------------------------------------------------------
crew = Crew(
    agents=[researcher, writer],
    tasks=[task1, task2],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    topic = "Applications of Artificial Intelligence in Healthcare"
    print("\n🚀 Starting CrewAI workflow with OpenRouter...\n")
    result = crew.kickoff(inputs={"topic": topic})
    print("\n--- FINAL OUTPUT ---\n")
    print(result)

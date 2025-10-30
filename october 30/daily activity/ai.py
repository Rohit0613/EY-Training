# simple_crew.py
# Minimal CrewAI example — two-agent crew (researcher -> writer)

from crewai import Crew, Agent

# Agent definitions (minimal inline — for larger projects use YAML)
researcher = Agent(
    name="researcher",
    role="Research Assistant",
    # goal: gather 3 concise facts about the topic
    goal="Find three concise, reliable bullet points about {topic} with short citations.",
    # backstory or system prompt could go here
)

writer = Agent(
    name="writer",
    role="Summary Writer",
    goal="Write a short (3-sentence) summary of the topic using the researcher's bullet points."
)

# Create a crew with a simple sequential process
crew = Crew(
    name="mini-research-crew",
    agents=[researcher, writer],
    process="sequential"  # researcher runs first, then writer
)

if __name__ == "__main__":
    topic = "edge AI for drones"
    # kickoff runs the crew with inputs; returns aggregated output
    result = crew.kickoff(inputs={"topic": topic})
    print("=== Crew output ===")
    print(result)

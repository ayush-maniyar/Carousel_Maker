import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM

load_dotenv()

# We are forcing the library to use the STABLE v1 API
my_llm = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1" # Forces Stable v1
)

test_agent = Agent(
    role="System Tester",
    goal="Verify the stable API connection.",
    backstory="A specialized diagnostic agent.",
    llm=my_llm,
    verbose=True
)

test_task = Task(
    description="Say 'System Online'.",
    expected_output="The words 'System Online'",
    agent=test_agent
)

test_crew = Crew(agents=[test_agent], tasks=[test_task])

print("--- Final Attempt: Forcing Stable v1 ---")
try:
    result = test_crew.kickoff()
    print(f"\nSUCCESS: {result}")
except Exception as e:
    print(f"\nERROR: {e}")
    
from phi.agent import Agent
from phi.model.openai import OpenAIChat

finance_agent = Agent(
    name="Finance Agent",
    model=OpenAIChat(id="gpt-4o"),
    instructions=["Use tables to display data"],
    show_tool_calls=True,
    markdown=True,
)
finance_agent.print_response("Summarize analyst recommendations for NVDA", stream=True)
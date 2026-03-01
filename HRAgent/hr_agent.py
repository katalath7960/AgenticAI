"""
hr_agent.py — LangGraph ReAct agent for HR management.

Uses langgraph.prebuilt.create_react_agent which automatically handles
the START → agent → tools → agent → ... → END loop.
"""

from __future__ import annotations

import os
from datetime import date
from functools import lru_cache

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from hr_database import init_db
from hr_tools import ALL_TOOLS

load_dotenv()

SYSTEM_PROMPT = f"""You are an intelligent HR assistant for Edureka Corp.
Today's date is {{today}}.

You have access to the following capabilities:
- Employee directory: look up employees by name, department, or role
- Leave management: check balances, submit requests, approve or reject leave
- HR policies: search and explain company policies (leave, benefits, code of conduct, etc.)
- Recruitment: view open positions, post new jobs, submit applications, manage applicant pipeline

Guidelines:
- Always use the lookup_employee tool first to find an employee's id before checking their leave or details.
- When submitting or approving leave, confirm the key details (dates, type, days) before acting.
- For policy questions, always use search_hr_policy to retrieve accurate policy text before answering.
- Be concise, professional, and helpful.
- If you cannot find information, say so clearly rather than guessing.
"""


@lru_cache(maxsize=1)
def get_agent():
    init_db()
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
    )
    prompt = SYSTEM_PROMPT.format(today=date.today().isoformat())
    return create_react_agent(llm, tools=ALL_TOOLS, prompt=prompt)


def run(message: str, history: list[dict] | None = None) -> str:
    """Run the HR agent with a user message and optional prior conversation history.

    Args:
        message: The user's latest message.
        history: List of prior messages as dicts with 'role' and 'content' keys.

    Returns:
        The agent's final text response.
    """
    agent = get_agent()

    messages = []
    for msg in (history or []):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        # assistant messages are handled by the agent state automatically

    messages.append(HumanMessage(content=message))

    result = agent.invoke({"messages": messages})
    last = result["messages"][-1]
    return last.content


if __name__ == "__main__":
    print("HR Agent ready. Type 'quit' to exit.\n")
    history: list[dict] = []
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue
        response = run(user_input, history)
        print(f"\nHR Agent: {response}\n")
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})

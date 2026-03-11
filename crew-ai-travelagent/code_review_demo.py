"""
CrewAI Code Review Demo
Two agents: Coder writes Python code, Reviewer audits it for bugs and improvements.
"""

import ast
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool

load_dotenv()


# ── Tools ─────────────────────────────────────────────────────────────────────

class SyntaxCheckerTool(BaseTool):
    name: str = "Python Syntax Checker"
    description: str = (
        "Checks a Python code snippet for syntax errors. "
        "Input: raw Python source code as a string. "
        "Returns 'OK' or the syntax error message."
    )

    def _run(self, code: str) -> str:
        try:
            ast.parse(code)
            return "Syntax OK — no syntax errors found."
        except SyntaxError as e:
            return f"SyntaxError at line {e.lineno}: {e.msg}"


class ComplexityCheckerTool(BaseTool):
    name: str = "Complexity Checker"
    description: str = (
        "Counts functions and classes in a Python code snippet and flags "
        "functions longer than 20 lines as potentially too complex. "
        "Input: raw Python source code as a string."
    )

    def _run(self, code: str) -> str:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return f"Cannot analyse — SyntaxError: {e}"

        report = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno
                end = max(
                    getattr(n, "end_lineno", start) for n in ast.walk(node)
                )
                length = end - start + 1
                flag = " ⚠️  (>20 lines — consider refactoring)" if length > 20 else ""
                report.append(f"  def {node.name}(): {length} lines{flag}")
            elif isinstance(node, ast.ClassDef):
                report.append(f"  class {node.name}")

        if not report:
            return "No functions or classes found."
        return "Structure:\n" + "\n".join(report)


# ── Agents ────────────────────────────────────────────────────────────────────

coder = Agent(
    role="Python Developer",
    goal="Write clean, working Python code that fulfils the given requirement.",
    backstory=(
        "You are a senior Python developer who writes readable, well-structured "
        "code. You follow PEP-8 and include docstrings for every function."
    ),
    verbose=True,
    allow_delegation=False,
    llm="gpt-4o",
)

reviewer = Agent(
    role="Code Reviewer",
    goal=(
        "Thoroughly review the provided Python code. "
        "Use your tools to check syntax and complexity, then give a structured "
        "review covering: bugs, edge cases, readability, and improvements."
    ),
    backstory=(
        "You are a meticulous code reviewer with 10+ years of Python experience. "
        "You check code correctness, style, and maintainability, and always "
        "provide actionable, specific feedback."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[SyntaxCheckerTool(), ComplexityCheckerTool()],
    llm="gpt-4o",
)


# ── Tasks ─────────────────────────────────────────────────────────────────────

def build_tasks(requirement: str) -> tuple[Task, Task]:
    write_task = Task(
        description=(
            f"Write a Python implementation for the following requirement:\n\n"
            f"{requirement}\n\n"
            "Include a docstring, type hints, and a brief usage example at the bottom "
            "inside an `if __name__ == '__main__':` block."
        ),
        expected_output=(
            "Complete, runnable Python source code as a plain text code block."
        ),
        agent=coder,
    )

    review_task = Task(
        description=(
            "Review the Python code produced by the developer.\n"
            "Steps:\n"
            "1. Run the Syntax Checker tool on the code.\n"
            "2. Run the Complexity Checker tool on the code.\n"
            "3. Based on tool output AND your own analysis, write a structured review:\n"
            "   - BUGS / ERRORS (if any)\n"
            "   - EDGE CASES not handled\n"
            "   - READABILITY & STYLE notes\n"
            "   - SUGGESTED IMPROVEMENTS with short code snippets where helpful\n"
            "   - OVERALL SCORE out of 10"
        ),
        expected_output=(
            "A structured markdown code-review report with sections for bugs, "
            "edge cases, style, improvements, and an overall score."
        ),
        agent=reviewer,
        context=[write_task],
    )

    return write_task, review_task


# ── Crew ──────────────────────────────────────────────────────────────────────

def run_code_review(requirement: str) -> str:
    write_task, review_task = build_tasks(requirement)

    crew = Crew(
        agents=[coder, reviewer],
        tasks=[write_task, review_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    return str(result)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    REQUIREMENT = (
        "Write a Python function `find_duplicates(items: list) -> list` "
        "that returns a list of elements that appear more than once in the input list. "
        "The result should preserve the order of first duplicate occurrence."
    )

    print("\n" + "=" * 60)
    print("CrewAI Code Review Demo")
    print("=" * 60)
    print(f"Requirement:\n{REQUIREMENT}\n")

    output = run_code_review(REQUIREMENT)

    print("\n" + "=" * 60)
    print("FINAL REVIEW REPORT")
    print("=" * 60)
    print(output)

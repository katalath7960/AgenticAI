# Demo — LangChain & Agentic AI Examples

A collection of progressively more complex LangChain programs demonstrating core patterns for building Agentic AI applications.

---

## Programs

### 1. `main.py` — Basic LangChain Chain
The simplest possible LCEL (LangChain Expression Language) chain.

- Builds a `PromptTemplate | ChatOpenAI | StrOutputParser` pipeline
- Asks the model "What is Agentic AI?" and prints the response
- **Good starting point** for understanding the `|` operator and LCEL basics

**Run:**
```bash
python main.py
```

---

### 2. `mainuvicorn.py` — FastAPI REST Chatbot
Wraps a LangChain chain in a FastAPI web service.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/`      | GET    | Health check — returns `{"status": "Agent is running!"}` |
| `/ask`   | POST   | Accepts `{"question": "..."}` and returns `{"answer": "..."}` |

**Run:**
```bash
uvicorn mainuvicorn:app --reload
```

---

### 3. `conditional-chain.py` — Conditional Branching
Demonstrates `RunnableBranch` for context-aware routing.

- A **Context Checker** chain first evaluates if the user's message has enough context
- Routes to an **Answer Chain** (sufficient context) or a **Follow-up Chain** (asks clarifying questions)
- Uses `RunnablePassthrough.assign()` to enrich inputs before branching

**Run:**
```bash
python conditional-chain.py
```

---

### 4. `router-chain.py` — Multi-destination Router
Routes messages to specialist agents based on category.

- A **Classifier Chain** labels each message as `billing`, `support`, or `general`
- Three specialist chains handle each category with tailored system prompts:
  - **Billing** — payments, invoices, subscriptions
  - **Technical Support** — troubleshooting and bug reports
  - **General** — everything else
- Uses `RunnableBranch` for multi-way routing

**Run:**
```bash
python router-chain.py
```

---

### 5. `runnable-demo.py` — Multi-step Workflow (Generate + Review)
Shows how to chain multiple LLM calls together into a pipeline.

1. **Story Creator** (GPT, temperature 0.8) — generates a 3–4 paragraph short story from a topic
2. **Reviewer** (GPT-4o, temperature 0.2) — evaluates the story for family-friendliness, returning a verdict, reason, and suggestions
3. Final output is a dictionary with `topic`, `story`, and `review` keys

**Run:**
```bash
python runnable-demo.py
```

---

### 6. `main.ipynb` — Empty Notebook
Placeholder Jupyter notebook with no content yet.

---

### 7. `app.ipynb` — Hello World Notebook
Minimal Jupyter notebook with a single `print("hello world123")` cell. Useful for verifying that the notebook environment is working.

---

## Prerequisites

All Python scripts require an OpenAI API key. Create a `.env` file in this directory (or the project root):

```
OPENAI_API_KEY=sk-...
```

Install dependencies:

```bash
pip install langchain langchain-openai langchain-core fastapi uvicorn python-dotenv
```

---

## Key Concepts Covered

| Concept | File(s) |
|--------|---------|
| Basic LCEL chain (`|` operator) | `main.py`, `mainuvicorn.py` |
| FastAPI + LangChain integration | `mainuvicorn.py` |
| Conditional branching (`RunnableBranch`) | `conditional-chain.py`, `router-chain.py` |
| Input enrichment (`RunnablePassthrough.assign`) | `conditional-chain.py`, `router-chain.py`, `runnable-demo.py` |
| Multi-step chained LLM workflows | `runnable-demo.py` |

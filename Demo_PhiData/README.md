# Demo PhiData — Agent with Web Search

A PhiData-powered research agent ("Jarvis") that combines **DuckDuckGo search**, **article scraping**, and **custom webpage fetching** to answer queries with cited, up-to-date information.

## Files

| File | Description |
|---|---|
| `Agent_with_WebSearch` | Main agent with 4 tools: DuckDuckGo, Newspaper4k, scrape_webpage, get_current_datetime |
| `basic.py` | Minimal conversational agent (no tools) |
| `finance_agent.py` | Finance-focused agent for analyst recommendations |
| `Requirement.txt` | Python dependencies |

## Agent Architecture

The agent uses **GPT-4o** as the reasoning model and selects tools dynamically based on the query.

### Tools

| Tool | Type | Purpose |
|---|---|---|
| `DuckDuckGo` | PhiData built-in | Web search — returns links and snippets |
| `Newspaper4k` | PhiData built-in | Full article extraction from URLs |
| `scrape_webpage` | Custom Python fn | Raw HTML-to-text scraper (fallback) |
| `get_current_datetime` | Custom Python fn | Returns current date/time for time-sensitive queries |

---

## Sequence Diagram — Agent with Web Search

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Agent as Jarvis Agent<br/>(PhiData)
    participant LLM as OpenAI GPT-4o
    participant DDG as DuckDuckGo Tool
    participant N4K as Newspaper4k Tool
    participant SW as scrape_webpage Tool
    participant DT as get_current_datetime Tool

    User->>Agent: Submit query (e.g. "Latest news on AI agents")

    Agent->>LLM: Forward query + system instructions + tool definitions

    LLM-->>Agent: Decide: call get_current_datetime (if time-sensitive)

    Agent->>DT: get_current_datetime()
    DT-->>Agent: "2025-03-01 10:30:00"

    Agent->>LLM: Append datetime context, re-reason

    LLM-->>Agent: Decide: call DuckDuckGo(query)

    Agent->>DDG: search("Latest news on AI agents")
    DDG-->>Agent: Search results (titles, URLs, snippets)

    Agent->>LLM: Append search results, re-reason

    LLM-->>Agent: Decide: call Newspaper4k(url) for deeper article

    Agent->>N4K: read_article(url)
    N4K-->>Agent: Full article text

    Agent->>LLM: Append article content, re-reason

    alt Newspaper4k insufficient or raw HTML needed
        LLM-->>Agent: Decide: call scrape_webpage(url)
        Agent->>SW: scrape_webpage(url)
        SW-->>Agent: Extracted visible text (up to 8000 chars)
        Agent->>LLM: Append scraped content, re-reason
    end

    LLM-->>Agent: Final synthesized response (with sources, markdown)

    Agent-->>User: Stream formatted response
```

---

## Tool Decision Logic

```mermaid
flowchart TD
    Q([User Query]) --> A{Time-sensitive?}
    A -- Yes --> DT[get_current_datetime\nAppend current date]
    A -- No --> S
    DT --> S[DuckDuckGo Search\nGet URLs + snippets]
    S --> D{Need full article?}
    D -- Yes --> N4K[Newspaper4k\nExtract article text]
    D -- No --> R
    N4K --> F{Content sufficient?}
    F -- Yes --> R[GPT-4o Synthesizes\nFinal Response]
    F -- No --> SW[scrape_webpage\nRaw HTML text fallback]
    SW --> R
    R --> U([Stream to User])
```

---

## Setup

```bash
# Install dependencies
pip install -r Requirement.txt

# Set OpenAI key
echo OPENAI_API_KEY=sk-... > .env

# Run the web search agent
python Agent_with_WebSearch

# Run the basic agent
python basic.py
```

## Key Behaviors

- **Streaming output** — responses print token-by-token via `stream=True`
- **Tool call visibility** — `show_tool_calls=True` prints each tool invocation
- **Markdown output** — responses are formatted with headers and bullet points
- **Context safety** — `scrape_webpage` truncates content to 8000 chars to protect the LLM context window

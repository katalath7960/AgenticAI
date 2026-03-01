# ChromaDB RAG System

A Retrieval-Augmented Generation (RAG) application built with **ChromaDB Cloud**, **LangGraph**, **LangChain**, and **OpenAI**. It provides a Streamlit UI for ingesting documents and a FastAPI backend for answering questions using an agentic RAG pipeline with self-correction.

---

## Project Structure

```
ChromaDB/
├── chroma_client.py       # Shared ChromaDB Cloud client and LangChain wrappers
├── rag_agent.py           # LangGraph agentic RAG graph definition
├── api.py                 # FastAPI REST API (chat + streaming endpoints)
├── upload_documents.py    # Streamlit UI for document ingestion
├── requirements.txt       # Python dependencies
├── Dockerfile             # Single image for both services
├── docker-compose.yml     # Orchestrates API + Ingest UI containers
└── .dockerignore          # Excludes cache, secrets, and editor files
```

---

## File Descriptions

### `chroma_client.py`
Centralised module that owns all ChromaDB and LLM connections. Used by every other module.

| Export | Type | Description |
|---|---|---|
| `DEFAULT_COLLECTION` | `str` | Collection name from `CHROMA_COLLECTION` env var |
| `DEFAULT_TOP_K` | `int` | Number of docs to retrieve (from `CHROMA_TOP_K`) |
| `get_client()` | function | Cached `chromadb.CloudClient` instance |
| `get_embeddings()` | function | Cached `OpenAIEmbeddings` instance |
| `get_llm()` | function | Cached `ChatOpenAI` instance |
| `get_vectorstore(collection)` | function | Returns a `Chroma` LangChain vectorstore |

---

### `rag_agent.py`
Defines the LangGraph stateful RAG pipeline. The graph nodes are:

| Node | Description |
|---|---|
| `rewrite_query` | Rewrites the user question for better vector search retrieval |
| `retrieve` | Fetches top-k documents from ChromaDB |
| `grade_documents` | Grades each document for relevance; filters irrelevant ones |
| `generate` | Streams an answer using filtered docs as context |
| `grade_generation` | Checks if the answer is grounded in retrieved context |

Routing logic retries up to `MAX_RETRIES = 2` times when documents are irrelevant or the answer is hallucinated.

---

### `api.py`
FastAPI application exposing two endpoints:

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/chat` | Synchronous chat — returns full answer + sources |
| `POST` | `/chat/stream` | Server-Sent Events stream of answer tokens |

**Request body (`/chat`, `/chat/stream`):**
```json
{
  "message": "What is ChromaDB?",
  "collection": "edureka-session-demo"
}
```

**Run with:**
```bash
cd ChromaDB
uvicorn api:app --reload
```

---

### `upload_documents.py`
Streamlit web app for building the RAG index.

**Features:**
- Paste raw text directly
- Upload `.txt`, `.md`, or `.pdf` files
- Configure chunk size and overlap in the sidebar
- Choose the target ChromaDB collection

**Run with:**
```bash
streamlit run ChromaDB/upload_documents.py
```

---

### `requirements.txt`
| Package | Purpose |
|---|---|
| `fastapi` | REST API framework |
| `uvicorn[standard]` | ASGI server for FastAPI |
| `streamlit` | Document ingestion UI |
| `langgraph` | Agentic graph execution engine |
| `langchain` / `langchain-openai` / `langchain-chroma` | LangChain integrations |
| `langchain-text-splitters` | Document chunking |
| `chromadb` | ChromaDB Cloud client |
| `pydantic` | Data validation |
| `python-dotenv` | `.env` file loading |
| `pypdf` | PDF text extraction |

**Install:**
```bash
pip install -r ChromaDB/requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
# ChromaDB Cloud
CHROMA_API_KEY=your_chroma_api_key
CHROMA_TENANT=your_tenant_name
CHROMA_DATABASE=your_database_name
CHROMA_COLLECTION=edureka-session-demo   # optional, has default
CHROMA_TOP_K=4                           # optional, has default

# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini                 # optional, has default
OPENAI_EMBEDDINGS_MODEL=text-embedding-3-small  # optional, has default
```

---

## Diagrams

### 1. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        User                             │
└───────────────┬──────────────────┬──────────────────────┘
                │                  │
                ▼                  ▼
  ┌─────────────────────┐  ┌───────────────────────┐
  │  Streamlit UI        │  │  FastAPI (api.py)      │
  │  upload_documents.py │  │  POST /chat            │
  │                      │  │  POST /chat/stream     │
  └──────────┬──────────┘  └──────────┬────────────┘
             │                         │
             │ add_documents()         │ ainvoke / astream
             │                         ▼
             │             ┌───────────────────────┐
             │             │  LangGraph RAG Agent   │
             │             │     rag_agent.py        │
             │             └──────────┬────────────┘
             │                        │
             ▼                        ▼
  ┌──────────────────────────────────────────────┐
  │              chroma_client.py                │
  │  get_client() · get_embeddings() · get_llm() │
  └──────────┬───────────────────────┬───────────┘
             │                       │
             ▼                       ▼
  ┌────────────────────┐   ┌──────────────────────┐
  │  ChromaDB Cloud    │   │  OpenAI API           │
  │  (vector store)    │   │  Embeddings + Chat    │
  └────────────────────┘   └──────────────────────┘
```

---

### 2. Document Ingestion Flow

```
 User Input
 ┌──────────────────────┐
 │  Pasted Text / Files │  (.txt · .md · .pdf)
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │  RecursiveCharacter  │  chunk_size (default 900)
 │  TextSplitter        │  chunk_overlap (default 150)
 └──────────┬───────────┘
            │  List[Document] with metadata
            ▼
 ┌──────────────────────┐
 │  Chroma.add_documents│  OpenAI embeddings generated per chunk
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │  ChromaDB Cloud      │  Stored in named collection
 └──────────────────────┘
```

---

### 3. LangGraph RAG Agent — Graph Flow

```
         START
           │
           ▼
   ┌───────────────┐
   │ rewrite_query │  LLM rewrites question for better retrieval
   └───────┬───────┘
           │
           ▼
   ┌───────────────┐
   │    retrieve   │  Fetch top-k docs from ChromaDB
   └───────┬───────┘
           │
           ▼
   ┌───────────────────┐
   │  grade_documents  │  LLM grades each doc: relevant? yes/no
   └───────┬───────────┘
           │
     ┌─────┴──────────────────────────┐
     │ relevant docs found?           │
     │ OR retry_count >= 2?           │
     │                                │
    YES                              NO
     │                                │
     ▼                                └──────────────┐
 ┌──────────┐                                        │
 │ generate │  Stream answer using context           │
 └────┬─────┘                                        │
      │                                              │
      ▼                                              │
 ┌────────────────┐                                  │
 │ grade_generation│  LLM checks: answer grounded?   │
 └────┬───────────┘                                  │
      │                                              │
 ┌────┴────────────────────────┐                     │
 │ grounded?                   │                     │
 │ OR retry_count >= 2?        │                     │
 │                             │                     │
YES                           NO                     │
 │                             │                     │
 ▼                             └──────► rewrite_query┘
END                                    (retry loop)
```

**Retry cap:** `MAX_RETRIES = 2` — the agent will rewrite and re-retrieve at most twice before returning its best answer.

---

### 4. API Request Flow (`/chat`)

```
  Client
    │
    │  POST /chat  { "message": "...", "collection": "..." }
    ▼
  FastAPI (api.py)
    │
    │  get_graph(collection)
    ▼
  LangGraph graph.ainvoke({"question": message})
    │
    │  (runs full RAG graph — see diagram 3)
    ▼
  { "answer": "...", "sources": [...] }
    │
    ▼
  Client  ◄── JSON response
```

### 5. API Request Flow (`/chat/stream`)

```
  Client
    │
    │  POST /chat/stream  { "message": "...", "collection": "..." }
    ▼
  FastAPI (api.py)
    │
    │  get_graph(collection)
    ▼
  LangGraph graph.astream(..., stream_mode="custom")
    │
    │  generate node calls get_stream_writer()
    │  and emits token chunks during LLM streaming
    ▼
  Server-Sent Events
    data: {"type": "token", "content": "Hello"}
    data: {"type": "token", "content": " world"}
    ...
    data: [DONE]
    │
    ▼
  Client  ◄── SSE stream
```

---

## Docker Deployment (Docker Desktop)

### Docker files in this folder

| File | Purpose |
|---|---|
| `Dockerfile` | Builds a single `python:3.11-slim` image used by both services |
| `docker-compose.yml` | Defines and orchestrates the two containers |
| `.dockerignore` | Prevents `__pycache__`, `.env`, `.venv`, and editor files from entering the image |

---

### Prerequisites

#### 1. Docker Desktop
Download and install from https://www.docker.com/products/docker-desktop/

#### 2. WSL2 (Windows only — required by Docker Desktop)
Docker Desktop on Windows uses WSL2 as its Linux kernel backend.
Check if WSL2 is installed:
```powershell
wsl --status
```
If not installed, run this in an **admin PowerShell**:
```powershell
wsl --install
```
Then **restart your PC**. After restart, Ubuntu will open once to finish setup (create a username/password).

#### 3. `.env` file
Place a `.env` file in the **project root** (`Python/.env`) — one level above the `ChromaDB/` folder.
The `docker-compose.yml` references it as `../.env`.

```env
CHROMA_API_KEY=your_chroma_api_key
CHROMA_TENANT=your_tenant_name
CHROMA_DATABASE=your_database_name
OPENAI_API_KEY=your_openai_api_key
```

> **Note:** The env var must be named `OPENAI_API_KEY` (not `OPEN_API_KEY`).

---

### Dockerfile — explained

```dockerfile
FROM python:3.11-slim AS base
```
Uses the official slim Python 3.11 image (~50 MB) as the base.

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
```
Installs `curl` (needed by the container healthcheck) and cleans up apt cache to keep the image small.

```dockerfile
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```
Sets `/app` as the working directory, copies only `requirements.txt` first so pip install is cached as a separate layer — rebuilds are fast when only source files change.

```dockerfile
COPY . .
```
Copies all application source files (`api.py`, `rag_agent.py`, `chroma_client.py`, `upload_documents.py`) into `/app`.

```dockerfile
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```
Default command runs the FastAPI server. The Streamlit service overrides this in `docker-compose.yml`.

---

### docker-compose.yml — explained

```yaml
x-build: &common-build
  build:
    context: .
    dockerfile: Dockerfile
  env_file:
    - ../.env
  restart: unless-stopped
```
A YAML anchor (`&common-build`) shared by both services — avoids repetition. Both services:
- Build from the same `Dockerfile` in the current (`ChromaDB/`) directory
- Load environment variables from `../.env` (project root)
- Restart automatically unless manually stopped

#### Service: `api` (FastAPI)

```yaml
api:
  <<: *common-build
  container_name: chromadb-api
  command: uvicorn api:app --host 0.0.0.0 --port 8000 --reload
  ports:
    - "8000:8000"
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 10s
```
- Runs `uvicorn` with `--reload` so code changes inside the container are picked up automatically
- Exposes port `8000` on the host
- Healthcheck polls `GET /` every 30 s; marked healthy after 1 passing check

#### Service: `ingest` (Streamlit)

```yaml
ingest:
  <<: *common-build
  container_name: chromadb-ingest
  command: streamlit run upload_documents.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
  ports:
    - "8501:8501"
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 15s
```
- `--server.headless true` suppresses the "open browser" prompt inside the container
- `--server.address 0.0.0.0` makes Streamlit accessible from outside the container
- Healthcheck uses Streamlit's built-in `/_stcore/health` endpoint

---

### Deployment diagram

```
Docker Desktop
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  ┌────────────────────────┐  ┌────────────────────────┐  │
│  │   chromadb-api         │  │   chromadb-ingest       │  │
│  │   FastAPI + uvicorn    │  │   Streamlit             │  │
│  │   localhost:8000       │  │   localhost:8501        │  │
│  └───────────┬────────────┘  └───────────┬────────────┘  │
│              │                            │               │
│              └──────────┬─────────────────┘               │
│                         │  (same Docker image)            │
│              ┌──────────▼──────────┐                      │
│              │   python:3.11-slim  │                      │
│              │   + curl            │                      │
│              │   + requirements    │                      │
│              └─────────────────────┘                      │
└──────────────────────────────────────────────────────────┘
                         │
              ┌──────────▼──────────┐    ┌──────────────────┐
              │   ChromaDB Cloud    │    │   OpenAI API      │
              │   (external)        │    │   (external)      │
              └─────────────────────┘    └──────────────────┘
```

---

### Build and run

```bash
# From inside the ChromaDB/ folder:
cd ChromaDB

# Build images and start both containers (foreground — see live logs)
docker compose up --build

# Run in the background (detached mode)
docker compose up --build -d
```

| Service | URL |
|---|---|
| FastAPI (chat API) | http://localhost:8000 |
| FastAPI docs (Swagger UI) | http://localhost:8000/docs |
| FastAPI docs (ReDoc) | http://localhost:8000/redoc |
| Streamlit ingest UI | http://localhost:8501 |

---

### Useful commands

```bash
# Show running containers and their health
docker compose ps

# Tail live logs from both services
docker compose logs -f

# Tail logs from one service only
docker compose logs -f api
docker compose logs -f ingest

# Exec into a running container (for debugging)
docker exec -it chromadb-api bash
docker exec -it chromadb-ingest bash

# Stop containers (keep images and volumes)
docker compose down

# Stop and remove built images
docker compose down --rmi all

# Rebuild and restart after code changes
docker compose up --build -d

# Check resource usage (CPU/memory per container)
docker stats
```

---

### Docker Desktop GUI

After running `docker compose up --build -d`, open **Docker Desktop** and navigate to the **Containers** tab. You will see:

```
chromadb-api      Running   healthy   0.0.0.0:8000->8000/tcp
chromadb-ingest   Running   healthy   0.0.0.0:8501->8501/tcp
```

- Green dot = healthy
- Click a container → **Logs** tab to see live output
- Click a container → **Inspect** tab to view env vars, mounts, and network settings
- Click a container → **Terminal** tab to open an interactive shell inside it

---

### Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `Docker Desktop is unable to start` | WSL2 not installed | Run `wsl --install` in admin PowerShell, then restart |
| `docker: command not found` | Docker not in PATH | Use full path: `"C:\Program Files\Docker\Docker\resources\bin\docker.exe"` or restart terminal after Docker Desktop install |
| `Attribute "app" not found in module "api"` | uvicorn run from wrong directory | Always run from inside `ChromaDB/` folder |
| `No module named 'chroma_client'` | Wrong working directory or filename case | Ensure file is named `chroma_client.py` (lowercase) and run from `ChromaDB/` |
| Container unhealthy | Missing env vars | Check `.env` file exists one level up and contains all required keys |
| `OPENAI_API_KEY` error | Typo in `.env` | Ensure the key is `OPENAI_API_KEY` not `OPEN_API_KEY` |
| Port already in use | Another process on 8000 or 8501 | Stop the conflicting process or change port mapping in `docker-compose.yml` |

---

## Quick Start (local, no Docker)

```bash
# 1. Install dependencies
pip install -r ChromaDB/requirements.txt

# 2. Set up environment variables
cp .env.example .env   # then fill in your keys

# 3. Ingest documents
streamlit run ChromaDB/upload_documents.py

# 4. Start the API server (in a separate terminal)
cd ChromaDB
uvicorn api:app --reload

# 5. Query the API
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What did I upload?"}'
```

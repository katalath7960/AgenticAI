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
└── requirements.txt       # Python dependencies
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

## Quick Start

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

# HorizonByte : Complete Project Guide

### 1. 🔭 Project Overview

[![Production Link](https://img.shields.io/badge/MVP-HorizonByte_on_render-green)](https://horizonbyte.onrender.com)

**HorizonByte** is a full-stack, document-aware AI chatbot built from scratch without any high-level AI framework like LangChain or LlamaIndex. It implements a custom **Retrieval-Augmented Generation (RAG)** pipeline using:

- **FastAPI** (Python) as the backend web server
- **FAISS** as the in-memory vector database
- **Cloudflare Workers AI (Llama 3.3 70B)** for LLM inference
- **HuggingFace (`sentence-transformers/all-MiniLM-L6-v2`)** for local, zero-cost embedding generation
- **PyMuPDF** for PDF text extraction
- A custom recursive text chunker (no LangChain dependency)
- A single-page **Cyber-Brutalist** frontend (HTML + Tailwind CSS + Vanilla JS)
- An additional **Hinglish-to-English Rephrase Engine** powered by Llama 3.3

It allows users to chat with their documents, extract insights, and refine their writing seamlessly. The app is deployed as a monolith on **Render** — the FastAPI server serves both the API and the frontend HTML.

---

### 2. 🏗️ Project Structure (Quick Reference)

```
HorizonByte/
├── backend/
│   ├── main.py              # FastAPI app, all routes
│   └── rag/
│       ├── ingestion.py     # PDF/TXT → raw text
│       ├── chunking.py      # Recursive text splitter
│       ├── vector_store.py  # FAISS wrapper + embeddings
│       ├── memory.py        # TTL-based session memory
│       └── llm.py           # LLM calls: chat, suggestions, rephrase
├── frontend/
│   └── index.html           # Entire frontend (654 lines)
├── data/                    # Uploaded documents (ephemeral)
├── requirements.txt         # Python dependencies
└── README.md
```

---

### 3. ⚙️ Local Setup & Installation

#### 1. Clone the repository
```bash
git clone https://github.com/your-username/HorizonByte.git
cd HorizonByte
```

#### 2. Set up a Python Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables
You will need a Google Gemini API key to run the models.
Ensure your environment has the API key set. You can set it in your terminal before running:
```bash
# On Windows
set GEMINI_API_KEY=your_api_key_here
# On macOS/Linux
export GEMINI_API_KEY=your_api_key_here
```
*(Alternatively, you can create a `.env` file if you have configured python-dotenv).*

#### 5. Run the Application
Start the FastAPI server using Uvicorn:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 6. Access the App
Open your web browser and navigate to:
`http://localhost:8000`

---

### 4. 🛠️ Tech Stack Summary

| Layer | Technology | Why |
|---|---|---|
| **Web Framework** | FastAPI + Uvicorn | Fast, async, type-safe Python APIs |
| **LLM** | Llama 3.3 | SOTA reasoning, good at instruction following |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | Local, 384-dimensional vectors |
| **Vector DB** | FAISS (in-memory) | Zero-cost, in-process, low latency |
| **Document Parsing** | PyMuPDF (`fitz`) | Fast PDF text extraction |
| **Frontend** | HTML + Tailwind CSS + Vanilla JS | Zero build step, single-file |
| **Deployment** | Render (PaaS) | Easy Git-based deploy |


---

### 5. 🗺️ High-Level Architecture

```
User's Browser (index.html + Vanilla JS)
        |
        | HTTP (fetch API)
        v
  FastAPI Server (backend/main.py)
        |
  ┌─────┴──────────────────────────────────┐
  │  /api/upload  /api/chat  /api/rephrase  │
  └──┬────────────┬──────────┬─────────────┘
     │            │          │
  [ingestion.py] [memory.py] [llm.py]
  [chunking.py]              [vector_store.py]
     │
  [data/] (uploaded PDF/TXT files)
```

#### Data Flow for a Chat Query:
```
User types query
    → POST /api/chat
    → Retrieve chat history from memory (TTL-filtered)
    → Embed query locally using HuggingFace (MiniLM)
    → FAISS similarity_search → top-3 relevant chunks
    → Build prompt (persona + context + history + query)
    → Cloudflare Llama 3.3 generates response
    → Save user+bot messages to memory
    → Return response JSON to frontend
```

#### Data Flow for Document Upload:
```
User uploads PDF/TXT
    → POST /api/upload
    → PyMuPDF extracts raw text
    → recursive_character_splitter → list of chunks
    → HuggingFace embeds all chunks locally
    → FAISS index stores embeddings (chunk_map stores text)
    → First 1000 chars saved as document summary in memory
```

---

### 6. 📁 File-by-File Breakdown

#### `backend/main.py` — The Application Entry Point
The FastAPI app with 4 routes:
| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Serves `frontend/index.html` (monolith pattern) |
| `/api/upload` | POST | Ingests a document into the RAG pipeline |
| `/api/chat` | POST | Handles a user query using RAG + LLM |
| `/api/suggestions` | GET | Returns 4 AI-generated follow-up prompts |
| `/api/rephrase` | POST | Translates Hinglish text to English |

**Key Design Decision:** The server is a monolith — it serves both the API and the frontend from a single process. This simplifies deployment (no CORS needed, single `uvicorn` command).

---

#### `backend/rag/ingestion.py` — Document Loading
- Uses **PyMuPDF (`fitz`)** to read PDF files page-by-page
- Handles `.txt` files with UTF-8 encoding
- Cleans text: removes null bytes (`\x00`), collapses multiple whitespaces using `re.sub(r'\s+', ' ', text)`

---

#### `backend/rag/chunking.py` — Recursive Character Text Splitter
This is the most algorithmically interesting file — a **custom implementation** of LangChain's `RecursiveCharacterTextSplitter`.

**Algorithm:**
1. Try to split by `\n\n` (paragraphs)
2. If chunks are still too large, try `\n` (lines)
3. Then by space (` `)
4. Final fallback: split by character count

**With Overlap:** When starting a new chunk, it carries forward the last `chunk_overlap=250` characters from the previous chunk. This prevents context from being lost at chunk boundaries.

**Why this matters:**
> "I built the chunker from scratch to avoid the LangChain dependency. The recursive approach ensures semantic coherence — it tries to break on natural language boundaries first, only resorting to hard character splits as a last resort."

---

#### `backend/rag/vector_store.py` — FAISS Vector Store
A class (`VectorStore`) wrapping the FAISS index:
- **Index type:** `faiss.IndexFlatL2` — brute-force L2 (Euclidean) distance search
- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (Local, 384-dimensional vectors)
- **`chunk_map`:** A Python dict mapping FAISS internal index IDs → original chunk text
- **`add_chunks()`:** Embeds chunks with `task_type="retrieval_document"` and adds to FAISS
- **`similarity_search()`:** Embeds the query with `task_type="retrieval_query"`, searches FAISS for top-k=3 nearest neighbors

**Why HuggingFace Embeddings?**
> "Using `sentence-transformers` locally eliminates the need for a third-party embedding API (like Google Llama 3.3). This results in zero costs for embedding, drastically lower latency, and 100% data privacy since the vectors are generated inside the app container."

---

#### `backend/rag/memory.py` — Session-Based Chat Memory
A `ChatMemory` class that stores per-session chat history **in-memory** (a Python dict):
- **TTL (Time-To-Live):** Messages older than 5 minutes (300 seconds) are automatically expired
- **`add_message()`** → stores `{role, text, timestamp}`
- **`get_context()`** → filters expired messages and returns a formatted string of recent history
- Also stores **document summaries** per session for the suggestions endpoint

**Limitation to know:**
> "The memory is in-process — if the server restarts, all history is lost. For production, you'd replace this with Redis for persistent, distributed session storage."

---

#### `backend/rag/llm.py` — LLM Integration (3 Functions)

#### 1. `generate_response()` — The Core RAG Response
Builds a structured prompt:
```
You are HorizonByte... Your personality is {personality_desc}.
Answer based on provided context. If insufficient, say so.

DOCUMENT CONTEXT: {retrieved_chunks joined by ---}
RECENT CHAT HISTORY: {memory.get_context()}
USER QUERY: {query}
AI RESPONSE:
```
- Uses `@cf/meta/llama-3.3-70b-instruct-fp8-fast`
- Supports 3 personas: `cyber-brutalist`, `verbose`, `casual`

#### 2. `generate_suggestions()` — Dynamic Follow-up Prompts
- Sends document summary + chat history to Llama 3.3
- Asks for exactly 4 suggestions as a **JSON array** (under 40 chars each)
- Has fallback hardcoded suggestions in case JSON parsing fails

#### 3. `rephrase_text()` — Hinglish-to-English
- Takes a text and a tone (`Professional`, `Casual`, `Friendly`, `Direct`)
- Prompts Llama 3.3 to translate/rephrase to English in that tone
- Returns only the final English string

---

### `frontend/index.html` — The Entire Frontend (654 lines)
A single HTML file with:
- **Tailwind CSS** (via CDN) with a custom config (Cyber-Brutalist color tokens, Space Mono font, 0px border radius)
- **CRT Screen effects:** CSS keyframe `scanline` animation, phosphor glow (`text-shadow`), vignette via `radial-gradient`
- **Three tabs:** Terminal (main chat), About (modal), Config (modal)
- **Config system:** Saves to `localStorage` (model, persona, chunk size, theme). Theme switching uses CSS `hue-rotate` filter — elegant one-liner to shift the entire color scheme
- **Vanilla JS:** All API calls use the native `fetch()` API with `FormData`

---

### 7. 🔑 Core Concepts Explained 

#### ❓ What is RAG (Retrieval-Augmented Generation)?

**The Problem:** LLMs are trained on general data and have a knowledge cutoff. They hallucinate when asked about private/specific documents.

**The Solution (RAG):**
1. **Index:** Break your document into chunks → embed as vectors → store in a vector DB
2. **Retrieve:** When a query comes in, embed the query → find the most semantically similar chunks
3. **Augment:** Inject those chunks into the LLM's prompt as "context"
4. **Generate:** LLM answers based on the grounded context, not just its training data

> **Analogy:** RAG is like an open-book exam. Instead of memorizing everything, you give the AI the relevant pages from the textbook right before it answers.

---

#### ❓ What is a Vector Embedding?

A vector embedding is a numerical representation of text (an array of floats, e.g., 768 numbers) that captures **semantic meaning**. Texts with similar meaning have embeddings that are close together in vector space.

- `"dog"` and `"puppy"` will have similar embeddings
- `"dog"` and `"quantum physics"` will be far apart

---

#### ❓ What is FAISS and why use it?

**FAISS (Facebook AI Similarity Search)** is an open-source library for efficient **approximate nearest-neighbor search** in high-dimensional vector spaces.

- `IndexFlatL2`: Exact brute-force search using Euclidean (L2) distance — fine for small document collections
- In production, you'd use `IndexIVFFlat` or `IndexHNSW` for faster approximate search on millions of vectors

**Why not use Pinecone/Weaviate?**
> "FAISS runs entirely in-process, no external service, no cost, no network latency. For a single-server deployment, it's the simplest and fastest option."

---

#### ❓ What is Chunking and why is it needed?

LLMs have a **context window limit** (max tokens per prompt). You can't feed a 200-page PDF into a single prompt.

**Chunking** solves this by:
1. Breaking the document into overlapping segments (`chunk_size=1000 chars`, `overlap=150 chars`)
2. Only retrieving the **most relevant** 3-5 chunks for each query

**Why overlap?** If a key sentence falls at the boundary between two chunks, overlap ensures it appears in at least one of them. Without overlap, you'd lose context at every boundary.

---

#### ❓ What is FastAPI and why use it?

FastAPI is a modern Python web framework for building APIs:
- **Async by default** — non-blocking I/O for high concurrency
- **Automatic data validation** using Python type hints + Pydantic
- **Automatic OpenAPI docs** at `/docs`
- Much faster than Flask for API-heavy workloads

**Uvicorn** is the ASGI server that runs FastAPI (like Gunicorn runs Flask).

---

#### ❓ What is the Hinglish Rephrase Engine?

A two-step UX workflow:
1. User types thoughts naturally in Hinglish (e.g., *"mujhe professional email likhni hai boss ko about leave"*)
2. User clicks the translate icon → selects tone (Professional/Casual/etc.)
3. Llama 3.3 rephrases it into clean English, which is placed back in the input box
4. User reviews and sends to the chat

This is a **writing assistant** feature — useful for non-native English speakers who think in their native language.

---

#### ❓ How does session management work?

Currently, there's a **single hardcoded session ID** (`SID-77-B-0X42`) for all users. This is a simplification for the MVP.

In a multi-user production system, you'd:
1. Generate a unique UUID per browser session
2. Store in `sessionStorage` / `localStorage` on the client
3. Pass it with every request
4. Use Redis on the backend to store session data persistently

---

#### ❓ Explain the Deployment Architecture on Render

- Single **Python Web Service** on Render
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn backend.main:app --host 0.0.0.0 --port 10000`
- Environment variable: `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`
- The app is a **monolith** — FastAPI serves the `frontend/index.html` at the root `/` route
- **Limitation:** Render's free tier uses an **ephemeral filesystem** — uploaded files and the FAISS index reset on every restart/redeploy

---

#### ❓ What is the Cloudflare Workers AI integration?
Instead of a standard LLM API, HorizonByte uses Cloudflare's serverless AI inference. This reduces complexity and latency. My integration uses the `/run/` REST endpoint with a 30-second timeout, designed to bypass local GPU requirements.

---

#### ❓ How did you solve the Render memory limits?
1. **CPU-only PyTorch:** Used `--extra-index-url https://download.pytorch.org/whl/cpu` in `requirements.txt` to avoid bulky CUDA binaries.
2. **Local Model Selection:** Used `all-MiniLM-L6-v2` (~80MB RAM usage).
3. **Index Reset:** Used `vector_store.reset_store()` to clear RAM when a new document is uploaded.

---

### 8. 💡 What Makes This Project Stand Out

1. **No LangChain / LlamaIndex** — Built the RAG pipeline from scratch (chunker, vector store, memory). Shows genuine understanding of the underlying concepts.

2. **Custom Recursive Chunker** — Mirrors the algorithm used in production frameworks but without the dependency.

3. **Dual Embedding Strategy** — Uses `task_type="retrieval_document"` for indexing and `task_type="retrieval_query"` for querying. This is best practice for better retrieval accuracy.

4. **Monolith Deployment Pattern** — Clever use of FastAPI to serve both the API and the static frontend from one process — no separate frontend server, no CORS issues.

5. **Hinglish Engine** — A unique, India-specific feature that addresses a real language barrier for millions of users.

6. **TTL-based Memory** — Automatic context expiration prevents prompt bloat on long sessions.

---

### 9. ❓ Likely Interview Questions & Model Answers

**Q: What is the difference between RAG and fine-tuning?**
> Fine-tuning updates the model's weights with new training data — expensive, time-consuming, and the model "bakes in" knowledge which can go stale. RAG keeps the base model frozen and injects fresh, specific context at inference time. RAG is cheaper, faster to update, and always uses the latest document.

**Q: Why did you choose FAISS over a managed vector database like Pinecone?**
> For this project's scale, FAISS is ideal — no external service cost, zero network latency (it's in-process), and simple to set up. Pinecone would be better at millions of vectors with persistent storage, multi-user scenarios, and production scale.

**Q: How would you make HorizonByte multi-user?**
> Generate a UUID per browser tab, store in `sessionStorage`. Pass it with every request. Replace the in-memory `ChatMemory` dict with Redis for persistent, cross-process session storage. Also store the FAISS index per-session or use a database-backed vector store like pgvector.

**Q: What happens if the user asks about something not in the document?**
> The similarity search returns the top-3 chunks regardless of relevance. The LLM prompt explicitly instructs: *"If the context does not contain the answer, state that there is insufficient data."* So the model should decline to hallucinate.

**Q: What is chunk overlap and why is it important?**
> If a critical piece of information spans two adjacent chunks (at the boundary), without overlap you'd have half the context in each. With `overlap=250 chars`, the end of the previous chunk is repeated at the start of the next — ensuring boundary information is always captured in full.

**Q: How does the Hinglish rephrase work technically?**
> It's a zero-shot prompt engineering task. The Llama 3.3 model is instructed with a precise prompt: take this Hinglish text, return ONLY the rephrased English version in the specified tone. No training or fine-tuning was needed.

**Q: How does theme switching work in the frontend?**
> Instead of duplicating all CSS color variables for each theme, I use a CSS `hue-rotate()` filter on the `<body>` element. The base color is Cobalt Blue (`#007FFF`), and each theme simply rotates the hue by a specific degree. This changes all colors on the page simultaneously with a single CSS property.


### 📄 License
This project is for educational and personal use. Build by HIMANSHU BANSAL

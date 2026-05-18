from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
import os
import shutil
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_forwarded_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

from backend.rag.ingestion import load_document
from backend.rag.chunking import recursive_character_splitter
from backend.rag.vector_store import vector_store
from backend.rag.memory import memory
from backend.rag.llm import generate_response, generate_suggestions, rephrase_text, rerank_chunks

app = FastAPI()

limiter = Limiter(key_func=get_forwarded_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# Make data directory
os.makedirs("data", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...), 
    session_id: str = Form("SID-77-B-0X42"),
    chunk_size: int = Form(1000)
):
    
    # Clear old data from memory so new chunk size applies to fresh state
    vector_store.index.reset() 
    vector_store.chunk_map.clear()

    if not file.filename.endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")
        
    file_path = f"data/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:

        # 0. VectorStore is fresh for the new document
        vector_store.reset_store()

        # 1. Ingest
        raw_text = load_document(file_path)
        
        # 2. Chunk
        chunks = recursive_character_splitter(raw_text, chunk_size=chunk_size)
        
        # 3. Vector Store
        vector_store.add_chunks(chunks)
        
        # 4. Save summary for dynamic prompts
        memory.set_document_summary(session_id, raw_text[:1000])
        
        return {"message": f"Successfully ingested {file.filename} into {len(chunks)} chunks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
@limiter.limit("10/minute")
async def chat(
    request: Request,
    query: str = Form(...), 
    session_id: str = Form("SID-77-B-0X42"),
    model: str = Form("@cf/meta/llama-3.3-70b-instruct-fp8-fast"),  # Updated default
    persona: str = Form("cyber-brutalist")
):
    # 1. Retrieve history
    chat_history = memory.get_context(session_id)
    
    # 2. Retrieve vector context
    retrieved_chunks = vector_store.similarity_search(query, k=10)

    if len(retrieved_chunks) > 3:
        final_context = rerank_chunks(query, retrieved_chunks)
    else:
        final_context = retrieved_chunks
    
    # 3. Generate Response
    response_text = generate_response(query, final_context, chat_history, model_name=model, persona=persona)
    
    # 4. Save to memory
    memory.add_message(session_id, "user", query)
    memory.add_message(session_id, "assistant", response_text)
    
    return {
        "response": response_text,
        "retrieved_chunks_count": len(retrieved_chunks)
    }

@app.get("/api/suggestions")
async def get_suggestions(
    session_id: str = Form("SID-77-B-0X42"),
    model: str = Form("@cf/meta/llama-3.3-70b-instruct-fp8-fast"),  # Updated default
):
    summary = memory.get_document_summary(session_id)
    history = memory.get_context(session_id)
    suggestions = generate_suggestions(summary, history, model_name=model)
    return {"suggestions": suggestions}

@app.post("/api/rephrase")
async def rephrase(
    text: str = Form(...),
    tone: str = Form("Professional"),
    model: str = Form("@cf/meta/llama-3.3-70b-instruct-fp8-fast"),  # Updated default
):
    rephrased = rephrase_text(text, tone, model_name=model)
    return {"rephrased_text": rephrased}
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

@app.get("/health")
async def health_check():
    """Lightweight endpoint for UptimeRobot."""
    return {"status": "ok"}
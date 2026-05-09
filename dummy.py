"""
backend.py — FastAPI server for RAG Chatbot
Endpoints: /chat, /history/{session_id}, /admin/logs,
           /admin/upload_pdf, /admin/clear_knowledge, /admin/kb_status
"""

import os
import shutil
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

# LangChain / Ollama / ChromaDB
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama
from langchain_classic.chains.retrieval_qa.base import RetrievalQA
from langchain_classic.prompts import PromptTemplate

from database import ChatHistory, KnowledgeBase, get_db, init_db, SessionLocal

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
CHROMA_DIR   = "./chroma_db"          # persists until admin clears it
UPLOAD_DIR   = "./uploaded_pdfs"      # all uploaded PDFs stored here
OLLAMA_BASE_URL = "http://localhost:11434"
ADMIN_TOKEN  = "Admin123"

Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# Broken-English-tolerant prompt
# ─────────────────────────────────────────────
PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are a friendly and helpful restaurant assistant.\n"
        "The user's question may contain spelling mistakes, grammar errors, "
        "or broken English — always try your best to understand their intent "
        "and give a clear, helpful answer.\n\n"
        "Rules:\n"
        "1. If the question is unclear, make a reasonable assumption and answer it.\n"
        "2. Use only the context below to answer. Do not make up information.\n"
        "3. If the answer is not in the context, say politely that you don't have "
        "   that information and suggest they ask the staff directly.\n"
        "4. Keep answers concise and friendly.\n\n"
        "Context:\n{context}\n\n"
        "User question: {question}\n\n"
        "Answer:"
    )
)

# ─────────────────────────────────────────────
# Global RAG state
# ─────────────────────────────────────────────
rag_chain: Optional[RetrievalQA] = None
current_pdf_name: Optional[str]  = None


def build_rag_chain(pdf_path: str, pdf_name: str) -> Optional[RetrievalQA]:
    """
    Load a PDF, create/update embeddings in the PERSISTENT ChromaDB,
    and return a RetrievalQA chain.
    The vector store is NOT deleted before rebuilding — use clear_knowledge
    for that.  This means a second upload simply replaces the collection.
    """
    global current_pdf_name
    try:
        loader = PyPDFLoader(pdf_path)
        docs   = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks   = splitter.split_documents(docs)

        embeddings = OllamaEmbeddings(model="all-minilm:l6-v2")

        # Always wipe old chroma data so the new PDF is the sole source
        if os.path.exists(CHROMA_DIR):
            shutil.rmtree(CHROMA_DIR)
            os.makedirs(CHROMA_DIR, exist_ok=True)
            print(f"[Build] Cleared old vector store, rebuilding from: {pdf_name}")

        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_DIR,
            collection_name="kb_collection",
        )
        print(f"[Build] Stored {len(chunks)} chunks in persistent vector store.")

        llm = ChatOllama(
            model="gemma:2b",
            temperature=0.3,
            num_predict=150,          # slightly longer for better answers
        )

        chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
            chain_type_kwargs={"prompt": PROMPT_TEMPLATE},
            return_source_documents=False,
        )

        current_pdf_name = pdf_name

        # Persist metadata to DB
        db = SessionLocal()
        try:
            db.query(KnowledgeBase).delete()
            db.add(KnowledgeBase(
                filename=pdf_name,
                filepath=pdf_path,
                uploaded_at=datetime.utcnow(),
                is_active=True,
            ))
            db.commit()
        finally:
            db.close()

        return chain

    except Exception as e:
        print(f"[Build] Error building RAG chain: {e}")
        return None


def load_existing_chain() -> Optional[RetrievalQA]:
    """
    On startup, if ChromaDB already has data (from a previous session),
    reload the chain so the bot is immediately ready without re-upload.
    """
    try:
        chroma_files = list(Path(CHROMA_DIR).rglob("*.bin")) + \
                       list(Path(CHROMA_DIR).rglob("*.parquet")) + \
                       list(Path(CHROMA_DIR).rglob("chroma.sqlite3"))
        if not chroma_files:
            return None

        embeddings = OllamaEmbeddings(model="all-minilm:l6-v2")
        vector_store = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings,
            collection_name="kb_collection",
        )
        if vector_store._collection.count() == 0:
            return None

        llm = ChatOllama(model="gemma:2b", temperature=0.3, num_predict=150)

        chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
            chain_type_kwargs={"prompt": PROMPT_TEMPLATE},
            return_source_documents=False,
        )
        print("[Startup] Reloaded existing vector store from disk.")
        return chain

    except Exception as e:
        print(f"[Startup] Could not reload existing chain: {e}")
        return None


# ─────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_chain, current_pdf_name
    init_db()
    print("[Startup] Database initialised.")

    # Try to reload the last known PDF name from DB
    db = SessionLocal()
    try:
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True).first()
        if kb:
            current_pdf_name = kb.filename
    finally:
        db.close()

    # Try to reload the persisted vector store
    rag_chain = load_existing_chain()
    if rag_chain:
        print(f"[Startup] RAG chain ready (PDF: {current_pdf_name or 'unknown'}).")
    else:
        print("[Startup] No existing knowledge base found. "
              "Upload a PDF via the Admin Panel to activate the chatbot.")
    yield


# ─────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────
app = FastAPI(title="Restaurant Chatbot API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    timestamp: str


# ─────────────────────────────────────────────
# Auth helper
# ─────────────────────────────────────────────
def verify_admin(x_admin_token: str = Header(...)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden: invalid admin token")


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "RAG Chatbot API is running.",
        "kb_loaded": rag_chain is not None,
        "kb_pdf": current_pdf_name,
    }


@app.get("/admin/kb_status", dependencies=[Depends(verify_admin)])
def kb_status():
    """Returns the current knowledge-base status."""
    chroma_exists = os.path.exists(CHROMA_DIR) and bool(
        list(Path(CHROMA_DIR).rglob("chroma.sqlite3"))
    )
    return {
        "kb_loaded": rag_chain is not None,
        "current_pdf": current_pdf_name,
        "vector_store_on_disk": chroma_exists,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    if rag_chain is None:
        raise HTTPException(
            status_code=503,
            detail="RAG chain not initialised. Upload a PDF via the Admin Panel."
        )

    result = rag_chain.invoke({"query": req.message})
    answer = result.get("result", "I'm sorry, I couldn't find an answer.")

    ts = datetime.utcnow()
    db.add(ChatHistory(session_id=req.session_id, role="user",
                       content=req.message, timestamp=ts))
    db.add(ChatHistory(session_id=req.session_id, role="assistant",
                       content=answer, timestamp=ts))
    db.commit()

    return ChatResponse(
        session_id=req.session_id,
        answer=answer,
        timestamp=ts.isoformat()
    )


@app.get("/history/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.timestamp.asc())
        .all()
    )
    return [
        {
            "id": r.id,
            "session_id": r.session_id,
            "role": r.role,
            "content": r.content,
            "timestamp": r.timestamp.isoformat()
        }
        for r in rows
    ]


@app.get("/admin/logs", dependencies=[Depends(verify_admin)])
def admin_logs(db: Session = Depends(get_db)):
    rows = (
        db.query(ChatHistory)
        .order_by(ChatHistory.timestamp.desc())
        .limit(500)
        .all()
    )
    return [
        {
            "id": r.id,
            "session_id": r.session_id,
            "role": r.role,
            "content": r.content,
            "timestamp": r.timestamp.isoformat()
        }
        for r in rows
    ]


@app.post("/admin/upload_pdf", dependencies=[Depends(verify_admin)])
async def upload_pdf(file: UploadFile = File(...)):
    global rag_chain

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Save the PDF permanently in UPLOAD_DIR
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

    if not os.path.exists(save_path) or os.path.getsize(save_path) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty or could not be saved.")

    file_size = os.path.getsize(save_path)
    print(f"[Admin] Saved PDF: {save_path} ({file_size} bytes)")
    print(f"[Admin] Building RAG chain…")

    new_chain = build_rag_chain(save_path, file.filename)
    if new_chain is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to build RAG chain from PDF. Check server logs."
        )

    rag_chain = new_chain
    print("[Admin] RAG chain updated successfully.")

    return {
        "status": "success",
        "filename": file.filename,
        "file_size": file_size,
        "message": (
            f"✅ Knowledge base updated from '{file.filename}'. "
            "The chatbot is ready to answer questions."
        ),
    }


@app.post("/admin/clear_knowledge", dependencies=[Depends(verify_admin)])
async def clear_knowledge():
    """Permanently wipe the vector store and PDF metadata."""
    global rag_chain, current_pdf_name

    rag_chain        = None
    current_pdf_name = None

    # Wipe vector store
    if os.path.exists(CHROMA_DIR):
        try:
            shutil.rmtree(CHROMA_DIR)
            os.makedirs(CHROMA_DIR, exist_ok=True)
            print("[Admin] Vector store cleared.")
        except Exception as e:
            print(f"[Admin] Warning: could not fully clear vector store: {e}")

    # Wipe KB metadata from DB
    db = SessionLocal()
    try:
        db.query(KnowledgeBase).delete()
        db.commit()
    finally:
        db.close()

    return {
        "status": "success",
        "message": "✅ Knowledge base cleared. Upload a new PDF to continue.",
    }

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

# LangChain / Ollama / FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_classic.chains.retrieval_qa.base import RetrievalQA
from langchain_classic.prompts import PromptTemplate
from langchain_core.documents import Document

from database import ChatHistory, KnowledgeBase, get_db, init_db, SessionLocal

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
FAISS_DIR    = "../faiss_db"           # persists until admin clears it
UPLOAD_DIR   = "../uploaded_pdfs"      # all uploaded PDFs stored here
TEMP_TEXT_FILE = "../temp_knowledge.txt"  # temporary text file for text-based knowledge
ADMIN_TOKEN  = "Admin123"

Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(FAISS_DIR).mkdir(parents=True, exist_ok=True)

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

#----------------------------------------------
# api-key from env
#----------------------------------------------
import os
from dotenv import load_dotenv

load_dotenv() # Loads the .env file
api_key = os.getenv("groq_api")
google_api_key=os.getenv("GOOGLE_API_KEY")

# ─────────────────────────────────────────────
# Global RAG state
# ─────────────────────────────────────────────
rag_chain: Optional[RetrievalQA] = None
current_pdf_name: Optional[str]  = None

# FAISS index files saved with this name inside FAISS_DIR
FAISS_INDEX_NAME = "index"


def build_rag_chain(pdf_path: str, pdf_name: str) -> Optional[RetrievalQA]:
    """
    Load a PDF, create embeddings, save them as a FAISS index on disk,
    and return a RetrievalQA chain.
    Old index is wiped before rebuilding so the new PDF is the sole source.
    """
    global current_pdf_name
    try:
        loader = PyPDFLoader(pdf_path)
        docs   = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks   = splitter.split_documents(docs)

        embeddings =  GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=google_api_key
        )

        # Wipe old FAISS index so the new PDF is the sole source
        if os.path.exists(FAISS_DIR):
            shutil.rmtree(FAISS_DIR)
            os.makedirs(FAISS_DIR, exist_ok=True)
            print(f"[Build] Cleared old FAISS index, rebuilding from: {pdf_name}")

        vector_store = FAISS.from_documents(chunks, embeddings)
        vector_store.save_local(FAISS_DIR, index_name=FAISS_INDEX_NAME)
        print(f"[Build] Stored {len(chunks)} chunks in persistent FAISS index.")

        # llm = ChatOllama(
        #     model="llama3",
        #     temperature=0.3,
        #     num_predict=250,
        # )
        llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    api_key=api_key
    # api_key="your-api-key-here" # Or set as GROQ_API_KEY env var
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

        rag_chain = chain
        return rag_chain

    except Exception as e:
        print(f"[Build] Error building RAG chain: {e}")
        return None


def add_text_to_knowledge_base(text_content: str, source_name: str) -> Optional[RetrievalQA]:
    """
    Add text content to the existing knowledge base (FAISS index).
    1. Save text to temporary file (create if not exists, rewrite if exists)
    2. Read content from file and convert to chunks
    3. Create embeddings and store in FAISS DB
    """
    global rag_chain, current_pdf_name
    try:
        # Save text to temporary file (create if not exists, rewrite if exists)
        with open(TEMP_TEXT_FILE, "w", encoding="utf-8") as f:
            f.write(text_content)
        print(f"[Text] Saved text to temporary file: {TEMP_TEXT_FILE}")
        
        # Read content from the temporary file
        with open(TEMP_TEXT_FILE, "r", encoding="utf-8") as f:
            file_content = f.read()
        
        # Create Document from file content
        doc = Document(page_content=file_content, metadata={"source": source_name})
        
        # Split text into chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents([doc])
        
        print(f"[Text] Created {len(chunks)} chunks from text file")

        embeddings =  GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=google_api_key
        )

        # Check if FAISS index exists
        index_file = Path(FAISS_DIR) / f"{FAISS_INDEX_NAME}.faiss"
        
        if index_file.exists():
            # Load existing index and add new documents
            vector_store = FAISS.load_local(
                FAISS_DIR,
                embeddings,
                index_name=FAISS_INDEX_NAME,
                allow_dangerous_deserialization=True,
            )
            vector_store.add_documents(chunks)
            vector_store.save_local(FAISS_DIR, index_name=FAISS_INDEX_NAME)
            print(f"[Text] Added {len(chunks)} chunks to existing FAISS index")
        else:
            # Create new index from text
            vector_store = FAISS.from_documents(chunks, embeddings)
            vector_store.save_local(FAISS_DIR, index_name=FAISS_INDEX_NAME)
            print(f"[Text] Created new FAISS index with {len(chunks)} chunks")

        # Create or update RAG chain
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            api_key=api_key
        )

        chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
            chain_type_kwargs={"prompt": PROMPT_TEMPLATE},
            return_source_documents=False,
        )

        # Update current knowledge source name
        if not current_pdf_name:
            current_pdf_name = source_name

        # Persist metadata to DB
        db = SessionLocal()
        try:
            existing_kb = db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True).first()
            if not existing_kb:
                db.add(KnowledgeBase(
                    filename=source_name,
                    filepath="text_input",
                    uploaded_at=datetime.utcnow(),
                    is_active=True,
                ))
            db.commit()
        finally:
            db.close()

        rag_chain = chain
        return rag_chain

    except Exception as e:
        print(f"[Text] Error adding text to knowledge base: {e}")
        return None


def load_existing_chain() -> Optional[RetrievalQA]:
    """
    On startup, if a FAISS index already exists on disk (from a previous session),
    reload the chain so the bot is immediately ready without re-upload.
    """
    try:
        index_file = Path(FAISS_DIR) / f"{FAISS_INDEX_NAME}.faiss"
        if not index_file.exists():
            return None

        embeddings =  GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=google_api_key
        )
        vector_store = FAISS.load_local(
            FAISS_DIR,
            embeddings,
            index_name=FAISS_INDEX_NAME,
            allow_dangerous_deserialization=True,   # safe — we wrote this file ourselves
        )

        # llm = ChatOllama(model="llama3", temperature=0.3, num_predict=150)
        llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                api_key=api_key
                # api_key="your-api-key-here" # Or set as GROQ_API_KEY env var
            )

        chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
            chain_type_kwargs={"prompt": PROMPT_TEMPLATE},
            return_source_documents=False,
        )
        print("[Startup] Reloaded existing FAISS index from disk.")
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

    # Try to reload the persisted FAISS index
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


class TextUploadRequest(BaseModel):
    text_content: str
    source_name: str = "User Text Input"


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
    index_exists = (Path(FAISS_DIR) / f"{FAISS_INDEX_NAME}.faiss").exists()
    return {
        "kb_loaded": rag_chain is not None,
        "current_pdf": current_pdf_name,
        "vector_store_on_disk": index_exists,
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
            f"Knowledge base updated from '{file.filename}'. "
            "The chatbot is ready to answer questions."
        ),
    }


@app.post("/admin/upload_text", dependencies=[Depends(verify_admin)])
async def upload_text(req: TextUploadRequest):
    """Add text content to the knowledge base (FAISS vector store)."""
    global rag_chain

    if not req.text_content or not req.text_content.strip():
        raise HTTPException(status_code=400, detail="Text content cannot be empty.")

    print(f"[Admin] Adding text to knowledge base: {req.source_name}")
    print(f"[Admin] Text length: {len(req.text_content)} characters")

    new_chain = add_text_to_knowledge_base(req.text_content, req.source_name)
    if new_chain is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to add text to knowledge base. Check server logs."
        )

    rag_chain = new_chain
    print("[Admin] Text added to RAG chain successfully.")

    return {
        "status": "success",
        "source": req.source_name,
        "text_length": len(req.text_content),
        "message": (
            f"Text content added to knowledge base. "
            "The chatbot is ready to answer questions based on the new content."
        ),
    }


@app.post("/admin/clear_knowledge", dependencies=[Depends(verify_admin)])
async def clear_knowledge():
    """Permanently wipe the FAISS index, PDF metadata, and temporary text file."""
    global rag_chain, current_pdf_name

    rag_chain        = None
    current_pdf_name = None

    # Wipe FAISS index
    if os.path.exists(FAISS_DIR):
        try:
            shutil.rmtree(FAISS_DIR)
            os.makedirs(FAISS_DIR, exist_ok=True)
            print("[Admin] FAISS index cleared.")
        except Exception as e:
            print(f"[Admin] Warning: could not fully clear FAISS index: {e}")

    # Delete temporary text file
    if os.path.exists(TEMP_TEXT_FILE):
        try:
            os.remove(TEMP_TEXT_FILE)
            print(f"[Admin] Temporary text file deleted: {TEMP_TEXT_FILE}")
        except Exception as e:
            print(f"[Admin] Warning: could not delete temporary text file: {e}")

    # Wipe KB metadata from DB
    db = SessionLocal()
    try:
        db.query(KnowledgeBase).delete()
        db.commit()
    finally:
        db.close()

    return {
        "status": "success",
        "message": "Knowledge base cleared. Upload a new PDF to continue.",
    }

# 🍽️ Restaurant FAQ Bot

An intelligent RAG (Retrieval-Augmented Generation) chatbot for restaurant FAQs. Upload menu PDFs and get instant answers about your restaurant with AI-powered understanding of broken English and spelling mistakes.

## ✨ Features

- **Smart PDF Upload** — Upload restaurant menu/FAQ PDFs and build a knowledge base instantly
- **Intelligent RAG Chain** — Uses Ollama embeddings (all-minilm:l6-v2) for semantic search
- **Broken English Tolerant** — Understands misspellings, grammar errors, and slang
- **Session Management** — Track chat history per session
- **Admin Panel** — Manage knowledge base, view logs, clear data
- **Glassmorphism UI** — Modern, responsive Streamlit frontend
- **FastAPI Backend** — High-performance REST API with CORS support
- **Persistent Storage** — SQLite for chat history, FAISS for vector indexing

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│      Streamlit Frontend (8501)          │
│   - Chat Interface                      │
│   - Admin Panel (Upload/Clear)          │
└────────────┬────────────────────────────┘
             │ HTTP
             ↓
┌─────────────────────────────────────────┐
│   FastAPI Backend (8000)                │
│   - /chat endpoint                      │
│   - /admin/upload_pdf                   │
│   - /admin/clear_knowledge              │
│   - /history/{session_id}               │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    ↓                 ↓
┌──────────┐      ┌──────────────┐
│ SQLite   │      │ FAISS/ChromaDB
│ DB       │      │ Vector Store
│ (History)│      │ (Embeddings)
└──────────┘      └──────────────┘
    ↑                 ↑
    └────────┬────────┘
             │
       ┌─────────────┐
       │ Ollama      │
       │ Embeddings  │
       │ + LLM       │
       │ (localhost) │
       └─────────────┘
```

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend Framework** | FastAPI | 0.136.1 |
| **Frontend Framework** | Streamlit | 1.57.0 |
| **Database** | SQLAlchemy + SQLite | 2.0.49 |
| **LLM Framework** | LangChain | 1.2.17 |
| **Embeddings & LLM** | Ollama | - |
| **Vector Storage** | FAISS/ChromaDB | - |
| **PDF Processing** | PyPDF | 6.10.2 |
| **HTTP Client** | Requests | 2.33.1 |

## 📋 Prerequisites

- **Python 3.9+**
- **Ollama** (with models pulled)
- **pip** or **conda**

### Required Ollama Models

```bash
ollama pull gemma:2b          # LLM for Q&A
ollama pull all-minilm:l6-v2  # Embeddings model
```

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/restaurant_faq_bot.git
cd restaurant_faq_bot
```

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Ensure Ollama is Running

```bash
# In a separate terminal, start Ollama
ollama serve

# Pull required models if not already done
ollama pull gemma:2b
ollama pull all-minilm:l6-v2
```

### 5. Run the Application

```bash
python run.py
```

This will start:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:8501

## 📖 Usage

### 💬 Chat Interface

1. Open **http://localhost:8501** in your browser
2. Type your question about the restaurant
3. Get instant answers from the PDF knowledge base

**Example questions:**
- "What's your lunch special?"
- "Do u have veggie optins?" (Broken English OK!)
- "Tell me about desserts"

### 🔐 Admin Panel

1. Click **"Admin Panel"** in the sidebar
2. Login with credentials:
   - **Username**: Admin
   - **Password**: Admin123

**Admin Features:**
- 📤 **Upload PDF** — Add menu/FAQ documents
- 🗑️ **Clear Knowledge Base** — Remove all stored data
- 📊 **Knowledge Base Status** — View current active PDF
- 📋 **View Logs** — See all chat interactions

## 📁 Project Structure

```
restaurant_faq_bot/
├── backend.py              # FastAPI server & RAG chain logic
├── frontend.py             # Streamlit UI with glassmorphism
├── database.py             # SQLAlchemy models & DB setup
├── run.py                  # Startup script (runs both servers)
├── dummy.py                # Alternative backend (for testing)
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── chroma_db/             # ChromaDB vector store (auto-created)
├── uploaded_pdfs/         # Uploaded PDF files (auto-created)
└── faiss_db/              # FAISS vector index (auto-created)
```

## 🔌 API Endpoints

### Chat Endpoint

```http
POST /chat
Content-Type: application/json

{
  "session_id": "user-123",
  "question": "What's on the menu?"
}

Response:
{
  "session_id": "user-123",
  "answer": "We have...",
  "source_context": "..."
}
```

### History

```http
GET /history/{session_id}

Response:
[
  {"role": "user", "content": "..."},
  {"role": "assistant", "content": "..."}
]
```

### Admin: Upload PDF

```http
POST /admin/upload_pdf
Authorization: Bearer Admin123
Content-Type: multipart/form-data

file: <PDF file>
```

### Admin: Clear Knowledge Base

```http
POST /admin/clear_knowledge
Authorization: Bearer Admin123
```

### Admin: KB Status

```http
GET /admin/kb_status
Authorization: Bearer Admin123

Response:
{
  "filename": "menu.pdf",
  "uploaded_at": "2026-05-09T10:30:00",
  "is_active": true
}
```

## ⚙️ Configuration

Edit these in `backend.py` and `frontend.py`:

```python
# backend.py
FAISS_DIR = "./faiss_db"              # Vector store location
UPLOAD_DIR = "./uploaded_pdfs"        # PDF storage
OLLAMA_BASE_URL = "http://localhost:11434"
ADMIN_TOKEN = "Admin123"              # Change this in production!

# frontend.py
BACKEND_URL = "http://localhost:8000"
ADMIN_TOKEN = "Admin123"
```

## 🧠 How It Works

1. **PDF Upload** → Documents are split into chunks
2. **Embedding** → Chunks converted to vectors using all-minilm:l6-v2
3. **Storage** → Vectors indexed in FAISS/ChromaDB
4. **Query** → User question embedded and matched with relevant chunks
5. **Generation** → Gemma LLM generates answer with context
6. **History** → Chat saved to SQLite

## 🎨 UI Features

- **Iridescent Glassmorphism** — Modern gradient backgrounds
- **Dark Mode** — Eye-friendly blue and purple theme
- **Real-time Chat** — Interactive message display
- **Session Management** — Each user gets unique session ID
- **Admin Dashboard** — Sidebar-based admin controls

## 🔒 Security Notes

⚠️ **For Production:**
- Change `ADMIN_TOKEN` to a strong secret
- Use environment variables for secrets (`.env` file)
- Implement proper authentication/authorization
- Add rate limiting to API endpoints
- Use HTTPS instead of HTTP

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Connection refused" to Ollama** | Ensure Ollama is running (`ollama serve`) |
| **"Model not found" error** | Pull required models: `ollama pull gemma:2b` `ollama pull all-minilm:l6-v2` |
| **FAISS/ChromaDB not loading** | Delete `faiss_db/` or `chroma_db/` folder and re-upload PDF |
| **Port already in use** | Change port in `run.py` |
| **PDF not processing** | Ensure PDF is not corrupted and contains text (not scanned images) |

## 📝 Example `.env` File (Optional)

```
ADMIN_TOKEN=your-super-secret-token
OLLAMA_BASE_URL=http://localhost:11434
BACKEND_URL=http://localhost:8000
UPLOAD_DIR=./uploaded_pdfs
FAISS_DIR=./faiss_db
```

## 🚀 Deployment

### Local Development
```bash
python run.py
```

### Docker (Future Enhancement)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

## 📄 License

MIT License — Feel free to use and modify!

## 👨‍💻 Author

Created for restaurant FAQ automation using RAG and Ollama.

## 🤝 Contributing

Pull requests and issues are welcome! Feel free to:
- Report bugs
- Suggest improvements
- Add new features

## 📞 Support

For issues or questions:
1. Check the Troubleshooting section
2. Review logs in the Admin Panel
3. Check backend terminal for error messages

---

**Happy chatting! 🎉 Your restaurant assistant is ready to serve.**

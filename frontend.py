"""
frontend.py — Streamlit UI for RAG Chatbot
- Main chat with Iridescent Glassmorphism styling
- Sidebar Admin Panel (hardcoded login: Admin / Admin123)
- KB status shown at top of admin panel
"""

import uuid
import requests
import streamlit as st

BACKEND_URL = "http://localhost:8000"
ADMIN_TOKEN = "Admin123"

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Restaurant Assistant",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
GLASS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 100%) !important;
    min-height: 100vh;
    color: #e8eaed;
}

[data-testid="stHeader"] { background: transparent !important; }

[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #1a1f2e 0%, #242b3d 100%) !important;
    border-right: 2px solid #00d4ff !important;
    box-shadow: -4px 0 15px rgba(0, 212, 255, 0.15) !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: #e8eaed !important;
}

#MainMenu, footer, header { visibility: hidden; }

.chat-wrapper {
    max-width: 800px;
    margin: 0 auto;
    padding: 2.5rem 1.5rem 6rem;
}

.chat-title {
    text-align: center;
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #00d4ff 0%, #00f7ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
    letter-spacing: -0.5px;
}

.chat-subtitle {
    text-align: center;
    font-size: 1rem;
    color: #a0aec0;
    margin-bottom: 2.5rem;
    font-weight: 400;
}

.msg-row {
    display: flex;
    margin-bottom: 1.5rem;
    align-items: flex-end;
    gap: 0.75rem;
}

.msg-row.user  { flex-direction: row-reverse; }
.msg-row.bot   { flex-direction: row; }

.avatar {
    width: 40px; height: 40px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; flex-shrink: 0; font-weight: 600;
}
.avatar.user {
    background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
    box-shadow: 0 4px 16px rgba(0, 212, 255, 0.4);
}
.avatar.bot {
    background: linear-gradient(135deg, #ff6b35 0%, #ff9500 100%);
    box-shadow: 0 4px 16px rgba(255, 107, 53, 0.4);
}

.bubble {
    max-width: 70%;
    padding: 1rem 1.25rem;
    border-radius: 16px;
    line-height: 1.65;
    font-size: 0.95rem;
    word-break: break-word;
}
.bubble.user {
    background: linear-gradient(135deg, #0099ff 0%, #00d4ff 100%);
    color: #ffffff;
    border-bottom-right-radius: 4px;
    box-shadow: 0 8px 24px rgba(0, 153, 255, 0.35);
}
.bubble.bot {
    background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
    border: 1.5px solid #00d4ff;
    color: #e8eaed;
    border-bottom-left-radius: 4px;
    box-shadow: 0 8px 24px rgba(0, 212, 255, 0.15);
}

/* KB status badge */
.kb-status-active {
    background: rgba(0, 255, 120, 0.15);
    border: 1px solid #00ff78;
    border-radius: 8px;
    padding: 0.6rem 0.9rem;
    color: #00ff78;
    font-size: 0.88rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
}
.kb-status-inactive {
    background: rgba(255, 80, 80, 0.15);
    border: 1px solid #ff5050;
    border-radius: 8px;
    padding: 0.6rem 0.9rem;
    color: #ff5050;
    font-size: 0.88rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
}

[data-testid="stChatInput"] > div {
    background: #1a1f2e !important;
    border: 2px solid #00d4ff !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 16px rgba(0, 212, 255, 0.2) !important;
}
[data-testid="stChatInput"] input {
    color: #e8eaed !important;
    font-size: 0.95rem !important;
}
[data-testid="stChatInput"] input::placeholder { color: #64748b !important; }

.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
    background: #1a1f2e !important;
    color: #e8eaed !important;
}

.stTextInput > div > div > input,
.stPasswordInput > div > div > input {
    background: #1a1f2e !important;
    color: #e8eaed !important;
    border: 1.5px solid #00d4ff !important;
    border-radius: 8px !important;
    font-size: 0.95rem !important;
}
.stTextInput > div > div > input::placeholder,
.stPasswordInput > div > div > input::placeholder { color: #64748b !important; }

.stButton > button {
    background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
    color: #0f1419;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 1.4rem;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.95rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(0, 212, 255, 0.4);
}

[data-testid="stFileUploader"] {
    border: 2px dashed #00d4ff !important;
    background: rgba(0, 212, 255, 0.05) !important;
    border-radius: 8px !important;
}

.stSpinner { color: #00d4ff !important; }
</style>
"""

st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────
if "session_id"      not in st.session_state:
    st.session_state.session_id      = str(uuid.uuid4())
if "messages"        not in st.session_state:
    st.session_state.messages        = []
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def render_message(role: str, content: str):
    if role == "user":
        html = f"""
        <div class="msg-row user">
            <div class="avatar user">👤</div>
            <div class="bubble user">{content}</div>
        </div>"""
    else:
        html = f"""
        <div class="msg-row bot">
            <div class="avatar bot">🍽️</div>
            <div class="bubble bot">{content}</div>
        </div>"""
    st.markdown(html, unsafe_allow_html=True)


def fetch_kb_status() -> dict:
    try:
        r = requests.get(
            f"{BACKEND_URL}/admin/kb_status",
            headers={"x-admin-token": ADMIN_TOKEN},
            timeout=5
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"kb_loaded": False, "current_pdf": None, "vector_store_on_disk": False}


# ─────────────────────────────────────────────
# Sidebar — Admin Panel
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Admin Panel")
    st.markdown("---")

    if not st.session_state.admin_logged_in:
        username = st.text_input("Username", placeholder="Admin")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        if st.button("Login"):
            if username.strip() == "Admin" and password == "Admin123":
                st.session_state.admin_logged_in = True
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid credentials.")
    else:
        st.markdown("**Logged in as Admin**")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("Logout", use_container_width=True):
                st.session_state.admin_logged_in = False
                st.rerun()

        st.markdown("---")

        # ── Knowledge Base Status ──
        st.markdown("### 📡 Knowledge Base Status")
        kb = fetch_kb_status()
        if kb["kb_loaded"]:
            pdf_label = kb.get("current_pdf") or "Unknown PDF"
            st.markdown(
                f'<div class="kb-status-active">🟢 Active — <b>{pdf_label}</b></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="kb-status-inactive">🔴 No knowledge base loaded</div>',
                unsafe_allow_html=True
            )
            if kb.get("vector_store_on_disk"):
                st.info("💡 Vector store exists on disk but chain is not loaded. "
                        "Restart the backend to auto-reload it.")

        st.markdown("---")

        # ── Upload PDF ──
        st.markdown("### Knowledge Base Management")
        st.markdown("**Upload a PDF to build / replace the knowledge base**")
        st.caption(
            "The PDF is stored permanently. The chatbot stays ready even after restarts "
            "— until you explicitly clear the knowledge base."
        )

        uploaded_file = st.file_uploader(
            "Choose a PDF file", type=["pdf"], label_visibility="collapsed"
        )

        if uploaded_file:
            st.info(f"📄 **{uploaded_file.name}** — "
                    f"{uploaded_file.size / (1024 * 1024):.2f} MB")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬆️ Upload & Build", use_container_width=True, key="upload_btn"):
                    with st.spinner("🔄 Building knowledge base… this may take a minute"):
                        try:
                            resp = requests.post(
                                f"{BACKEND_URL}/admin/upload_pdf",
                                headers={"x-admin-token": ADMIN_TOKEN},
                                files={"file": (
                                    uploaded_file.name,
                                    uploaded_file.getvalue(),
                                    "application/pdf"
                                )},
                                timeout=300
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                st.success(data.get("message", "✅ Knowledge base updated!"))
                                st.info(
                                    f"**{data.get('filename')}** — "
                                    f"{data.get('file_size', 0) / 1024:.1f} KB"
                                )
                                st.rerun()
                            else:
                                detail = (
                                    resp.json().get("detail", resp.text)
                                    if "application/json" in resp.headers.get("content-type", "")
                                    else resp.text
                                )
                                st.error(f"Error {resp.status_code}: {detail}")
                        except Exception as e:
                            st.error(f"Could not reach backend: {e}")
            with col2:
                if st.button("Cancel", use_container_width=True, key="cancel_upload"):
                    st.rerun()

        st.markdown("---")

        # ── Clear Knowledge Base ──
        st.markdown("**🗑️ Clear Knowledge Base**")
        st.caption("Removes the vector store AND the PDF metadata. "
                   "The chatbot will stop answering until a new PDF is uploaded.")

        if st.button("🔴 Delete All Knowledge", use_container_width=True, key="clear_kb_btn"):
            if st.session_state.get("confirm_clear", False):
                with st.spinner("Clearing knowledge base…"):
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/admin/clear_knowledge",
                            headers={"x-admin-token": ADMIN_TOKEN},
                            timeout=30
                        )
                        if resp.status_code == 200:
                            st.success("Knowledge base cleared.")
                            st.info("Upload a new PDF to rebuild.")
                            st.session_state.confirm_clear = False
                            st.rerun()
                        else:
                            st.error(f"Error {resp.status_code}: {resp.text}")
                    except Exception as e:
                        st.error(f"Could not reach backend: {e}")
            else:
                st.warning("Are you sure? Click again to confirm.")
                st.session_state.confirm_clear = True

        st.markdown("---")

        # ── Chat Logs ──
        st.markdown("### Chat Logs")

        if st.checkbox("Show Chat Logs", value=st.session_state.get("show_logs", False)):
            try:
                resp = requests.get(
                    f"{BACKEND_URL}/admin/logs",
                    headers={"x-admin-token": ADMIN_TOKEN},
                    timeout=10
                )
                if resp.status_code == 200:
                    logs = resp.json()
                    if logs:
                        import pandas as pd
                        rows = [
                            {
                                "Session ID": l["session_id"][:8] + "…",
                                "Role": "👤 User" if l["role"] == "user" else "🍽️ Bot",
                                "Preview": (l["content"][:50] + "…"
                                            if len(l["content"]) > 50
                                            else l["content"]),
                                "Time": l["timestamp"][:19],
                            }
                            for l in logs
                        ]
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, height=400)
                        st.info(
                            f"📊 **{len(logs)}** total messages | "
                            f"👤 {sum(1 for l in logs if l['role']=='user')} user | "
                            f"🍽️ {sum(1 for l in logs if l['role']=='assistant')} bot"
                        )
                        with st.expander("View Last 10 Full Messages"):
                            for i, log in enumerate(logs[:10]):
                                st.markdown(f"**{i+1}. {log['role'].upper()}**")
                                st.code(log["content"])
                                st.caption(log["timestamp"])
                                st.divider()
                    else:
                        st.info("No chat history yet.")
                else:
                    st.error(f"Error {resp.status_code}: {resp.text}")
            except Exception as e:
                st.error(f"❌ Could not reach backend: {e}")


# ─────────────────────────────────────────────
# Main Chat UI
# ─────────────────────────────────────────────
st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
st.markdown('<div class="chat-title">Restaurant Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="chat-subtitle">Ask me anything about our menu, hours, reservations & more</div>',
    unsafe_allow_html=True
)

for msg in st.session_state.messages:
    render_message(msg["role"], msg["content"])

st.markdown('</div>', unsafe_allow_html=True)

# ── Chat input ──
if user_input := st.chat_input("Type your question…"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    render_message("user", user_input)

    with st.spinner(""):
        try:
            resp = requests.post(
                f"{BACKEND_URL}/chat",
                json={"session_id": st.session_state.session_id, "message": user_input},
                timeout=120
            )
            if resp.status_code == 200:
                answer = resp.json()["answer"]
            elif resp.status_code == 503:
                answer = ("The knowledge base isn't ready yet. "
                          "Please ask the admin to upload a PDF.")
            else:
                answer = f"Backend error ({resp.status_code}). Please try again."
        except requests.exceptions.ConnectionError:
            answer = "⚠️ Cannot connect to the backend. Make sure `run.py` is running."
        except Exception as e:
            answer = f"Unexpected error: {e}"

    st.session_state.messages.append({"role": "assistant", "content": answer})
    render_message("assistant", answer)

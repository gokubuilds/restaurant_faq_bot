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

/* Floating Admin Button */
.floating-admin-btn {
    position: fixed;
    bottom: 30px;
    right: 30px;
    z-index: 999;
}
.floating-admin-btn button {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    font-size: 1.5rem;
    padding: 0 !important;
    box-shadow: 0 4px 12px rgba(0, 212, 255, 0.4) !important;
}
.floating-admin-btn button:hover {
    transform: scale(1.1);
}
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
if "show_admin_modal" not in st.session_state:
    st.session_state.show_admin_modal = False


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
# Admin Panel Modal (Opens with button)
# ─────────────────────────────────────────────
col1, col2, col3 = st.columns([0.8, 0.1, 0.1])
with col3:
    if st.button("⚙️", help="Admin Panel", key="floating_admin_btn"):
        st.session_state.show_admin_modal = not st.session_state.show_admin_modal

if st.session_state.show_admin_modal:
    st.markdown("---")
    admin_container = st.container()
    with admin_container:
        st.markdown("<h3 style='text-align: center; color: #00d4ff;'>🔒 Admin Panel</h3>", unsafe_allow_html=True)
        
        if not st.session_state.admin_logged_in:
            # Login Form
            st.markdown("<div style='background: rgba(26, 31, 46, 0.8); border: 1px solid #00d4ff; border-radius: 12px; padding: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            st.markdown("#### Admin Login")
            
            login_col1, login_col2 = st.columns(2)
            with login_col1:
                username = st.text_input("👤 Username", placeholder="Enter username", key="modal_user")
            with login_col2:
                password = st.text_input("🔐 Password", type="password", placeholder="Enter password", key="modal_pass")
            
            login_btn_col1, login_btn_col2, login_btn_col3 = st.columns([1, 1, 1])
            with login_btn_col2:
                if st.button("🔓 Login", use_container_width=True, key="modal_login"):
                    if username.strip() == "Admin" and password == "Admin123":
                        st.session_state.admin_logged_in = True
                        st.success("✅ Logged in successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
            st.markdown("</div>", unsafe_allow_html=True)
        
        else:
            # Admin Dashboard After Login
            st.markdown(f"<div style='color: #00ff78; font-weight: bold; margin-bottom: 15px;'>✅ Logged in as: <span style='color: #00d4ff;'>Admin</span></div>", unsafe_allow_html=True)
            
            # Top Controls
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            with btn_col1:
                if st.button("🔄 Refresh", use_container_width=True, key="modal_refresh"):
                    st.rerun()
            with btn_col2:
                if st.button("Close Panel", use_container_width=True, key="modal_close"):
                    st.session_state.show_admin_modal = False
                    st.rerun()
            with btn_col3:
                if st.button("🚪 Logout", use_container_width=True, key="modal_logout"):
                    st.session_state.admin_logged_in = False
                    st.session_state.show_admin_modal = False
                    st.rerun()
            
            st.markdown("---")
            
            # Tabs for different admin sections
            tab1, tab2, tab3, tab4 = st.tabs(["📡 KB Status", "📤 Upload PDF", "🗑️ Clear KB", "📊 Chat Logs"])
            
            with tab1:
                st.markdown("### Knowledge Base Status")
                kb = fetch_kb_status()
                col1, col2 = st.columns(2)
                with col1:
                    if kb["kb_loaded"]:
                        pdf_label = kb.get("current_pdf") or "Unknown PDF"
                        st.markdown(f'<div class="kb-status-active">🟢 Status: <b>ACTIVE</b></div>', unsafe_allow_html=True)
                        st.markdown(f"📄 **PDF Loaded:** {pdf_label}")
                    else:
                        st.markdown(f'<div class="kb-status-inactive">🔴 Status: <b>INACTIVE</b></div>', unsafe_allow_html=True)
                        st.markdown("ℹ️ No knowledge base is currently loaded")
                with col2:
                    st.info("💾 Vector store metadata will be shown here after upload")
            
            with tab2:
                st.markdown("### Upload Knowledge Base Content")
                st.caption("Add content to your knowledge base via PDF upload or text input")
                
                # Subtabs for PDF and Text
                subtab1, subtab2 = st.tabs(["📄 PDF Upload", "📝 Text Input"])
                
                with subtab1:
                    st.markdown("#### 📄 Upload PDF")
                    st.caption("Upload a PDF file to build or replace your knowledge base")
                    
                    uploaded_file = st.file_uploader(
                        "Choose a PDF file",
                        type=["pdf"],
                        key="modal_uploader"
                    )
                    
                    if uploaded_file:
                        file_size_mb = uploaded_file.size / (1024 * 1024)
                        st.divider()
                        
                        # File Details
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("📄 Filename", uploaded_file.name)
                        with col2:
                            st.metric("📊 File Size", f"{file_size_mb:.2f} MB")
                        
                        st.divider()
                        
                        # Action Buttons
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("⬆️ Upload & Build KB", use_container_width=True, key="modal_upload_btn"):
                                with st.spinner("🔄 Building knowledge base… This may take a minute"):
                                    try:
                                        resp = requests.post(
                                            f"{BACKEND_URL}/admin/upload_pdf",
                                            headers={"x-admin-token": ADMIN_TOKEN},
                                            files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                                            timeout=300
                                        )
                                        if resp.status_code == 200:
                                            data = resp.json()
                                            st.success("✅ Knowledge base updated successfully!")
                                            st.balloons()
                                            st.rerun()
                                        else:
                                            detail = resp.json().get("detail", resp.text) if "application/json" in resp.headers.get("content-type", "") else resp.text
                                            st.error(f"❌ Error {resp.status_code}: {detail}")
                                    except Exception as e:
                                        st.error(f"❌ Connection error: {e}")
                        
                        with btn_col2:
                            if st.button("❌ Cancel", use_container_width=True, key="modal_cancel_upload"):
                                st.rerun()
                    else:
                        st.info("👆 Select a PDF file above to get started")
                
                with subtab2:
                    st.markdown("#### 📝 Add Text Content")
                    st.caption("Paste text content to add to your knowledge base (menu, hours, policies, FAQs, etc.)")
                    
                    # Source name for reference
                    source_name = st.text_input(
                        "📋 Source Name (optional)",
                        placeholder="E.g., Menu, Hours & Policies, FAQ",
                        value="User Text Input",
                        key="text_source_name"
                    )
                    
                    # Text input area
                    text_content = st.text_area(
                        "📝 Paste your text here",
                        placeholder="E.g., Menu items, restaurant hours, policies, FAQs, etc.",
                        height=200,
                        key="text_input_area"
                    )
                    
                    # Display stats when text is entered
                    if text_content and text_content.strip():
                        st.divider()
                        
                        # Text statistics
                        char_count = len(text_content)
                        word_count = len(text_content.split())
                        
                        stat_col1, stat_col2 = st.columns(2)
                        with stat_col1:
                            st.metric("📊 Characters", f"{char_count:,}")
                        with stat_col2:
                            st.metric("📄 Words", f"{word_count:,}")
                        
                        st.divider()
                        
                        # Submit and Clear Buttons
                        submit_col, clear_col = st.columns([2, 1])
                        
                        with submit_col:
                            if st.button("✅ Add to Knowledge Base", use_container_width=True, key="modal_text_upload_btn"):
                                with st.spinner("🔄 Adding text to knowledge base…"):
                                    try:
                                        resp = requests.post(
                                            f"{BACKEND_URL}/admin/upload_text",
                                            headers={"x-admin-token": ADMIN_TOKEN},
                                            json={
                                                "text_content": text_content,
                                                "source_name": source_name or "User Text Input"
                                            },
                                            timeout=300
                                        )
                                        if resp.status_code == 200:
                                            data = resp.json()
                                            st.success("✅ Text added to knowledge base successfully!")
                                            st.info(f"**Source:** {data.get('source')}\n\n**Characters Added:** {data.get('text_length'):,}")
                                            st.balloons()
                                            st.rerun()
                                        else:
                                            detail = resp.json().get("detail", resp.text) if "application/json" in resp.headers.get("content-type", "") else resp.text
                                            st.error(f"❌ Error {resp.status_code}: {detail}")
                                    except Exception as e:
                                        st.error(f"❌ Connection error: {e}")
                        
                        with clear_col:
                            if st.button("🗑️ Clear", use_container_width=True, key="modal_clear_text"):
                                st.rerun()
                    else:
                        st.info("👆 Enter your text above to get started")
            
            with tab3:
                st.markdown("### Clear Knowledge Base")
                st.warning("⚠️ This will permanently delete the knowledge base and vector store.")
                st.caption("After deletion, the chatbot will not be able to answer questions until a new PDF is uploaded.")
                
                if st.button("🔴 Delete All Knowledge", use_container_width=True, key="modal_clear_btn"):
                    if st.session_state.get("modal_confirm_clear", False):
                        with st.spinner("🔄 Clearing knowledge base…"):
                            try:
                                resp = requests.post(
                                    f"{BACKEND_URL}/admin/clear_knowledge",
                                    headers={"x-admin-token": ADMIN_TOKEN},
                                    timeout=30
                                )
                                if resp.status_code == 200:
                                    st.success("✅ Knowledge base cleared successfully.")
                                    st.info("Upload a new PDF to rebuild the knowledge base.")
                                    st.session_state.modal_confirm_clear = False
                                    st.rerun()
                                else:
                                    st.error(f"❌ Error {resp.status_code}: {resp.text}")
                            except Exception as e:
                                st.error(f"❌ Connection error: {e}")
                    else:
                        st.warning("❗ Click the button again to confirm deletion")
                        st.session_state.modal_confirm_clear = True
            
            with tab4:
                st.markdown("### Chat Logs History")
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
                            
                            # Prepare data for table
                            rows = []
                            for log in logs:
                                rows.append({
                                    "Session ID": log["session_id"][:12] + "…",
                                    "Sender": "👤 User" if log["role"] == "user" else "🍽️ Bot",
                                    "Message": (log["content"][:60] + "…") if len(log["content"]) > 60 else log["content"],
                                    "Timestamp": log["timestamp"]
                                })
                            
                            df = pd.DataFrame(rows)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                            
                            # Summary stats
                            st.markdown("---")
                            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                            with stat_col1:
                                st.metric("📊 Total Messages", len(logs))
                            with stat_col2:
                                user_count = sum(1 for l in logs if l["role"] == "user")
                                st.metric("👤 User Messages", user_count)
                            with stat_col3:
                                bot_count = sum(1 for l in logs if l["role"] == "assistant")
                                st.metric("🍽️ Bot Responses", bot_count)
                            with stat_col4:
                                unique_sessions = len(set(l["session_id"] for l in logs))
                                st.metric("🔗 Unique Sessions", unique_sessions)
                            
                            # Full message view
                            if st.checkbox("📖 View Full Messages", key="view_full_logs"):
                                st.markdown("---")
                                for i, log in enumerate(reversed(logs[:20])):
                                    st.markdown(f"**{i+1}. {log['role'].upper()}** — {log['timestamp']}")
                                    st.code(log["content"], language="text")
                                    st.divider()
                        else:
                            st.info("📭 No chat history yet")
                    else:
                        st.error(f"❌ Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"❌ Could not fetch logs: {e}")
    
    st.markdown("---")

st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
st.markdown('<div class="chat-title">🍽️ Restaurant Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="chat-subtitle">Ask me anything about our menu, hours, reservations & more</div>',
    unsafe_allow_html=True
)

# Display chat messages
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
                timeout=300
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

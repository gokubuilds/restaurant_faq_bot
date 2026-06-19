"""
frontend.py — Streamlit UI for RAG Chatbot
- Main chat with Iridescent Glassmorphism styling
- Sidebar Admin Panel (hardcoded login: Admin / Admin123)
- KB status shown at top of admin panel
"""

import uuid
import requests
import streamlit as st

BACKEND_URL = "https://restaurant-faq-bot-u8my.onrender.com"
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {
    --anthropic-font: "Anthropic", "Styrene B", "Inter", Arial, sans-serif;
    --ink: #111111;
    --paper: #fffaf0;
    --panel: #ffffff;
    --accent: #ff5a1f;
    --accent-2: #fae100;
    --mint: #79f2c0;
    --danger: #ff3b30;
    --shadow: 7px 7px 0 #111111;
    --shadow-sm: 4px 4px 0 #111111;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: var(--anthropic-font);
    background:
        linear-gradient(90deg, rgba(17, 17, 17, 0.055) 1px, transparent 1px),
        linear-gradient(rgba(17, 17, 17, 0.055) 1px, transparent 1px),
        var(--paper) !important;
    background-size: 32px 32px !important;
    min-height: 100vh;
    color: var(--ink);
}

[data-testid="stHeader"] { background: transparent !important; }

h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stCaptionContainer"] {
    color: var(--ink) !important;
    font-family: var(--anthropic-font) !important;
}

[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    font-weight: 900 !important;
    line-height: 1.15 !important;
}

[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    background: var(--panel);
    border: 3px solid var(--ink);
    box-shadow: var(--shadow-sm);
    display: inline-block;
    padding: 0.35rem 0.55rem;
}

[data-testid="stSidebar"] {
    background: var(--panel) !important;
    border-right: 4px solid var(--ink) !important;
    box-shadow: 8px 0 0 var(--ink) !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: var(--ink) !important;
}

#MainMenu, footer, header { visibility: hidden; }

* {
    letter-spacing: 0 !important;
}

.chat-wrapper {
    max-width: 860px;
    margin: 0 auto;
    padding: 2.25rem 1.5rem 6.5rem;
}

.chat-title {
    text-align: center;
    font-size: 2.65rem;
    font-weight: 900;
    color: var(--ink);
    text-transform: uppercase;
    margin-bottom: 0.5rem;
    line-height: 1;
    text-shadow: 3px 3px 0 var(--accent-2);
}

.chat-subtitle {
    text-align: center;
    font-size: 1rem;
    color: var(--ink);
    margin: 0 auto 2.5rem;
    font-weight: 800;
    display: table;
    background: var(--mint);
    border: 3px solid var(--ink);
    box-shadow: var(--shadow-sm);
    padding: 0.55rem 0.8rem;
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
    width: 42px; height: 42px;
    border-radius: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; flex-shrink: 0; font-weight: 600;
    border: 3px solid var(--ink);
    box-shadow: var(--shadow-sm);
}
.avatar.user {
    background: var(--accent-2);
    color: var(--ink);
}
.avatar.bot {
    background: var(--accent);
    color: var(--panel);
}

.bubble {
    max-width: 72%;
    padding: 1rem 1.15rem;
    border-radius: 0;
    line-height: 1.6;
    font-size: 0.95rem;
    word-break: break-word;
    border: 3px solid var(--ink);
    box-shadow: var(--shadow-sm);
    font-weight: 700;
}
.bubble.user {
    background: var(--accent-2);
    color: var(--ink);
}
.bubble.bot {
    background: var(--panel);
    color: var(--ink);
}

/* KB status badge */
.kb-status-active {
    background: var(--mint);
    border: 3px solid var(--ink);
    border-radius: 0;
    padding: 0.6rem 0.9rem;
    color: var(--ink);
    font-size: 0.88rem;
    font-weight: 900;
    margin-bottom: 0.5rem;
    box-shadow: var(--shadow-sm);
}
.kb-status-inactive {
    background: #ffd5d0;
    border: 3px solid var(--ink);
    border-radius: 0;
    padding: 0.6rem 0.9rem;
    color: var(--ink);
    font-size: 0.88rem;
    font-weight: 900;
    margin-bottom: 0.5rem;
    box-shadow: var(--shadow-sm);
}

[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"],
[data-testid="stBottomBlockContainer"] > div {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}

[data-testid="stBottom"] {
    padding: 0 !important;
}

[data-testid="stBottomBlockContainer"] {
    padding: 0 1.5rem 1.25rem !important;
}

[data-testid="stChatInput"] {
    width: min(720px, calc(100vw - 48px)) !important;
    margin: 0 auto !important;
    padding: 0 !important;
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}

[data-testid="stChatInput"] > div {
    min-height: 46px !important;
    background: #ffffff !important;
    border: 3px solid var(--ink) !important;
    border-radius: 0 !important;
    box-shadow: 6px 6px 0 var(--ink) !important;
    padding: 0 !important;
    overflow: hidden !important;
}

[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--ink) !important;
    box-shadow: 6px 6px 0 var(--ink) !important;
}

[data-testid="stChatInput"] div[data-baseweb="textarea"],
[data-testid="stChatInput"] div[data-baseweb="base-input"],
[data-testid="stChatInput"] div[data-baseweb="textarea"] > div,
[data-testid="stChatInput"] [data-baseweb="textarea"] {
    background: #ffffff !important;
    border: 0 !important;
    outline: 0 !important;
    box-shadow: none !important;
}

[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input {
    min-height: 40px !important;
    background: #ffffff !important;
    color: var(--ink) !important;
    border: 0 !important;
    outline: 0 !important;
    box-shadow: none !important;
    font-size: 0.95rem !important;
    font-weight: 900 !important;
    line-height: 1.25 !important;
    padding: 0.75rem 0.9rem !important;
    -webkit-text-fill-color: var(--ink) !important;
}

[data-testid="stChatInput"] button {
    width: 46px !important;
    min-width: 46px !important;
    height: 46px !important;
    background: #ffffff !important;
    color: var(--ink) !important;
    border: 0 !important;
    border-left: 3px solid var(--ink) !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    margin: 0 !important;
    padding: 0 !important;
}

[data-testid="stChatInput"] button:hover,
[data-testid="stChatInput"] button:active {
    background: #ffffff !important;
    color: var(--ink) !important;
}

[data-testid="stChatInput"] button svg {
    color: var(--ink) !important;
    fill: var(--ink) !important;
    stroke: var(--ink) !important;
}

[data-testid="stChatInput"] input::placeholder,
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--ink) !important;
    opacity: 1 !important;
    font-weight: 900 !important;
}

.stDataFrame {
    border: 3px solid var(--ink);
    border-radius: 0;
    overflow: hidden;
    background: var(--panel) !important;
    color: var(--ink) !important;
    box-shadow: var(--shadow-sm);
}

.stTextInput > div > div > input,
.stPasswordInput > div > div > input,
.stTextArea textarea {
    background: var(--panel) !important;
    color: var(--ink) !important;
    border: 3px solid var(--ink) !important;
    border-radius: 0 !important;
    font-size: 0.95rem !important;
    font-weight: 800 !important;
    box-shadow: var(--shadow-sm) !important;
}
.stTextInput > div > div > input::placeholder,
.stPasswordInput > div > div > input::placeholder,
.stTextArea textarea::placeholder { color: #525252 !important; }

.stButton > button {
    background: var(--panel) !important;
    color: var(--ink) !important;
    border: 3px solid var(--ink) !important;
    border-radius: 0 !important;
    padding: 0.6rem 1.4rem;
    font-family: var(--anthropic-font);
    font-weight: 900;
    font-size: 0.95rem;
    text-transform: uppercase;
    transition: all 0.1s ease-in-out;
    box-shadow: var(--shadow-sm) !important;
}
.stButton > button:hover {
    background: var(--accent-2) !important;
    color: var(--ink) !important;
    border: 3px solid var(--ink) !important;
}
.stButton > button:active {
    transform: translate(3px, 3px);
    box-shadow: 1px 1px 0 var(--ink) !important;
    background: var(--ink) !important;
    color: var(--panel) !important;
}

[data-testid="stFileUploader"] {
    border: 3px dashed var(--ink) !important;
    background: var(--panel) !important;
    border-radius: 0 !important;
    box-shadow: var(--shadow-sm);
}

.stSpinner { color: var(--accent) !important; }

[data-testid="stExpander"],
div[role="dialog"] {
    background: var(--panel) !important;
    border: 4px solid var(--ink) !important;
    border-radius: 0 !important;
    box-shadow: var(--shadow) !important;
}

div[role="dialog"] {
    width: min(760px, calc(100vw - 48px)) !important;
    padding: 1.5rem 1.75rem 1.75rem !important;
}

div[role="dialog"] [data-testid="stVerticalBlock"] {
    gap: 1rem !important;
}

div[role="dialog"] .stTextInput {
    margin-bottom: 0.25rem !important;
}

div[role="dialog"] .stTextInput label {
    color: var(--ink) !important;
    font-family: var(--anthropic-font) !important;
    font-weight: 900 !important;
}

div[role="dialog"] .stButton > button {
    width: auto !important;
    min-width: 94px !important;
    padding: 0.55rem 0.9rem !important;
    letter-spacing: 0.08em !important;
}

[data-testid="stTabs"] button {
    border-radius: 0 !important;
    font-weight: 900 !important;
}

[data-testid="stTabs"] [role="tablist"] {
    gap: 0.85rem !important;
    border-bottom: none !important;
    margin: 1.2rem 0 2rem !important;
}

[data-testid="stTabs"] [role="tab"] {
    background: var(--panel) !important;
    border: 3px solid var(--ink) !important;
    border-radius: 0 !important;
    box-shadow: var(--shadow-sm) !important;
    min-height: 48px !important;
    padding: 0.6rem 1rem !important;
}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: var(--accent-2) !important;
}

[data-testid="stTabs"] [role="tab"] p {
    color: var(--ink) !important;
    font-family: var(--anthropic-font) !important;
    font-size: 0.92rem !important;
    font-weight: 900 !important;
}

[data-testid="stAlert"] {
    background: #fff7b8 !important;
    border: 3px solid var(--ink) !important;
    border-radius: 0 !important;
    box-shadow: var(--shadow-sm) !important;
}

[data-testid="stAlert"] *,
[data-testid="stAlert"] p {
    color: var(--ink) !important;
    font-weight: 800 !important;
}

[data-testid="stMetric"] {
    background: var(--panel);
    border: 3px solid var(--ink);
    box-shadow: var(--shadow-sm);
    padding: 1rem 1.15rem;
    min-height: 108px;
}

[data-testid="stMetric"] label,
[data-testid="stMetric"] [data-testid="stMetricLabel"],
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--ink) !important;
    font-family: var(--anthropic-font) !important;
}

[data-testid="stMetric"] label,
[data-testid="stMetric"] [data-testid="stMetricLabel"] {
    font-size: 0.95rem !important;
    font-weight: 900 !important;
}

.admin-title {
    text-align: center;
    color: var(--ink);
    font-weight: 900;
    font-size: 2.05rem;
    text-transform: uppercase;
    text-shadow: 3px 3px 0 var(--accent-2);
    margin: 2rem auto 0.65rem;
    display: table;
    background: var(--panel);
    border: 4px solid var(--ink);
    box-shadow: var(--shadow);
    padding: 0.35rem 0.85rem;
}

.admin-auth-state {
    color: var(--ink);
    font-weight: 900;
    margin: 1rem auto 1.5rem;
    background: var(--mint);
    border: 3px solid var(--ink);
    box-shadow: var(--shadow-sm);
    padding: 0.65rem 0.85rem;
    display: table;
}

.admin-auth-state span {
    color: var(--ink);
    background: var(--accent-2);
    padding: 0.1rem 0.35rem;
    border: 2px solid var(--ink);
}

.admin-subtitle {
    color: #3f3a31;
    font-size: 0.98rem;
    font-weight: 800;
    margin: 0 auto 2rem;
    text-align: center;
}

.admin-section-spacer {
    margin-top: 1.5rem;
}

.admin-login-title {
    text-align: center;
    margin: 0 auto 1.25rem;
}

/* Floating Admin Button */
.floating-admin-btn {
    position: fixed;
    top: 30px;
    right: 30px;
    z-index: 999;
}
.floating-admin-btn button {
    width: 60px;
    height: 60px;
    border-radius: 0;
    font-size: 1.5rem;
    padding: 0 !important;
    box-shadow: var(--shadow-sm) !important;
    background: var(--accent-2) !important;
    border: 3px solid var(--ink) !important;
    color: var(--ink) !important;
}
.floating-admin-btn button:hover {
    transform: translate(-2px, -2px);
    background: var(--mint) !important;
    color: var(--ink) !important;
    border-color: var(--ink) !important;
}

/* Phone/Mobile compatibility adjustments */
@media (max-width: 640px) {
    .chat-wrapper {
        padding: 1.5rem 0.5rem 5rem;
    }
    .chat-title {
        font-size: 1.8rem;
    }
    .chat-subtitle {
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
    .bubble {
        max-width: 85%;
        padding: 0.85rem 1rem;
        font-size: 0.9rem;
    }
    .avatar {
        width: 32px;
        height: 32px;
        font-size: 1rem;
    }
    .msg-row {
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .floating-admin-btn {
        top: 15px;
        right: 15px;
    }
    .floating-admin-btn button {
        width: 50px;
        height: 50px;
        font-size: 1.25rem;
    }
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


@st.dialog("Admin Panel")
def admin_login_dialog():
    username = st.text_input("Username", placeholder="", key="dialog_admin_user")
    password = st.text_input("Password", type="password", placeholder="", key="dialog_admin_pass")

    if st.button("Log In", key="dialog_admin_login"):
        if username.strip() == "Admin" and password == "Admin123":
            st.session_state.admin_logged_in = True
            st.session_state.show_admin_modal = True
            st.rerun()
        else:
            st.error("Invalid credentials")


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
# Floating admin button HTML
# st.markdown(
#     """
#     <div class="floating-admin-btn">
#         <button onclick="document.getElementById('floating_admin_toggle').click()" 
#                 style="cursor: pointer;">⚙️</button>
#     </div>
#     """,
#     unsafe_allow_html=True
# )

# Hidden button to toggle state
if st.button("⚙️", key="floating_admin_btn"):
    if st.session_state.admin_logged_in:
        st.session_state.show_admin_modal = not st.session_state.show_admin_modal
    else:
        st.session_state.show_admin_modal = False
        admin_login_dialog()

admin_dashboard_open = (
    st.session_state.show_admin_modal and st.session_state.admin_logged_in
)

if st.session_state.show_admin_modal and st.session_state.admin_logged_in:
    st.markdown("---")
    admin_container = st.container()
    with admin_container:
        st.markdown('<h3 class="admin-title">Admin Panel</h3>', unsafe_allow_html=True)
        st.markdown(
            '<div class="admin-subtitle">Manage knowledge base content, review logs, and control admin settings.</div>',
            unsafe_allow_html=True
        )
        # Admin Dashboard After Login
        with st.container():
            st.markdown('<div class="admin-auth-state">Logged in as: <span>Admin</span></div>', unsafe_allow_html=True)
            
            # Top Controls
            action_gap_left, action_col1, action_col2, action_col3, action_gap_right = st.columns([1.4, 1, 1, 1, 1.4])
            with action_col1:
                if st.button("Refresh", use_container_width=True, key="modal_refresh"):
                    st.rerun()
            with action_col2:
                if st.button("Close Panel", use_container_width=True, key="modal_close"):
                    st.session_state.show_admin_modal = False
                    st.rerun()
            with action_col3:
                if st.button("Logout", use_container_width=True, key="modal_logout"):
                    st.session_state.admin_logged_in = False
                    st.session_state.show_admin_modal = False
                    st.rerun()
            
            st.markdown("---")
            
            # Tabs for different admin sections
            tab1, tab2, tab3, tab4 = st.tabs(["KB Status", "Upload Content", "Clear Knowledge", "Chat Logs"])
            
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
                subtab1, subtab2 = st.tabs(["PDF Upload", "Text Input"])
                
                with subtab1:
                    st.markdown("#### Upload PDF")
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
                            st.metric("Filename", uploaded_file.name)
                        with col2:
                            st.metric("File Size", f"{file_size_mb:.2f} MB")
                        
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
                    st.markdown("#### Add Text Content")
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
                            st.metric("Characters", f"{char_count:,}")
                        with stat_col2:
                            st.metric("Words", f"{word_count:,}")
                        
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
                                st.metric("Total Messages", len(logs))
                            with stat_col2:
                                user_count = sum(1 for l in logs if l["role"] == "user")
                                st.metric("User Messages", user_count)
                            with stat_col3:
                                bot_count = sum(1 for l in logs if l["role"] == "assistant")
                                st.metric("Bot Responses", bot_count)
                            with stat_col4:
                                unique_sessions = len(set(l["session_id"] for l in logs))
                                st.metric("Unique Sessions", unique_sessions)
                            
                            # Full message view
                            if st.checkbox("View Full Messages", key="view_full_logs"):
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

if not admin_dashboard_open:
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

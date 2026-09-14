import os
import re
import io
import json
import requests
import streamlit as st

# FastAPI Backend URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="AskDoc AI",
    page_icon="●",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tour_step" not in st.session_state:
    st.session_state.tour_step = 0
if "tour_active" not in st.session_state:
    st.session_state.tour_active = False
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

def get_indexed_documents():
    """Fetches list of all documents currently saved and indexed in the knowledge base."""
    try:
        r = requests.get(f"{API_URL}/documents", timeout=3)
        if r.status_code == 200:
            return r.json().get("documents", [])
    except Exception:
        pass
    return []

def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def get_file_symbol_badge(filename: str, ext: str):
    ext = ext.lower()
    if ext in [".pdf"]:
        return "[PDF]", "#38bdf8"
    elif ext in [".docx", ".doc"]:
        return "[DOC]", "#60a5fa"
    elif ext in [".csv", ".xlsx", ".xls"]:
        return "[DATA]", "#34d399"
    elif ext in [".json", ".html", ".htm"]:
        return "[WEB]", "#c084fc"
    else:
        return "[TXT]", "#94a3b8"


def build_question_with_history(prompt_text: str) -> str:
    """Builds a question string that includes recent chat history for context."""
    history_messages = st.session_state.messages[:-1]  # Exclude the current question
    recent = history_messages[-20:]  # Last 10 pairs
    if not recent:
        return prompt_text.strip()
    history_parts = []
    for msg in recent:
        role_label = "User" if msg["role"] == "user" else "Assistant"
        history_parts.append(f"{role_label}: {msg['content'][:500]}")
    history_context = "\n".join(history_parts)
    return f"[CONVERSATION HISTORY]\n{history_context}\n[END HISTORY]\n\nCurrent question: {prompt_text.strip()}"

# --- Custom ChatGPT Minimalist Theme & UI Polish ---
st.markdown(
    """
    <style>
    :root {
        --custom-sidebar-border: var(--custom-sidebar-border);
        --custom-card-border: var(--custom-card-border);
        --custom-icon-border: var(--custom-icon-border);
        --custom-icon-bg: var(--custom-icon-bg);
        --custom-pill-border: var(--custom-pill-border);
        --custom-doc-row-bg: var(--custom-doc-row-bg);
        --custom-doc-row-border: var(--custom-doc-row-border);
        --custom-doc-row-hover: var(--custom-doc-row-hover);
        --custom-accent-bg: var(--custom-accent-bg);
        --custom-text-muted: #8e8ea0;
        --custom-popup-bg: #2f2f2f;
        --custom-popup-border: var(--custom-popup-border);
        --custom-popup-hover: #404040;
    }
    
    @media (prefers-color-scheme: light) {
        :root {
            --custom-sidebar-border: rgba(0, 0, 0, 0.1);
            --custom-card-border: rgba(0, 0, 0, 0.15);
            --custom-icon-border: rgba(0, 0, 0, 0.15);
            --custom-icon-bg: rgba(0, 0, 0, 0.03);
            --custom-pill-border: rgba(0, 0, 0, 0.2);
            --custom-doc-row-bg: rgba(0, 0, 0, 0.02);
            --custom-doc-row-border: rgba(0, 0, 0, 0.08);
            --custom-doc-row-hover: rgba(0, 0, 0, 0.06);
            --custom-accent-bg: rgba(16, 163, 127, 0.08);
            --custom-text-muted: #6e6e80;
            --custom-popup-bg: #ffffff;
            --custom-popup-border: rgba(0,0,0,0.15);
            --custom-popup-hover: #f0f0f0;
        }
    }

    /* Dark ChatGPT Minimalist Palette */
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        border-right: 1px solid var(--custom-sidebar-border) !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: var(--custom-sidebar-border) !important;
        margin: 16px 0 !important;
    }
    
    /* 1. VISUAL REFERENCE CARD (Underneath) */
    .sidebar-upload-card {
        box-sizing: border-box !important;
        position: relative !important;
        width: 100% !important;
        height: 195px !important;
        min-height: 195px !important;
        max-height: 195px !important;
        border: 1.5px dashed var(--custom-card-border) !important;
        border-radius: 14px !important;
        background: var(--secondary-background-color) !important;
        padding: 18px 14px !important;
        text-align: center !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease !important;
        user-select: none !important;
        pointer-events: none !important;
        z-index: 1 !important;
        margin-bottom: 0px !important;
    }
    .sidebar-upload-icon {
        width: 44px;
        height: 44px;
        margin: 0 auto 10px auto;
        border-radius: 12px;
        border: 1px solid var(--custom-icon-border);
        background: var(--custom-icon-bg);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .sidebar-upload-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-color);
        margin-bottom: 4px;
    }
    .sidebar-upload-sub {
        font-size: 0.76rem;
        color: var(--custom-text-muted);
        line-height: 1.35;
        margin-bottom: 12px;
    }
    .sidebar-browse-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 18px;
        border-radius: 9999px;
        border: 1px solid var(--custom-pill-border);
        background: var(--secondary-background-color);
        color: var(--text-color);
        font-size: 0.82rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.15s ease;
    }

    /* 2. INVISIBLE NATIVE OVERLAY: Pull stFileUploader directly over the card */
    .sidebar-uploader-wrap,
    [data-testid="stSidebar"] [data-testid="stFileUploader"] {
        position: relative !important;
        margin-top: calc(-195px - 1rem) !important;
        width: 100% !important;
        height: 195px !important;
        min-height: 195px !important;
        max-height: 195px !important;
        padding: 0 !important;
        opacity: 0 !important;
        cursor: pointer !important;
        z-index: 10 !important;
        overflow: hidden !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] *,
    [data-testid="stSidebar"] [data-testid="stFileUploadDropzone"],
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        cursor: pointer !important;
        height: 100% !important;
        width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        background: transparent !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] input[type="file"] {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        opacity: 0 !important;
        cursor: pointer !important;
        display: block !important;
        z-index: 20 !important;
        pointer-events: auto !important;
    }

    /* 3. HOVER SYNCHRONIZATION: Highlight the reference card when hovering the invisible uploader */
    [data-testid="stSidebar"]:has([data-testid="stFileUploader"]:hover) .sidebar-upload-card {
        border-color: var(--primary-color) !important;
        background: var(--custom-accent-bg) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
    }
    [data-testid="stSidebar"]:has([data-testid="stFileUploader"]:hover) .sidebar-browse-pill {
        border-color: var(--primary-color) !important;
        color: var(--primary-color) !important;
        background: var(--secondary-background-color) !important;
    }

    /* Session Document Item */
    .doc-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 10px;
        border-radius: 8px;
        background: var(--custom-doc-row-bg);
        border: 1px solid var(--custom-doc-row-border);
        margin-bottom: 6px;
        transition: background 0.15s ease;
    }
    .doc-row:hover {
        background: var(--custom-doc-row-hover);
    }
    .doc-meta {
        display: flex;
        align-items: center;
        gap: 8px;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        font-size: 0.82rem;
    }
    [data-testid="stSidebar"] button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: var(--custom-text-muted) !important;
        padding: 2px 6px !important;
        border-radius: 6px !important;
        font-size: 0.8rem !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: rgba(239, 68, 68, 0.15) !important;
        color: #ef4444 !important;
        border-color: #ef4444 !important;
    }

    /* Constrain main conversation container to centered readable ChatGPT width */
    .stMainBlockContainer,
    [data-testid="stMainBlockContainer"],
    .main .block-container {
        max-width: 820px !important;
        margin: 0 auto !important;
        padding-top: 1.5rem !important;
        padding-bottom: 6rem !important;
        padding-left: 1.25rem !important;
        padding-right: 1.25rem !important;
    }

    /* Chat Messages styling - strictly vertical, no horizontal breaks */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 16px 0 !important;
        border-bottom: 1px solid var(--custom-doc-row-hover) !important;
        max-width: 100% !important;
        width: 100% !important;
        word-break: break-word !important;
        overflow-wrap: break-word !important;
    }
    [data-testid="stChatMessage"] .stMarkdown,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        max-width: 100% !important;
        width: 100% !important;
    }
    /* Contained horizontal scroll for tables if generated */
    [data-testid="stChatMessage"] table {
        width: 100% !important;
        max-width: 100% !important;
        display: block !important;
        overflow-x: auto !important;
        border-collapse: collapse !important;
        margin: 14px 0 !important;
    }
    [data-testid="stChatMessage"] th,
    [data-testid="stChatMessage"] td {
        border: 1px solid var(--custom-icon-border) !important;
        padding: 6px 12px !important;
        white-space: normal !important;
    }

    /* ChatGPT-style Assistant Action Bar */
    .assistant-action-bar {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        margin-top: 10px !important;
        margin-bottom: 2px !important;
    }
    .chatgpt-read-btn {
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid var(--custom-icon-border) !important;
        border-radius: 8px !important;
        padding: 5px 12px !important;
        color: #b4b4b4 !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        user-select: none !important;
    }
    .chatgpt-read-btn:hover {
        background: rgba(255, 255, 255, 0.09) !important;
        color: var(--text-color) !important;
        border-color: var(--custom-pill-border) !important;
        transform: translateY(-1px) !important;
    }
    .chatgpt-read-btn.speaking {
        background: rgba(16, 163, 127, 0.15) !important;
        border-color: var(--primary-color) !important;
        color: var(--primary-color) !important;
        box-shadow: 0 0 10px rgba(16, 163, 127, 0.25) !important;
    }
    .chatgpt-read-btn.speaking .tts-play-icon {
        display: none !important;
    }
    .chatgpt-read-btn.speaking .tts-stop-icon {
        display: inline-block !important;
        animation: pulse-stop 1.2s infinite ease-in-out !important;
    }
    @keyframes pulse-stop {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.6; transform: scale(0.92); }
    }

    /* ========== THINKING ANIMATION ========== */
    @keyframes thinking-dot {
        0%, 20% { opacity: 0.2; transform: translateY(0); }
        50% { opacity: 1; transform: translateY(-4px); }
        80%, 100% { opacity: 0.2; transform: translateY(0); }
    }
    .thinking-indicator {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 0;
    }
    .thinking-dots {
        display: flex;
        gap: 5px;
        align-items: center;
    }
    .thinking-dots span {
        width: 8px;
        height: 8px;
        background: var(--primary-color);
        border-radius: 50%;
        animation: thinking-dot 1.4s ease-in-out infinite;
    }
    .thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
    .thinking-dots span:nth-child(3) { animation-delay: 0.4s; }
    .thinking-label {
        font-size: 0.88rem;
        color: var(--custom-text-muted);
        font-style: italic;
    }

    /* ========================================================
       SEARCH BAR / CHAT INPUT UI (True ChatGPT Pill Design)
       ======================================================== */
    [data-testid="stBottom"] {
        background-color: #212121 !important;
        border-top: none !important;
        padding-bottom: 14px !important;
    }
    [data-testid="stBottom"] > div {
        background-color: transparent !important;
    }

    /* Single Centered Pill Container (No double box!) */
    [data-testid="stChatInput"] {
        max-width: 768px !important;
        width: 100% !important;
        margin: 0 auto 12px auto !important;
        background: #2f2f2f !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 28px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35) !important;
        padding: 4px 12px 4px 18px !important;
        box-sizing: border-box !important;
        display: block !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: rgba(255, 255, 255, 0.32) !important;
        box-shadow: 0 6px 26px rgba(0, 0, 0, 0.5) !important;
    }

    /* Inner containers must be transparent, borderless, and 100% width */
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] form,
    [data-testid="stChatInput"] form > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
        min-width: 100% !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
    }

    /* Textarea takes full width across the pill without wrapping */
    [data-testid="stChatInput"] textarea {
        flex: 1 1 auto !important;
        width: 100% !important;
        background: transparent !important;
        color: var(--text-color) !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
        border: none !important;
        outline: none !important;
        resize: none !important;
        box-shadow: none !important;
        padding: 8px 10px 8px 0 !important;
        margin: 0 !important;
        white-space: pre-wrap !important;
        overflow-y: hidden !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: var(--custom-text-muted) !important;
        font-size: 0.95rem !important;
    }

    /* Sleek Circular Send Button */
    [data-testid="stChatInputSubmitButton"] {
        background: #ffffff !important;
        color: #171717 !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
        min-width: 32px !important;
        min-height: 32px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: none !important;
        margin: 0 !important;
        padding: 0 !important;
        flex-shrink: 0 !important;
        cursor: pointer !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stChatInputSubmitButton"]:hover:not(:disabled) {
        background: #f1f5f9 !important;
        transform: scale(1.05) !important;
    }
    [data-testid="stChatInputSubmitButton"]:disabled {
        background: var(--custom-icon-border) !important;
        color: rgba(255, 255, 255, 0.3) !important;
        cursor: not-allowed !important;
        box-shadow: none !important;
        opacity: 0.65 !important;
    }
    [data-testid="stChatInputSubmitButton"] svg {
        width: 17px !important;
        height: 17px !important;
    }

    /* In-Bar Microphone Button (Left of Send) - Native & Fallback */
    [data-testid="stChatInputMicButton"],
    #chat-inbar-mic-btn {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: transparent !important;
        border: none !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
        min-width: 32px !important;
        min-height: 32px !important;
        cursor: pointer !important;
        color: #b4b4b4 !important;
        margin-right: 6px !important;
        padding: 0 !important;
        flex-shrink: 0 !important;
        outline: none !important;
        transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    [data-testid="stChatInputMicButton"]:hover,
    #chat-inbar-mic-btn:hover {
        background: var(--custom-icon-border) !important;
        color: var(--text-color) !important;
        transform: scale(1.06) !important;
    }
    [data-testid="stChatInputMicButton"] svg,
    #chat-inbar-mic-btn svg {
        width: 18px !important;
        height: 18px !important;
        color: inherit !important;
        fill: currentColor !important;
    }
    [data-testid="stChatInputMicButton"]:active,
    #chat-inbar-mic-btn.listening {
        color: var(--text-color) !important;
        background: #ef4444 !important;
        box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.35) !important;
        animation: mic-pulse-ring 1.3s infinite ease-in-out !important;
    }
    @keyframes mic-pulse-ring {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6); }
        50% { transform: scale(1.1); box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }

    /* --- Thinking / Searching Animation --- */
    .thinking-indicator {
        padding: 8px 0;
    }
    .thinking-dots {
        display: flex;
        gap: 6px;
        align-items: center;
    }
    .thinking-dots span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #8e8ea0;
        animation: thinkingBounce 1.4s infinite ease-in-out;
    }
    .thinking-dots span:nth-child(2) {
        animation-delay: 0.2s;
    }
    .thinking-dots span:nth-child(3) {
        animation-delay: 0.4s;
    }
    @keyframes thinkingBounce {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40% { transform: scale(1); opacity: 1; }
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Interactive Walkthrough Dialog (Only displays once on first site visit) ---
@st.dialog("AskDoc AI — Interactive Tour")
def show_tutorial_dialog():
    step = st.session_state.tour_step
    
    if step == 0:
        st.markdown("### 1. Ingest Any File Format")
        st.markdown(
            "Use the **Add Files** card in the left sidebar to upload documents.\n\n"
            "- Supports **PDF, DOCX, XLSX, CSV, JSON, HTML, and Text**.\n"
            "- *Videos and images are excluded*."
        )
    elif step == 1:
        st.markdown("### 2. Ask Questions or Speak")
        st.markdown(
            "Type your query in the chat input below, or **click the microphone button** located directly on the left of the Send button.\n\n"
            "- Instant speech-to-text recording.\n"
            "- Hands-free queries with automatic submission."
        )
    elif step == 2:
        st.markdown("### 3. Grounded Answers & Audio Output")
        st.markdown(
            "AskDoc AI guarantees zero hallucination by strictly referencing your documents.\n\n"
            "- Inspect exact document names and page numbers in **Sources & Citations**.\n"
            "- Click **Listen** at the bottom of any assistant answer to hear it read aloud.\n"
            "- The AI **remembers your conversation** — ask follow-up questions naturally."
        )

    col_prev, col_next, col_skip = st.columns([2, 3, 2])
    with col_prev:
        if step > 0:
            if st.button("Previous", key="tour_prev"):
                st.session_state.tour_step -= 1
                st.rerun()
    with col_next:
        if step < 2:
            if st.button("Next ->", type="primary", key="tour_next"):
                st.session_state.tour_step += 1
                st.rerun()
        else:
            if st.button("Finish Tour ✓", type="primary", key="tour_finish"):
                st.session_state.tour_active = False
                st.rerun()
    with col_skip:
        if st.button("Skip Tour ✕", key="tour_skip"):
            st.session_state.tour_active = False
            st.rerun()

# Trigger tour dialog if active
if st.session_state.tour_active:
    show_tutorial_dialog()

# --- SIDEBAR: "Add Files" Session ---
with st.sidebar:
    st.markdown("<h3 style='margin-bottom: 2px; color: var(--text-color); font-weight: 600;'>Add Files</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.78rem; color: var(--custom-text-muted); margin-bottom: 12px;'>PDF, Office Docs, CSV, JSON, HTML, Text (No images or videos)</p>", unsafe_allow_html=True)
    
    # Sleek Reference Dropzone Card (Native invisible overlay sits on top)
    st.markdown(
        """
        <div class="sidebar-upload-card" id="sidebar-upload-card" title="Click to browse files or drag and drop">
            <div class="sidebar-upload-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ececec" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="17 8 12 3 7 8"></polyline>
                    <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
            </div>
            <div class="sidebar-upload-title">Click to upload or drop files</div>
            <div class="sidebar-upload-sub">PDF, DOC/DOCX, XLSX, CSV, JSON, HTML, TXT</div>
            <div class="sidebar-browse-pill" id="sidebar-browse-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="12" y1="19" x2="12" y2="5"></line>
                    <polyline points="5 12 12 5 19 12"></polyline>
                </svg>
                Browse files
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # NATIVE UPLOADER: Rendered right after card, overlayed on top via CSS negative margin
    # NOTE: Images removed from accepted types per user request
    uploaded_files = st.file_uploader(
        "Upload files",
        type=["pdf", "html", "htm", "json", "docx", "doc", "txt", "md", "csv", "xlsx", "xls", "py", "log"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=f"sidebar_files_{st.session_state.uploader_key}"
    )

    # If user selected files, render a sleek status card, file list, and index/clear buttons
    if uploaded_files:
        files_summary_html = "".join([
            f"<div style='font-size: 0.72rem; color: var(--text-color); margin-top: 3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>• {f.name} ({(len(f.getvalue()) / 1024):.1f} KB)</div>"
            for f in uploaded_files[:4]
        ])
        if len(uploaded_files) > 4:
            files_summary_html += f"<div style='font-size: 0.7rem; color: var(--custom-text-muted); margin-top: 2px;'>... and {len(uploaded_files) - 4} more</div>"
            
        st.markdown(
            f"""
            <div style="background: rgba(16, 163, 127, 0.1); border: 1px solid rgba(16, 163, 127, 0.4); border-radius: 12px; padding: 12px; margin-top: 10px; margin-bottom: 8px;">
                <div style="color: var(--primary-color); font-weight: 600; font-size: 0.85rem; margin-bottom: 4px;">✓ {len(uploaded_files)} file{'s' if len(uploaded_files) > 1 else ''} selected</div>
                {files_summary_html}
            </div>
            """,
            unsafe_allow_html=True
        )
        col_idx, col_clr = st.columns([3, 1])
        with col_idx:
            if st.button(f"Index {len(uploaded_files)} File{'s' if len(uploaded_files) > 1 else ''} ->", type="primary", width="stretch"):
                prog = st.progress(0)
                indexed_count = 0
                has_error = False
                for idx_f, f_item in enumerate(uploaded_files):
                    with st.spinner(f"Indexing {f_item.name}..."):
                        f_mime = f_item.type or "application/octet-stream"
                        file_payload = {"file": (f_item.name, f_item.getvalue(), f_mime)}
                        try:
                            resp = requests.post(f"{API_URL}/documents/upload", files=file_payload, timeout=300)
                            if resp.status_code == 200:
                                indexed_count += 1
                            else:
                                st.error(f"{f_item.name}: {resp.json().get('detail', 'Upload failed')}")
                                has_error = True
                        except Exception as ex:
                            st.error(f"{f_item.name}: {ex}")
                            has_error = True
                    prog.progress((idx_f + 1) / len(uploaded_files))
                
                st.session_state.uploader_key += 1
                if indexed_count > 0:
                    st.toast(f"Successfully indexed {indexed_count} file(s).")
                
                if has_error:
                    import time
                    time.sleep(4)
                    
                st.rerun()
        with col_clr:
            if st.button("✕", width="stretch", help="Clear selected files"):
                st.session_state.uploader_key += 1
                st.rerun()

    st.divider()

    # Active Session Documents with Individual Deletion
    session_docs = get_indexed_documents()
    st.markdown(f"<div style='font-size: 0.88rem; font-weight: 600; color: var(--text-color); margin-bottom: 8px;'>Active Documents ({len(session_docs)})</div>", unsafe_allow_html=True)
    
    if session_docs:
        for d in session_docs:
            badge_symbol, badge_color = get_file_symbol_badge(d["name"], d["ext"])
            col_doc_name, col_doc_del = st.columns([8, 2])
            with col_doc_name:
                st.markdown(
                    f"""
                    <div class="doc-meta" title="{d['name']}">
                        <span style="color: {badge_color}; font-weight: 700; font-size: 0.72rem;">{badge_symbol}</span>
                        <span style="color: var(--text-color); text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">{d['name']}</span>
                        <span style="color: #71717a; font-size: 0.72rem;">({format_size(d['size'])})</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_doc_del:
                if st.button("✕", key=f"del_doc_{d['name']}", help=f"Delete {d['name']} from session"):
                    try:
                        del_res = requests.delete(f"{API_URL}/documents/{d['name']}", timeout=10)
                        if del_res.status_code == 200:
                            st.toast(f"Deleted {d['name']}")
                            st.rerun()
                        else:
                            st.error("Delete failed.")
                    except Exception as err:
                        st.error(f"Error: {err}")
    else:
        st.markdown("<p style='font-size: 0.78rem; color: #71717a;'>No documents indexed yet.</p>", unsafe_allow_html=True)

    st.divider()
    
    # Sidebar footer actions
    col_clear, col_tour = st.columns(2)
    with col_clear:
        if st.button("⌫ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col_tour:
        if st.button("? Tour", use_container_width=True, help="Revisit interactive walkthrough"):
            st.session_state.tour_step = 0
            st.session_state.tour_active = True
            st.rerun()

# --- MAIN CONVERSATION VIEWPORT ---
active_docs = get_indexed_documents()
doc_count = len(active_docs)

# Subtle Minimal Top Bar
col_title, col_status = st.columns([8, 2])
with col_title:
    st.markdown("<h2 style='margin: 0; font-weight: 600; color: var(--text-color);'>AskDoc AI</h2>", unsafe_allow_html=True)
with col_status:
    badge_label = f"{doc_count} document{'s' if doc_count != 1 else ''} active"
    st.markdown(
        f"<div style='text-align: right; padding-top: 6px;'><span style='background: var(--custom-doc-row-border); border: 1px solid var(--custom-popup-border); border-radius: 9999px; padding: 4px 12px; font-size: 0.78rem; color: var(--custom-text-muted);'>● {badge_label}</span></div>",
        unsafe_allow_html=True
    )

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# Fetch active doc names once for source filtering
active_doc_names = {d["name"] for d in active_docs}

# Conversation Stream
if not st.session_state.messages:
    # Minimalist ChatGPT empty state
    st.markdown(
        """
        <div style="text-align: center; margin-top: 80px; margin-bottom: 60px;">
            <div style="font-size: 1.8rem; font-weight: 600; color: var(--text-color); margin-bottom: 8px;">What would you like to know?</div>
            <div style="font-size: 0.95rem; color: var(--custom-text-muted); max-width: 540px; margin: 0 auto 28px auto;">
                Ask questions grounded directly in your uploaded policies, reports, spreadsheets, or documents. I remember our conversation, so feel free to ask follow-ups.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # If assistant response: Show sources and per-response ChatGPT-style audio button
            if message["role"] == "assistant":
                # Sources & Citations (strictly filtered against active session documents)
                raw_sources = message.get("sources", []) or []
                valid_sources = [s for s in raw_sources if s.get("source") in active_doc_names]
                if valid_sources:
                    with st.expander("Sources & Citations", expanded=False):
                        for src in valid_sources:
                            st.markdown(f"- **{src['source']}** (Page {src['page']})")
                
                # ChatGPT-Style Instant Natural AI Speech Action Bar
                import urllib.parse
                raw_txt_encoded = urllib.parse.quote(message["content"])
                st.markdown(
                    f"""
                    <div class="assistant-action-bar">
                        <button class="chatgpt-read-btn" id="tts-btn-{idx}" data-idx="{idx}" data-text="{raw_txt_encoded}" title="Read answer aloud with natural AI voice">
                            <svg class="tts-play-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                                <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                                <path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
                            </svg>
                            <svg class="tts-stop-icon" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="display: none;">
                                <rect x="6" y="6" width="12" height="12" rx="2"></rect>
                            </svg>
                            <span class="tts-btn-text">Read aloud</span>
                        </button>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

import json
import streamlit.components.v1 as components

# --- TEXT & VOICE CHAT INPUT (with real-time thinking animation) ---
# Inject JS to augment the native st.chat_input with @mention support
active_docs_for_mention = get_indexed_documents()
active_doc_names = [d["name"] for d in active_docs_for_mention]
docs_json = json.dumps(active_doc_names)

js_code = f"""
<script>
    const docs = {docs_json};
    const parentDoc = document;
    
    function setupMention() {{
        const textarea = parentDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
        if (!textarea) {{
            setTimeout(setupMention, 500);
            return;
        }}
        
        if (textarea.dataset.mentionAttached) return;
        textarea.dataset.mentionAttached = 'true';
        
        let popup = parentDoc.getElementById('native-mention-popup');
        if (!popup) {{
            popup = parentDoc.createElement('div');
            popup.id = 'native-mention-popup';
            popup.style.display = 'none';
            popup.style.position = 'absolute';
            popup.style.bottom = '100%';
            popup.style.left = '0';
            popup.style.width = '100%';
            popup.style.maxHeight = '200px';
            popup.style.overflowY = 'auto';
            popup.style.backgroundColor = 'var(--custom-popup-bg)';
            popup.style.border = '1px solid var(--custom-popup-border)';
            popup.style.borderRadius = '16px';
            popup.style.zIndex = '999999';
            popup.style.marginBottom = '10px';
            popup.style.boxShadow = '0 10px 20px rgba(0,0,0,0.3)';
            popup.style.padding = '8px 0';
            
            const style = parentDoc.createElement('style');
            style.innerHTML = `
                #native-mention-popup::-webkit-scrollbar {{ width: 8px; }}
                #native-mention-popup::-webkit-scrollbar-thumb {{ background-color: #4a4a4a; border-radius: 4px; }}
            `;
            parentDoc.head.appendChild(style);
            
            const container = parentDoc.querySelector('[data-testid="stChatInput"]');
            if (container) {{
                container.style.position = 'relative';
                container.appendChild(popup);
            }}
        }}
        
        let currentFilteredDocs = [];
        let selectedIndex = 0;
        let lastAtPos = -1;
        
        function renderPopup() {{
            popup.innerHTML = '';
            currentFilteredDocs.forEach((doc, idx) => {{
                const item = parentDoc.createElement('div');
                item.textContent = doc;
                item.style.padding = '10px 16px';
                item.style.color = 'var(--text-color)';
                item.style.cursor = 'pointer';
                item.style.fontFamily = '"Source Sans Pro", sans-serif';
                item.style.fontSize = '15px';
                item.style.backgroundColor = (idx === selectedIndex) ? 'var(--custom-popup-hover)' : 'transparent';
                
                item.addEventListener('mouseenter', () => {{
                    selectedIndex = idx;
                    renderPopup();
                }});
                
                item.addEventListener('mousedown', function(evt) {{
                    evt.preventDefault();
                    applyMention(doc);
                }});
                
                popup.appendChild(item);
            }});
        }}
        
        function applyMention(docName) {{
            const val = textarea.value;
            const cursor = textarea.selectionStart;
            const before = val.substring(0, lastAtPos);
            const after = val.substring(cursor);
            
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
            const newValue = before + '@' + docName + ' ' + after;
            nativeInputValueSetter.call(textarea, newValue);
            textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
            
            popup.style.display = 'none';
            
            // Move cursor to end of inserted mention
            const newPos = before.length + docName.length + 2;
            setTimeout(() => {{
                textarea.setSelectionRange(newPos, newPos);
                textarea.focus();
            }}, 0);
        }}
        
        textarea.addEventListener('input', function(e) {{
            const val = textarea.value;
            const cursor = textarea.selectionStart;
            const textBefore = val.substring(0, cursor);
            lastAtPos = textBefore.lastIndexOf('@');
            
            // If the chat was submitted and input cleared
            if (val.trim() === '') {{
                popup.style.display = 'none';
                return;
            }}
            
            if (lastAtPos !== -1 && (lastAtPos === 0 || textBefore[lastAtPos - 1] === ' ')) {{
                const query = textBefore.substring(lastAtPos + 1);
                currentFilteredDocs = docs.filter(d => d.toLowerCase().includes(query.toLowerCase()));
                
                if (currentFilteredDocs.length > 0) {{
                    selectedIndex = 0; // reset selection
                    renderPopup();
                    popup.style.display = 'block';
                }} else {{
                    popup.style.display = 'none';
                }}
            }} else {{
                popup.style.display = 'none';
            }}
        }});
        
        // Use capture phase to intercept Tab/Enter before Streamlit's native handlers
        textarea.addEventListener('keydown', function(e) {{
            if (popup.style.display === 'block') {{
                if (e.key === 'Tab' || e.key === 'Enter') {{
                    e.preventDefault();
                    e.stopImmediatePropagation(); // Stop Streamlit from sending the message early!
                    
                    if (currentFilteredDocs.length > 0) {{
                        applyMention(currentFilteredDocs[selectedIndex]);
                    }}
                }} else if (e.key === 'ArrowDown') {{
                    e.preventDefault();
                    selectedIndex = (selectedIndex + 1) % currentFilteredDocs.length;
                    renderPopup();
                    // Scroll into view
                    const items = popup.children;
                    if(items[selectedIndex]) items[selectedIndex].scrollIntoView({{block: 'nearest'}});
                }} else if (e.key === 'ArrowUp') {{
                    e.preventDefault();
                    selectedIndex = (selectedIndex - 1 + currentFilteredDocs.length) % currentFilteredDocs.length;
                    renderPopup();
                    const items = popup.children;
                    if(items[selectedIndex]) items[selectedIndex].scrollIntoView({{block: 'nearest'}});
                }} else if (e.key === 'Escape') {{
                    popup.style.display = 'none';
                }}
            }} else if (e.key === 'Enter' && !e.shiftKey) {{
                // If popup is closed and user sends message, hide popup just in case
                setTimeout(() => popup.style.display = 'none', 50);
            }}
        }}, true);
        
        textarea.addEventListener('blur', () => {{
            setTimeout(() => popup.style.display = 'none', 150);
        }});
    }}
    
    setupMention();
</script>
"""
st.html(js_code, unsafe_allow_javascript=True)

if user_prompt := st.chat_input("Ask a question about your documents...", accept_audio=True):
    query_text = ""
    if isinstance(user_prompt, str):
        query_text = user_prompt.strip()
    else:
        text_val = getattr(user_prompt, "text", "") or ""
        if text_val and text_val.strip():
            query_text = text_val.strip()
            
        audio_val = getattr(user_prompt, "audio", None)
        if audio_val and not query_text:
            with st.spinner("Transcribing your spoken question..."):
                try:
                    audio_bytes = audio_val.getvalue()
                    mime_type = audio_val.type or "audio/wav"
                    fname = audio_val.name or "voice_recording.wav"
                    file_payload = {"file": (fname, audio_bytes, mime_type)}
                    resp = requests.post(f"{API_URL}/transcribe", files=file_payload, timeout=45)
                    if resp.status_code == 200:
                        transcribed = resp.json().get("transcription", "").strip()
                        if transcribed:
                            query_text = transcribed
                        else:
                            st.warning("No speech detected in recording.")
                    else:
                        st.error(f"Transcription error: {resp.text}")
                except Exception as ex:
                    st.error(f"Transcription connection error: {ex}")
                    
    if query_text:
        # 1. Add user message to state and display it immediately
        st.session_state.messages.append({"role": "user", "content": query_text})
        with st.chat_message("user"):
            st.markdown(query_text)

        # 2. Show real-time thinking animation while making API call
        with st.chat_message("assistant"):
            thinking_placeholder = st.empty()
            thinking_placeholder.markdown(
                """
                <div class="thinking-indicator">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8e8ea0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation: spin 1.5s linear infinite;">
                            <circle cx="12" cy="12" r="10"></circle>
                            <path d="M12 6v6l4 2"></path>
                        </svg>
                        <span style="color: var(--custom-text-muted); font-size: 0.9rem;">Searching through your documents...</span>
                    </div>
                    <div class="thinking-dots" style="margin-top: 8px;">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # 3. Build question with history context and make API call
            question_with_context = build_question_with_history(query_text)
            answer = ""
            sources = []
            try:
                response = requests.post(
                    f"{API_URL}/ask",
                    json={"question": question_with_context},
                    timeout=180
                )
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    sources = data.get("sources", [])
                else:
                    answer = f"Notice: {response.json().get('detail', 'Failed to retrieve answer.')}"
            except Exception as e:
                answer = f"Connection error: {e}"

            # 4. Replace thinking animation with the actual answer
            thinking_placeholder.markdown(answer)

            # 5. Show sources if any
            if sources:
                valid_sources = [s for s in sources if s.get("source") in active_doc_names]
                if valid_sources:
                    with st.expander("Sources & Citations", expanded=False):
                        for src in valid_sources:
                            st.markdown(f"- **{src['source']}** (Page {src['page']})")

        # 6. Save assistant response to state
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })
        st.rerun()

# --- JAVASCRIPT: REDIRECT GREEN BOX TO FILE MANAGER & INJECT IN-BAR MIC ---
client_enhancements_js = r"""
<script>
(function() {
  const pDoc = window.parent ? window.parent.document : document;

  // 1. Open File Manager helper (for programmatic triggers)
  function openSidebarFilePicker() {
    try {
      const fi = pDoc.querySelector('[data-testid="stSidebar"] input[type="file"]') ||
                 pDoc.querySelector('input[type="file"]');
      if (fi) {
        fi.click();
      }
    } catch(err) {
      console.error("Error triggering file manager:", err);
    }
  }

  // Expose globally to window and parent window
  window.openSidebarFilePicker = openSidebarFilePicker;
  if (window.parent) {
    window.parent.openSidebarFilePicker = openSidebarFilePicker;
  }

  // 2. Attach drag synchronization between overlay and visual card
  function attachCardListeners() {
    try {
      const card = pDoc.getElementById('sidebar-upload-card') || document.getElementById('sidebar-upload-card');
      const uploader = pDoc.querySelector('[data-testid="stSidebar"] [data-testid="stFileUploader"]');
      if (uploader && card && !uploader.dataset.boundDrag) {
        uploader.dataset.boundDrag = "true";
        uploader.addEventListener('dragover', function(e) {
          card.style.borderColor = 'var(--primary-color)';
          card.style.background = 'rgba(16, 163, 127, 0.08)';
        });
        uploader.addEventListener('dragleave', function(e) {
          card.style.borderColor = 'var(--custom-card-border)';
          card.style.background = '#1e1e1e';
        });
        uploader.addEventListener('drop', function(e) {
          card.style.borderColor = 'var(--custom-card-border)';
          card.style.background = '#1e1e1e';
        });
      }
    } catch(e) {}
  }

  // 3. Microphone Injection Directly on the Left Side of the Send Button
  function initMic() {
    try {
      const submitBtn = pDoc.querySelector('button[data-testid="stChatInputSubmitButton"]');
      if (!submitBtn) return;
      
      const parentContainer = submitBtn.parentElement;
      if (!parentContainer || parentContainer.querySelector('#chat-inbar-mic-btn') || parentContainer.querySelector('[data-testid="stChatInputMicButton"]')) return;
      
      parentContainer.style.display = 'inline-flex';
      parentContainer.style.alignItems = 'center';
      parentContainer.style.flexShrink = '0';
      parentContainer.style.margin = '0';
      parentContainer.style.padding = '0';
      
      const micBtn = pDoc.createElement('button');
      micBtn.id = 'chat-inbar-mic-btn';
      micBtn.type = 'button';
      micBtn.title = 'Speak input';
      micBtn.setAttribute('aria-label', 'Speak input');
      micBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
        </svg>
      `;
      
      let isRecording = false;
      let recognition = null;
      let mediaRecorder = null;
      let audioChunks = [];
      const SpeechRecognition = window.parent ? (window.parent.SpeechRecognition || window.parent.webkitSpeechRecognition) : (window.SpeechRecognition || window.webkitSpeechRecognition);
      
      micBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const chatContainer = submitBtn.closest('[data-testid="stChatInput"]');
        const textarea = chatContainer ? chatContainer.querySelector('textarea') : null;
        if (!textarea) return;
        
        if (isRecording) {
          if (recognition) recognition.stop();
          if (mediaRecorder && mediaRecorder.state === "recording") mediaRecorder.stop();
          stopListening(textarea);
          return;
        }
        
        if (SpeechRecognition) {
          try {
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.lang = 'en-US';
            
            let finalTranscript = '';
            
            recognition.onstart = function() {
              isRecording = true;
              micBtn.classList.add('listening');
              textarea.setAttribute('data-orig-placeholder', textarea.placeholder);
              textarea.placeholder = "Listening... Speak your question";
            };
            
            recognition.onresult = function(event) {
              let interim = '';
              for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                  finalTranscript += event.results[i][0].transcript;
                } else {
                  interim += event.results[i][0].transcript;
                }
              }
              const currentText = finalTranscript || interim;
              if (currentText) {
                setNativeValue(textarea, currentText);
              }
            };
            
            recognition.onerror = function(event) {
              console.warn('SpeechRecognition error:', event.error);
              stopListening(textarea);
            };
            
            recognition.onend = function() {
              stopListening(textarea);
              if (finalTranscript.trim()) {
                setNativeValue(textarea, finalTranscript.trim());
                setTimeout(function() {
                  const currentSubmitBtn = pDoc.querySelector('button[data-testid="stChatInputSubmitButton"]');
                  if (currentSubmitBtn && !currentSubmitBtn.disabled) {
                    currentSubmitBtn.click();
                  }
                }, 200);
              }
            };
            
            recognition.start();
          } catch(err) {
            fallbackRecorder(textarea, submitBtn, pDoc);
          }
        } else {
          fallbackRecorder(textarea, submitBtn, pDoc);
        }
      });
      
      function stopListening(textarea) {
        isRecording = false;
        micBtn.classList.remove('listening');
        const orig = textarea.getAttribute('data-orig-placeholder');
        if (orig) textarea.placeholder = orig;
      }
      
      function setNativeValue(element, value) {
        const proto = window.parent ? window.parent.HTMLTextAreaElement.prototype : HTMLTextAreaElement.prototype;
        const setVal = Object.getOwnPropertyDescriptor(proto, 'value').set;
        setVal.call(element, value);
        element.dispatchEvent(new Event('input', { bubbles: true }));
      }
      
      function fallbackRecorder(textarea, submitBtn, doc) {
        const nav = window.parent ? window.parent.navigator : navigator;
        if (!nav.mediaDevices || !nav.mediaDevices.getUserMedia) {
          alert("Microphone not supported in this browser.");
          return;
        }
        nav.mediaDevices.getUserMedia({ audio: true }).then(function(stream) {
          audioChunks = [];
          const MR = window.parent ? window.parent.MediaRecorder : MediaRecorder;
          mediaRecorder = new MR(stream);
          mediaRecorder.ondataavailable = function(e) { audioChunks.push(e.data); };
          mediaRecorder.onstart = function() {
            isRecording = true;
            micBtn.classList.add('listening');
            textarea.placeholder = "Recording... Click mic again to send";
          };
          mediaRecorder.onstop = function() {
            stopListening(textarea);
            stream.getTracks().forEach(function(t) { t.stop(); });
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const formData = new FormData();
            formData.append('file', audioBlob, 'mic.wav');
            textarea.placeholder = "Transcribing audio...";
            fetch('http://127.0.0.1:8000/transcribe', {
              method: 'POST',
              body: formData
            }).then(function(r) { return r.json(); }).then(function(data) {
              if (data.transcription) {
                setNativeValue(textarea, data.transcription);
                setTimeout(function() {
                  const currentSubmitBtn = doc.querySelector('button[data-testid="stChatInputSubmitButton"]');
                  if (currentSubmitBtn && !currentSubmitBtn.disabled) currentSubmitBtn.click();
                }, 200);
              }
            }).catch(function(err) {
              console.error("Transcription error:", err);
            });
          };
          mediaRecorder.start();
        }).catch(function(err) {
          alert("Microphone access denied: " + err.message);
        });
      }
      
      // Place mic button immediately before send button inside parentContainer
      parentContainer.insertBefore(micBtn, submitBtn);
    } catch(err) {
      console.warn("initMic note:", err);
    }
  }

  // 4. Instant Natural AI Speech Synthesis Manager (Sentence-chunked, Markdown-cleaned, Neural Voice)
  let speechQueue = [];
  let isSpeaking = false;
  let activeSpeechBtn = null;

  function getTopSynth() {
    try {
      if (window.parent && window.parent.speechSynthesis) return window.parent.speechSynthesis;
    } catch(e) {}
    if (typeof window !== "undefined" && window.speechSynthesis) return window.speechSynthesis;
    return null;
  }

  function cleanMarkdownForNaturalSpeech(md) {
    if (!md) return "";
    let text = md;
    text = text.replace(/```[\s\S]*?```/g, "Code block omitted.");
    text = text.replace(/`([^`]+)`/g, "$1");
    text = text.replace(/\|\s*[-:]+[-|\s:]*\|/g, " ");
    text = text.replace(/\|/g, ", ");
    text = text.replace(/^#{1,6}\s*(.+)$/gm, "$1. ");
    text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
    text = text.replace(/https?:\/\/\S+/g, "");
    text = text.replace(/(\*\*|__)(.*?)\1/g, "$2");
    text = text.replace(/(\*|_)(.*?)\1/g, "$2");
    text = text.replace(/~~(.*?)~~/g, "$1");
    text = text.replace(/^\s*[-*+•]\s+/gm, "");
    text = text.replace(/\(Page\s*\d+\)/gi, "");
    text = text.replace(/\[[A-Z]{3,4}\]/g, "");
    text = text.replace(/(\d+)\/(\d+)/g, "$1 out of $2");
    text = text.replace(/(→|->|-->)/g, " to ");
    text = text.replace(/[*_~`]/g, "");
    text = text.replace(/,\s*,/g, ",");
    text = text.replace(/\s*,\s*/g, ", ");
    text = text.replace(/^,\s*/, "");
    text = text.replace(/[ \t]+/g, " ");
    text = text.replace(/\n+/g, " ");
    return text.trim();
  }

  function getBestNaturalVoice() {
    const s = getTopSynth();
    if (!s) return null;
    const voices = s.getVoices();
    if (!voices || voices.length === 0) return null;
    const preferredOrder = [
      "jenny", "guy", "natural", "neural", "online", "aria", "christopher", 
      "eric", "steffan", "google us english", "samantha", "daniel"
    ];
    for (const kw of preferredOrder) {
      const match = voices.find(v => v.lang && v.lang.startsWith("en") && v.name.toLowerCase().includes(kw));
      if (match) return match;
    }
    const enVoice = voices.find(v => v.lang && v.lang.startsWith("en"));
    if (enVoice) return enVoice;
    return voices[0];
  }

  function splitIntoSpeechChunks(text) {
    const sentences = text.match(/[^.!?:\n]+[.!?:\n]+|[^.!?:\n]+$/g) || [text];
    const chunks = [];
    let current = "";
    for (const s of sentences) {
      const trimmed = s.trim();
      if (!trimmed) continue;
      if (current.length + trimmed.length > 180) {
        if (current) chunks.push(current.trim());
        current = trimmed;
      } else {
        current = current ? current + " " + trimmed : trimmed;
      }
    }
    if (current) chunks.push(current.trim());
    return chunks;
  }

  function stopAllSpeech() {
    const s = getTopSynth();
    if (s) s.cancel();
    speechQueue = [];
    isSpeaking = false;
    if (activeSpeechBtn) {
      activeSpeechBtn.classList.remove('speaking');
      const txt = activeSpeechBtn.querySelector('.tts-btn-text');
      if (txt) txt.textContent = "Read aloud";
      activeSpeechBtn = null;
    }
    pDoc.querySelectorAll('.chatgpt-read-btn').forEach(b => {
      b.classList.remove('speaking');
      const txt = b.querySelector('.tts-btn-text');
      if (txt) txt.textContent = "Read aloud";
    });
  }

  function playNextSpeechChunk() {
    if (speechQueue.length === 0) {
      stopAllSpeech();
      return;
    }
    const s = getTopSynth();
    if (!s) return;

    const chunkText = speechQueue.shift();
    const UtteranceClass = (window.parent && window.parent.SpeechSynthesisUtterance) || window.SpeechSynthesisUtterance;
    const utterance = new UtteranceClass(chunkText);
    const voice = getBestNaturalVoice();
    if (voice) utterance.voice = voice;
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onend = function() {
      if (isSpeaking) {
        playNextSpeechChunk();
      }
    };

    utterance.onerror = function(err) {
      console.warn("TTS chunk note:", err);
      if (isSpeaking && speechQueue.length > 0) {
        playNextSpeechChunk();
      } else {
        stopAllSpeech();
      }
    };

    s.speak(utterance);
  }

  function toggleSpeech(btn, rawText) {
    const s = getTopSynth();
    if (!s) {
      alert("Speech synthesis is not supported in this browser.");
      return;
    }

    if (isSpeaking && activeSpeechBtn === btn) {
      stopAllSpeech();
      return;
    }

    stopAllSpeech();

    const cleanText = cleanMarkdownForNaturalSpeech(rawText);
    if (!cleanText) return;

    speechQueue = splitIntoSpeechChunks(cleanText);
    if (speechQueue.length === 0) return;

    isSpeaking = true;
    activeSpeechBtn = btn;
    btn.classList.add('speaking');
    const txt = btn.querySelector('.tts-btn-text');
    if (txt) txt.textContent = "Stop";

    playNextSpeechChunk();
  }

  // Delegated click listener on pDoc to handle Read Aloud buttons cleanly
  pDoc.addEventListener('click', function(e) {
    const btn = e.target.closest('.chatgpt-read-btn');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();

    let rawText = "";
    try {
      const enc = btn.getAttribute('data-text');
      if (enc) rawText = decodeURIComponent(enc);
    } catch(err) {}

    if (!rawText) {
      const msgElem = btn.closest('[data-testid="stChatMessage"]') || btn.closest('.stChatMessage');
      if (msgElem) {
        const clone = msgElem.cloneNode(true);
        clone.querySelectorAll('.assistant-action-bar, [data-testid="stExpander"], .streamlit-expander').forEach(el => el.remove());
        rawText = clone.innerText || clone.textContent || "";
      }
    }
    toggleSpeech(btn, rawText);
  });

  // Observers and Timers to maintain bindings across Streamlit reruns
  try {
    const observer = new MutationObserver(function() {
      initMic();
      attachCardListeners();
    });
    observer.observe(pDoc.body, { childList: true, subtree: true });
  } catch(e) {}

  initMic();
  attachCardListeners();
  setTimeout(function() { initMic(); attachCardListeners(); }, 300);
  setTimeout(function() { initMic(); attachCardListeners(); }, 1000);
  setTimeout(function() { initMic(); attachCardListeners(); }, 2500);
})();
</script>
"""
st.html(client_enhancements_js, unsafe_allow_javascript=True)

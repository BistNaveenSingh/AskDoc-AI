import os
import re
import io
import requests
import streamlit as st
from gtts import gTTS

# FastAPI Backend URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="AntiRag System", page_icon="📚", layout="wide")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tutorial_dismissed" not in st.session_state:
    st.session_state.tutorial_dismissed = False
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None
if "show_uploader" not in st.session_state:
    st.session_state.show_uploader = True
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

def get_file_badge_info(filename: str, ext: str):
    ext = ext.lower()
    if ext in [".pdf"]:
        return "📄", "PDF Document", "#38bdf8"
    elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
        return "🖼️", "Image (OCR)", "#f43f5e"
    elif ext in [".docx", ".doc"]:
        return "📝", "Word Doc", "#3b82f6"
    elif ext in [".csv", ".xlsx", ".xls"]:
        return "📊", "Spreadsheet", "#10b981"
    elif ext in [".json", ".html", ".htm"]:
        return "🌐", "Web / Data", "#a855f7"
    else:
        return "📃", "Text File", "#64748b"

def generate_speech(text: str) -> bytes:
    """
    Converts text to speech bytes using gTTS.
    Strips basic markdown syntax for natural pronunciation.
    """
    try:
        clean_text = re.sub(r'[*_#`\[\]]', '', text)
        tts = gTTS(text=clean_text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        st.warning(f"Audio generation failed: {e}")
        return None

def submit_query(prompt_text: str, speak: bool):
    """
    Sends the user question to the backend and records the answer & sources in session state.
    """
    # 1. Add user message
    st.session_state.messages.append({"role": "user", "content": prompt_text})
    
    # 2. Query backend
    try:
        response = requests.post(f"{API_URL}/ask", json={"question": prompt_text})
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            sources = data.get("sources", [])
            
            # 3. Generate speech if enabled
            audio_bytes = generate_speech(answer) if speak and answer else None
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources,
                "audio": audio_bytes
            })
        else:
            error_detail = response.json().get("detail", "Failed to retrieve answer.")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"⚠️ Error: {error_detail}"
            })
    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"⚠️ Connection error: {e}"
        })

# --- Sidebar ---
with st.sidebar:
    st.header("📄 Add Files")
    st.caption("PDF, DOC/DOCX, XLSX, CSV, PNG, or JPG (Videos excluded).")
    sidebar_files = st.file_uploader(
        "Upload files",
        type=["pdf", "png", "jpg", "jpeg", "webp", "bmp", "html", "htm", "json", "docx", "doc", "txt", "md", "csv", "xlsx", "xls", "py", "log"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=f"sidebar_uploader_{st.session_state.uploader_key}"
    )
    
    if sidebar_files:
        if st.button(f"⚡ Process {len(sidebar_files)} File{'s' if len(sidebar_files) > 1 else ''}", type="primary", key="btn_side_process"):
            with st.spinner("Uploading & indexing files..."):
                s_count = 0
                for f_item in sidebar_files:
                    f_mime = f_item.type or "application/octet-stream"
                    files = {"file": (f_item.name, f_item.getvalue(), f_mime)}
                    try:
                        resp = requests.post(f"{API_URL}/documents/upload", files=files)
                        if resp.status_code == 200:
                            s_count += 1
                    except Exception as err:
                        st.error(f"Error {f_item.name}: {err}")
                st.session_state.uploader_key += 1
                st.success(f"Indexed {s_count} file(s) into session!")
                st.rerun()
                
    st.divider()
    # Sidebar session summary
    side_docs = get_indexed_documents()
    st.markdown(f"**📚 Session Files ({len(side_docs)})**")
    if side_docs:
        for d in side_docs[:5]:
            icon, label, color = get_file_badge_info(d["name"], d["ext"])
            st.markdown(f"<small>{icon} {d['name']} ({format_size(d['size'])})</small>", unsafe_allow_html=True)
        if len(side_docs) > 5:
            st.caption(f"+ {len(side_docs) - 5} more files in session")
    else:
        st.caption("No files added yet.")

    st.divider()
    st.header("⚙️ Audio & Settings")
    speak_enabled = st.toggle("🔊 Speak responses (Voice Output)", value=False, help="Automatically read answers aloud using Text-to-Speech")
    
    st.divider()
    col_clear, col_guide = st.columns(2)
    with col_clear:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.last_audio_hash = None
            st.rerun()
    with col_guide:
        if st.session_state.tutorial_dismissed:
            if st.button("❓ Show Guide"):
                st.session_state.tutorial_dismissed = False
                st.rerun()

# --- Main App Header ---
st.title("📚 AntiRag: Universal Document QA System")
st.caption("AI question-answering for PDFs, Images, HTML, JSON, Word & Text with strict anti-hallucination guardrails.")

# --- Beginner Tutorial (Skippable) ---
if not st.session_state.tutorial_dismissed:
    with st.container(border=True):
        col_text, col_btn = st.columns([5, 1])
        with col_text:
            st.markdown("### 🚀 Quick Start Guide")
            st.markdown(
                "1. **Upload Files**: Browse or drag-and-drop any PDF, image (scanned docs, receipts, diagrams), HTML, JSON, Word (.docx), or spreadsheet into the dropzone below (videos excluded).\n"
                "2. **Process Document**: Click **⚡ Index Files** to extract text, run Gemini Vision OCR on diagrams, and build vector embeddings.\n"
                "3. **Ask Questions**: Type in the chat box or use the **🎙️ Voice Question** microphone at the bottom to speak!\n"
                "4. **Voice Output**: Toggle **Speak responses** in the sidebar to hear answers read aloud."
            )
        with col_btn:
            if st.button("Skip Guide ✕", key="btn_skip_guide"):
                st.session_state.tutorial_dismissed = True
                st.rerun()

# --- Custom Styling for Reference Image Dropzone ---
st.markdown(
    """
    <style>
    /* Reference Image Dropzone Card */
    .upload-card-outer {
        background: #0d0f14;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 22px;
        padding: 22px;
        margin: 12px 0 20px 0;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.45);
    }
    .upload-card-inner {
        border: 1.5px dashed rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        padding: 30px 16px 22px 16px;
        text-align: center;
        background: #08090d;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .upload-card-inner:hover {
        border-color: #38bdf8;
        background: rgba(56, 189, 248, 0.02);
    }
    .upload-icon-box {
        width: 62px;
        height: 54px;
        margin: 0 auto 12px auto;
        border-radius: 16px;
        border: 1.5px solid rgba(255, 255, 255, 0.16);
        background: rgba(255, 255, 255, 0.03);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .upload-hero-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 5px;
        letter-spacing: -0.01em;
    }
    .upload-hero-formats {
        font-size: 0.88rem;
        color: #94a3b8;
        margin-bottom: 16px;
        font-weight: 400;
    }
    .session-badge-shelf {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        padding: 10px 0;
    }
    .session-doc-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        font-size: 0.82rem;
        color: #e2e8f0;
        transition: all 0.2s ease;
    }
    .session-doc-badge:hover {
        border-color: #38bdf8;
        background: rgba(56, 189, 248, 0.06);
    }
    /* Style the native file uploader button to match reference pill */
    [data-testid="stFileUploader"] {
        padding: 0 !important;
    }
    [data-testid="stFileUploadDropzone"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    [data-testid="stFileUploadDropzoneInstructions"] {
        display: none !important;
    }
    [data-testid="stFileUploadDropzone"] button {
        border-radius: 9999px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        background: #141720 !important;
        color: #e2e8f0 !important;
        padding: 8px 24px !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        margin: 0 auto !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stFileUploadDropzone"] button:hover {
        border-color: #38bdf8 !important;
        color: #38bdf8 !important;
        background: rgba(56, 189, 248, 0.12) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Files Adding Session (Active Knowledge Base & Drag & Drop Zone) ---
active_docs = get_indexed_documents()
doc_count = len(active_docs)

# Session Header Bar
col_sess_info, col_sess_action = st.columns([7, 3])
with col_sess_info:
    st.markdown(
        f"#### 📁 Active Session Documents &nbsp; <span style='font-size: 0.82rem; padding: 3px 10px; border-radius: 9999px; background: rgba(56, 189, 248, 0.12); color: #38bdf8; font-weight: 600;'>{doc_count} Loaded</span>",
        unsafe_allow_html=True
    )
with col_sess_action:
    toggle_text = "➖ Hide Upload Box" if st.session_state.show_uploader else "➕ Add More Files"
    if st.button(toggle_text, key="toggle_upload_box"):
        st.session_state.show_uploader = not st.session_state.show_uploader
        st.rerun()

# Upload Zone matching Reference Image
if st.session_state.show_uploader:
    st.markdown(
        """
        <div class="upload-card-outer">
            <div class="upload-card-inner" onclick="const b = document.querySelector('[data-testid=\\'stFileUploadDropzone\\'] button') || document.querySelector('button[kind=\\'secondary\\']'); if(b) b.click();" style="cursor: pointer;" title="Click to browse files or drag and drop">
                <div class="upload-icon-box">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="5" y="3" width="14" height="18" rx="3" ry="3"></rect>
                        <path d="M12 9v6"></path>
                        <path d="M9 12l3-3 3 3"></path>
                    </svg>
                </div>
                <div class="upload-hero-title">Click to upload or drop files</div>
                <div class="upload-hero-formats">PDF, DOC/DOCX, XLSX, CSV, PNG, or JPG</div>
                <div style="margin-top: 14px;">
                    <div style="display: inline-flex; align-items: center; gap: 8px; padding: 7px 24px; border-radius: 9999px; border: 1px solid rgba(255, 255, 255, 0.2); background: #141720; color: #e2e8f0; font-size: 0.88rem; font-weight: 500; box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="12" y1="19" x2="12" y2="5"></line>
                            <polyline points="5 12 12 5 19 12"></polyline>
                        </svg>
                        Browse files
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    main_files = st.file_uploader(
        "Upload files",
        type=["pdf", "png", "jpg", "jpeg", "webp", "bmp", "html", "htm", "json", "docx", "doc", "txt", "md", "csv", "xlsx", "xls", "py", "log"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=f"main_dropzone_{st.session_state.uploader_key}"
    )
    
    if main_files:
        col_btn_idx, col_btn_status = st.columns([4, 6])
        with col_btn_idx:
            if st.button(f"⚡ Index {len(main_files)} File{'s' if len(main_files) > 1 else ''} into Session", type="primary", key="btn_index_main_files"):
                prog = st.progress(0)
                idx_success = 0
                for idx_f, f_obj in enumerate(main_files):
                    with st.spinner(f"Indexing {f_obj.name} (Extracting content & Vision OCR)..."):
                        f_mime = f_obj.type or "application/octet-stream"
                        file_payload = {"file": (f_obj.name, f_obj.getvalue(), f_mime)}
                        try:
                            upload_res = requests.post(f"{API_URL}/documents/upload", files=file_payload, timeout=60)
                            if upload_res.status_code == 200:
                                idx_success += 1
                            else:
                                st.error(f"Error {f_obj.name}: {upload_res.json().get('detail', 'Upload failed')}")
                        except Exception as up_err:
                            st.error(f"Connection error on {f_obj.name}: {up_err}")
                    prog.progress((idx_f + 1) / len(main_files))
                st.session_state.uploader_key += 1
                st.success(f"🎉 Successfully indexed {idx_success} file(s) into your active session!")
                st.rerun()

# Display Current Session Files Shelf
if active_docs:
    with st.expander(f"📚 View All {doc_count} Indexed Files in Session", expanded=(doc_count <= 6)):
        cols = st.columns(3)
        for d_idx, d_info in enumerate(active_docs):
            target_col = cols[d_idx % 3]
            d_icon, d_type, d_color = get_file_badge_info(d_info["name"], d_info["ext"])
            with target_col:
                st.markdown(
                    f"""
                    <div class="session-doc-badge">
                        <span style="font-size: 1.15rem;">{d_icon}</span>
                        <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            <strong style="color: #f8fafc;">{d_info['name']}</strong><br>
                            <span style="font-size: 0.72rem; color: #94a3b8;">{format_size(d_info['size'])} • <span style="color: {d_color};">{d_type}</span> • <span style="color: #10b981;">Indexed</span></span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
else:
    st.info("💡 No files in current session. Drop files above or browse to start querying.")
# --- Chat History Display ---
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display clean, collapsible sources if available
        if message.get("sources"):
            with st.expander("📄 Sources & Citations", expanded=False):
                for src in message["sources"]:
                    st.markdown(f"- **{src['source']}** (Page {src['page']})")
                    
        # Display audio player if speech was generated
        if message.get("audio"):
            # Autoplay only the latest message if speech is enabled
            is_latest = (idx == len(st.session_state.messages) - 1)
            st.audio(message["audio"], format="audio/mp3", autoplay=(is_latest and speak_enabled))

# --- Prominent Bottom Voice Input Bar (100% Visible & Instant) ---
with st.container(border=True):
    v_col_label, v_col_rec, v_col_info = st.columns([2, 6, 2])
    with v_col_label:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 8px; height: 100%; padding-top: 6px;">
                <span style="font-size: 1.3rem;">🎙️</span>
                <span style="font-weight: 700; color: #38bdf8; font-size: 0.95rem;">Voice Question</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with v_col_rec:
        voice_rec = st.audio_input(
            "Record voice question",
            label_visibility="collapsed",
            key="direct_voice_recorder"
        )
        if voice_rec is not None:
            voice_data = voice_rec.getvalue()
            v_hash = hash(voice_data)
            if st.session_state.get("last_audio_hash") != v_hash:
                st.session_state.last_audio_hash = v_hash
                with st.spinner("🎙️ Transcribing and searching documents..."):
                    try:
                        files = {"file": ("voice_question.wav", voice_data, "audio/wav")}
                        t_res = requests.post(f"{API_URL}/transcribe", files=files)
                        if t_res.status_code == 200:
                            v_text = t_res.json().get("transcription", "").strip()
                            if v_text:
                                submit_query(v_text, speak=speak_enabled)
                                st.rerun()
                            else:
                                st.warning("No speech detected.")
                    except Exception as err:
                        st.error(f"Voice error: {err}")
    with v_col_info:
        st.markdown(
            """
            <div style="font-size: 0.75rem; color: #94a3b8; height: 100%; display: flex; align-items: center; line-height: 1.2;">
                <span>🔴 Click to speak<br>⚡ Instant answer</span>
            </div>
            """,
            unsafe_allow_html=True
        )

# --- Text Chat Input ---
if prompt := st.chat_input("Ask a question about your documents..."):
    submit_query(prompt, speak=speak_enabled)
    st.rerun()

# --- Gemini-Style Microphone Button Injection ---
import streamlit.components.v1 as components

gemini_mic_js = """
<script>
(function() {
  function initMic() {
    try {
      const doc = window.parent.document;
      const submitBtn = doc.querySelector('button[data-testid="stChatInputSubmitButton"]');
      if (!submitBtn) return;
      
      const parentContainer = submitBtn.parentElement;
      if (!parentContainer || parentContainer.querySelector('#gemini-mic-btn')) return;
      
      // Inject CSS into parent document if not already present
      if (!doc.querySelector('#gemini-mic-style')) {
        const style = doc.createElement('style');
        style.id = 'gemini-mic-style';
        style.textContent = `
          #gemini-mic-btn {
            display: inline-flex !important;
            align-items: center;
            justify-content: center;
            background: transparent;
            border: none;
            border-radius: 50%;
            width: 34px;
            height: 34px;
            cursor: pointer;
            color: #94a3b8;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            margin-right: 4px;
            padding: 0;
            outline: none;
            flex-shrink: 0;
            position: relative;
            z-index: 10;
          }
          #gemini-mic-btn:hover {
            background: rgba(255, 255, 255, 0.15);
            color: #38bdf8;
            transform: scale(1.08);
          }
          #gemini-mic-btn.listening {
            color: #ffffff !important;
            background: #ef4444 !important;
            box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.35);
            animation: gemini-mic-pulse 1.3s infinite ease-in-out;
          }
          @keyframes gemini-mic-pulse {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6); }
            50% { transform: scale(1.1); box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
            100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
          }
        `;
        doc.head.appendChild(style);
      }
      
      const micBtn = doc.createElement('button');
      micBtn.id = 'gemini-mic-btn';
      micBtn.type = 'button';
      micBtn.title = 'Speak your question (Gemini style)';
      micBtn.setAttribute('aria-label', 'Speak your question');
      micBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
          <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
        </svg>
      `;
      
      let isRecording = false;
      let recognition = null;
      let mediaRecorder = null;
      let audioChunks = [];
      const SpeechRecognition = window.parent.SpeechRecognition || window.parent.webkitSpeechRecognition;
      
      micBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const chatContainer = submitBtn.closest('[data-testid="stChatInput"]');
        const textarea = chatContainer ? chatContainer.querySelector('textarea') : null;
        if (!textarea) return;
        
        if (isRecording) {
          if (recognition) recognition.stop();
          if (mediaRecorder && mediaRecorder.state === "recording") mediaRecorder.stop();
          stopListeningState(textarea);
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
              textarea.placeholder = "🎙️ Listening... Speak your question";
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
              stopListeningState(textarea);
            };
            
            recognition.onend = function() {
              stopListeningState(textarea);
              if (finalTranscript.trim()) {
                setNativeValue(textarea, finalTranscript.trim());
                setTimeout(function() {
                  const currentSubmitBtn = doc.querySelector('button[data-testid="stChatInputSubmitButton"]');
                  if (currentSubmitBtn && !currentSubmitBtn.disabled) {
                    currentSubmitBtn.click();
                  }
                }, 200);
              }
            };
            
            recognition.start();
          } catch (err) {
            console.error("SpeechRecognition error:", err);
            fallbackRecorder(textarea, submitBtn, doc);
          }
        } else {
          fallbackRecorder(textarea, submitBtn, doc);
        }
      });
      
      function stopListeningState(textarea) {
        isRecording = false;
        micBtn.classList.remove('listening');
        const orig = textarea.getAttribute('data-orig-placeholder');
        if (orig) textarea.placeholder = orig;
      }
      
      function setNativeValue(element, value) {
        const proto = window.parent.HTMLTextAreaElement.prototype;
        const setVal = Object.getOwnPropertyDescriptor(proto, 'value').set;
        setVal.call(element, value);
        element.dispatchEvent(new Event('input', { bubbles: true }));
      }
      
      function fallbackRecorder(textarea, submitBtn, doc) {
        if (!window.parent.navigator.mediaDevices || !window.parent.navigator.mediaDevices.getUserMedia) {
          alert("Microphone not supported in this browser.");
          return;
        }
        window.parent.navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream) {
          audioChunks = [];
          mediaRecorder = new window.parent.MediaRecorder(stream);
          mediaRecorder.ondataavailable = function(e) { audioChunks.push(e.data); };
          mediaRecorder.onstart = function() {
            isRecording = true;
            micBtn.classList.add('listening');
            textarea.placeholder = "🎙️ Recording... Click mic again to send";
          };
          mediaRecorder.onstop = function() {
            stopListeningState(textarea);
            stream.getTracks().forEach(function(t) { t.stop(); });
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const formData = new FormData();
            formData.append('file', audioBlob, 'mic.wav');
            textarea.placeholder = "⏳ Transcribing audio...";
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
      
      parentContainer.insertBefore(micBtn, submitBtn);
    } catch(err) {
      console.warn("initMic parent access note:", err);
    }
  }
  
  try {
    const pDoc = window.parent.document;
    const observer = new MutationObserver(initMic);
    observer.observe(pDoc.body, { childList: true, subtree: true });
  } catch(e) {}
  
  initMic();
  setTimeout(initMic, 300);
  setTimeout(initMic, 1000);
  setTimeout(initMic, 2500);
})();
</script>
"""
components.html(gemini_mic_js, height=0)



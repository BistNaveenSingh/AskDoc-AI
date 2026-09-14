# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-07)

**Core value:** Users get accurate, source-cited answers from their documents — never hallucinated content.
**Current focus:** All v1 phases complete

## Active Phase

Phase 7: ChatGPT-Style UI Redesign & Streamlined UX

## Phase Tracking

- [x] Phase 1: Scaffolding & Setup
- [x] Phase 2: Document Ingestion & Chunking
- [x] Phase 3: Embeddings & Vector Store
- [x] Phase 4: Retrieval & LLM Generation
- [x] Phase 5: FastAPI Backend
- [x] Phase 6: Streamlit UI
- [x] Phase 7: ChatGPT-Style UI Redesign & Streamlined UX



## Phase Completion Notes

### Phase 1: Scaffolding & Setup ✅
- Python venv with all dependencies (requirements.txt)
- `.env.example` with OPENAI_API_KEY placeholder
- `README.md` with setup instructions
- Modular `src/` structure with `__init__.py` in all packages
- Directories: `src/ingestion/`, `src/embeddings/`, `src/retrieval/`, `src/api/`, `src/ui/`, `data/`, `db/`

### Phase 2: Document Ingestion & Chunking ✅
- `src/ingestion/document_processor.py` — PDF text extraction via PyPDFLoader
- `clean_text()` strips excess whitespace
- RecursiveCharacterTextSplitter: 800-char chunks, 100-char overlap
- Source filename + page number in metadata

### Phase 3: Embeddings & Vector Store ✅
- `src/embeddings/vector_store.py` — OpenAI text-embedding-3-small
- FAISS local vector store with save/load to `db/faiss_index/`
- Supports incremental document addition to existing index
- Retriever returns top-k similar chunks

### Phase 4: Retrieval & LLM Generation ✅
- `src/retrieval/qa_chain.py` — GPT-4o-mini via LangChain LCEL
- Strict system prompt: "I don't know" when answer not in context
- Source citations (filename + page) appended to answers
- `answer_question()` returns structured dict with question, answer, sources

### Phase 5: FastAPI Backend ✅
- `src/api/main.py` — 3 endpoints:
  - `POST /documents/upload` — upload + process PDF in one step
  - `POST /documents/process` — re-process already-uploaded file
  - `POST /ask` — question answering with citations
- Proper error handling, file validation, vector store checks

### Phase 6: Streamlit UI ✅
- `src/ui/app.py` — chat interface with sidebar file upload
- Session-state chat history
- Source citations displayed below answers
- Connects to FastAPI backend at localhost:8000

### Phase 7: ChatGPT-Style UI Redesign & Streamlined UX ✅
- Removed red-marked UI clutter: floating voice recorder bar, global audio toggle, duplicate main upload box
- Relocated reference dropzone card to sidebar "Add Files" session; clicking card triggers system file manager
- In-bar microphone button placed directly on left of Send button inside `st.chat_input`
- ChatGPT-style per-response `🔊 Listen` audio action at the bottom of assistant messages
- Added `DELETE /documents/{filename}` endpoint and instant vector index updating
- Each active document has a clean `✕` delete button in sidebar
- Interactive multi-step onboarding guide (`st.dialog`) that runs only once per site visit (persisted via `localStorage`)
- Minimalist dark aesthetic (`#212121` / `#2f2f2f`) with clean monochrome symbols instead of emojis


### Quick Task: Purge Stale Citations & Conversational Guardrails ✅
- Purged stale chunks (`cars_data.csv`) from FAISS vector store; added automatic disk sync in `src/embeddings/vector_store.py`.
- Added greeting/chitchat detector in `src/retrieval/qa_chain.py` returning `sources: []`.
- Added grounded citation verification: 'I don't know' responses and missing context never cite documents.
- Active document filtering added to both backend QA chain and Streamlit frontend.

## Session Continuity

Last session: 2026-09-14
Stopped at: Stale citations bug fixed and verified
Resume file: None


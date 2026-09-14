# Project Roadmap

## Proposed Roadmap

**6 phases** | **15 requirements mapped** | All v1 requirements covered ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Scaffolding & Setup | Initialize the project structure, dependencies, and environment configuration. | None | 2 |
| 2 | Document Ingestion & Chunking | Extract text from text-based PDFs and split it into overlapping chunks with metadata. | DOC-01, DOC-02, DOC-03, DOC-04 | 3 |
| 3 | Embeddings & Vector Store | Embed text chunks using OpenAI and store them in a local FAISS index. | RET-01, RET-02 | 2 |
| 4 | Retrieval & LLM Generation | Retrieve relevant chunks for a question, generate an answer using GPT-4o-mini with citations, and apply relevance guardrails. | RET-03, GEN-01, GEN-02, GEN-03 | 3 |
| 5 | FastAPI Backend | Expose the ingestion, processing, and Q&A capabilities through REST endpoints. | API-01, API-02, API-03 | 2 |
| 6 | Streamlit UI | Provide a web interface for uploading documents and interacting with the Q&A system. | UI-01, UI-02 | 2 |
| 7 | ChatGPT-Style UI Redesign & Streamlined UX | Minimalist dark ChatGPT theme, in-bar microphone, per-response audio, deletable session files, and interactive onboarding guide. | UI-03, UI-04, UI-05 | 5 |
| 7.1 | Natural AI Voice & Instant Read Aloud | Replace robotic gTTS and server reruns with instant, fluent natural AI speech via client-side Web Speech Synthesis, toggle play/stop, and zero page reload. | UI-06 | 3 |

### Phase Details

**Phase 1: Scaffolding & Setup**
Goal: Initialize the project structure, dependencies, and environment configuration.
Requirements: None
**Mode:** mvp
Success criteria:
1. Python environment is set up with required dependencies (LangChain, PyMuPDF, FAISS, FastAPI, Streamlit, etc.).
2. `.env.example` and `README.md` are created.

**Phase 2: Document Ingestion & Chunking**
Goal: Extract text from text-based PDFs and split it into overlapping chunks with metadata.
Requirements: DOC-01, DOC-02, DOC-03, DOC-04
**Mode:** mvp
Success criteria:
1. Text is successfully extracted from a sample PDF using PyMuPDF.
2. Text is cleaned of excess whitespace.
3. Text is split into chunks of ~500-800 tokens with ~100 token overlap, with source filename and page number attached.

**Phase 3: Embeddings & Vector Store**
Goal: Embed text chunks using OpenAI and store them in a local FAISS index.
Requirements: RET-01, RET-02
**Mode:** mvp
Success criteria:
1. Text chunks are successfully converted into embeddings using `text-embedding-3-small`.
2. Embeddings and their metadata are saved to a local FAISS vector store on disk.

**Phase 4: Retrieval & LLM Generation**
Goal: Retrieve relevant chunks for a question, generate an answer using GPT-4o-mini with citations, and apply relevance guardrails.
Requirements: RET-03, GEN-01, GEN-02, GEN-03
**Mode:** mvp
Success criteria:
1. A similarity search correctly returns the top-k relevant chunks for a given question.
2. The LLM generates a coherent answer grounded in the provided context, appending the source filename and page number.
3. The system returns an explicit "not found" message if the retrieved chunks are irrelevant to the question.

**Phase 5: FastAPI Backend**
Goal: Expose the ingestion, processing, and Q&A capabilities through REST endpoints.
Requirements: API-01, API-02, API-03
**Mode:** mvp
Success criteria:
1. `POST /documents/upload` and `POST /documents/process` correctly accept and process a PDF file into the vector store.
2. `POST /ask` correctly accepts a question and returns the generated answer and source citations in JSON format.

**Phase 6: Streamlit UI**
Goal: Provide a web interface for uploading documents and interacting with the Q&A system.
Requirements: UI-01, UI-02
**Mode:** mvp
Success criteria:
1. Users can upload a PDF via the Streamlit interface, successfully hitting backend endpoints.
2. Users can ask questions in a chat interface and see the AI's response along with citations.

**Phase 7: ChatGPT-Style UI Redesign & Streamlined UX**
Goal: Transform the UI into a clean, minimalist ChatGPT-inspired experience with embedded mic, per-response audio, deletable files, and interactive onboarding guide.
Requirements: UI-03, UI-04, UI-05
**Mode:** mvp
Success criteria:
1. Red-marked clutter is eliminated (no floating voice container, no global audio toggle, no duplicate upload card).
2. Reference upload dropzone card is housed in the sidebar "Add Files" session and triggers the file picker on click.
3. Microphone is embedded inside the chat input immediately to the left of the send button.
4. Spoken audio playback is located at the bottom of each assistant message like ChatGPT.
5. Session files can be deleted individually with updated indexing.
6. Interactive tutorial guide runs once per site visit.

**Phase 7.1: Natural AI Voice & Instant Read Aloud**
Goal: Upgrade response reading to instant, fluent, natural AI speech using browser-native Speech Synthesis (Neural AI voices) with zero latency, zero page reruns, markdown stripping, and play/stop toggle.
Requirements: UI-06
**Mode:** mvp
Success criteria:
1. Clicking "Read aloud" starts playback instantly without page reload, server spinner, or generating a new response.
2. Voice uses high-definition natural neural English voices (e.g. Microsoft Natural or Google US English) instead of robotic gTTS.
3. Formatted markdown, code blocks, and source citations are cleanly stripped so speech flows like natural human conversational reading.
4. Button toggles between Play and Stop (`⏹ Stop`) with active audio indication.


# Requirements

## v1 Requirements

### API Backend
- [ ] **API-01**: User can upload a PDF document via a `POST /documents/upload` endpoint.
- [ ] **API-02**: User can trigger document processing via a `POST /documents/process` endpoint.
- [ ] **API-03**: User can submit a natural-language question via a `POST /ask` endpoint and receive a JSON response with the answer and source citations.

### Document Processing
- [ ] **DOC-01**: System extracts text from text-based PDFs using PyMuPDF (with PyPDF2 fallback).
- [ ] **DOC-02**: System cleans extracted text (removes excess whitespace/headers where possible).
- [ ] **DOC-03**: System splits text into overlapping chunks (~500–800 tokens, ~100 token overlap) using `RecursiveCharacterTextSplitter`.
- [ ] **DOC-04**: System attaches source file name and page number metadata to each chunk.

### Embedding & Retrieval
- [ ] **RET-01**: System embeds text chunks using OpenAI `text-embedding-3-small`.
- [ ] **RET-02**: System stores embedded chunks and metadata in a local FAISS vector store.
- [ ] **RET-03**: System embeds the user's question and performs a similarity search in FAISS (retrieving top-k chunks, e.g., k=4).

### LLM Generation
- [ ] **GEN-01**: System populates a prompt template with retrieved chunks and the user's question, instructing the LLM to answer *only* from the provided context.
- [ ] **GEN-02**: System generates the answer using OpenAI `GPT-4o-mini`.
- [ ] **GEN-03**: System returns an explicit "I cannot find the answer in the provided documents" response if retrieved chunks fall below a relevance threshold (guardrails against hallucination).

### User Interface
- [ ] **UI-01**: System provides a Streamlit web interface for uploading PDFs.
- [ ] **UI-02**: System provides a Streamlit chat interface for asking questions and displaying answers with citations.

## v2 Requirements (Deferred)

- **V2-01**: Multi-turn conversation memory.
- **V2-02**: Multi-document filtering (e.g., query only a specific subset of uploaded docs).
- **V2-03**: Hybrid search (keyword + semantic) and reranking.
- **V2-04**: Deployment via Docker to Azure/AWS/GCP.
- **V2-05**: Automated RAG evaluation using RAGAS.

## Out of Scope

- **OCR for Scanned PDFs**: Explicitly excluded from v1 to keep the focus on core RAG concepts rather than Tesseract dependencies and image preprocessing.
- **Per-User Isolation and Authentication**: Explicitly excluded from v1 to avoid the complexity of namespacing and login systems while learning RAG fundamentals.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| API-01 | Phase 5 | ⏳ Pending |
| API-02 | Phase 5 | ⏳ Pending |
| API-03 | Phase 5 | ⏳ Pending |
| DOC-01 | Phase 2 | ⏳ Pending |
| DOC-02 | Phase 2 | ⏳ Pending |
| DOC-03 | Phase 2 | ⏳ Pending |
| DOC-04 | Phase 2 | ⏳ Pending |
| RET-01 | Phase 3 | ⏳ Pending |
| RET-02 | Phase 3 | ⏳ Pending |
| RET-03 | Phase 4 | ⏳ Pending |
| GEN-01 | Phase 4 | ⏳ Pending |
| GEN-02 | Phase 4 | ⏳ Pending |
| GEN-03 | Phase 4 | ⏳ Pending |
| UI-01 | Phase 6 | ⏳ Pending |
| UI-02 | Phase 6 | ⏳ Pending |

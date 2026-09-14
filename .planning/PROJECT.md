# AskDoc AI — AI-Powered Document Question Answering System

## What This Is

A Retrieval-Augmented Generation (RAG) application that lets users upload PDF documents (policies, manuals, reports) and ask natural-language questions about them. The system retrieves relevant passages, generates answers grounded only in document content with source citations, and explicitly says "I don't know" when the answer isn't in the documents. Built as a learning-first project to deeply understand RAG pipelines end to end.

## Core Value

**Users get accurate, source-cited answers from their documents — never hallucinated content.** If the answer isn't in the documents, the system says so.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Upload PDF documents via API and UI
- [ ] Extract text from text-based PDFs (PyMuPDF with PyPDF2 fallback)
- [ ] Split extracted text into overlapping chunks with metadata (source file, page number)
- [ ] Embed chunks using OpenAI text-embedding-3-small and store in FAISS
- [ ] Accept natural-language questions and retrieve relevant chunks via similarity search
- [ ] Generate answers using GPT-4o-mini grounded only in retrieved context
- [ ] Return source citations (filename + page number) with every answer
- [ ] Refuse to answer (explicit "not found" response) when retrieved chunks don't clear relevance threshold
- [ ] Expose full pipeline through FastAPI REST endpoints
- [ ] Provide a Streamlit UI with file upload and chat interface

### Out of Scope

- OCR / scanned PDF support — adds Tesseract complexity; v1 handles text-based PDFs only, OCR is a stretch goal
- Per-user document isolation / authentication — single shared document store for v1; user separation deferred to stretch goals
- Multi-document filtering (query specific docs) — deferred to stretch goals
- Conversation memory / multi-turn chat — deferred to stretch goals
- Hybrid search (keyword + semantic) and reranking — deferred to stretch goals
- RAG evaluation framework (RAGAS) — deferred to stretch goals
- Containerization and cloud deployment — deferred to stretch goals
- Real-time streaming responses — not needed for learning project
- Database-backed document metadata — FAISS + filesystem is sufficient for v1

## Context

This project is primarily a **learning exercise** to deeply understand how RAG systems work — from PDF parsing through chunking, embedding, retrieval, prompt engineering, and answer generation. The codebase should be modular (separate files per concern), well-commented, and built step-by-step so each component can be studied independently.

The eventual ambition is public-facing, but v1 is single-user, locally-run, and focused on getting the full pipeline correct and well-understood. Documents will range from 10-page policy docs to 500+ page manuals.

**Tech ecosystem:**
- Python 3.11+ with LangChain orchestrating the RAG pipeline
- OpenAI API for both LLM (GPT-4o-mini) and embeddings (text-embedding-3-small)
- FAISS for local vector storage (no external database)
- PyMuPDF for PDF parsing, PyPDF2 as fallback
- FastAPI for the REST API layer
- Streamlit for the optional web UI
- LangChain's RecursiveCharacterTextSplitter for chunking

## Constraints

- **LLM Provider**: OpenAI only for v1 — GPT-4o-mini for generation, text-embedding-3-small for embeddings. Keeps the stack simple and cost low (~$0.15/M input tokens)
- **Vector Store**: FAISS (local, in-memory/on-disk) — no external vector DB setup required
- **No secrets in code**: All API keys via `.env` file, `.env.example` committed as reference
- **Modularity**: Separate files for ingestion, chunking, embeddings, retrieval, generation, API — never one monolithic script
- **Learning-first**: Every file and function must include explanatory comments; code clarity over cleverness

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| OpenAI over Ollama/local models | Fastest to get running, minimal setup, pennies in cost — learning focus is on RAG architecture not model hosting | — Pending |
| FAISS over ChromaDB/Pinecone | Zero infrastructure, runs locally, sufficient for learning — can swap later | — Pending |
| PyMuPDF primary, PyPDF2 fallback | PyMuPDF is faster and handles more PDF variants; PyPDF2 is a safety net | — Pending |
| Text PDFs only for v1 (no OCR) | OCR adds Tesseract dependency + accuracy issues — scope creep for a learning project | — Pending |
| Single shared doc store (no auth) | Per-user isolation adds auth + namespacing complexity — not needed to learn RAG | — Pending |
| Streamlit UI included in v1 | Makes learning tangible and demo-friendly — worth the minimal extra effort | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-07 after initialization*

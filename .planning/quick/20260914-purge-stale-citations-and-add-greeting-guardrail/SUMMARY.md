---
status: complete
date: 2026-09-14
---

# Quick Task Summary: Purge Stale Citations & Conversational Guardrails

## Outcome
Fixed the issue where the system cited non-existent files (`cars_data.csv`) and hallucinated document citations for casual greetings like "hey" or unanswerable questions.

## Changes Implemented
1. **Vector Store Self-Healing (`src/embeddings/vector_store.py`)**:
   - Added `sync_vector_store_with_disk()` to verify FAISS docstore against active files in `data/`.
   - Any chunks referencing deleted files (e.g. `cars_data.csv`, `yearly_budget.csv`, etc.) are automatically pruned.
   - Integrated into `get_retriever()` so orphaned chunks can never be retrieved under any condition.
2. **Conversational Greeting Detector (`src/retrieval/qa_chain.py`)**:
   - Added `is_greeting_or_chitchat()` to recognize friendly greetings ("hey", "hello", "good morning", "thanks", "who are you", etc.).
   - Returns a helpful assistant welcoming message with zero document retrieval and empty sources: `sources: []`.
3. **Active Document Guardrail & Grounded Citations (`src/retrieval/qa_chain.py`)**:
   - Only document chunks whose source file exists on disk in `data/` are allowed into the generation context.
   - If the LLM answer is "I don't know" or indicates missing context, `sources` is strictly set to `[]` to prevent false citations.
4. **UI Source Filtering (`src/ui/app.py`)**:
   - Filtered citations in `st.chat_message("assistant")` against active session documents (`active_doc_names`).
   - If `sources` is empty, the "Sources & Citations" expander is omitted.
5. **Backend & Frontend Restart**:
   - Restarted FastAPI server (port 8000) and Streamlit (port 8501).
   - Executed `scratch/test_verification_citations.py` confirming 100% test pass.

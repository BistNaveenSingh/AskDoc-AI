# Quick Task Plan: Purge Stale Citations and Add Greeting Guardrails

## Objectives
1. Purge any stale/orphaned document chunks from FAISS vector store and add automatic synchronization with disk in `src/embeddings/vector_store.py`.
2. Add greeting and chitchat guardrails to `src/retrieval/qa_chain.py` so greetings ("hey", "hello", etc.) never trigger retrieval or cite random document pages.
3. Add grounded citation logic to `src/retrieval/qa_chain.py` so "I don't know" answers never attach false source citations.
4. Add frontend active-document citation filtering in `src/ui/app.py`.
5. Restart backend/frontend services and verify with automated requests.

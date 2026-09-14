# AskDoc AI — AI-Powered Document Question Answering System

A Retrieval-Augmented Generation (RAG) application that lets users upload documents (PDFs, DOCX, Spreadsheets, Images, Reports) and ask natural-language questions about them. The system retrieves relevant passages, generates answers grounded only in document content with exact source citations, and explicitly says "I don't know" when the answer isn't in the documents.

## Features
- **Multi-Format Ingestion**: Support for PDF, DOCX, XLSX, CSV, JSON, HTML, and Images with Vision OCR.
- **RAG Q&A with Strict Grounding**: Answers grounded exclusively in uploaded files — zero hallucinations.
- **Verifiable Citations**: Exact file names and page numbers cited for every factual statement.
- **Live Voice Input & AI Voice Readout**: In-bar microphone for speech queries and natural neural voice read-aloud.
- **ChatGPT-Inspired UI**: Minimalist, centered reading container with interactive onboarding walkthrough.
- **FastAPI Backend & Streamlit Frontend**: Production-ready, modular REST architecture.

## Tech Stack
- **Python 3.11+**
- **LangChain** for RAG orchestration.
- **Gemini & OpenAI API** (`gemini-3.5-flash-lite`, `gpt-4o-mini`, `text-embedding-3-small`).
- **FAISS** for fast local vector search.
- **PyMuPDF & Tesseract/Vision** for document and image extraction.
- **FastAPI** & **Streamlit** for backend and frontend.

## Setup Instructions

1. **Clone the repository** and navigate to the project directory.

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Copy the example environment file and configure your API keys (`GEMINI_API_KEY` or `OPENAI_API_KEY`).
   ```bash
   cp .env.example .env
   ```

## Running the Application

AskDoc AI consists of two components: the **FastAPI backend** (API & RAG pipeline) and the **Streamlit frontend** (chat UI).

### Option A: Run Using Two Terminal Windows

#### Terminal 1 — Start the FastAPI Backend:
```bash
# Activate virtual environment
venv\Scripts\activate

# Start backend server
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```
*The backend will be live at: `http://127.0.0.1:8000` (API docs at `http://127.0.0.1:8000/docs`).*

#### Terminal 2 — Start the Streamlit Frontend:
```bash
# Activate virtual environment
venv\Scripts\activate

# Start frontend application
streamlit run src/ui/app.py
```
*The Streamlit web UI will open automatically in your browser at: `http://localhost:8501`.*

---

### Option B: Single Command (PowerShell)
You can launch both concurrently from PowerShell:
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "venv\Scripts\activate; uvicorn src.api.main:app --port 8000 --reload" ; venv\Scripts\activate ; streamlit run src/ui/app.py
```

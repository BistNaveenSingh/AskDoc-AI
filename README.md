# AntiRag — AI-Powered Document Question Answering System

A Retrieval-Augmented Generation (RAG) application that lets users upload PDF documents (policies, manuals, reports) and ask natural-language questions about them. The system retrieves relevant passages, generates answers grounded only in document content with source citations, and explicitly says "I don't know" when the answer isn't in the documents. 

## Features
- **Upload PDFs**: Extract text from documents.
- **RAG Q&A**: Ask natural language questions about the uploaded documents.
- **Source Citations**: Answers are grounded in document content and cite the source filename and page number.
- **FastAPI Backend**: REST endpoints for document ingestion and Q&A.
- **Streamlit UI**: A clean, interactive web interface.

## Tech Stack
- **Python 3.11+**
- **LangChain** for RAG orchestration.
- **OpenAI API** (`GPT-4o-mini` for generation, `text-embedding-3-small` for embeddings).
- **FAISS** for local, in-memory/on-disk vector search.
- **PyMuPDF** for text extraction.
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
   Copy the example environment file and fill in your OpenAI API key.
   ```bash
   cp .env.example .env
   ```

## Running the Application
*Details on running the FastAPI backend and Streamlit UI will be added here in upcoming phases.*

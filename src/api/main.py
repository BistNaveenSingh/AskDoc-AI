import os
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables (e.g. OPENAI_API_KEY)
load_dotenv()

from src.ingestion.document_processor import process_pdf
from src.embeddings.vector_store import add_documents_to_store, get_retriever
from src.retrieval.qa_chain import answer_question

app = FastAPI(title="AntiRag API", description="AI-Powered Document Question Answering System", version="1.0.0")

# Setup data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

class QuestionRequest(BaseModel):
    question: str

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Uploads a PDF document, extracts text, chunks it, and adds it to the vector store.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    file_path = os.path.join(DATA_DIR, file.filename)
    
    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process the PDF
        chunks = process_pdf(file_path)
        
        # Add to vector store
        add_documents_to_store(chunks)
        
        return {"message": f"Successfully processed {file.filename} and added {len(chunks)} chunks to the vector store."}
    except Exception as e:
        # Clean up file on failure if needed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

class ProcessRequest(BaseModel):
    filename: str

@app.post("/documents/process")
async def process_document(request: ProcessRequest):
    """
    Processes an already-uploaded PDF file in the data directory.
    Extracts text, chunks it, and adds it to the vector store.
    Useful for re-processing or batch processing documents that were uploaded separately.
    """
    file_path = os.path.join(DATA_DIR, request.filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File '{request.filename}' not found in data directory.")
    if not request.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        chunks = process_pdf(file_path)
        add_documents_to_store(chunks)
        return {"message": f"Successfully processed {request.filename} and added {len(chunks)} chunks to the vector store."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """
    Given a question, retrieves relevant context from the vector store and generates an answer.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
    retriever = get_retriever()
    if not retriever:
        raise HTTPException(status_code=404, detail="Vector store is empty. Please upload a document first.")
        
    try:
        result = answer_question(request.question, retriever)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")

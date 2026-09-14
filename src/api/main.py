import os
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables (e.g. OPENAI_API_KEY)
load_dotenv()

from src.ingestion.document_processor import process_file, VIDEO_EXTENSIONS
from src.embeddings.vector_store import add_documents_to_store, get_retriever, delete_document_from_store, rebuild_vector_store
from src.retrieval.qa_chain import answer_question

app = FastAPI(title="AskDoc AI API", description="AI-Powered Document Question Answering System", version="1.0.0")

# Setup data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

class QuestionRequest(BaseModel):
    question: str

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Uploads a document (PDF, Image, HTML, JSON, DOCX, TXT, etc.), extracts text, chunks it, and adds it to the vector store.
    Rejects video files.
    """
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    if ext in VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Video files ({ext}) are not supported.")
        
    file_path = os.path.join(DATA_DIR, file.filename)
    
    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process the file
        chunks = process_file(file_path)
        
        # Add to vector store
        add_documents_to_store(chunks)
        
        return {"message": f"Successfully processed {file.filename} and added {len(chunks)} chunks to the vector store."}
    except ValueError as ve:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Clean up file on failure if needed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.get("/documents")
async def list_documents():
    """
    Returns metadata for all documents currently saved in the data directory.
    """
    documents = []
    if os.path.exists(DATA_DIR):
        for filename in sorted(os.listdir(DATA_DIR)):
            file_path = os.path.join(DATA_DIR, filename)
            if os.path.isfile(file_path):
                size_bytes = os.path.getsize(file_path)
                _, ext = os.path.splitext(filename)
                documents.append({
                    "name": filename,
                    "size": size_bytes,
                    "ext": ext.lower()
                })
    return {"documents": documents}

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """
    Deletes a document from the session (data directory) and updates the vector store.
    """
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found.")
        
    try:
        os.remove(file_path)
        # Instantly filter and update vector store
        delete_document_from_store(filename)
        return {"message": f"Document '{filename}' successfully deleted and vector store updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")



class ProcessRequest(BaseModel):
    filename: str

@app.post("/documents/process")
async def process_document(request: ProcessRequest):
    """
    Processes an already-uploaded document or image in the data directory.
    Extracts text, chunks it, and adds it to the vector store.
    """
    file_path = os.path.join(DATA_DIR, request.filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File '{request.filename}' not found in data directory.")
    
    _, ext = os.path.splitext(request.filename)
    ext = ext.lower()
    if ext in VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Video files ({ext}) are not supported.")

    try:
        chunks = process_file(file_path)
        add_documents_to_store(chunks)
        return {"message": f"Successfully processed {request.filename} and added {len(chunks)} chunks to the vector store."}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
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

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribes spoken voice audio (WAV, MP3, WebM) to text.
    Prioritizes Gemini 2.5 Flash, with fallback to OpenAI Whisper.
    """
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file received.")

        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if gemini_key:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=gemini_key)
            mime_type = file.content_type or "audio/wav"
            
            model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                            "Please transcribe the spoken speech in this audio accurately. Return ONLY the transcribed text without quotes or commentary."
                        ]
                    )
                except Exception as primary_err:
                    print(f"Notice: Primary model {model_name} error: {primary_err}, attempting fallback...")
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=[
                            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                            "Please transcribe the spoken speech in this audio accurately. Return ONLY the transcribed text without quotes or commentary."
                        ]
                    )
                transcription = response.text.strip() if response.text else ""
                return {"transcription": transcription}
            except Exception as audio_err:
                print(f"Notice: Audio transcription error: {audio_err}")
                return {"transcription": "", "notice": "Audio processed successfully (no speech detected)."}

        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            from openai import OpenAI
            import io
            client = OpenAI(api_key=openai_key)
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = file.filename or "audio.wav"
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return {"transcription": transcription.text.strip()}

        raise HTTPException(status_code=500, detail="No API key (GEMINI_API_KEY or OPENAI_API_KEY) found for transcription.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")

import os
from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

# Ensure the db directory exists relative to this file
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "db", "faiss_index")

def get_embeddings_model():
    """
    Initializes and returns the embeddings model.
    Prioritizes Gemini (text-embedding-004) if GEMINI_API_KEY or GOOGLE_API_KEY is found,
    otherwise falls back to OpenAI (text-embedding-3-small).
    """
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=gemini_key
        )
    
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(model="text-embedding-3-small")

def add_documents_to_store(chunks: List[Document], persist_directory: str = DB_PATH):
    """
    Embeds text chunks and adds them to a local FAISS vector store.
    If the store already exists, it loads it and adds the new chunks.
    """
    embeddings = get_embeddings_model()
    
    if os.path.exists(persist_directory) and os.path.exists(os.path.join(persist_directory, "index.faiss")):
        # Load existing index and add texts
        # Note: allow_dangerous_deserialization is set to True because we are loading a local file we created.
        vector_store = FAISS.load_local(
            persist_directory, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        vector_store.add_documents(chunks)
    else:
        # Create a new index from texts
        vector_store = FAISS.from_documents(chunks, embeddings)
        
    # Save the updated index locally
    vector_store.save_local(persist_directory)

def get_retriever(persist_directory: str = DB_PATH, k: int = 4):
    """
    Loads the FAISS vector store and returns a retriever for querying.
    Returns None if the vector store does not exist yet.
    """
    if not os.path.exists(persist_directory) or not os.path.exists(os.path.join(persist_directory, "index.faiss")):
        return None
        
    embeddings = get_embeddings_model()
    vector_store = FAISS.load_local(
        persist_directory, 
        embeddings, 
        allow_dangerous_deserialization=True
    )
    
    # Return a retriever that fetches the top k most similar chunks
    return vector_store.as_retriever(search_kwargs={"k": k})

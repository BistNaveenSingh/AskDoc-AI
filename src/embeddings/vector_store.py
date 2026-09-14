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
            model="models/gemini-embedding-2",
            task_type="retrieval_document",
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

def sync_vector_store_with_disk(data_dir: str = None, persist_directory: str = DB_PATH) -> int:
    """
    Ensures the FAISS vector store is strictly synchronized with the files currently
    present in data_dir. Any chunks belonging to deleted or non-existent files are removed.
    """
    if data_dir is None:
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
        
    if not os.path.exists(persist_directory) or not os.path.exists(os.path.join(persist_directory, "index.faiss")):
        return 0
        
    active_files = set(os.listdir(data_dir)) if os.path.exists(data_dir) else set()
    embeddings = get_embeddings_model()
    
    try:
        vector_store = FAISS.load_local(
            persist_directory,
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        # Check if there are any orphaned chunks
        orphaned = False
        valid_docs = []
        for doc in vector_store.docstore._dict.values():
            src = doc.metadata.get("source", "")
            base = os.path.basename(src)
            if base in active_files:
                valid_docs.append(doc)
            else:
                orphaned = True
                
        if orphaned:
            import shutil
            if valid_docs:
                new_store = FAISS.from_documents(valid_docs, embeddings)
                new_store.save_local(persist_directory)
                return len(valid_docs)
            else:
                if os.path.exists(persist_directory):
                    shutil.rmtree(persist_directory)
                return 0
                
        return len(vector_store.docstore._dict)
    except Exception as e:
        print(f"Sync vector store warning: {e}")
        return 0

def get_retriever(persist_directory: str = DB_PATH, k: int = 8):
    """
    Loads the FAISS vector store and returns a retriever for querying.
    Ensures that stale/orphaned document vectors are purged before returning.
    Returns None if the vector store does not exist or has no active documents.
    """
    # Self-heal and purge any orphaned documents first
    sync_vector_store_with_disk(persist_directory=persist_directory)
    
    if not os.path.exists(persist_directory) or not os.path.exists(os.path.join(persist_directory, "index.faiss")):
        return None
        
    embeddings = get_embeddings_model()
    vector_store = FAISS.load_local(
        persist_directory, 
        embeddings, 
        allow_dangerous_deserialization=True
    )
    
    if not vector_store.docstore._dict:
        return None
        
    # Return a retriever that fetches the top k most similar chunks
    return vector_store.as_retriever(search_kwargs={"k": k})

def delete_document_from_store(filename: str, persist_directory: str = DB_PATH) -> int:
    """
    Deletes all chunks belonging to `filename` from the FAISS vector store
    instantly by filtering existing docstore chunks without re-processing other files.
    """
    if not os.path.exists(persist_directory) or not os.path.exists(os.path.join(persist_directory, "index.faiss")):
        return 0
        
    embeddings = get_embeddings_model()
    try:
        vector_store = FAISS.load_local(
            persist_directory,
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        target_name = os.path.basename(filename).lower()
        # Filter docstore to keep documents that do NOT match the deleted file
        remaining_docs = [
            doc for doc in vector_store.docstore._dict.values()
            if os.path.basename(doc.metadata.get("source", "")).lower() != target_name
        ]
        
        if remaining_docs:
            new_store = FAISS.from_documents(remaining_docs, embeddings)
            new_store.save_local(persist_directory)
            return len(remaining_docs)
        else:
            import shutil
            if os.path.exists(persist_directory):
                shutil.rmtree(persist_directory)
            return 0
    except Exception as e:
        print(f"Error filtering vector store for {filename}: {e}")
        return 0

def rebuild_vector_store(data_dir: str = None, persist_directory: str = DB_PATH):
    """
    Rebuilds the FAISS vector store from all valid files remaining in data_dir.
    If no documents remain, clears the vector store files.
    """
    import shutil
    from src.ingestion.document_processor import process_file
    
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        
    all_chunks = []
    if os.path.exists(data_dir):
        for fname in sorted(os.listdir(data_dir)):
            fpath = os.path.join(data_dir, fname)
            if os.path.isfile(fpath):
                try:
                    chunks = process_file(fpath)
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"Warning: could not process {fname} during rebuild: {e}")
                    
    if all_chunks:
        embeddings = get_embeddings_model()
        vector_store = FAISS.from_documents(all_chunks, embeddings)
        os.makedirs(persist_directory, exist_ok=True)
        vector_store.save_local(persist_directory)
        return len(all_chunks)
    else:
        if os.path.exists(persist_directory):
            try:
                shutil.rmtree(persist_directory)
            except Exception as e:
                print(f"Warning: could not delete persist directory {persist_directory}: {e}")
        return 0



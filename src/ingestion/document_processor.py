import os
import re
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def clean_text(text: str) -> str:
    """
    Cleans extracted text by replacing multiple spaces and newlines with a single space,
    and stripping leading/trailing whitespace.
    """
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def process_pdf(file_path: str, chunk_size: int = 800, chunk_overlap: int = 100) -> List[Document]:
    """
    Extracts text from a PDF, cleans it, and splits it into overlapping chunks.
    
    Args:
        file_path: The path to the PDF file.
        chunk_size: Maximum token/character size per chunk.
        chunk_overlap: Number of overlapping characters between chunks.
        
    Returns:
        A list of Document objects with cleaned text and metadata (source, page).
    """
    # 1. Load the PDF
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    
    # 2. Clean the text within each document
    for doc in documents:
        doc.page_content = clean_text(doc.page_content)
        
    # 3. Initialize the text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
        length_function=len,
    )
    
    # 4. Split the documents into chunks
    chunks = text_splitter.split_documents(documents)
    
    # Notice: PyPDFLoader already populates 'source' and 'page' metadata.
    return chunks

if __name__ == "__main__":
    # Simple test if run directly
    sample_pdf = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample.pdf")
    if os.path.exists(sample_pdf):
        chunks = process_pdf(sample_pdf)
        print(f"Processed {len(chunks)} chunks.")
        if chunks:
            print("First chunk preview:")
            print(chunks[0].page_content)
            print(chunks[0].metadata)
    else:
        print(f"No sample PDF found at {sample_pdf} for testing.")

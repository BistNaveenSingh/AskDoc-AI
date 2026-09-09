from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

def format_docs(docs: List[Document]) -> str:
    """
    Formats the retrieved documents into a string for the prompt context.
    It appends source metadata to each chunk so the LLM knows where it came from.
    """
    formatted_docs = []
    for i, doc in enumerate(docs):
        # Extract metadata
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "Unknown")
        
        # Format chunk
        chunk_text = f"--- Document {i+1} ---\nSource: {source} (Page {page})\nContent: {doc.page_content}\n"
        formatted_docs.append(chunk_text)
        
    return "\n".join(formatted_docs)

def get_qa_chain(retriever):
    """
    Creates and returns a conversational retrieval chain using LangChain Expression Language (LCEL).
    The prompt enforces that the LLM only answers using context and includes citations.
    """
    # 1. Initialize the LLM
    # Requires OPENAI_API_KEY to be set in environment variables
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # 2. Define the system prompt with strict guardrails
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the question. "
        "If the answer is not contained in the provided context, you MUST explicitly state exactly: 'I don't know.' Do not try to invent an answer or use outside knowledge.\n"
        "If you do find the answer, append the source filename and page numbers you used to formulate your answer at the very end.\n\n"
        "Context:\n{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}"),
    ])
    
    # 3. Build the LCEL chain
    # We pass the question directly, use the retriever to get docs, format them, and pipe to the prompt, llm, and output parser.
    qa_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return qa_chain

def answer_question(query: str, retriever) -> Dict[str, Any]:
    """
    Given a question and a retriever, gets the answer from the LLM and the source documents used.
    """
    # We retrieve the docs separately to return them alongside the answer
    docs = retriever.invoke(query)
    
    qa_chain = get_qa_chain(retriever)
    answer = qa_chain.invoke(query)
    
    # Extract unique sources for the frontend to display
    sources = []
    for doc in docs:
        src_info = {"source": doc.metadata.get("source", "Unknown"), "page": doc.metadata.get("page", "Unknown")}
        if src_info not in sources:
            sources.append(src_info)
            
    return {
        "question": query,
        "answer": answer,
        "sources": sources
    }

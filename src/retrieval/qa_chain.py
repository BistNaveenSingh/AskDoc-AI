from typing import List, Dict, Any
import os
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

def format_docs(docs: List[Document]) -> str:
    """
    Formats the retrieved documents into a string for the prompt context.
    Appends only the clean file name and page number to avoid exposing full disk paths.
    """
    formatted_docs = []
    for i, doc in enumerate(docs):
        # Extract metadata and get only the filename
        raw_source = doc.metadata.get("source", "Unknown")
        source_name = os.path.basename(raw_source) if raw_source != "Unknown" else "Unknown"
        raw_page = doc.metadata.get("page", 0)
        page = raw_page + 1 if isinstance(raw_page, int) else raw_page
        
        # Format chunk
        chunk_text = f"--- Document {i+1} ---\nSource: {source_name} (Page {page})\nContent: {doc.page_content}\n"
        formatted_docs.append(chunk_text)
        
    return "\n".join(formatted_docs)

def get_qa_chain(retriever):
    """
    Creates and returns a conversational retrieval chain using LangChain Expression Language (LCEL).
    The prompt enforces that the LLM only answers using context and stays concise.
    """
    # 1. Initialize the LLM (Gemini prioritized, fallback to OpenAI)
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        primary_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        primary_llm = ChatGoogleGenerativeAI(
            model=primary_model,
            google_api_key=gemini_key,
            temperature=0
        )
        fallback_llm1 = ChatGoogleGenerativeAI(
            model="gemini-3.1-flash-lite",
            google_api_key=gemini_key,
            temperature=0
        )
        fallback_llm2 = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            google_api_key=gemini_key,
            temperature=0
        )
        llm = primary_llm.with_fallbacks([fallback_llm1, fallback_llm2])
    else:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # 2. Define the system prompt with strict guardrails
    system_prompt = (
        "You are a helpful assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the question directly, concisely, and accurately.\n"
        "RULES:\n"
        "1. If the answer is not contained in the provided context, you MUST explicitly state exactly: 'I don't know.' Do not invent answers or use outside knowledge.\n"
        "2. Answer the question directly without repeating full filesystem paths or citation blocks; citations are displayed separately.\n\n"
        "Context:\n{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}"),
    ])
    
    # 3. Build the LCEL chain
    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain

import time
import re
from typing import Dict, Any

def answer_question(query: str, retriever) -> Dict[str, Any]:
    """
    Given a user query and a retriever, retrieves relevant document chunks,
    generates an answer with citations using the QA chain, and ensures robust retries.
    """
    try:
        docs = retriever.invoke(query)
    except Exception as ret_err:
        docs = []
        print(f"Retrieval warning: {ret_err}")
        
    qa_chain = get_qa_chain(retriever)
    
    answer = ""
    for attempt in range(5):
        try:
            answer = qa_chain.invoke(query)
            break
        except Exception as e:
            err_str = str(e).lower()
            if "quota" in err_str or "rate" in err_str or "429" in err_str or "resourceexhausted" in err_str:
                if attempt < 4:
                    wait_time = 4 * (attempt + 1)
                    # Check if error specified a retryDelay
                    delay_match = re.search(r'retry.*?(\d+)', err_str)
                    if delay_match:
                        try:
                            wait_time = max(wait_time, int(delay_match.group(1)) + 1)
                        except ValueError:
                            pass
                    time.sleep(wait_time)
                    continue
                answer = "API quota exceeded. Please wait a moment before asking another question."
            elif "safety" in err_str or "block" in err_str:
                answer = "I could not generate an answer because the content was filtered by safety policies."
                break
            elif "empty" in err_str or not docs:
                answer = "I don't know. (No relevant document context found in the knowledge base.)"
                break
            else:
                answer = f"I encountered an error analyzing the documents: {str(e)}"
                break
    
    # Extract clean, unique sources (basename and 1-indexed page)
    sources = []
    for doc in docs:
        raw_source = doc.metadata.get("source", "Unknown")
        clean_name = os.path.basename(raw_source) if raw_source != "Unknown" else "Unknown"
        raw_page = doc.metadata.get("page", 0)
        page_num = raw_page + 1 if isinstance(raw_page, int) else raw_page
        
        src_info = {"source": clean_name, "page": page_num}
        if src_info not in sources:
            sources.append(src_info)
            
    return {
        "question": query,
        "answer": answer,
        "sources": sources
    }

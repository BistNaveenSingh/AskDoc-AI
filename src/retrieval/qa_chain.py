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

def get_llm():
    """Initializes and returns the primary LLM with fallbacks."""
    gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if gemini_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        primary_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        primary_llm = ChatGoogleGenerativeAI(
            model=primary_model,
            google_api_key=gemini_key,
            temperature=0
        )
        fallback_llm1 = ChatGoogleGenerativeAI(
            model="gemini-3.8-flash",
            google_api_key=gemini_key,
            temperature=0
        )
        fallback_llm2 = ChatGoogleGenerativeAI(
            model="gemini-3.8-flash",
            google_api_key=gemini_key,
            temperature=0
        )
        return primary_llm.with_fallbacks([fallback_llm1, fallback_llm2])
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)

def get_generation_chain():
    """Builds the core prompt + LLM + output parser chain."""
    system_prompt = (
        "You are AskDoc AI, an expert, insightful, and highly articulate AI document assistant.\n"
        "Use the provided context pieces retrieved from the user's documents to answer questions with thoroughness, structure, and accuracy.\n\n"
        "CORE GUIDELINES:\n"
        "1. STRICT GROUNDING: Ground all factual statements strictly in the provided document context. If an answer cannot be found or deduced from the provided documents, you MUST explicitly state: 'I don't know.' Never hallucinate fake facts, figures, dates, or specifications.\n"
        "2. CONVERSATION MEMORY: The user's message may include [CONVERSATION HISTORY] from prior exchanges. Use this history to understand follow-up questions, resolve pronouns (e.g. 'it', 'that', 'the same'), and maintain conversational continuity. Always answer the [Current question] — the history is for context only.\n"
        "3. COMPREHENSIVE & ADAPTIVE STRUCTURE: When asked to analyze, review, summarize, evaluate, or give an overview of a document:\n"
        "   - Adapt the section breakdown to the document domain:\n"
        "     * Resumes & Portfolios: Profile & Stack, Education, Projects & Key Metrics, Technical Skills, Achievements, Strengths, and Strategic Positioning/Improvement Advice.\n"
        "     * Business, Finance & Reports: Executive Summary, Key Findings, Metrics & Performance Data, Risks or Discrepancies, and Actionable Recommendations.\n"
        "     * Policies, Manuals & Contracts: Scope & Purpose, Core Rules & Responsibilities, Step-by-Step Procedures, Exceptions, and Compliance Notes.\n"
        "     * Technical & Research Papers: Objective, Methodology, Key Architecture/Components, Results & Benchmarks, and Practical Takeaways.\n"
        "   - Provide expert-level depth: articulate multi-section breakdown, clear markdown headers (###), bullet points (*), and bold key terms.\n"
        "4. DIRECT & PRECISE FOR FACTUAL QUERIES: If the user asks a specific factual question (e.g. 'What is the CGPA?', 'What is the return policy window?', 'What database was used?'), answer directly, concisely, and accurately.\n"
        "5. CLEAN PRESENTATION: Do not output raw filesystem paths or citation blocks in the answer body; citations are handled automatically.\n"
        "6. STRICT VERTICAL LAYOUT (NO WIDE TABLES): Always format your response in clean, vertical sections flowing top-to-bottom down the page using markdown headers (###), bullet points (*), and paragraphs. NEVER put sections, project summaries, or paragraphs into multi-column tables or horizontal grids. Tables must only be used for small 2-column key-value lists.\n"
        "7. RESPONSE FORMATTING: Use clean markdown. Add a blank line between sections. Use ### for headers, * for bullet points, and **bold** for key terms. Keep responses well-organized and easy to scan.\n\n"
        "Context:\n{context}"
    )

    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}"),
    ])
    
    return prompt | get_llm() | StrOutputParser()

def get_qa_chain(retriever):
    """
    Creates and returns a conversational retrieval chain using LangChain Expression Language (LCEL).
    Maintained for backward compatibility.
    """
    gen_chain = get_generation_chain()
    return (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough()
        }
        | gen_chain
    )

import time
import re

def is_greeting_or_chitchat(text: str) -> bool:
    """Detects simple greetings, thank yous, and introductory phrases that should not trigger document retrieval."""
    clean = text.strip().lower()
    clean_no_punct = re.sub(r"[^\w\s]", "", clean).strip()
    
    simple_greetings = {
        "hi", "hello", "hey", "hiya", "howdy", "sup", "yo", "hola",
        "greetings", "good morning", "good afternoon", "good evening",
        "good day", "who are you", "what can you do", "what is this",
        "what is askdoc", "what is askdoc ai", "what is antirag", "help", "thanks", "thank you", "thanks a lot",
        "thank you so much", "ok", "okay"
    }
    if clean_no_punct in simple_greetings:
        return True
        
    if re.match(r"^(hi|hello|hey|howdy|hiya)\s*(there|assistant|bot|askdoc|askdoc ai|antirag)?$", clean_no_punct):
        return True
        
    return False

def is_unknown_response(ans: str) -> bool:
    """Checks if the LLM output explicitly states that the answer is not known or not in documents."""
    clean = ans.strip().lower()
    indicators = [
        "i don't know",
        "i do not know",
        "not contained in the provided",
        "not mentioned in the provided",
        "not found in the provided",
        "not available in the provided",
        "provided context does not contain",
        "provided documents do not contain",
        "no relevant document context",
        "cannot answer",
        "no information provided"
    ]
    return any(ind in clean for ind in indicators)

def answer_question(query: str, retriever) -> Dict[str, Any]:
    """
    Given a user query and a retriever, retrieves relevant document chunks,
    generates an answer with citations using the QA chain, and ensures robust retries.
    Guarantees:
    - Greetings never cite documents.
    - Chunks from deleted files are never cited.
    - 'I don't know' responses never cite documents.
    """
    # 1. Fast path for greetings / chitchat: zero retrieval, zero false citations
    if is_greeting_or_chitchat(query):
        return {
            "question": query,
            "answer": "Hello! I am AskDoc AI, your AI document assistant. Ask me questions about your uploaded documents, and I will provide answers grounded strictly in your content with exact source citations.",
            "sources": []
        }

    # 2. Check active files on disk
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    active_files = set(os.listdir(data_dir)) if os.path.exists(data_dir) else set()
    if not active_files:
        return {
            "question": query,
            "answer": "No documents are currently active. Please upload a document first to ask questions.",
            "sources": []
        }

    # 3. Retrieve relevant chunks
    try:
        raw_docs = retriever.invoke(query)
    except Exception as ret_err:
        raw_docs = []
        print(f"Retrieval warning: {ret_err}")

    # 4. Strict filter: only chunks from files physically present in data/ are permitted
    docs = [
        d for d in raw_docs
        if os.path.basename(d.metadata.get("source", "")) in active_files
    ]

    if not docs:
        return {
            "question": query,
            "answer": "I don't know. (No relevant document context found in the active documents.)",
            "sources": []
        }

    # 5. Generate answer using grounded generation chain
    gen_chain = get_generation_chain()
    context_str = format_docs(docs)
    
    answer = ""
    for attempt in range(5):
        try:
            answer = gen_chain.invoke({"context": context_str, "question": query})
            break
        except Exception as e:
            err_str = str(e).lower()
            if "quota" in err_str or "rate" in err_str or "429" in err_str or "resourceexhausted" in err_str:
                if attempt < 4:
                    wait_time = 4 * (attempt + 1)
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
            else:
                answer = f"I encountered an error analyzing the documents: {str(e)}"
                break

    # 6. Extract clean sources ONLY if the answer is grounded in content (not 'I don't know')
    sources = []
    if answer and not is_unknown_response(answer):
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

import os
import re
import json
import mimetypes
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm", ".m4v", ".3gp", ".mpeg", ".mpg"
}

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif"
}

def clean_text(text: str) -> str:
    """
    Cleans extracted text by stripping trailing whitespace from lines,
    normalizing multiple spaces on each line, and collapsing excessive empty lines,
    while preserving table rows, code blocks, and multi-year data structure.
    """
    if not text:
        return ""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]
    return '\n'.join(lines).strip()

def transcribe_image_bytes(image_bytes: bytes, mime_type: str = "image/png", context_label: str = "") -> str:
    """
    Transcribes all text, tables, charts, diagrams, and handwriting from image bytes using Gemini.
    """
    gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not gemini_key:
        return ""
        
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=gemini_key)
        prompt = (
            f"Carefully examine this image {context_label}. "
            "Extract, transcribe, and describe all textual content, tables, charts, figures, numbers, and handwriting. "
            "Return clean, comprehensive, verbatim text without commentary."
        )
        
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt
                ]
            )
            return response.text.strip() if response.text else ""
        except Exception as primary_err:
            # Fallback to flash-lite if rate limit or quota encountered
            print(f"Notice: Primary model {model_name} error: {primary_err}, attempting fallback...")
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt
                ]
            )
            return response.text.strip() if response.text else ""
    except Exception as e:
        print(f"Notice: Vision extraction error for {context_label}: {e}")
        return ""

def process_pdf(file_path: str, chunk_size: int = 800, chunk_overlap: int = 100) -> List[Document]:
    """
    Extracts text AND embedded images from every PDF page.
    If a page is a scanned document (little or no digital text), renders the page to image and runs OCR.
    """
    all_page_docs = []
    
    try:
        import pymupdf
        doc = pymupdf.open(file_path)
        
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_num = page_idx + 1
            page_text = page.get_text().strip()
            page_visual_content = []
            
            # 1. Scanned page detection: If page has minimal digital text, render and OCR the whole page
            if len(page_text) < 60:
                try:
                    pix = page.get_pixmap(dpi=150)
                    rendered_bytes = pix.tobytes("png")
                    scanned_ocr = transcribe_image_bytes(rendered_bytes, "image/png", f"scanned PDF page {page_num}")
                    if scanned_ocr:
                        page_visual_content.append(f"[Scanned Page Content]:\n{scanned_ocr}")
                except Exception as pix_err:
                    print(f"Pixmap rendering error on page {page_num}: {pix_err}")
            else:
                # 2. Extract embedded images on the page (diagrams, photos, charts)
                try:
                    image_list = page.get_images(full=True)
                    for img_idx, img_info in enumerate(image_list[:4]):  # Top 4 prominent images per page
                        xref = img_info[0]
                        base_image = doc.extract_image(xref)
                        width = base_image.get("width", 0)
                        height = base_image.get("height", 0)
                        img_bytes = base_image.get("image", b"")
                        
                        # Filter out small decorative tracking pixels
                        if width >= 40 and height >= 40 and len(img_bytes) > 500:
                            ext = base_image.get("ext", "png")
                            mime = "image/jpeg" if ext.lower() in ["jpg", "jpeg"] else f"image/{ext}"
                            img_desc = transcribe_image_bytes(img_bytes, mime, f"embedded image {img_idx+1} on page {page_num}")
                            if img_desc:
                                page_visual_content.append(f"[Embedded Image/Diagram {img_idx+1}]:\n{img_desc}")
                except Exception as img_err:
                    print(f"Embedded image extraction error on page {page_num}: {img_err}")
                    
            # Combine digital text and image extractions for this page
            combined_parts = []
            if page_text:
                combined_parts.append(clean_text(page_text))
            if page_visual_content:
                combined_parts.extend(page_visual_content)
                
            full_page_str = "\n\n".join(combined_parts)
            if full_page_str:
                all_page_docs.append(Document(
                    page_content=full_page_str,
                    metadata={"source": file_path, "page": page_num}
                ))
        doc.close()
    except Exception as e:
        print(f"PyMuPDF failed, falling back to PyPDFLoader: {e}")
        loader = PyPDFLoader(file_path)
        all_page_docs = loader.load()
        for doc in all_page_docs:
            doc.page_content = clean_text(doc.page_content)
            
    # Split documents into chunks while preserving page metadata
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
        length_function=len,
    )
    return text_splitter.split_documents(all_page_docs)

def process_image(file_path: str) -> str:
    """
    Extracts and transcribes all text, tables, diagrams, and visual data from a standalone image.
    """
    with open(file_path, "rb") as f:
        image_bytes = f.read()
        
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type or not mime_type.startswith("image/"):
        ext = os.path.splitext(file_path)[1].lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
        }
        mime_type = mime_map.get(ext, "image/jpeg")
        
    return transcribe_image_bytes(image_bytes, mime_type, f"from file {os.path.basename(file_path)}")

def process_html(file_path: str) -> str:
    """
    Extracts text content from an HTML file, removing scripts, styles, and markup.
    """
    from bs4 import BeautifulSoup
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.extract()
    return soup.get_text(separator="\n")

def process_json(file_path: str) -> str:
    """
    Parses and formats a JSON file into structured text.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)
    return json.dumps(data, indent=2)

def process_docx(file_path: str) -> str:
    """
    Extracts paragraphs, tables, AND embedded images from a Word (.docx) document.
    """
    import docx
    doc = docx.Document(file_path)
    lines = []
    
    # 1. Text from paragraphs
    for para in doc.paragraphs:
        if para.text.strip():
            lines.append(para.text.strip())
            
    # 2. Text from tables
    for table in doc.tables:
        for row in table.rows:
            row_vals = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_vals:
                lines.append(" | ".join(row_vals))
                
    # 3. Embedded images inside the DOCX
    img_count = 0
    try:
        for rel_id, rel in doc.part.related_parts.items():
            if "image" in rel.content_type:
                img_count += 1
                if img_count > 6:  # limit to top 6 embedded images
                    break
                img_bytes = rel.blob
                if len(img_bytes) > 500:
                    img_desc = transcribe_image_bytes(img_bytes, rel.content_type, f"embedded image {img_count} in Word doc")
                    if img_desc:
                        lines.append(f"\n[Embedded Image {img_count}]:\n{img_desc}\n")
    except Exception as docx_img_err:
        print(f"Notice: DOCX embedded image extraction: {docx_img_err}")
        
    return "\n".join(lines)

def process_text_file(file_path: str) -> str:
    """
    Reads plain text or source code files with UTF-8 / fallback encoding.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1", errors="ignore") as f:
            return f.read()

def process_file(file_path: str, chunk_size: int = 800, chunk_overlap: int = 100) -> List[Document]:
    """
    Universal document and media ingestion function.
    Supports PDF (text + embedded images/OCR), Images, HTML, JSON, DOCX (text + embedded images),
    Markdown, CSV, and Text files. Explicitly rejects video files.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    # Reject video files
    if ext in VIDEO_EXTENSIONS:
        raise ValueError(f"Video files ({ext}) are not supported.")

    # PDF handler (with embedded image OCR)
    if ext == ".pdf":
        return process_pdf(file_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # Dispatch to appropriate extractor
    if ext in IMAGE_EXTENSIONS:
        raw_text = process_image(file_path)
    elif ext in {".html", ".htm"}:
        raw_text = process_html(file_path)
    elif ext == ".json":
        raw_text = process_json(file_path)
    elif ext == ".docx":
        raw_text = process_docx(file_path)
    else:
        raw_text = process_text_file(file_path)

    raw_text = clean_text(raw_text)
    if not raw_text:
        raise ValueError(f"No extractable text or visual content found in {os.path.basename(file_path)}.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
        length_function=len,
    )
    
    split_texts = text_splitter.split_text(raw_text)
    return [
        Document(page_content=chunk, metadata={"source": file_path, "page": 1})
        for chunk in split_texts
    ]



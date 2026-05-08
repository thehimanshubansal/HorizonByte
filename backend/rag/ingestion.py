import fitz  # PyMuPDF
import re

def clean_text(text: str) -> str:
    # Remove null bytes and multiple whitespaces
    text = text.replace('\x00', '')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def load_document(file_path: str) -> str:
    """Loads a PDF or TXT file and returns its raw text."""
    if file_path.lower().endswith('.pdf'):
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text() + " "
        return clean_text(text)
    elif file_path.lower().endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return clean_text(f.read())
    else:
        raise ValueError("Unsupported file format. Please upload PDF or TXT.")

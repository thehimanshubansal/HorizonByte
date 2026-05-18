import fitz  # PyMuPDF
import re

def clean_text(text: str) -> str:
    # Remove null bytes and multiple whitespaces
    text = text.replace('\x00', '')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def scrub_pii(text: str) -> str:
    """Redacts emails and phone numbers using Regex."""
    # Redact Emails
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_REDACTED]', text)
    # Redact Phone Numbers (Basic pattern for 10-15 digits)
    text = re.sub(r'\+?\d{10,15}', '[PHONE_REDACTED]', text)
    return text

def load_document(file_path: str) -> str:
    """Loads a PDF or TXT file and returns its raw text."""
    if file_path.lower().endswith('.pdf'):
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            page_text = page.get_text()
            # Extract tables as markdown
            tables = page.find_tables()
            if tables:
                for table in tables:
                    page_text += "\n" + table.to_markdown() + "\n"
            text += page_text + " "
        return scrub_pii(clean_text(text)) 
    elif file_path.lower().endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return scrub_pii(clean_text(f.read()))
    else:
        raise ValueError("Unsupported file format. Please upload PDF or TXT.")

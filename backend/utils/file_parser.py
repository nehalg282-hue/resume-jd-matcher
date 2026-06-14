"""
file_parser.py
Extracts plain text from uploaded resume files (PDF, DOCX, TXT).
"""
import io


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Return all text from a PDF file as a single string."""
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        return ''.join(page.extract_text() or '' for page in reader.pages)
    except Exception:
        return ''


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Return all paragraph text from a DOCX file joined by newlines."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return '\n'.join(p.text for p in doc.paragraphs)
    except Exception:
        return ''

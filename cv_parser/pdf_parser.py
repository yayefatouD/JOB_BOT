"""
pdf_parser.py - Groupe 4 : Extraction du texte d'un CV PDF
"""
import io
import PyPDF2


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extrait le texte brut d'un fichier PDF fourni en bytes.
    Returns: texte extrait (string)
    """
    text = ""
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()

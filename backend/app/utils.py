import re
from io import BytesIO
from pypdf import PdfReader

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text.strip()

def strip_pii(text: str) -> str:
    """Strips PII (email and phone numbers) from resume text[cite: 1]."""
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_EMAIL]', text)
    text = re.sub(r'\+?\d[\d\-\s]{8,}\d', '[REDACTED_PHONE]', text)
    return text

def compute_resume_score(skills: list[str], text: str, target_keywords: list[str]):
    """Calculates keyword/skills match fit score using deterministic rule engine[cite: 1, 3]."""
    text_lower = text.lower()
    found = [kw for kw in target_keywords if kw.lower() in text_lower or any(kw.lower() in s.lower() for s in skills)]
    missing = [kw for kw in target_keywords if kw not in found]
    
    score = int((len(found) / len(target_keywords)) * 100) if target_keywords else 70
    return min(100, max(0, score)), found, missing

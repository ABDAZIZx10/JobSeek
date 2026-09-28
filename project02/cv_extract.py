from io import BytesIO


def extract_cv_text(uploaded_file) -> str:
    """Extract plain text from an uploaded CV (txt, pdf, or docx)."""
    name = (uploaded_file.name or "").lower()
    data = uploaded_file.read()

    if name.endswith(".txt"):
        text = data.decode("utf-8", errors="replace")
    elif name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(data))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    elif name.endswith(".docx"):
        from docx import Document

        doc = Document(BytesIO(data))
        text = "\n".join(p.text for p in doc.paragraphs)
    else:
        raise ValueError("Unsupported file type. Use PDF, DOCX, or TXT.")

    text = text.strip()
    if not text:
        raise ValueError(
            "No text found in this file. Use a text-based PDF/DOCX (not a scanned image)."
        )
    return text

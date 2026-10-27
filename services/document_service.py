"""Safe, local PDF text extraction for document-grounded questions."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from config import MAX_DOCUMENT_CHARS, MAX_PDF_BYTES


class DocumentError(ValueError):
    """A user-correctable PDF upload or extraction problem."""


@dataclass(frozen=True)
class ExtractedDocument:
    name: str
    page_count: int
    text: str


def extract_pdf(name: str, data: bytes) -> ExtractedDocument:
    if not name.lower().endswith(".pdf") or not data.startswith(b"%PDF"):
        raise DocumentError("Choose a valid PDF file.")
    if len(data) > MAX_PDF_BYTES:
        raise DocumentError("This PDF is larger than the 10 MB upload limit.")
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(data), strict=False)
        if reader.is_encrypted:
            raise DocumentError("This PDF is encrypted. Upload an unlocked copy.")
        pages = []
        remaining = MAX_DOCUMENT_CHARS
        for index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            excerpt = text[:remaining]
            pages.append(f"[Page {index}]\n{excerpt}")
            remaining -= len(excerpt)
            if remaining <= 0:
                break
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError("Astra could not read this PDF. Try another file or a text-based PDF.") from exc
    if not pages:
        raise DocumentError("No readable text was found. Scanned PDFs need OCR, which this release does not include.")
    return ExtractedDocument(name=name, page_count=len(reader.pages), text="\n\n".join(pages))

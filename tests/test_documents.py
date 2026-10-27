from io import BytesIO

import pytest

from services.document_service import DocumentError, extract_pdf


def make_text_pdf() -> bytes:
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = writer._add_object(DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    }))
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})
    })
    content = DecodedStreamObject()
    content.set_data(b"BT /F1 12 Tf 72 720 Td (Hello from the Astra PDF test) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(content)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_extracts_page_labeled_text():
    document = extract_pdf("notes.pdf", make_text_pdf())
    assert document.name == "notes.pdf"
    assert document.page_count == 1
    assert "[Page 1]" in document.text
    assert "Hello from the Astra PDF test" in document.text


def test_rejects_invalid_upload_and_large_file():
    with pytest.raises(DocumentError, match="valid PDF"):
        extract_pdf("notes.txt", b"not a pdf")
    with pytest.raises(DocumentError, match="10 MB"):
        extract_pdf("large.pdf", b"%PDF" + b"x" * (10 * 1024 * 1024))

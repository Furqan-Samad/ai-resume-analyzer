import io
import pytest
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from backend.services.pdf_parser import extract_pdf_text


def _build_sample_pdf_bytes(text_lines):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    for line in text_lines:
        c.drawString(72, y, line)
        y -= 20
    c.save()
    buffer.seek(0)
    return buffer.read()


def test_extract_pdf_text_returns_clean_lines():
    pdf_bytes = _build_sample_pdf_bytes(
        ["John Doe", "Software Engineer", "Python, FastAPI, Streamlit"]
    )
    result = extract_pdf_text(pdf_bytes)
    assert "John Doe" in result
    assert "Software Engineer" in result
    assert "Python, FastAPI, Streamlit" in result


def test_extract_pdf_text_raises_on_empty_pdf():
    pdf_bytes = _build_sample_pdf_bytes([])
    with pytest.raises(ValueError):
        extract_pdf_text(pdf_bytes)

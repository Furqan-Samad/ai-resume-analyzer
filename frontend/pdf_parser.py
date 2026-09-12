import io
import pdfplumber


def extract_pdf_text(file_bytes: bytes) -> str:
    extracted_lines = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        if len(pdf.pages) == 0:
            raise ValueError("The uploaded PDF has no pages.")

        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                for line in page_text.split("\n"):
                    cleaned_line = line.strip()
                    if cleaned_line:
                        extracted_lines.append(cleaned_line)

    full_text = "\n".join(extracted_lines)

    if not full_text.strip():
        raise ValueError(
            "No extractable text was found in this PDF. "
            "It may be a scanned image or a corrupted file."
        )

    return full_text
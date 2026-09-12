"""
parser.py - Robust, Modular Document Text Parser for Resumes and Portfolios.

This module provides clean extraction of text from PDF and DOCX documents
with primary and fallback engines, comprehensive edge-case handling, and 
advanced text normalization tailored for resumes and portfolios.

Key Capabilities:
1. Primary PDF Engine: `pdfplumber` for precise spatial layout & text extraction.
2. Fallback PDF Engine: `PyPDF2` (or `pypdf`) for recovery when pdfplumber fails or yields empty text.
3. DOCX Support: `python-docx` for extracting both paragraph content and tabular layouts.
4. Text Normalization: `clean_text()` strips non-printable control characters,
   fixes PDF hyphenation & line breaks, converts ligatures, and cleans excess whitespace.
5. Edge Case Protection: Graceful handling of empty files, password-protected documents,
   corrupted files, and unsupported formats without crashing.
6. Streamlit & Web App Ready: Directly handles file paths, raw byte streams, or Streamlit UploadedFile objects.
"""

from __future__ import annotations

import io
import os
import re
import sys
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional, Tuple, Union

# Configure logger
logger = logging.getLogger("document_parser")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Optional / Lazy Imports for Engines
try:
    import pdfplumber
    _HAS_PDFPLUMBER = True
except ImportError:
    pdfplumber = None
    _HAS_PDFPLUMBER = False

try:
    import PyPDF2
    _HAS_PYPDF2 = True
except ImportError:
    try:
        import pypdf as PyPDF2  # Modern alias / successor
        _HAS_PYPDF2 = True
    except ImportError:
        PyPDF2 = None
        _HAS_PYPDF2 = False

try:
    import docx
    _HAS_DOCX = True
except ImportError:
    docx = None
    _HAS_DOCX = False


# ==============================================================================
# Data Structures
# ==============================================================================

@dataclass
class ParseResult:
    """Standardized result object returned by all extraction routines."""
    text: str = ""
    raw_text: str = ""
    success: bool = True
    error: Optional[str] = None
    extraction_method: Optional[str] = None  # e.g., 'pdfplumber', 'PyPDF2', 'docx'
    page_count: int = 0
    file_name: Optional[str] = None
    file_type: Optional[str] = None  # 'pdf' or 'docx'
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the parse result to a standard dictionary."""
        return asdict(self)

    def __bool__(self) -> bool:
        """Truthiness evaluates to whether extraction was successful and non-empty."""
        return self.success and bool(self.text.strip())


# ==============================================================================
# Text Cleaning and Normalization
# ==============================================================================

# Mapping for common typographic ligatures found in LaTeX / modern PDF typography
_LIGATURE_REPLACEMENTS = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "ft",
    "\ufb06": "st",
    "\u2010": "-",  # hyphen
    "\u2011": "-",  # non-breaking hyphen
    "\u2012": "-",  # figure dash
    "\u2013": "-",  # en-dash
    "\u2014": " - ",  # em-dash
    "\u2018": "'",  # left single quote
    "\u2019": "'",  # right single quote
    "\u201c": '"',  # left double quote
    "\u201d": '"',  # right double quote
    "\u00a0": " ",  # non-breaking space
    "\u202f": " ",  # narrow no-break space
    "\u200b": "",   # zero-width space
    "\ufeff": "",   # zero-width no-break space / BOM
    "\u200e": "",   # left-to-right mark
    "\u200f": "",   # right-to-left mark
}

# Regex to match non-standard control characters (excluding standard \t and \n)
_CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Regex to match bullet symbols commonly used in resumes
_BULLET_SYMBOLS_PATTERN = re.compile(r"^[\s]*[\u2022\u25cf\u25aa\u25ab\u25e6\u2023\u2043\u2219\*\-]\s+", re.MULTILINE)

# Regex to heal words split across line breaks by hyphens (e.g., "imple-\nmentation" -> "implementation")
_HYPHENATED_LINEBREAK_PATTERN = re.compile(r"(\b[a-zA-Z]{2,})-\s*\n\s*([a-zA-Z]{2,}\b)")


def clean_text(raw_text: Optional[str]) -> str:
    """
    Cleans and normalizes raw text extracted from resumes and portfolios.

    Operations performed:
    1. Replaces typographic ligatures and non-standard quotation/dash characters.
    2. Removes non-standard ASCII and Unicode control characters.
    3. Heals hyphenated line-break artifacts common in narrow PDF columns.
    4. Standardizes bullet characters into uniform '• ' markers.
    5. Strips redundant horizontal whitespace and tabs.
    6. Eliminates excessive blank lines while preserving paragraph boundaries.

    Args:
        raw_text: Raw string extracted from document.

    Returns:
        Cleaned, readable string. Returns empty string if input is None or empty.
    """
    if not raw_text or not isinstance(raw_text, str):
        return ""

    text = raw_text

    # 1. Normalize carriage returns to standard newline
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Replace ligatures and specific Unicode typography characters
    for ligature, replacement in _LIGATURE_REPLACEMENTS.items():
        if ligature in text:
            text = text.replace(ligature, replacement)

    # 3. Strip non-printable control characters (keeping \t and \n)
    text = _CONTROL_CHARS_PATTERN.sub("", text)

    # 4. Heal hyphenated words split across line breaks
    # Example: "architec-\nture" becomes "architecture"
    text = _HYPHENATED_LINEBREAK_PATTERN.sub(r"\1\2", text)

    # 5. Standardize bullet characters at the start of lines
    text = _BULLET_SYMBOLS_PATTERN.sub("• ", text)

    # 6. Process line by line: collapse multiple spaces/tabs and strip line boundaries
    processed_lines = []
    for line in text.split("\n"):
        # Collapse horizontal whitespace
        cleaned_line = re.sub(r"[^\S\n]+", " ", line).strip()
        processed_lines.append(cleaned_line)

    text = "\n".join(processed_lines)

    # 7. Collapse 3+ consecutive newlines down to 2 (maintaining paragraph separation)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ==============================================================================
# Low-level Extractors
# ==============================================================================

def _extract_with_pdfplumber(stream: io.BytesIO) -> Tuple[bool, str, int, Optional[str]]:
    """
    Primary PDF extraction using pdfplumber.
    Returns: (success, extracted_text, page_count, error_message)
    """
    if not _HAS_PDFPLUMBER:
        return False, "", 0, "pdfplumber is not installed"

    stream.seek(0)
    pages_text = []
    page_count = 0

    try:
        with pdfplumber.open(stream) as pdf:
            page_count = len(pdf.pages)
            if page_count == 0:
                return False, "", 0, "PDF contains no pages"

            for i, page in enumerate(pdf.pages):
                try:
                    # layout=False preserves sequential text flow; fallback to layout=True if needed
                    extracted = page.extract_text()
                    if extracted and extracted.strip():
                        pages_text.append(extracted.strip())
                except Exception as page_err:
                    logger.debug(f"pdfplumber error on page {i + 1}: {page_err}")

        combined_text = "\n\n".join(pages_text).strip()
        if not combined_text:
            return False, "", page_count, "pdfplumber returned empty text (possible scanned document or complex layout)"

        return True, combined_text, page_count, None

    except Exception as exc:
        err_msg = str(exc)
        # Check for password issues in exception string
        if "password" in err_msg.lower() or "encrypt" in err_msg.lower():
            return False, "", 0, "The PDF file is password-protected and cannot be parsed."
        return False, "", page_count, f"pdfplumber extraction failed: {err_msg}"


def _extract_with_pypdf(stream: io.BytesIO) -> Tuple[bool, str, int, Optional[str]]:
    """
    Fallback PDF extraction using PyPDF2 / pypdf.
    Returns: (success, extracted_text, page_count, error_message)
    """
    if not _HAS_PYPDF2:
        return False, "", 0, "PyPDF2 / pypdf is not installed"

    stream.seek(0)
    pages_text = []
    page_count = 0

    try:
        # PyPDF2 >= 3.0.0 uses PdfReader; older versions use PdfFileReader
        if hasattr(PyPDF2, "PdfReader"):
            reader = PyPDF2.PdfReader(stream)
        elif hasattr(PyPDF2, "PdfFileReader"):
            reader = PyPDF2.PdfFileReader(stream)
        else:
            return False, "", 0, "No compatible PdfReader found in PyPDF2"

        # Check for encryption
        if getattr(reader, "is_encrypted", False):
            # Attempt to decrypt with empty password (standard for some protected PDFs)
            try:
                decrypted = reader.decrypt("")
                # In PyPDF2, decrypt returns 0, 1, or 2, or a boolean
                if decrypted == 0:
                    return False, "", 0, "The PDF file is password-protected and cannot be read without credentials."
            except Exception:
                return False, "", 0, "The PDF file is encrypted and password-protected."

        pages = getattr(reader, "pages", None)
        if pages is None and hasattr(reader, "getNumPages"):
            pages = [reader.getPage(i) for i in range(reader.getNumPages())]

        page_count = len(pages) if pages else 0
        if page_count == 0:
            return False, "", 0, "PDF contains no pages or could not be read"

        for i, page in enumerate(pages):
            try:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    pages_text.append(page_text.strip())
            except Exception as page_err:
                logger.debug(f"PyPDF2 error on page {i + 1}: {page_err}")

        combined_text = "\n\n".join(pages_text).strip()
        if not combined_text:
            return False, "", page_count, "PyPDF2 returned empty text. The document may be a scanned image or contain non-extractable text."

        return True, combined_text, page_count, None

    except Exception as exc:
        err_msg = str(exc)
        if "password" in err_msg.lower() or "encrypt" in err_msg.lower():
            return False, "", 0, "The PDF file is password-protected and cannot be parsed."
        return False, "", page_count, f"PyPDF2 extraction failed: {err_msg}"


def _extract_from_docx(stream: io.BytesIO) -> Tuple[bool, str, int, Optional[str]]:
    """
    Extracts text from DOCX files, capturing both paragraphs and structured tables.
    Returns: (success, extracted_text, estimated_pages, error_message)
    """
    if not _HAS_DOCX:
        return False, "", 0, "python-docx is not installed. Please install it using `pip install python-docx`."

    stream.seek(0)
    try:
        doc = docx.Document(stream)
        content_elements = []

        # 1. Extract paragraphs
        for p in doc.paragraphs:
            p_text = p.text.strip()
            if p_text:
                content_elements.append(p_text)

        # 2. Extract tables (resumes often use 2-column tables for skills or contact headers)
        for table in doc.tables:
            for row in table.rows:
                # Deduplicate merged cells in the same row
                seen_cells = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text and (not seen_cells or cell_text != seen_cells[-1]):
                        seen_cells.append(cell_text)
                if seen_cells:
                    content_elements.append(" | ".join(seen_cells))

        combined_text = "\n\n".join(content_elements).strip()
        if not combined_text:
            return False, "", 1, "The DOCX file does not contain any readable text."

        # Estimate page count (roughly 3000 chars per page as rough heuristic for docx)
        estimated_pages = max(1, len(combined_text) // 3000 + 1)
        return True, combined_text, estimated_pages, None

    except Exception as exc:
        err_msg = str(exc)
        if "not a valid zip file" in err_msg.lower() or "file is not a zip file" in err_msg.lower():
            return False, "", 0, "The file is corrupted or not a valid DOCX document."
        return False, "", 0, f"Failed to extract text from DOCX: {err_msg}"


# ==============================================================================
# Helper & Normalization Utilities
# ==============================================================================

def _prepare_byte_stream(
    file_input: Union[str, Path, bytes, BinaryIO, Any],
    file_name: Optional[str] = None,
) -> Tuple[Optional[io.BytesIO], str, Optional[str]]:
    """
    Normalizes various input formats (Streamlit UploadedFile, file path, bytes, or file-like objects)
    into an in-memory `io.BytesIO` stream and extracts the filename.

    Returns:
        (stream, detected_filename, error_message)
    """
    if file_input is None:
        return None, "", "No file was provided (file input is None)."

    detected_name = file_name or ""

    # Case A: String or Path representing a local file path
    if isinstance(file_input, (str, Path)):
        path = Path(file_input)
        if not path.exists():
            return None, path.name, f"File not found: {path}"
        if not path.is_file():
            return None, path.name, f"Path is not a regular file: {path}"

        size = path.stat().st_size
        if size == 0:
            return None, path.name, "File is empty (0 bytes)."

        if not detected_name:
            detected_name = path.name

        try:
            with open(path, "rb") as f:
                return io.BytesIO(f.read()), detected_name, None
        except Exception as e:
            return None, detected_name, f"Could not open file: {e}"

    # Case B: Raw bytes
    if isinstance(file_input, bytes):
        if len(file_input) == 0:
            return None, detected_name or "document", "File is empty (0 bytes)."
        return io.BytesIO(file_input), detected_name or "document", None

    # Case C: Streamlit UploadedFile or file-like object
    # Duck-typing: Check for getvalue(), name, or read()
    if hasattr(file_input, "name") and not detected_name:
        detected_name = getattr(file_input, "name", "")

    try:
        # Check if it has getvalue() (typical of Streamlit UploadedFile or BytesIO)
        if hasattr(file_input, "getvalue") and callable(file_input.getvalue):
            raw_bytes = file_input.getvalue()
        elif hasattr(file_input, "read") and callable(file_input.read):
            # If pointer at end, seek(0) first
            if hasattr(file_input, "seek") and callable(file_input.seek):
                try:
                    file_input.seek(0)
                except Exception:
                    pass
            raw_bytes = file_input.read()
            # Reset pointer after reading
            if hasattr(file_input, "seek") and callable(file_input.seek):
                try:
                    file_input.seek(0)
                except Exception:
                    pass
        else:
            return None, detected_name, "Unsupported file input type."

        if not raw_bytes or len(raw_bytes) == 0:
            return None, detected_name or "document", "File is empty (0 bytes)."

        return io.BytesIO(raw_bytes), detected_name or "document", None

    except Exception as err:
        return None, detected_name or "document", f"Error reading file stream: {err}"


def _detect_file_type(stream: io.BytesIO, file_name: str) -> Optional[str]:
    """
    Infers document type ('pdf' or 'docx') using file extension and magic byte headers.
    """
    ext = Path(file_name).suffix.lower().lstrip(".")
    if ext in ["pdf", "docx"]:
        return ext

    # Fallback to inspecting magic numbers
    stream.seek(0)
    header = stream.read(8)
    stream.seek(0)

    if header.startswith(b"%PDF"):
        return "pdf"
    if header.startswith(b"PK\x03\x04"):
        return "docx"

    return None


# ==============================================================================
# Public API Functions
# ==============================================================================

def extract_from_pdf(
    file_input: Union[str, Path, bytes, BinaryIO, Any],
    file_name: Optional[str] = None,
    clean: bool = True,
) -> ParseResult:
    """
    Extracts text from a PDF document using pdfplumber as the primary engine
    and PyPDF2/pypdf as an automatic fallback.

    Args:
        file_input: File path, bytes, or file-like object (e.g. Streamlit UploadedFile).
        file_name: Optional filename for logging and metadata.
        clean: Whether to apply text cleaning and normalization (default: True).

    Returns:
        ParseResult containing extracted text, raw text, metadata, and status.
    """
    stream, resolved_name, err = _prepare_byte_stream(file_input, file_name)
    if err or stream is None:
        return ParseResult(
            success=False,
            error=err or "Failed to load document stream.",
            file_name=resolved_name,
            file_type="pdf",
        )

    # 1. Primary Extraction: pdfplumber
    success, raw_text, page_count, plumber_err = _extract_with_pdfplumber(stream)
    method = "pdfplumber"

    # 2. Check if Fallback to PyPDF2 is necessary
    if not success or not raw_text.strip():
        # If the failure was due to password protection, PyPDF2 will also fail with password
        if plumber_err and "password" in plumber_err.lower():
            return ParseResult(
                success=False,
                error=plumber_err,
                file_name=resolved_name,
                file_type="pdf",
                page_count=page_count,
            )

        logger.info(f"pdfplumber extraction unsuccessful ({plumber_err}). Initiating PyPDF2 fallback.")
        fallback_success, fallback_text, fallback_pages, pypdf_err = _extract_with_pypdf(stream)

        if fallback_success and fallback_text.strip():
            success = True
            raw_text = fallback_text
            page_count = fallback_pages or page_count
            method = "PyPDF2"
        else:
            # Check if failure was due to password protection
            if (pypdf_err and "password" in pypdf_err.lower()) or (plumber_err and "password" in plumber_err.lower()):
                combined_error = "The PDF file is password-protected and cannot be read without credentials."
            else:
                combined_error = (
                    f"PDF extraction failed. Primary engine (pdfplumber): {plumber_err or 'Empty text'}. "
                    f"Fallback engine (PyPDF2): {pypdf_err or 'Empty text'}."
                )
            return ParseResult(
                success=False,
                error=combined_error,
                file_name=resolved_name,
                file_type="pdf",
                page_count=page_count or fallback_pages,
            )

    # 3. Clean Text
    processed_text = clean_text(raw_text) if clean else raw_text

    return ParseResult(
        text=processed_text,
        raw_text=raw_text,
        success=True,
        extraction_method=method,
        page_count=page_count,
        file_name=resolved_name,
        file_type="pdf",
        metadata={"cleaned": clean, "character_count": len(processed_text)},
    )


def extract_from_docx(
    file_input: Union[str, Path, bytes, BinaryIO, Any],
    file_name: Optional[str] = None,
    clean: bool = True,
) -> ParseResult:
    """
    Extracts text from a DOCX document using python-docx.

    Args:
        file_input: File path, bytes, or file-like object (e.g. Streamlit UploadedFile).
        file_name: Optional filename for logging and metadata.
        clean: Whether to apply text cleaning and normalization (default: True).

    Returns:
        ParseResult containing extracted text, raw text, metadata, and status.
    """
    stream, resolved_name, err = _prepare_byte_stream(file_input, file_name)
    if err or stream is None:
        return ParseResult(
            success=False,
            error=err or "Failed to load document stream.",
            file_name=resolved_name,
            file_type="docx",
        )

    success, raw_text, page_count, docx_err = _extract_from_docx(stream)
    if not success:
        return ParseResult(
            success=False,
            error=docx_err or "Failed to extract text from DOCX.",
            file_name=resolved_name,
            file_type="docx",
            page_count=page_count,
        )

    processed_text = clean_text(raw_text) if clean else raw_text

    return ParseResult(
        text=processed_text,
        raw_text=raw_text,
        success=True,
        extraction_method="docx",
        page_count=page_count,
        file_name=resolved_name,
        file_type="docx",
        metadata={"cleaned": clean, "character_count": len(processed_text)},
    )


def extract_text_from_file(
    file_input: Union[str, Path, bytes, BinaryIO, Any],
    file_name: Optional[str] = None,
    clean: bool = True,
) -> ParseResult:
    """
    Universal extraction entrypoint. Automatically detects whether the file
    is PDF or DOCX and invokes the appropriate parser pipeline.

    Ideal for direct use with Streamlit's `st.file_uploader`:
    ```python
    uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])
    if uploaded_file:
        result = extract_text_from_file(uploaded_file)
        if result.success:
            st.write(result.text)
        else:
            st.error(result.error)
    ```

    Args:
        file_input: File path, bytes, or file-like object (Streamlit UploadedFile).
        file_name: Explicit filename if file_input is raw bytes.
        clean: Whether to normalize and clean the text.

    Returns:
        ParseResult containing parsed output and metadata.
    """
    stream, resolved_name, err = _prepare_byte_stream(file_input, file_name)
    if err or stream is None:
        return ParseResult(
            success=False,
            error=err or "Invalid file input.",
            file_name=resolved_name,
        )

    file_type = _detect_file_type(stream, resolved_name)

    if file_type == "pdf":
        return extract_from_pdf(stream, file_name=resolved_name, clean=clean)
    elif file_type == "docx":
        return extract_from_docx(stream, file_name=resolved_name, clean=clean)
    else:
        ext = Path(resolved_name).suffix.lower()
        if ext:
            msg = f"Unsupported file type '{ext}'. Only PDF (.pdf) and DOCX (.docx) documents are supported."
        else:
            msg = "Unrecognized document format. Please upload a valid PDF or DOCX file."
        return ParseResult(
            success=False,
            error=msg,
            file_name=resolved_name,
        )


# Alias for intuitive convenience
parse_document = extract_text_from_file


# ==============================================================================
# CLI and Demonstration
# ==============================================================================

def main():
    """Command-line interface for testing and inspecting documents."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract and clean text from PDF and DOCX resume/portfolio documents."
    )
    parser.add_argument("file_path", help="Path to the PDF or DOCX file.")
    parser.add_argument("--raw", action="store_true", help="Print raw uncleaned text.")
    parser.add_argument("--json", action="store_true", help="Output full ParseResult as JSON.")
    parser.add_argument("--output", "-o", help="Save extracted text to a destination file.")

    args = parser.parse_args()

    result = extract_text_from_file(args.file_path, clean=not args.raw)

    if args.json:
        import json
        print(json.dumps(result.to_dict(), indent=2))
        return

    if not result.success:
        print(f"Error: {result.error}", file=sys.stderr)
        sys.exit(1)

    output_content = result.raw_text if args.raw else result.text

    if args.output:
        Path(args.output).write_text(output_content, encoding="utf-8")
        print(f"Extracted {len(output_content)} characters saved to {args.output}")
        print(f"Engine used: {result.extraction_method} (Pages: {result.page_count})")
    else:
        print(f"--- Extraction Successful ({result.extraction_method}, {result.page_count} pages) ---")
        print(output_content)


if __name__ == "__main__":
    main()

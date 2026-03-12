"""
utils/pdf_extractor.py
Phase 1, Day 2 – PDF Parsing & OCR

Provides a unified extract_text_from_pdf(file) function that:
1. First tries pdfplumber (for digital/text-based PDFs).
2. Falls back to pytesseract + pdf2image for scanned PDFs.
"""

import io
import logging
from typing import Union

import pdfplumber

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# OCR fallback
# ──────────────────────────────────────────────

def _ocr_text_from_bytes(pdf_bytes: bytes) -> str:
    """
    Task 1 (Day 2): OCR for scanned PDFs.
    Converts each page to an image and runs pytesseract.
    Requires poppler to be installed and on PATH.
    """
    try:
        from pdf2image import convert_from_bytes
        import pytesseract

        images = convert_from_bytes(pdf_bytes, dpi=200)
        pages = [pytesseract.image_to_string(img) for img in images]
        text = "\n\n".join(pages)
        logger.info("OCR extracted %d chars from %d pages", len(text), len(images))
        return text
    except ImportError as e:
        logger.warning("pdf2image / pytesseract not available: %s", e)
        return ""
    except Exception as e:
        logger.error("OCR failed: %s", e)
        return ""


# ──────────────────────────────────────────────
# Digital PDF extraction
# ──────────────────────────────────────────────

def _pdfplumber_text(pdf_bytes: bytes) -> str:
    """
    Task 2 (Day 2): Extract text from digital PDFs using pdfplumber.
    """
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        text = "\n\n".join(pages)
        return text
    except Exception as e:
        logger.error("pdfplumber extraction failed: %s", e)
        return ""


def _pdfplumber_tables(pdf_bytes: bytes) -> list[dict]:
    """
    Extract tables from a PDF using pdfplumber.
    Returns a list of row-dictionaries per table.
    """
    tables = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    if table and len(table) > 1:
                        headers = [str(h).strip() if h else f"col{i}"
                                   for i, h in enumerate(table[0])]
                        for row in table[1:]:
                            if any(cell for cell in row):
                                tables.append(dict(zip(headers, row)))
    except Exception as e:
        logger.error("Table extraction failed: %s", e)
    return tables


# ──────────────────────────────────────────────
# Unified entry point
# ──────────────────────────────────────────────

def extract_text_from_pdf(file: Union[bytes, io.BytesIO, str]) -> dict:
    """
    Task 3 (Day 2): Unified PDF extraction.

    Auto-detects digital vs. scanned PDFs:
    - Tries pdfplumber first.
    - Falls back to OCR if extracted text is too short (< 100 chars).

    Args:
        file: PDF as bytes, BytesIO, or a file path string.

    Returns:
        {
            "text":   str,          # Full extracted text
            "tables": list[dict],   # Tables extracted (digital only)
            "method": str,          # "pdfplumber" | "ocr" | "empty"
            "pages":  int,          # Page count
        }
    """
    # Normalise input to bytes
    if isinstance(file, str):
        with open(file, "rb") as f:
            pdf_bytes = f.read()
    elif isinstance(file, io.BytesIO):
        pdf_bytes = file.getvalue()
    else:
        pdf_bytes = file  # assume raw bytes

    # Step 1: Try pdfplumber
    text = _pdfplumber_text(pdf_bytes)
    tables = _pdfplumber_tables(pdf_bytes)

    MIN_CHARS = 100  # threshold to decide if PDF is digital or scanned

    if len(text.strip()) >= MIN_CHARS:
        method = "pdfplumber"
    else:
        # Step 2: Fallback to OCR
        logger.info("pdfplumber yielded < %d chars – switching to OCR", MIN_CHARS)
        text = _ocr_text_from_bytes(pdf_bytes)
        tables = []  # OCR does not produce structured tables
        method = "ocr" if text.strip() else "empty"

    # Count pages
    page_count = 0
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            page_count = len(pdf.pages)
    except Exception:
        pass

    return {
        "text": text,
        "tables": tables,
        "method": method,
        "pages": page_count,
    }

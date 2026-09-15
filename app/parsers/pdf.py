from pathlib import Path

import pymupdf


class PDFExtractionError(Exception):
    """Raised when a PDF cannot be processed."""


# Keep PyMuPDF warnings available internally, but don't print
# recoverable MuPDF diagnostics to the terminal.
pymupdf.TOOLS.mupdf_display_errors(False)


def extract_text_from_pdf(path: str | Path) -> str:
    pdf_path = Path(path)

    if not pdf_path.exists():
        raise PDFExtractionError(f"PDF not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise PDFExtractionError(f"Expected a PDF file: {pdf_path}")

    try:
        with pymupdf.open(pdf_path) as document:
            pages: list[str] = []

            for page in document:
                text = page.get_text("text").strip()

                if text:
                    pages.append(text)

            return "\n\n".join(pages)

    except pymupdf.FileDataError as exc:
        raise PDFExtractionError(
            f"Invalid or corrupted PDF: {pdf_path}"
        ) from exc
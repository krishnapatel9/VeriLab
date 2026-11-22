"""Open an uploaded PDF or image once at upload time, so a file that can never be
read is refused with a clear reason instead of being accepted and failing later."""

from __future__ import annotations

import io

from constants import settings

# Smaller than this and there is nothing legible to read.
MIN_IMAGE_SIDE = 50


class UnreadableDocument(ValueError):
    """The upload can't be used. The message is safe to show to the person."""


def inspect_document(data: bytes, suffix: str) -> int:
    """Return the page count, or raise UnreadableDocument."""
    if suffix == ".pdf":
        return _inspect_pdf(data)
    return _inspect_image(data)


def _inspect_pdf(data: bytes) -> int:
    import pypdfium2 as pdfium

    try:
        pdf = pdfium.PdfDocument(data)
    except pdfium.PdfiumError as exc:
        if "password" in str(exc).lower():
            raise UnreadableDocument("Encrypted or password-protected PDFs are not accepted") from exc
        raise UnreadableDocument(
            "This PDF can't be opened. It may be damaged, or not a real PDF. "
            "Try exporting or scanning it again."
        ) from exc
    try:
        pages = len(pdf)
    finally:
        pdf.close()
    if pages == 0:
        raise UnreadableDocument("This PDF has no pages.")
    if pages > settings.max_pdf_pages:
        raise UnreadableDocument(
            f"This PDF has {pages} pages. The limit is {settings.max_pdf_pages}; "
            "please upload one report at a time."
        )
    return pages


def _inspect_image(data: bytes) -> int:
    from PIL import Image

    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()  # checks the file's structure
        with Image.open(io.BytesIO(data)) as img:
            width, height = img.size
            img.load()  # decodes the pixels, catching truncated files
    except Exception as exc:  # PIL raises many types for broken files
        raise UnreadableDocument(
            "This image can't be opened. It may be damaged or incomplete."
        ) from exc
    if min(width, height) < MIN_IMAGE_SIDE:
        raise UnreadableDocument(
            f"This image is only {width}×{height} pixels, too small to read. "
            "Upload a clearer scan or photo."
        )
    return 1

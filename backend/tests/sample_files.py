"""Small real PDFs and PNGs for upload tests. Uploads are opened at intake, so
fake bytes like b"%PDF-1.4 x" are (correctly) refused. Each call with a different
tag gives different bytes, and so a different SHA-256."""

import io
import uuid

from PIL import Image


def _image(tag: str | None) -> Image.Image:
    seed = uuid.uuid5(uuid.NAMESPACE_OID, tag or uuid.uuid4().hex).bytes
    img = Image.new("RGB", (200, 120), "white")
    for i, b in enumerate(seed):  # a unique dot pattern per tag
        img.putpixel((10 + i * 10, 10 + b % 100), (0, 0, 0))
    return img


def make_pdf(tag: str | None = None) -> bytes:
    buf = io.BytesIO()
    _image(tag).save(buf, format="PDF")
    return buf.getvalue()


def make_png(tag: str | None = None) -> bytes:
    buf = io.BytesIO()
    _image(tag).save(buf, format="PNG")
    return buf.getvalue()

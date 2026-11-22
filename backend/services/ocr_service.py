import io
import logging
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import uuid
import asyncio
import threading
from PIL import Image
from sqlalchemy.orm import Session
from db.models.core_models import Report, Result, ReviewItem, generate_uuidv7
from services.storage import get_storage
from constants import (
    PHASE1_VALUE_CONFIDENCE_REVIEW_BELOW,
    FIELD_CONFIDENCE_THRESHOLDS,
    settings,
)

logger = logging.getLogger(__name__)


def parse_numeric_value(value_raw: str) -> float | None:
    """
    Tier 1.8: Parses exact numeric values into float.
    If value_raw contains inequality operators ('<', '>'), returns None
    so that bounded values like '<0.01' are never naively stripped to 0.01.
    """
    if not value_raw:
        return None
    val_clean = value_raw.strip()
    if re.search(r"[<>]", val_clean):
        return None
    try:
        return float(val_clean)
    except ValueError:
        return None


class OCRProvider(ABC):
    """
    Abstract base class for OCR extraction.
    Ensures that we can swap between Mock or any future self-hosted OCR provider.
    """
    @abstractmethod
    async def extract_data(self, file_path: str) -> Dict[str, Any]:
        pass


class MockOCRProvider(OCRProvider):
    """
    DEMO ONLY. Returns the same fixed payload for every upload, regardless of the
    file's contents. Never use it with anything but synthetic data.
    """
    async def extract_data(self, file_path: str) -> Dict[str, Any]:
        if settings.environment != "development":
            raise RuntimeError("MockOCRProvider cannot be executed in non-development environments.")

        await asyncio.sleep(2)  # Simulate network latency

        return {
            "patient_info": {
                "name": "Jane Doe",
                "patient_id": "MRN-12345",
                "collection_date": "2026-10-01"
            },
            "results": [
                {
                    "test_name": "Hemoglobin",
                    "value": "12.5",
                    "unit": "g/dL",
                    "reference_range": "12.0 - 15.5",
                    "flag": "Normal",
                    "confidence": 0.98,
                    "bounding_box": {"x1": 100, "y1": 200, "x2": 400, "y2": 220}
                },
                {
                    "test_name": "TSH",
                    "value": "<0.01",
                    "unit": "uIU/mL",
                    "reference_range": "0.4 - 4.0",
                    "flag": "Low",
                    "confidence": 0.85,  # Simulated lower confidence for the '<' symbol
                    "bounding_box": {"x1": 100, "y1": 250, "x2": 400, "y2": 270}
                }
            ]
        }


# "Name  value  unit  low - high  [flag]" on one line, e.g. "Hemoglobin 12.5 g/dL 12.0 - 15.5 L".
# ponytail: single-line layouts only; add table-aware parsing when real report samples exist.
_LINE = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z0-9 ()/%.,-]*?)\s+"
    r"(?P<value>[<>]?\s?-?\d+(?:\.\d+)?)\s*"
    r"(?P<unit>[A-Za-z%µμ][A-Za-z0-9%/µμ^.*-]*(?:/[A-Za-z0-9]+)?)?\s*"
    r"(?P<range>\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?)?\s*"
    r"(?P<flag>High|Low|Normal|Critical|H|L|\*{1,2})?$"
)

# Downscale huge scans before OCR: keeps memory and time sane on small hosts.
_MAX_SIDE = 2000
# PDF pages are rendered at this scale (1.0 = 72 dpi).
_PDF_SCALE = 2.0


def _group_lines(boxes, txts, scores) -> List[Dict[str, Any]]:
    """
    Turn OCR text boxes into printed lines. A box whose vertical centre falls
    inside an existing line's band joins that line; each line is then read left
    to right. Each line keeps, per character span, the score of the box it came
    from, so a field's confidence is the score of the boxes that field came from.
    """
    items = []
    for box, txt, sc in zip(boxes, txts, scores):
        txt = (txt or "").strip()
        if not txt:
            continue
        xs = [float(p[0]) for p in box]
        ys = [float(p[1]) for p in box]
        items.append({"x1": min(xs), "y1": min(ys), "x2": max(xs), "y2": max(ys), "text": txt, "score": float(sc)})
    items.sort(key=lambda i: (i["y1"] + i["y2"]) / 2)

    lines: List[List[dict]] = []
    for it in items:
        cy = (it["y1"] + it["y2"]) / 2
        for line in lines:
            if min(i["y1"] for i in line) <= cy <= max(i["y2"] for i in line):
                line.append(it)
                break
        else:
            lines.append([it])

    out = []
    for line in lines:
        line.sort(key=lambda i: i["x1"])
        text, spans = "", []
        for it in line:
            if text:
                text += " "
            spans.append((len(text), len(text) + len(it["text"]), it["score"]))
            text += it["text"]
        out.append({
            "text": text,
            "spans": spans,
            "bbox": {
                "x1": int(min(i["x1"] for i in line)), "y1": int(min(i["y1"] for i in line)),
                "x2": int(max(i["x2"] for i in line)), "y2": int(max(i["y2"] for i in line)),
            },
        })
    return out


def _span_confidence(spans, start: int, end: int) -> float | None:
    """Lowest score among the boxes that a matched field's characters came from."""
    hit = [sc for (s, e, sc) in spans if s < end and start < e]
    return min(hit) if hit else None


def parse_result_lines(lines: List[Dict[str, Any]], page_no: int) -> List[Dict[str, Any]]:
    results = []
    for line in lines:
        m = _LINE.match(line["text"])
        if not m:
            continue
        # A lab result row prints a unit or a reference range. Lines with neither
        # (e.g. "Page 1 of 1") are layout text, not results.
        if not m["unit"] and not m["range"]:
            continue
        overall = min(sc for (_, _, sc) in line["spans"])

        def conf(group: str) -> float:
            c = None if m[group] is None else _span_confidence(line["spans"], m.start(group), m.end(group))
            return round(overall if c is None else c, 2)

        results.append({
            "test_name": m["name"].strip(),
            "value": m["value"].replace(" ", ""),
            "unit": m["unit"],
            "reference_range": m["range"],
            "flag": m["flag"],
            "confidence": round(overall, 2),
            "confidence_test_name": conf("name"),
            "confidence_value": conf("value"),
            "confidence_unit": conf("unit"),
            "confidence_reference_range": conf("range"),
            "bounding_box": line["bbox"],
            "page": page_no,
        })
    return results


_engine = None
_engine_lock = threading.Lock()


def _get_engine():
    """Load the OCR models once per process (a few seconds, ~100 MB)."""
    global _engine
    with _engine_lock:
        if _engine is None:
            from rapidocr import RapidOCR
            # Lab reports are upright. The text-orientation classifier can flip short
            # words (it read "g/dL" as "7p/6"), so it stays off.
            _engine = RapidOCR(params={
                "Global.use_cls": False,
                # Text detection runs on the page scaled so its longer side is at most
                # this many pixels. 960 keeps peak memory near 330 MB, inside a 512 MB host.
                "Det.limit_type": "max",
                "Det.limit_side_len": settings.ocr_det_max_side,
            })
        return _engine


def warm_up() -> None:
    """Download (if needed) and load the OCR models. Hosts run this at build time."""
    _get_engine()


def _to_images(data: bytes, is_pdf: bool) -> List[Image.Image]:
    if is_pdf:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(data)
        try:
            pages = [pdf[i].render(scale=_PDF_SCALE).to_pil() for i in range(len(pdf))]
        finally:
            pdf.close()
    else:
        pages = [Image.open(io.BytesIO(data))]
    out = []
    for img in pages:
        img = img.convert("RGB")
        if max(img.size) > _MAX_SIDE:
            img.thumbnail((_MAX_SIDE, _MAX_SIDE))
        out.append(img)
    return out


class RapidOCRProvider(OCRProvider):
    """
    Real OCR via RapidOCR (PaddleOCR models on ONNX Runtime). A plain pip
    install with no system packages, so it runs on any Python host. Values are
    the printed text, verbatim. Each field's confidence is the recogniser's
    score for the text box it came from. Any failure raises: the report goes
    to 'error' rather than showing invented results.
    """
    async def extract_data(self, file_path: str) -> Dict[str, Any]:
        data = await asyncio.to_thread(get_storage().get, file_path)
        if data is None:
            raise FileNotFoundError(f"Stored file missing for {file_path}")
        return await asyncio.to_thread(self._extract, data, file_path.lower().endswith(".pdf"))

    def _extract(self, data: bytes, is_pdf: bool) -> Dict[str, Any]:
        import numpy as np

        engine = _get_engine()
        results: List[Dict[str, Any]] = []
        for page_no, img in enumerate(_to_images(data, is_pdf), start=1):
            out = engine(np.array(img)[:, :, ::-1].copy())  # RGB -> BGR, as OpenCV expects
            if out.boxes is None or out.txts is None:
                continue  # blank page
            results.extend(parse_result_lines(_group_lines(out.boxes, out.txts, out.scores), page_no))

        logger.info("OCR extracted %d result lines", len(results))
        # Patient identity is deliberately NOT guessed here (Invariant 3): matching is a separate, human-gated step.
        return {"patient_info": {}, "results": results}


class OCRService:
    def __init__(self, db_session: Session, provider: OCRProvider = None):
        self.db = db_session
        self.last_error: str | None = None  # why the last process_report failed, for the audit trail
        if provider:
            if isinstance(provider, MockOCRProvider) and settings.environment != "development":
                raise RuntimeError("MockOCRProvider is strictly prohibited outside development environments.")
            self.provider = provider
        elif settings.ocr_provider == "mock":
            if settings.environment != "development":
                raise RuntimeError("Mock OCR provider is configured, but environment is not 'development'.")
            self.provider = MockOCRProvider()
        elif settings.ocr_provider in ("rapidocr", "tesseract"):  # "tesseract" kept as an alias for old configs
            self.provider = RapidOCRProvider()
        else:
            raise RuntimeError(f"Unknown OCR_PROVIDER {settings.ocr_provider!r}; use 'rapidocr' or 'mock'.")

    async def process_report(self, report_id: uuid.UUID):
        """
        Retrieves the report, calls the OCR provider, and maps the extracted
        data to the Result and ReviewItem database models.
        """
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report:
            logger.warning("Report %s not found for OCR processing", report_id)
            return

        # 1. Update status to processing
        report.status = 'processing'
        self.db.commit()

        try:
            # 2. Extract data
            extracted_data = await self.provider.extract_data(report.file_object_key)

            # 3. Map extracted data to Result + ReviewItem models
            for item in extracted_data.get("results", []):
                confidence = float(item["confidence"])
                conf_test_name = float(item.get("confidence_test_name", confidence))
                conf_value = float(item.get("confidence_value", confidence))
                conf_unit = float(item.get("confidence_unit", confidence))
                conf_ref_range = float(item.get("confidence_reference_range", confidence))

                flag_reasons = []
                if conf_value < FIELD_CONFIDENCE_THRESHOLDS["value"]:
                    flag_reasons.append(
                        f"Value confidence {conf_value:.0%} is below threshold {FIELD_CONFIDENCE_THRESHOLDS['value']:.0%}"
                    )
                if conf_test_name < FIELD_CONFIDENCE_THRESHOLDS["test_name"]:
                    flag_reasons.append(
                        f"Test name confidence {conf_test_name:.0%} is below threshold {FIELD_CONFIDENCE_THRESHOLDS['test_name']:.0%}"
                    )
                if conf_unit < FIELD_CONFIDENCE_THRESHOLDS["unit"]:
                    flag_reasons.append(
                        f"Unit confidence {conf_unit:.0%} is below threshold {FIELD_CONFIDENCE_THRESHOLDS['unit']:.0%}"
                    )
                if conf_ref_range < FIELD_CONFIDENCE_THRESHOLDS["reference_range"]:
                    flag_reasons.append(
                        f"Ref range confidence {conf_ref_range:.0%} is below threshold {FIELD_CONFIDENCE_THRESHOLDS['reference_range']:.0%}"
                    )

                needs_review = len(flag_reasons) > 0 or (confidence < PHASE1_VALUE_CONFIDENCE_REVIEW_BELOW)
                verification_status = 'needs_review' if needs_review else 'unverified'

                # Determine if result is critical based on the flag
                is_critical_flag = False
                if item.get("flag") and str(item["flag"]).lower() in ["high", "low", "h", "l", "abnormal", "critical", "*", "**"]:
                    is_critical_flag = True

                parsed_numeric = parse_numeric_value(item["value"])

                new_result = Result(
                    id=generate_uuidv7(),
                    tenant_id=report.tenant_id,
                    report_id=report.id,
                    test_name_raw=item["test_name"],
                    value_raw=item["value"],
                    value_numeric=parsed_numeric,
                    unit_raw=item.get("unit"),
                    reference_range_raw=item.get("reference_range"),
                    flag_raw=item.get("flag"),
                    is_critical=is_critical_flag,

                    # Distribute confidence score across all fields
                    confidence_test_name=conf_test_name,
                    confidence_value=conf_value,
                    confidence_unit=conf_unit,
                    confidence_reference_range=conf_ref_range,

                    # Map bounding box to source fields
                    source_page=item.get("page", 1),
                    source_x=item["bounding_box"]["x1"],
                    source_y=item["bounding_box"]["y1"],
                    source_width=item["bounding_box"]["x2"] - item["bounding_box"]["x1"],
                    source_height=item["bounding_box"]["y2"] - item["bounding_box"]["y1"],
                    # FR-17: Route ambiguity to review based on confidence
                    verification_status=verification_status,
                )
                self.db.add(new_result)
                self.db.flush()  # Get new_result.id before creating ReviewItem

                # 3a. Create a ReviewItem for every low-confidence result (Task 1.3)
                if needs_review:
                    reason_str = "; ".join(flag_reasons) if flag_reasons else (
                        f"Value confidence {confidence:.0%} is below threshold "
                        f"{PHASE1_VALUE_CONFIDENCE_REVIEW_BELOW:.0%} for test '{item['test_name']}'"
                    )
                    review_item = ReviewItem(
                        id=generate_uuidv7(),
                        tenant_id=report.tenant_id,
                        report_id=report.id,
                        result_id=new_result.id,
                        item_type="field_confidence",
                        flag_reason=reason_str,
                        status="open",
                    )
                    self.db.add(review_item)

            # 4. Mark report as processed
            report.status = 'processed'
            self.db.commit()
            logger.info("Processed OCR for report %s", report_id)

        except Exception as exc:
            self.db.rollback()
            self.last_error = f"{type(exc).__name__}: {exc}"[:500]
            report.status = 'error'
            self.db.commit()
            logger.exception("OCR processing failed for report %s", report_id)


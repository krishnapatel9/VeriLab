import io
import logging
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import uuid
import asyncio
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
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


class TesseractOCRProvider(OCRProvider):
    """
    Real OCR via Tesseract. Needs the Tesseract binary (and Poppler for PDFs).
    Values are the printed text, verbatim. Confidence is Tesseract's own mean
    word confidence for the line. Any failure raises: the report goes to
    'error' rather than showing invented results.
    """
    async def extract_data(self, file_path: str) -> Dict[str, Any]:
        data = await asyncio.to_thread(get_storage().get, file_path)
        if data is None:
            raise FileNotFoundError(f"Stored file missing for {file_path}")

        images = convert_from_bytes(data) if file_path.lower().endswith(".pdf") \
            else [Image.open(io.BytesIO(data))]

        results: List[Dict[str, Any]] = []
        for page_no, img in enumerate(images, start=1):
            d = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            lines: Dict[tuple, list] = {}
            for i, word in enumerate(d["text"]):
                if word.strip() and float(d["conf"][i]) >= 0:
                    lines.setdefault((d["block_num"][i], d["par_num"][i], d["line_num"][i]), []).append(i)
            for idxs in lines.values():
                text = " ".join(d["text"][i] for i in idxs)
                m = _LINE.match(text.strip())
                if not m:
                    continue
                x1 = min(d["left"][i] for i in idxs)
                y1 = min(d["top"][i] for i in idxs)
                x2 = max(d["left"][i] + d["width"][i] for i in idxs)
                y2 = max(d["top"][i] + d["height"][i] for i in idxs)
                results.append({
                    "test_name": m["name"].strip(),
                    "value": m["value"].replace(" ", ""),
                    "unit": m["unit"],
                    "reference_range": m["range"],
                    "flag": m["flag"],
                    "confidence": round(sum(float(d["conf"][i]) for i in idxs) / len(idxs) / 100, 2),
                    "bounding_box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "page": page_no,
                })

        logger.info("Tesseract extracted %d result lines", len(results))
        # Patient identity is deliberately NOT guessed here (Invariant 3): matching is a separate, human-gated step.
        return {"patient_info": {}, "results": results}


class OCRService:
    def __init__(self, db_session: Session, provider: OCRProvider = None):
        self.db = db_session
        if provider:
            if isinstance(provider, MockOCRProvider) and settings.environment != "development":
                raise RuntimeError("MockOCRProvider is strictly prohibited outside development environments.")
            self.provider = provider
        elif settings.ocr_provider == "mock":
            if settings.environment != "development":
                raise RuntimeError("Mock OCR provider is configured, but environment is not 'development'.")
            self.provider = MockOCRProvider()
        else:
            self.provider = TesseractOCRProvider()

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

        except Exception:
            self.db.rollback()
            report.status = 'error'
            self.db.commit()
            logger.exception("OCR processing failed for report %s", report_id)


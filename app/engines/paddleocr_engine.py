import logging
from typing import Any, List, Optional
import numpy as np
from .base import BaseOCREngine
from .easyocr_engine import sort_lines_reading_order
from app.config import get_settings

logger = logging.getLogger(__name__)


class PaddleOCREngine(BaseOCREngine):
    """
    PaddleOCR Engine wrapper with fallback capability.
    """
    name: str = "paddleocr"
    _ocr = None

    def __init__(self, languages: Optional[List[str]] = None, gpu: Optional[bool] = None):
        settings = get_settings()
        self.languages = languages or getattr(settings, "ocr_languages", ["en"])
        self.gpu = gpu if gpu is not None else getattr(settings, "ocr_gpu", False)

    def _ensure_engine(self):
        if PaddleOCREngine._ocr is None:
            try:
                from paddleocr import PaddleOCR
                lang = self.languages[0] if self.languages else "en"
                PaddleOCREngine._ocr = PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=self.gpu)
                logger.info("PaddleOCR engine loaded successfully.")
            except ImportError:
                logger.warning("PaddleOCR package is not installed. Falling back to EasyOCR.")
                raise ImportError("PaddleOCR not installed")

    def recognize(self, image: np.ndarray) -> List[dict[str, Any]]:
        self._ensure_engine()
        settings = get_settings()
        min_conf = getattr(settings, "min_confidence_threshold", 0.20)

        results = PaddleOCREngine._ocr.ocr(image, cls=True)

        output_lines = []
        if results and results[0]:
            for line_res in results[0]:
                bbox, (text, confidence) = line_res
                text_str = str(text).strip()
                conf_val = round(float(confidence), 4)

                if conf_val < min_conf or not text_str:
                    continue

                clean_bbox = [[round(float(c), 2) for c in pt] for pt in bbox]
                output_lines.append({
                    "text": text_str,
                    "confidence": conf_val,
                    "bbox": clean_bbox,
                })

        return sort_lines_reading_order(output_lines)

import logging
from typing import Optional
from .base import BaseOCREngine
from .easyocr_engine import EasyOCREngine
from app.config import get_settings

logger = logging.getLogger(__name__)

_active_engine: Optional[BaseOCREngine] = None


def get_ocr_engine(engine_name: Optional[str] = None) -> BaseOCREngine:
    """
    Factory to retrieve or initialize the configured OCR engine.
    """
    global _active_engine
    if _active_engine is not None and engine_name is None:
        return _active_engine

    settings = get_settings()
    target = (engine_name or getattr(settings, "ocr_engine", "auto")).lower()

    if target == "paddleocr":
        try:
            from .paddleocr_engine import PaddleOCREngine
            _active_engine = PaddleOCREngine()
            return _active_engine
        except Exception as e:
            logger.warning(f"PaddleOCR unavailable ({e}), defaulting to EasyOCR.")
            _active_engine = EasyOCREngine()
            return _active_engine
    else:
        # Default or "easyocr" or "auto"
        _active_engine = EasyOCREngine()
        return _active_engine


__all__ = [
    "BaseOCREngine",
    "EasyOCREngine",
    "get_ocr_engine",
]

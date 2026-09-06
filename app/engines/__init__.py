import logging
from typing import Optional
from .base import BaseOCREngine
from app.config import get_settings

logger = logging.getLogger(__name__)

_active_engine: Optional[BaseOCREngine] = None


class OCREngineUnavailableError(RuntimeError):
    """
    Raised when no OCR engine (EasyOCR or PaddleOCR) can be initialized.
    This is a hard failure — the caller must surface it as OCR_ENGINE_UNAVAILABLE,
    not treat it as 'no text on the document'.
    """
    pass


def get_ocr_engine(engine_name: Optional[str] = None) -> BaseOCREngine:
    """
    Factory to retrieve or initialize the configured OCR engine.

    Priority:
    1. Explicit engine_name argument (or settings.ocr_engine)
    2. EasyOCR (default)
    3. PaddleOCR (automatic fallback if EasyOCR fails to init)

    On total failure: raises OCREngineUnavailableError and logs at CRITICAL level.
    This ensures the caller receives a distinct error — never silently returns
    an unusable engine that produces 0 lines.
    """
    global _active_engine
    if _active_engine is not None and engine_name is None:
        return _active_engine

    settings = get_settings()
    target = (engine_name or getattr(settings, "ocr_engine", "auto")).lower()

    if target == "paddleocr":
        # Explicit PaddleOCR request: try Paddle first, fall back to EasyOCR
        try:
            from .paddleocr_engine import PaddleOCREngine
            _active_engine = PaddleOCREngine()
            logger.info("PaddleOCR engine initialized as primary.")
            return _active_engine
        except (ImportError, ModuleNotFoundError) as e:
            logger.warning(f"PaddleOCR unavailable ({e}), trying EasyOCR fallback.")
        except Exception as e:
            logger.warning(f"PaddleOCR initialization failed ({e}), trying EasyOCR fallback.")

        try:
            from .easyocr_engine import EasyOCREngine
            _active_engine = EasyOCREngine()
            logger.info("EasyOCR initialized as fallback (PaddleOCR unavailable).")
            return _active_engine
        except (ImportError, ModuleNotFoundError) as e:
            logger.critical(
                f"CRITICAL: OCR engine unavailable — both PaddleOCR and EasyOCR failed to load. "
                f"OCR will not function. Install 'easyocr' or 'paddleocr'. Last error: {e}"
            )
            raise OCREngineUnavailableError(
                f"No OCR engine could be initialized. PaddleOCR unavailable and EasyOCR also failed: {e}"
            )
        except Exception as e:
            logger.critical(
                f"CRITICAL: OCR engine unavailable — EasyOCR fallback initialization failed: {e}"
            )
            raise OCREngineUnavailableError(f"No OCR engine could be initialized: {e}")

    else:
        # Default / "easyocr" / "auto": try EasyOCR first, fall back to PaddleOCR
        try:
            from .easyocr_engine import EasyOCREngine
            _active_engine = EasyOCREngine()
            logger.info("EasyOCR engine initialized as primary.")
            return _active_engine
        except (ImportError, ModuleNotFoundError) as e:
            logger.warning(f"EasyOCR unavailable ({e}), trying PaddleOCR fallback.")
        except Exception as e:
            logger.warning(f"EasyOCR initialization failed ({e}), trying PaddleOCR fallback.")

        try:
            from .paddleocr_engine import PaddleOCREngine
            _active_engine = PaddleOCREngine()
            logger.info("PaddleOCR initialized as fallback (EasyOCR unavailable).")
            return _active_engine
        except (ImportError, ModuleNotFoundError) as e:
            logger.critical(
                f"CRITICAL: OCR engine unavailable — both EasyOCR and PaddleOCR failed to load. "
                f"OCR will not function. Install 'easyocr + torch' or 'paddleocr'. Last error: {e}"
            )
            raise OCREngineUnavailableError(
                f"No OCR engine could be initialized. EasyOCR unavailable and PaddleOCR also failed: {e}"
            )
        except Exception as e:
            logger.critical(
                f"CRITICAL: OCR engine unavailable — PaddleOCR fallback initialization failed: {e}"
            )
            raise OCREngineUnavailableError(f"No OCR engine could be initialized: {e}")


__all__ = [
    "BaseOCREngine",
    "OCREngineUnavailableError",
    "get_ocr_engine",
]

import logging
from typing import Any, List, Optional
import numpy as np
from .base import BaseOCREngine
from app.config import get_settings

logger = logging.getLogger(__name__)


def sort_lines_reading_order(lines: List[dict[str, Any]], y_thresh: int = 15) -> List[dict[str, Any]]:
    """
    Sorts OCR lines in natural reading order (top-to-bottom, then left-to-right for lines on same horizontal band).
    """
    if not lines:
        return []

    def get_top_y(item):
        bbox = item.get("bbox", [])
        if bbox and isinstance(bbox[0], (list, tuple)):
            return min(pt[1] for pt in bbox)
        return 0

    def get_left_x(item):
        bbox = item.get("bbox", [])
        if bbox and isinstance(bbox[0], (list, tuple)):
            return min(pt[0] for pt in bbox)
        return 0

    # Sort initially by Y
    sorted_y = sorted(lines, key=get_top_y)

    # Cluster into lines with similar Y
    clustered = []
    current_cluster = []
    current_y = None

    for item in sorted_y:
        y = get_top_y(item)
        if current_y is None:
            current_cluster.append(item)
            current_y = y
        elif abs(y - current_y) <= y_thresh:
            current_cluster.append(item)
        else:
            # Sort current cluster by X
            current_cluster.sort(key=get_left_x)
            clustered.extend(current_cluster)
            current_cluster = [item]
            current_y = y

    if current_cluster:
        current_cluster.sort(key=get_left_x)
        clustered.extend(current_cluster)

    return clustered


class EasyOCREngine(BaseOCREngine):
    """
    EasyOCR Engine (CRAFT detector + ResNet/CRNN recognizer).
    """
    name: str = "easyocr"
    _reader = None

    def __init__(self, languages: Optional[List[str]] = None, gpu: Optional[bool] = None):
        settings = get_settings()
        self.languages = languages or getattr(settings, "ocr_languages", ["en"])
        self.gpu = gpu if gpu is not None else getattr(settings, "ocr_gpu", False)

    def _ensure_reader(self):
        if EasyOCREngine._reader is None:
            logger.info(f"Initializing EasyOCR Reader (languages={self.languages}, gpu={self.gpu})...")
            try:
                import easyocr
                import torch
                use_gpu = self.gpu and torch.cuda.is_available()
                EasyOCREngine._reader = easyocr.Reader(self.languages, gpu=use_gpu)
                logger.info("EasyOCR Reader loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                raise

    def recognize(self, image: np.ndarray) -> List[dict[str, Any]]:
        """
        Runs EasyOCR recognition on RGB image ndarray.
        """
        self._ensure_reader()
        settings = get_settings()
        min_conf = getattr(settings, "min_confidence_threshold", 0.20)

        # EasyOCR accepts numpy array (RGB)
        raw_results = EasyOCREngine._reader.readtext(image)

        output_lines = []
        for bbox, text, confidence in raw_results:
            text_str = str(text).strip()
            conf_val = round(float(confidence), 4)

            if conf_val < min_conf or not text_str:
                continue

            # Convert bbox numpy types to plain python float lists
            clean_bbox = [[round(float(coord), 2) for coord in pt] for pt in bbox]

            output_lines.append({
                "text": text_str,
                "confidence": conf_val,
                "bbox": clean_bbox,
            })

        return sort_lines_reading_order(output_lines)

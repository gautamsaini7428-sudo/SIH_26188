from abc import ABC, abstractmethod
from typing import Any
import numpy as np


class BaseOCREngine(ABC):
    """
    Abstract Base Class for OCR engines.
    """
    name: str = "base"

    @abstractmethod
    def recognize(self, image: np.ndarray) -> list[dict[str, Any]]:
        """
        Runs OCR on a single RGB numpy image.

        Returns:
            list of dicts: [
                {
                    "text": "Extracted line text",
                    "confidence": 0.95,
                    "bbox": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                },
                ...
            ]
        """
        pass

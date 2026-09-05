from .classifier import classify_document
from .generic import (
    extract_generic_fields,
    extract_dates,
    extract_gender,
    extract_key_value_pairs,
    normalize_date,
)

__all__ = [
    "classify_document",
    "extract_generic_fields",
    "extract_dates",
    "extract_gender",
    "extract_key_value_pairs",
    "normalize_date",
]

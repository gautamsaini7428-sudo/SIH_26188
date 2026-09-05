import io
import logging
from typing import List, Union
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def load_image_from_bytes(file_bytes: bytes, filename: str = "") -> List[np.ndarray]:
    """
    Decodes raw bytes into a list of RGB numpy ndarrays (one per page for PDFs, single element list for images).
    """
    is_pdf = False
    if filename.lower().endswith(".pdf") or file_bytes.startswith(b"%PDF"):
        is_pdf = True

    if is_pdf:
        return load_pdf_pages(file_bytes)
    else:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            # Handle orientation from EXIF if present
            try:
                from PIL import ImageOps
                image = ImageOps.exif_transpose(image)
            except Exception:
                pass

            # Convert to RGB (handles RGBA, Palette, Grayscale, etc.)
            if image.mode != "RGB":
                image = image.convert("RGB")
            return [np.array(image)]
        except Exception as e:
            logger.error(f"Failed to decode image from bytes: {e}")
            raise ValueError(f"Invalid image format: {e}")


def load_pdf_pages(pdf_bytes: bytes, dpi: int = 200) -> List[np.ndarray]:
    """
    Renders all pages of a PDF into RGB numpy ndarrays using pypdfium2, with fallback to pypdf / error.
    """
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(pdf_bytes)
        pages = []
        for i in range(len(pdf)):
            page = pdf[i]
            scale = dpi / 72.0
            bitmap = page.render(scale=scale)
            pil_image = bitmap.to_pil()
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")
            pages.append(np.array(pil_image))
        return pages
    except ImportError:
        logger.warning("pypdfium2 is not installed. Trying alternative fallback for PDF.")
        try:
            from PIL import Image
            # Some environments have ghostscript / PIL PDF support
            image = Image.open(io.BytesIO(pdf_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")
            return [np.array(image)]
        except Exception as e:
            raise ValueError("PDF rendering requires pypdfium2: " + str(e))
    except Exception as e:
        logger.error(f"Error reading PDF with pypdfium2: {e}")
        raise ValueError(f"Could not render PDF pages: {e}")

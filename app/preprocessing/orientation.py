import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


def compute_skew_angle(gray_image: np.ndarray) -> float:
    """
    Computes skew angle in degrees using Otsu binarization and minAreaRect on text contours.
    """
    try:
        # Invert so text is white
        thresh = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Morphological dilation to connect text horizontally
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
        dilated = cv2.dilate(thresh, kernel, iterations=2)

        # Find all contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        angles = []
        for c in contours:
            if cv2.contourArea(c) < 100:
                continue
            rect = cv2.minAreaRect(c)
            angle = rect[-1]

            # minAreaRect returns angle in [-90, 0)
            if angle < -45:
                angle = 90 + angle
            elif angle > 45:
                angle = angle - 90

            if abs(angle) > 0.1:
                angles.append(angle)

        if len(angles) > 3:
            median_angle = float(np.median(angles))
            return median_angle
        return 0.0
    except Exception as e:
        logger.debug(f"Deskew calculation error: {e}")
        return 0.0


def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """
    Rotates image by arbitrary angle in degrees around the center, expanding borders so no text is cropped.
    """
    if abs(angle) < 0.2:
        return image

    h, w = image.shape[:2]
    center = (w / 2, h / 2)

    # Compute rotation matrix
    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Compute new bounding dimensions
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))

    # Adjust rotation matrix translation
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]

    # Perform rotation with white background
    rotated = cv2.warpAffine(
        image, M, (new_w, new_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255)
    )
    return rotated


def correct_perspective_if_present(image: np.ndarray) -> np.ndarray:
    """
    Detects if there is a clear document boundary with perspective distortion and warps to rectangular top-down view.
    If no clear document quad is found, returns the original image.
    """
    try:
        h, w = image.shape[:2]
        img_area = h * w
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 200)

        # Dilate edges slightly to close gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edged, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        for c in contours:
            area = cv2.contourArea(c)
            if area < 0.25 * img_area:
                continue
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)

            if len(approx) == 4 and cv2.isContourConvex(approx):
                # Order points: top-left, top-right, bottom-right, bottom-left
                pts = approx.reshape(4, 2)
                rect = np.zeros((4, 2), dtype="float32")

                s = pts.sum(axis=1)
                rect[0] = pts[np.argmin(s)]
                rect[2] = pts[np.argmax(s)]

                diff = np.diff(pts, axis=1)
                rect[1] = pts[np.argmin(diff)]
                rect[3] = pts[np.argmax(diff)]

                (tl, tr, br, bl) = rect

                # Compute width and height of transformed image
                width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
                width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
                max_w = max(int(width_a), int(width_b))

                height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
                height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
                max_h = max(int(height_a), int(height_b))

                if max_w > 100 and max_h > 100:
                    dst = np.array([
                        [0, 0],
                        [max_w - 1, 0],
                        [max_w - 1, max_h - 1],
                        [0, max_h - 1]
                    ], dtype="float32")

                    M = cv2.getPerspectiveTransform(rect, dst)
                    warped = cv2.warpPerspective(image, M, (max_w, max_h), flags=cv2.INTER_CUBIC)
                    return warped
        return image
    except Exception as e:
        logger.debug(f"Perspective correction skipped: {e}")
        return image


def deskew_and_orient(image: np.ndarray) -> np.ndarray:
    """
    Performs perspective rectification and deskewing.
    """
    processed = correct_perspective_if_present(image)
    gray = cv2.cvtColor(processed, cv2.COLOR_RGB2GRAY)
    angle = compute_skew_angle(gray)
    if abs(angle) > 0.5:
        processed = rotate_image(processed, -angle)
    return processed

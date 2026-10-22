"""Image preprocessing pipeline for scanned vintage comics and documents.

Removes yellowed paper backgrounds, paper texture grain, scanning speckles,
halftone print screens, scanner margins, and ink bleeding while preserving line art.
"""

from pathlib import Path
from typing import List, Optional, Tuple, Union
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

from .presets import PresetConfig


def read_image(path: Union[str, Path], grayscale: bool = True) -> np.ndarray:
    """Read an image safely across all platforms (including non-ASCII/Unicode paths)."""
    if cv2 is None:
        raise ImportError("OpenCV is required: pip install opencv-python-headless")

    p = Path(path).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Input image not found: {p}")

    raw_data = np.fromfile(str(p), dtype=np.uint8)
    flag = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
    img = cv2.imdecode(raw_data, flag)
    if img is None:
        raise ValueError(f"Could not decode image file: {p}")
    return img


def write_image(path: Union[str, Path], img: np.ndarray) -> Path:
    """Write an image safely across all platforms (including non-ASCII/Unicode paths)."""
    if cv2 is None:
        raise ImportError("OpenCV is required: pip install opencv-python-headless")

    p = Path(path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    suffix = p.suffix.lower() if p.suffix else ".png"

    success, encoded = cv2.imencode(suffix, img)
    if not success:
        raise ValueError(f"Failed to encode image to {suffix}")

    encoded.tofile(str(p))
    return p


def denoise(img: np.ndarray, h: float = 10.0) -> np.ndarray:
    """Apply Non-Local Means Denoising to eliminate paper grain."""
    if h <= 0:
        return img
    if len(img.shape) == 2:
        return cv2.fastNlMeansDenoising(img, None, h=float(h), templateWindowSize=7, searchWindowSize=21)
    else:
        return cv2.fastNlMeansDenoisingColored(img, None, h=float(h), hColor=float(h), templateWindowSize=7, searchWindowSize=21)


def descreen_halftone(img: np.ndarray, radius: int = 2) -> np.ndarray:
    """Eliminate printing halftone dot screens (半色调网点) common in vintage press prints."""
    if radius <= 0:
        return img
    # Median blur followed by gentle bilateral filtering removes periodic raster dots
    # while preserving strong inked boundaries.
    ksize = radius * 2 + 1
    median = cv2.medianBlur(img, ksize)
    if len(img.shape) == 2:
        return cv2.bilateralFilter(median, d=ksize, sigmaColor=50, sigmaSpace=50)
    return median


def crop_scanner_borders(img: np.ndarray, border_threshold: int = 25, margin: int = 8) -> np.ndarray:
    """Detect and crop away black scanning borders and scanner cover shadows."""
    gray = img if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]

    # Threshold for dark scanner margins
    _, thresh = cv2.threshold(gray, border_threshold, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return img

    # Find the largest bounding box containing the white page content
    largest_cnt = max(contours, key=cv2.contourArea)
    x, y, bw, bh = cv2.boundingRect(largest_cnt)

    # If bounding box is reasonable page size (> 50% of image), crop margins
    if (bw * bh) > (w * h * 0.4):
        x1 = max(0, x - margin)
        y1 = max(0, y - margin)
        x2 = min(w, x + bw + margin)
        y2 = min(h, y + bh + margin)
        return img[y1:y2, x1:x2]

    return img


def split_double_pages(
    img: np.ndarray,
    threshold_ratio: float = 1.25,
    direction: str = "ltr",
) -> List[np.ndarray]:
    """Detect wide 2-page scans (double-spread) and split into single pages at the center gutter."""
    h, w = img.shape[:2]
    aspect_ratio = w / float(h)

    if aspect_ratio < threshold_ratio:
        # Standard single page
        return [img]

    # Analyze vertical gutter valley in the center 20% zone
    mid_start = int(w * 0.40)
    mid_end = int(w * 0.60)

    gray = img if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    center_strip = gray[:, mid_start:mid_end]

    # Column-wise average brightness
    col_means = np.mean(center_strip, axis=0)
    # The binding gutter usually has a slight shadow valley or white gap
    split_offset = np.argmin(col_means) if np.min(col_means) < 180 else int((mid_end - mid_start) / 2)
    split_x = mid_start + split_offset

    left_page = img[:, :split_x]
    right_page = img[:, split_x:]

    if direction.lower() == "rtl":
        # Right-to-Left reading (e.g. Traditional Manga)
        return [right_page, left_page]
    else:
        # Left-to-Right reading (e.g. Standard Lianhuanhua / Comics)
        return [left_page, right_page]


def stretch_contrast(img: np.ndarray) -> np.ndarray:
    """Normalize and stretch contrast to separate ink from faded background."""
    if len(img.shape) != 2:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def adaptive_binarize(img: np.ndarray, block_size: int = 31, c: float = 12.0) -> np.ndarray:
    """Adaptive Gaussian thresholding to handle uneven yellowing and lighting across pages."""
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    if block_size % 2 == 0:
        block_size += 1
    block_size = max(3, block_size)

    return cv2.adaptiveThreshold(
        img,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block_size,
        c,
    )


def filter_speckles(binary_img: np.ndarray, min_size: int = 4) -> np.ndarray:
    """Remove small isolated scanning artifacts/dust without eroding real drawing strokes.

    Uses high-speed connected component labeling with area LUT mapping.
    """
    if min_size <= 1:
        return binary_img

    inverted = cv2.bitwise_not(binary_img)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(inverted, connectivity=8)

    # Fast LUT mapping
    areas = stats[:, cv2.CC_STAT_AREA]
    keep_mask = (areas >= min_size).astype(np.uint8) * 255
    keep_mask[0] = 0  # Background label 0 is always 0

    cleaned_inverted = keep_mask[labels]
    return cv2.bitwise_not(cleaned_inverted)


def deskew(img: np.ndarray) -> np.ndarray:
    """Detect skew angle and deskew page content."""
    inverted = cv2.bitwise_not(img if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    coords = np.column_stack(np.where(inverted > 0))
    if len(coords) < 100:
        return img

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    elif angle > 45:
        angle = 90 - angle
    else:
        angle = -angle

    if abs(angle) > 0.3 and abs(angle) < 10.0:
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        m = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            img, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=255
        )
        return rotated
    return img


def clean_image(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    preset: Optional[PresetConfig] = None,
    crop_borders: bool = False,
    descreen: bool = False,
) -> Path:
    """Full preprocessing pipeline for a single comic page."""
    if preset is None:
        from .presets import get_preset
        preset = get_preset("vintage-comic")

    in_p = Path(input_path).resolve()
    if output_path is None:
        out_p = in_p.with_suffix(f".clean_{preset.name}.png")
    else:
        out_p = Path(output_path).resolve()

    is_color = (preset.color_mode == "color")
    img = read_image(in_p, grayscale=not is_color)

    # 1. Scanner border cropping if requested
    if crop_borders:
        img = crop_scanner_borders(img)

    # 2. Halftone descreening if requested
    if descreen:
        img = descreen_halftone(img)

    # 3. Denoise
    if preset.denoise_h > 0:
        img = denoise(img, h=preset.denoise_h)

    # 4. Contrast stretch
    if preset.contrast_stretch and not is_color:
        img = stretch_contrast(img)

    # 5. Binarization
    if not is_color:
        img = adaptive_binarize(img, block_size=preset.adaptive_block_size, c=preset.adaptive_c)
        if preset.despeckle_size > 0:
            img = filter_speckles(img, min_size=preset.despeckle_size)
        if preset.deskew:
            img = deskew(img)

    return write_image(out_p, img)

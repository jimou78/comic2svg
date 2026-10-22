"""Image preprocessing pipeline for scanned vintage comics and documents.

Removes yellowed paper backgrounds, paper texture grain, scanning speckles,
and ink bleeding while preserving line art integrity.
"""

from pathlib import Path
from typing import Optional, Union
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None  # Handled gracefully if loaded in test environment without binary cv2

from .presets import PresetConfig


def read_image(path: Union[str, Path], grayscale: bool = True) -> np.ndarray:
    """Read an image safely across all platforms (including non-ASCII/Unicode paths)."""
    if cv2 is None:
        raise ImportError("OpenCV is required for image preprocessing: pip install opencv-python-headless")
    
    p = Path(path).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Input image not found: {p}")

    # Use fromfile to safely read paths with Chinese or special Unicode characters
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
    
    # Block size must be an odd number greater than 1
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
    
    binary_img: Expects white background (255) and black ink (0).
    """
    if min_size <= 1:
        return binary_img
    
    # Invert image so ink strokes are foreground (255)
    inverted = cv2.bitwise_not(binary_img)
    
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(inverted, connectivity=8)
    
    # Filter out components with bounding area or pixel area smaller than threshold
    cleaned_inverted = np.zeros_like(inverted)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_size:
            cleaned_inverted[labels == i] = 255
            
    # Invert back to white background and black ink
    return cv2.bitwise_not(cleaned_inverted)


def deskew(img: np.ndarray) -> np.ndarray:
    """Detect skew angle and deskew page content."""
    # Find contours or lines to compute angle
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

    # Only rotate if skew is noticeable and minor (within 10 degrees)
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
) -> Path:
    """Full preprocessing pipeline for a single comic page.
    
    Reads input image, applies denoising, background normalization,
    adaptive binarization, despeckling, and deskewing. Returns path to cleaned image.
    """
    if preset is None:
        from .presets import get_preset
        preset = get_preset("vintage-comic")

    in_p = Path(input_path).resolve()
    if output_path is None:
        out_p = in_p.with_suffix(f".clean_{preset.name}.png")
    else:
        out_p = Path(output_path).resolve()

    # 1. Read input
    is_color = (preset.color_mode == "color")
    img = read_image(in_p, grayscale=not is_color)

    # 2. Denoise
    if preset.denoise_h > 0:
        img = denoise(img, h=preset.denoise_h)

    # 3. Contrast stretch
    if preset.contrast_stretch and not is_color:
        img = stretch_contrast(img)

    # 4. Binarization (if binary mode)
    if not is_color:
        img = adaptive_binarize(img, block_size=preset.adaptive_block_size, c=preset.adaptive_c)
        
        # 5. Despeckle
        if preset.despeckle_size > 0:
            img = filter_speckles(img, min_size=preset.despeckle_size)

        # 6. Deskew
        if preset.deskew:
            img = deskew(img)

    # 7. Write output
    return write_image(out_p, img)

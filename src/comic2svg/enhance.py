"""High-definition enhancement and line restoration engine for comic2svg.

Transforms degraded, low-resolution, or yellowed scanned pages into
super-resolution, razor-sharp, noise-free HD line art.
"""

from pathlib import Path
from typing import Optional, Union
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

from .preprocess import denoise, read_image, write_image


def flat_field_correction(img: np.ndarray, blur_radius: int = 51) -> np.ndarray:
    """Normalize uneven paper lighting, yellowing, and scanner shadow gradients.

    Estimates the background illumination plane using a large Gaussian blur,
    and normalizes the foreground against it.
    """
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    if blur_radius % 2 == 0:
        blur_radius += 1

    background = cv2.GaussianBlur(gray, (blur_radius, blur_radius), 0)

    norm = np.clip(
        (gray.astype(np.float32) / (background.astype(np.float32) + 1e-5)) * 255.0,
        0,
        255,
    ).astype(np.uint8)

    return norm


def upscale_image(
    img: np.ndarray,
    scale: float = 2.0,
) -> np.ndarray:
    """Perform high-fidelity super-resolution upscaling using Lanczos-4 interpolation."""
    if scale <= 1.0:
        return img

    h, w = img.shape[:2]
    new_w = int(w * scale)
    new_h = int(h * scale)

    return cv2.resize(
        img,
        (new_w, new_h),
        interpolation=cv2.INTER_LANCZOS4,
    )


def unsharp_mask(
    img: np.ndarray,
    sigma: float = 1.2,
    strength: float = 1.5,
    threshold: int = 3,
) -> np.ndarray:
    """Sharpen faded, blurry ink edges without amplifying grain."""
    blurred = cv2.GaussianBlur(img, (0, 0), sigma)
    diff = cv2.subtract(img, blurred)
    low_contrast_mask = np.abs(diff) < threshold
    sharpened = cv2.addWeighted(img, 1.0 + strength, blurred, -strength, 0)
    sharpened[low_contrast_mask] = img[low_contrast_mask]
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def reconnect_broken_strokes(img: np.ndarray, kernel_size: int = 2) -> np.ndarray:
    """Connect microscopic gaps in fragile or faded strokes caused by paper aging."""
    inverted = cv2.bitwise_not(img)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    closed = cv2.morphologyEx(inverted, cv2.MORPH_CLOSE, kernel)
    return cv2.bitwise_not(closed)


def enhance_to_hd(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    scale: float = 2.0,
    sharpen: bool = True,
    flat_field: bool = True,
    reconnect: bool = True,
    denoise_strength: float = 8.0,
    fast: bool = False,
    binarize: bool = False,
) -> Path:
    """Full High-Definition (HD) enhancement pipeline for a single page image.

    Key Performance Optimization: Denoising and flat-field illumination correction
    are performed on the original resolution BEFORE upscaling, saving 4x-16x compute!
    """
    if cv2 is None:
        raise ImportError(
            "OpenCV is required for HD enhancement: pip install opencv-python-headless"
        )

    in_p = Path(input_path).resolve()
    if output_path is None:
        out_p = in_p.with_suffix(f".hd_{int(scale)}x.png")
    else:
        out_p = Path(output_path).resolve()

    img = read_image(in_p, grayscale=True)

    # 1. Background flat-field illumination normalization (on native resolution)
    if flat_field:
        img = flat_field_correction(img, blur_radius=51)

    # 2. Denoising on native resolution BEFORE upscaling (saves 4x-16x compute!)
    if denoise_strength > 0:
        img = denoise(img, h=denoise_strength, fast=fast, search_window=11)

    # 3. Broken stroke reconnection
    if reconnect:
        img = reconnect_broken_strokes(img, kernel_size=2)

    # 4. Super-resolution upscaling (Lanczos-4)
    if scale > 1.0:
        img = upscale_image(img, scale=scale)

    # 5. Line edge sharpening (on HD scale)
    if sharpen:
        img = unsharp_mask(img, sigma=1.2, strength=1.6)

    # 6. Optional final binarization or contrast enhancement
    if binarize:
        img = cv2.adaptiveThreshold(
            img,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            35,
            12.0,
        )
    else:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img = clahe.apply(img)

    return write_image(out_p, img)

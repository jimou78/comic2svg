import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

from comic2svg.enhance import (
    flat_field_correction,
    reconnect_broken_strokes,
    unsharp_mask,
    upscale_image,
)


def test_upscale_image():
    if cv2 is None:
        return
    img = np.zeros((50, 50), dtype=np.uint8)
    img[20:30, 20:30] = 255
    upscaled = upscale_image(img, scale=2.0)
    assert upscaled.shape == (100, 100)


def test_unsharp_mask():
    if cv2 is None:
        return
    img = np.full((40, 40), 128, dtype=np.uint8)
    sharpened = unsharp_mask(img, sigma=1.0, strength=1.5)
    assert sharpened.shape == img.shape


def test_reconnect_broken_strokes():
    if cv2 is None:
        return
    # White background (255) with broken black line
    img = np.full((30, 30), 255, dtype=np.uint8)
    img[15, 5:14] = 0
    # gap at x=14
    img[15, 15:25] = 0
    reconnected = reconnect_broken_strokes(img, kernel_size=3)
    assert reconnected.shape == img.shape


def test_flat_field_correction():
    if cv2 is None:
        return
    # Gradient background
    grad = np.tile(np.linspace(150, 255, 60, dtype=np.uint8), (60, 1))
    corrected = flat_field_correction(grad, blur_radius=31)
    assert corrected.shape == grad.shape

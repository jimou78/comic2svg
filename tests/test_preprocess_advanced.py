import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

from comic2svg.preprocess import (
    crop_scanner_borders,
    descreen_halftone,
    filter_speckles,
    split_double_pages,
)


def test_split_double_pages():
    if cv2 is None:
        return
    # Wide landscape image (100h x 200w, ratio = 2.0)
    wide_img = np.full((100, 200), 255, dtype=np.uint8)
    # Add vertical gutter line in the middle
    wide_img[:, 98:102] = 50

    pages = split_double_pages(wide_img, threshold_ratio=1.25, direction="ltr")
    assert len(pages) == 2
    assert pages[0].shape[1] > 0
    assert pages[1].shape[1] > 0


def test_split_double_pages_single():
    if cv2 is None:
        return
    # Portrait image (200h x 100w, ratio = 0.5)
    portrait_img = np.full((200, 100), 255, dtype=np.uint8)
    pages = split_double_pages(portrait_img, threshold_ratio=1.25)
    assert len(pages) == 1


def test_crop_scanner_borders():
    if cv2 is None:
        return
    # 200x200 image with black outer border (0) and white content inside (255)
    img = np.zeros((200, 200), dtype=np.uint8)
    img[20:180, 20:180] = 255

    cropped = crop_scanner_borders(img, border_threshold=30, margin=2)
    assert cropped.shape[0] < 200
    assert cropped.shape[1] < 200


def test_filter_speckles_lut():
    if cv2 is None:
        return
    # White background (255) with 1 tiny noise pixel and 1 large line stroke
    img = np.full((50, 50), 255, dtype=np.uint8)
    img[10, 10] = 0  # 1px speckle
    img[20:40, 20:40] = 0  # large stroke

    cleaned = filter_speckles(img, min_size=4)
    # The tiny speckle at (10, 10) should be removed (back to 255)
    assert cleaned[10, 10] == 255
    # The large stroke should remain 0
    assert cleaned[25, 25] == 0


def test_descreen_halftone():
    if cv2 is None:
        return
    # Image with high frequency alternating halftone dot pattern
    img = np.full((60, 60), 200, dtype=np.uint8)
    img[::2, ::2] = 50
    descreened = descreen_halftone(img, radius=2)
    assert descreened.shape == img.shape
    # Variance should decrease due to smoothing of halftone dots
    assert np.std(descreened) < np.std(img)

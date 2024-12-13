import numpy as np


def equal_with_eps(x: int, y: int, eps: int = 10) -> bool:
    return y + eps >= x >= y - eps


def get_highest_pixel_frequency(image: np.ndarray) -> int:
    unique, counts = np.unique(image.reshape(-1, 1), axis=0, return_counts=True)
    if len(counts) == 0:
        return np.uint8(255)
    color = unique[np.argmax(counts)][0]
    if color == 0:
        color = np.uint8(255)

    return color


def similarity(s1: str, s2: str) -> float:
    """string similarity"""
    import difflib

    normalized1 = s1.lower()
    normalized2 = s2.lower()
    matcher = difflib.SequenceMatcher(None, normalized1, normalized2)
    return matcher.ratio()

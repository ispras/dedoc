import difflib
import numpy as np

from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_utils import get_text_from_table_cell


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


def get_cell_text_by_ocr(img_cell: np.ndarray, language: str) -> str:
    if img_cell.shape[0] == 0 or img_cell.shape[1] == 0:
        return ""

    text = get_text_from_table_cell(img_cell, language=language)

    return text


def similarity(s1: str, s2: str) -> float:
    """string similarity"""
    normalized1 = s1.lower()
    normalized2 = s2.lower()
    matcher = difflib.SequenceMatcher(None, normalized1, normalized2)
    return matcher.ratio()


MINIMAL_CELL_CNT_LINE = 7
MINIMAL_CELL_AVG_LENGTH_LINE = 10


def detect_diff_orient(cell_text: str) -> bool:
    # 1 - разбиваем на строки длины которых состоят хотя бы из одного символа
    parts = cell_text.split('\n')
    parts = [p for p in parts if len(p) > 0]

    # 2 - подсчитываем среднюю длину строк ячейки
    len_parts = [len(p) for p in parts]
    avg_len_part = np.average(len_parts)

    # Эвристика: считаем сто ячейка повернута если у нас большое количество строк и строки короткие
    return len(parts) > MINIMAL_CELL_CNT_LINE and avg_len_part < MINIMAL_CELL_AVG_LENGTH_LINE

import numpy as np
import pytesseract

from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_page.ocr_page import OcrPage


def get_cell_text_by_ocr(img_cell: np.ndarray, language: str) -> str:
    if img_cell.shape[0] == 0 or img_cell.shape[1] == 0:
        return ""

    text = get_text_from_table_cell(img_cell, language=language)

    return text


def get_text_from_table_cell(image: np.ndarray, language: str) -> str:
    config = "--psm 6"
    text = pytesseract.image_to_string(image, lang=language, output_type=pytesseract.Output.DICT, config=config)['text']
    return text


def get_text_with_bbox_from_document_page_one_column(image: np.ndarray, language: str, ocr_conf_thr: float) -> OcrPage:
    """
    Extract text from image with Tesseract OCR.
    :param image: document image (assume that it is black and white text)
    :param language: document language as rus, eng or rus+eng
    :return:
    """
    config = "--psm 4"
    rec_dict = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT, config=config)

    return OcrPage.from_dict(rec_dict, ocr_conf_thr)


def get_text_with_bbox_from_document_page(image: np.ndarray, language: str, ocr_conf_thr: float) -> OcrPage:
    """
    Extract text from image with Tesseract OCR.
    :param image: document image (assume that it is black and white text)
    :param language: document language as rus, eng or rus+eng
    :return:
    """
    config = "--psm 3"
    rec_dict = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT, config=config)

    return OcrPage.from_dict(rec_dict, ocr_conf_thr)


def get_text_with_bbox_from_cells(image: np.ndarray, language: str, ocr_conf_threshold: float) -> OcrPage:
    """
    Extract text from image with Tesseract OCR.
    :param image: document image (assume that it is black and white text)
    :param language: document language as rus, eng or rus+eng
    :return:
    """
    config = "--psm 6"
    rec_dict = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT, config=config)

    return OcrPage.from_dict(rec_dict, ocr_conf_threshold)

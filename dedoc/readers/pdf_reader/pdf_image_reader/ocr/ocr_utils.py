import numpy as np

from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_page.ocr_page import OcrPage

# pytesseract is imported lazily inside the functions below: importing it eagerly pulls in pandas + PIL (~58 MB) at
# module load, which is paid by every worker even though the hybrid engine recognizes text (page and table cells) with
# its own recognizer and never calls Tesseract. Deferring the import keeps those workers ~58 MB leaner. The Tesseract
# engine / non-pipeline paths pay the one-time import on their first OCR call.


def get_text_with_bbox_from_document_page_one_column(image: np.ndarray, language: str, ocr_conf_threshold: float) -> OcrPage:
    """
    Extract text from image with Tesseract OCR.
    :param image: document image (assume that it is black and white text)
    :param language: document language as rus, eng or rus+eng
    :param ocr_conf_threshold: minimal confidence value
    :return:
    """
    import pytesseract
    config = "--psm 4"
    rec_dict = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT, config=config)

    return OcrPage.from_dict(rec_dict, ocr_conf_threshold)


def get_text_with_bbox_from_document_page(image: np.ndarray, language: str, ocr_conf_threshold: float = -1.0) -> OcrPage:
    """
    Extract text from image with Tesseract OCR.
    :param image: document image (assume that it is black and white text)
    :param language: document language as rus, eng or rus+eng
    :param ocr_conf_threshold: minimal confidence value
    :return:
    """
    import pytesseract
    config = "--psm 3"
    rec_dict = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT, config=config)

    return OcrPage.from_dict(rec_dict, ocr_conf_threshold)


def get_text_with_bbox_from_cells(image: np.ndarray, language: str, ocr_conf_threshold: float = -1.0) -> OcrPage:
    """
    Extract text from image with Tesseract OCR.
    :param image: document image (assume that it is black and white text)
    :param language: document language as rus, eng or rus+eng
    :param ocr_conf_threshold: minimal confidence value
    :return:
    """
    import pytesseract
    config = "--psm 6"
    rec_dict = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT, config=config)

    return OcrPage.from_dict(rec_dict, ocr_conf_threshold)

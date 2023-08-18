from typing import Optional

from PIL.Image import Image
from PyPDF2 import PdfFileReader
from pdf2image import convert_from_path


def get_pdf_page_count(path: str) -> Optional[int]:
    try:
        with open(path, "rb") as fl:
            reader = PdfFileReader(fl)
            return reader.getNumPages()
    except Exception:
        return None


def get_page_image(path: str, page_id: int) -> Optional[Image]:
    """
    return image of pdf page, (page_num starts from zero)
    @param path: path to pdf file
    @param page_id: page id starts from zero
    @return: pil image if success None otherwise
    """
    images = convert_from_path(path, first_page=page_id + 1, last_page=page_id + 1)
    return images[0] if len(images) > 0 else None

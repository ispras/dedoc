from typing import Optional, Dict, Any, Tuple

from PIL.Image import Image
from PyPDF2 import PdfFileReader
from pdf2image import convert_from_path


def get_pdf_page_count(path: str) -> Optional[int]:
    try:
        with open(path, 'rb') as fl:
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


def get_page_slice(parameters: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    pages = parameters.get("pages", "")
    if pages is None or pages.strip() == "":
        return None, None
    try:
        first_page, last_page = pages.split(":")
        first_page = None if first_page == "" else int(first_page) - 1
        last_page = None if last_page == "" else int(last_page)
        return first_page, last_page
    except Exception:
        raise ValueError("Bad page limit {}".format(pages))

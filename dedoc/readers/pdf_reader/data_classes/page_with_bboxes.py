from typing import List, Optional

import numpy as np

from dedoc.readers.pdf_reader.data_classes.pdf_image_attachment import PdfImageAttachment
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox


class PageWithBBox:

    def __init__(self, image: np.ndarray, bboxes: List[TextWithBBox], page_num: int, attachments: List[PdfImageAttachment] = None,
                 pdf_page_width: Optional[int] = None, pdf_page_height: Optional[int] = None) -> None:
        self.image = image
        self.bboxes = bboxes
        self.page_num = page_num
        self.attachments = [] if attachments is None else attachments
        self.pdf_page_width = pdf_page_width
        self.pdf_page_height = pdf_page_height

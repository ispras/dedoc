from typing import List
import numpy as np

from dedoc.readers.pdf_reader.data_classes.pdf_image_attachment import PdfImageAttachment
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox


class PageWithBBox:

    def __init__(self,
                 image: np.ndarray,
                 bboxes: List[TextWithBBox],
                 page_num: int,
                 attachments: List[PdfImageAttachment] = None) -> None:
        self.image = image
        self.bboxes = bboxes
        self.page_num = page_num
        self.attachments = [] if attachments is None else attachments

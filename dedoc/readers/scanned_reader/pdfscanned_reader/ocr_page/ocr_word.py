from dedoc.data_structures.bbox import BBox


class OcrWord:
    level = 5

    def __init__(self, text: str, bbox: BBox, order: int) -> None:
        """
        Single word from ocr.
        :param text: extracted text
        :param bbox: word coordinates
        :param order: word order in line
        """
        super().__init__()
        self.text = text.replace("—", " ")
        self.bbox = bbox
        self.order = order

from pathlib import Path
from typing import Optional

from dedoc.readers.pdf_reader.data_classes.page_with_bboxes import PageWithBBox
from dedoc.readers.pdf_reader.pdf_base_reader import ParametersForParseDoc
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_broken_encoding.pdf_layout_corrector import PDFLayoutCorrector
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdfminer_reader.pdfminer_extractor import PdfminerExtractor


class BrokenEncodingExtractor(PdfminerExtractor):

    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)
        self.layout_corrector = PDFLayoutCorrector()
        self.cache = {}

    def extract_text_layer(self, path: str, page_number: int, parameters: ParametersForParseDoc) -> Optional[PageWithBBox]:
        if path in self.cache:  # TODO think how to do it more properly
            pages, layouts = self.cache[path]
        else:
            pages, layouts = self.layout_corrector.get_correct_layout(Path(path))
            self.cache = {path: (pages, layouts)}

        for page_num, (page, layout) in enumerate(zip(pages, layouts)):
            if page_num != page_number:
                continue
            return self._handle_page(page=page, page_number=page_number, path=path, parameters=parameters, layout=layout)

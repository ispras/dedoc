import logging
from collections import namedtuple
from copy import deepcopy
from typing import List

from dedoc.data_structures import LineWithMeta
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_tabby_reader import PdfTabbyReader
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier import TxtlayerClassifier
from dedoc.utils.pdf_utils import get_pdf_page_count

PdfTxtlayerParameters = namedtuple("PdfTxtlayerParameters", ["is_correct_text_layer", "is_first_page_correct"])


class TxtLayerDetector:

    def __init__(self, pdf_txtlayer_reader: PdfTxtlayerReader, pdf_tabby_reader: PdfTabbyReader, *, config: dict) -> None:
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

        self.txtlayer_classifier = TxtlayerClassifier(config=config)
        self.pdf_txtlayer_reader = pdf_txtlayer_reader
        self.pdf_tabby_reader = pdf_tabby_reader

    def detect_txtlayer(self, path: str, parameters: dict) -> PdfTxtlayerParameters:
        """
        Detect if the PDF document has a textual layer.

        :param path: path to the PDF file
        :param parameters: parameters for the txtlayer classifier
        :return: information about a textual layer in the PDF document
        """
        try:
            lines = self.__get_lines_for_predict(path=path, parameters=parameters)
            is_correct = self.txtlayer_classifier.predict(lines)
            first_page_correct = self.__is_first_page_correct(lines=lines, is_txt_layer_correct=is_correct)
            return PdfTxtlayerParameters(is_correct_text_layer=is_correct, is_first_page_correct=first_page_correct)

        except Exception as e:
            self.logger.debug(f"Error occurred white detecting PDF textual layer ({e})")
            return PdfTxtlayerParameters(is_correct_text_layer=False, is_first_page_correct=False)

    def __get_lines_for_predict(self, path: str, parameters: dict) -> List[LineWithMeta]:
        parameters_copy = deepcopy(parameters)
        parameters_copy["pages"] = "1:8"  # two batches for pdf_txtlayer_reader
        parameters_copy["need_pdf_table_analysis"] = "false"
        num_pages = get_pdf_page_count(path)
        if num_pages is None or num_pages >= 50:
            # TODO remove this when TLDR-404 is done
            document = self.pdf_txtlayer_reader.read(path, parameters=parameters_copy)
        else:
            # tabby reader reads the whole document regardless "pages" parameter
            # still it's faster to use tabby for documents with <= 50 pages
            document = self.pdf_tabby_reader.read(path, parameters=parameters_copy)

        return document.lines

    def __is_first_page_correct(self, lines: List[LineWithMeta], is_txt_layer_correct: bool) -> bool:
        if not is_txt_layer_correct:
            return False

        first_page_lines = [line for line in lines if line.metadata.page_id == 0]
        return self.txtlayer_classifier.predict(first_page_lines)

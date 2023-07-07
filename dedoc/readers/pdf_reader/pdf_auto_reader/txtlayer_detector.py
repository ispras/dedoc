import logging
from collections import namedtuple
from typing import List

import numpy as np
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError

from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier import TxtlayerClassifier
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_utils import get_text_with_bbox_from_document_page
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.extractor_pdf_textlayer import ExtractorPdfTextLayer
from dedoc.utils.parameter_utils import get_param_language
from dedoc.utils.pdf_utils import get_pdf_page_count
from dedoc.utils.utils import similarity_levenshtein

PdfTxtlayerParameters = namedtuple("PdfTxtlayerParameters", ["is_correct_text_layer", "is_first_page_correct"])
PdfPageWithParameters = namedtuple('PdfPageWithParameters', ['page_num_with_max_text_size', 'has_text', 'text_with_bboxes'])


class TxtLayerDetector:

    def __init__(self, *, config: dict) -> None:
        self.config = config
        self.logger = config.get("logger", logging.getLogger())
        self.check_page_num = 5
        self.txtlayer_classifier = TxtlayerClassifier(config=config)
        self.pdf_txtlayer_extractor = ExtractorPdfTextLayer(config=config)
        self.logger = config.get("logger", logging.getLogger())

    def detect_txtlayer(self, path: str, parameters: dict) -> PdfTxtlayerParameters:
        """
        Detect if the PDF document has a textual layer.

        :param path: path to the PDF file
        :param parameters: parameters for the txtlayer classifier
        :return: information about a textual layer in the PDF document
        """

        is_one_column_list = parameters.get("is_one_column_document_list", [])
        try:
            page_with_longest_text = self.__get_page_with_longest_text(
                path=path,
                is_one_column_list=is_one_column_list,
                page_count=get_pdf_page_count(path)
            )

            if page_with_longest_text.has_text:
                return self.__detect_text_layer(
                    path=path,
                    pdf_page_text_layer_param=page_with_longest_text,
                    is_one_column_list=is_one_column_list,
                    lang=get_param_language(parameters)
                )
            else:
                self.logger.debug("The longest page doesn't have any text")
                return PdfTxtlayerParameters(is_correct_text_layer=False, is_first_page_correct=False)

        except PDFPageCountError:
            self.logger.debug("PDFPageCountError occured")
            return PdfTxtlayerParameters(is_correct_text_layer=False, is_first_page_correct=False)

    def __get_page_with_longest_text(self, path: str, is_one_column_list: List[bool], page_count: int) -> PdfPageWithParameters:
        max_text_with_bboxes: List[TextWithBBox] = []
        page_count = self.check_page_num if page_count >= self.check_page_num else page_count
        page_with_max_count_symbol, max_symbol_count = 0, 0

        try:
            for page_num in range(page_count):
                try:
                    txtlayer_bboxes = self.__extract_text_by_txtlayer_extractor(path=path,
                                                                                page_number=page_num,
                                                                                is_one_column_document=is_one_column_list[page_num])

                    symbol_count = sum([len(pdf_line.text) for pdf_line in txtlayer_bboxes])
                    if max_symbol_count < symbol_count:
                        max_symbol_count, page_with_max_count_symbol, max_text_with_bboxes = symbol_count, page_num, txtlayer_bboxes

                except Exception as exception:
                    self.logger.info(f"Can't get text from {path}, get error {exception}. Seems that text layer is broken")
                    if self.config.get("debug_mode", False):
                        raise exception

            has_text = max_symbol_count != 0
            return PdfPageWithParameters(page_with_max_count_symbol, has_text, max_text_with_bboxes)

        except PDFPageCountError:
            self.logger.debug("PDFPageCountError occured")
            return PdfPageWithParameters(0, False, max_text_with_bboxes)

    def __extract_text_by_ocr(self, image: np.ndarray, lang: str, page_num: int) -> List[TextWithBBox]:
        """
        Extract text from the first page by ocr-tools
        :param image: image of the first page of PDF
        :param lang: language of the text
        :return: extracted text-lines with bboxes
        """
        ocr_text_bboxes = []
        ocr_page = get_text_with_bbox_from_document_page(image, language=lang, ocr_conf_thr=self.config.get("ocr_conf_threshold", -1))
        for line_num, line in enumerate(ocr_page.lines):
            ocr_text_bboxes.append(TextWithBBox(bbox=line.bbox, text=line.text, page_num=page_num, line_num=line_num))

        return ocr_text_bboxes

    def __extract_text_by_txtlayer_extractor(self,
                                             path: str,
                                             page_number: int = 0,
                                             is_one_column_document: bool = False) -> List[TextWithBBox]:
        """
        Extract text from the first page by txtlayer extractor
        :param path: path to PDF
        :return: extracted text-lines with bboxes
        """
        page = self.pdf_txtlayer_extractor.extract_text_layer(path=path,
                                                              page_number=page_number,
                                                              is_one_column_document=is_one_column_document)
        return page.bboxes

    def __detect_text_layer(self,
                            path: str,
                            pdf_page_text_layer_param: PdfPageWithParameters,
                            is_one_column_list: List[bool],
                            lang: str) -> PdfTxtlayerParameters:

        txtlayer_correct_predicted = self.txtlayer_classifier.predict(pdf_page_text_layer_param.text_with_bboxes)

        if txtlayer_correct_predicted:
            txtlayer_correct = self.__is_similar_to_ocr(path=path,
                                                        lang=lang,
                                                        page_number=pdf_page_text_layer_param.page_num_with_max_text_size,
                                                        text_with_bboxes=pdf_page_text_layer_param.text_with_bboxes)
            message = "Assume document has a correct textual layer" if txtlayer_correct else "Assume document has incorrect textual layer"
        else:
            message = "Assume document has incorrect predicted textual layer"
            txtlayer_correct = False

        self.logger.debug(message)

        first_page_correct = self.__is_first_page_correct(path=path, is_one_column=is_one_column_list[0], is_txt_layer_correct=txtlayer_correct)
        return PdfTxtlayerParameters(is_correct_text_layer=txtlayer_correct, is_first_page_correct=first_page_correct)

    def __is_similar_to_ocr(self, path: str, lang: str, page_number: int, text_with_bboxes: List[TextWithBBox]) -> bool:
        image = convert_from_path(path, first_page=page_number + 1, last_page=page_number + 1)[0]
        image = np.array(image)
        ocr_bboxes = self.__extract_text_by_ocr(image=image, lang=lang, page_num=page_number)
        mean_similarity = self.__ocr_and_txtlayer_similarity(text_with_bboxes, ocr_bboxes)

        threshold_similarity = self.config.get("threshold_similarity", 0.5)
        is_txt_layer_correct = mean_similarity > threshold_similarity
        return is_txt_layer_correct

    def __ocr_and_txtlayer_similarity(self, txtlayer_bboxes: List[TextWithBBox], ocr_bboxes: List[TextWithBBox]) -> float:
        """
        :param txtlayer_bboxes: text from text-layer of pdf
        :param ocr_bboxes: recognized text with help ocr
        :return: average similarity of Layer texts and recognized texts
        """
        text_layer = "".join([pdf_line.text for pdf_line in txtlayer_bboxes])
        text_ocr = "".join([ocr_word.text for ocr_word in ocr_bboxes])
        similarity = similarity_levenshtein(text_layer, text_ocr)

        if self.config.get("debug_mode", False):
            self.logger.debug(f"AVG SIMILARITY = {similarity}")
        return similarity

    def __is_first_page_correct(self, path: str, is_one_column: bool, is_txt_layer_correct: bool) -> bool:
        """
        Checks emptiness of the result extracted by pdf_txtlayer_extractor
        """
        if not is_txt_layer_correct:
            return False

        lines = self.__extract_text_by_txtlayer_extractor(path=path, page_number=0, is_one_column_document=is_one_column)
        bboxes_first_page = [line for line in lines if len(line.text.strip()) > 0]
        return len(bboxes_first_page) > 0

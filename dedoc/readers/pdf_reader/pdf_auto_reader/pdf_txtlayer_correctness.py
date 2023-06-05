import logging
from collections import namedtuple
from typing import List
import cv2
import numpy as np
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError

import dedoc.utils.parameter_utils as param_utils
from dedoc.readers.pdf_reader.pdf_auto_reader.catboost_model_extractor import CatboostModelExtractor
from dedoc.readers.pdf_reader.pdf_auto_reader.pdf_txtlayer_parameters import PdfTxtlayerParameters
from dedoc.readers.pdf_reader.data_classes.text_with_bbox import TextWithBBox
from dedoc.readers.pdf_reader.pdf_image_reader.ocr.ocr_utils import get_text_with_bbox_from_document_page
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.extractor_pdf_textlayer import ExtractorPdfTextLayer
from dedoc.utils.pdf_utils import get_pdf_page_count
from dedoc.utils.utils import similarity_levenshtein


class PdfTextLayerCorrectness:

    def __init__(self, *, config: dict) -> None:
        self.config = config
        self.logger = config.get("logger", logging.getLogger())
        self.check_page_num = 5
        self.pdf_page_text_layer_param = namedtuple('Param', 'page_num_with_max_text_size have_text text_layer_bboxes')
        self.catboost_model_extractor = CatboostModelExtractor(config=config)
        self.logger = config.get("logger", logging.getLogger())

    def with_text_layer(self, path: str, parameters: dict, is_one_column_list: List[bool]) -> PdfTxtlayerParameters:
        """
         Have PDF text layer or not? Also, classify documents onto booklets or not booklets
         :param path: path to PDF file
         :param parameters: parameters for classifier
         :return: PdfParameter information about PDF text layer and if the document is a booklet
         """
        threshold_similarity = self.config.get("threshold_similarity", 0.5)
        # get the first image from PDF
        try:
            page_count = get_pdf_page_count(path)
            image, page_number, page_count = self._get_image_from_first_page(path=path, page_count=page_count)
            is_booklet = self.__is_booklet(image)
            lang = param_utils.get_param_language(parameters)
            pdf_page_text_layer_param = \
                self._get_page_num_and_have_text_flag_from_text_layer(path=path,
                                                                      is_one_column_list=is_one_column_list,
                                                                      page_count=page_count)
            if pdf_page_text_layer_param.have_text:
                return self._detect_text_layer(path=path,
                                               pdf_page_text_layer_param=pdf_page_text_layer_param,
                                               is_one_column_list=is_one_column_list,
                                               is_booklet=is_booklet, lang=lang,
                                               threshold_similarity=threshold_similarity)
            else:
                return PdfTxtlayerParameters(False, False, is_booklet)
        except PDFPageCountError:
            return PdfTxtlayerParameters(False, False, False)

    @staticmethod
    def __is_booklet(image: np.ndarray) -> bool:
        """
        The booklet is a colorful document with complex background. Booklet required special handling, so we have to
        classify each document like a booklet or not.
        :param image: Image of the document page in RGB format.
        :return: True if the document is a booklet, False otherwise.
        """
        # convert image from RGB to HSV (https://en.wikipedia.org/wiki/HSL_and_HSV)
        # In that space, booklets are well separate from the ordinary documents
        image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        height, width, channels = image.shape
        # Reshape into flat array of points and calculate mean color
        flat_array = image.reshape(height * width, channels)
        hue, saturation, value = flat_array.mean(axis=0)
        return hue > 30 or value < 190 or saturation > 160

    def __extract_text_by_ocr(self, image: np.ndarray, lang: str, page_num: int) -> List[TextWithBBox]:
        """
        recognition text by ocr-tools from the PDF first page
        :param image: image of the first page of PDF
        :param lang: language of text
        :return: extracted text-words with bboxes
        """
        ocr_text_bboxes = []

        output_dict = get_text_with_bbox_from_document_page(image,
                                                            language=lang,
                                                            ocr_conf_thr=self.config.get("ocr_conf_threshold", -1))
        for line_num, line in enumerate(output_dict.lines):
            ocr_text_bboxes.append(TextWithBBox(bbox=line.bbox, text=line.text, page_num=page_num, line_num=line_num))

        return ocr_text_bboxes

    def __mean_similarities_ocr_and_text(self, text_layer_bboxes: List[TextWithBBox],
                                         ocr_bboxes: List[TextWithBBox]) -> float:
        """
        :param text_layer_bboxes: text from text-layer of pdf
        :param ocr_bboxes: recognized text with help ocr
        :return: average similarity of Layer texts and recognized texts
        """
        text_layer = "".join([pdf_line.text for pdf_line in text_layer_bboxes])
        text_ocr = "".join([ocr_word.text for ocr_word in ocr_bboxes])
        similarity = similarity_levenshtein(text_layer, text_ocr)

        if self.config.get("debug_mode", False):
            self.config.get("logger", logging.getLogger()).debug("AVG SIMILARITY = {}".format(similarity))
        return similarity

    def __extract_text_layer_from_pdf(self,
                                      path: str,
                                      page_number: int = 0,
                                      is_one_column_document: bool = False) -> List[TextWithBBox]:
        """
        extraction text-layer from the PDF first page
        :param path: path to PDF
        :return: extracted text-lines with bboxes
        """
        page = ExtractorPdfTextLayer(config=self.config). \
            extract_text_layer(path=path,
                               page_number=page_number,
                               is_one_column_document=is_one_column_document)

        return page.bboxes

    def _get_page_num_and_have_text_flag_from_text_layer(self, path: str, is_one_column_list: List[bool],
                                                         page_count: int) -> namedtuple:
        have_text = True
        max_text_layer_bboxes = List[TextWithBBox]
        try:
            page_count = self.check_page_num if page_count >= self.check_page_num else page_count
            page_with_max_count_symbol = 0
            symbol_count = 0
            max_symbol_count = 0
            for page_num in range(page_count):
                try:
                    text_layer_bboxes = \
                        self.__extract_text_layer_from_pdf(path=path,
                                                           page_number=page_num,
                                                           is_one_column_document=is_one_column_list[page_num])

                    for pdf_line in text_layer_bboxes:
                        symbol_count += len(pdf_line.text)
                    if max_symbol_count < symbol_count:
                        max_symbol_count = symbol_count
                        page_with_max_count_symbol = page_num
                        max_text_layer_bboxes = text_layer_bboxes
                    symbol_count = 0
                except Exception as exception:
                    self.logger.warning("Can't get text from {}, get error {}. Seems that text layer is broken".format(
                        path, exception
                    ))
                    if self.config.get("debug_mode", False):
                        raise exception
            if max_symbol_count == 0:
                have_text = False
            return self.pdf_page_text_layer_param(page_with_max_count_symbol, have_text, max_text_layer_bboxes)
        except PDFPageCountError:
            return self.pdf_page_text_layer_param(0, have_text, max_text_layer_bboxes)

    def _get_image_from_first_page(self, path: str, page_count: int) -> tuple:
        if page_count is None:
            page_count = 0
        page_number = 1 if page_count > 1 else 0
        image = convert_from_path(path, first_page=page_number + 1, last_page=page_number + 1)[0]
        image = np.array(image)
        return image, page_number, page_count

    def _is_txt_layer_correct(self, path: str, lang: str, page_number: int, text_layer_bboxes: List[TextWithBBox],
                              threshold_similarity: float) -> bool:
        image = convert_from_path(path, first_page=page_number + 1, last_page=page_number + 1)[0]
        image = np.array(image)
        ocr_bboxes = self.__extract_text_by_ocr(image=image, lang=lang, page_num=page_number)
        mean_similarity = self.__mean_similarities_ocr_and_text(text_layer_bboxes, ocr_bboxes)
        is_txt_layer_correct = mean_similarity > threshold_similarity
        return is_txt_layer_correct

    def _is_first_page_correct(self, path: str, is_one_column: bool, is_txt_layer_correct: bool) -> bool:
        if is_txt_layer_correct:
            bboxes_first_page = [line for line in
                                 self.__extract_text_layer_from_pdf(path=path,
                                                                    page_number=0,
                                                                    is_one_column_document=is_one_column)
                                 if
                                 len(line.text.strip()) > 0]
            is_first_page_correct = len(bboxes_first_page) > 0
        else:
            is_first_page_correct = False
        return is_first_page_correct

    def _detect_text_layer(self, path: str, pdf_page_text_layer_param: namedtuple, is_one_column_list: List[bool],
                           is_booklet: bool,
                           lang: str, threshold_similarity: float) -> PdfTxtlayerParameters:
        if self.catboost_model_extractor.detect_text_layer_correctness(text_layer_bboxes=pdf_page_text_layer_param.text_layer_bboxes):
            message = "assume document has almost correct text layer"
            self.logger.debug(message)
            is_txt_layer_correct = \
                self._is_txt_layer_correct(path=path,
                                           lang=lang,
                                           page_number=pdf_page_text_layer_param.page_num_with_max_text_size,
                                           text_layer_bboxes=pdf_page_text_layer_param.text_layer_bboxes,
                                           threshold_similarity=threshold_similarity)
            if is_txt_layer_correct:
                message = "assume document has correct text layer"
                self.logger.debug(message)
            else:
                message = "assume document has incorrect text layer"
                self.logger.debug(message)
        else:
            message = "assume document has catboost incorrect text layer"
            self.logger.debug(message)
            is_txt_layer_correct = False
        is_first_page_correct = self._is_first_page_correct(path=path,
                                                            is_one_column=is_one_column_list[0],
                                                            is_txt_layer_correct=is_txt_layer_correct)
        return PdfTxtlayerParameters(is_txt_layer_correct, is_first_page_correct, is_booklet)

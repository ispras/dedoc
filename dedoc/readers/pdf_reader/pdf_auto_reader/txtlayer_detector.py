import logging
import math
from copy import deepcopy
from itertools import chain
from typing import List

import numpy as np

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier.abstract_txtlayer_classifier import AbstractTxtlayerClassifier
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier.ml_txtlayer_classifier import MlTxtlayerClassifier
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier.simple_txtlayer_classifier import SimpleTxtlayerClassifier
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_result import TxtLayerResult
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_tabby_reader import PdfTabbyReader
from dedoc.utils.parameter_utils import get_bool_parameter, get_param_page_slice
from dedoc.utils.pdf_utils import get_pdf_page_count


class TxtLayerDetector:

    def __init__(self, pdf_reader: PdfTabbyReader, *, config: dict) -> None:
        self.config = config
        self.logger = config.get("logger", logging.getLogger())

        self.ml_txtlayer_classifier = MlTxtlayerClassifier(config=config)
        self.simple_txtlayer_classifier = SimpleTxtlayerClassifier(config=config)
        self.pdf_reader = pdf_reader

    def detect_txtlayer(self, path: str, parameters: dict) -> List[TxtLayerResult]:
        """
        Detect if the PDF document has a textual layer.

        :param path: path to the PDF file
        :param parameters: parameters for the txtlayer classifier
        :return: information about a textual layer in the PDF document
        """
        if get_bool_parameter(parameters, "fast_textual_layer_detection", False):
            txtlayer_classifier = self.simple_txtlayer_classifier
        else:
            txtlayer_classifier = self.ml_txtlayer_classifier
        classify_each_page = get_bool_parameter(parameters, "each_page_textual_layer_detection", False)
        detect_function = self.__classify_each_page if classify_each_page else self.__classify_all_pages
        try:
            return detect_function(path, parameters, txtlayer_classifier)
        except Exception as e:
            self.logger.debug(f"Error occurred white detecting PDF textual layer ({e})")
            return [TxtLayerResult(correct=False, start=1, end=None)]

    def __classify_all_pages(self, path: str, parameters: dict, txtlayer_classifier: AbstractTxtlayerClassifier) -> List[TxtLayerResult]:
        """
        Check only first 8 pages of the document, use classification results for the entire document.
        Separately handle the first page (it's common that only first page doesn't have a textual layer).
        """
        start, end = get_param_page_slice(parameters)
        start = 1 if start is None else start + 1

        parameters_copy = deepcopy(parameters)
        parameters_copy["pages"] = "1:8"  # two batches for pdf_txtlayer_reader
        parameters_copy["need_pdf_table_analysis"] = "false"

        document = self.pdf_reader.read(path, parameters=parameters_copy)
        is_correct = txtlayer_classifier.predict([document.lines])[0]
        if not is_correct:
            return [TxtLayerResult(correct=False, start=start, end=end)]

        if start > 1:  # no need to classify correctness of the first page
            return [TxtLayerResult(correct=True, start=start, end=end)]

        first_page_lines = [line for line in document.lines if line.metadata.page_id == 0]
        first_page_correct = txtlayer_classifier.predict([first_page_lines])[0]
        if first_page_correct:
            return [TxtLayerResult(correct=True, start=start, end=end)]
        else:
            return [TxtLayerResult(correct=False, start=start, end=start), TxtLayerResult(correct=True, start=start + 1, end=end)]

    def __classify_each_page(self, path: str, parameters: dict, txtlayer_classifier: AbstractTxtlayerClassifier) -> List[TxtLayerResult]:
        """
        Classify each page of the document correct/not correct textual layer.
        """
        document = self.pdf_reader.read(path, parameters=parameters)
        start, end = get_param_page_slice(parameters)
        start = 1 if start is None else start + 1
        if not document.lines:
            return [TxtLayerResult(correct=False, start=start, end=end)]

        # Prepare lines for prediction - list of pages
        lines = sorted(document.lines, key=lambda l: (l.metadata.page_id, l.metadata.line_id))
        lines_for_predict = []
        fisrt_page_id = start - 1
        last_page_id = lines[-1].metadata.page_id
        current_line_idx = 0

        for page_id in range(fisrt_page_id, last_page_id + 1):
            current_lines = []
            for line_idx, line in enumerate(lines[current_line_idx:]):
                if line.metadata.page_id != page_id:
                    current_line_idx += line_idx
                    break
                current_lines.append(line)
            lines_for_predict.append(current_lines)

        predictions = txtlayer_classifier.predict(lines_for_predict)
        # e.g. predictions = [0, 0, 1, 1, 0, 1, 0, 0, 1], transitions = [2, 4, 5, 6, 8]
        transitions = list(np.where(predictions[:-1] != predictions[1:])[0] + 1)
        transitions.append(len(predictions))
        result: List[TxtLayerResult] = []

        # Split document into chunks with different value of the textual layer correctness
        is_correct = predictions[0]
        prev_idx = 0
        for transition_idx in transitions:
            chunk_lines = list(chain.from_iterable(lines_for_predict[prev_idx:transition_idx]))
            chunk_document = UnstructuredDocument(lines=chunk_lines, tables=document.tables, attachments=document.attachments)
            chunk_result = TxtLayerResult(start=prev_idx + fisrt_page_id + 1, end=transition_idx + fisrt_page_id, correct=is_correct, document=chunk_document)
            result.append(chunk_result)
            is_correct = not is_correct
            prev_idx = transition_idx

        # Handle last pages without textual layer
        page_count = get_pdf_page_count(path)
        end_numeric_value = min(page_count or math.inf, end or math.inf)
        start_value = prev_idx + fisrt_page_id + 1
        end_value = end or page_count
        if end_value is None or start_value <= end_numeric_value:
            if result and not result[-1].correct:
                result[-1].end = end_value
            else:
                result.append(TxtLayerResult(start=start_value, end=end_value, correct=False))

        return result

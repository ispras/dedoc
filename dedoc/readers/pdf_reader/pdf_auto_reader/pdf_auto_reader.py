import copy
import logging
import os
from itertools import chain
from typing import Optional, Tuple, List
import numpy as np

from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.config import get_config
from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_mimes
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_tabby_reader import PdfTabbyReader
from dedoc.utils.parameter_utils import get_param_pdf_with_txt_layer, get_param_page_slice
from dedoc.utils.pdf_utils import get_page_image, get_pdf_page_count
from dedoc.readers.pdf_reader.pdf_image_reader.columns_orientation_classifier.columns_orientation_classifier import ColumnsOrientationClassifier
from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader
from dedoc.readers.pdf_reader.pdf_auto_reader.pdf_txtlayer_correctness import PdfTextLayerCorrectness


# TODO delete parameter is_one_column_document_list
class PdfAutoReader(BaseReader):
    """
    This class allows to extract content from the .pdf documents of any kind.
    PDF documents can have a textual layer (copyable documents) or be without it (images, scanned documents).

    :class:`~dedoc.readers.PdfAutoReader` is used for automatic detection of a correct textual layer in the given PDF file:

    * if PDF document has a correct textual layer then :class:`~dedoc.readers.PdfTxtLayerReader` or :class:`~dedoc.readers.PdfTabbyReader` is used for document content extraction;

    * if PDF document doesn't have a correct textual layer then :class:`~dedoc.readers.PdfImageReader` is used for document content extraction.

    For more information, look to `pdf_with_text_layer` option description in the table :ref:`table_parameters`.
    """

    def __init__(self, *, config: dict) -> None:
        """
        :param config: configuration of the reader, e.g. logger for logging
        """
        self.pdf_parser = PdfTxtlayerReader(config=config)
        self.tabby_parser = PdfTabbyReader(config=config)
        self.pdf_image_reader = PdfImageReader(config=config)
        self.config = config
        self.logger = config.get("logger", logging.getLogger())
        self.__checkpoint_path = get_config()["resources_path"]
        self._orientation_classifier = None
        self.pdf_correctness = PdfTextLayerCorrectness(config=config)

    @property
    def orientation_classifier(self) -> ColumnsOrientationClassifier:
        if self._orientation_classifier is None:
            self._orientation_classifier = ColumnsOrientationClassifier(on_gpu=False,
                                                                        checkpoint_path=self.__checkpoint_path,
                                                                        delete_lines=False,
                                                                        config=self.config)
        return self._orientation_classifier

    def can_read(self, path: str, mime: str, extension: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader (PDF format is supported only).
        This method returns `True` only when the key `pdf_with_text_layer` with value `auto` or `auto_tabby`
        is set in the dictionary `parameters`.

        It is recommended to use `pdf_with_text_layer=auto_tabby` because it's faster and allows to get better results.
        You can look to the table :ref:`table_parameters` to get more information about `parameters` dictionary possible arguments.

        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        parameters = {} if parameters is None else parameters

        is_pdf = mime in recognized_mimes.pdf_like_format
        if not is_pdf:
            return False

        pdf_with_txt_layer = get_param_pdf_with_txt_layer(parameters)
        return is_pdf and pdf_with_txt_layer in ("auto", "auto_tabby")

    def read(self, path: str, document_type: Optional[str] = None, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines, tables and attachments.
        This reader is able to add some additional information to the `tag_hierarchy_level` of :class:`~dedoc.data_structures.LineMetadata`.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        pdf_with_txt_layer = get_param_pdf_with_txt_layer(parameters)
        warnings = []
        is_one_column_document_list = self.__get_one_column_document(parameters, path=path, warnings=warnings)

        parameters_copy = copy.deepcopy(parameters)
        parameters_copy["is_one_column_document_list"] = is_one_column_document_list
        parameters_copy["is_one_column_document"] = "true" if is_one_column_document_list[0] else "false"
        parameters_copy["pdf_with_text_layer"] = str(pdf_with_txt_layer)

        text_layer_parameters = self.pdf_correctness.with_text_layer(path=path,
                                                                     parameters=parameters,
                                                                     is_one_column_list=is_one_column_document_list)

        if text_layer_parameters.is_correct_text_layer:
            result = self._handle_correct_layer(document_type=document_type,
                                                is_first_page_correct=text_layer_parameters.is_first_page_correct,
                                                parameters=parameters_copy,
                                                path=path,
                                                warnings=warnings,
                                                pdf_with_txt_layer=pdf_with_txt_layer)
        else:
            result = self._handle_incorrect_text_layer(document_type, parameters_copy, path, warnings)

        result.warnings.extend(warnings)
        return result

    def _handle_incorrect_text_layer(self, document_type: str, parameters_copy: dict, path: str, warnings: list) -> UnstructuredDocument:
        message = "assume document has incorrect text layer"
        warnings.append(message)
        warnings.append(message + " " + os.path.basename(path))
        self.logger.info(message.format(os.path.basename(path)))
        result = self.pdf_image_reader.read(path=path, document_type=document_type, parameters=parameters_copy)
        return result

    def __preparing_first_page(self, parameters: dict) -> dict:
        first_page, last_page = get_param_page_slice(parameters)
        # calculate indexes for the first page parsing
        first_page_index = 0 if first_page is None else first_page
        last_page_index = 0
        scan_parameters = copy.deepcopy(parameters)
        scan_parameters["pages"] = f"{first_page_index + 1}:{last_page_index + 1}"

        return scan_parameters

    def __preparing_other_pages(self, parameters: dict) -> dict:
        first_page, last_page = get_param_page_slice(parameters)
        first_page_index = 1 if first_page is None else first_page
        last_page_index = "" if last_page is None else last_page - 1
        parameters["pages"] = f"{first_page_index + 1}:{last_page_index + 1}"

        return parameters

    def _handle_correct_layer(self,
                              document_type: str,
                              is_first_page_correct: bool,
                              parameters: dict,
                              path: str,
                              pdf_with_txt_layer: str,
                              warnings: list) -> UnstructuredDocument:
        message = "assume {} has a correct text layer"
        self.logger.info(message.format(os.path.basename(path)))
        warnings.append(message.format("the document"))
        recognized_first_page = None
        if not is_first_page_correct:
            message = "assume the first page hasn't a text layer"
            warnings.append(message)
            self.logger.info(message)
            # GET THE FIRST PAGE: recognize the first page like a scanned page
            scan_parameters = self.__preparing_first_page(parameters)
            recognized_first_page = self.pdf_image_reader.read(path=path, document_type=document_type, parameters=scan_parameters)
            # PREPARE PARAMETERS: from the second page we recognize the content in auto mode
            parameters = self.__preparing_other_pages(parameters)

        reader = self.pdf_parser if pdf_with_txt_layer == "auto" else self.tabby_parser
        result = reader.read(path=path, document_type=document_type, parameters=parameters)
        result = self._merge_documents(recognized_first_page, result) if recognized_first_page is not None else result
        return result

    def _merge_documents(self, first: UnstructuredDocument, second: UnstructuredDocument) -> UnstructuredDocument:
        tables = first.tables
        dropped_tables = set()
        for table in second.tables:
            if table.metadata.page_id != 0:
                tables.append(table)
            else:
                dropped_tables.add(table.metadata.uid)

        lines = []
        line_id = 0
        for line in chain(first.lines, second.lines):
            line.metadata.line_id = line_id
            line_id += 1
            annotations = [annotation for annotation in line.annotations
                           if not (isinstance(annotation, TableAnnotation) and annotation.value in dropped_tables)]
            new_line = LineWithMeta(line=line.line, metadata=line.metadata, annotations=annotations, uid=line.uid)
            lines.append(new_line)
        return UnstructuredDocument(tables=tables,
                                    lines=lines,
                                    attachments=first.attachments + second.attachments,
                                    metadata=second.metadata)

    def __get_one_column_document(self, parameters: Optional[dict], path: str, warnings: list) -> List[bool]:
        if parameters is None:
            parameters = {}

        is_one_column_document = str(parameters.get("is_one_column_document", "auto"))

        page_count = get_pdf_page_count(path)
        if is_one_column_document.lower() != "auto":
            return [is_one_column_document.lower() == "true" for _ in range(page_count)]

        if page_count is None:
            return self._get_page_is_one_columns_list(path=path, start=0, stop=1, warnings=warnings)

        page_check_count = min(3, page_count)  # it's a heuristic. We don't want to check all pages. Only 3 pages maximum.
        is_one_columns_list = self._get_page_is_one_columns_list(path=path, start=0, stop=page_check_count, warnings=warnings)
        if page_count == page_check_count:
            return is_one_columns_list

        # Let's make a guess about other pages based on the previous first three pages
        if is_one_columns_list[1] == is_one_columns_list[2]:
            is_one_columns_list.extend(is_one_columns_list[1] for _ in range(page_count - page_check_count))
            warnings_count = min(5, page_count)  # TODO will think about logging in this case (now log only the first 5 pages)
            for i in range(page_check_count, warnings_count):
                warnings.append(f"assume page {str(i)} has {1 if is_one_columns_list[1] else 2} columns")
        else:
            is_one_columns = self._get_page_is_one_columns_list(path=path, start=page_check_count, stop=page_count, warnings=warnings)
            is_one_columns_list += is_one_columns

        self.logger.info(warnings)
        return is_one_columns_list

    def _get_page_is_one_columns_list(self, path: str, start: int, stop: int, warnings: list) -> List[bool]:
        """
        Function returns predictions of column classificator for each page
        Return: List[bool] - list of prediction. Each element is True - if one text column on the page, False - if the page has multi-columns
        """
        is_one_columns_list = []
        for page_id in range(start, stop):
            try:
                image = get_page_image(path=path, page_id=page_id)
                if image is None:
                    warnings.append(f"fail to read an image from pdf page={page_id}")
                    return [False]
            except Exception as ex:
                self.logger.warning("It seems the input PDF-file is incorrect")
                raise BadFileFormatException(msg=f"It seems the input PDF-file is uncorrected. Exception: {ex}")

            columns, _ = self.orientation_classifier.predict(np.array(image))
            is_one_columns_list.append(columns == 1)
            warnings.append("assume page {} has {} columns".format(page_id, columns))
        return is_one_columns_list

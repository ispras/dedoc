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
from dedoc.utils.parameter_utils import get_param_pdf_with_txt_layer
from dedoc.utils.pdf_utils import get_page_slice, get_page_image, get_pdf_page_count
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

        is_one_column_document_list, warning_list = self.__get_one_column_document(parameters, path=path)
        parameters["is_one_column_document_list"] = is_one_column_document_list
        parameters_copy = copy.deepcopy(parameters)
        parameters_copy["is_one_column_document"] = "true" if is_one_column_document_list[0] else "false"
        for warning in warning_list:
            if warning is not None:
                warnings.append(warning)
        text_layer_parameters = self.pdf_correctness.with_text_layer(path=path,
                                                                     parameters=parameters,
                                                                     is_one_column_list=is_one_column_document_list)
        is_booklet = text_layer_parameters.is_booklet
        pdf_with_text_layer = text_layer_parameters.correct_text_layout
        is_first_page_correct = text_layer_parameters.correct_first_page

        if is_booklet:
            message = "assume document is booklet"
            warnings.append(message)
            self.logger.warning(message + " " + os.path.basename(path))

        if pdf_with_text_layer:
            result = self._handle_correct_layer(document_type=document_type,
                                                is_first_page_correct=is_first_page_correct,
                                                parameters=parameters,
                                                parameters_copy=parameters_copy,
                                                path=path,
                                                warnings=warnings,
                                                pdf_with_txt_layer=pdf_with_txt_layer)
        else:
            result = self._handle_incorrect_text_layer(document_type, parameters_copy, path, warnings)
        parameters_copy["pdf_with_text_layer"] = str(pdf_with_text_layer)

        result.warnings.extend(warnings)
        return result

    def _handle_incorrect_text_layer(self, document_type: str, parameters_copy: dict, path: str, warnings: list) -> UnstructuredDocument:
        message = "assume document has incorrect text layer"
        warnings.append(message)
        warnings.append(message + " " + os.path.basename(path))
        self.logger.info(message.format(os.path.basename(path)))
        result = self.pdf_image_reader.read(path=path, document_type=document_type, parameters=parameters_copy)
        return result

    def _handle_correct_layer(self,
                              document_type: str,
                              is_first_page_correct: bool,
                              parameters: dict,
                              parameters_copy: dict,
                              path: str,
                              pdf_with_txt_layer: str,
                              warnings: list) -> UnstructuredDocument:
        message = "assume {} has correct text layer"
        self.logger.info(message.format(os.path.basename(path)))
        warnings.append(message.format("document"))
        prefix = None
        if not is_first_page_correct:
            message = "assume first page has no text layer"
            warnings.append(message)
            self.logger.info(message)
            first_page, last_page = get_page_slice(parameters_copy)
            first_page = 1 if first_page is None else first_page + 1
            last_page = 1
            scan_parameters = copy.deepcopy(parameters)
            scan_parameters["pages"] = f"{first_page}:{last_page}"
            prefix = self.pdf_image_reader.read(path=path, document_type=document_type, parameters=scan_parameters)
        reader = self.pdf_parser if pdf_with_txt_layer == "auto" else self.tabby_parser
        if not is_first_page_correct:
            first_page, last_page = get_page_slice(parameters_copy)
            first_page = 2 if first_page is None else first_page + 1
            last_page = "" if last_page is None else last_page
            parameters_copy["pages"] = f"{first_page}:{last_page}"
        result = reader.read(path=path, document_type=document_type, parameters=parameters_copy)
        result = self._merge_documents(prefix, result) if prefix is not None else result
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

    def __get_one_column_document(self, parameters: Optional[dict], path: str) -> Tuple[List[bool], List[Optional[str]]]:
        if parameters is None:
            parameters = {}
        is_one_column_document = str(parameters.get("is_one_column_document", "auto"))
        page_count = get_pdf_page_count(path)
        if is_one_column_document.lower() != "auto":
            return [is_one_column_document.lower() == "true" for _ in range(page_count)], [None]

        if page_count is None:
            return self._get_page_is_one_columns_list(path=path, start=0, stop=1)[0], [None]
        page_check_count = min(3, page_count)
        is_one_columns_list, warnings = self._get_page_is_one_columns_list(path=path, start=0, stop=page_check_count)
        if page_count == page_check_count:
            self.logger.info(warnings)
            return is_one_columns_list, warnings

        if is_one_columns_list[1] == is_one_columns_list[2]:
            is_one_columns_list.extend(is_one_columns_list[1] for _ in range(page_count - page_check_count))
            warnings_count = min(5, page_count)
            for i in range(page_check_count, warnings_count):
                warning = warnings[2].replace("page " + str(page_check_count - 1), "page " + str(i))
                warnings.append(warning)
        else:
            is_one_columns, warnings_next = self._get_page_is_one_columns_list(path=path, start=page_check_count,
                                                                               stop=page_count)
            is_one_columns_list += is_one_columns
            warnings += warnings_next[:5]
        self.logger.info(warnings)
        return is_one_columns_list, warnings

    def _get_page_is_one_columns_list(self, path: str, start: int, stop: int) -> Tuple[List[bool], List[Optional[str]]]:
        is_one_columns_list = []
        warnings = []
        for page_id in range(start, stop):
            try:
                image = get_page_image(path=path, page_id=page_id)
                if image is None:
                    return [False], ["fail to read image from pdf"]
            except Exception as ex:
                self.logger.warning("It seems the input PDF-file is uncorrected")
                raise BadFileFormatException(msg=f"It seems the input PDF-file is uncorrected. Exception: {ex}")

            columns, _ = self.orientation_classifier.predict(np.array(image))
            is_one_columns_list.append(columns == 1)
            warnings.append("assume page {} has {} columns".format(page_id, columns))
        return is_one_columns_list, warnings

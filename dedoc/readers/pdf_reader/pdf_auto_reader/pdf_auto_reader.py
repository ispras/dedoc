import copy
import os
from itertools import chain
from typing import Optional

from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_mimes
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_detector import TxtLayerDetector
from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_tabby_reader import PdfTabbyReader
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader
from dedoc.utils.parameter_utils import get_param_page_slice, get_param_pdf_with_txt_layer
from dedoc.utils.utils import get_mime_extension


class PdfAutoReader(BaseReader):
    """
    This class allows to extract content from the .pdf documents of any kind.
    PDF documents can have a textual layer (copyable documents) or be without it (images, scanned documents).

    :class:`~dedoc.readers.PdfAutoReader` is used for automatic detection of a correct textual layer in the given PDF file:

    * if PDF document has a correct textual layer then :class:`~dedoc.readers.PdfTxtLayerReader` or :class:`~dedoc.readers.PdfTabbyReader` is used \
    for document content extraction;

    * if PDF document doesn't have a correct textual layer then :class:`~dedoc.readers.PdfImageReader` is used for document content extraction.

    For more information, look to `pdf_with_text_layer` option description in :ref:`pdf_handling_parameters`.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        self.pdf_txtlayer_reader = PdfTxtlayerReader(config=self.config)
        self.pdf_tabby_reader = PdfTabbyReader(config=self.config)
        self.pdf_image_reader = PdfImageReader(config=self.config)
        self.txtlayer_detector = TxtLayerDetector(pdf_reader=self.pdf_tabby_reader, config=self.config)

    def can_read(self, file_path: Optional[str] = None, mime: Optional[str] = None, extension: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader (PDF format is supported only).
        This method returns `True` only when the key `pdf_with_text_layer` with value `auto` or `auto_tabby`
        is set in the dictionary `parameters`.

        It is recommended to use `pdf_with_text_layer=auto_tabby` because it's faster and allows to get better results.
        You can look to :ref:`pdf_handling_parameters` to get more information about `parameters` dictionary possible arguments.
        """
        extension, mime = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        if not (mime in recognized_mimes.pdf_like_format or extension.lower() == ".pdf"):
            return False

        parameters = {} if parameters is None else parameters
        return get_param_pdf_with_txt_layer(parameters) in ("auto", "auto_tabby")

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines, tables and attachments.
        This reader is able to add some additional information to the `tag_hierarchy_level` of :class:`~dedoc.data_structures.LineMetadata`.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        You can also see :ref:`pdf_handling_parameters` to get more information about `parameters` dictionary possible arguments.
        """
        warnings = []
        txtlayer_parameters = self.txtlayer_detector.detect_txtlayer(path=file_path, parameters=parameters)

        if txtlayer_parameters.is_correct_text_layer:
            result = self.__handle_correct_text_layer(is_first_page_correct=txtlayer_parameters.is_first_page_correct,
                                                      parameters=parameters,
                                                      path=file_path,
                                                      warnings=warnings)
        else:
            result = self.__handle_incorrect_text_layer(parameters, file_path, warnings)

        result.warnings.extend(warnings)
        return result

    def __handle_incorrect_text_layer(self, parameters_copy: dict, path: str, warnings: list) -> UnstructuredDocument:
        self.logger.info(f"Assume document {os.path.basename(path)} has incorrect textual layer")
        warnings.append("Assume document has incorrect textual layer")
        result = self.pdf_image_reader.read(file_path=path, parameters=parameters_copy)
        return result

    def __handle_correct_text_layer(self, is_first_page_correct: bool, parameters: dict, path: str, warnings: list) -> UnstructuredDocument:
        self.logger.info(f"Assume document {os.path.basename(path)} has a correct textual layer")
        warnings.append("Assume document has a correct textual layer")
        recognized_first_page = None

        if not is_first_page_correct:
            message = "Assume the first page hasn't a textual layer"
            warnings.append(message)
            self.logger.info(message)

            # GET THE FIRST PAGE: recognize the first page like a scanned page
            scan_parameters = self.__preparing_first_page_parameters(parameters)
            recognized_first_page = self.pdf_image_reader.read(file_path=path, parameters=scan_parameters)

            # PREPARE PARAMETERS: from the second page we recognize the content like PDF with a textual layer
            parameters = self.__preparing_other_pages_parameters(parameters)

        pdf_with_txt_layer = get_param_pdf_with_txt_layer(parameters)
        reader = self.pdf_txtlayer_reader if pdf_with_txt_layer == "auto" else self.pdf_tabby_reader
        result = reader.read(file_path=path, parameters=parameters)
        result = self.__merge_documents(recognized_first_page, result) if recognized_first_page is not None else result
        return result

    def __preparing_first_page_parameters(self, parameters: dict) -> dict:
        first_page, last_page = get_param_page_slice(parameters)
        # calculate indexes for the first page parsing
        first_page_index = 0 if first_page is None else first_page
        last_page_index = 0
        scan_parameters = copy.deepcopy(parameters)

        # page numeration in parameters starts with 1, both ends are included
        scan_parameters["pages"] = f"{first_page_index + 1}:{last_page_index + 1}"
        # if the first page != 0 then we won't read it (because first_page_index > last_page_index)
        return scan_parameters

    def __preparing_other_pages_parameters(self, parameters: dict) -> dict:
        first_page, last_page = get_param_page_slice(parameters)
        # parameters for reading pages from the second page
        first_page_index = 1 if first_page is None else first_page
        last_page_index = "" if last_page is None else last_page
        parameters["pages"] = f"{first_page_index + 1}:{last_page_index}"

        return parameters

    def __merge_documents(self, first: UnstructuredDocument, second: UnstructuredDocument) -> UnstructuredDocument:
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
            annotations = [
                annotation for annotation in line.annotations if not (isinstance(annotation, TableAnnotation) and annotation.value in dropped_tables)
            ]
            new_line = LineWithMeta(line=line.line, metadata=line.metadata, annotations=annotations, uid=line.uid)
            lines.append(new_line)
        return UnstructuredDocument(tables=tables, lines=lines, attachments=first.attachments + second.attachments, metadata=second.metadata)

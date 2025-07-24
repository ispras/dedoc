from typing import List, Optional, Tuple

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_result import TxtLayerResult


class PdfAutoReader(BaseReader):
    """
    This class allows to extract content from the .pdf documents of any kind.
    PDF documents can have a textual layer (copyable documents) or be without it (images, scanned documents).

    :class:`~dedoc.readers.PdfAutoReader` is used for automatic detection of a correct textual layer in the given PDF file:

    * if PDF document has a correct textual layer then :class:`~dedoc.readers.PdfTxtlayerReader` or :class:`~dedoc.readers.PdfTabbyReader` is used \
    for document content extraction;

    * if PDF document doesn't have a correct textual layer then :class:`~dedoc.readers.PdfImageReader` is used for document content extraction.

    For more information, look to `pdf_with_text_layer` option description in :ref:`pdf_handling_parameters`.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        from dedoc.extensions import recognized_extensions, recognized_mimes
        from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_detector import TxtLayerDetector
        from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader
        from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_tabby_reader import PdfTabbyReader
        from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader

        super().__init__(config=config, recognized_extensions=recognized_extensions.pdf_like_format, recognized_mimes=recognized_mimes.pdf_like_format)

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
        from dedoc.utils.parameter_utils import get_param_pdf_with_txt_layer
        return super().can_read(file_path=file_path, mime=mime, extension=extension) and get_param_pdf_with_txt_layer(parameters) in ("auto", "auto_tabby")

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines, tables and attachments.
        This reader is able to add some additional information to the `tag_hierarchy_level` of :class:`~dedoc.data_structures.LineMetadata`.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        You can also see :ref:`pdf_handling_parameters` to get more information about `parameters` dictionary possible arguments.
        """
        parameters = {} if parameters is None else parameters
        warnings = []
        txtlayer_result = self.txtlayer_detector.detect_txtlayer(path=file_path, parameters=parameters)

        documents = []
        for txtlayer_result_chunk in txtlayer_result:
            document = self.__parse_document(txtlayer_result=txtlayer_result_chunk, parameters=parameters, path=file_path, warnings=warnings)
            documents.append(document)

        result_document = self.__merge_documents(documents)
        result_document.warnings.extend(warnings)
        return result_document

    def __parse_document(self, txtlayer_result: TxtLayerResult, parameters: dict, path: str, warnings: list) -> UnstructuredDocument:
        import os

        end = "" if txtlayer_result.end is None else txtlayer_result.end
        correct_text = "correct" if txtlayer_result.correct else "incorrect"
        log_text = f"Assume document {os.path.basename(path)} has {correct_text} textual layer on pages [{txtlayer_result.start}:{end}]"
        self.logger.info(log_text)
        warnings.append(log_text)
        if txtlayer_result.document:
            return txtlayer_result.document

        import copy
        from dedoc.utils.parameter_utils import get_param_pdf_with_txt_layer

        if txtlayer_result.correct:
            pdf_with_txt_layer = get_param_pdf_with_txt_layer(parameters)
            reader = self.pdf_txtlayer_reader if pdf_with_txt_layer == "auto" else self.pdf_tabby_reader
        else:
            reader = self.pdf_image_reader

        copy_parameters = copy.deepcopy(parameters)
        copy_parameters["pages"] = f"{txtlayer_result.start}:{end}"
        result = reader.read(file_path=path, parameters=copy_parameters)
        return result

    def __merge_documents(self, documents: List[UnstructuredDocument]) -> UnstructuredDocument:
        if len(documents) == 0:
            raise ValueError("No documents to merge")

        if len(documents) == 1:
            return documents[0]

        from itertools import chain
        from dedoc.data_structures.concrete_annotations.attach_annotation import AttachAnnotation
        from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
        from dedoc.data_structures.line_with_meta import LineWithMeta

        tables, attachments = self.__prepare_tables_attachments(documents)
        warnings = list(set(chain.from_iterable([document.warnings for document in documents])))
        table_uids = set([table.metadata.uid for table in tables])
        attachment_uids = set([attachment.uid for attachment in attachments])
        lines, line_id = [], 0

        for line in chain.from_iterable([document.lines for document in documents]):
            line.metadata.line_id = line_id
            line_id += 1
            annotations = []
            for annotation in line.annotations:
                if isinstance(annotation, TableAnnotation) and annotation.value not in table_uids:
                    continue
                if isinstance(annotation, AttachAnnotation) and annotation.value not in attachment_uids:
                    continue
                annotations.append(annotation)
            lines.append(LineWithMeta(line=line.line, metadata=line.metadata, annotations=annotations, uid=line.uid))

        return UnstructuredDocument(tables=tables, lines=lines, attachments=attachments, metadata=documents[0].metadata, warnings=warnings)

    def __prepare_tables_attachments(self, documents: List[UnstructuredDocument]) -> Tuple[list, list]:
        from dedoc.readers.pdf_reader.data_classes.pdf_image_attachment import PdfImageAttachment

        tables, attachments, attachment_uids = [], [], set()
        for document in documents:
            if not document.lines:
                continue

            lines = sorted(document.lines, key=lambda l: l.metadata.page_id)
            min_page, max_page = lines[0].metadata.page_id, lines[-1].metadata.page_id
            tables.extend([table for table in document.tables if min_page <= table.metadata.page_id <= max_page])
            for attachment in document.attachments:
                if not isinstance(attachment, PdfImageAttachment) and attachment.uid not in attachment_uids:
                    attachment_uids.add(attachment.uid)
                    attachments.append(attachment)

                if isinstance(attachment, PdfImageAttachment) and min_page <= attachment.location.page_number <= max_page:
                    attachments.append(attachment)

        return tables, attachments

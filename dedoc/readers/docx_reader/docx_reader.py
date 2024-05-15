from typing import List, Optional

from dedoc.attachments_extractors.concrete_attachments_extractors.docx_attachments_extractor import DocxAttachmentsExtractor
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.docx_reader.data_structures.docx_document import DocxDocument
from dedoc.utils.parameter_utils import get_param_with_attachments


class DocxReader(BaseReader):
    """
    This class is used for parsing documents with .docx extension.
    Please use :class:`~dedoc.converters.DocxConverter` for getting docx file from similar formats.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config, recognized_extensions=recognized_extensions.docx_like_format, recognized_mimes=recognized_mimes.docx_like_format)
        self.attachment_extractor = DocxAttachmentsExtractor(config=self.config)

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines, tables and attachments.
        This reader is able to add some additional information to the `tag_hierarchy_level` of :class:`~dedoc.data_structures.LineMetadata`.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        with_attachments = get_param_with_attachments(parameters)
        attachments = self.attachment_extractor.extract(file_path=file_path, parameters=parameters) if with_attachments else []

        docx_document = DocxDocument(path=file_path, attachments=attachments, logger=self.logger)
        lines = self.__fix_lines(docx_document.lines)
        return UnstructuredDocument(lines=lines, tables=docx_document.tables, attachments=attachments, warnings=[])

    def __fix_lines(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        for i, line in enumerate(lines[1:]):
            if lines[i].metadata.tag_hierarchy_level != line.metadata.tag_hierarchy_level \
                    or lines[i].metadata.tag_hierarchy_level.line_type != HierarchyLevel.unknown \
                    or lines[i].line.endswith("\n"):
                continue

            old_len = len(lines[i].line)
            lines[i].set_line(lines[i].line + "\n")

            for annotation in lines[i].annotations:
                if annotation.end == old_len:
                    annotation.end += 1

        return lines

import zipfile
from bs4 import BeautifulSoup

from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.readers.docx_reader.styles_extractor import StylesExtractor
from dedoc.readers.docx_reader.numbering_extractor import NumberingExtractor
from dedoc.readers.docx_reader.data_structures import Paragraph, ParagraphInfo

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table as DocxTable

from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.utils.hierarch_level_extractor import HierarchyLevelExtractor

from typing import List, Dict, Tuple, Optional, Union

from dedoc.structure_parser.heirarchy_level import HierarchyLevel
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.annotation import Annotation


class DocxReader(BaseReader):
    def __init__(self):
        self.remove_empty_paragraphs = True
        self.hierarchy_level_extractor = HierarchyLevelExtractor()
        self.annotations = []

    def can_read(self,
                 path: str,
                 mime: str,
                 extension: str,
                 document_type: Optional[str]) -> bool:
        return ((extension in recognized_extensions.docx_like_format or mime in recognized_mimes.docx_like_format) and
                not document_type)

    def read(self,
             path: str,
             document_type: Optional[str] = None,
             parameters: Optional[dict] = None) -> Tuple[UnstructuredDocument, bool]:

        # extract tables
        try:
            document = Document(path)
            tables = [self._process_table(table) for table in document.tables]
        except IndexError:
            tables = []
        except PackageNotFoundError:
            tables = []

        # extract text lines
        lines = self._process_lines(path)

        return UnstructuredDocument(lines=lines, tables=tables), True

    @staticmethod
    def _process_table(table: DocxTable) -> Table:
        cells = [[cell.text for cell in row.cells] for row in table.rows]
        metadata = TableMetadata(page_id=None)
        return Table(cells=cells, metadata=metadata)

    def _process_lines(self,
                       path: str) -> List[LineWithMeta]:
        # TODO do not extract table contents
        document_xml = zipfile.ZipFile(path)
        body = BeautifulSoup(document_xml.read('word/document.xml'), 'xml').body
        styles_extractor = StylesExtractor(BeautifulSoup(document_xml.read('word/styles.xml'), 'xml'))
        try:
            numbering_extractor = NumberingExtractor(BeautifulSoup(document_xml.read('word/numbering.xml'), 'xml'),
                                                     styles_extractor)
            styles_extractor.numbering_extractor = numbering_extractor
        except KeyError:
            numbering_extractor = None

        # the list of paragraph with their properties
        paragraph_list = []

        for paragraph in body:
            # ignore tables
            if paragraph.name == 'tbl':
                continue
            if paragraph.name != 'p':
                child_paragraph_list = paragraph.find_all('w:p')
                for child_paragraph in child_paragraph_list:
                    paragraph_list.append(Paragraph(child_paragraph, styles_extractor, numbering_extractor))
                continue
            paragraph_list.append(Paragraph(paragraph, styles_extractor, numbering_extractor))

        return self._get_lines_with_meta(paragraph_list)

    def _get_lines_with_meta(self,
                             paragraph_list: List[Paragraph]) -> List[LineWithMeta]:
        """
        :param paragraph_list: list of Paragraph
        :return: list of LineWithMeta
        """
        lines_with_meta = []
        paragraph_id = 0

        for paragraph in paragraph_list:

            # line with meta:
            # {"text": "",
            #  "type": ""("paragraph" ,"list_item", "raw_text"), "level": (1,1) or None (hierarchy_level),
            #  "indent": {"firstLine", "hanging", "start", "left"}, "alignment": "" ("left", "right", "center", "both"),
            #  "annotations": [[start, end, size], [start, end, "bold"], [start, end, "italic"],
            #  [start, end, "underlined"], ...] }
            paragraph_properties = ParagraphInfo(paragraph)
            line_with_meta = paragraph_properties.get_info()
            self.annotations.append(line_with_meta)

            text = line_with_meta["text"]
            paragraph_type = line_with_meta["type"]
            level = line_with_meta["level"]
            if level:
                hierarchy_level = HierarchyLevel(level[0], level[1], False, paragraph_type)
            else:
                hierarchy_level = HierarchyLevel(None, None, False, "raw_text")
            annotations = []
            for annotation in line_with_meta["annotations"]:
                # TODO add indent, size, alignment
                annotations.append(Annotation(*annotation))

            paragraph_id += 1
            metadata = ParagraphMetadata(paragraph_type=paragraph_type,
                                         predicted_classes=None,
                                         page_id=0,
                                         line_id=paragraph_id)

            lines_with_meta.append(LineWithMeta(line=text,
                                                hierarchy_level=hierarchy_level,
                                                metadata=metadata,
                                                annotations=annotations))
            lines_with_meta = self.hierarchy_level_extractor.get_hierarchy_level(lines_with_meta)
        return lines_with_meta

    @property
    def get_annotations(self) -> List[Dict[str, Union[str, Optional[Tuple[int, int]], Dict[str, int],
                                                      List[Tuple[int, int, str]]]]]:
        return self.annotations

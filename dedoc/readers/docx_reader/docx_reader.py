import zipfile
from bs4 import BeautifulSoup
from dedoc.readers.docx_reader.styles_extractor import StylesExtractor
from dedoc.readers.docx_reader.numbering_extractor import NumberingExtractor
from dedoc.readers.docx_reader.data_structures import Paragraph

from docx import Document
from docx.table import Table as DocxTable

from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.utils.hierarch_level_extractor import HierarchyLevelExtractor

from typing import List, Optional, Tuple

from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
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

    def can_read(self,
                 path: str,
                 mime: str,
                 extension: str,
                 document_type: str) -> bool:
        return extension in recognized_extensions.docx_like_format or mime in recognized_mimes.docx_like_format

    def read(self,
             path: str,
             document_type: Optional[str] = None,
             parameters: Optional[dict] = None) -> Tuple[UnstructuredDocument, bool]:
        # extract tables
        document = Document(path)
        tables = [self._process_table(table) for table in document.tables]
        # extract text lines
        lines = self._process_lines(path)

        return UnstructuredDocument(lines=lines, tables=tables), True

    def _process_table(self,
                       table: DocxTable) -> Table:
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
        paragraphs = body.find_all('w:p')
        for paragraph in paragraphs:
            # TODO text may be without w:t
            if not paragraph.t:
                continue

            paragraph_list.append(Paragraph(paragraph, styles_extractor, numbering_extractor))
        return self._get_lines_with_meta(paragraph_list)

    def _get_lines_with_meta(self,
                             paragraph_list: list) -> List[LineWithMeta]:
        """
        :param paragraph_list: list of Paragraph
        :return: list of LineWithMeta
        """
        lines_with_meta = []
        paragraph_id = 0

        for paragraph in paragraph_list:
            # line_with_meta - dictionary
            # [{"text": "",
            # "properties": [[start, end, {"indent", "size", "bold", "italic", "underlined"}], ...] }, ...]
            # start, end - character's positions begin with 0, end isn't included
            # indent = {"firstLine", "hanging", "start", "left"}
            line_with_meta = paragraph.get_info()
            
            text = line_with_meta["text"]
            annotations = []
            for item in line_with_meta["properties"]:
                if item[2]["bold"]:
                    annotations.append(Annotation(item[0], item[1], "bold"))
                if item[2]["italic"]:
                    annotations.append(Annotation(item[0], item[1], "italic"))
                if item[2]["underlined"]:
                    annotations.append(Annotation(item[0], item[1], "underlined"))

            paragraph_id += 1
            metadata = ParagraphMetadata(paragraph_type="raw_text",
                                         predicted_classes=None,
                                         page_id=0,
                                         line_id=paragraph_id)
            lines_with_meta.append(LineWithMeta(line=text, hierarchy_level=None,
                                                metadata=metadata, annotations=annotations))
            lines_with_meta = self.hierarchy_level_extractor.get_hierarchy_level(lines_with_meta)
        return lines_with_meta


if __name__ == "__main__":
    filename = input()
    docx_reader = DocxReader()
    result, _ = docx_reader.read(filename)
    lines = result.lines
    for line in lines:
        print(line.line)
        print(line.annotations)
        print(line.hierarchy_level.level_1, line.hierarchy_level.level_2)

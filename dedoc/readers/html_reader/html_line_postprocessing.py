from typing import List

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.html_reader.html_tags import HtmlTags


class HtmlLinePostprocessing:

    def postprocess(self, document: UnstructuredDocument) -> UnstructuredDocument:
        lines = self.__lines_postprocessing(document.lines)
        document.lines = lines
        return document

    def __lines_postprocessing(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        lines = self.__add_newlines(lines)
        lines = self.__fix_special_symbols(lines)
        for line_id, line in enumerate(lines):
            line.metadata.line_id = line_id
        return lines

    def __add_newlines(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        for line, next_line in zip(lines[:-1], lines[1:]):
            next_line_tag = getattr(next_line.metadata, "html_tag", None)
            if not line.line.endswith("\n") and next_line_tag in HtmlTags.paragraphs:
                line.set_line(line.line + "\n")
        return lines

    def __fix_special_symbols(self, lines: List[LineWithMeta]) -> List[LineWithMeta]:
        """
        replace some special symbols to common symbols, e.q.
        "\xa0" -> " "
        @param lines:
        @return:
        """
        for line in lines:
            new_text = line.line.replace("\xa0", " ")
            line.set_line(new_text)
        return lines

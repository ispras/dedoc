import hashlib
import string
from typing import List, Optional, Union

from bs4 import BeautifulSoup
from bs4 import Comment, Doctype, Tag

from dedoc.data_structures.cell_with_meta import CellWithMeta
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.html_reader.html_line_postprocessing import HtmlLinePostprocessing
from dedoc.readers.html_reader.html_tag_annotation_parser import HtmlTagAnnotationParser
from dedoc.readers.html_reader.html_tags import HtmlTags
from dedoc.utils.utils import calculate_file_hash, get_mime_extension


class HtmlReader(BaseReader):
    """
    This reader allows to handle documents with the following extensions: .html, .shtml
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        self.postprocessor = HtmlLinePostprocessing()
        self.tag_annotation_parser = HtmlTagAnnotationParser()

    def can_read(self, file_path: Optional[str] = None, mime: Optional[str] = None, extension: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if the document extension is suitable for this reader.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        extension, mime = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return extension.lower() in [".html", ".shtml"] or mime in ["text/html"]

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines and tables, attachments remain empty.
        This reader is able to add some additional information to the `tag_hierarchy_level` of :class:`~dedoc.data_structures.LineMetadata`.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        parameters = {} if parameters is None else parameters
        with open(file_path, "rb") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        handle_invisible_table = str(parameters.get("handle_invisible_table", "false")).lower() == "true"
        path_hash = calculate_file_hash(path=file_path)
        lines = self.__read_blocks(soup, path_hash=path_hash, handle_invisible_table=handle_invisible_table)
        tables = [
            self._read_table(table, path_hash) for table in soup.find_all("table") if self._visible_table(table, handle_invisible_table=handle_invisible_table)
        ]
        document = UnstructuredDocument(tables=tables, lines=lines, attachments=[])
        document_postprocess = self.postprocessor.postprocess(document)
        return document_postprocess

    def __handle_block(self, tag: Union[Tag], uid: str, handle_invisible_table: bool, table: Optional[bool] = False) -> List[LineWithMeta]:
        tag_uid = hashlib.md5((uid + str(tag.name)).encode()).hexdigest()
        assert isinstance(tag, (Tag, str))
        if not self.__is_content_tag(tag, handle_invisible_table=handle_invisible_table):
            block_lines = []
        elif tag.name == "table" and not self._visible_table(tag, handle_invisible_table=handle_invisible_table):
            # if table is invisible and we don't parse invisible tables (handle_invisible_table == False)
            # then we parse table as raw text
            block_lines = self.__handle_invisible_table(block=tag, path_hash=tag_uid)
        elif isinstance(tag, str):
            block_lines = self._handle_text_line(block=tag, path_hash=tag_uid)
        elif tag.name not in HtmlTags.available_tags:
            self.logger.debug(f"skip tag {tag.name.encode()}")
            block_lines = []
        elif tag.name in HtmlTags.special_symbol_tags:
            tag_value = HtmlTags.special_symbol_tags[tag.name]
            block_lines = self._handle_text_line(block=tag_value, path_hash=uid, ignore_space=False)
        elif tag.name in HtmlTags.block_tags:
            block_lines = self.__read_blocks(block=tag, path_hash=tag_uid)
        elif tag.name in HtmlTags.list_tags:
            block_lines = self.__read_list(lst=tag, uid=tag_uid, path_hash=uid, handle_invisible_table=handle_invisible_table)
        else:
            block_lines = self.__handle_single_tag(tag, tag_uid, table)
        for line in block_lines:
            if not getattr(line.metadata, "html_tag", None):
                line.metadata.extend_other_fields({"html_tag": tag.name})
        return block_lines

    def __handle_single_tag(self, tag: Tag, uid: str, table: Optional[bool] = False) -> List[LineWithMeta]:
        text = self.__get_text(tag, table)

        if not text or text.isspace():
            return []

        annotations = self.tag_annotation_parser.parse(tag=tag)
        header_level = int(tag.name[1:]) if tag.name in HtmlTags.header_tags else 0
        line_type = HierarchyLevel.unknown if header_level == 0 else HierarchyLevel.header
        tag_uid = hashlib.md5((uid + text).encode()).hexdigest()
        line = self.__make_line(line=text, line_type=line_type, header_level=header_level, uid=tag_uid, path_hash=uid, annotations=annotations)
        line.metadata.extend_other_fields({"html_tag": tag.name})
        return [line]

    def __read_blocks(self, block: Tag, path_hash: str = "", handle_invisible_table: bool = False, table: Optional[bool] = False) -> List[LineWithMeta]:
        uid = hashlib.md5((path_hash + str(block.name)).encode()).hexdigest()
        if not self.__is_content_tag(block, handle_invisible_table=handle_invisible_table):
            return []

        lines = []

        for tag in block:
            assert isinstance(tag, (Tag, str))
            block_lines = self.__handle_block(tag=tag, uid=uid, handle_invisible_table=handle_invisible_table, table=table)
            lines.extend(block_lines)
        return lines

    def _handle_text_line(self, block: str, path_hash: str, ignore_space: bool = True) -> List[LineWithMeta]:
        if not block.strip() and ignore_space:
            return []
        uid = hashlib.md5(block.encode()).hexdigest()
        line = self.__make_line(block, HierarchyLevel.unknown, 0, uid=uid, path_hash=path_hash)
        return [line]

    def __make_line(self, line: str, line_type: str, header_level: int = 0, uid: str = None, path_hash: str = None, annotations: List = None) -> LineWithMeta:
        if annotations is None:
            annotations = []

        level = None if header_level == 0 else HierarchyLevel(1, header_level, False, line_type=line_type)
        metadata = LineMetadata(page_id=0, line_id=None, tag_hierarchy_level=level)  # TODO line_id

        uid = f"{path_hash}_{uid}"
        return LineWithMeta(line=line, metadata=metadata, annotations=annotations, uid=uid)

    def __get_li_header(self, list_type: str, index: int) -> LineWithMeta:
        end = ") " if list_type in ["a", "A"] else ". "
        if list_type == "":
            header = ""

        elif list_type in ["a", "A"]:
            alphabet = string.ascii_lowercase if list_type == "a" else string.ascii_uppercase
            header = alphabet[index % len(alphabet)]

            while index >= len(alphabet):
                index = index // len(alphabet) - 1
                header = alphabet[index % len(alphabet)] + header

            header = header + end
        else:
            header = str(index + 1) + end
        metadata = LineMetadata(tag_hierarchy_level=HierarchyLevel(2, 1, False, line_type=HierarchyLevel.list_item), page_id=0, line_id=0)
        header_line = LineWithMeta(line=header, metadata=metadata)
        return header_line

    def __read_list(self, lst: Tag, uid: str, path_hash: str, handle_invisible_table: bool) -> List[LineWithMeta]:
        lines = []
        list_type = lst.get("type", "1" if lst.name in HtmlTags.ordered_list else "")
        item_index = 0

        for item in lst:
            if item.name in HtmlTags.list_items:
                item_lines = self.__handle_list_item(item=item,
                                                     item_index=item_index,
                                                     list_type=list_type,
                                                     path_hash=path_hash,
                                                     handle_invisible_table=handle_invisible_table)
                item_index += 1
                lines.extend(item_lines)
        return lines

    def __handle_list_item(self, item: Tag, item_index: int, list_type: str, path_hash: str, handle_invisible_table: bool) -> List[LineWithMeta]:
        lines = []
        header_line = self.__get_li_header(list_type=list_type, index=item_index)
        block_lines = self.__handle_block(item, uid=path_hash, handle_invisible_table=handle_invisible_table)
        hl_depth = header_line.metadata.tag_hierarchy_level.level_1
        for line in block_lines:
            if line.metadata.tag_hierarchy_level.is_unknown():
                header_line += line
            else:
                # Handle complex and nested lists
                lines.append(header_line)
                line.metadata.tag_hierarchy_level.level_1 += hl_depth
                header_line = line
        lines.append(header_line)
        return lines

    # not currently used, but may be useful in the future
    def __get_text(self, tag: Tag, table: Optional[bool] = False) -> [str, int, int]:
        for br in tag.find_all("br"):
            br.replace_with("\n")
        text = tag.getText() + "\n" if tag.name == "p" and not table else tag.getText()
        text = "" if text is None else text
        return text

    def __is_content_tag(self, tag: Tag, handle_invisible_table: bool = False) -> bool:
        """
        check if given tag is a content tag
        @param tag: html tag
        @param handle_invisible_table: is invisibly table should be handled as table
        @return: True if tag is a content tag False otherwise.
        """
        if tag.name in HtmlTags.service_tags:
            return False
        if tag.name == "table" and not self._visible_table(tag, handle_invisible_table=handle_invisible_table):
            return True
        return not isinstance(tag, Doctype) and not isinstance(tag, Comment)

    def __handle_invisible_table(self, block: Tag, path_hash: str) -> List[LineWithMeta]:
        uid = hashlib.md5(block.name.encode()).hexdigest()
        result = []
        rows = self._read_table(block, path_hash).cells
        for row in rows:
            text = "\t".join([cell.get_text() for cell in row])
            if text.strip() != "":
                tag_uid = hashlib.md5((uid + text).encode()).hexdigest()
                line = self.__make_line(line=text, line_type=HierarchyLevel.unknown, uid=tag_uid, path_hash=path_hash)
                result.append(line)
        return result

    def _read_table(self, table: Tag, path_hash: str) -> Table:
        cells_with_meta = []

        for row in table.find_all(HtmlTags.table_rows):
            row_lines = []
            for cell in row.find_all(HtmlTags.table_cells):
                cell_with_meta = CellWithMeta(
                    lines=self.__read_blocks(block=cell, path_hash=path_hash, handle_invisible_table=False, table=True),  # read cells as blocks in order to extract styles
                    colspan=cell.colspan if cell.colspan else 1,
                    rowspan=cell.rowspan if cell.rowspan else 1,
                    invisible=cell.invisible if cell.invisible else True
                )
                row_lines.append(cell_with_meta)
            cells_with_meta.append(row_lines)

        return Table(cells=cells_with_meta, metadata=TableMetadata(page_id=0))

    def _visible_table(self, table: Tag, handle_invisible_table: bool) -> bool:
        if handle_invisible_table:
            return True
        assert table.name == "table", f"block {table} is not table"
        for td in table.find_all("td"):
            style = td.attrs.get("style", "")
            if "border-bottom-style:solid" in style or "border-top-style:solid" in style:
                return True
        return table.attrs.get("border", "0") != "0"

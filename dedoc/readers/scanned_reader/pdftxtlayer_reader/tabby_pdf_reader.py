import json
import logging
import os
import re
import subprocess
from typing import List, Optional, Tuple

import numpy as np
from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.indentation_annotation import IndentationAnnotation
from dedoc.data_structures.concrete_annotations.italic_annotation import ItalicAnnotation
from dedoc.data_structures.concrete_annotations.size_annotation import SizeAnnotation
from dedoc.data_structures.concrete_annotations.spacing_annotation import SpacingAnnotation
from dedoc.data_structures.concrete_annotations.style_annotation import StyleAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.scanned_reader.data_classes.bbox import BBox
from dedoc.readers.scanned_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.scanned_reader.data_classes.pdf_image_attachment import PdfImageAttachment
from dedoc.readers.scanned_reader.data_classes.tables.location import Location
from dedoc.readers.scanned_reader.data_classes.tables.scantable import ScanTable
from dedoc.utils.utils import calculate_file_hash

from dedoc.common.exceptions.java_not_found_error import JavaNotFoundError
from dedoc.common.exceptions.tabby_pdf_error import TabbyPdfError
from dedoc.readers.scanned_reader.pdf_base_reader import ParametersForParseDoc, PdfBase


class TabbyPDFReader(PdfBase):
    """
     Pdf extractor based on TabbyPDF
    """

    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)
        self.config = config
        self.logger = config.get("logger", logging.getLogger())
        self.tabby_java_version = "2.0.0"
        self.jar_name = "ispras_tbl_extr.jar"
        jar_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "resources", "jars")
        self.jar_dir = os.path.abspath(jar_dir)
        self.java_not_found_error = (
            "`java` command is not found from this Python process."
            "Please ensure Java is installed and PATH is set for `java`"
        )
        self.default_config = {"JAR_PATH": os.path.join(self.jar_dir, self.jar_name)}

    def can_read(self,
                 path: str,
                 mime: str,
                 extension: str,
                 document_type: str,
                 parameters: Optional[dict] = None) -> bool:
        return extension.endswith("pdf") and (str(parameters.get("pdf_with_text_layer", "false")).lower() == "tabby")

    def _process_one_page(self,
                          image: np.ndarray,
                          parameters: ParametersForParseDoc,
                          page_number: int,
                          path: str) -> Tuple[List[LineWithLocation], List[ScanTable], List[PdfImageAttachment]]:

        return [], [], []

    def read(self, path: str, document_type: Optional[str], parameters: Optional[dict]) -> UnstructuredDocument:
        lines, scan_tables = self.__extract(path=path)
        warnings = []
        document_metadata = None
        pages = str(parameters.get("pages", ""))
        pattern = r"\d*:\d*"
        if re.match(pattern, pages):
            pages_array = pages.split(":")
            start, end = pages_array
            start_page = int(start) if start else 0
            end_page = int(end) if end else None
            warnings.append("The document is partially parsed")
            document_metadata = dict(first_page=start_page, last_page=end_page)
            if end_page:
                lines = [line for line in lines if start_page - 1 <= line.metadata.page_id < end_page]
            else:
                lines = [line for line in lines if start_page - 1 <= line.metadata.page_id]

        lines = self.linker.link_objects(lines=lines, tables=scan_tables, images=[])
        lines = self.hierarchy_level_extractor.get_hierarchy_level(lines=lines)
        tables = []
        for scan_table in scan_tables:
            metadata = TableMetadata(page_id=scan_table.page_number, uid=scan_table.name)
            cells = [[cell.replace("\n", "<br />") for cell in row] for row in scan_table.matrix_cells]
            table = Table(metadata=metadata, cells=cells)
            tables.append(table)
        lines = [line for line_group in lines for line in line_group.split("\n")]
        lines_with_paragraphs = self.paragraph_extractor.extract(lines)
        result = UnstructuredDocument(lines=lines_with_paragraphs, tables=tables, attachments=[], warnings=warnings, metadata=document_metadata)

        return self._postprocess(result)

    def __extract(self, path: str, start_page: int = None, end_page: int = None) -> Tuple[List[LineWithMeta], List[ScanTable]]:
        file_hash = calculate_file_hash(path=path)
        document = self.__process_pdf(path=path, start_page=start_page, end_page=end_page)
        all_lines = []
        all_tables = []
        for page in document.get("pages", []):
            lines = self.__get_lines_with_location(page, file_hash)
            if lines:
                all_lines.extend(lines)
            tables = self.__get_tables(page, file_hash)
            if tables:
                all_tables.extend(tables)

        return all_lines, all_tables

    def __get_tables(self, page: dict, file_hash: str) -> List[ScanTable]:
        tables = []
        page_number = page["number"]
        i = 0
        for table in page["tables"]:
            i += 1
            x_top_left = table["x_top_left"]
            y_top_left = table["y_top_left"]
            x_bottom_right = x_top_left + table["width"]
            y_bottom_right = y_top_left + table["height"]
            rows = table["rows"]
            cells = [row for row in rows]
            bbox = BBox.from_two_points((x_top_left, y_top_left), (x_bottom_right, y_bottom_right))

            tables.append(ScanTable(matrix_cells=cells, page_number=page_number, bbox=bbox, name=file_hash + str(page_number) + str(i)))
        return tables

    def __get_lines_with_location(self, page: dict, file_hash: str) -> List[LineWithLocation]:
        lines = []
        page_number = page["number"]
        for block in page["blocks"]:
            annotations = []
            block_id = block["order"]
            block_text = block["text"]
            bx_top_left = block["x_top_left"]
            by_top_left = block["y_top_left"]
            bx_bottom_right = bx_top_left + block["width"]
            by_bottom_right = by_top_left + block["height"]
            indent = block["indent"]
            spacing = block["spacing"]
            len_block = len(block_text)
            annotations.append(IndentationAnnotation(0, len_block, str(indent)))
            annotations.append(SpacingAnnotation(0, len_block, str(spacing)))

            for annotation in block["annotations"]:
                is_bold = annotation["is_bold"]
                is_italic = annotation["is_italic"]
                font_name = annotation["font_name"]
                font_size = annotation["font_size"]
                start = annotation["start"]
                end = annotation["end"]

                annotations.append(SizeAnnotation(start, end, str(font_size)))
                if is_bold:
                    annotations.append(BoldAnnotation(start, end, "True"))
                if is_italic:
                    annotations.append(ItalicAnnotation(start, end, "True"))
                annotations.append(StyleAnnotation(start, end, font_name))

            meta = block["metadata"].lower()
            uid = "txt_{}_{}".format(file_hash, block_id)
            bbox = BBox.from_two_points((bx_top_left, by_top_left), (bx_bottom_right, by_bottom_right))
            metadata = ParagraphMetadata(page_id=page_number, line_id=block_id, predicted_classes=None, paragraph_type=meta)

            line_with_location = LineWithLocation(line=block_text,
                                                  hierarchy_level=None,
                                                  metadata=metadata,
                                                  annotations=annotations,
                                                  uid=uid,
                                                  location=Location(bbox=bbox, page_number=page_number))
            lines.append(line_with_location)

        return lines

    def __jar_path(self) -> str:
        return os.environ.get("TABBY_JAR", self.default_config["JAR_PATH"])

    def __run(self, path: str = None, encoding: str = "utf-8",
              start_page: int = None, end_page: int = None) -> bytes:
        args = ["java"] + ["-jar", self.__jar_path(), "-i", path]
        if start_page is not None and end_page is not None:
            args += ["-sp", str(start_page), "-ep", str(end_page)]
        try:
            result = subprocess.run(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                check=True,
            )
            if result.stderr:
                self.logger.warning("Got stderr: {}".format(result.stderr.decode(encoding)))
            return result.stdout
        except FileNotFoundError:
            raise JavaNotFoundError(self.java_not_found_error)
        except subprocess.CalledProcessError as e:
            raise TabbyPdfError(e.stderr.decode(encoding))

    def __process_pdf(self, path: str, start_page: int = None, end_page: int = None) -> dict:
        output = self.__run(path=path, start_page=start_page, end_page=end_page)
        response = output.decode('UTF-8')
        document = json.loads(response) if response else {}
        return document

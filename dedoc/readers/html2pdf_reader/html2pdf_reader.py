import os
import re
from copy import deepcopy
from tempfile import TemporaryDirectory
from typing import Dict, Optional, Tuple
from uuid import uuid1

from bs4 import BeautifulSoup
from weasyprint import HTML

from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.table import Table
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.html_reader.html_reader import HtmlReader
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader
from dedoc.utils.utils import calculate_file_hash


class Html2PdfReader(HtmlReader):

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        self.pdf_reader = PdfTxtlayerReader(config=self.config)

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        parameters = {} if parameters is None else parameters
        with TemporaryDirectory() as tmp_dir:
            modified_path, tables = self._modify_html(file_path, tmp_dir)
            converted_path = os.path.join(tmp_dir, os.path.basename(file_path).replace(".html", ".pdf"))
            HTML(filename=modified_path).write_pdf(converted_path)
            self.logger.info(f"Convert {modified_path} to {converted_path}")
            parameters_new = deepcopy(parameters)
            parameters_new["pdf_with_text_layer"] = "true"
            unstructured_document = self.pdf_reader.read(file_path=converted_path, parameters=parameters_new)

        return self._add_tables(document=unstructured_document, tables=tables)

    def _add_tables(self, document: UnstructuredDocument, tables: Dict[str, Table]) -> UnstructuredDocument:
        lines = []
        tables_result = []
        previous_line = None
        line_id = 0
        for line in document.lines:
            table_uid = line.line.strip()
            if table_uid not in tables:
                previous_line = line
                line.metadata.page_id = line_id
                line_id += 1
                lines.append(line)
            elif previous_line is not None:
                table_annotation = TableAnnotation(name=table_uid, start=0, end=len(line.line))
                previous_line.annotations.append(table_annotation)
                tables_result.append(tables[table_uid])
        return UnstructuredDocument(lines=lines, tables=tables_result, attachments=document.attachments)

    def _handle_tables(self, soup: BeautifulSoup, path_hash: str) -> dict:
        tables = {}
        for table_tag in soup.find_all("table"):
            table_uid = f"table_{uuid1()}"
            table = self._read_table(table_tag, path_hash)
            table.metadata.uid = table_uid
            tables[table_uid] = table
            table_tag.replace_with(table_uid)

        return tables

    def _handle_super_elements(self, soup: BeautifulSoup) -> None:
        """
        Function finds super-elements in the html (html present as BeautifulSoup's object)
        (For example:
         html-code: <span>1</span><span style="font-size:6pt; vertical-align:super">1</span><span>) lalala</span>)
         view: "1 ^1 ) lalala"

         and converts into
         html-code: <span>1.1) lalala</span>
         view: "1.1) lalala"
        """
        supers = soup.find_all(["span", "p"], {"style": re.compile("vertical-align:super")})

        for super_element in supers:
            if super_element.previous and super_element.previousSibling:
                super_element.previous.replaceWith(super_element.previous + "." + super_element.contents[0])
                if super_element.next and super_element.nextSibling:
                    super_element.previousSibling.replaceWith(super_element.previous + super_element.nextSibling.string)
                    super_element.nextSibling.decompose()
                super_element.decompose()

    def _modify_html(self, path: str, tmp_dir: str) -> Tuple[str, dict]:
        with open(path, encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        tables = self._handle_tables(soup, path_hash=calculate_file_hash(path=path))
        self._handle_super_elements(soup)

        path_out = os.path.join(tmp_dir, os.path.basename(path))

        with open(path_out, "wb") as f_output:
            f_output.write(soup.prettify("utf-8"))
        return path_out, tables

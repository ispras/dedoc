import os
import time
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup, Tag

from dedoc.data_structures import Annotation, CellWithMeta, HierarchyLevel, LineMetadata, Table, TableAnnotation, TableMetadata
from dedoc.data_structures.concrete_annotations.reference_annotation import ReferenceAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_mimes
from dedoc.readers.base_reader import BaseReader
from dedoc.utils.parameter_utils import get_param_document_type
from dedoc.utils.utils import get_mime_extension


class ArticleReader(BaseReader):
    """
    This class is used for parsing scientific articles with .pdf extension using `GROBID <https://grobid.readthedocs.io/en/latest/>`_ system.
    """

    def __init__(self, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        self.grobid_url = f"http://{os.environ.get('GROBID_HOST', 'localhost')}:{os.environ.get('GROBID_PORT', '8070')}"
        self.url = f"{self.grobid_url}/api/processFulltextDocument"
        self.grobid_is_alive = False
        self.__update_grobid_alive(self.grobid_url, max_attempts=self.config.get("grobid_max_connection_attempts", 3))

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method calls the service GROBID method ``/api/processFulltextDocument`` and analyzes the result (format XML/TEI) of the recognized article
        using beautifulsoup library.
        As a result, the method fills the class :class:`~dedoc.data_structures.UnstructuredDocument`.
        Article reader adds additional information to the `tag_hierarchy_level` of :class:`~dedoc.data_structures.LineMetadata`.
        The method extracts information about ``authors``, ``bibliography items``, ``sections``, and ``tables``.
        You can find more information about the extracted information from GROBID system on the page :ref:`article_structure`.

        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        with open(file_path, "rb") as file:
            files = {"input": file}
            try:
                response = requests.post(self.url, files=files)
                if response.status_code != 200:
                    warning = f"GROBID returns code {response.status_code}."
                    self.logger.warning(warning)
                    return UnstructuredDocument(tables=[], lines=[], attachments=[], warnings=[warning])
            except requests.exceptions.ConnectionError as ex:
                warning = f"GROBID doesn't response. Check GROBID service on {self.url}. Exception' msg: {ex}"
                self.logger.warning(warning)
                return UnstructuredDocument(tables=[], lines=[], attachments=[], warnings=[warning])

            soup = BeautifulSoup(response.text, features="lxml")
            lines = self.__parse_title(soup)

            if soup.biblstruct is not None:
                authors = soup.biblstruct.find_all("author")
                lines += [line for author in authors for line in self.__parse_author(author)]

            bib_lines, bib2uid = self.__parse_bibliography(soup)
            tables, table2uid = self.__parse_tables(soup)

            lines += self.__parse_text(soup, bib2uid, table2uid)
            lines.extend(bib_lines)

            return UnstructuredDocument(tables=tables, lines=lines, attachments=[], warnings=["use GROBID (version: 0.8.0)"])

    def can_read(self, file_path: Optional[str] = None, mime: Optional[str] = None, extension: Optional[str] = None, parameters: Optional[dict] = None) -> bool:
        """
        Check if:

        * the document extension is suitable for this reader (.pdf);
        * parameter "document_type" is "article";
        * GROBID service is running on port 8070.

        Look to the documentation of :meth:`~dedoc.readers.BaseReader.can_read` to get information about the method's parameters.
        """
        if get_param_document_type(parameters) != "article":
            return False

        self.__update_grobid_alive(self.grobid_url, max_attempts=1)
        if not self.grobid_is_alive:
            return False

        mime, extension = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return mime in recognized_mimes.pdf_like_format and extension.lower() == ".pdf"

    def __update_grobid_alive(self, grobid_url: str, max_attempts: int = 2) -> None:
        if self.grobid_is_alive:
            return

        attempt = max_attempts
        while attempt > 0:
            try:
                response = requests.get(f"{grobid_url}/api/isalive")
                if response.status_code == 200:
                    self.logger.info(f"GROBID up on {grobid_url}.")
                    self.grobid_is_alive = True
                    return
            except requests.exceptions.ConnectionError as ex:
                self.logger.warning(f"GROBID doesn't response. Check GROBID service on {self.url}. Exception's msg: {ex}")
            time.sleep(5)
            attempt -= 1

        self.grobid_is_alive = False

    def __get_tag_by_hierarchy_path(self, source: Tag, hierarchy_path: List[str]) -> Optional[str]:
        cur_tag = source
        for path_item in hierarchy_path:
            cur_tag = cur_tag.find(path_item)
            if cur_tag is None:
                # tag not found
                return ""

        return ArticleReader.__tag2text(cur_tag)

    def __create_line(self, text: str, hierarchy_level_id: Optional[int] = None, paragraph_type: Optional[str] = None,
                      annotations: Optional[List[Annotation]] = None, other_fields: Optional[Dict] = None) -> LineWithMeta:
        # TODO check on improve
        if other_fields is None:
            other_fields = {}
        assert text is not None
        assert isinstance(text, str)

        if hierarchy_level_id is None or paragraph_type is None:
            hierarchy_level = HierarchyLevel.create_raw_text()
        else:
            hierarchy_level = HierarchyLevel(level_1=hierarchy_level_id, level_2=0, can_be_multiline=False, line_type=paragraph_type)

        return LineWithMeta(line=text,
                            metadata=LineMetadata(page_id=0, line_id=0, tag_hierarchy_level=hierarchy_level, other_fields=other_fields),
                            annotations=annotations)

    def __parse_affiliation(self, affiliation_tag: Tag) -> List[LineWithMeta]:
        lines = [self.__create_line(text=affiliation_tag.get("key"), hierarchy_level_id=2, paragraph_type="author_affiliation")]

        if affiliation_tag.orgname:
            lines.append(self.__create_line(text=self.__tag2text(affiliation_tag.orgname), hierarchy_level_id=3, paragraph_type="org_name"))

        if affiliation_tag.address:
            lines.append(self.__create_line(text=affiliation_tag.address.text, hierarchy_level_id=3, paragraph_type="address"))

        return lines

    def __parse_author(self, author_tag: Tag) -> List[LineWithMeta]:
        """

        Example:
        <author>
        <persname><forename type="first">Sonia</forename><surname>Belaïd</surname></persname>
        <affiliation key="aff0">
        <orgname type="institution">École Normale Supérieure</orgname>
        <address>
        <addrline>45 rue dUlm</addrline>
        <postcode>75005</postcode>
        <settlement>Paris</settlement>
        </address>
        </affiliation>
        <affiliation key="aff1">
        <orgname type="institution">Thales Communications &amp; Security</orgname>
        <address>
        <addrline>4 Avenue des Louvresses</addrline>
        <postcode>92230</postcode>
        <settlement>Gennevilliers</settlement>
        </address>
        </affiliation>
        </author>
        """
        lines = [self.__create_line(text="", hierarchy_level_id=1, paragraph_type="author")]

        first_name = self.__get_tag_by_hierarchy_path(author_tag, ["persname", "forename"])
        if first_name:
            lines.append(self.__create_line(text=first_name, hierarchy_level_id=2, paragraph_type="author_first_name"))

        surname = self.__get_tag_by_hierarchy_path(author_tag, ["persname", "surname"])
        if surname:
            lines.append(self.__create_line(text=surname, hierarchy_level_id=2, paragraph_type="author_surname"))

        lines += [
            self.__create_line(text=email.get_text(), hierarchy_level_id=3, paragraph_type="email")
            for email in author_tag.find_all("email") if email
        ]

        affiliations = author_tag.find_all("affiliation")
        lines += [line for affiliation in affiliations for line in self.__parse_affiliation(affiliation)]

        return lines

    def __create_line_with_refs(self, content: List[Tuple[str, Tag]], bib2uid: dict, table2uid: dict) -> LineWithMeta:
        text = ""
        start = 0
        annotations = []

        for subpart in content:
            if isinstance(subpart, Tag) and subpart.name == "ref":
                target = subpart.get("target")
                sub_text = subpart.string
                if subpart.get("type") == "bibr" and target in bib2uid:
                    annotations.append(ReferenceAnnotation(value=bib2uid[target], start=start, end=start + len(sub_text)))
                if subpart.get("type") == "table" and target in table2uid:
                    annotations.append(TableAnnotation(name=table2uid[target], start=start, end=start + len(sub_text)))
            else:
                sub_text = subpart if isinstance(subpart, str) else ""

            text += sub_text
            start += len(sub_text)

        return self.__create_line(text=text, hierarchy_level_id=None, paragraph_type=None, annotations=annotations)

    def __parse_text(self, soup: Tag, bib2uid: dict, table2uid: dict) -> List[LineWithMeta]:
        """
        Example of section XML tag:
        <div xmlns="http://www.tei-c.org/ns/1.0"><head n="4.1.1">Preprocessing</head><p>...</p><p>...</p></div>
        """
        lines = []

        abstract = soup.find("abstract").p
        lines.append(self.__create_line(text="Abstract", hierarchy_level_id=1, paragraph_type="abstract"))
        lines.append(self.__create_line(text=self.__tag2text(abstract)))

        for text in soup.find_all("text"):
            for part in text.find_all("div"):
                # TODO: Beautifulsoup doesn't read <head> tags from input XML file. WTF!
                #       As a result we lose section number in text (see example above)
                #       Need to fix this in the future.
                number = part.head.get("n") + " " if part.head else ""
                line_text = str(part.contents[0]) if len(part.contents) > 0 else None
                if line_text is not None and len(line_text) > 0:
                    lines.append(self.__create_line(text=number + line_text, hierarchy_level_id=1, paragraph_type="section"))
                for subpart in part.find_all("p"):
                    if subpart.string is not None:
                        lines.append(self.__create_line_with_refs(subpart.string, bib2uid, table2uid))
                    elif subpart.contents and len(subpart.contents) > 0:
                        lines.append(self.__create_line_with_refs(subpart.contents, bib2uid, table2uid))

        return lines

    @staticmethod
    def __tag2text(tag: Tag) -> str:
        return "" if not tag or not tag.string else tag.string

    def __parse_tables(self, soup: Tag) -> Tuple[List[Table], dict]:
        """
        Example Table with table's ref:
         -----------------------------------------------
            Table Reference Example:
            <ref type="table" target="#tab_0">1</ref>
            ...
            Table Example:
                <figure xmlns="http://www.tei-c.org/ns/1.0" type="table" xml:id="tab_0">
                <head>Table 1 .</head>
                <label>1</label>
                <figDesc>Performance of some illustrative AES implementations.</figDesc>
                <table>
                <row><cell>Software (8-bit)</cell><cell>code size</cell><cell>cycle</cell><cell>cost</cell><cell>physical</cell></row>
                <row><cell>Implementations</cell><cell>(bytes)</cell><cell>count</cell><cell>function</cell><cell>assumptions</cell></row>
                <row><cell>Unprotected [13]</cell><cell>1659</cell><cell>4557</cell><cell>7.560</cell><cell>-</cell></row>
                ...
                </table>
                </figure>
        """
        tables = []
        table2uid = {}

        tag_tables = soup.find_all("figure", {"type": "table"})
        for table in tag_tables:
            row_cells = []
            head = table.contents[0] if len(table.contents) > 0 and isinstance(table.contents[0], str) else self.__tag2text(table.head)
            title = head + self.__tag2text(table.figdesc)
            for row in table.table.find_all("row"):
                row_cells.append([CellWithMeta(lines=[self.__create_line(self.__tag2text(cell))]) for cell in row.find_all("cell")])
            tables.append(Table(cells=row_cells, metadata=TableMetadata(page_id=0, title=title)))
            table2uid["#" + table.get("xml:id")] = tables[-1].metadata.uid

        return tables, table2uid

    def __parse_bibliography(self, soup: Tag) -> Tuple[List[LineWithMeta], dict]:
        """
        Reference Example:
            <ref type="bibr" target="#b5">[6]</ref>
            ...
            <listBibl>
            <biblStruct xml:id="b0">
                <analytic>
                    <title level="a" type="main">Leakage-resilient symmetric encryption via re-keying</title>
                    <author>
                        <persName><forename type="first">Michel</forename><surname>Abdalla</surname></persName>
                    </author>
                    <author>
                        <persName><forename type="first">Sonia</forename><surname>Belaïd</surname></persName>
                    </author>
                    <author>
                        <persName><forename type="first">Pierre-Alain</forename><surname>Fouque</surname></persName>
                    </author>
                </analytic>
                <monogr>
                    <title level="m">Bertoni and Coron</title>
                    <imprint>
                        <biblScope unit="volume">4</biblScope>
                        <biblScope unit="page" from="471" to="488" />
                    </imprint>
                </monogr>
            </biblStruct>
            <biblStruct xml:id="b1">
        """
        lines = []
        cites = {}  # bib_item_grobid_uid: line_uid

        # according GROBID description
        level_2_paragraph_type = {"a": "title", "j": "title_journal", "s": "title_series", "m": "title_conference_proceedings"}

        bibliography = soup.find("listbibl", recursive=True)
        lines.append(self.__create_line(text="bibliography", hierarchy_level_id=1, paragraph_type="bibliography"))
        if not bibliography:
            return lines, cites

        bib_items = bibliography.find_all("biblstruct")
        if not bib_items:
            return lines, cites

        # parse bibliography items
        for bib_item in bib_items:
            cites["#" + bib_item.get("xml:id")] = lines[-1].uid
            lines.append(self.__create_line(text="", hierarchy_level_id=2, paragraph_type="bibliography_item", other_fields={"uid": lines[-1].uid}))

            # parse bib title
            for title in bib_item.find_all("title", recursive=True):
                if title.get("level"):
                    paragraph_type = level_2_paragraph_type[title.get("level")]
                    lines.append(self.__create_line(text=self.__tag2text(title), hierarchy_level_id=3, paragraph_type=paragraph_type))

            lines += [  # parse bib authors
                self.__create_line(text=author.get_text(), hierarchy_level_id=3, paragraph_type="author")
                for author in bib_item.find_all("author", recursive=True) if author
            ]

            lines += [  # parse biblScope <biblScope unit="volume">
                self.__create_line(text=self.__tag2text(bibl_scope), hierarchy_level_id=3, paragraph_type="biblScope_volume")
                for bibl_scope in bib_item.find_all("biblscope", {"unit": "volume"}, recursive=True) if bibl_scope
            ]

            try:
                lines += [  # parse <biblScope unit="page"> values
                    self.__create_line(text=f"{bibl_scope.get('from')}-{bibl_scope.get('to')}", hierarchy_level_id=3, paragraph_type="biblScope_page")
                    for bibl_scope in bib_item.find_all("biblscope", {"unit": "page"}, recursive=True) if bibl_scope
                ]
            finally:
                self.logger.warning("Grobid parsing warning: <biblScope unit='page' ... /> was non-standard format")

            lines += [  # parse DOI (maybe more one)
                self.__create_line(text=self.__tag2text(idno), hierarchy_level_id=3, paragraph_type="DOI")
                for idno in bib_item.find_all("idno", recursive=True) if idno
            ]

            if bib_item.publisher:
                lines.append(self.__create_line(text=self.__tag2text(bib_item.publisher), hierarchy_level_id=3, paragraph_type="publisher"))

            if bib_item.date:
                lines.append(self.__create_line(text=self.__tag2text(bib_item.date), hierarchy_level_id=3, paragraph_type="date"))

        return lines, cites

    def __parse_title(self, soup: Tag) -> List[LineWithMeta]:
        return [self.__create_line(text=self.__tag2text(soup.title), hierarchy_level_id=0, paragraph_type="root")]

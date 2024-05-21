import math
import os
import time
import uuid
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import requests
from bs4 import BeautifulSoup, Tag
from pdf2image import convert_from_path

from dedoc.data_structures import Annotation, AttachAnnotation, AttachedFile, CellWithMeta, HierarchyLevel, LineMetadata, Table, TableAnnotation, TableMetadata
from dedoc.data_structures.concrete_annotations.reference_annotation import ReferenceAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.base_reader import BaseReader
from dedoc.structure_extractors.feature_extractors.list_features.list_utils import get_dotted_item_depth
from dedoc.utils.parameter_utils import get_param_attachments_dir, get_param_document_type, get_param_need_content_analysis, get_param_with_attachments


class ArticleReader(BaseReader):
    """
    This class is used for parsing scientific articles with .pdf extension using `GROBID <https://grobid.readthedocs.io/en/latest/>`_ system.
    """

    def __init__(self, config: Optional[dict] = None) -> None:
        super().__init__(config=config, recognized_extensions=recognized_extensions.pdf_like_format, recognized_mimes=recognized_mimes.pdf_like_format)
        grobid_url = os.environ.get("GROBID_URL", "")
        if grobid_url:
            self.grobid_url = grobid_url
        else:
            self.grobid_url = f"http://{os.environ.get('GROBID_HOST', 'localhost')}:{os.environ.get('GROBID_PORT', '8070')}"
        self.url = f"{self.grobid_url}/api/processFulltextDocument"
        self.grobid_is_alive = False

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method calls the service GROBID method ``/api/processFulltextDocument`` and analyzes the result (format XML/TEI) of the recognized article
        using beautifulsoup library.
        As a result, the method fills the class :class:`~dedoc.data_structures.UnstructuredDocument`.
        Article reader adds additional information to the `tag_hierarchy_level` of :class:`~dedoc.data_structures.LineMetadata`.
        The method extracts information about ``authors``, ``keywords``, ``bibliography items``, ``sections``, and ``tables``.
        In table cells, ``colspan`` attribute can be filled according to the GROBID's "cols" attribute.
        You can find more information about the extracted information from GROBID system on the page :ref:`article_structure`.

        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        with open(file_path, "rb") as file:
            files = {"input": file}
            try:
                response = requests.post(self.url, files=files, data={"teiCoordinates": "figure"})
                if response.status_code != 200:
                    warning = f"GROBID returns code {response.status_code}."
                    self.logger.warning(warning)
                    return UnstructuredDocument(tables=[], lines=[], attachments=[], warnings=[warning])
            except requests.exceptions.ConnectionError as ex:
                warning = f"GROBID doesn't response. Check GROBID service on {self.url}. Exception' msg: {ex}"
                self.logger.warning(warning)
                return UnstructuredDocument(tables=[], lines=[], attachments=[], warnings=[warning])

            soup = BeautifulSoup(response.text, features="xml")
            lines = self.__parse_title(soup)

            if soup.biblStruct is not None:
                authors = soup.biblStruct.find_all("author")
                lines += [line for author in authors for line in self.__parse_author(author)]
            lines += self.__parse_keywords(soup.keywords)

            bib_lines, bib2uid = self.__parse_bibliography(soup)
            tables, table2uid = self.__parse_tables(soup)
            attachments, attachment2uid = self.__parse_images(soup, file_path, parameters)

            lines += self.__parse_text(soup, bib2uid, table2uid, attachment2uid)
            lines.extend(bib_lines)

            return UnstructuredDocument(tables=tables, lines=lines, attachments=attachments, warnings=["use GROBID (version: 0.8.0)"])

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

        self.__update_grobid_alive(self.grobid_url, max_attempts=self.config.get("grobid_max_connection_attempts", 3))
        if not self.grobid_is_alive:
            return False

        return super().can_read(file_path=file_path, mime=mime, extension=extension)

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
                            metadata=LineMetadata(page_id=0, line_id=0, tag_hierarchy_level=hierarchy_level, **other_fields),
                            annotations=annotations)

    def __parse_affiliation(self, affiliation_tag: Tag) -> List[LineWithMeta]:
        lines = [self.__create_line(text=affiliation_tag.get("key"), hierarchy_level_id=2, paragraph_type="author_affiliation")]

        if affiliation_tag.orgName:
            lines.append(self.__create_line(text=self.__tag2text(affiliation_tag.orgName), hierarchy_level_id=3, paragraph_type="org_name"))

        if affiliation_tag.address:
            lines.append(self.__create_line(text=self.__remove_newlines(affiliation_tag.address).get_text(separator=", "),
                                            hierarchy_level_id=3,
                                            paragraph_type="address"))

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

        first_name = self.__get_tag_by_hierarchy_path(author_tag, ["persName", "forename"])
        if first_name:
            lines.append(self.__create_line(text=first_name, hierarchy_level_id=2, paragraph_type="author_first_name"))

        surname = self.__get_tag_by_hierarchy_path(author_tag, ["persName", "surname"])
        if surname:
            lines.append(self.__create_line(text=surname, hierarchy_level_id=2, paragraph_type="author_surname"))

        lines += [
            self.__create_line(text=email.get_text(), hierarchy_level_id=3, paragraph_type="email")
            for email in author_tag.find_all("email") if email
        ]

        affiliations = author_tag.find_all("affiliation")
        lines += [line for affiliation in affiliations for line in self.__parse_affiliation(affiliation)]

        return lines

    def __parse_keywords(self, keywords_tag: Tag) -> List[LineWithMeta]:
        """
        <keywords>
            <term>Multi-Object Tracking</term>
            <term>Data Association</term>
            <term>Survey</term>
        </keywords>
        """
        if keywords_tag is None:
            return []

        lines = [self.__create_line(text="", hierarchy_level_id=1, paragraph_type="keywords")]
        lines += [self.__create_line(text=item.text, hierarchy_level_id=2, paragraph_type="keyword") for item in keywords_tag.find_all("term")]
        return lines

    def __create_line_with_refs(self, content: List[Tuple[str, Tag]], bib2uid: dict, table2uid: dict, attachment2uid: dict) -> LineWithMeta:
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
                if subpart.get("type") == "figure" and target in attachment2uid:
                    annotations.append(AttachAnnotation(attach_uid=attachment2uid[target], start=start, end=start + len(sub_text)))
            else:
                sub_text = subpart if isinstance(subpart, str) else ""

            text += sub_text
            start += len(sub_text)

        return self.__create_line(text=text, hierarchy_level_id=None, paragraph_type=None, annotations=annotations)

    def __parse_text(self, soup: Tag, bib2uid: dict, table2uid: dict, attachment2uid: dict) -> List[LineWithMeta]:
        """
        Example of section XML tag:
        <div xmlns="http://www.tei-c.org/ns/1.0"><head n="4.1.1">Preprocessing</head><p>...</p><p>...</p></div>
        """
        lines = []

        abstract = soup.find("abstract").p
        lines.append(self.__create_line(text="Abstract", hierarchy_level_id=1, paragraph_type="abstract"))
        lines.append(self.__create_line(text=self.__tag2text(abstract)))

        for part in soup.body.find_all("div"):
            lines.extend(self.__parse_section(part, bib2uid, table2uid, attachment2uid))

        for other_text_type in ("acknowledgement", "annex"):
            for text_tag in soup.find_all("div", attrs={"type": other_text_type}):
                for part in text_tag.find_all("div"):
                    lines.extend(self.__parse_section(part, bib2uid, table2uid, attachment2uid))

        return lines

    def __parse_section(self, section_tag: Tag, bib2uid: dict, table2uid: dict, attachment2uid: dict) -> List[LineWithMeta]:
        lines = []
        number = section_tag.head.get("n") if section_tag.head else ""
        number = number + " " if number else ""
        section_depth = get_dotted_item_depth(number)
        section_depth = section_depth if section_depth > 0 else 1

        line_text = section_tag.head.string if section_tag.head else None
        if line_text is not None and len(line_text) > 0:
            lines.append(self.__create_line(text=number + line_text, hierarchy_level_id=section_depth, paragraph_type="section"))
        for subpart in section_tag.find_all("p"):
            if subpart.string is not None:
                lines.append(self.__create_line_with_refs(subpart.string + "\n", bib2uid, table2uid, attachment2uid))
            elif subpart.contents and len(subpart.contents) > 0:
                lines.append(self.__create_line_with_refs(subpart.contents, bib2uid, table2uid, attachment2uid))

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
            table_cells = []
            head = table.contents[0] if len(table.contents) > 0 and isinstance(table.contents[0], str) else self.__tag2text(table.head)
            title = head + self.__tag2text(table.figDesc)
            for row in table.table.find_all("row"):
                row_cells = []
                for cell in row.find_all("cell"):
                    cell_text = self.__create_line(self.__tag2text(cell))
                    colspan = int(cell.get("cols", 1))
                    row_cells.append(CellWithMeta(lines=[cell_text], colspan=colspan))

                    if colspan > 1:
                        row_cells.extend([CellWithMeta(lines=[cell_text], invisible=True) for _ in range(colspan - 1)])

                table_cells.append(row_cells)

            # ignore empty tables
            if len(table_cells) == 0:
                continue

            tables.append(Table(cells=table_cells, metadata=TableMetadata(page_id=0, title=title)))
            table2uid[f'#{table.get("xml:id")}'] = tables[-1].metadata.uid

        return tables, table2uid

    def __parse_images(self, soup: Tag, file_path: str, parameters: Optional[dict]) -> Tuple[List[AttachedFile], dict]:
        """
        Example Figure with figure's ref:
        -----------------------------------------------
            Figure Reference Example:
                <ref type="figure" coords="2,444.07,632.21,4.98,8.74" target="#fig_0">1</ref>
            Figure Example:
                <figure
                    xmlns="http://www.tei-c.org/ns/1.0" xml:id="fig_0" coords="3,151.56,211.52,312.23,7.89;3,136.68,115.84,338.92,75.24">
                    <head>Fig. 1 .</head>
                    <label>1</label>
                    <figDesc>Fig. 1. Stateful leakage-resilient PRG with N = 2 (left) and N = 256 (right).</figDesc>
                    <graphic coords="3,136.68,115.84,338.92,75.24" type="bitmap"/>
                </figure>
            List of PDF page sizes:
                <facsimile>
                    <surface n="1" ulx="0.0" uly="0.0" lrx="612.0" lry="792.0"/>
                    <surface n="2" ulx="0.0" uly="0.0" lrx="612.0" lry="792.0"/>
                </facsimile>
        Documentation: https://grobid.readthedocs.io/en/latest/Coordinates-in-PDF/
        """
        if not get_param_with_attachments(parameters):
            return [], {}

        attachments_dir = get_param_attachments_dir(parameters, file_path)
        need_content_analysis = get_param_need_content_analysis(parameters)
        try:
            page_sizes = [(float(item["lrx"]), float(item["lry"])) for item in soup.facsimile.find_all("surface")]
        except Exception as e:
            self.logger.warning(f"Exception {e} during attached images handling")
            return [], {}

        attachments, attachment2uid = [], {}
        figure_tags = soup.find_all("figure", {"type": None})
        for figure_tag in figure_tags:
            try:
                cropped = self.__get_image(figure_tag, file_path, page_sizes)
                if cropped is None:
                    continue

                uid = f"fig_{uuid.uuid1()}"
                file_name = f"{uid}.png"
                attachment_path = os.path.join(attachments_dir, file_name)
                cv2.imwrite(attachment_path, cropped)
                attachments.append(AttachedFile(original_name=file_name, tmp_file_path=attachment_path, need_content_analysis=need_content_analysis, uid=uid))
                attachment2uid[f'#{figure_tag.get("xml:id")}'] = attachments[-1].uid
            except Exception as e:
                self.logger.warning(f"Exception {e} during figure tag handling:\n{figure_tag}")

        return attachments, attachment2uid

    def __get_image(self, figure_tag: Tag, file_path: str, page_sizes: List[Tuple[float, float]]) -> Optional[np.ndarray]:
        """
        Crop the PDF page according to the figure's coordinates.
        Figure can consist of multiple sub-figures: we crop the union of all sub-figures.
        Example of the figure's coordinates: coords="3,151.56,211.52,312.23,7.89;3,136.68,115.84,338.92,75.24"
        """
        if figure_tag.graphic is None:
            return None

        coords_list = figure_tag["coords"].split(";")
        prev_page_number, page_image = None, None
        x_min, x_max, y_min, y_max = np.inf, 0, np.inf, 0

        for coords_text in coords_list:
            # coords=[p, y, x, h, w], where p - page number, (x, y) - upper-left point, h - height, w - width
            coords = coords_text.split(",")
            page_number = int(coords[0])

            if prev_page_number is None:
                prev_page_number = page_number
                page_image = np.array(convert_from_path(file_path, first_page=page_number, last_page=page_number)[0])

            if page_number != prev_page_number:
                self.logger.warning("The figure is located on several pages: handle only the first page (we don't handle multi-page images)")
                break

            coords = [float(i) for i in coords[1:]]
            page_size = page_sizes[page_number - 1]
            actual_page_size = page_image.shape[1], page_image.shape[0]
            coords = [
                coords[0] / page_size[0] * actual_page_size[0], coords[1] / page_size[1] * actual_page_size[1],
                coords[2] / page_size[0] * actual_page_size[0], coords[3] / page_size[1] * actual_page_size[1]
            ]
            y, x, h, w = coords[0], coords[1], coords[2], coords[3]
            x1, x2, y1, y2 = math.floor(x), math.ceil(x + w), math.floor(y), math.ceil(y + h)
            x_min, x_max, y_min, y_max = min(x_min, x1), max(x_max, x2), min(y_min, y1), max(y_max, y2)

        cropped = page_image[x_min:x_max, y_min:y_max]
        return cropped

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

        bibliography = soup.find("listBibl", recursive=True)
        lines.append(self.__create_line(text="bibliography", hierarchy_level_id=1, paragraph_type="bibliography"))
        if not bibliography:
            return lines, cites

        bib_items = bibliography.find_all("biblStruct")
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
                self.__create_line(text=self.__remove_newlines(author).get_text(separator=" "), hierarchy_level_id=3, paragraph_type="author")
                for author in bib_item.find_all("author", recursive=True) if author
            ]

            lines += [  # parse biblScope <biblScope unit="volume">
                self.__create_line(text=self.__tag2text(bibl_scope), hierarchy_level_id=3, paragraph_type="biblScope_volume")
                for bibl_scope in bib_item.find_all("biblScope", {"unit": "volume"}, recursive=True) if bibl_scope
            ]

            try:
                lines += [  # parse <biblScope unit="page"> values
                    self.__create_line(text=f"{bibl_scope.get('from')}-{bibl_scope.get('to')}", hierarchy_level_id=3, paragraph_type="biblScope_page")
                    for bibl_scope in bib_item.find_all("biblScope", {"unit": "page"}, recursive=True) if bibl_scope
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

    def __remove_newlines(self, tag: Tag) -> Tag:
        for item in tag:
            if not isinstance(item, Tag):
                item.extract()
        return tag

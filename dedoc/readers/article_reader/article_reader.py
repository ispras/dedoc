from typing import List, Optional, Tuple

import requests
from bs4 import BeautifulSoup, Tag

from dedoc.data_structures import Annotation, HierarchyLevel, LineMetadata
from dedoc.data_structures.concrete_annotations.bibliography_annotation import BibliographyAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_mimes
from dedoc.readers.base_reader import BaseReader
from dedoc.utils.utils import get_mime_extension


class ArticleReader(BaseReader):

    def __init__(self, config: dict, grobid_url: str) -> None:
        super().__init__()
        self.url = grobid_url
        self.config = config

    @staticmethod
    def __get_tag_by_hierarchy_path(source: Tag, hierarchy_path: List[str]) -> Optional[str]:
        cur_tag = source
        for path_item in hierarchy_path:
            cur_tag = cur_tag.find(path_item)
            if cur_tag is None:
                # tag not found
                return ""

        return cur_tag.string if cur_tag.string is not None else ""

    def __get_all_tags(self, source: Tag, tag: str) -> List[Tag]:
        return source.find_all(tag)

    @staticmethod  # TODO check on improve
    def __create_line(text: str, hierarchy_level_id: Optional[int], paragraph_type: Optional[str],
                      annotations: Optional[List[Annotation]] = None) -> LineWithMeta:
        assert text is not None
        assert isinstance(text, str)

        if hierarchy_level_id is None:
            hierarchy_level = HierarchyLevel.create_raw_text()
            metadata = LineMetadata(page_id=0, line_id=0, tag_hierarchy_level=hierarchy_level)
        else:
            hierarchy_level = HierarchyLevel(level_1=hierarchy_level_id, level_2=0, can_be_multiline=False, line_type=paragraph_type)
            metadata = LineMetadata(page_id=0, line_id=0, tag_hierarchy_level=hierarchy_level)

        return LineWithMeta(line=text, metadata=metadata, annotations=annotations)

    def __parse_affiliation(self, affiliation_tag: Tag) -> List[LineWithMeta]:
        lines = [self.__create_line(text=affiliation_tag.get("key"), hierarchy_level_id=2, paragraph_type="author_affiliation")]

        org_name = ArticleReader.__get_tag_by_hierarchy_path(affiliation_tag, ["orgname"])
        if org_name:
            lines.append(self.__create_line(text=org_name, hierarchy_level_id=3, paragraph_type="org_name"))

        # TODO add org's address
        """org_name = ArticleReader.__get_tag_by_hierarchy_path(affiliation_tag, ["address"])
        if org_name:
            lines.append(self.__create_line(text=org_name, hierarchy_level_id=4, paragraph_type="org_name"))"""

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
        first_name = ArticleReader.__get_tag_by_hierarchy_path(author_tag, ["persname", "forename"])
        if first_name:
            lines.append(self.__create_line(text=first_name, hierarchy_level_id=2, paragraph_type="author_first_name"))

        surname = ArticleReader.__get_tag_by_hierarchy_path(author_tag, ["persname", "surname"])
        if surname:
            lines.append(self.__create_line(text=surname, hierarchy_level_id=2, paragraph_type="author_surname"))

        email = ArticleReader.__get_tag_by_hierarchy_path(author_tag, ["email"])
        if len(email) > 0:
            lines.append(self.__create_line(text=email, hierarchy_level_id=2, paragraph_type="author_email"))

        affiliations = author_tag.find_all("affiliation")
        lines += [line for affiliation in affiliations for line in self.__parse_affiliation(affiliation)]

        return lines

    def __create_line_with_text_links(self, subparts: List[Tuple[str, Tag]], bib_cites: dict) -> LineWithMeta:
        subpart_text = ""
        start = 0
        text_link_annotations = []

        for subsubpart in subparts:
            if isinstance(subsubpart, str):
                subpart_text += subsubpart
                start += len(subsubpart)
            elif isinstance(subsubpart, Tag):
                if subsubpart.name == "ref" and subsubpart.get("type") == "bibr":
                    target = subsubpart.get("target")
                    value = subsubpart.string
                    if target in bib_cites:
                        text_link_annotations.append(BibliographyAnnotation(bib_cites[target], start, start + len(value)))
                    subpart_text += value
                    start += len(value)

        return self.__create_line(text=subpart_text, hierarchy_level_id=None, paragraph_type=None, annotations=text_link_annotations)

    def __parse_text(self, soup: Tag, bib_cites: dict) -> List[LineWithMeta]:
        lines = []

        abstract = soup.find("abstract").p
        abstract = "" if abstract is None or abstract.string is None else abstract.string
        lines.append(self.__create_line(text=abstract, hierarchy_level_id=1, paragraph_type="abstract"))

        for text in soup.find_all("text"):
            for part in text.find_all("div"):
                line_text = str(part.contents[0]) if len(part.contents) > 0 else None
                if line_text is not None and len(line_text) > 0:
                    lines.append(self.__create_line(text=line_text, hierarchy_level_id=1, paragraph_type="section"))
                for subpart in part.find_all("p"):
                    if subpart.string is not None:
                        lines.append(self.__create_line_with_text_links(subpart.string, bib_cites))
                    else:
                        if subpart.contents and len(subpart.contents) > 0:
                            lines.append(self.__create_line_with_text_links(subpart.contents, bib_cites))

        return lines

    def __tag_2_text(self, tag: Tag) -> str:
        return "" if not tag or not tag.string else tag.string

    def __parse_bibliography(self, soup: Tag) -> Tuple[List[LineWithMeta], dict]:
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
            lines.append(self.__create_line(text=lines[-1].uid, hierarchy_level_id=2, paragraph_type="bibliography_item"))

            # parse bib title
            for title in bib_item.find_all("title", recursive=True):
                paragraph_type = level_2_paragraph_type[title.get("level")]
                lines.append(self.__create_line(text=self.__tag_2_text(title), hierarchy_level_id=3, paragraph_type=paragraph_type))

            lines += [  # parse bib authors
                self.__create_line(text=author.get_text(), hierarchy_level_id=3, paragraph_type="author")
                for author in bib_item.find_all("author", recursive=True) if author
            ]

            lines += [  # parse biblScope <biblScope unit="volume">
                self.__create_line(text=self.__tag_2_text(bibl_scope), hierarchy_level_id=3, paragraph_type="biblScope_volume")
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
                self.__create_line(text=self.__tag_2_text(idno), hierarchy_level_id=3, paragraph_type="DOI")
                for idno in bib_item.find_all("idno", recursive=True) if idno
            ]

            publisher = bib_item.find("publisher")
            if publisher:
                lines.append(self.__create_line(text=self.__tag_2_text(publisher), hierarchy_level_id=3, paragraph_type="publisher"))

            date = bib_item.find("date")
            if date:
                lines.append(self.__create_line(text=self.__tag_2_text(date), hierarchy_level_id=3, paragraph_type="date"))

        return lines, cites

    def __parse_title(self, soup: Tag) -> List[LineWithMeta]:
        title = soup.title.string if soup.title is not None and soup.title.string is not None else ""
        return [self.__create_line(text=title, hierarchy_level_id=0, paragraph_type="root")]

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        with open(file_path, "rb") as file:
            files = {"input": file}
            response = requests.post(self.url, files=files)

            soup = BeautifulSoup(response.text, features="lxml")
            lines = self.__parse_title(soup)

            if soup.biblstruct is not None:
                authors = soup.biblstruct.find_all("author")
                lines += [line for author in authors for line in self.__parse_author(author)]

            bib_lines, bib_cites = self.__parse_bibliography(soup)

            lines += self.__parse_text(soup, bib_cites)
            lines.extend(bib_lines)

            return UnstructuredDocument(tables=[], lines=lines, attachments=[])

    def can_read(self, file_path: Optional[str] = None, mime: Optional[str] = None, extension: Optional[str] = None, parameters: Optional[dict] = None) -> bool:

        extension, mime = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        if not (mime in recognized_mimes.pdf_like_format or extension.lower() == ".pdf"):
            return False

        parameters = {} if parameters is None else parameters
        return parameters.get("document_type", "") == "article"


"""
LinkedTextAnnotation:
    -----------------------------------------------
    Table Reference Example:
    <ref type="table" target="#tab_0">1</ref>
    ...
    Table Example:
    '<figure xmlns="http://www.tei-c.org/ns/1.0" type="table" xml:id="tab_0">' \
    '<head>Table 1 .</head>'
    '<label>1</label>'
    '<figDesc>Performance of some illustrative AES implementations.</figDesc>'
    '<table>'
    '<row><cell>Software (8-bit)</cell><cell>code size</cell><cell>cycle</cell><cell>cost</cell><cell>physical</cell></row>'
    '<row><cell>Implementations</cell><cell>(bytes)</cell><cell>count</cell><cell>function</cell><cell>assumptions</cell></row>'
    '<row><cell>Unprotected [13]</cell><cell>1659</cell><cell>4557</cell><cell>7.560</cell><cell>-</cell></row>'
    '<row><cell>1-mask Boolean [53]</cell><cell>3153</cell><cell>129 • 10 3</cell><cell>406.7</cell><cell>glitch-sensitive</cell></row>'
    '<row><cell>1-mask polynomial [20, 45]</cell><cell>20 682</cell><cell>1064 • 10 3</cell><cell>22 000</cell><cell>glitch-resistant</cell></row>'
    '<row><cell>2-mask Boolean [53]</cell><cell>3845</cell><cell>271 • 10 3</cell><cell>1042</cell><cell>glitch-sensitive</cell></row>'
    '<row><cell>FPGA (Virtex-5)</cell><cell>area</cell><cell>throughput</cell><cell>cost</cell><cell>physical</cell></row>'
    '<row><cell>Implementations</cell><cell>(slices)</cell><cell>(enc/sec)</cell><cell>function</cell><cell>assumptions</cell></row>'
    '<row><cell>Unprotected (128-bit) [48] 1-mask Boolean (128-bit) [48] Threshold (8-bit) [36]</cell><cell>478 1462 958</cell>
          <cell>245•10 6 11 100•10 6 11 170•10 6 266</cell><cell>21.46 160.8 1499</cell><cell>-glitch-sensitive glitch-resistant</cell></row>'
    </table>
    </figure>
    -----------------------------------------------
    Figure Reference Example:
    <ref type="figure" target="#fig_12">13</ref>
    ...
    Figure Example:
    '<figure xmlns="http://www.tei-c.org/ns/1.0" xml:id="fig_12">
    <head>Fig. 13 .</head>F
    <label>13</label>
    <figDesc>Fig. 13. DPA-based security graphs for KHT * 2 /f =1 (left) and repeating attacks (right).</figDesc>
    <graphic coords="24,131.14,538.99,181.26,103.17" type="bitmap" />
    </figure>
     -----------------------------------------------
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

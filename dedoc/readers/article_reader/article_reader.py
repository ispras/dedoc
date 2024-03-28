from typing import List, Optional

import requests
from bs4 import BeautifulSoup, Tag

from dedoc.data_structures import HierarchyLevel, LineMetadata
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
    def __get_tag(source: Tag, tags: List[str]) -> Optional[str]:
        cur_tag = source
        for tag_name in tags:
            cur_tag = cur_tag.find(tag_name)
            if cur_tag is None:
                return ""
        return cur_tag.string if cur_tag.string is not None else ""

    @staticmethod
    def __create_line(text: str, hierarchy_level_id: Optional[int], paragraph_type: Optional[str]) -> LineWithMeta:
        assert text is not None
        assert isinstance(text, str)

        if hierarchy_level_id is None:
            hierarchy_level = HierarchyLevel.create_raw_text()
            metadata = LineMetadata(page_id=0, line_id=0, tag_hierarchy_level=hierarchy_level)
        else:
            hierarchy_level = HierarchyLevel(level_1=hierarchy_level_id, level_2=0, can_be_multiline=False, line_type=paragraph_type)
            metadata = LineMetadata(page_id=0, line_id=0, tag_hierarchy_level=hierarchy_level)

        return LineWithMeta(line=text, metadata=metadata)

    def parse_author(self, author_tag: Tag) -> List[LineWithMeta]:
        res = []
        res.append(self.__create_line(text="", hierarchy_level_id=1, paragraph_type="author"))

        first_name = ArticleReader.__get_tag(author_tag, ["persname", "forename"])
        if first_name:
            res.append(self.__create_line(text=first_name, hierarchy_level_id=2, paragraph_type="author_first_name"))

        surname = ArticleReader.__get_tag(author_tag, ["persname", "surname"])
        if surname:
            res.append(self.__create_line(text=surname, hierarchy_level_id=2, paragraph_type="author_surname"))

        email = ArticleReader.__get_tag(author_tag, ["email"])
        if len(email) > 0:
            res.append(self.__create_line(text=email, hierarchy_level_id=2, paragraph_type="author_email"))
        return res

    def _parse_text(self, soup: Tag) -> List[LineWithMeta]:
        lines = []

        abstract = soup.find("abstract").p
        abstract = "" if abstract is None or abstract.string is None else abstract.string
        lines.append(self.__create_line(text=abstract, hierarchy_level_id=1, paragraph_type="abstract"))

        for text in soup.find_all("text"):
            for part in text.find_all("div"):
                line_text = str(part.contents[0]) if len(part.contents) > 0 else None
                if line_text is not None and len(line_text) > 0:
                    lines.append(self.__create_line(text=line_text,
                                                    hierarchy_level_id=1,
                                                    paragraph_type="section"))
                for subpart in part.find_all("p"):
                    if subpart.string is not None:
                        lines.append(self.__create_line(text=subpart.string,
                                                        hierarchy_level_id=None,
                                                        paragraph_type=None))
                    else:
                        if subpart.contents and len(subpart.contents) > 0:
                            subpart_text = ""
                            for subsubpart in subpart.contents:
                                if isinstance(subsubpart, str):
                                    subpart_text += subsubpart
                            lines.append(self.__create_line(text=subpart_text,
                                                            hierarchy_level_id=None,
                                                            paragraph_type=None))

        return lines

    def _parse_title(self, soup: Tag) -> List[LineWithMeta]:
        title = soup.title.string if soup.title is not None and soup.title.string is not None else ""
        return [self.__create_line(text=title, hierarchy_level_id=0, paragraph_type="root")]

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        with open(file_path, "rb") as file:
            files = {"input": file}
            response = requests.post(self.url, files=files)

            soup = BeautifulSoup(response.text, features="lxml")

            lines = self._parse_title(soup)

            if soup.biblstruct is not None:
                authors = soup.biblstruct.find_all("author")
                lines += [line for author in authors for line in self.parse_author(author)]

            lines += self._parse_text(soup)

            return UnstructuredDocument(tables=[], lines=lines, attachments=[])

    def can_read(self, file_path: Optional[str] = None, mime: Optional[str] = None, extension: Optional[str] = None, parameters: Optional[dict] = None) -> bool:

        extension, mime = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        if not (mime in recognized_mimes.pdf_like_format or extension.lower() == ".pdf"):
            return False

        parameters = {} if parameters is None else parameters
        return parameters.get("document_type", "") == "article"

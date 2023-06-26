import hashlib
import logging
import os
import re
import zipfile
from collections import defaultdict
from typing import Optional, List

from bs4 import BeautifulSoup, Tag

from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.data_structures.concrete_annotations.attach_annotation import AttachAnnotation
from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.docx_reader.line_with_meta_converter import LineWithMetaConverter
from dedoc.readers.docx_reader.data_structures.paragraph import Paragraph
from dedoc.readers.docx_reader.data_structures.table import DocxTable
from dedoc.readers.docx_reader.data_structures.utils import Counter
from dedoc.readers.docx_reader.footnote_extractor import FootnoteExtractor
from dedoc.readers.docx_reader.numbering_extractor import NumberingExtractor
from dedoc.readers.docx_reader.styles_extractor import StylesExtractor
from dedoc.utils.utils import calculate_file_hash


class DocxDocument:
    def __init__(self, path: str, logger: logging.Logger) -> None:
        self.logger = logger
        self.path = path
        self.path_hash = calculate_file_hash(path=path)

        self.document_bs_tree = self.__get_bs_tree('word/document.xml')
        if self.document_bs_tree is None:
            self.document_bs_tree = self.__get_bs_tree('word/document2.xml')
        self.body = self.document_bs_tree.body if self.document_bs_tree else None

        self.footnote_extractor = FootnoteExtractor(self.__get_bs_tree('word/footnotes.xml'))
        self.endnote_extractor = FootnoteExtractor(self.__get_bs_tree('word/endnotes.xml'), key="endnote")
        self.styles_extractor = StylesExtractor(self.__get_bs_tree('word/styles.xml'), logger)
        num_tree = self.__get_bs_tree('word/numbering.xml')
        self.numbering_extractor = NumberingExtractor(num_tree, self.styles_extractor) if num_tree else None
        self.styles_extractor.numbering_extractor = self.numbering_extractor

        self.table_ref_reg = re.compile(r"^[Тт](аблица|абл?\.) ")
        self.tables = []
        self.paragraph_list = []
        self.lines = self.__get_lines(logger=logger)

    def __get_lines(self, logger: logging.Logger) -> List[LineWithMeta]:
        """
        Get list of LineWithMeta with annotations, references to the images, diagrams and tables.
        Fill tables if they exist in the document.
        1. Get paragraphs in the inner representation, tables, images and diagrams.
        2. Convert paragraphs into list with LineWithMeta with annotations

        :return: list of document lines with annotations
        """
        # { paragraph index in paragraph_list : list of uids }
        table_refs, image_refs, diagram_refs = defaultdict(list), defaultdict(list), defaultdict(list)
        cnt = Counter(self.body, logger)
        uids_set = set()

        for paragraph_xml in self.body:
            if not isinstance(paragraph_xml, Tag):
                continue

            if paragraph_xml.name == 'tbl':
                self.__handle_table_xml(paragraph_xml, table_refs, uids_set, cnt)
                continue

            if paragraph_xml.pict:  # diagrams are saved using docx_attachments_extractor
                self.__handle_diagrams_xml(paragraph_xml, diagram_refs, uids_set, cnt)
                continue

            if paragraph_xml.name != 'p':
                for subparagraph_xml in paragraph_xml.find_all('w:p'):  # TODO check what to add
                    paragraph = self.__xml2paragraph(subparagraph_xml, uids_set, cnt)
                    self.paragraph_list.append(paragraph)
                continue

            self.paragraph_list.append(self.__xml2paragraph(paragraph_xml, uids_set, cnt))
            images = paragraph_xml.find_all('pic:pic')
            if images:
                self.__handle_images_xml(images, image_refs, uids_set, cnt)

        return self.__paragraphs2lines(image_refs, table_refs, diagram_refs)

    def __paragraphs2lines(self, image_refs: dict, table_refs: dict, diagram_refs: dict) -> List[LineWithMeta]:
        """
        Convert list of paragraphs into list of LineWithMeta.
        Add all annotations to the lines.
        :return: list of LineWithMeta
        """
        lines_with_meta = []
        paragraph_id = 0

        for i, paragraph in enumerate(self.paragraph_list):
            line = LineWithMetaConverter(paragraph, paragraph_id).line

            for object_dict in [image_refs, diagram_refs]:
                if i in object_dict:
                    for object_uid in object_dict[i]:
                        annotation = AttachAnnotation(attach_uid=object_uid, start=0, end=len(line))
                        line.annotations.append(annotation)

            if i in table_refs:
                for table_uid in table_refs[i]:
                    annotation = TableAnnotation(name=table_uid, start=0, end=len(line))
                    line.annotations.append(annotation)

            paragraph_id += 1
            lines_with_meta.append(line)

        return lines_with_meta

    def __get_bs_tree(self, filename: str) -> Optional[BeautifulSoup]:
        """
        Gets xml bs tree from the given file inside the self.path.
        :param filename: name of file to extract the tree
        :return: BeautifulSoup tree or None if file wasn't found
        """
        try:
            with zipfile.ZipFile(self.path) as document:
                content = document.read(filename)
                content = re.sub(br"\n[\t ]*", b"", content)
                soup = BeautifulSoup(content, 'xml')
                return soup
        except KeyError:
            return None
        except zipfile.BadZipFile:
            raise BadFileFormatException("Bad docx file:\n file_name = {}. Seems docx is broken".format(os.path.basename(self.path)))

    def __xml2paragraph(self, paragraph_xml: Tag, uids_set: set, cnt: Counter) -> Paragraph:
        uid = self.__get_paragraph_uid(paragraph_xml=paragraph_xml, uids_set=uids_set)
        paragraph = Paragraph(xml=paragraph_xml,
                              styles_extractor=self.styles_extractor,
                              numbering_extractor=self.numbering_extractor,
                              footnote_extractor=self.footnote_extractor,
                              endnote_extractor=self.endnote_extractor,
                              uid=uid)
        prev_paragraph = None if len(self.paragraph_list) == 0 else self.paragraph_list[-1]
        paragraph.spacing = paragraph.spacing_before if prev_paragraph is None else max(prev_paragraph.spacing_after, paragraph.spacing_before)
        cnt.inc()
        return paragraph

    def __get_paragraph_uid(self, paragraph_xml: Tag, uids_set: set) -> str:
        xml_hash = hashlib.md5(paragraph_xml.encode()).hexdigest()
        raw_uid = '{}_{}'.format(self.path_hash, xml_hash)
        uid = raw_uid
        n = 0
        while uid in uids_set:
            n += 1
            uid = raw_uid + "_{}".format(n)
        uids_set.add(uid)
        return uid

    def __handle_table_xml(self, xml: Tag, table_refs: dict, uids_set: set, cnt: Counter) -> None:
        table = DocxTable(xml, self.styles_extractor)
        self.tables.append(table.to_table())
        table_uid = table.uid

        self.__prepare_paragraph_list(uids_set, cnt)

        if len(self.paragraph_list) >= 2 and self.table_ref_reg.match(self.paragraph_list[-2].text):
            table_refs[len(self.paragraph_list) - 2].append(table_uid)
        else:
            table_refs[len(self.paragraph_list) - 1].append(table_uid)

    def __handle_images_xml(self, xmls: List[Tag], image_refs: dict, uids_set: set, cnt: Counter) -> None:
        rels = self.__get_bs_tree('word/_rels/document.xml.rels')
        if rels is None:
            rels = self.__get_bs_tree('word/_rels/document2.xml.rels')

        images_rels = dict()
        for rel in rels.find_all('Relationship'):
            if rel["Target"].startswith('media/'):
                images_rels[rel["Id"]] = rel["Target"][6:]

        self.__prepare_paragraph_list(uids_set, cnt)

        for image_xml in xmls:
            blips = image_xml.find_all("a:blip")
            image_uid = images_rels[blips[0]["r:embed"]]
            image_refs[len(self.paragraph_list) - 1].append(image_uid)

    def __handle_diagrams_xml(self, xml: Tag, diagram_refs: dict, uids_set: set, cnt: Counter) -> None:
        diagram_uid = hashlib.md5(xml.encode()).hexdigest()
        self.__prepare_paragraph_list(uids_set, cnt)
        diagram_refs[len(self.paragraph_list) - 1].append(diagram_uid)

    def __prepare_paragraph_list(self, uids_set: set, cnt: Counter) -> None:
        while len(self.paragraph_list) > 0:
            if self.paragraph_list[-1].text.strip() == "":
                self.paragraph_list.pop()
            else:
                break

        if not self.paragraph_list:
            empty_paragraph = self.__xml2paragraph(BeautifulSoup('<w:p></w:p>').body.contents[0], uids_set, cnt)
            self.paragraph_list.append(empty_paragraph)

import hashlib
import logging
import os
import re
import zipfile
from collections import defaultdict
from typing import List, Optional

from bs4 import BeautifulSoup, Tag

from dedoc.common.exceptions.bad_file_error import BadFileFormatError
from dedoc.data_structures.attached_file import AttachedFile
from dedoc.data_structures.concrete_annotations.attach_annotation import AttachAnnotation
from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.docx_reader.data_structures.table import DocxTable
from dedoc.readers.docx_reader.data_structures.utils import Counter, ParagraphMaker
from dedoc.readers.docx_reader.footnote_extractor import FootnoteExtractor
from dedoc.readers.docx_reader.line_with_meta_converter import LineWithMetaConverter
from dedoc.readers.docx_reader.numbering_extractor import NumberingExtractor
from dedoc.readers.docx_reader.styles_extractor import StylesExtractor
from dedoc.utils.utils import calculate_file_hash


class DocxDocument:
    def __init__(self, path: str, attachments: List[AttachedFile], logger: logging.Logger) -> None:
        self.logger = logger
        self.path = path
        self.attachment_name2uid = {attachment.original_name: attachment.uid for attachment in attachments}

        self.document_bs_tree = self.__get_bs_tree("word/document.xml")
        self.document_bs_tree = self.__get_bs_tree("word/document2.xml") if self.document_bs_tree is None else self.document_bs_tree
        self.body = self.document_bs_tree.body if self.document_bs_tree else None
        self.paragraph_maker = self.__get_paragraph_maker()

        self.table_ref_reg = re.compile(r"^[Тт](аблица|абл?\.) ")
        self.tables = []
        self.paragraph_list = []
        self.lines = self.__get_lines()

    def __get_paragraph_maker(self) -> ParagraphMaker:
        styles_extractor = StylesExtractor(self.__get_bs_tree("word/styles.xml"), self.logger)
        num_tree = self.__get_bs_tree("word/numbering.xml")
        numbering_extractor = NumberingExtractor(num_tree, styles_extractor) if num_tree else None
        styles_extractor.numbering_extractor = numbering_extractor

        return ParagraphMaker(
            counter=Counter(self.body, self.logger),
            path_hash=calculate_file_hash(path=self.path),
            styles_extractor=styles_extractor,
            numbering_extractor=numbering_extractor,
            footnote_extractor=FootnoteExtractor(self.__get_bs_tree("word/footnotes.xml")),
            endnote_extractor=FootnoteExtractor(self.__get_bs_tree("word/endnotes.xml"), key="endnote")
        )

    def __get_lines(self) -> List[LineWithMeta]:
        """
        Get list of LineWithMeta with annotations, references to the images, diagrams and tables.
        Fill tables if they exist in the document.
        1. Get paragraphs in the inner representation, tables, images and diagrams.
        2. Convert paragraphs into list with LineWithMeta with annotations

        :return: list of document lines with annotations
        """
        # { paragraph index in paragraph_list : list of uids }
        table_refs, image_refs, diagram_refs = defaultdict(list), defaultdict(list), defaultdict(list)

        for paragraph_xml in self.body:
            if not isinstance(paragraph_xml, Tag):
                continue

            if paragraph_xml.name == "tbl":
                self.__handle_table_xml(paragraph_xml, table_refs)
                continue

            if self.attachment_name2uid and paragraph_xml.pict:  # diagrams are saved using docx_attachments_extractor
                self.__handle_diagram_xml(paragraph_xml, diagram_refs)
                continue

            if paragraph_xml.name != "p":
                for subparagraph_xml in paragraph_xml.find_all("w:p"):  # TODO check what to add
                    paragraph = self.paragraph_maker.make_paragraph(subparagraph_xml, self.paragraph_list)
                    self.paragraph_list.append(paragraph)
                continue

            self.paragraph_list.append(self.paragraph_maker.make_paragraph(paragraph_xml, self.paragraph_list))

            if self.attachment_name2uid:
                images = paragraph_xml.find_all("pic:pic")
                if images:
                    self.__handle_images_xml(images, image_refs)

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
                soup = BeautifulSoup(content, "xml")
                return soup
        except KeyError:
            return None
        except zipfile.BadZipFile:
            raise BadFileFormatError(f"Bad docx file:\n file_name = {os.path.basename(self.path)}. Seems docx is broken")

    def __handle_table_xml(self, xml: Tag, table_refs: dict) -> None:
        table = DocxTable(xml, self.paragraph_maker)
        self.tables.append(table.to_table())
        table_uid = table.uid

        self.__prepare_paragraph_list()

        if len(self.paragraph_list) >= 2 and self.table_ref_reg.match(self.paragraph_list[-2].text):
            table_refs[len(self.paragraph_list) - 2].append(table_uid)
        else:
            table_refs[len(self.paragraph_list) - 1].append(table_uid)

    def __handle_images_xml(self, xmls: List[Tag], image_refs: dict) -> None:
        rels = self.__get_bs_tree("word/_rels/document.xml.rels")
        if rels is None:
            rels = self.__get_bs_tree("word/_rels/document2.xml.rels")

        images_rels = dict()
        for rel in rels.find_all("Relationship"):
            if rel["Target"].startswith("media/"):
                images_rels[rel["Id"]] = rel["Target"][6:]

        self.__prepare_paragraph_list()

        for image_xml in xmls:
            blips = image_xml.find_all("a:blip")
            image_name = images_rels[blips[0]["r:embed"]]

            if image_name in self.attachment_name2uid:
                image_uid = self.attachment_name2uid[image_name]
            else:
                self.logger.info(f"Attachment with name {image_name} not found")
                continue
            image_refs[len(self.paragraph_list) - 1].append(image_uid)

    def __handle_diagram_xml(self, xml: Tag, diagram_refs: dict) -> None:
        diagram_name = f"{hashlib.md5(xml.encode()).hexdigest()}.docx"
        if diagram_name in self.attachment_name2uid:
            diagram_uid = self.attachment_name2uid[diagram_name]
        else:
            self.logger.info(f"Attachment with name {diagram_name} not found")
            return
        self.__prepare_paragraph_list()
        diagram_refs[len(self.paragraph_list) - 1].append(diagram_uid)

    def __prepare_paragraph_list(self) -> None:
        while len(self.paragraph_list) > 0:
            if self.paragraph_list[-1].text.strip() == "":
                self.paragraph_list.pop()
            else:
                break

        if not self.paragraph_list:
            empty_paragraph = self.paragraph_maker.make_paragraph(BeautifulSoup("<w:p></w:p>").body.contents[0], self.paragraph_list)
            self.paragraph_list.append(empty_paragraph)

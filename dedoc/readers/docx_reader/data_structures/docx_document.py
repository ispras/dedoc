import hashlib
import logging
import os
import re
import time
import zipfile
from collections import defaultdict
from typing import Optional, List, Dict
from bs4 import BeautifulSoup

from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.data_structures.concrete_annotations.alignment_annotation import AlignmentAnnotation
from dedoc.data_structures.concrete_annotations.attach_annotation import AttachAnnotation
from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.indentation_annotation import IndentationAnnotation
from dedoc.data_structures.concrete_annotations.italic_annotation import ItalicAnnotation
from dedoc.data_structures.concrete_annotations.linked_text_annotation import LinkedTextAnnotation
from dedoc.data_structures.concrete_annotations.size_annotation import SizeAnnotation
from dedoc.data_structures.concrete_annotations.spacing_annotation import SpacingAnnotation
from dedoc.data_structures.concrete_annotations.strike_annotation import StrikeAnnotation
from dedoc.data_structures.concrete_annotations.style_annotation import StyleAnnotation
from dedoc.data_structures.concrete_annotations.subscript_annotation import SubscriptAnnotation
from dedoc.data_structures.concrete_annotations.superscript_annotation import SuperscriptAnnotation
from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.concrete_annotations.underlined_annotation import UnderlinedAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.readers.docx_reader.data_structures.paragraph import Paragraph
from dedoc.readers.docx_reader.data_structures.paragraph_info import ParagraphInfo
from dedoc.readers.docx_reader.data_structures.table import DocxTable
from dedoc.readers.docx_reader.footnote_extractor import FootnoteExtractor
from dedoc.readers.docx_reader.numbering_extractor import NumberingExtractor
from dedoc.readers.docx_reader.styles_extractor import StylesExtractor
from dedoc.readers.utils.hierarchy_level_extractor import HierarchyLevelExtractor
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.utils.utils import calculate_file_hash


class Counter:

    def __init__(self, body: BeautifulSoup, logger: logging.Logger) -> None:
        self.logger = logger
        self.total_paragraph_number = sum([len(p.find_all('w:p')) for p in body if p.name != 'p' and p.name != "tbl"])
        self.total_paragraph_number += len([p for p in body if p.name == 'p'])
        self.current_paragraph_number = 0
        self.checkpoint_time = time.time()

    def inc(self) -> None:
        self.current_paragraph_number += 1
        current_time = time.time()
        if current_time - self.checkpoint_time > 3:
            self.logger.info(f"Processed {self.current_paragraph_number} paragraphs from {self.total_paragraph_number}")
            self.checkpoint_time = current_time


class DocxDocument:
    def __init__(self, path: str, hierarchy_level_extractor: HierarchyLevelExtractor, logger: logging.Logger) -> None:
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
        self.lines = self.__get_lines(hierarchy_level_extractor=hierarchy_level_extractor, logger=logger)

    def __get_lines(self, hierarchy_level_extractor: HierarchyLevelExtractor, logger: logging.Logger) -> List[LineWithMeta]:
        """
        Get list of LineWithMeta with annotations, links to the images and tables.
        Fill tables if they exist in the document.
        1. Get paragraphs in the inner representation, tables, images and diagrams.
        2. Convert paragraphs into list with LineWithMeta with annotations

        :return: list of document lines with annotations
        """
        # { paragraph index in paragraph_list : list of uids }
        table_refs, image_refs, diagram_refs = defaultdict(list), defaultdict(list), defaultdict(list)
        cnt = Counter(self.body, logger)
        uids_set = set()
        prev_paragraph = None
        paragraph_list = []

        for paragraph_xml in self.body:
            if paragraph_xml.name == 'tbl':
                self.__handle_table_xml(paragraph_xml, paragraph_list, table_refs, uids_set, cnt)
                continue

            if paragraph_xml.pict:  # diagrams are saved using docx_attachments_extractor
                self.__handle_diagrams_xml(paragraph_xml, paragraph_list, diagram_refs, uids_set, cnt)
                continue

            if paragraph_xml.name != 'p':
                for subparagraph_xml in paragraph_xml.find_all('w:p'):  # TODO check what to add
                    prev_paragraph = paragraph = self.__xml2paragraph(subparagraph_xml, prev_paragraph, uids_set, cnt)
                    paragraph_list.append(paragraph)
                continue

            prev_paragraph = paragraph = self.__xml2paragraph(paragraph_xml, prev_paragraph, uids_set, cnt)
            paragraph_list.append(paragraph)

            images = paragraph_xml.find_all('pic:pic')
            if images:
                self.__handle_images_xml(images, paragraph_list, image_refs, uids_set, cnt)

        return self.__paragraphs2lines(hierarchy_level_extractor, paragraph_list, image_refs, table_refs, diagram_refs)

    def __paragraphs2lines(self,
                           hierarchy_level_extractor: HierarchyLevelExtractor,
                           paragraph_list: List[Paragraph],
                           image_refs: dict,
                           table_refs: dict,
                           diagram_refs: dict) -> List[LineWithMeta]:
        """
        Convert list of paragraphs into list of LineWithMeta.
        Add all annotations to the lines.
        :param hierarchy_level_extractor: extractor of hierarchy level
        :return: list of LineWithMeta
        """
        lines_with_meta = []
        paragraph_id = 0

        for i, paragraph in enumerate(paragraph_list):
            # line with meta:
            # {"text": "",
            #  "type": ""("paragraph" ,"list_item", "raw_text", "style_header"),
            #  "level": (1,1) or None (hierarchy_level),
            #  "annotations": [["size", start, end, size], ["bold", start, end, "True"], ...]}
            paragraph_properties = ParagraphInfo(paragraph)
            line_with_meta = paragraph_properties.get_info()
            text = line_with_meta["text"]

            paragraph_type = line_with_meta["type"]
            level = line_with_meta["level"]
            hl = HierarchyLevel(level[0], level[1], False, paragraph_type) if level else HierarchyLevel.create_raw_text()

            annotations_class = [AlignmentAnnotation,
                                 BoldAnnotation,
                                 IndentationAnnotation,
                                 ItalicAnnotation,
                                 SizeAnnotation,
                                 SpacingAnnotation,
                                 StrikeAnnotation,
                                 StyleAnnotation,
                                 SubscriptAnnotation,
                                 SuperscriptAnnotation,
                                 UnderlinedAnnotation]
            dict2annotations = {annotation.name: annotation for annotation in annotations_class}

            annotations = []
            for annotation in line_with_meta["annotations"]:
                annotations.append(dict2annotations[annotation[0]](*annotation[1:]))
            for footnote in paragraph.footnotes:
                annotations.append(LinkedTextAnnotation(start=0, end=len(line_with_meta), value=footnote))

            for object_dict in [image_refs, diagram_refs]:
                if i in object_dict:
                    for object_uid in object_dict[i]:
                        annotation = AttachAnnotation(attach_uid=object_uid, start=0, end=len(text))
                        annotations.append(annotation)

            if i in table_refs:
                for table_uid in table_refs[i]:
                    annotation = TableAnnotation(name=table_uid, start=0, end=len(text))
                    annotations.append(annotation)

            paragraph_id += 1
            metadata = ParagraphMetadata(paragraph_type=paragraph_type, predicted_classes=None, page_id=0, line_id=paragraph_id)

            lines_with_meta.append(LineWithMeta(line=text, hierarchy_level=hl, metadata=metadata, annotations=annotations, uid=paragraph.uid))

        lines_with_meta = hierarchy_level_extractor.get_hierarchy_level(lines_with_meta)
        return lines_with_meta

    def __get_bs_tree(self, filename: str) -> Optional[BeautifulSoup]:
        """
        Gets xml bs tree from the given file inside the self.path.
        :param filename: name of file to extract the tree
        :return: BeautifulSoup tree or None if file wasn't found
        """
        try:
            with zipfile.ZipFile(self.path) as document:
                return BeautifulSoup(document.read(filename), 'xml')
        except KeyError:
            return None
        except zipfile.BadZipFile:
            raise BadFileFormatException("Bad docx file:\n file_name = {}. Seems docx is broken".format(os.path.basename(self.path)))

    def __xml2paragraph(self, paragraph_xml: BeautifulSoup, prev_paragraph: Optional[Paragraph], uids_set: set, cnt: Counter) -> Paragraph:
        uid = self.__get_paragraph_uid(paragraph_xml=paragraph_xml, uids_set=uids_set)
        paragraph = Paragraph(xml=paragraph_xml,
                              styles_extractor=self.styles_extractor,
                              numbering_extractor=self.numbering_extractor,
                              footnote_extractor=self.footnote_extractor,
                              endnote_extractor=self.endnote_extractor,
                              uid=uid)
        paragraph.spacing = paragraph.spacing_before if prev_paragraph is None else max(prev_paragraph.spacing_after, paragraph.spacing_before)
        cnt.inc()
        return paragraph

    def __get_paragraph_uid(self, paragraph_xml: BeautifulSoup, uids_set: set) -> str:
        xml_hash = hashlib.md5(paragraph_xml.encode()).hexdigest()
        raw_uid = '{}_{}'.format(self.path_hash, xml_hash)
        uid = raw_uid
        n = 0
        while uid in uids_set:
            n += 1
            uid = raw_uid + "_{}".format(n)
        uids_set.add(uid)
        return uid

    def __handle_table_xml(self, xml: BeautifulSoup, paragraph_list: List[Paragraph], table_refs: dict, uids_set: set, cnt: Counter) -> None:
        table = DocxTable(xml, self.styles_extractor)
        self.tables.append(table.to_table())
        table_uid = table.uid

        self.__prepare_paragraph_list(paragraph_list, uids_set, cnt)

        if len(paragraph_list) >= 2 and self.table_ref_reg.match(paragraph_list[-2].text):
            table_refs[len(paragraph_list) - 2].append(table_uid)
        else:
            table_refs[len(paragraph_list) - 1].append(table_uid)

    def __handle_images_xml(self, xmls: List[BeautifulSoup], paragraph_list: List[Paragraph], image_refs: dict, uids_set: set, cnt: Counter) -> None:
        rels = self.__get_bs_tree('word/_rels/document.xml.rels')
        if rels is None:
            rels = self.__get_bs_tree('word/_rels/document2.xml.rels')
        images_rels = self.__get_images_rels(rels)

        self.__prepare_paragraph_list(paragraph_list, uids_set, cnt)

        for image_xml in xmls:
            blips = image_xml.find_all("a:blip")
            image_uid = images_rels[blips[0]["r:embed"]]
            image_refs[len(paragraph_list) - 1].append(image_uid)

    def __handle_diagrams_xml(self, xml: BeautifulSoup, paragraph_list: List[Paragraph], diagram_refs: dict, uids_set: set, cnt: Counter) -> None:
        diagram_uid = hashlib.md5(xml.encode()).hexdigest()
        self.__prepare_paragraph_list(paragraph_list, uids_set, cnt)
        diagram_refs[len(paragraph_list) - 1].append(diagram_uid)

    def __get_images_rels(self, rels: BeautifulSoup) -> Dict[str, str]:
        media_ids = dict()
        for rel in rels.find_all('Relationship'):
            if rel["Target"].startswith('media/'):
                media_ids[rel["Id"]] = rel["Target"][6:]

        return media_ids

    def __prepare_paragraph_list(self, paragraph_list: List[Paragraph], uids_set: set, cnt: Counter) -> None:
        while len(paragraph_list) > 0:
            if paragraph_list[-1].text.strip() == "":
                paragraph_list.pop()
            else:
                break

        if not paragraph_list:
            empty_paragraph = self.__xml2paragraph(BeautifulSoup('<w:p></w:p>').body.contents[0], None, uids_set, cnt)
            paragraph_list.append(empty_paragraph)

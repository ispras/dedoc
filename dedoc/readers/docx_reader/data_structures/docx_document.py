import hashlib
import os
import zipfile
from collections import defaultdict
from typing import Optional, List, Dict

from bs4 import BeautifulSoup

from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.data_structures.concrete_annotations.alignment_annotation import AlignmentAnnotation
from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.indentation_annotation import IndentationAnnotation
from dedoc.data_structures.concrete_annotations.italic_annotation import ItalicAnnotation
from dedoc.data_structures.concrete_annotations.size_annotation import SizeAnnotation
from dedoc.data_structures.concrete_annotations.style_annotation import StyleAnnotation
from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.concrete_annotations.attach_annotation import AttachAnnotation
from dedoc.data_structures.concrete_annotations.underlined_annotation import UnderlinedAnnotation
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata
from dedoc.readers.docx_reader.data_structures.paragraph import Paragraph
from dedoc.readers.docx_reader.data_structures.paragraph_info import ParagraphInfo
from dedoc.readers.docx_reader.data_structures.table import DocxTable
from dedoc.readers.docx_reader.numbering_extractor import NumberingExtractor
from dedoc.readers.docx_reader.styles_extractor import StylesExtractor
from dedoc.readers.utils.hierarch_level_extractor import HierarchyLevelExtractor
from dedoc.structure_parser.heirarchy_level import HierarchyLevel
from dedoc.utils import calculate_file_hash


class DocxDocument:
    def __init__(self, path: str, hierarchy_level_extractor: HierarchyLevelExtractor):
        self.path = path
        self.path_hash = calculate_file_hash(path=path)

        self.document_bs_tree = self.__get_bs_tree('word/document.xml')
        self.body = self.document_bs_tree.body if self.document_bs_tree else None

        self.styles_extractor = StylesExtractor(self.__get_bs_tree('word/styles.xml'))
        num_tree = self.__get_bs_tree('word/numbering.xml')
        self.numbering_extractor = NumberingExtractor(num_tree, self.styles_extractor) if num_tree else None
        self.styles_extractor.numbering_extractor = self.numbering_extractor

        rels = self.__get_bs_tree('word/_rels/document.xml.rels')
        self.images_rels = self.__get_images_rels(rels)

        self.paragraph_list = []
        self.table_refs = defaultdict(list)
        self.image_refs = defaultdict(list)
        self.table_uids = []
        self._uids_set = set()
        self.tables = []
        self.lines = self._process_lines(hierarchy_level_extractor=hierarchy_level_extractor)

    def __get_bs_tree(self, filename: str) -> Optional[BeautifulSoup]:
        """
        gets xml bs tree from the given file inside the self.path
        :param filename: name of file to extract the tree
        :return: BeautifulSoup tree or None if file wasn't found
        """
        try:
            with zipfile.ZipFile(self.path) as document:
                return BeautifulSoup(document.read(filename), 'xml')
        except KeyError:
            return None
        except zipfile.BadZipFile as exception:
            raise BadFileFormatException("Bad docx file:\n file_name = {}. Seems docx is broken".format(
                os.path.basename(self.path)
            ))

    def __get_paragraph_uid(self, paragraph_xml: BeautifulSoup):
        xml_hash = hashlib.md5(paragraph_xml.encode()).hexdigest()
        raw_uid = '{}_{}'.format(self.path_hash, xml_hash)
        uid = raw_uid
        n = 0
        while uid in self._uids_set:
            n += 1
            uid = raw_uid + "_{}".format(n)
        self._uids_set.add(uid)
        return uid

    def __xml2paragraph(self, paragraph_xml: BeautifulSoup) -> Paragraph:
        uid = self.__get_paragraph_uid(paragraph_xml=paragraph_xml)
        return Paragraph(xml=paragraph_xml,
                         styles_extractor=self.styles_extractor,
                         numbering_extractor=self.numbering_extractor,
                         uid=uid)

    def __get_images_rels(self, rels: BeautifulSoup) -> Dict[str, str]:
        media_ids = dict()
        for rel in rels.find_all('Relationship'):
            if rel["Target"].startswith('media/'):
                media_ids[rel["Id"]] = rel["Target"][6:]

        return media_ids

    def _get_lines_with_meta(self, hierarchy_level_extractor: HierarchyLevelExtractor) -> List[LineWithMeta]:
        """
        :param paragraph_list: list of Paragraph
        :return: list of LineWithMeta
        """
        lines_with_meta = []
        paragraph_id = 0

        for i, paragraph in enumerate(self.paragraph_list):
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
            if level:
                hierarchy_level = HierarchyLevel(level[0], level[1], False, paragraph_type)
            else:
                hierarchy_level = HierarchyLevel.create_raw_text()

            dict2annotations = {
                "bold": BoldAnnotation,
                "italic": ItalicAnnotation,
                "underlined": UnderlinedAnnotation,
                "size": SizeAnnotation,
                "indentation": IndentationAnnotation,
                "alignment": AlignmentAnnotation,
                "style": StyleAnnotation,
            }

            annotations = []
            for annotation in line_with_meta["annotations"]:
                annotations.append(dict2annotations[annotation[0]](*annotation[1:]))

            if i in self.table_refs:
                for table_uid in self.table_refs[i]:
                    annotation = TableAnnotation(name=table_uid, start=0, end=len(text))
                    annotations.append(annotation)

            if i in self.image_refs:
                for image_uid in self.image_refs[i]:
                    annotation = AttachAnnotation(attach_uid=image_uid, start=0, end=len(text))
                    annotations.append(annotation)

            paragraph_id += 1
            metadata = ParagraphMetadata(paragraph_type=paragraph_type,
                                         predicted_classes=None,
                                         page_id=0,
                                         line_id=paragraph_id)

            lines_with_meta.append(LineWithMeta(line=text,
                                                hierarchy_level=hierarchy_level,
                                                metadata=metadata,
                                                annotations=annotations,
                                                uid=paragraph.uid))
            lines_with_meta = hierarchy_level_extractor.get_hierarchy_level(lines_with_meta)
        return lines_with_meta

    def get_paragraph_xml_list(self) -> List[Paragraph]:
        return self.paragraph_list

    def get_document_bs_tree(self) -> BeautifulSoup:
        return self.document_bs_tree

    def _process_lines(self, hierarchy_level_extractor: HierarchyLevelExtractor) -> List[LineWithMeta]:
        """
        :return: list of document lines with annotations
        """

        for paragraph_xml in self.body:
            if paragraph_xml.name == 'tbl':
                self._handle_table_xml(paragraph_xml)
                continue

            if paragraph_xml.name != 'p':
                # TODO check what to add
                self.paragraph_list += map(self.__xml2paragraph, paragraph_xml.find_all('w:p'))
                continue

            paragraph = self.__xml2paragraph(paragraph_xml)
            self.paragraph_list.append(paragraph)

            images = paragraph_xml.find_all('pic:pic')
            if images:
                self._handle_images_xml(images)

        return self._get_lines_with_meta(hierarchy_level_extractor=hierarchy_level_extractor)

    def _handle_table_xml(self, paragraph_xml: BeautifulSoup):
        table = DocxTable(paragraph_xml, self.styles_extractor)
        metadata = TableMetadata(page_id=None, uid=table.uid)
        self.tables.append(Table(cells=table.get_cells(), metadata=metadata))
        table_uid = table.uid
        if not self.paragraph_list:
            empty_paragraph_xml = BeautifulSoup('<w:p></w:p>').body.contents[0]
            empty_paragraph = self.__xml2paragraph(empty_paragraph_xml)
            self.paragraph_list.append(empty_paragraph)
        self.table_refs[len(self.paragraph_list) - 1].append(table_uid)

    def _handle_images_xml(self, images_xml: BeautifulSoup):
        for image_xml in images_xml:
            blips = image_xml.find_all("a:blip")
            image_uid = self.images_rels[blips[0]["r:embed"]]
            self.image_refs[len(self.paragraph_list) - 1].append(image_uid)

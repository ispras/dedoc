import zipfile
from typing import Dict, List, Optional

from bs4 import BeautifulSoup, Tag

from dedoc.attachments_extractors.concrete_attachments_extractors.pptx_attachments_extractor import PptxAttachmentsExtractor
from dedoc.data_structures import AttachAnnotation, Table, TableAnnotation
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.extensions import recognized_extensions, recognized_mimes
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.pptx_reader.numbering_extractor import NumberingExtractor
from dedoc.readers.pptx_reader.properties_extractor import PropertiesExtractor
from dedoc.readers.pptx_reader.shape import PptxShape
from dedoc.readers.pptx_reader.table import PptxTable
from dedoc.utils.office_utils import get_bs_from_zip
from dedoc.utils.parameter_utils import get_param_with_attachments


class PptxReader(BaseReader):
    """
    This class is used for parsing documents with .pptx extension.
    Please use :class:`~dedoc.converters.PptxConverter` for getting pptx file from similar formats.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config, recognized_extensions=recognized_extensions.pptx_like_format, recognized_mimes=recognized_mimes.pptx_like_format)
        self.attachments_extractor = PptxAttachmentsExtractor(config=self.config)
        self.numbering_extractor = NumberingExtractor()

    def read(self, file_path: str, parameters: Optional[dict] = None) -> UnstructuredDocument:
        """
        The method return document content with all document's lines, tables and attachments.
        Look to the documentation of :meth:`~dedoc.readers.BaseReader.read` to get information about the method's parameters.
        """
        with_attachments = get_param_with_attachments(parameters)
        attachments = self.attachments_extractor.extract(file_path=file_path, parameters=parameters) if with_attachments else []
        attachment_name2uid = {attachment.original_name: attachment.uid for attachment in attachments}
        images_rels = self.__get_slide_images_rels(file_path)
        properties_extractor = PropertiesExtractor(file_path)

        slide_xml_list = self.__get_slides_bs(file_path, xml_prefix="ppt/slides/slide", xml_postfix=".xml")
        lines = []
        tables = []

        for slide_id, slide_xml in enumerate(slide_xml_list):
            shape_tree_xml = slide_xml.spTree

            is_first_shape = True
            for tag in shape_tree_xml:
                if tag.name == "sp":
                    if not tag.txBody:
                        continue

                    shape = PptxShape(tag, page_id=slide_id, init_line_id=len(lines), numbering_extractor=self.numbering_extractor,
                                      properties_extractor=properties_extractor, is_title=is_first_shape)
                    shape_lines = shape.get_lines()
                    lines.extend(shape_lines)
                    if is_first_shape and len(shape_lines) > 0:
                        is_first_shape = False

                elif tag.tbl:
                    self.__add_table(lines=lines, tables=tables, page_id=slide_id, table_xml=tag.tbl, properties_extractor=properties_extractor)
                elif tag.name == "pic" and tag.blip:
                    if len(lines) == 0:
                        lines.append(LineWithMeta(line="", metadata=LineMetadata(page_id=slide_id, line_id=0)))
                    image_rel_id = str(slide_id) + tag.blip.get("r:embed", "")
                    self.__add_attach_annotation(lines[-1], image_rel_id, attachment_name2uid, images_rels)

        return UnstructuredDocument(lines=lines, tables=tables, attachments=attachments, warnings=[])

    def __get_slides_bs(self, path: str, xml_prefix: str, xml_postfix: str) -> List[BeautifulSoup]:
        with zipfile.ZipFile(path) as document:
            xml_names = document.namelist()
        filtered_names = [file_name for file_name in xml_names if file_name.startswith(xml_prefix) and file_name.endswith(xml_postfix)]
        sorted_names = sorted(filtered_names, key=lambda x: int(x[len(xml_prefix):-len(xml_postfix)]))
        slides_bs_list = [get_bs_from_zip(path, file_name, remove_spaces=True) for file_name in sorted_names]
        return slides_bs_list

    def __get_slide_images_rels(self, path: str) -> Dict[str, str]:
        """
        return mapping: {image Id -> image name}
        """
        rels_xml_list = self.__get_slides_bs(path, xml_prefix="ppt/slides/_rels/slide", xml_postfix=".xml.rels")
        images_dir = "../media/"

        images_rels = dict()
        for slide_id, rels_xml in enumerate(rels_xml_list):
            for rel in rels_xml.find_all("Relationship"):
                if rel["Target"].startswith(images_dir):
                    images_rels[str(slide_id) + rel["Id"]] = rel["Target"][len(images_dir):]

        return images_rels

    def __add_table(self, lines: List[LineWithMeta], tables: List[Table], page_id: int, table_xml: Tag, properties_extractor: PropertiesExtractor) -> None:
        table = PptxTable(table_xml, page_id, self.numbering_extractor, properties_extractor).to_table()

        if len(lines) == 0:
            lines.append(LineWithMeta(line="", metadata=LineMetadata(page_id=page_id, line_id=0)))
        lines[-1].annotations.append(TableAnnotation(start=0, end=len(lines[-1]), name=table.metadata.uid))
        tables.append(table)

    def __add_attach_annotation(self, line: LineWithMeta, image_rel_id: str, attachment_name2uid: dict, images_rels: dict) -> None:
        try:
            image_name = images_rels[image_rel_id]
            image_uid = attachment_name2uid[image_name]
            line.annotations.append(AttachAnnotation(start=0, end=len(line), attach_uid=image_uid))
        except KeyError as e:
            self.logger.warning(f"Attachment key hasn't been found ({e})")

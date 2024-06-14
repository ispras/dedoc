from bs4 import Tag

from dedoc.data_structures.concrete_annotations.alignment_annotation import AlignmentAnnotation
from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.italic_annotation import ItalicAnnotation
from dedoc.data_structures.concrete_annotations.size_annotation import SizeAnnotation
from dedoc.data_structures.concrete_annotations.strike_annotation import StrikeAnnotation
from dedoc.data_structures.concrete_annotations.subscript_annotation import SubscriptAnnotation
from dedoc.data_structures.concrete_annotations.superscript_annotation import SuperscriptAnnotation
from dedoc.data_structures.concrete_annotations.underlined_annotation import UnderlinedAnnotation
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.pptx_reader.numbering_extractor import NumberingExtractor
from dedoc.readers.pptx_reader.properties_extractor import PropertiesExtractor
from dedoc.utils.annotation_merger import AnnotationMerger


class PptxParagraph:
    """
    This class corresponds to one textual paragraph of some entity, e.g. shape or table cell (tag <a:p>).
    """
    def __init__(self, xml: Tag, numbering_extractor: NumberingExtractor, properties_extractor: PropertiesExtractor) -> None:
        self.xml = xml
        self.numbered_list_type = self.xml.buAutoNum.get("type", "arabicPeriod") if self.xml.buAutoNum else None
        self.level = int(self.xml.pPr.get("lvl", 0)) + 1 if self.xml.pPr else 1
        self.numbering_extractor = numbering_extractor
        self.properties_extractor = properties_extractor
        self.annotation_merger = AnnotationMerger()
        annotations = [BoldAnnotation, ItalicAnnotation, UnderlinedAnnotation, StrikeAnnotation, SuperscriptAnnotation, SubscriptAnnotation]
        self.dict2annotation = {annotation.name: annotation for annotation in annotations}

    def get_line_with_meta(self, page_id: int, line_id: int, is_title: bool, shift: int = 0) -> LineWithMeta:
        text = ""
        paragraph_properties = self.properties_extractor.get_properties(self.xml.pPr, level=self.level)
        hierarchy_level = HierarchyLevel.create_raw_text()

        if is_title or paragraph_properties.title:
            hierarchy_level = HierarchyLevel(line_type=HierarchyLevel.header, level_1=1, level_2=self.level, can_be_multiline=False)
        elif self.numbered_list_type:  # numbered list
            text += self.numbering_extractor.get_text(self.numbered_list_type, shift)
            hierarchy_level = HierarchyLevel(line_type=HierarchyLevel.list_item, level_1=2, level_2=self.level, can_be_multiline=False)
        elif self.xml.buChar:  # bullet list
            text += self.xml.buChar["char"] + " "
            hierarchy_level = HierarchyLevel(line_type=HierarchyLevel.list_item, level_1=3, level_2=self.level, can_be_multiline=False)

        annotations = []
        if self.xml.r:
            for run in self.xml.find_all("a:r"):
                prev_text = text
                for run_text in run:
                    if run_text.name == "t" and run.text:
                        text += run.text

                run_properties = self.properties_extractor.get_properties(run.rPr, level=self.level, properties=paragraph_properties)
                annotations.append(SizeAnnotation(start=len(prev_text), end=len(text), value=str(run_properties.size)))
                for property_name in self.dict2annotation:
                    if getattr(run_properties, property_name):
                        annotations.append(self.dict2annotation[property_name](start=len(prev_text), end=len(text), value="True"))

        text = f"{text}\n"
        annotations = self.annotation_merger.merge_annotations(annotations, text)
        annotations.append(AlignmentAnnotation(start=0, end=len(text), value=paragraph_properties.alignment))
        return LineWithMeta(text, metadata=LineMetadata(page_id=page_id, line_id=line_id, tag_hierarchy_level=hierarchy_level), annotations=annotations)

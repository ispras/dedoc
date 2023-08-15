from dedoc.data_structures.concrete_annotations.alignment_annotation import AlignmentAnnotation
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
from dedoc.data_structures.concrete_annotations.underlined_annotation import UnderlinedAnnotation
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.docx_reader.data_structures.paragraph import Paragraph
from dedoc.utils.annotation_merger import AnnotationMerger


class LineWithMetaConverter:

    def __init__(self, paragraph: Paragraph, paragraph_id: int) -> None:
        """
        Converts custom DOCX Paragraph to LineWithMeta class.
        :param paragraph: Paragraph for converting its properties to the unified representation.
        """
        annotations = [BoldAnnotation, ItalicAnnotation, UnderlinedAnnotation, StrikeAnnotation, SuperscriptAnnotation, SubscriptAnnotation]
        self.dict2annotation = {annotation.name: annotation for annotation in annotations}
        self.annotation_merger = AnnotationMerger()

        self.paragraph = paragraph
        self.line = self.__parse(paragraph, paragraph_id)

    def __parse(self, paragraph: Paragraph, paragraph_id: int) -> LineWithMeta:
        annotations = [
            IndentationAnnotation(start=0, end=len(paragraph.text), value=str(paragraph.indentation)),
            AlignmentAnnotation(start=0, end=len(paragraph.text), value=paragraph.jc),
            SpacingAnnotation(start=0, end=len(paragraph.text), value=str(paragraph.spacing))
        ]
        for footnote in paragraph.footnotes:
            annotations.append(LinkedTextAnnotation(start=0, end=len(paragraph.text), value=footnote))

        if paragraph.style_name is not None:
            annotations.append(StyleAnnotation(start=0, end=len(paragraph.text), value=paragraph.style_name))

        assert len(paragraph.runs) == len(paragraph.runs_ids)

        for run, (start, end) in zip(paragraph.runs, paragraph.runs_ids):
            annotations.append(SizeAnnotation(start=start, end=end, value=str(run.size / 2)))
            for property_name in ["bold", "italic", "underlined", "strike", "superscript", "subscript"]:
                property_value = getattr(run, property_name)
                if property_value:
                    annotations.append(self.dict2annotation[property_name](start=start, end=end, value=str(property_value)))
        annotations = self.annotation_merger.merge_annotations(annotations, paragraph.text)

        metadata = LineMetadata(page_id=0, line_id=paragraph_id, tag_hierarchy_level=self.__get_tag(paragraph))
        return LineWithMeta(line=paragraph.text, metadata=metadata, annotations=annotations, uid=paragraph.uid)

    def __get_tag(self, paragraph: Paragraph) -> HierarchyLevel:
        # TODO toc, toc_item, bullet_list
        if paragraph.style_level is not None:
            return HierarchyLevel(1, paragraph.style_level, False, HierarchyLevel.header)

        if paragraph.list_level is not None:
            return HierarchyLevel(2, paragraph.list_level, False, HierarchyLevel.list_item)

        return HierarchyLevel(None, None, True, HierarchyLevel.unknown)

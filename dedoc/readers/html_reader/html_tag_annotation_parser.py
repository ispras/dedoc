from typing import List, Union, Optional, Tuple

from bs4 import Tag
from dedoc.data_structures.annotation import Annotation
from dedoc.data_structures.concrete_annotations.alignment_annotation import AlignmentAnnotation
from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.italic_annotation import ItalicAnnotation
from dedoc.data_structures.concrete_annotations.linked_text_annotation import LinkedTextAnnotation
from dedoc.data_structures.concrete_annotations.size_annotation import SizeAnnotation
from dedoc.data_structures.concrete_annotations.strike_annotation import StrikeAnnotation
from dedoc.data_structures.concrete_annotations.style_annotation import StyleAnnotation
from dedoc.data_structures.concrete_annotations.subscript_annotation import SubscriptAnnotation
from dedoc.data_structures.concrete_annotations.superscript_annotation import SuperscriptAnnotation
from dedoc.data_structures.concrete_annotations.underlined_annotation import UnderlinedAnnotation
from dedoc.readers.html_reader.html_tags import HtmlTags


class HtmlTagAnnotationParser:

    def parse(self, tag: Tag) -> List[Annotation]:
        _, annotations = self.__parse_annotations(tag, 0)
        return annotations

    def __parse_annotations(self, tag: Tag, start: int = 0) -> Tuple[int, List[Annotation]]:
        if isinstance(tag, str):
            return len(tag), []

        if tag.name not in HtmlTags.text_tags:
            return 0, []

        annotations = []
        curr_len = 0

        for sub_tag in tag:
            part_len, part_annotations = self.__parse_annotations(sub_tag, start + curr_len)
            annotations.extend(part_annotations)
            curr_len += part_len

        annotations.extend(self.__create_annotations(tag, start, start + curr_len))

        if 'style' in tag.attrs.keys():
            annotations.extend(self.__parse_style_string(tag.attrs['style'], start, start + curr_len))

        return curr_len, annotations

    def __create_annotations(self, tag: Union[str, Tag], start: int, end: int) -> List[Annotation]:
        if isinstance(tag, str):
            return []
        elif tag.name in HtmlTags.bold_tags:
            return [BoldAnnotation(start=start, end=end, value="True")]
        elif tag.name in HtmlTags.italic_tags:
            return [ItalicAnnotation(start=start, end=end, value="True")]
        elif tag.name in HtmlTags.underlined_tags:
            return [UnderlinedAnnotation(start=start, end=end, value="True")]
        elif tag.name in HtmlTags.superscript_tags:
            return [SuperscriptAnnotation(start=start, end=end, value="True")]
        elif tag.name in HtmlTags.subscript_tags:
            return [SubscriptAnnotation(start=start, end=end, value="True")]
        elif tag.name in HtmlTags.link_tags:
            return [LinkedTextAnnotation(start=start, end=end, value=tag.get("href", ""))]
        elif tag.name in HtmlTags.strike_tags:
            return [StrikeAnnotation(start=start, end=end, value="True")]
        return []

    def __parse_style_string(self, styles_string: str, start: int, end: int) -> List[Annotation]:
        annotations = []
        styles_list = styles_string.split(';')
        for st in styles_list:
            st = st.strip()

            if not st:
                continue

            pair = st.split(':')
            if len(pair) != 2:
                continue
            key, value = st.split(':')
            value = value.strip()

            if key == 'font-style':
                if value == 'italic':
                    annotations.append(ItalicAnnotation(start, end, value="True"))
            elif key == 'font-weight':
                if value == 'bold':
                    annotations.append(BoldAnnotation(start, end, value="True"))
            elif key == 'font-size':
                font_size = self.__parse_font_size_style(value)

                if font_size is not None:
                    annotations.append(SizeAnnotation(start, end, value=font_size))
            elif key == 'text-align':
                if value in ['justify', 'inherit', 'auto']:
                    continue
                elif value in AlignmentAnnotation.valid_values:
                    annotations.append(AlignmentAnnotation(start, end, value=value))
                elif value in ['start', 'end']:  # additional fields for left
                    annotations.append(AlignmentAnnotation(start, end, value="left"))
                else:
                    continue
            elif key == 'font-family':
                annotations.append(StyleAnnotation(start, end, value=value))
            elif key == 'display':
                if value in {"none", "hidden"}:
                    annotations.append(StyleAnnotation(start, end, value="hidden"))

        return annotations

    def __parse_font_size_style(self, value: str) -> Optional[str]:
        if value.endswith("pt"):
            return value[:-2]

        if value.endswith("px"):
            return str(float(value[:-2]) / 0.75)

        try:
            return str(float(value))
        except ValueError:
            return None

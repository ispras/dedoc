import re
from collections import defaultdict
from typing import Dict, List, Union, Tuple, Optional

from dedoc.readers.docx_reader.data_structures.paragraph import Paragraph
from dedoc.data_structures.hierarchy_level import HierarchyLevel


class ParagraphInfo:

    def __init__(self, paragraph: Paragraph) -> None:
        """
        extracts information from paragraph properties
        :param paragraph: Paragraph for extracting it's properties
        """
        self.list_level = paragraph.list_level
        self.style_level = paragraph.style_level
        self.text = ""
        # common properties for all runs in one paragraph
        self.paragraph_properties = {"indentation": str(paragraph.indentation),
                                     "alignment": paragraph.jc,
                                     "spacing": str(paragraph.spacing)}
        if paragraph.style_name is not None:
            self.paragraph_properties["style"] = paragraph.style_name

        # dict with lists of unified run's properties
        # {"size": [[start, end, value], ...], ...}
        self.properties = defaultdict(list)
        for run in paragraph.runs:
            if len(run.text) == 0:
                continue
            self.text = run.text if not self.text else self.text + run.text
            new_properties = dict()
            new_properties['size'] = run.size if run.size else paragraph.size
            new_properties['bold'] = run.bold
            new_properties['italic'] = run.italic
            new_properties['underlined'] = run.underlined
            new_properties['strike'] = run.strike
            new_properties['superscript'] = run.superscript
            new_properties['subscript'] = run.subscript
            new_properties['text'] = run.text
            self.__extend_properties(new_properties)

        if hasattr(paragraph, "caps") and paragraph.caps:
            self.text = self.text.upper()

    def __extend_properties(self, new_properties: dict) -> None:
        self.__extend_size_property(new_properties)
        for property_name in ['bold', 'italic', 'underlined', 'strike', 'superscript', 'subscript']:
            self.__extend_font_property(property_name, new_properties)

    def __extend_size_property(self, new_properties: dict) -> None:
        text_len = len(self.text)
        new_size = str(new_properties['size'] / 2)
        if self.properties["size"]:
            if self.__is_space(new_properties) or self.properties["size"][-1][2] == new_size:
                # change end boarder of the annotation
                self.properties["size"][-1][1] = text_len
                return

        self.properties["size"].append([text_len - len(new_properties["text"]), text_len, new_size])

    def __extend_font_property(self, property_name: str, new_properties: dict) -> None:
        if not new_properties[property_name] and not self.__is_space(new_properties):
            return

        text_len = len(self.text)
        if self.properties[property_name]:
            if self.properties[property_name][-1][1] == text_len - len(new_properties["text"]):
                self.properties[property_name][-1][1] = text_len
                return
            if self.__is_space(new_properties):
                return

        self.properties[property_name].append([text_len - len(new_properties["text"]), text_len, "True"])

    def __is_space(self, new_properties: dict) -> bool:
        return re.fullmatch(r"\s+", new_properties["text"]) is not None

    def _get_hierarchy_level(self) -> Optional[Tuple[int, int]]:
        """
        defines the type of paragraph and it's level according to it's type
        :return: hierarchy level if the paragraph isn't raw text else returns None
        """
        # 0 - Глава, Параграф
        # 1 - Статья, Пункт, heading
        # 2 - list item
        if self.list_level is not None:
            return 2, self.list_level + 1
        if self.style_level is not None:
            return self.style_level, 0
        if re.match(r"^(Глава|Параграф)\s*(\d\\.)*(\d\\.?)?", self.text):
            return 0, 0
        if re.match(r"^(Статья|Пункт)\s*(\d\\.)*(\d\\.?)?", self.text):
            return 1, 0
        return None

    def get_info(self) -> Dict[str, Union[str, Optional[Tuple[int, int]], List[Tuple[str, int, int, str]]]]:
        """
        returns paragraph properties in special format
        :return: dictionary {"text": "",
        "type": "" ("paragraph" ,"list_item", "raw_text", "style_header"),
        "level": (1,1) or None (hierarchy_level),
        "annotations": [(name, start, end, value), ...] },
        name - annotation name
        start, end - character's positions begin with 0, end isn't included
        value - annotation value
        """
        hierarchy_level = self._get_hierarchy_level()
        result = dict()
        result['text'] = self.text
        result['level'] = hierarchy_level

        if not hierarchy_level:
            result['type'] = HierarchyLevel.unknown
        elif self.style_level is not None:
            result['type'] = "style_header"
        elif hierarchy_level[0] == 0 or hierarchy_level[0] == 1:
            result['type'] = HierarchyLevel.paragraph
        elif hierarchy_level[0] == 2:
            result['type'] = HierarchyLevel.list_item
        else:
            result['type'] = HierarchyLevel.unknown

        result['annotations'] = []
        # add annotations common for all paragraph
        text_len = len(self.text)
        for annotation_name, value in self.paragraph_properties.items():
            result['annotations'].append((annotation_name, 0, text_len, value))

        for annotation_name, annotation_list in self.properties.items():
            for annotation in annotation_list:
                result['annotations'].append((annotation_name, annotation[0], annotation[1], annotation[2]))

        return result

    def get_text(self) -> str:
        """
        :return: text of the paragraph
        """
        return self.text

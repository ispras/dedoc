import re
import hashlib
from typing import Dict, List, Union, Tuple, Optional

from dedoc.readers.docx_reader.data_structures.paragraph import Paragraph


class ParagraphInfo:

    def __init__(self,
                 paragraph: Paragraph):
        """
        extracts information from paragraph properties
        :param paragraph: Paragraph for extracting it's properties
        """
        self.text = ""
        self.uid = hashlib.md5(paragraph.xml.encode()).hexdigest()
        self.list_level = paragraph.list_level
        self.style_level = paragraph.style_level
        self.style_name = paragraph.style_name
        self.properties = []
        for run in paragraph.runs:
            start, end = len(self.text), len(self.text) + len(run.text)
            if start == end:
                continue
            if not self.text:
                self.text = run.text
            else:
                self.text += run.text
            properties = dict()
            properties['indent'] = paragraph.indent.copy()
            properties['alignment'] = paragraph.jc
            if run.size:
                properties['size'] = run.size
            else:
                properties['size'] = paragraph.size
            properties['bold'] = run.bold
            properties['italic'] = run.italic
            properties['underlined'] = run.underlined
            self.properties.append([start, end, properties])
        if hasattr(paragraph, "caps") and paragraph.caps:
            self.text = self.text.upper()
        # dict for saving last annotations
        # it is used to unite annotations with same values
        self.last_properties = {}

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
        "uid": string with xml hash,
        "annotations": [(name, start, end, value), ...] },
        name - annotation name
        start, end - character's positions begin with 0, end isn't included
        value - annotation value
        """
        hierarchy_level = self._get_hierarchy_level()
        result = dict()
        result['text'] = self.text
        result['level'] = hierarchy_level
        result['uid'] = self.uid

        if not hierarchy_level:
            result['type'] = "raw_text"
        elif self.style_level is not None:
            result['type'] = "style_header"
        elif hierarchy_level[0] == 0 or hierarchy_level[0] == 1:
            result['type'] = "paragraph"
        elif hierarchy_level[0] == 2:
            result['type'] = "list_item"
        else:
            result['type'] = "raw_text"

        result['annotations'] = []
        if self.properties:
            # TODO more complex information about indent
            result['annotations'].append(("indentation", 0, len(self.text),
                                          str(self.properties[0][2]['indent']['left'])))
            result['annotations'].append(("alignment", 0, len(self.text), self.properties[0][2]['alignment']))

        self.last_properties = {"bold": [], "italic": [], "underlined": [], "size": []}
        for prop in self.properties:
            # add annotation if some new properties were found
            for annotation_name in ["bold", "italic", "underlined"]:
                annotation = self.make_annotation(prop, annotation_name)
                if annotation:
                    result['annotations'].append(annotation)
            annotation = self.make_annotation(prop, "size")
            if annotation:
                result['annotations'].append(annotation)
        for annotation_name, prop in self.last_properties.items():
            # add last properties, which were not added during previous step
            if prop:
                if annotation_name != "size":
                    annotation = (annotation_name, prop[0], prop[1], "True")
                    result['annotations'].append(annotation)
                else:
                    annotation = ("size", prop[0], prop[1], str(prop[2] / 2))
                    result['annotations'].append(annotation)
        if self.style_name:
            result['annotations'].append(("style", 0, len(self.text), self.style_name))
        return result

    def make_annotation(self,
                        prop: List[Union[int, Dict[str, Union[str, int, bool, Dict[str, int]]]]],
                        annotation_name: str) -> Optional[Tuple[str, int, int, str]]:
        """
        makes new annotation if some new properties were found
        else saves annotation in last_properties and returns None
        :param prop: list with properties and it's positions in the text
        :param annotation_name: "bold", "italic", "underlined" or size
        :return: annotation or None
        """
        if type(prop[2]) != dict or annotation_name not in prop[2]:
            return None

        if annotation_name == 'size':
            if not self.last_properties[annotation_name]:
                # for size save start, end, value
                self.last_properties[annotation_name] = [prop[0], prop[1], prop[2][annotation_name]]
                return None
            # if size value wasn't changed or text consists of spaces extend current annotation
            if prop[2][annotation_name] == self.last_properties[annotation_name][2] or \
                    re.fullmatch(r" +", self.text[prop[0]:prop[1]]):
                self.last_properties[annotation_name][1] = prop[1]
                return None
            # else save current annotation and return previous annotation
            annotation = ('size',
                          self.last_properties[annotation_name][0],
                          self.last_properties[annotation_name][1],
                          str(self.last_properties[annotation_name][2] / 2))
            self.last_properties[annotation_name] = [prop[0], prop[1], prop[2][annotation_name]]
            return annotation

        # the same as size but without value
        if prop[2][annotation_name] or \
                self.last_properties[annotation_name] and re.fullmatch(r"\s+", self.text[prop[0]:prop[1]]):
            if self.last_properties[annotation_name]:
                self.last_properties[annotation_name][1] = prop[1]
            else:
                self.last_properties[annotation_name] = [prop[0], prop[1]]  # start, end
            return None
        else:
            if self.last_properties[annotation_name]:
                annotation = (annotation_name,
                              self.last_properties[annotation_name][0],
                              self.last_properties[annotation_name][1], "True")
                self.last_properties[annotation_name] = []
                return annotation
            return None

    @property
    def get_text(self) -> str:
        """
        :return: text of the paragraph
        """
        return self.text

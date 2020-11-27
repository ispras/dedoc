from bs4 import BeautifulSoup
import re
from dedoc.readers.docx_reader.properties_extractor import change_paragraph_properties, change_run_properties
from typing import Dict, List, Union, Tuple, Optional


class BaseProperties:

    def __init__(self,
                 styles_extractor: "StylesExtractor",
                 properties: Optional["BaseProperties"] = None):
        """
        contains properties for paragraphs and runs
        jc, indent, size, bold, italic, underlined
        :param styles_extractor: StylesExtractor
        :param properties: Paragraph or Run for copying it's properties
        """
        if properties:
            self.jc = properties.jc
            self.indent = properties.indent.copy()
            self.size = properties.size
            self.bold = properties.bold
            self.italic = properties.italic
            self.underlined = properties.underlined
            properties.underlined = properties.underlined
        else:
            self.jc = 'left'
            self.indent = {'firstLine': 0, 'hanging': 0, 'start': 0, 'left': 0}
            self.size = 0
            self.bold = False
            self.italic = False
            self.underlined = False
        self.styles_extractor = styles_extractor


class Run(BaseProperties):

    def __init__(self,
                 properties: BaseProperties,
                 styles_extractor: "StylesExtractor"):
        """
        contains information about run properties
        :param properties: Paragraph or Run for copying it's properties
        :param styles_extractor: StylesExtractor
        """

        self.text = ""
        super().__init__(styles_extractor, properties)

    def get_text(self,
                 xml: BeautifulSoup):
        """
        makes the text of run
        :param xml: BeautifulSoup tree with run properties
        """
        for tag in xml:
            if tag.name == 't' and tag.text:
                self.text += tag.text
            elif tag.name == 'tab':
                self.text += '\t'
            elif tag.name == 'br':
                self.text += '\n'
            elif tag.name == 'cr':
                self.text += '\r'
            elif tag.name == 'sym':
                try:
                    self.text += chr(int("0x" + tag['w:char'], 16))
                except KeyError:
                    pass

    def __eq__(self,
               other: "Run") -> bool:
        """
        :param other: Run
        """
        if not isinstance(other, Run):
            return False
        return self.size == other.size and self.bold == other.bold \
            and self.italic == other.italic and self.underlined == other.underlined


class Paragraph(BaseProperties):

    def __init__(self,
                 xml: BeautifulSoup,
                 styles_extractor: "StylesExtractor",
                 numbering_extractor: "NumberingExtractor"):
        """
        contains information about paragraph properties
        :param xml: BeautifulSoup tree with paragraph properties
        :param styles_extractor: StylesExtractor
        :param numbering_extractor: NumberingExtractor
        """
        self.numbering_extractor = numbering_extractor
        self.runs = []
        # level of list of the paragraph is a list item
        self.list_level = None
        self.style_level = None
        self.style_name = None

        self.xml = xml
        super().__init__(styles_extractor)
        self.parse()

    def parse(self) -> None:
        """
        makes the list of paragraph's runs according to the style hierarchy
        """
        # hierarchy: properties in styles -> direct properties (paragraph, character)
        # 1) documentDefault (styles.xml)
        # 2) tables (styles.xml)
        # 3) paragraphs styles (styles.xml)
        # 4) numbering styles (styles.xml, numbering.xml)
        # 5) characters styles (styles.xml)
        # 6) paragraph direct formatting (document.xml)
        # 7) numbering direct formatting (document.xml, numbering.xml)
        # 8) character direct formatting (document.xml)

        # 1) docDefaults
        self.styles_extractor.parse(None, self, "paragraph")
        # 2) we ignore tables

        # 3) paragraph styles
        # 4) numbering styles within styles_extractor
        if self.xml.pStyle:
            self.styles_extractor.parse(self.xml.pStyle['w:val'], self, "paragraph")

        # 5) character style parsed later for each run
        # 6) paragraph direct formatting
        if self.xml.pPr:
            change_paragraph_properties(self, self.xml.pPr)

        # 7) numbering direct formatting
        numbering_run = self._get_numbering_formatting()
        if numbering_run:
            self.runs.append(numbering_run)

        # 8) character direct formatting
        self._make_run_list()

    def _get_numbering_formatting(self) -> Optional[Run]:
        """
        if the paragraph is a list item applies it's properties to the paragraph
        adds numbering run to the list of paragraph runs
        :returns: numbering run if there is the text in numbering else None
        """
        if self.xml.numPr and self.numbering_extractor:
            numbering_run = Run(self, self.styles_extractor)
            self.numbering_extractor.parse(self.xml.numPr, self, numbering_run)
            if numbering_run.text:
                if self.xml.pPr.rPr:
                    change_run_properties(numbering_run, self.xml.pPr.rPr)
                return numbering_run
        return None

    def _make_run_list(self):
        """
        makes runs of the paragraph and adds them to the paragraph list
        """
        run_list = self.xml.find_all('w:r')
        for run_tree in run_list:
            new_run = Run(self, self.styles_extractor)
            if run_tree.rStyle:
                self.styles_extractor.parse(run_tree.rStyle['w:val'], new_run, "character")
                if self.xml.pPr and self.xml.pPr.rPr:
                    change_run_properties(new_run, self.xml.pPr.rPr)
            if run_tree.rPr:
                change_run_properties(new_run, run_tree.rPr)
            new_run.get_text(run_tree)
            if not new_run.text:
                continue

            if self.runs and self.runs[-1] == new_run:
                self.runs[-1].text += new_run.text
            else:
                self.runs.append(new_run)


class ParagraphInfo:

    def __init__(self,
                 paragraph: Paragraph):
        """
        extracts information from paragraph properties
        :param paragraph: Paragraph for extracting it's properties
        """
        self.text = ""
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

    def get_info(self) -> Dict[str, Union[str, Optional[Tuple[int, int]], List[Tuple[int, int, str, str]]]]:
        """
        returns paragraph properties in special format
        :return: dictionary {"text": "",
        "type": "" ("paragraph" ,"list_item", "raw_text", "style_header"),
        "level": (1,1) or None (hierarchy_level),
        "annotations": [[start, end, size], [start, end, "bold"], [start, end, "italic"],
        [start, end, "underlined"], [start, end, "annotations:{'firstLine', 'hanging', 'start', 'left'}"],
        [start, end, "alignment:left" ("left", "right", "center", "both")], [start, end, "size:26"] ...] }
        start, end - character's positions begin with 0, end isn't included
        """
        hierarchy_level = self._get_hierarchy_level()
        result = dict()
        result['text'] = self.text
        result['level'] = hierarchy_level

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
            result['annotations'].append((0, len(self.text), "indentation", self.properties[0][2]['indent']['left']))
            result['annotations'].append((0, len(self.text), "alignment", self.properties[0][2]['alignment']))

        self.last_properties = {"bold": [], "italic": [], "underlined": [], "size": []}
        for prop in self.properties:
            # add annotation if some new properties were found
            for annotation_name in ["bold", "italic", "underlined"]:
                annotation = self.make_annotation(prop, annotation_name)
                if annotation:
                    result['annotations'].append(annotation)
            annotation = self.make_annotation(prop, "size")
            if annotation:
                annotation = (annotation[0], annotation[1], "size", str(prop[2]["size"] / 2))
                result['annotations'].append(annotation)
        for annotation_name, prop in self.last_properties.items():
            # add last properties, which were not added during previous step
            if prop:
                if annotation_name != "size":
                    annotation = (prop[0], prop[1], annotation_name, "True")
                    result['annotations'].append(annotation)
                else:
                    annotation = (prop[0], prop[1], "size", str(prop[2] / 2))
                    result['annotations'].append(annotation)
        if self.style_name:
            result['annotations'].append((0, len(self.text), "style", self.style_name))
        return result

    def make_annotation(self,
                        prop: List[Union[int, Dict[str, Union[str, int, bool, Dict[str, int]]]]],
                        annotation_name: str) -> Optional[Tuple[int, int, str, str]]:
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
            annotation = (self.last_properties[annotation_name][0],
                          self.last_properties[annotation_name][1],
                          'size', str(self.last_properties[annotation_name][2] / 2))
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
                annotation = (self.last_properties[annotation_name][0],
                              self.last_properties[annotation_name][1], annotation_name, "True")
                self.last_properties[annotation_name] = []
                return annotation
            return None

    @property
    def get_text(self) -> str:
        """
        :return: text of the paragraph
        """
        return self.text

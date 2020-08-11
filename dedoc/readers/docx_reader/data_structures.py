from bs4 import BeautifulSoup
from dedoc.readers.docx_reader.properties_extractor import change_paragraph_properties, change_run_properties
from typing import Dict, List, Union


class BaseProperties:

    def __init__(self,
                 styles_extractor,
                 properties=None):
        if properties:
            self.size = properties.size
            self.indent = properties.indent.copy()
            self.bold = properties.bold
            self.italic = properties.italic
            self.underlined = properties.underlined
            properties.underlined = properties.underlined
        else:
            self.size = 0
            self.indent = {'firstLine': 0, 'hanging': 0, 'start': 0, 'left': 0}
            self.bold = False
            self.italic = False
            self.underlined = False
        self.styles_extractor = styles_extractor


class Paragraph(BaseProperties):

    def __init__(self,
                 xml: BeautifulSoup,
                 styles_extractor,
                 numbering_extractor):

        self.numbering_extractor = numbering_extractor
        self.runs = []
        self.xml = xml  # BeautifulSoup tree with paragraph properties
        self.r_pr = None  # rPr from styles of numbering if it exists
        super().__init__(styles_extractor)
        self.parse()

    def parse(self) -> None:
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
        self._get_numbering_formatting()

        # 8) character direct formatting
        self._make_run_list()

    def _get_numbering_formatting(self):
        if self.xml.numPr and self.numbering_extractor:
            numbering_run = Run(self, self.styles_extractor)
            self.numbering_extractor.parse(self.xml.numPr, self, numbering_run)
            if numbering_run.text:
                if self.xml.pPr.rPr:
                    change_run_properties(numbering_run, self.xml.pPr.rPr)
                self.runs.append(numbering_run)

    def _make_run_list(self):
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
        self.text = ""
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
            if run.size:
                properties['size'] = run.size
            else:
                properties['size'] = paragraph.size
            properties['bold'] = run.bold
            properties['italic'] = run.italic
            properties['underlined'] = run.underlined
            self.properties.append([start, end, properties])

    def get_info(self) -> Dict[str, Union[str, List[List[Union[int, int, Dict[str, int]]]]]]:
        """
        :return: dictionary {"text": "",
        "properties": [[start, end, {"indent", "size", "bold", "italic", "underlined"}], ...] }
        start, end - character's positions begin with 0, end isn't included
        indent = {"firstLine", "hanging", "start", "left"}
        """
        return {"text": self.text, "properties": self.properties}


class Run(BaseProperties):

    def __init__(self,
                 properties: BaseProperties,
                 styles_extractor):

        self.text = ""
        super().__init__(styles_extractor, properties)

    def get_text(self,
                 xml):
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
               other):
        if not isinstance(other, Run):
            return False
        return self.size == other.size and self.bold == other.bold \
               and self.italic == other.italic and self.underlined == other.underlined


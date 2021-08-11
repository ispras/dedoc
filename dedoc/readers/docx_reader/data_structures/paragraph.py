from bs4 import BeautifulSoup
from typing import Optional

from dedoc.readers.docx_reader.data_structures.base_props import BaseProperties
from dedoc.readers.docx_reader.data_structures.run import Run
from dedoc.readers.docx_reader.properties_extractor import change_paragraph_properties, change_run_properties


class Paragraph(BaseProperties):

    def __init__(self,
                 xml: BeautifulSoup,
                 styles_extractor: "StylesExtractor",
                 numbering_extractor: "NumberingExtractor",
                 uid: str):
        """
        contains information about paragraph properties
        :param xml: BeautifulSoup tree with paragraph properties
        :param styles_extractor: StylesExtractor
        :param numbering_extractor: NumberingExtractor
        :param uid: unique paragraph id based on file hash and paragraph xml
        """
        self.numbering_extractor = numbering_extractor
        self.runs = []
        self.text = ""
        # level of list of the paragraph is a list item
        self.list_level = None
        self.style_level = None
        self.style_name = None

        # spacing before and after paragraph
        self.spacing_before = 0
        self.spacing_after = 0

        # the maximum spacing: after value for the previous paragraph or before value for the current paragraph
        self.spacing = 0

        self.xml = xml
        super().__init__(styles_extractor)
        self.parse()
        self.uid = uid

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
        for run in self.runs:
            self.text = run.text if not self.text else self.text + run.text

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

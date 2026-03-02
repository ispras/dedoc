from typing import Optional

from bs4 import Tag

from dedoc.readers.docx_reader.data_structures.base_props import BaseProperties
from dedoc.readers.docx_reader.data_structures.run import Run
from dedoc.readers.docx_reader.note_extractor import NoteExtractor
from dedoc.readers.docx_reader.numbering_extractor import NumberingExtractor
from dedoc.readers.docx_reader.properties_extractor import change_paragraph_properties, change_run_properties
from dedoc.readers.docx_reader.styles_extractor import StyleType, StylesExtractor


class Paragraph(BaseProperties):

    def __init__(self,
                 xml: Tag,
                 styles_extractor: StylesExtractor,
                 numbering_extractor: NumberingExtractor,
                 footnote_extractor: NoteExtractor,
                 endnote_extractor: NoteExtractor,
                 comment_extractor: NoteExtractor,
                 uid: str) -> None:
        """
        Contains information about paragraph properties.
        :param xml: BeautifulSoup tree with paragraph properties
        :param styles_extractor: StylesExtractor
        :param numbering_extractor: NumberingExtractor
        :param uid: unique paragraph id based on file hash and paragraph xml
        """
        self.uid = uid
        self.xml = xml
        self.footnote_extractor = footnote_extractor
        self.endnote_extractor = endnote_extractor
        self.comment_extractor = comment_extractor
        self.numbering_extractor = numbering_extractor
        self.styles_extractor = styles_extractor
        self.notes = []
        self.runs = []
        self.runs_ids = []  # list of (start, end) inside the paragraph text
        self.text = ""

        self.list_level = None  # level of nested list if the paragraph is a list item
        self.style_level, self.style_name = None, None

        # spacing before and after paragraph, the maximum spacing: after value for the previous paragraph or before value for the current paragraph
        self.spacing_before, self.spacing_after, self.spacing = 0, 0, 0

        super().__init__()
        self.__parse()

    def __parse(self) -> None:
        """
        Makes the list of paragraph's runs according to the style hierarchy: properties in styles -> direct properties (paragraph, character)
        1) documentDefault (styles.xml)
        2) tables (styles.xml)
        3) paragraphs styles (styles.xml)
        4) numbering styles (styles.xml, numbering.xml)
        5) characters styles (styles.xml)
        6) paragraph direct formatting (document.xml)
        7) numbering direct formatting (document.xml, numbering.xml)
        8) character direct formatting (document.xml)
        """
        # 1) docDefaults
        self.styles_extractor.parse(None, self, StyleType.PARAGRAPH)
        # 2) we ignore tables
        # 3) paragraph styles
        # 4) numbering styles within styles_extractor
        if self.xml.pStyle:
            self.styles_extractor.parse(self.xml.pStyle["w:val"], self, StyleType.PARAGRAPH)

        # 5) character style parsed later for each run
        # 6) paragraph direct formatting
        if self.xml.pPr:
            change_paragraph_properties(self, self.xml.pPr)

        # 7) numbering direct formatting
        numbering_run = self.__get_numbering_formatting()
        if numbering_run:
            self.runs.append(numbering_run)

        # 8) character direct formatting
        self.__make_run_list()
        for run in self.runs:
            self.runs_ids.append((len(self.text), len(self.text + run.text)))
            self.text = run.text if not self.text else self.text + run.text

        if hasattr(self, "caps") and self.caps:
            self.text = self.text.upper()

        for extractor in [self.footnote_extractor, self.endnote_extractor]:
            self.notes.extend(extractor.get_notes(self.xml))

    def __get_numbering_formatting(self) -> Optional[Run]:
        """
        If the paragraph is a list item applies its properties to the paragraph.
        Adds numbering run to the list of paragraph runs.
        :returns: numbering run if there is the text in numbering else None
        """
        if self.xml.numPr and self.numbering_extractor:
            numbering_run = Run(self, self.styles_extractor, self.comment_extractor)
            self.numbering_extractor.parse(self.xml.numPr, self, numbering_run)

            if numbering_run.text:
                if self.xml.pPr.rPr:
                    change_run_properties(numbering_run, self.xml.pPr.rPr)
                return numbering_run
        return None

    def __make_run_list(self) -> None:
        """
        Make runs of the paragraph and adds them to the paragraph list.
        """
        run_list = self.xml.find_all("w:r")

        for run_tree in run_list:
            new_run = Run(self, self.styles_extractor, self.comment_extractor)

            if run_tree.rStyle:
                self.styles_extractor.parse(run_tree.rStyle["w:val"], new_run, StyleType.CHARACTER)
                if self.xml.pPr and self.xml.pPr.rPr:
                    change_run_properties(new_run, self.xml.pPr.rPr)

            if run_tree.rPr:
                change_run_properties(new_run, run_tree.rPr)
            new_run.get_text(run_tree)
            if not new_run.text:
                if new_run.linked_text and self.runs:
                    prev_linked_text = self.runs[-1].linked_text
                    self.runs[-1].linked_text = new_run.linked_text if not prev_linked_text else f"{prev_linked_text}; {new_run.linked_text}"
                continue

            if self.runs and self.runs[-1] == new_run:
                self.runs[-1].text += new_run.text
            else:
                self.runs.append(new_run)

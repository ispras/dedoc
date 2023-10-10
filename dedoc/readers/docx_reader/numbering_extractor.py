import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup, Tag

from dedoc.readers.docx_reader.data_structures.base_props import BaseProperties
from dedoc.readers.docx_reader.properties_extractor import change_paragraph_properties, change_run_properties
from dedoc.readers.docx_reader.styles_extractor import StyleType, StylesExtractor
from dedoc.readers.docx_reader.windows_font_mapping import windows_mapping


class NumberingExtractor:
    """
    Parsing of styles of the paragraphs which are list items.
    Gets the text of the list numbering and may add some annotations like boldness, font size, etc.
    """

    def __init__(self, xml: Optional[BeautifulSoup], styles_extractor: StylesExtractor) -> None:
        """
        :param xml: BeautifulSoup tree with numberings from word/numberings.xml file
        :param styles_extractor: StylesExtractor
        """
        if not xml or not xml.numbering:
            raise Exception("There are no numbering")

        if not styles_extractor:
            raise Exception("Styles extractor must not be empty")

        self.numbering = xml.numbering
        self.styles_extractor = styles_extractor
        self.numbering_formatter = NumberingFormatter()
        self.state = NumberingState()

        abstract_num_dict = {abstract_num["w:abstractNumId"]: abstract_num for abstract_num in xml.find_all("w:abstractNum")}
        num_dict = {num["w:numId"]: num for num in xml.find_all("w:num")}
        # dictionary with num properties
        self.num_dict = {num_id: Num(num_id, abstract_num_dict, num_dict, styles_extractor) for num_id in num_dict}

    def parse(self, xml: Tag, paragraph_properties: BaseProperties, run_properties: BaseProperties) -> None:
        """
        Parses numPr content and extracts properties for paragraph for given numId and list level.
        Changes old_paragraph properties according to list properties.
        Changes run_properties adding text of numeration and it's properties.
        :param xml: BeautifulSoup tree with numPr from document.xml or styles.xml (style content)
        :param paragraph_properties: Paragraph for changing
        :param run_properties: Run for changing
        """
        if not xml:
            return

        ilvl, num_id = xml.ilvl, xml.numId
        if not num_id or num_id["w:val"] not in self.num_dict:
            return
        num_id = num_id["w:val"]

        # find list level
        if not ilvl:
            try:
                style_id = xml["w:styleId"]
                num = self.num_dict[num_id]
                # find link on this styleId in the levels list
                for level_num, level_info in num.level_number2level_info.items():
                    if level_info.style_id == style_id:
                        ilvl = level_num
            except KeyError:
                return
        else:
            ilvl = ilvl["w:val"]

        lvl_info: LevelInfo = self.num_dict[num_id].level_number2level_info[ilvl]
        text = self.__get_list_item_text(ilvl, num_id)

        # change style of the paragraph/run: style -> pPr -> rPr
        if lvl_info.style_id:
            self.styles_extractor.parse(lvl_info.style_id, paragraph_properties, StyleType.NUMBERING)
        if lvl_info.pPr:
            change_paragraph_properties(paragraph_properties, lvl_info.pPr)
        if lvl_info.rPr:
            change_run_properties(run_properties, lvl_info.rPr)
            change_run_properties(paragraph_properties, lvl_info.rPr)

        run_properties.text = text
        paragraph_properties.list_level = self.state.levels_count

    def __get_list_item_text(self, ilvl: str, num_id: str) -> str:
        """
        Counts list item number and it's text.
        :param ilvl: string with list ilvl
        :param num_id: string with list numId
        :return: text of the list numeration
        """
        if num_id not in self.num_dict:
            return ""

        abstract_num_id = self.num_dict[num_id].abstract_num_id

        lvl_info: LevelInfo = self.num_dict[num_id].level_number2level_info[ilvl]
        # the other list started
        if self.state.prev_abstract_num_id and self.state.prev_num_id and self.state.prev_abstract_num_id != abstract_num_id \
                and self.num_dict[self.state.prev_num_id].properties["restart"]:
            del self.state.prev_ilvl_dict[self.state.prev_abstract_num_id]

        # there is the information about this list
        if abstract_num_id in self.state.prev_ilvl_dict:
            prev_ilvl = self.state.prev_ilvl_dict[abstract_num_id]

            # startOverride:
            if lvl_info.restart:
                if abstract_num_id in self.state.prev_num_id_dict:
                    prev_num_id = self.state.prev_num_id_dict[abstract_num_id]
                else:
                    prev_num_id = None
                if prev_num_id and prev_num_id != num_id:
                    self.state.numerations_dict[(abstract_num_id, ilvl)] = lvl_info.start

            # it's a new deeper level
            if prev_ilvl < ilvl and lvl_info.lvl_restart or (abstract_num_id, ilvl) not in self.state.numerations_dict:
                self.state.numerations_dict[(abstract_num_id, ilvl)] = lvl_info.start
            # it's a continue of the old level (current level <= previous level)
            else:
                self.state.numerations_dict[(abstract_num_id, ilvl)] += 1

        # there isn't the information about this list
        else:
            self.state.numerations_dict[(abstract_num_id, ilvl)] = lvl_info.start

        self.state.prev_ilvl_dict[abstract_num_id] = ilvl
        self.state.prev_num_id_dict[abstract_num_id] = num_id
        self.state.prev_abstract_num_id = abstract_num_id
        self.state.prev_num_id = num_id

        text = lvl_info.lvl_text
        levels = re.findall(r"%\d+", text)
        for level in levels:
            # level = "%level"
            level = level[1:]
            next_number = self.__get_next_number(num_id, level)
            text = re.sub(r"%\d+", next_number, text, count=1)
        text += lvl_info.suff
        return text

    def __get_next_number(self, num_id: str, level: str) -> str:
        """
        Computes the shift from the first item for given list and text of next item according to the shift.
        :param num_id: string with list numId
        :param level: list level = ilvl + 1
        :return: text of the next item in numbering
        """
        abstract_num_id = self.num_dict[num_id].abstract_num_id
        # level = ilvl + 1
        self.state.levels_count = int(level)
        ilvl = str(self.state.levels_count - 1)
        lvl_info: LevelInfo = self.num_dict[num_id].level_number2level_info[ilvl]
        if lvl_info.num_fmt == "bullet":
            return lvl_info.lvl_text

        try:
            shift = self.state.numerations_dict[(abstract_num_id, ilvl)]
        except KeyError:
            shift = lvl_info.start
            self.state.numerations_dict[(abstract_num_id, ilvl)] = shift

        return self.numbering_formatter.get_text(lvl_info.num_fmt, shift - 1)


class NumberingFormatter:

    # this is realization of the numFmtList tag
    list_type2start_value = dict(
        decimal="1",  # 1, 2, 3, ..., 10, 11, 12, ...
        lowerLette="a",  # a, b, c, ..., y, z, aa, bb, cc, ..., yy, zz, aaa, bbb, ccc, ...
        lowerRoman="i",  # i, ii, iii, iv, ..., xviii, xix, xx, xxi, ...
        none="",
        russianLower="а",  # а, б, в, ..., ю, я, аа, бб, вв, ..., юю, яя, ааа, ббб, ввв, ...
        russianUpper="А",  # А, Б, В, ..., Ю, Я, АА, ББ, ВВ, ..., ЮЮ, ЯЯ, ААА, БББ, ВВВ, ...
        upperLetter="A",  # A, B, C, ..., Y, Z, AA, BB, CC, ..., YY, ZZ, AAA, BBB, CCC, ...
        upperRoman="I",  # I, II, III, IV, ..., XVIII, XIX, XX, XXI, ...
    )
    roman_mapping = [(1000, "m"), (500, "d"), (100, "c"), (50, "l"), (10, "x"), (5, "v"), (1, "i")]

    def get_text(self, num_fmt: str, shift: int) -> str:
        """
        Computes the next item of the list sequence.
        :param num_fmt: some value from numFmtList
        :param shift: shift from the beginning of list numbering
        :return: string representation of the next numbering item
        """
        if num_fmt == "none" or num_fmt not in self.list_type2start_value:
            return self.list_type2start_value["none"]

        if num_fmt == "decimal":
            return str(int(self.list_type2start_value[num_fmt]) + shift)

        if num_fmt == "lowerLetter" or num_fmt == "upperLetter":
            shift1, shift2 = shift % 26, shift // 26 + 1
            return chr(ord(self.list_type2start_value[num_fmt]) + shift1) * shift2

        if num_fmt == "russianLower" or num_fmt == "russianUpper":
            shift1, shift2 = shift % 32, shift // 32 + 1
            return chr(ord(self.list_type2start_value[num_fmt]) + shift1) * shift2

        if num_fmt == "lowerRoman" or num_fmt == "upperRoman":
            # 1 = I, 5 = V, 10 = X, 50 = L, 100 = C, 500 = D, 1000 = M.

            result = ""
            for number, letter in self.roman_mapping:
                cnt, shift = shift // number, shift % number
                if num_fmt == "upperRoman":
                    letter = chr(ord(letter) + ord("A") - ord("a"))
                result += letter * cnt
            return result


class NumberingState:
    """
    Class with intermediate values of list levels and items numbers during document parsing
    """

    def __init__(self) -> None:
        # {(abstractNumId, ilvl): current number for list element}
        self.numerations_dict = dict()

        # {abstractNumId: ilvl} previous ilvl for list element with given numId
        self.prev_ilvl_dict = dict()

        # {abstractNumId: numId} previous numId for list element with given abstractNumId
        self.prev_num_id_dict = dict()

        # {(abstractNumId, ilvl): shift for wrong numeration}
        self.shift_dict = dict()

        self.prev_num_id = None
        self.prev_abstract_num_id = None

        # the number of levels for current list
        self.levels_count = 1


class LevelInfo:
    """
    Stores properties for each list level.
    """

    def __init__(self) -> None:
        # refers to "lvlText", "numFmt", "start", "lvlRestart", "restart", "suff", "styleId", "pPr", "rPr" tags
        self.lvl_text = ""
        self.num_fmt = "none"
        self.start = 1
        self.lvl_restart = True
        self.restart = None
        self.suff = "\t"
        self.style_id = None
        self.pPr = None
        self.rPr = None


class AbstractNum:

    suffix_dict = dict(nothing="", space=" ", tab="\t")

    def __init__(self, tree: Tag, styles_extractor: StylesExtractor) -> None:
        """
        :param tree: BeautifulSoup tree with abstractNum content
        :param styles_extractor: StylesExtractor
        """
        self.styles_extractor = styles_extractor
        self.abstract_num_id = tree["w:abstractNumId"]

        # properties for all levels {"styleLink", "restart"}, styleLink-> abstractNumId of the other numbering
        self.properties = {"styleLink": tree.numStyleLink["w:val"] if tree.numStyleLink else None}

        try:
            if tree["w15:restartNumberingAfterBreak"]:
                self.properties["restart"] = bool(int(tree["w15:restartNumberingAfterBreak"]))
        except KeyError:
            self.properties["restart"] = False

        # properties for each list level {level number: LevelInfo}
        self.level_number2level_info = dict()

    def parse(self, lvl_list: List[Tag]) -> None:
        """
        Save information about levels in self.levels
        :param lvl_list: list with BeautifulSoup trees which contain information about levels
        """
        for lvl in lvl_list:

            ilvl = lvl["w:ilvl"]
            level_info = self.level_number2level_info.get(ilvl, LevelInfo())

            if lvl.lvlText and lvl.lvlText["w:val"]:  # lvlText (val="some text %num some text")
                # some characters in bullets are displayed incorrectly, replace them with the unicode equivalent
                hex_text = hex(ord(lvl.lvlText["w:val"][0]))
                level_info.lvl_text = windows_mapping.get(hex_text, lvl.lvlText["w:val"])

            if lvl.isLgl:
                level_info.num_fmt = "decimal"
            elif lvl.numFmt:  # numFmt (val="bullet", "decimal", ...)
                level_info.num_fmt = lvl.numFmt["w:val"]

            if lvl.start:
                level_info.start = int(lvl.start["w:val"])

            if lvl.lvlRestart:
                level_info.lvl_restart = bool(int(lvl.lvlRestart["w:val"]))

            if level_info.restart is None:
                level_info.restart = self.properties["restart"]

            if lvl.suff:  # suff (w:val="nothing", "tab" - default, "space")
                level_info.suff = self.suffix_dict[lvl.suff["w:val"]]

            # extract information from paragraphs and runs properties
            if lvl.pStyle:
                level_info.style_id = lvl.pStyle["w:val"]

            # paragraph -> run
            if lvl.pPr:
                level_info.pPr = lvl.pPr

            if lvl.rPr:
                level_info.rPr = lvl.rPr

            if lvl.startOverride:
                level_info.restart = True
                level_info.start = int(lvl.startOverride["w:val"])

            self.level_number2level_info[ilvl] = level_info


class Num(AbstractNum):
    def __init__(self, num_id: str, abstract_num_dict: Dict[str, Tag], num_dict: Dict[str, Tag], styles_extractor: StylesExtractor) -> None:
        """
        :param num_id: numId for num element
        :param abstract_num_dict: dictionary with abstractNum BeautifulSoup trees
        :param num_dict: dictionary with num BeautifulSoup trees
        :param styles_extractor: StylesExtractor
        """
        self.num_id = num_id
        num_tree = num_dict[num_id]
        abstract_num_tree = abstract_num_dict[num_tree.abstractNumId["w:val"]]
        super().__init__(abstract_num_tree, styles_extractor)  # create properties

        # extract the information from numStyleLink
        while self.properties["styleLink"]:
            for abstract_num in abstract_num_dict.values():
                if abstract_num.find("w:styleLink", attrs={"w:val": self.properties["styleLink"]}):
                    abstract_num_tree = abstract_num
                    break
            super().__init__(abstract_num_tree, styles_extractor)
        self.parse(abstract_num_tree.find_all("w:lvl"))

        # override some of abstractNum properties
        if num_tree.lvlOverride:
            lvl_list = num_tree.find_all("w:lvlOverride")
            self.parse(lvl_list)

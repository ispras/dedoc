import logging
import re
from abc import ABC
from collections import OrderedDict
from enum import Enum
from typing import List, Dict, Iterable, Optional

from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.structure_extractors.abstract_structure_extractor import AbstractStructureExtractor
from dedoc.structure_extractors.concrete_structure_extractors.foiv_law_structure_extractor import \
    FoivLawStructureExtractor
from dedoc.structure_extractors.concrete_structure_extractors.law_structure_excractor import LawStructureExtractor


class LawDocType(Enum):
    decree = 'постановление'
    order = 'приказ'
    bylaw = 'распоряжение'
    definition = 'определение'
    directive = 'директива'
    code = 'кодекс'
    law = 'закон'
    constitution = 'конституция'
    edict = 'указ'
    state = 'положение'
    instruction = 'инструкция'
    federalLaw = 'федеральный закон'

    @staticmethod
    def doc_types() -> List[str]:
        # order is important
        return [LawDocType.definition,
                LawDocType.order,
                LawDocType.bylaw,
                LawDocType.code,
                LawDocType.federalLaw,
                LawDocType.edict,
                LawDocType.law,
                LawDocType.decree,
                LawDocType.directive,
                LawDocType.constitution,
                LawDocType.state,
                LawDocType.instruction]

    @staticmethod
    def foiv_types() -> List['LawDocType']:
        return [LawDocType.order, LawDocType.state, LawDocType.instruction]


class ClassifyingLawStructureExtractor(AbstractStructureExtractor, ABC):
    document_type = LawStructureExtractor.document_type

    def __init__(self, extractors: Dict[str, AbstractStructureExtractor], *, config: dict):
        self.extractors = extractors
        self.logger = config.get("logger", logging.getLogger())

        self.hat_batch_size = 3
        self.hat_batch_count = 7

        self.main_templates = dict()
        federal_law_ws = self.__add_whitespace_match("федеральный закон")
        self.main_templates[LawDocType.federalLaw] = {r"\b{}\b".format(federal_law_ws)}

        decree_ws = self.__add_whitespace_match("постановление")
        self.main_templates[LawDocType.decree] = {r"\b{}\b".format(decree_ws)}

        # Hot fix for tesseract common error
        order_char_map = {"з": "[з3]"}
        order_ws = self.__add_whitespace_match("приказ", char_map=order_char_map)
        self.main_templates[LawDocType.order] = {r"\b{}\b".format(order_ws)}

        bylaw_ws = self.__add_whitespace_match("распоряжение")
        self.main_templates[LawDocType.bylaw] = {r"\b{}\b".format(bylaw_ws)}

        law_ws = self.__add_whitespace_match("закон")
        self.main_templates[LawDocType.law] = {r"\b{}\b".format(law_ws)}

        edict_ws = self.__add_whitespace_match("указ")
        self.main_templates[LawDocType.edict] = {r"\b{}\b".format(edict_ws)}

        definition_ws = self.__add_whitespace_match("определение")
        self.main_templates[LawDocType.definition] = {r"\b{}\b".format(definition_ws)}

        directive_ws = self.__add_whitespace_match("директива")
        self.main_templates[LawDocType.directive] = {r"\b{}\b".format(directive_ws)}  # TODO нет данных

        code_ws = self.__add_whitespace_match("кодекс")
        self.main_templates[LawDocType.code] = {r"\b{}\b".format(code_ws)}

        constitution_ws = self.__add_whitespace_match("конституция")
        self.main_templates[LawDocType.constitution] = {r"\b{}\b".format(constitution_ws)}

        state_ws = self.__add_whitespace_match("положение")
        self.main_templates[LawDocType.state] = {r"\b{}\b".format(state_ws)}

        instruction_ws = self.__add_whitespace_match("инструкция")
        self.main_templates[LawDocType.instruction] = {r"\b{}\b".format(instruction_ws)}

    def extract_structure(self, document: UnstructuredDocument, parameters: dict) -> UnstructuredDocument:
        selected_extractor = self._predict_extractor(lines=document.lines)
        return selected_extractor.extract_structure(document, parameters)

    def _predict_extractor(self, lines: List[LineWithMeta]) -> AbstractStructureExtractor:
        raw_lines = [line.line for line in lines]
        doc_type = self.__type_detect(lines=raw_lines)
        extractor = self.__get_extractor_by_type(doc_type=doc_type)
        return extractor

    def __type_detect(self, lines: List[str]) -> Optional[LawDocType]:
        """
        Search for type N in first lines.
        Roud robin type search for each line batch.
        """
        first_lines = self.__create_line_batches(lines, batch_size=self.hat_batch_size, batch_count=self.hat_batch_count)

        # Hack for ЗАКОН ... КОДЕКС ...
        law_matched = False

        for batch in first_lines:
            for doc_type in LawDocType.doc_types():
                for template in self.main_templates[doc_type]:
                    for line in batch:
                        # - for ЯМАЛО-НЕНЕЦКИЙ, \.№ for ПОСТАНОВЛЕНИЕ от 1.1.2000 № 34
                        # / for Приказ № 47/823 от 17.12.2013 г.
                        if re.fullmatch(r'[\s\w-]*' + template + r'[()/\.№\s\w-]*', line, re.IGNORECASE):
                            if doc_type is LawDocType.law:
                                law_matched = True
                            else:
                                return doc_type
        if law_matched:
            return LawDocType.law

        return None

    def __get_extractor_by_type(self, doc_type: Optional[LawDocType]) -> AbstractStructureExtractor:
        if doc_type is None:
            self.logger.info("Dynamic document type not found, using base: {}".format(
                FoivLawStructureExtractor.document_type))
            return self.extractors[self.document_type]
        elif doc_type in LawDocType.foiv_types():
            if FoivLawStructureExtractor.document_type in self.extractors:
                self.logger.info("Dynamic document type predicted: {}".format(
                    FoivLawStructureExtractor.document_type))
                return self.extractors[FoivLawStructureExtractor.document_type]
            else:
                self.logger.warning("No classifier for predicted dynamic document type {}, using {}".format(
                    FoivLawStructureExtractor.document_type, self.document_type))
                return self.extractors[self.document_type]
        else:
            self.logger.info("Dynamic document type predicted: {}".format(self.document_type))
            return self.extractors[self.document_type]

    def __add_whitespace_match(self, pattern: Iterable, char_map: dict = None) -> str:
        if char_map is not None:
            # convert some chars to seq of chars: [з3]
            robust_word = (char_map.get(pattern[i:i + 1], pattern[i:i + 1])
                           for i in range(0, len(pattern), 1))
            return r"\s*".join(robust_word)
        else:
            return r"\s*".join(pattern[i:i + 1] for i in range(0, len(pattern), 1))

    def __create_line_batches(self, lines: List[str], batch_size: int, batch_count: int) -> List[List[str]]:
        """
        Pack lines into batch_count batches of size batch_size.
        """
        batch_lines = []
        cur_batch = []
        cur_batches_count = 0
        cur_batch_size = 0
        for line in lines:
            if line.strip():
                line = self.__text_clean(line).strip()
                if cur_batch_size < batch_size:
                    cur_batch.append(line)
                    cur_batch_size += 1
                else:
                    batch_lines.append(cur_batch)
                    cur_batch = [line]
                    cur_batch_size = 1
                    cur_batches_count += 1
            if cur_batches_count > batch_count:
                break
        return batch_lines

    def __text_clean(self, text: str) -> str:
        bad_characters = OrderedDict({"\u0438\u0306": "й", "\u0439\u0306": "й",
                                      "\u0418\u0306": "Й", "\u0419\u0306": "Й"})
        for bad_c, good_c in bad_characters.items():
            text = text.replace(bad_c, good_c)
        return text

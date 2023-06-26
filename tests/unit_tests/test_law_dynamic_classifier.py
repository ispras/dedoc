import os
import unittest

from dedoc.structure_extractors.concrete_structure_extractors.classifying_law_structure_extractor import ClassifyingLawStructureExtractor
from dedoc.structure_extractors.concrete_structure_extractors.foiv_law_structure_extractor import FoivLawStructureExtractor
from dedoc.structure_extractors.concrete_structure_extractors.law_structure_excractor import LawStructureExtractor
from dedoc.readers.txt_reader.raw_text_reader import RawTextReader


class TestFoivApiDocreader(unittest.TestCase):
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "laws")
    data_path = os.path.abspath(data_path)
    law_extractors = {
        FoivLawStructureExtractor.document_type: FoivLawStructureExtractor(config={}),
        LawStructureExtractor.document_type: LawStructureExtractor(config={})
    }
    structure_extractor = ClassifyingLawStructureExtractor(extractors=law_extractors, config={})

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_path, "doctypes", file_name)

    def _test_classifier_type(self, file_name: str, expected_type: str) -> None:
        config = {}
        base_reader = RawTextReader(config=config)
        unstructured_document = base_reader.read(path=self._get_abs_path(file_name),
                                                 document_type=None,
                                                 parameters=None)
        result = self.structure_extractor._predict_extractor(unstructured_document.lines)

        self.assertEqual(result.document_type, expected_type)

    def test_law(self) -> None:
        file_name = 'закон.txt'
        expected_type = 'law'
        self._test_classifier_type(file_name, expected_type)

    def test_instruction(self) -> None:
        file_name = 'инструкция.txt'
        expected_type = 'foiv_law'
        self._test_classifier_type(file_name, expected_type)

    def test_codex(self) -> None:
        file_name = 'кодекс.txt'
        expected_type = 'law'
        self._test_classifier_type(file_name, expected_type)

    def test_definition(self) -> None:
        file_name = 'определение.txt'
        expected_type = 'law'
        self._test_classifier_type(file_name, expected_type)

    def test_resolution(self) -> None:
        file_name = 'постановление.txt'
        expected_type = 'law'
        self._test_classifier_type(file_name, expected_type)

    def test_order(self) -> None:
        file_name = 'приказ.txt'
        expected_type = 'foiv_law'
        self._test_classifier_type(file_name, expected_type)

    def test_disposal(self) -> None:
        file_name = 'распоряжение.txt'
        expected_type = 'law'
        self._test_classifier_type(file_name, expected_type)

    def test_decree(self) -> None:
        file_name = 'указ.txt'
        expected_type = 'law'
        self._test_classifier_type(file_name, expected_type)

    def test_fz(self) -> None:
        file_name = 'федеральный_закон.txt'
        expected_type = 'law'
        self._test_classifier_type(file_name, expected_type)

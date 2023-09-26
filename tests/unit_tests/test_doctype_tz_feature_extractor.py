import os
from unittest import TestCase

from dedoc.readers.docx_reader.docx_reader import DocxReader
from dedoc.structure_extractors.feature_extractors.tz_feature_extractor import TzTextFeatures
from tests.test_utils import get_test_config


class TestTzTextFeatures(TestCase):

    docx_reader = DocxReader(config=get_test_config())
    feature_extractor = TzTextFeatures()

    def test_extractor(self) -> None:
        document_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "docx", "english_doc.docx"))
        self.assertTrue(os.path.isfile(document_path))
        unstructured_document = self.docx_reader.read(document_path)
        lines = [unstructured_document.lines]
        matrix = self.feature_extractor.transform(lines)
        self.assertEqual(len(lines[0]), matrix.shape[0])
        self.assertTrue(matrix.shape[1] > 0)

    def test_start_regexp(self) -> None:
        line1 = "РАЗДЕЛ 4. РЕЗУЛЬТАТ ОКАЗАННЫХ УСЛУГ"
        self.assertEqual(2, self.__count_start(line1.lower()))
        line2 = "- протоколы аттестационных испытаний;"
        self.assertEqual(2, self.__count_start(line2))
        line3 = ". ГОСТРО 0043-003-2012 «Защита информации. Аттестация объектов"
        self.assertEqual(2, self.__count_start(line3))
        line4 = "3.2.1. Проектная и рабочая документация должны разрабатываться в"
        self.assertEqual(0, self.__count_start(line4))
        line5 = "1.	Наименование оказываемых услуг."
        self.assertEqual(0, self.__count_start(line5))

    def __count_start(self, line: str) -> int:
        return sum([1 for _, i in self.feature_extractor._start_regexp(line, self.feature_extractor.list_item_regexp) if i > 0])

    def test_end_regexp(self) -> None:
        line1 = "Подраздел 3.2 Требования к качеству оказываемых услуг\t12"
        self.assertEqual(2, sum(self.feature_extractor._end_regexp(line1)))
        line2 = "Подраздел 3.2 Требования к качеству оказываемых услуг"
        self.assertEqual(0, sum(self.feature_extractor._end_regexp(line2)))

    def test_named_item_regexp(self) -> None:
        self.assertTrue(self.feature_extractor.named_item_regexp.fullmatch("раздел"))
        self.assertTrue(self.feature_extractor.named_item_regexp.fullmatch("подраздел"))
        self.assertTrue(self.feature_extractor.named_item_regexp.fullmatch("подраздел           \t        "))
        self.assertTrue(self.feature_extractor.named_item_regexp.fullmatch("разделывать") is None)

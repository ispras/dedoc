import os
import unittest

from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.docx_reader.docx_reader import DocxReader
from dedoc.structure_extractors.feature_extractors.toc_feature_extractor import TOCFeatureExtractor

from tests.test_utils import get_test_config


class TestTOCFeatureExtractor(unittest.TestCase):
    feature_extractor = TOCFeatureExtractor()
    reader = DocxReader(config=get_test_config())
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "tz")
    data_path = os.path.abspath(data_path)

    path = os.path.join(data_path, "tz-10ea-2020.docx")
    _document = None

    @property
    def document(self) -> UnstructuredDocument:
        if self._document is None:
            self._document = self.reader.read(path=self.path, parameters={}, document_type=None)
        return self._document

    def test_toc_extractor(self) -> None:
        toc = self.feature_extractor.get_toc(document=self.document.lines)
        self.assertIn("5", toc[0]["page"])
        self.assertEqual("1.\xa0\xa0\xa0\xa0\xa0Общие сведения	5", toc[0]["line"].line.strip())
        self.assertIn("5", toc[1]["page"])
        self.assertEqual("1.1.\xa0Основание для выполнения	5", toc[1]["line"].line.strip())
        self.assertIn("6", toc[2]["page"])
        self.assertEqual("1.2.\xa0Наименование услуг	6", toc[2]["line"].line.strip())

        self.assertIn("26", toc[13]["page"])
        self.assertEqual("4.2.\xa0Требования к оказанию услуг по обследованию подсистем ИВС Росстата, разработке "
                         "актов классификации, моделей угроз и нарушителя безопасности информации	26",
                         toc[13]["line"].line.strip())

        self.assertIn("40", toc[26]["page"])
        self.assertEqual("9.\xa0Перечень материалов, передаваемых Заказчику	40", toc[26]["line"].line.strip())

        self.assertEqual(27, len(toc))

    def test_end_with_num(self) -> None:
        self.assertTrue(self.feature_extractor.end_with_num.match("Как кормить альпака       1"))
        self.assertTrue(self.feature_extractor.end_with_num.match("Как поить альпака.........2"))
        self.assertFalse(self.feature_extractor.end_with_num.match("Как поймать альпака"))

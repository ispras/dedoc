import os
import unittest

from dedoc.readers.docx_reader.docx_reader import DocxReader


class TestAnyDocReader(unittest.TestCase):

    def test_docx(self):
        any_doc_reader = DocxReader()
        path = os.path.join(os.path.dirname(__file__), "data/example.docx")
        result, _ = any_doc_reader.read(path)
        lines = result.lines

        self.assertEqual("Пример документа", lines[0].line)
        self.assertEqual("Глава 1", lines[1].line)
        self.assertEqual("Статья 1", lines[3].line)
        self.assertEqual("Статья 2", lines[5].line)
        self.assertEqual("Дадим пояснения", lines[6].line)

        self.assertEqual("1.2.1. Поясним за непонятное", lines[7].line)
        self.assertEqual("1.2.2. Поясним за понятное", lines[8].line)
        self.assertEqual("а) это даже ежу понятно", lines[9].line)
        self.assertEqual("б) это ежу не понятно", lines[10].line)

        self.assertEqual("1.2.3.", lines[11].line)

    def test_structure_docx(self):
        any_doc_reader = DocxReader()
        path = os.path.join(os.path.dirname(__file__), "data/header_test.docx")
        result, _ = any_doc_reader.read(path)
        lines = result.lines

        self.assertEqual("Глава 543", lines[0].line)
        self.assertEqual("Какой-то текст.", lines[1].line)

        self.assertEqual("1. Текстового", lines[2].line)
        self.assertEqual("2. Текстового", lines[3].line)
        self.assertEqual("3. Еще текстового", lines[4].line)
        self.assertEqual("4. Пам", lines[5].line)

        self.assertEqual("4.1. авп", lines[6].line)
        self.assertEqual("4.2. текстового", lines[7].line)
        self.assertEqual("4.3. п", lines[8].line)
        self.assertEqual("4.4. п", lines[9].line)
        self.assertEqual("4.5. п", lines[10].line)
        self.assertEqual("4.6. п", lines[11].line)


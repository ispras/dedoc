import os
import unittest

from dedoc.readers.docx_reader.docx_reader import DocxReader


class TestAnyDocReader(unittest.TestCase):

    def test_docx(self):
        any_doc_reader = DocxReader()
        path = os.path.join(os.path.dirname(__file__), "data/example.docx")
        result = any_doc_reader.read(path)
        lines = result.lines

        self.assertEqual("Пример документа", lines[0].line)
        self.assertEqual("Глава 1", lines[1].line)
        self.assertEqual("Статья 1", lines[3].line)
        self.assertEqual("Статья 2", lines[5].line)
        self.assertEqual("Дадим пояснения", lines[6].line)

        self.assertEqual("1.2.1. Поясним за непонятное", lines[7].line)
        self.assertEqual("1.2.2. Поясним за понятное", lines[8].line)
        self.assertEqual("а) это даже ежу понятно", lines[9].line.strip())
        self.assertEqual("б) это ежу не понятно", lines[10].line.strip())

        self.assertEqual("1.2.3.", lines[11].line)

    def test_structure_docx(self):
        any_doc_reader = DocxReader()
        path = os.path.join(os.path.dirname(__file__), "data/header_test.docx")
        result = any_doc_reader.read(path)
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

    def test_tz_file(self):
        any_doc_reader = DocxReader()
        path = os.path.join(os.path.dirname(__file__), "data/tz.docx")
        result = any_doc_reader.read(path)
        lines = result.lines

        self.assertEqual("Техническое задание\nна оказание услуг по созданию системы защиты персональных данных \n", lines[0].line)

    def test_docx_without_numbering(self):
        any_doc_reader = DocxReader()
        path = os.path.join(os.path.dirname(__file__), "data/without_numbering.docx")
        try:
            result = any_doc_reader.read(path)
        except AttributeError:
            result = None
        self.assertTrue(result is not None)

    def test_docx_table_location(self):
        any_doc_reader = DocxReader()
        path = os.path.join(os.path.dirname(__file__), "data/example.docx")
        result = any_doc_reader.read(path)
        lines, tables = result.lines, result.tables
        found = False
        for annotation in lines[12].annotations:
            if annotation.name == "table":
                found = True
                self.assertEqual('0a668025582ff0cb4bd790759ae7ced3', annotation.value)
                break
        self.assertTrue(found)
        found = False
        for annotation in lines[14].annotations:
            if annotation.name == "table":
                found = True
                self.assertEqual('d324e58fecdf03bbe1c9b517809655d4', annotation.value)
                break
        self.assertTrue(found)
        self.assertEqual('0a668025582ff0cb4bd790759ae7ced3', tables[0].metadata.uid)
        self.assertEqual('d324e58fecdf03bbe1c9b517809655d4', tables[1].metadata.uid)

    def test_caps_letters(self):
        any_doc_reader = DocxReader()
        path = os.path.join(os.path.dirname(__file__), "data/caps_1.docx")
        result = any_doc_reader.read(path)
        self.assertEqual('ШИЖМАШ МОГАЙ ЛИЕШ ГЫН?	', result.lines[2].line)
        self.assertEqual('АНАСТАСИЯ АЙГУЗИНА', result.lines[3].line)
        path = os.path.join(os.path.dirname(__file__), "data/caps_2.docx")
        result = any_doc_reader.read(path)
        self.assertEqual('И. Одар "Таргылтыш"\n', result.lines[0].line)
        self.assertEqual('I глава\n', result.lines[2].line)

    def test_justification(self):
        any_doc_reader = DocxReader()
        path = os.path.join(os.path.dirname(__file__), "data/justification.docx")
        result = any_doc_reader.read(path)
        answers = [(15, "left"), (16, "center"), (17, "both"), (18, "right")]
        for answer in answers:
            for annotation in result.lines[answer[0]].annotations:
                if annotation.name == "alignment":
                    self.assertEqual(answer[1], annotation.value)

    def test_numeration(self):
        any_doc_reader = DocxReader()
        path = os.path.join(os.path.dirname(__file__), "data/numeration.docx")
        result = any_doc_reader.read(path)
        lines = result.lines
        self.assertEqual("5. Test numeration", lines[1].line)
        self.assertEqual("5.1 text", lines[2].line)
        self.assertEqual("5.2 text. ", lines[3].line)
        self.assertEqual("5.2.1.\tlist. ", lines[4].line)
        self.assertEqual("5.2.2.\tlist", lines[5].line)
        self.assertEqual("5.3.\tlist.", lines[7].line)
        self.assertEqual("5.3.1\t list.", lines[8].line)
        self.assertEqual("5.3.2\t list", lines[9].line)
        self.assertEqual("5.4.\tlist", lines[11].line)
        self.assertEqual("5.5.\tlist", lines[13].line)

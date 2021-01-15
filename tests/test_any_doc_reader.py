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
        self.assertEqual("а) это даже ежу понятно", lines[9].line.strip())
        self.assertEqual("б) это ежу не понятно", lines[10].line.strip())

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

    def test_tz_file(self):
        any_doc_reader = DocxReader()
        path = os.path.join(os.path.dirname(__file__), "data/tz.docx")
        result, _ = any_doc_reader.read(path)
        lines = result.lines

        self.assertEqual("Техническое задание\nна оказание услуг по созданию системы защиты персональных данных ", lines[0].line)

    def test_headers_footers_docx(self):
        any_doc_reader = DocxReader()
        path = os.path.join(os.path.dirname(__file__), "data/footer_header_example.docx")
        result, _ = any_doc_reader.read(path)
        lines = result.lines
        self.assertEqual("This is header for even pages", lines[0].line)
        self.assertEqual("This is header for odd pages", lines[4].line)
        self.assertEqual("3", lines[6].line)
        self.assertEqual("This is the first header", lines[8].line)
        self.assertEqual("This is example document for testing headers, footers, footnotes and endnotes.", lines[12].line)
        self.assertEqual("This sentence is made for testing footnote.", lines[13].line)
        self.assertEqual("This sentence is made for testing endnote.", lines[14].line)
        self.assertEqual("New page-1", lines[16].line)
        self.assertEqual("New page-2", lines[18].line)
        self.assertEqual(" this is the first footnote", lines[21].line)
        self.assertEqual(" this is the second footnote", lines[22].line)
        self.assertEqual(" this is the first endnote", lines[25].line)
        self.assertEqual(" this is the second endnote", lines[26].line)
        self.assertEqual("This is footer for even pages", lines[27].line)
        self.assertEqual("This is footer for odd pages", lines[31].line)
        self.assertEqual("This is the first footer", lines[35].line)

    def test_docx_without_numbering(self):
        any_doc_reader = DocxReader()
        path = os.path.join(os.path.dirname(__file__), "data/without_numbering.docx")
        try:
            result, _ = any_doc_reader.read(path)
        except AttributeError:
            result = None
        self.assertTrue(result is not None)

    def test_docx_table_location(self):
        any_doc_reader = DocxReader()
        path = os.path.join(os.path.dirname(__file__), "data/example.docx")
        result, _ = any_doc_reader.read(path)
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

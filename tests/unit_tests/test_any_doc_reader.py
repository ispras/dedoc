import os
import shutil
import unittest
from tempfile import TemporaryDirectory

from dedoc.config import get_config
from dedoc.readers.docx_reader.docx_reader import DocxReader


class TestAnyDocReader(unittest.TestCase):

    directory = os.path.join(os.path.dirname(__file__), "..", "data", "docx")
    tmpdir = None

    def setUp(self) -> None:
        super().setUp()
        self.tmpdir = TemporaryDirectory()

    def tearDown(self) -> None:
        self.tmpdir.cleanup()
        super().tearDown()

    def test_docx(self) -> None:
        any_doc_reader = DocxReader(config=get_config())
        path = self._get_path("example.docx")
        result = any_doc_reader.read(path)
        lines = result.lines
        self.assertEqual("Пример документа", lines[0].line)
        self.assertEqual("Глава 1", lines[1].line)
        self.assertEqual("Статья 1", lines[3].line)
        self.assertEqual("Статья 2", lines[5].line)
        self.assertEqual("Дадим пояснения", lines[6].line.strip())

        self.assertEqual("1.2.1. Поясним за непонятное", lines[7].line)
        self.assertEqual("1.2.2. Поясним за понятное", lines[8].line)
        self.assertEqual("а) это даже ежу понятно", lines[9].line.strip())
        self.assertEqual("б) это ежу не понятно", lines[10].line.strip())

        self.assertEqual("1.2.3.", lines[11].line)

    def test_structure_docx(self) -> None:
        any_doc_reader = DocxReader(config=get_config())
        path = self._get_path("header_test.docx")
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

    def test_tz_file(self) -> None:
        any_doc_reader = DocxReader(config=get_config())
        path = self._get_path("tz.docx")
        result = any_doc_reader.read(path)
        lines = result.lines

        self.assertEqual("Техническое задание\nна оказание услуг по созданию системы защиты персональных данных \n",
                         lines[0].line)

    def test_docx_without_numbering(self) -> None:
        any_doc_reader = DocxReader(config=get_config())
        path = self._get_path("without_numbering.docx")
        try:
            result = any_doc_reader.read(path)
        except AttributeError:
            result = None
        self.assertTrue(result is not None)

    def test_docx_table_location(self) -> None:
        any_doc_reader = DocxReader(config=get_config())
        path = self._get_path("example.docx")
        result = any_doc_reader.read(path)
        lines, tables = result.lines, result.tables
        first_table_uid = tables[0].metadata.uid
        second_table_uid = tables[1].metadata.uid
        found = False
        for annotation in lines[6].annotations:
            if annotation.name == "table":
                found = True
                self.assertEqual(first_table_uid, annotation.value)
                break
        self.assertTrue(found)
        found = False
        for annotation in lines[-2].annotations:
            if annotation.name == "table":
                found = True
                self.assertEqual(second_table_uid, annotation.value)
                break
        self.assertTrue(found)

    def test_caps_letters1(self) -> None:
        any_doc_reader = DocxReader(config=get_config())
        path = self._get_path("caps_1.docx")
        result = any_doc_reader.read(path)
        self.assertEqual('ШИЖМАШ МОГАЙ ЛИЕШ ГЫН?	', result.lines[2].line)
        self.assertEqual('АНАСТАСИЯ АЙГУЗИНА', result.lines[3].line)

    def test_caps_letters2(self) -> None:
        any_doc_reader = DocxReader(config=get_config())
        path = self._get_path("caps_2.docx")
        result = any_doc_reader.read(path)
        self.assertEqual('И. Одар "Таргылтыш"\n', result.lines[0].line)
        self.assertEqual('I глава\n', result.lines[2].line)

    def test_justification(self) -> None:
        any_doc_reader = DocxReader(config=get_config())
        path = self._get_path("justification.docx")
        result = any_doc_reader.read(path)
        answers = [(15, "left"), (16, "center"), (17, "both"), (18, "right")]
        for answer in answers:
            for annotation in result.lines[answer[0]].annotations:
                if annotation.name == "alignment":
                    self.assertEqual(answer[1], annotation.value)

    def test_numeration(self) -> None:
        any_doc_reader = DocxReader(config=get_config())
        path = self._get_path("numeration.docx")
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

    def test_tables(self) -> None:
        any_doc_reader = DocxReader(config=get_config())
        path = self._get_path("merged_cells.docx")
        result = any_doc_reader.read(path)

        self.assertEqual("Merged sells", result.tables[0].cells[0][0])
        self.assertEqual("Merged sells", result.tables[0].cells[0][1])
        self.assertEqual("Some text", result.tables[0].cells[0][2])
        self.assertEqual("Some text", result.tables[0].cells[0][3])
        self.assertEqual("Cell 1", result.tables[0].cells[1][0])
        self.assertEqual("Cell 2", result.tables[0].cells[1][1])
        self.assertEqual("Vertically split cells 1", result.tables[0].cells[1][2])
        self.assertEqual("Vertically split cells 2", result.tables[0].cells[1][3])
        self.assertEqual("Cell 3", result.tables[0].cells[2][0])
        self.assertEqual("Cell 4", result.tables[0].cells[2][1])
        self.assertEqual("Horizontally split cells 1", result.tables[0].cells[2][2])
        self.assertEqual("Horizontally split cells 1", result.tables[0].cells[2][3])
        self.assertEqual("Cell 3", result.tables[0].cells[3][0])
        self.assertEqual("Cell 4", result.tables[0].cells[3][1])
        self.assertEqual("Horizontally split cells 2", result.tables[0].cells[3][2])
        self.assertEqual("Horizontally split cells 2", result.tables[0].cells[3][3])

        self.assertEqual("cell1", result.tables[1].cells[0][0])
        self.assertEqual("cell2", result.tables[1].cells[0][1])
        self.assertEqual("Horizontally merged", result.tables[1].cells[0][2])
        self.assertEqual("Horizontally merged", result.tables[1].cells[0][3])
        self.assertEqual("Horizontally merged", result.tables[1].cells[0][4])
        self.assertEqual("Horizontally merged", result.tables[1].cells[0][5])
        self.assertEqual("Vertically and horizontally merged cells", result.tables[1].cells[1][0])
        self.assertEqual("Vertically and horizontally merged cells", result.tables[1].cells[1][1])
        self.assertEqual("cell3", result.tables[1].cells[1][2])
        self.assertEqual("Vertically merged", result.tables[1].cells[1][3])
        self.assertEqual("cell4", result.tables[1].cells[1][4])
        self.assertEqual("cell4", result.tables[1].cells[1][5])
        self.assertEqual("Vertically and horizontally merged cells", result.tables[1].cells[2][0])
        self.assertEqual("Vertically and horizontally merged cells", result.tables[1].cells[2][1])
        self.assertEqual("cell5", result.tables[1].cells[2][2])
        self.assertEqual("Vertically merged", result.tables[1].cells[2][3])
        self.assertEqual("v1", result.tables[1].cells[2][4])
        self.assertEqual("v2", result.tables[1].cells[2][5])

    def test_merged_tables(self) -> None:
        any_doc_reader = DocxReader(config=get_config())
        path = self._get_path("merged_cells.docx")
        result = any_doc_reader.read(path)

        hidden_cells_table_1 = [(0, 1), (0, 3), (2, 3), (3, 0), (3, 1), (3, 3)]
        for i, j in hidden_cells_table_1:
            self.assertTrue(result.tables[0].metadata.cell_properties[i][j].invisible)
            self.assertEqual(result.tables[0].metadata.cell_properties[i][j].rowspan, 1)
            self.assertEqual(result.tables[0].metadata.cell_properties[i][j].colspan, 1)

        hidden_cells_table_1_with_colspan = [(0, 0), (0, 2), (2, 2), (3, 2)]
        for i, j in hidden_cells_table_1_with_colspan:
            self.assertFalse(result.tables[0].metadata.cell_properties[i][j].invisible)
            self.assertEqual(result.tables[0].metadata.cell_properties[i][j].rowspan, 1)
            self.assertEqual(result.tables[0].metadata.cell_properties[i][j].colspan, 2)

        hidden_cells_table_1_with_rowspan = [(2, 0), (2, 1)]
        for i, j in hidden_cells_table_1_with_rowspan:
            self.assertFalse(result.tables[0].metadata.cell_properties[i][j].invisible)
            self.assertEqual(result.tables[0].metadata.cell_properties[i][j].rowspan, 2)
            self.assertEqual(result.tables[0].metadata.cell_properties[i][j].colspan, 1)

        hidden_cells_table_2 = [(0, 3), (0, 4), (0, 5), (1, 1), (1, 5), (2, 0), (2, 1), (2, 3)]
        for i, j in hidden_cells_table_2:
            self.assertTrue(result.tables[1].metadata.cell_properties[i][j].invisible)
            self.assertEqual(result.tables[1].metadata.cell_properties[i][j].rowspan, 1)
            self.assertEqual(result.tables[1].metadata.cell_properties[i][j].colspan, 1)

        hidden_cells_table_2_with_colspan = [[(0, 2), 4], [(1, 4), 2]]
        for (i, j), k in hidden_cells_table_2_with_colspan:
            self.assertFalse(result.tables[1].metadata.cell_properties[i][j].invisible)
            self.assertEqual(result.tables[1].metadata.cell_properties[i][j].rowspan, 1)
            self.assertEqual(result.tables[1].metadata.cell_properties[i][j].colspan, k)

        # both colspan and rowspan check
        self.assertFalse(result.tables[1].metadata.cell_properties[1][0].invisible)
        self.assertEqual(result.tables[1].metadata.cell_properties[1][0].rowspan, 2)
        self.assertEqual(result.tables[1].metadata.cell_properties[1][0].colspan, 2)

        path = self._get_path("big_table_with_merged_cells.docx")
        result = any_doc_reader.read(path)
        hidden_cells_big_table = [(0, 1), (0, 2), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (3, 1), (3, 2), (3, 3), (4, 0), (4, 1), (4, 2), (4, 3), (5, 0), (5, 1), (5, 2), (5, 3), (5, 6), (5, 7), (5, 8), (5, 9)]
        for i, j in hidden_cells_big_table:
            self.assertTrue(result.tables[0].metadata.cell_properties[i][j].invisible)
            self.assertEqual(result.tables[0].metadata.cell_properties[i][j].rowspan, 1)
            self.assertEqual(result.tables[0].metadata.cell_properties[i][j].colspan, 1)

        hidden_cells_big_table_with_colspan = [[(1, 0), 10], [(5, 5), 5]]
        for (i, j), k in hidden_cells_big_table_with_colspan:
            self.assertFalse(result.tables[0].metadata.cell_properties[i][j].invisible)
            self.assertEqual(result.tables[0].metadata.cell_properties[i][j].rowspan, 1)
            self.assertEqual(result.tables[0].metadata.cell_properties[i][j].colspan, k)

        # both colspan and rowspan check
        self.assertFalse(result.tables[0].metadata.cell_properties[3][0].invisible)
        self.assertEqual(result.tables[0].metadata.cell_properties[3][0].rowspan, 3)
        self.assertEqual(result.tables[0].metadata.cell_properties[3][0].colspan, 4)

    def test_diagram_annotation(self) -> None:
        any_doc_reader = DocxReader(config=get_config())
        path = self._get_path("diagram_1.docx")
        result = any_doc_reader.read(path)

        for annotation in result.lines[0].annotations:
            if annotation.name == "attachment":
                self.assertEqual("dee352a576cf5ffd27ee1574d4dc4431", annotation.value)
            break

        path = self._get_path("diagram_2.docx")
        result = any_doc_reader.read(path)

        for i in [0, 22]:
            annotation_found = False
            for annotation in result.lines[i].annotations:
                if annotation.name == "attachment":
                    annotation_found = True
            self.assertTrue(annotation_found)

    def _get_path(self, file_name: str) -> str:
        path_in = os.path.join(self.directory, file_name)
        path_out = os.path.join(self.tmpdir.name, file_name)
        shutil.copy(path_in, path_out)
        return path_out

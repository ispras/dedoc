import os
import unittest
from collections import Counter
from typing import List, Dict

from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader
from tests.test_utils import tree2linear


class TestLawApiDocReader(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "laws", file_name)

    def test_law_image(self) -> None:
        file_name = "law_image.png"
        result = self._send_request(file_name, dict(document_type="law"))
        content = result["content"]
        self.assertEqual([], content["tables"])
        structure = content["structure"]
        self.__test_law_tree_sanity(structure)
        expected_text = "№ 206002-2016-16922\nот 18.07.16\nЛЕНИНГРАДСКАЯ ОБЛАСТЬ\nОБЛАСТНОЙ ЗАКОН\n" \
                        "Об экологическом образовании, просвещении и формировании\n" \
                        "экологической культуры в Ленинградской области\n" \
                        "(Принят Законодательным собранием Ленинградской области\n29 июня 2016 года)"
        expected_text = "\n".join(map(str.strip, expected_text.split("\n")))
        self.assertEqual(expected_text, "\n".join(filter(lambda t: t, map(str.strip, structure["text"].strip().split("\n")))))
        self.assertEqual("Глава 1. Общие положения", self._get_by_tree_path(structure, "0.0.0")["text"].strip())

    def _get_body(self, document_tree: dict) -> dict:
        body = document_tree["subparagraphs"][0]
        self.assertEqual("body", body["metadata"]["paragraph_type"])
        return body

    def _get_applications(self, document_tree: dict) -> List[dict]:
        applications = [node for node in document_tree["subparagraphs"] if node["metadata"]["paragraph_type"] == "application"]
        return applications

    def _check_ukrf(self, file_name: str) -> None:
        result = self._send_request(file_name, dict(document_type="law"))
        self.assertEqual(file_name, result["metadata"]["file_name"])
        document_tree = result["content"]["structure"]
        tables = result["content"]["tables"]

        annotations = document_tree["annotations"]
        self.assertGreater(len(annotations), 0)

        self.__test_law_tree_sanity(document_tree)
        self.assertTrue(document_tree["text"].strip().startswith("Уголовный кодекс"))

        article1 = self._get_by_tree_path(document_tree, "0.0.0")
        self.assertEqual("Статья 1. Уголовное законодательство Российской Федерации", article1["text"].strip())
        self.assertEqual("article", article1["metadata"]["paragraph_type"])

        part1 = self._get_by_tree_path(document_tree, "0.0.0.0")
        self.assertEqual("articlePart", part1["metadata"]["paragraph_type"])
        self.assertEqual("1.", part1["text"].strip())

        # check table annotations
        annotations = part1["annotations"]
        table_annotations = [annotation for annotation in annotations if annotation["name"] == TableAnnotation.name]
        self.assertEqual(1, len(table_annotations))
        part1_subparagraph = part1["subparagraphs"][0]
        annotations = part1_subparagraph["annotations"]
        table_annotations = [annotation for annotation in annotations if annotation["name"] == TableAnnotation.name]

        part2 = self._get_by_tree_path(document_tree, "0.0.0.1")
        self.assertEqual(0, len(table_annotations))
        self.assertEqual("2.", part2["text"].strip())
        self.assertEqual(1, len(tables))
        table = tables[0]
        self.assertListEqual(table["cells"][0], ["Столбец", "Строка"])
        self.assertListEqual(table["cells"][1], ["Первый", "Второй"])

    def test_law_doc(self) -> None:
        file_name = "ukrf.doc"
        self._check_ukrf(file_name)

    def test_law_docx(self) -> None:
        file_name = "ukrf.docx"
        self._check_ukrf(file_name)

    def test_law_odt(self) -> None:
        file_name = "ukrf.odt"
        self._check_ukrf(file_name)

    def test_law_article_multiline(self) -> None:
        file_name = "article_multiline.png"
        result = self._send_request(file_name, dict(document_type="law"), expected_code=200)
        document_tree = result["content"]["structure"]
        self.__test_law_tree_sanity(document_tree)

        article = self._get_by_tree_path(document_tree, "0.0.0")
        self.assertEqual('Статья 20.1. Представление сведений о расходах', article["text"].strip())
        self.assertEqual('article', article["metadata"]["paragraph_type"])

        item = self._get_by_tree_path(document_tree, "0.0.0.1")
        self.assertEqual('1.', item["text"].strip())
        self.assertEqual('articlePart', item["metadata"]["paragraph_type"])

        item = self._get_by_tree_path(document_tree, "0.0.0.2")
        self.assertEqual('2.', item["text"].strip())
        self.assertEqual('articlePart', item["metadata"]["paragraph_type"])

        item = self._get_by_tree_path(document_tree, "0.0.0.3")
        self.assertEqual('3.', item["text"].strip())
        self.assertEqual('articlePart', item["metadata"]["paragraph_type"])

        article = self._get_by_tree_path(document_tree, "0.0.1")
        self.assertEqual('Статья 20.2. Представление сведений о размещении информации в\n'
                         'информационно-телекоммуникационной сети "Интернет"', article["text"].strip())
        self.assertEqual('article', article["metadata"]["paragraph_type"])

        item = self._get_by_tree_path(document_tree, "0.0.1.1")
        self.assertEqual('1.', item["text"].strip())
        self.assertEqual('articlePart', item["metadata"]["paragraph_type"])

    def test_law_pdf_uc(self) -> None:
        file_name = "ukodeksrf.pdf"
        result = self._send_request(file_name, dict(document_type="law"), expected_code=200)
        document = result["content"]["structure"]
        self.assertEqual("Уголовный кодекс Российской Федерации от 13 июня 1996 г. М 63-ФЗ",
                         document["text"].split("\n")[0].strip())

        section = self._get_by_tree_path(document, "0.0.0")
        self.assertEqual("Раздел I. Уголовный закон", section["text"].strip())
        self.assertEqual("section", section["metadata"]["paragraph_type"])
        subsection = self._get_by_tree_path(document, "0.0.0.0")
        self.assertEqual("Глава 1. Задачи и принципы Уголовного кодекса Российской Федерации",
                         subsection["text"].strip())
        self.assertEqual("chapter", subsection["metadata"]["paragraph_type"])
        article = self._get_by_tree_path(document, "0.0.0.0.0")
        self.assertEqual("Статья 1. Уголовное законодательство Российской Федерации",
                         article["text"].strip())
        self.assertEqual("article", article["metadata"]["paragraph_type"])

    def test_law_pdf_with_applications(self) -> None:
        file_name = "with_applications.pdf"

        result = self._send_request(file_name, dict(document_type="law"), expected_code=200)
        document_tree = result["content"]["structure"]
        self.__test_law_tree_sanity(document_tree)

        self.assertIn('Утвержден\n', self._get_by_tree_path(document_tree, "0.1")['text'])
        self.assertIn('Приложение\n', self._get_by_tree_path(document_tree, "0.2")['text'])

    def test_chapter(self) -> None:
        # фстэк 17 это приказ, и в нем I. Общие положения трактуется как глава
        file_name = "fstek17.pdf"
        result = self._send_request(file_name, dict(document_type="law"), expected_code=200)
        document_tree = result["content"]["structure"]
        self.__test_law_tree_sanity(document_tree)

        node = self._get_by_tree_path(document_tree, "0.1.")
        self.assertEqual("cellar", node["metadata"]["paragraph_type"])
        self.assertEqual("ДИРЕКТОР ФЕДЕРАЛЬНОЙ СЛУЖБЫ\nПО ТЕХНИЧЕСКОМУ И ЭКСПОРТНОМУ КОНТРОЛЮ\nВ.СЕЛИН\n", node["text"])

        self.assertEqual("application", self._get_by_tree_path(document_tree, "0.2")["metadata"]["paragraph_type"])
        subsection = self._get_by_tree_path(document_tree, "0.2.0")
        self.assertEqual("chapter", subsection["metadata"]["paragraph_type"])
        self.assertEqual("I. Общие положения\n", subsection["text"])

    @unittest.skip("TODO fix this")
    def test_changes(self) -> None:
        file_name = "test_change.txt"
        result = self._send_request(file_name, dict(document_type="law"), expected_code=200)
        document_tree = result["content"]["structure"]
        self.__test_law_tree_sanity(document_tree)
        article1 = self._get_by_tree_path(document_tree, "0.0.0")
        self.assertEqual("Статья 1\n", article1["text"])
        self.assertEqual("article", article1["metadata"]["paragraph_type"])

        text_article1 = "".join([node["text"] for node in article1["subparagraphs"]])
        self.assertIn("Статью 521 Закона Российской Федерации от 9 октября 1992 года № 3612-I", text_article1)
        self.assertIn("Правительство Российской Федерации вправе при угрозе возникновения", text_article1)

        article2 = self._get_by_tree_path(document_tree, "0.0.1")
        self.assertEqual("Статья 2\n", article2["text"])
        self.assertEqual("article", article2["metadata"]["paragraph_type"])
        text_article2 = "".join([node["text"] for node in article2["subparagraphs"]])
        self.assertIn('Внести в Федеральный закон от 21 декабря 1994 года № 68-ФЗ "О защите населения', text_article2)
        self.assertIn("2004, № 35, ст. 3607; 2006, № 50, ст. 5284; 2009, № 1, ст. 17; № 48, ст. 5717;", text_article2)
        item1 = self._get_by_tree_path(document_tree, "0.0.1.1")
        self.assertEqual("1)", item1["text"])
        self.assertEqual("item", item1["metadata"]["paragraph_type"])

    @unittest.skip("TODO fix this. Here text of 1.0 on equal level with 1.1")
    def test_law_paragraphs(self) -> None:
        file_name = "minsport_24.12.2013_1112.txt"
        result = self._send_request(file_name, dict(document_type="law"), expected_code=200)
        document_tree = result["content"]["structure"]
        self.assertEqual("1.", self._get_by_tree_path(document_tree, "0.0.0")["text"].strip())
        self.assertEqual("item", self._get_by_tree_path(document_tree, "0.0.0")["metadata"]["paragraph_type"])
        self.assertTrue(self._get_by_tree_path(document_tree, "0.0.0.0")["text"].strip().startswith("Утвердить"))
        expected = "правила обработки персональных данных  в  Министерстве  спорта"
        self.assertEqual(expected, self._get_by_tree_path(document_tree, "0.0.0.1")["text"].strip()[0: len(expected)])

        # checking applications
        apps = self._get_applications(document_tree)
        self.assertEqual(5, len(apps))
        node = self._get_by_tree_path(document_tree, "0.1")
        self.assertTrue(node['text'].strip().startswith("Приложение N 1"))
        self.assertTrue(node['text'].strip().endswith("Российской Федерации"))
        self.assertEqual(node['metadata']['paragraph_type'], 'application')
        node = self._get_by_tree_path(document_tree, "0.2")
        self.assertTrue(node['text'].strip().startswith("Приложение N 2"))
        self.assertIn("Департамента   управления   делами", node['text'])
        self.assertTrue(node['text'].strip().endswith("____________"))
        self.assertEqual(node['metadata']['paragraph_type'], 'application')
        node = self._get_by_tree_path(document_tree, "0.3")
        self.assertTrue('Приложение N 3' in node['text'])
        self.assertEqual(node['metadata']['paragraph_type'], 'application')
        node = self._get_by_tree_path(document_tree, "0.4")
        self.assertTrue('Приложение N 4' in node['text'])
        self.assertEqual(node['metadata']['paragraph_type'], 'application')
        node = self._get_by_tree_path(document_tree, "0.5")
        self.assertTrue('Приложение N 5' in node['text'])
        self.assertEqual(node['metadata']['paragraph_type'], 'application')

        expected = "Отдел мобилизационной подготовки:"
        node = self._get_by_tree_path(document_tree, "0.3.0.6.0")
        self.assertEqual(expected, node["text"].strip()[0: len(expected)])

        expected = "начальник отдела;\n     заместитель начальника отдела;\n     советник;\n     консультант;"
        node = self._get_by_tree_path(document_tree, "0.3.0.6.1")
        self.assertEqual(expected, node["text"].strip()[0: len(expected)])

        expected = 'I. Общие положения'
        node = self._get_by_tree_path(document_tree, "0.1.0")
        self.assertEqual(expected, node["text"].strip()[0: len(expected)])
        self.assertEqual("chapter", node["metadata"]["paragraph_type"])

        expected = 'II. Процедуры, направленные на выявление и предотвращение\n' \
                   '          нарушений законодательства Российской Федерации\n ' \
                   '                   в сфере персональных данных'
        node = self._get_by_tree_path(document_tree, "0.1.1")
        self.assertEqual(expected, node["text"].strip()[0: len(expected)])
        self.assertEqual("chapter", node["metadata"]["paragraph_type"])

        expected = 'III. Цели обработки персональных данных, содержание\n' \
                   '     обрабатываемых персональных данных, категории субъектов,' \
                   '\n            персональные данные которых обрабатываются'
        node = self._get_by_tree_path(document_tree, "0.1.2")
        self.assertEqual(expected, node["text"].strip()[0: len(expected)])
        self.assertEqual("chapter", node["metadata"]["paragraph_type"])

        expected = 'IV. Содержание обрабатываемых персональных данных,\n' \
                   ' категории субъектов, персональные данные которых обрабатываются,\n' \
                   '        сроки их обработки и хранения, порядок уничтожения\n' \
                   '        при достижении целей обработки или при наступлении\n' \
                   '       иных законных оснований, определенные для каждой цели\n' \
                   '                   обработки персональных данных'
        node = self._get_by_tree_path(document_tree, "0.1.3")
        self.assertEqual(expected, node["text"].strip()[0: len(expected)])
        self.assertEqual("chapter", node["metadata"]["paragraph_type"])

    def test_foiv_txt(self) -> None:
        """
        Check hierarchy parsing application -> item ( 8. ) -> item ( 8.4. ) -> subitem ( 1) ) -> subitem ( a) )
        @return:
        """
        file_name = "prikaz_0.txt"
        result = self._send_request(file_name, dict(document_type="law"), expected_code=200)
        document_tree = result["content"]["structure"]
        self.assertTrue("Приложение" in self._get_by_tree_path(document_tree, "0.1")["text"].strip())
        node = self._get_by_tree_path(document_tree, "0.1.7")
        self.assertEqual("8.", node["text"].strip())
        self.assertEqual("item", node['metadata']['paragraph_type'])
        node = self._get_by_tree_path(document_tree, "0.1.7.4")
        self.assertEqual("8.4.", node["text"].strip())
        self.assertEqual("item", node['metadata']['paragraph_type'])
        node = self._get_by_tree_path(document_tree, "0.1.7.4.1")
        self.assertEqual("1)", node["text"].strip())
        self.assertEqual("subitem", node['metadata']['paragraph_type'])
        node = self._get_by_tree_path(document_tree, "0.1.7.4.1.1")
        self.assertEqual("а)", node["text"].strip())
        self.assertEqual("subitem", node['metadata']['paragraph_type'])

    def test_application_txt(self) -> None:
        file_name = "law_application.txt"
        result = self._send_request(file_name, dict(document_type="law"), expected_code=200)
        document_tree = result["content"]["structure"]
        node = self._get_by_tree_path(document_tree, "0.1")
        self.assertTrue(node["text"].strip().startswith(
            "УТВЕРЖДЕНЫ\n\nпостановлением Правительства\n\nРоссийской Федерации"))
        self.assertEqual("application", node['metadata']['paragraph_type'])

        node = self._get_by_tree_path(document_tree, "0.1.0")
        self.assertEqual(node["text"].strip(), "I. Общие положения")
        self.assertEqual("subsection", node['metadata']['paragraph_type'])

        node = self._get_by_tree_path(document_tree, "0.1.0.1")
        self.assertEqual(node["text"].strip(), "1.")
        self.assertEqual("articlePart", node['metadata']['paragraph_type'])

        node = self._get_by_tree_path(document_tree, "0.1.4.1.6")
        self.assertEqual(node["text"].strip(), "е)")
        self.assertEqual("subitem", node['metadata']['paragraph_type'])

    @unittest.skip("TODO fix this")
    def test_number_not_part(self) -> None:
        file_name = "31(1).txt"
        result = self._send_request(file_name, dict(document_type="law"), expected_code=200)
        document_tree = result["content"]["structure"]
        self.__test_law_tree_sanity(document_tree)
        node = self._get_by_tree_path(document_tree, "0.0.3.5.0.0")
        self.assertTrue(node["text"].strip().endswith("2 настоящей статьи."))
        self.assertEqual("raw_text", node['metadata']['paragraph_type'])

    def test_application_multiline(self) -> None:
        file_name = "13.txt"
        result = self._send_request(file_name, dict(document_type="law"), expected_code=200)
        document_tree = result["content"]["structure"]
        self.__test_law_tree_sanity(document_tree)
        app01 = self._get_by_tree_path(document_tree, "0.1")
        self.assertTrue(app01["text"].strip().startswith("Приложение № 1"))
        self.assertEqual("application", app01["metadata"]["paragraph_type"])

        app02 = self._get_by_tree_path(document_tree, "0.2")
        self.assertTrue(app02["text"].strip().startswith("Приложение № 2"))
        self.assertTrue(app02["text"].strip().endswith("Дальнего Востока"))
        self.assertEqual("application", app02["metadata"]["paragraph_type"])

        app03 = self._get_by_tree_path(document_tree, "0.3")
        self.assertTrue(app03["text"].strip().startswith("Приложение № 3"))
        self.assertTrue(app03["text"].strip().endswith("_____________"))
        self.assertIn("Утвержден", app03["text"])
        self.assertEqual("application", app03["metadata"]["paragraph_type"])

        app04 = self._get_by_tree_path(document_tree, "0.4")
        self.assertTrue(app04["text"].strip().startswith("Приложение № 4"))
        self.assertTrue(app04["text"].strip().endswith("_____________"))
        self.assertIn("Утвержден", app04["text"])
        self.assertEqual("application", app04["metadata"]["paragraph_type"])

        app05 = self._get_by_tree_path(document_tree, "0.5")
        self.assertTrue(app05["text"].strip().startswith("Приложение № 5"))
        self.assertTrue(app05["text"].strip().endswith("Я ознакомлен(а), что:"))
        self.assertIn("Утверждена", app05["text"])
        self.assertEqual("application", app05["metadata"]["paragraph_type"])

    @unittest.skip("TODO fix this")
    def test_auto_paragraph(self) -> None:
        file_name = "fstec_1_cut.pdf"
        result = self._send_request(file_name, dict(document_type="law",
                                                    pdf_with_text_layer="false",
                                                    is_one_column_document="auto"))
        tree = result["content"]["structure"]
        self.__test_law_tree_sanity(tree)
        warnings = result["warnings"]
        self.assertIn("Use foiv_law classifier", warnings)
        self.assertNotIn("assume document has 2 columns", warnings)
        node = self._get_by_tree_path(tree, "0.")
        self.assertEqual("root", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(tree, "0.0")
        self.assertEqual("body", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(tree, "0.0.0")
        self.assertEqual("item", node["metadata"]["paragraph_type"])
        self.assertEqual("1.", node["text"].strip())

        node = self._get_by_tree_path(tree, "0.0.0.0")
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])
        self.assertEqual("Утвердить прилагаемые Требован", node["text"][:30])

        node = self._get_by_tree_path(tree, "0.1")
        self.assertEqual("cellar", node["metadata"]["paragraph_type"])
        self.assertEqual("ДИРЕКТОР ФЕДЕРАЛЬНОЙ СЛУЖБЫ\nПО", node["text"][:30])

        node = self._get_by_tree_path(tree, "0.2.0")
        self.assertEqual("chapter", node["metadata"]["paragraph_type"])
        self.assertEqual("""I. Общие положения""", node["text"].strip())

        node = self._get_by_tree_path(tree, "0.2.0.1")
        self.assertEqual("item", node["metadata"]["paragraph_type"])
        self.assertEqual("""2.""", node["text"].strip())

        node = self._get_by_tree_path(tree, "0.2.0.1.0")
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])
        self.assertEqual("В документе устанавливаются тр", node["text"][:30])

        node = self._get_by_tree_path(tree, "0.2.0.1.1")
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])
        self.assertEqual("Настоящие Требования могут при", node["text"][:30])

        node = self._get_by_tree_path(tree, "0.2.0.1.2")
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])
        self.assertEqual("В документе не рассматриваются", node["text"][:30])

    def test_txt(self) -> None:
        file_name = "bfcd7a4e9bc4498cbe591153e341e0b9.txt"
        result = self._send_request(file_name, dict(document_type="law"), expected_code=200)
        tree = result["content"]["structure"]
        self.__test_law_tree_sanity(tree)
        text = self._get_by_tree_path(tree, "0")["text"].strip()
        self.assertIn("ГЛАВА РЕСПУБЛИКИ ТЫВА", text)
        self.assertTrue(text.endswith(" - Председателя Правительства Республики Тыва» постановляю:"))

    def test_chapter_article(self) -> None:
        file_name = "14_dev_direct.pdf"
        result = self._send_request(file_name, dict(document_type="law"), expected_code=200)
        tree = result["content"]["structure"]
        self.__test_law_tree_sanity(tree)

        node = self._get_by_tree_path(tree, "0")
        self.assertEqual("РОССИЙСКАЯ ФЕДЕРАЦИЯ ПРОЕКТ ФЕ", node["text"][:30].strip())
        self.assertEqual("root", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(tree, "0.0")
        self.assertEqual("", node["text"][:30].strip())
        self.assertEqual("body", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(tree, "0.0.0")
        self.assertEqual("Глава 1. Общие положения", node["text"][:30].strip())
        self.assertEqual("chapter", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(tree, "0.0.0.2")
        self.assertEqual("Статья 4. Трансграничная перед", node["text"][:30].strip())
        self.assertEqual("article", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(tree, "0.0.0.2.0")
        self.assertEqual("В соответствии со статьей 3 Фе", node["text"][:30].strip())
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(tree, "0.0.0.1")
        self.assertEqual("Статья 3. Основные понятия, ис", node["text"][:30].strip())
        self.assertEqual("article", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(tree, "0.0.0.1.0")
        self.assertEqual("В целях настоящего Федеральног", node["text"][:30].strip())
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(tree, "0.0.0.0")
        self.assertEqual("Статья 1. Сфера действия насто", node["text"][:30].strip())
        self.assertEqual("article", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(tree, "0.0.0.0.0")
        self.assertEqual("1.", node["text"][:30].strip())
        self.assertEqual("articlePart", node["metadata"]["paragraph_type"])

        node = self._get_by_tree_path(tree, "0.0.0.0.0.0")
        self.assertEqual("Настоящим Федеральным законом", node["text"][:30].strip())
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])

    def __test_law_tree_sanity(self, tree: Dict[str, dict]) -> None:
        self._check_tree_sanity(tree)
        linear = tree2linear(tree)
        cnt = Counter()
        for item in linear:
            cnt[item["metadata"]["paragraph_type"]] += 1
        self.assertEqual(1, cnt["root"], "Document should have only one root, get {}".format(cnt["root"]))
        self.assertEqual(1, cnt["body"], "Document should have only one body, get {}".format(cnt["body"]))

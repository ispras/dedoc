from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiDocReader(AbstractTestApiDocReader):

    def test_list_nesting_content(self) -> None:
        file_name = "docx/pr14tz_v5_2007_03_01.docx"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]

        lst = content["subparagraphs"][2]
        self.assertEqual(lst["subparagraphs"][4]["text"], "1.5.\tОснования разработки")
        self.assertEqual(lst["subparagraphs"][5]["text"], "1.6.\tНормативные документы")
        self.assertEqual(lst["subparagraphs"][6]["text"], "1.7.\tСведения об источниках и порядке финансирования работ")
        self.assertEqual(len(lst["subparagraphs"][5]["subparagraphs"][0]["subparagraphs"]), 12)

        lst = content["subparagraphs"][5]
        lst = lst["subparagraphs"][0]["subparagraphs"][0]
        self.assertEqual(lst["text"], "4.1.1.	Требования к структуре и функционированию")
        self.assertEqual(lst["subparagraphs"][0]["text"].startswith("Система должна иметь базу хранения"), True)
        self.assertEqual(len(lst["subparagraphs"][1]["subparagraphs"]), 13)

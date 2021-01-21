from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiDocReader(AbstractTestApiDocReader):

    def test_list_patching(self):
        file_name = "13_moloko_1_polug.docx"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]

        lst = content["subparagraphs"][2]
        self.assertEqual(len(lst["subparagraphs"][0]["subparagraphs"]), 6)
        self.assertEqual(lst["subparagraphs"][0]["subparagraphs"][2]["text"], "2.3.")

    def test_list_patching_2(self):
        file_name = "list_tests/missed_list.docx"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]

        list = content["subparagraphs"][0]
        self.assertEqual(len(list["subparagraphs"]), 6)
        self.assertEqual(list["subparagraphs"][0]["text"], "1. list item 1")
        self.assertEqual(list["subparagraphs"][1]["text"], "2. list item 2")
        self.assertEqual(list["subparagraphs"][2]["text"], "3. list item 3")
        self.assertEqual(list["subparagraphs"][3]["text"], "4. list item 4")
        self.assertEqual(list["subparagraphs"][4]["text"], "5.")
        self.assertEqual(list["subparagraphs"][5]["text"], "6. list item 6")

        list = list["subparagraphs"][5]["subparagraphs"][0]
        self.assertEqual(len(list["subparagraphs"]), 5)
        self.assertEqual(list["subparagraphs"][0]["text"], "6.1. list item 6.1")
        self.assertEqual(list["subparagraphs"][1]["text"], "6.2.")
        self.assertEqual(list["subparagraphs"][2]["text"], "6.3 list item 6.3")
        self.assertEqual(list["subparagraphs"][3]["text"], "6.4.")
        self.assertEqual(list["subparagraphs"][4]["text"], "6.5 list item 6.5")

        list = list["subparagraphs"][2]["subparagraphs"][1]
        self.assertEqual(len(list["subparagraphs"]), 2)
        self.assertEqual(list["subparagraphs"][0]["text"], "6.3.1.")
        self.assertEqual(list["subparagraphs"][1]["text"], "6.3.2.")

        list = list["subparagraphs"][1]["subparagraphs"][0]
        self.assertEqual(len(list["subparagraphs"]), 4)
        self.assertEqual(list["subparagraphs"][0]["text"], "6.3.2.1.")
        self.assertEqual(list["subparagraphs"][1]["text"], "6.3.2.2.")
        self.assertEqual(list["subparagraphs"][2]["text"], "6.3.2.3 list item 6.3.2.3")
        self.assertEqual(list["subparagraphs"][3]["text"], "6.3.2.4. list item 6.3.2.4")



from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestListPatching(AbstractTestApiDocReader):

    def test_list_patching(self) -> None:
        file_name = "docx/13_moloko_1_polug.docx"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]

        lst = content["subparagraphs"][1]
        self.assertEqual(len(lst["subparagraphs"]), 12)

    def test_list_patching_2(self) -> None:
        file_name = "list_tests/missed_list.docx"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]

        subparagraphs = content["subparagraphs"][0]["subparagraphs"][0]
        self.assertEqual(len(subparagraphs["subparagraphs"]), 5)
        self.assertEqual(subparagraphs["subparagraphs"][0]["text"].strip(), "1. list item 1")
        self.assertEqual(subparagraphs["subparagraphs"][1]["text"].strip(), "2. list item 2")
        self.assertEqual(subparagraphs["subparagraphs"][2]["text"].strip(), "3. list item 3")
        self.assertEqual(subparagraphs["subparagraphs"][3]["text"].strip(), "4. list item 4")
        self.assertEqual(subparagraphs["subparagraphs"][4]["text"].strip(), "6. list item 6")

        subparagraphs = subparagraphs["subparagraphs"][4]["subparagraphs"][0]
        self.assertEqual(len(subparagraphs["subparagraphs"]), 3)
        self.assertEqual(subparagraphs["subparagraphs"][0]["text"].strip(), "6.1. list item 6.1")
        self.assertEqual(subparagraphs["subparagraphs"][1]["text"].strip(), "6.3 list item 6.3")
        self.assertEqual(subparagraphs["subparagraphs"][2]["text"].strip(), "6.5 list item 6.5")

        subparagraphs = subparagraphs["subparagraphs"][1]["subparagraphs"][1]

        self.assertEqual(len(subparagraphs["subparagraphs"]), 2)
        self.assertEqual(subparagraphs["subparagraphs"][0]["text"].strip(), "6.3.2.3 list item 6.3.2.3")
        self.assertEqual(subparagraphs["subparagraphs"][1]["text"].strip(), "6.3.2.4. list item 6.3.2.4")

    def test_list_patching_3(self) -> None:
        file_name = "list_tests/missed_list_2.docx"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]

        subparagraphs = content["subparagraphs"][0]["subparagraphs"][0]
        self.assertEqual(len(subparagraphs["subparagraphs"]), 5)
        self.assertEqual(subparagraphs["subparagraphs"][0]["text"].strip(), "1. list item 1")
        self.assertEqual(subparagraphs["subparagraphs"][1]["text"].strip(), "2. list item 2")
        self.assertEqual(subparagraphs["subparagraphs"][2]["text"].strip(), "3. list item 3")
        self.assertEqual(subparagraphs["subparagraphs"][3]["text"].strip(), "4. list item 4")
        self.assertEqual(subparagraphs["subparagraphs"][4]["text"].strip(), "6. list item 6")

        self.assertEqual(subparagraphs["subparagraphs"][1]["subparagraphs"][0]["subparagraphs"][0]["text"].strip(), "1)")
        self.assertEqual(subparagraphs["subparagraphs"][1]["subparagraphs"][0]["subparagraphs"][1]["text"].strip(), "3)")
        # self.assertEqual(subparagraphs["subparagraphs"][1]["subparagraphs"][0]["subparagraphs"][2]["text"].strip(), "4)")
        # self.assertEqual(subparagraphs["subparagraphs"][1]["subparagraphs"][0]["subparagraphs"][3]["text"].strip(), "7)")

        subparagraphs = subparagraphs["subparagraphs"][4]["subparagraphs"][0]
        self.assertEqual(len(subparagraphs["subparagraphs"]), 3)
        self.assertEqual(subparagraphs["subparagraphs"][0]["text"].strip(), "6.1. list item 6.1")
        # self.assertEqual(subparagraphs["subparagraphs"][1]["text"], "6.2.")
        self.assertEqual(subparagraphs["subparagraphs"][1]["text"].strip(), "6.3 list item 6.3")
        # self.assertEqual(list["subparagraphs"][3]["text"], "6.4.")
        self.assertEqual(subparagraphs["subparagraphs"][2]["text"].strip(), "6.5 list item 6.5")

        subparagraphs = subparagraphs["subparagraphs"][1]["subparagraphs"][1]

        self.assertEqual(len(subparagraphs["subparagraphs"]), 2)
        self.assertEqual(subparagraphs["subparagraphs"][0]["text"].strip(), "6.3.2.3. list item 6.3.2.3")
        self.assertEqual(subparagraphs["subparagraphs"][1]["text"].strip(), "6.3.2.4. list item 6.3.2.4")

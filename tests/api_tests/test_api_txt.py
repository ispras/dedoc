from tests.api_tests.abstrac_api_test import AbstractTestApiDocReader


class TestApiTxtReader(AbstractTestApiDocReader):

    def test_txt_file(self):
        file_name = "Pr_2013.02.18_21.txt"
        result = self._send_request(file_name)

    def test_text(self):
        file_name = "doc_001.txt"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]
        self.assertEqual(content["subparagraphs"][1]["text"].rstrip(),
                         '     Статья 1. Сфера действия настоящёго Федерального закона')

        self._check_metainfo(result['metadata'], 'text/plain', file_name)

    def test_text2(self):
        file_name = "pr_17.txt"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]
        res = str(content)
        self.assertFalse("ufeff" in res)

    def test_paragraphs(self):
        file_name = "football.txt"
        result = self._send_request(file_name, data={"structure_type": "tree"})
        content = result["content"]["structure"]["subparagraphs"]
        self.assertEqual(4, len(content))
        node = content[0]
        self.assertTrue(node["text"].startswith("    Association football, more commonly known as simply"))
        self.assertTrue(node["text"].endswith("The team with the higher number of goals wins the game.\n\n"))
        annotations = node["annotations"]
        self.assertIn({'name': 'spacing', 'value': '50', 'start': 0, 'end': 546}, annotations)

        node = content[1]
        self.assertTrue(node["text"].startswith("  Football is played in accordance with a set of rules known"))
        self.assertTrue(node["text"].strip().endswith("the coin toss prior to kick-off or penalty kicks."))
        annotations = node["annotations"]
        self.assertIn({'name': 'spacing', 'value': '100', 'start': 0, 'end': 163}, annotations)

        node = content[2]
        self.assertTrue(node["text"].startswith("    Football is governed internationally by the International"))
        self.assertTrue(node["text"].endswith("the 2019 FIFA Women's World Cup in France.\n\n"))
        annotations = node["annotations"]
        self.assertIn({'name': 'spacing', 'value': '400', 'start': 0, 'end': 164}, annotations)
        self.assertIn({'name': 'spacing', 'value': '50', 'start': 164, 'end': 1068}, annotations)

        self.assertTrue(content[3]["text"].startswith("    The most prestigious competitions in European club"))
        self.assertTrue(content[3]["text"].endswith("cost in excess of £600 million/€763 million/US$1.185 billion.\n"))

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestArticleApi(AbstractTestApiDocReader):

    def test_article(self) -> None:
        file_name = "article.pdf"
        result = self._send_request(file_name, dict(document_type="article"))
        content = result["content"]
        self.assertEqual([], content["tables"])
        structure = content["structure"]
        self.assertEqual(structure["text"], "Masking and Leakage-Resilient Primitives: One, the Other(s) or Both?")
        first_author = structure["subparagraphs"][0]
        self.assertEqual(first_author["metadata"]["paragraph_type"], "author")
        self.assertEqual(first_author["subparagraphs"][0]["text"], "Sonia")

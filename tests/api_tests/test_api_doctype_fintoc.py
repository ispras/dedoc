from api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiFintoc(AbstractTestApiDocReader):

    def test_article_en(self) -> None:
        file_name = "pdf_with_text_layer/prospectus.pdf"
        result = self._send_request(file_name, dict(document_type="fintoc", pdf_with_text_layer="true"))

        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)

        # headers
        node = self._get_by_tree_path(tree, "0.1")
        self.assertEqual("header", node["metadata"]["paragraph_type"])
        self.assertEqual("Prospectus", node["text"].strip())
        node = self._get_by_tree_path(tree, "0.1.2")
        self.assertEqual("header", node["metadata"]["paragraph_type"])
        self.assertEqual("TABLE OF CONTENTS", node["text"].strip())

        # raw text
        node = self._get_by_tree_path(tree, "0.1.2.0")
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])
        self.assertTrue(node["text"].startswith("PART I - GENERAL INFORMATION"))

    def test_article_fr(self) -> None:
        file_name = "pdf_with_text_layer/prospectus_fr.pdf"
        result = self._send_request(file_name, dict(document_type="fintoc", pdf_with_text_layer="true", language="fr"))

        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)

        # headers
        node = self._get_by_tree_path(tree, "0.0")
        self.assertEqual("header", node["metadata"]["paragraph_type"])
        self.assertEqual("INFORMATIONS CLES POUR L’INVESTISSEUR", node["text"].strip())
        node = self._get_by_tree_path(tree, "0.1")
        self.assertEqual("header", node["metadata"]["paragraph_type"])
        self.assertEqual("Prospectus", node["text"].strip())

        # raw text
        node = self._get_by_tree_path(tree, "0.1.0")
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])
        self.assertEqual("OPCVM relevant de la directive européenne 2009/65/CE", node["text"].strip())

    def test_article_sp(self) -> None:
        file_name = "pdf_with_text_layer/prospectus_sp.pdf"
        result = self._send_request(file_name, dict(document_type="fintoc", pdf_with_text_layer="true", language="sp"))

        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)

        # headers
        node = self._get_by_tree_path(tree, "0.0")
        self.assertEqual("header", node["metadata"]["paragraph_type"])
        self.assertEqual("INFORME ANUAL", node["text"].strip())
        node = self._get_by_tree_path(tree, "0.0.1")
        self.assertEqual("header", node["metadata"]["paragraph_type"])
        self.assertEqual("ÍNDICE.", node["text"].strip())

        # raw text
        node = self._get_by_tree_path(tree, "0.0.0")
        self.assertEqual("raw_text", node["metadata"]["paragraph_type"])
        self.assertTrue(node["text"].startswith("2015"))

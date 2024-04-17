from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiArticle(AbstractTestApiDocReader):

    def test_article(self) -> None:
        file_name = "pdf_with_text_layer/article.pdf"
        result = self._send_request(file_name, dict(document_type="article"))
        self.assertEqual(result["warnings"], ["use GROBID (version: 0.8.0)"])

        tree = result["content"]["structure"]
        self._check_tree_sanity(tree)

        # author 1 info
        self.assertEqual("author", self._get_by_tree_path(tree, "0.0")["metadata"]["paragraph_type"])
        self.assertEqual("author_first_name", self._get_by_tree_path(tree, "0.0.0")["metadata"]["paragraph_type"])  # author 1 first name
        self.assertEqual("Sonia", self._get_by_tree_path(tree, "0.0.0")["text"])
        self.assertEqual("author_surname", self._get_by_tree_path(tree, "0.0.1")["metadata"]["paragraph_type"])  # author 1 second name
        self.assertEqual("Belaïd", self._get_by_tree_path(tree, "0.0.1")["text"])
        self.assertEqual("author_affiliation", self._get_by_tree_path(tree, "0.0.2")["metadata"]["paragraph_type"])  # the first affiliation of author 1
        self.assertEqual("org_name", self._get_by_tree_path(tree, "0.0.2.0")["metadata"]["paragraph_type"])
        self.assertEqual("École Normale Supérieure", self._get_by_tree_path(tree, "0.0.2.0")["text"])
        self.assertEqual("author_affiliation", self._get_by_tree_path(tree, "0.0.3")["metadata"]["paragraph_type"])  # the second affiliation of author 1
        self.assertEqual("org_name", self._get_by_tree_path(tree, "0.0.3.0")["metadata"]["paragraph_type"])
        self.assertEqual("Thales Communications & Security", self._get_by_tree_path(tree, "0.0.3.0")["text"])

        # author 3 info
        self.assertEqual("author", self._get_by_tree_path(tree, "0.2")["metadata"]["paragraph_type"])
        self.assertEqual("author_first_name", self._get_by_tree_path(tree, "0.2.0")["metadata"]["paragraph_type"])  # author 3 first name
        self.assertEqual("François", self._get_by_tree_path(tree, "0.2.0")["text"])
        self.assertEqual("author_surname", self._get_by_tree_path(tree, "0.2.1")["metadata"]["paragraph_type"])  # author 3 second name
        self.assertEqual("Xavier-Standaert", self._get_by_tree_path(tree, "0.2.1")["text"])
        self.assertEqual("author_affiliation", self._get_by_tree_path(tree, "0.2.2")["metadata"]["paragraph_type"])  # the first affiliation of author 3
        self.assertEqual("org_name", self._get_by_tree_path(tree, "0.2.2.0")["metadata"]["paragraph_type"])
        self.assertEqual("ICTEAM/ELEN/Crypto Group", self._get_by_tree_path(tree, "0.2.2.0")["text"])

        # check bibliography list
        self.assertEqual("bibliography", self._get_by_tree_path(tree, "0.20")["metadata"]["paragraph_type"])
        self.assertEqual(65, len(self._get_by_tree_path(tree, "0.20")["subparagraphs"]))

        # check bib_item 1 recognizing
        self.assertEqual("title", self._get_by_tree_path(tree, "0.20.0.0")["metadata"]["paragraph_type"])
        self.assertEqual("Leakage-resilient symmetric encryption via re-keying", self._get_by_tree_path(tree, "0.20.0.0")["text"])
        self.assertEqual("title_conference_proceedings", self._get_by_tree_path(tree, "0.20.0.1")["metadata"]["paragraph_type"])
        self.assertEqual("Bertoni and Coron", self._get_by_tree_path(tree, "0.20.0.1")["text"])
        self.assertEqual("author", self._get_by_tree_path(tree, "0.20.0.2")["metadata"]["paragraph_type"])  # author 1
        self.assertEqual("\nMichelAbdalla\n", self._get_by_tree_path(tree, "0.20.0.2")["text"])
        self.assertEqual("biblScope_volume", self._get_by_tree_path(tree, "0.20.0.5")["metadata"]["paragraph_type"])  # author 1
        self.assertEqual("4", self._get_by_tree_path(tree, "0.20.0.5")["text"])
        self.assertEqual("biblScope_page", self._get_by_tree_path(tree, "0.20.0.6")["metadata"]["paragraph_type"])  # author 1
        self.assertEqual("471-488", self._get_by_tree_path(tree, "0.20.0.6")["text"])

        # check cite on bib_item
        bibliography_item_uuid = self._get_by_tree_path(tree, "0.20.57")["metadata"]["uid"]  # checking on [58] references
        section = self._get_by_tree_path(tree, "0.4.0")
        bibliography_refs_in_text = [ann for ann in section["annotations"] if ann["name"] == "reference" and ann["value"] == bibliography_item_uuid]
        # We must found two refs [58] in Introduction section
        self.assertEqual(len(bibliography_refs_in_text), 2)
        self.assertEqual(["58,", "58,"], [section["text"][bibliography_refs_in_text[n]["start"]:bibliography_refs_in_text[n]["end"]] for n in range(2)])

        # check tables
        self.assertEqual(len(result["content"]["tables"]), 2)
        table = result["content"]["tables"][0]
        self.assertEqual(table["metadata"]["title"], "Table 1 .Performance of some illustrative AES implementations.")
        self.assertEqual(self._get_text_of_row(table["cells"][0]), ["Software (8-bit)", "code size", "cycle", "cost", "physical"])
        section_with_table_refs = self._get_by_tree_path(tree, "0.7.0")
        table_refs_in_text = [ann for ann in section_with_table_refs["annotations"] if ann["name"] == "table" and ann["value"] == table["metadata"]["uid"]]
        self.assertEqual(len(table_refs_in_text), 2)
        self.assertEqual(["1", "1"], [section_with_table_refs["text"][table_refs_in_text[n]["start"]:table_refs_in_text[n]["end"]] for n in range(2)])

        table = result["content"]["tables"][1]  # Grobid can't recognize vertical orientation tables
        self.assertEqual(table["metadata"]["title"], "Table 2 .List of our target implementations.")

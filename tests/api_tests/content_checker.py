import unittest
from typing import List, Union


class ContentChecker(unittest.TestCase):

    def _get_by_tree_path(self, tree: dict, path: Union[List[int], str]) -> dict:
        if isinstance(path, str):
            path = [int(i) for i in path.split(".") if len(i) > 0][1:]
        for child_id in path:
            tree = tree["subparagraphs"][child_id]
        return tree

    def _get_text_of_row(self, row: dict) -> List[str]:
        result = []
        for cell in row:
            result.append("\n".join([line["text"] for line in cell["lines"]]))
        return result

    def _check_tree_sanity(self, tree: dict) -> None:
        """
        sanity check for document tree (for example that there is all required keys, annotations not duplicated etc)
        @param tree:
        @return:
        """
        stack = [tree]
        node_id_set = set()
        while len(stack) > 0:
            # check that node id is unique
            node = stack.pop()
            # Check required fields
            self.assertIn("node_id", node)
            self.assertIn("text", node)
            self.assertIn("annotations", node)
            self.assertIn("metadata", node)
            self.assertIn("subparagraphs", node)

            node_id = node["node_id"]
            self.assertNotIn(node_id, node_id_set)
            node_id_set.add(node_id)
            annotations = [(a["name"], a["value"], a["end"], a["start"]) for a in node["annotations"]]
            self.assertEqual(len(set(annotations)), len(annotations))

            # check that metadata in line
            self.assertIn("metadata", node)

            # add subparagraphs
            for subparagraph in node["subparagraphs"]:
                stack.append(subparagraph)

    def _check_required_fields(self, result: dict) -> None:
        """
        check required fields in doc reader result
        """
        stack = [result]
        document_list = []
        while len(stack) > 0:
            document = stack.pop()
            stack.extend(document.get("attachments", []))
            document_list.append(document)
        for document in document_list:
            metadata = document["metadata"]
            self.__check_metadata(metadata)
            content = document["content"]
            self.assertIn("warnings", document)
            self.assertIn("tables", content)
            tree = content["structure"]
            self._check_tree_sanity(tree=tree)

    def __check_metadata(self, metadata: dict) -> None:
        self.assertIn("file_name", metadata)
        self.assertIsInstance(metadata["file_name"], str)
        self.assertIn("size", metadata)
        self.assertIsInstance(metadata["size"], int)
        self.assertIn("modified_time", metadata)
        self.assertIsInstance(metadata["modified_time"], int)
        self.assertIn("created_time", metadata)
        self.assertIsInstance(metadata["created_time"], int)
        self.assertIn("access_time", metadata)
        self.assertIsInstance(metadata["access_time"], int)
        if "file_type" in metadata:
            self.assertIsInstance(metadata["file_type"], str)

    def _check_english_doc(self, result: dict) -> None:
        content = result["content"]
        structure = content["structure"]
        self._check_tree_sanity(structure)
        self.assertEqual("THE GREAT ENGLISH DOCUMENT", structure["subparagraphs"][0]["text"].strip())
        list_elements = structure["subparagraphs"][1]["subparagraphs"]
        self.assertEqual("1) Fisrst item with some english text", list_elements[0]["text"].strip())
        self.assertEqual("2) Second item with some even more inglish text. Let me speek from my heart", list_elements[1]["text"].strip())
        table = content["tables"][0]["cells"]
        self.assertListEqual(["London", "The capital of Great Britain"], self._get_text_of_row(table[0]))
        self.assertListEqual(["Speek", "From my heart"], self._get_text_of_row(table[1]))

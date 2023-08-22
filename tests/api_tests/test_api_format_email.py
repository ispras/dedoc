import os

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiEmailReader(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "eml", file_name)

    def test_email_file(self) -> None:
        file_name = "spam_mail.eml"
        result = self._send_request(file_name, data={"with_attachments": "true"})
        attachments = result["attachments"]

        self.assertEqual(len(attachments), 1)  # message header fields
        self.assertIn("message_header_", attachments[0]["metadata"]["file_name"])
        content = result["content"]
        structure = content["structure"]
        self._check_tree_sanity(structure)
        self.assertEqual("[Spam]Artificial flowers  for decors", structure["text"])

        # require fields [subject, from, to, cc, bcc, date, reply-to]

        from_message = structure["subparagraphs"][1]
        to_message = structure["subparagraphs"][2]
        self.assertEqual("modis@ispras.ru", to_message["text"])
        self.assertEqual("to", to_message["metadata"]["paragraph_type"])
        self.assertEqual('"sunny_goldensun@126.com" <sunny_goldensun@126.com>', from_message["text"])
        self.assertEqual("from", from_message["metadata"]["paragraph_type"])

    def test_email_with_attachments(self) -> None:
        file_name = "message.eml"
        result = self._send_request(file_name, data={"with_attachments": "true"})
        structure = result["content"]["structure"]
        attachments = result["attachments"]
        self._check_tree_sanity(structure)

        self.assertEqual("TetSubj", structure["text"])
        from_message = structure["subparagraphs"][1]
        to_message = structure["subparagraphs"][2]
        self.assertEqual('"bb@bb.bb" <bb@bb.bb>', to_message["text"])
        self.assertEqual("to", to_message["metadata"]["paragraph_type"])
        self.assertEqual('"aa@aa.aa" <aa@aa.aa>', from_message["text"])
        self.assertEqual("from", from_message["metadata"]["paragraph_type"])

        self.assertEqual(3, len(attachments))
        self.assertIn("message_header_", attachments[0]["metadata"]["file_name"])
        self.assertEqual("grafana.jpg", attachments[1]["metadata"]["file_name"])
        self.assertEqual("KY100Product SheetProduct Sheet.pdf", attachments[2]["metadata"]["file_name"])

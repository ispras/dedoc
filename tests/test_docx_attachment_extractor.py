import unittest
import os
from dedoc.attachments_extractors.concrete_attach_extractors.docx_attachments_extractor import DocxAttachmentsExtractor
from dedoc.utils import get_file_mime_type


class TestDocxAttachmentsExtractor(unittest.TestCase):

    def test_example_1_2_3(self):
        docx_attachment_extractor = DocxAttachmentsExtractor()
        tmp_dir = os.path.join(os.path.dirname(__file__), 'data/with_attachments_docx/')
        extracted = 0
        for i in range(1, 4):
            filename = f'with_attachments_{i}.docx'
            mime = get_file_mime_type(os.path.join(tmp_dir, filename))
            self.assertTrue(docx_attachment_extractor.can_extract(mime, filename))
            attachments = docx_attachment_extractor.get_attachments(tmp_dir, filename, {})
            for attachment_name, attachment_data in attachments:
                with open(os.path.join(tmp_dir, attachment_name), 'rb') as f:
                    self.assertEqual(f.read(), attachment_data)
                    extracted += 1
        self.assertEqual(extracted, 24)
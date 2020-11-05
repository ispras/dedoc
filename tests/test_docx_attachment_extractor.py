import unittest
import os
import hashlib
from dedoc.attachments_extractors.concrete_attachments_extractors.docx_attachments_extractor import DocxAttachmentsExtractor
from dedoc.utils import get_file_mime_type


class TestDocxAttachmentsExtractor(unittest.TestCase):

    def test_example_1_2_3(self):
        right_hash = {
            '_________Microsoft_Visio.vsdx': 'b8512b46326a3488f54af64d1afa7b71',
            '_________Microsoft_Word.docx': '5644e4172116a213ba2363e28d98ff86',
            '_____Microsoft_Excel______________________.xlsm': 'd42b9c57cec20218f054d3ae721c369c',
            'cats.zip': '2a543e691bf92a7175479c755cfbeb56',
            'eiler.json': '5e1e57fd1084545b2054cdf524e8409e',
            'image4.png': '7d626347e9d44524cdae0d5eb5df9efc',
            'image5.gif': 'd53a32bc83edadbdcfa82be22f8a734a',
            'lorem.txt': 'a37e150ede66c92bd75b31b4805cc8a7',
            'oleObject1.docx': 'e9f40e48cc1d0b321de19f222967856d',
            'oleObject2.docx': 'b42a7a9a32812b0a404dc8615ba56301',
            'oleObject1.pdf': 'eef47ce98c4887d212907da8752df4d0',
            'test.py': 'd41d8cd98f00b204e9800998ecf8427e'
        }
        docx_attachment_extractor = DocxAttachmentsExtractor()
        tmp_dir = os.path.join(os.path.dirname(__file__), 'data/with_attachments_docx/')
        extracted = 0
        for i in range(1, 4):
            filename = 'with_attachments_{}.docx'.format(i)
            mime = get_file_mime_type(os.path.join(tmp_dir, filename))
            self.assertTrue(docx_attachment_extractor.can_extract(mime, filename))
            attachments = docx_attachment_extractor.get_attachments(tmp_dir, filename, {})
            for i, (attachment_name, attachment_data) in enumerate(attachments):
                self.assertEqual(right_hash[attachment_name], hashlib.md5(attachment_data).hexdigest())
                extracted += 1
        self.assertEqual(extracted, 12)

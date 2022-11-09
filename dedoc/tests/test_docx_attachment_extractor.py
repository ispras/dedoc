import hashlib
import os
import tempfile
import unittest
from shutil import copyfile

from dedoc.attachments_extractors.concrete_attachments_extractors.docx_attachments_extractor import \
    DocxAttachmentsExtractor


class TestDocxAttachmentsExtractor(unittest.TestCase):

    def test_example_1_2_3(self) -> None:
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
        docx_attachment_extractor = DocxAttachmentsExtractor(need_content_analysis=True)
        src_dir = os.path.join(os.path.dirname(__file__), 'data/with_attachments_docx/')
        extracted = 0
        with tempfile.TemporaryDirectory() as tmp_dir:
            for i in range(1, 4):
                filename = 'with_attachments_{}.docx'.format(i)
                copyfile(src=os.path.join(src_dir, filename), dst=os.path.join(tmp_dir, filename))
                attachments = docx_attachment_extractor.get_attachments(tmp_dir, filename, {})
                for i, file in enumerate(attachments):
                    with open(file.get_filename_in_path(), "rb") as file_content:
                        self.assertEqual(right_hash[file.get_original_filename()],
                                         hashlib.md5(file_content.read()).hexdigest())
                    extracted += 1
        self.assertEqual(extracted, 12)

    def test_diagrams_extraction(self) -> None:
        docx_attachment_extractor = DocxAttachmentsExtractor(need_content_analysis=True)
        src_dir = os.path.join(os.path.dirname(__file__), "data", "docx")
        files = [('diagram_1.docx', 1), ('diagram_2.docx', 5)]
        with tempfile.TemporaryDirectory() as tmp_dir:
            for file, num_attachments in files:
                attachments = docx_attachment_extractor.get_attachments(tmp_dir, os.path.join(src_dir, file), {})
                self.assertEqual(num_attachments, len(attachments))

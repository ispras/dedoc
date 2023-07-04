import os
import shutil
import tempfile
import unittest
from typing import List

from dedoc.attachments_extractors.concrete_attachments_extractors.docx_attachments_extractor import DocxAttachmentsExtractor
from dedoc.attachments_extractors.concrete_attachments_extractors.pptx_attachments_extractor import PptxAttachmentsExtractor
from dedoc.readers import ArchiveReader
from tests.test_utils import get_test_config


# переименовать торрент файл ???
# объединить тесты с аттачментами в один файл ???

class TestAttachmentsExtractor(unittest.TestCase):
    """
    Class with implemented tests for the attachment extractor
    """
    src_dir = os.path.join(os.path.dirname(__file__), "..", "data", "with_attachments")

    def test_docx_attachments_extractor(self) -> None:
        """
        Tests attachment extraction from docx files
        """
        attachments_name_list = [
            '_________Microsoft_Visio.vsdx',
            '_________Microsoft_Word.docx',
            '_____Microsoft_Excel______________________.xlsm',
            'cats.zip',
            'eiler.json',
            'image4.png',
            'image5.gif',
            'lorem.txt',
            'oleObject1.docx',
            'oleObject2.docx',
            'oleObject1.pdf',
            'test.py'
        ]

        docx_attachment_extractor = DocxAttachmentsExtractor()
        extracted = 0
        for i in range(1, 4):
            filename = f'with_attachments_{i}.docx'

            with tempfile.TemporaryDirectory() as tmpdir:
                shutil.copy(os.path.join(self.src_dir, filename), os.path.join(tmpdir, filename))
                attachments = docx_attachment_extractor.get_attachments(tmpdir, filename, {})

                for _, file in enumerate(attachments):
                    self.assertIn(file.original_name, attachments_name_list)
                    extracted += 1

        self.assertEqual(extracted, len(attachments_name_list))

    def test_pptx_attachments_extractor(self) -> None:
        """
        Tests attachment extraction from pptx files
        """
        attachments_name_list = [
            "Microsoft_Excel_97-2004_Worksheet.xls",
            "image3.png",
            "image2.svg",
            "image1.png",
            "Microsoft_Excel_Worksheet.xlsx",
            "OpenVPN-2.5.8-I603-amd64.msi",
            "head.html",
            "zip.zip",
            "Джинни и Джорджия Ginny & Georgia Сезон 2 Серии 1-10 из 10 (Аня Адамс, Каталина Агиляр Мастретта) [2023, США, драма, комед [rutracker-6307383].torrent",  # noqa
            "oleObject7.pdf",
            "image10.jpg",
            "database.c"
        ]

        pptx_attachment_extractor = PptxAttachmentsExtractor()
        extracted = 0
        for i in range(1, 3):
            filename = f'with_attachments_{i}.pptx'

            with tempfile.TemporaryDirectory() as tmpdir:
                shutil.copy(os.path.join(self.src_dir, filename), os.path.join(tmpdir, filename))
                attachments = pptx_attachment_extractor.get_attachments(tmpdir, filename, {})

                for _, file in enumerate(attachments):
                    self.assertIn(file.original_name, attachments_name_list)
                    extracted += 1

        self.assertEqual(extracted, len(attachments_name_list))

    def test_docx_diagrams_extraction(self) -> None:
        """
        Tests diagram extraction from docx files
        """
        docx_attachment_extractor = DocxAttachmentsExtractor()
        docx_dir = os.path.join(os.path.dirname(__file__), "..", "data", "docx")
        files = [('diagram_1.docx', 1), ('diagram_2.docx', 5)]
        with tempfile.TemporaryDirectory() as tmp_dir:
            for file, num_attachments in files:
                attachments = docx_attachment_extractor.get_attachments(tmp_dir, os.path.join(docx_dir, file), {})
                self.assertEqual(num_attachments, len(attachments))

    def test_archive_with_slash(self) -> None:
        """
        Tests attachment extraction from archives with files containing slash symbol in the name
        """
        file_name_template = "attachments.{}"
        for extension in "7z", "tar", "tar.gz", "zip":
            file_name = file_name_template.format(extension)
            files = self.__get_list_of_files(file_name)
            self.assertEqual(2, len(files))
            self.assertIn(r"som_file⁄wiht\slash.txt", files)
            self.assertIn("other_file.csv", files)

    def __get_list_of_files(self, file_name: str) -> List[str]:
        """
        Class method for getting list of files in an archive
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, file_name)
            shutil.copyfile(os.path.join(self.src_dir, file_name), file_path)
            config = get_test_config()
            document = ArchiveReader(config=config).read(path=file_path, parameters={"with_attachment": True})
            files = [file.original_name for file in document.attachments]
            return files

import os
import shutil
import tempfile

import requests

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiMimeDetection(AbstractTestApiDocReader):
    # sgi j2k pic hdr
    files = [
        "archives/arch_with_attachs.7z", "archives/arch_with_attachs.rar", "archives/arch_with_attachs.tar", "archives/arch_with_attachs.tar.gz",
        "archives/arch_with_attachs.zip", "csvs/csv_coma.csv", "csvs/csv_tab.tsv", "docx/english_doc.doc", "docx/english_doc.docx",
        "docx/english_doc.odt", "docx/english_doc.rtf", "pdf_with_text_layer/english_doc.pdf", "scanned/example.bmp", "scanned/example.dib",
        "scanned/example.eps", "scanned/example.gif", "scanned/example.jfif", "scanned/example.jpe", "scanned/example.jpeg", "scanned/example.jpg",
        "scanned/example.pbm", "scanned/example.pcx", "scanned/example.pdf", "scanned/example.pgm", "scanned/example.png", "scanned/example.pnm",
        "scanned/example.ppm", "scanned/example.ras", "scanned/example.sr", "scanned/example.tiff", "scanned/example.webp", "htmls/example.html",
        "xlsx/example.ods", "xlsx/example.xls", "xlsx/example.xlsx", "pptx/example.odp", "pptx/example.ppt", "pptx/example.pptx", "json/dict.json",
        "scanned/example_with_table9.djvu", "txt/football.txt", "eml/message.eml", "xml/simple.xml", "mhtml/with_attachments.mhtml"
    ]

    def __test_correct_response(self, file_path: str, actual_name: str) -> None:
        host = self._get_host()
        port = self._get_port()

        with open(file_path, "rb") as file:
            files = {"file": (os.path.basename(file_path), file)}
            r = requests.post(f"http://{host}:{port}/upload", files=files, data={})
            self.assertEqual(200, r.status_code, f"Error on file {actual_name}")

    def test_api_files_without_extension(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            for file in self.files:
                tmp_file_path = os.path.join(temp_dir, "file")
                shutil.copyfile(os.path.join(self.data_directory_path, file), tmp_file_path)
                self.__test_correct_response(tmp_file_path, file)

    def test_api_files_with_wrong_extension(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            for file in self.files:
                extension = "docx" if file.endswith("png") else "png"
                tmp_file_path = os.path.join(temp_dir, f"file.{extension}")
                shutil.copyfile(os.path.join(self.data_directory_path, file), tmp_file_path)
                self.__test_correct_response(tmp_file_path, file)

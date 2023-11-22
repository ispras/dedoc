import os

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiArchiveReader(AbstractTestApiDocReader):
    parameters = dict(with_attachments="True", need_content_analysis="True")

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "archives", file_name)

    def _check_archive_with_english_doc(self, file_name: str) -> None:
        result = self._send_request(file_name, self.parameters)
        self.assertEqual(len(result["attachments"]), 4)
        english_doc = [doc for doc in result["attachments"] if doc["metadata"]["file_name"].startswith("english_doc")][0]
        self._check_english_doc(english_doc)

    def test_zip(self) -> None:
        file_name = "arch_with_attachs.zip"
        result = self._send_request(file_name, self.parameters)
        self.assertEqual(len(result["attachments"]), 4)

    def test_tar(self) -> None:
        file_name = "arch_with_attachs.tar"
        result = self._send_request(file_name, self.parameters)

        self.assertEqual(len(result["attachments"]), 4)

    def test_targz(self) -> None:
        file_name = "arch_with_attachs.tar.gz"
        result = self._send_request(file_name, self.parameters)

        self.assertEqual(len(result["attachments"]), 4)

    def test_rar(self) -> None:
        file_name = "arch_with_attachs.rar"
        result = self._send_request(file_name, self.parameters)

        self.assertEqual(len(result["attachments"]), 4)

    def test_7zip(self) -> None:
        file_name = "arch_with_attachs.7z"
        result = self._send_request(file_name, self.parameters)

        self.assertEqual(len(result["attachments"]), 4)

    def test_zip_as_archive(self) -> None:
        file_name = "zipka_eng.zip"
        self._check_archive_with_english_doc(file_name)

    def test_archive_subfolder_tar(self) -> None:
        file_name = "subfolders.tar.gz"
        self._check_archive_with_english_doc(file_name)

    def test_archive_subfolder_zip(self) -> None:
        file_name = "subfolders.zip"
        self._check_archive_with_english_doc(file_name)

    def test_archive_subfolder_rar(self) -> None:
        file_name = "subfolders.rar"
        self._check_archive_with_english_doc(file_name)

    def test_archive_subfolder_7z(self) -> None:
        file_name = "subfolders.7z"
        self._check_archive_with_english_doc(file_name)

    def test_zip_with_unsupported_file(self) -> None:
        file_name = "arch_with_unsupport_atchs.zip"
        result = self._send_request(file_name, self.parameters)
        attachs = result["attachments"]

        self.assertEqual(len(attachs), 6)
        unsupported = [att for att in attachs if att["metadata"]["file_name"] == "file.bin"][0]["metadata"]
        self.assertEqual(unsupported["file_type"], "application/octet-stream")

    def test_broken_archive(self) -> None:
        file_name = "broken.zip"
        result = self._send_request(file_name, self.parameters)
        self.assertEqual(len(result["attachments"]), 7)
        english_doc = [doc for doc in result["attachments"] if doc["metadata"]["file_name"].startswith("english_doc")][0]
        self._check_english_doc(english_doc)

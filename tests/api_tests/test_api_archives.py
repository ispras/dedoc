import os

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiArchiveReader(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "archives", file_name)

    def __check_response(self, result: dict) -> None:
        self.assertEqual(result['attachments'], [])
        content = result['content']
        tree = content["structure"]
        self._check_tree_sanity(tree)
        node = self._get_by_tree_path(tree, "0.0")
        text = node["text"].strip().split("\n")
        self.assertEqual("Первая строка Первого файла", text[0])
        self.assertEqual("Вторая строка Первого файла", text[1])

        node = self._get_by_tree_path(tree, "0.1")
        text = node["text"].strip().split("\n")
        self.assertEqual("'Третья Строка третьего файла", text[0])
        self.assertEqual("Первая строка второго файла", text[1])

        node = self._get_by_tree_path(tree, "0.2")
        text = node["text"].strip().split("\n")
        self.assertEqual("Вторая строка второго файла", text[0])

        tables = content["tables"]
        self.assertEqual(1, len(tables))
        table = tables[0]
        self.assertEqual(1, table["metadata"]["page_id"])
        self.assertListEqual(['Номер', 'Имя', 'Фамилия'], table["cells"][0])
        self.assertListEqual(['1', 'Вася', 'Пупкин'], table["cells"][1])

    def test_zip_with_scanned_wo_orderfile(self) -> None:
        file_name = "zipka_wo_order.zip"
        result = self._send_request(file_name, dict(with_attachments="True"))
        self.__check_response(result)

    def test_zip_with_scanned_with_hidden_file(self) -> None:
        file_name = "zipka_2_with_hidden.zip"
        result = self._send_request(file_name, dict(with_attachments="True"))
        self.__check_response(result)

    def test_zip_with_scanned(self) -> None:
        file_name = "zipka.zip"
        result = self._send_request(file_name, dict(with_attachments="True"))
        self.__check_response(result)
        self._check_metainfo(result['metadata'], 'application/zip', file_name)

    def _check_archive_with_english_doc(self, file_name: str) -> None:
        result = self._send_request(file_name, dict(with_attachments="True", archive_as_single_file="False"))
        self.assertEqual(len(result['attachments']), 4)
        english_doc = [doc for doc in result['attachments']
                       if doc["metadata"]["file_name"].startswith("english_doc")][0]
        self.check_english_doc(english_doc)

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

    def test_zip_with_scanned_wo_name(self) -> None:
        file_name = "zipka2.zip"
        result = self._send_request(file_name, dict(with_attachments="True"))
        self.__check_response(result)

    def test_rar_with_scanned(self) -> None:
        file_name = "zipka.rar"
        result = self._send_request(file_name, dict(with_attachments="True"))
        self.__check_response(result)

    def test_tar_with_scanned(self) -> None:
        file_name = "zipka.tar"
        result = self._send_request(file_name, dict(with_attachments="True"))
        self.__check_response(result)

    def test_zip_wo_scanned(self) -> None:
        file_name = "arch_with_attachs.zip"
        result = self._send_request(file_name, dict(with_attachments="True"))
        self.assertEqual(len(result['attachments']), 4)

    def test_tar_wo_scanned(self) -> None:
        file_name = "arch_with_attachs.tar"
        result = self._send_request(file_name, dict(with_attachments="True"))

        self.assertEqual(len(result['attachments']), 4)

    def test_targz_wo_scanned(self) -> None:
        file_name = "arch_with_attachs.tar.gz"
        result = self._send_request(file_name, dict(with_attachments="True"))

        self.assertEqual(len(result['attachments']), 4)

    def test_rar_wo_scanned(self) -> None:
        file_name = "arch_with_attachs.rar"
        result = self._send_request(file_name, dict(with_attachments="True"))

        self.assertEqual(len(result['attachments']), 4)

    def test_7zip_wo_scanned(self) -> None:
        file_name = "arch_with_attachs.7z"
        result = self._send_request(file_name, dict(with_attachments="True"))

        self.assertEqual(len(result['attachments']), 4)

    def test_7zip_with_scanned(self) -> None:
        file_name = "zipka.7z"
        result = self._send_request(file_name, dict(with_attachments="True"))
        self.__check_response(result)

    def test_zip_with_unsupported_file(self) -> None:
        file_name = "arch_with_unsupport_atchs.zip"
        result = self._send_request(file_name, dict(with_attachments="True"))
        attachs = result['attachments']

        self.assertEqual(len(attachs), 6)
        unsupported = [att for att in attachs if att["metadata"]["file_name"] == "file.bin"][0]["metadata"]
        self.assertEqual(unsupported['file_type'], "application/octet-stream")

    def test_analyze_archive_by_mime(self) -> None:
        file_name = "tz-led-png.zip"
        result = self._send_request(file_name, dict(with_attachments="True"))
        par = result["content"]["structure"]
        self.assertEqual('1. ОБЩИЕ СВЕДЕНИЯ\n', self._get_by_tree_path(par, "0.7.0")["text"])
        self.assertEqual('2. ОСНОВНЫЕ ТРЕБОВАНИЯ\n', self._get_by_tree_path(par, "0.7.1")["text"])
        self.assertEqual('3. ОБОРУДОВАНИЕ\n', self._get_by_tree_path(par, "0.7.2")["text"])

    def test_broken_archive(self) -> None:
        file_name = "broken.zip"
        result = self._send_request(file_name, dict(with_attachments="True"))
        self.assertEqual(len(result['attachments']), 7)
        english_doc = [doc for doc in result['attachments']
                       if doc["metadata"]["file_name"].startswith("english_doc")][0]
        self.check_english_doc(english_doc)

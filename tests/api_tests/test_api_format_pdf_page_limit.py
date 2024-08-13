import os

from tests.api_tests.abstract_api_test import AbstractTestApiDocReader


class TestApiPdfPageLimit(AbstractTestApiDocReader):

    def _get_abs_path(self, file_name: str) -> str:
        return os.path.join(self.data_directory_path, "pdf_with_text_layer", file_name)

    lines = [
        "Первая страница",
        "Вторая страница",
        "Третья страница",
        "Четвёртая страница",
        "Пятая страница",
        "Шестая страница",
        "Седьмая страница",
        "Восьмая страница",
        "Девятая страница"
    ]

    def test_no_text_layer(self) -> None:
        self.__check_limit("false", check_partially=True)
        self.__check_out_of_limit("false")

    def test_text_layer(self) -> None:
        self.__check_limit("true", check_partially=True)
        self.__check_out_of_limit("true")

    def test_auto_text_layer(self) -> None:
        self.__check_limit("auto", check_partially=True)
        self.__check_out_of_limit("auto")

    def test_tabby_layer(self) -> None:
        self.__check_limit("tabby", check_partially=True)
        self.__check_out_of_limit("tabby")

    def test_auto_tabby(self) -> None:
        self.__check_limit("auto_tabby", check_partially=True)
        self.__check_out_of_limit("auto_tabby")

    def __check_out_of_limit(self, reader: str) -> None:
        text_expected = ""
        for pages in (":-1", "-1:0", "0:0", "10:11", "11:"):
            self.__check(pages, text_expected, reader=reader)

    def __check_limit(self, reader: str, check_partially: bool = False) -> None:
        text_expected = ""
        self.__check("2:1", text_expected, reader=reader, check_partially=check_partially)

        text_expected = "\n".join(self.lines[:])
        for pages in "", ":", "0:9", "0:20", ":9", "0:":
            self.__check(pages, text_expected, reader=reader)

        text_expected = "\n".join(self.lines[0:2])
        self.__check("1:2", text_expected, reader=reader, check_partially=check_partially)

        text_expected = self.lines[0]
        self.__check("1:1", text_expected, reader=reader, check_partially=check_partially)

        text_expected = self.lines[1]
        self.__check("2:2", text_expected, reader=reader, check_partially=check_partially)

        text_expected = "\n".join(self.lines[1:3])
        self.__check("2:3", text_expected, reader=reader, check_partially=check_partially)

        text_expected = "\n".join(self.lines[4:8])
        self.__check("5:8", text_expected, reader=reader, check_partially=check_partially)

        text_expected = self.lines[8]
        self.__check("9:", text_expected, reader=reader, check_partially=False)

        text_expected = "\n".join(self.lines[0:9])
        self.__check("1:9", text_expected, reader=reader, check_partially=False)

    def __check(self, pages: str, text_expected: str, reader: str, check_partially: bool = False) -> None:

        params = dict(pdf_with_text_layer=reader, pages=pages, is_one_column_document="true")
        result = self._send_request("multipage.pdf", params)
        if check_partially:
            self.assertIn("The document is partially parsed", result["warnings"])
            self.assertIn("first_page", result["metadata"])
            self.assertIn("last_page", result["metadata"])
        tree = result["content"]["structure"]
        text = "".join([node["text"] for node in tree["subparagraphs"]])
        self.assertEqual(text_expected.strip(), text.strip(), f"{pages} and {reader}")

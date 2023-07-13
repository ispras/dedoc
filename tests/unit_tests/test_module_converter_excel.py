import os

from dedoc.common.exceptions.conversion_exception import ConversionException
from dedoc.converters.concrete_converters.excel_converter import ExcelConverter
from tests.unit_tests.abstract_converter_test import AbstractConverterTest


class TestExcelConverter(AbstractConverterTest):
    converter = ExcelConverter(config={"need_content_analysis": True})

    path = os.path.join(AbstractConverterTest.path, "xlsx")

    def test_convert_broken_file(self) -> None:
        extension = ".ods"
        filename = "broken"
        with self.assertRaises(ConversionException):
            self._convert(filename=filename, extension=extension, converter=self.converter)

    def test_convert_ods(self) -> None:
        extension = ".ods"
        filename = "example"
        self._convert(filename=filename, extension=extension, converter=self.converter)

    def test_convert_xls(self) -> None:
        extension = ".xls"
        filename = "example"
        self._convert(filename=filename, extension=extension, converter=self.converter)

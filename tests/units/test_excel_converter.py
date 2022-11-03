import os

from dedoc import ConversionException
from dedoc import ExcelConverter
from tests.units.abstract_converter_test import AbstractConverterTest


class TestExcelConverter(AbstractConverterTest):
    converter = ExcelConverter(config={"need_content_analysis": True})

    path = os.path.join(AbstractConverterTest.path, "xlsx")

    def test_convert_broken(self) -> None:
        extension = ".ods"
        filename = "broken"
        with self.assertRaises(ConversionException):
            self._convert(filename=filename, extension=extension, converter=self.converter)

    def test_convert_ods(self) -> None:
        extension = ".ods"
        filename = "example"
        self._convert(filename=filename, extension=extension, converter=self.converter)

    def test_convert_doc(self) -> None:
        extension = ".xls"
        filename = "example"
        self._convert(filename=filename, extension=extension, converter=self.converter)

import os

from dedoc.common.exceptions.conversion_exception import ConversionException
from dedoc.converters.concrete_converters.pptx_converter import PptxConverter
from tests.unit_tests.abstract_converter_test import AbstractConverterTest


class TestPPTXConverter(AbstractConverterTest):

    path = os.path.join(AbstractConverterTest.path, "pptx")
    converter = PptxConverter(config={"need_content_analysis": True})

    def test_convert_broken_file(self) -> None:
        extension = ".odp"
        filename = "broken"
        with self.assertRaises(ConversionException):
            self._convert(filename=filename, extension=extension, converter=self.converter)

    def test_convert_odp(self) -> None:
        filename = "example"
        extension = ".odp"
        self._convert(filename=filename, extension=extension, converter=self.converter)

    def test_convert_ppt(self) -> None:
        filename = "example"
        extension = ".ppt"
        self._convert(filename=filename, extension=extension, converter=self.converter)

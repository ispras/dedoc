import os

from dedoc.common.exceptions.conversion_error import ConversionError
from dedoc.converters.concrete_converters.docx_converter import DocxConverter
from tests.unit_tests.abstract_converter_test import AbstractConverterTest


class TestDocxConverter(AbstractConverterTest):

    converter = DocxConverter(config={"need_content_analysis": True})
    path = os.path.join(AbstractConverterTest.path, "docx")

    def test_convert_broken_file(self) -> None:
        extension = ".odt"
        filename = "broken"
        with self.assertRaises(ConversionError):
            self._convert(filename=filename, extension=extension, converter=self.converter)

    def test_convert_odt(self) -> None:
        filename = "english_doc"
        extension = ".odt"
        self._convert(filename=filename, extension=extension, converter=self.converter)

    def test_convert_doc(self) -> None:
        filename = "english_doc"
        extension = ".doc"
        self._convert(filename=filename, extension=extension, converter=self.converter)

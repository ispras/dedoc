import os

from dedoc.common.exceptions.conversion_exception import ConversionException
from dedoc.converters.concrete_converters.docx_converter import DocxConverter
from tests.unit_tests.abstract_converter_test import AbstractConverterTest


class TestDocxConverter(AbstractConverterTest):
    """
    Class with implemented tests for DocxConvertor
    """

    converter = DocxConverter(config={"need_content_analysis": True})
    path = os.path.join(AbstractConverterTest.path, "docx")

    def test_convert_broken(self) -> None:
        """
        Tests the conversion of a broken file
        """
        extension = ".odt"
        filename = "broken"
        with self.assertRaises(ConversionException):
            self._convert(filename=filename, extension=extension, converter=self.converter)

    def test_convert_odt(self) -> None:
        """
        Tests the conversion of .odt file to .docx
        """
        filename = "english_doc"
        extension = ".odt"
        self._convert(filename=filename, extension=extension, converter=self.converter)

    def test_convert_doc(self) -> None:
        """
        Tests the conversion of .doc file to .docx
        """
        filename = "english_doc"
        extension = ".doc"
        self._convert(filename=filename, extension=extension, converter=self.converter)

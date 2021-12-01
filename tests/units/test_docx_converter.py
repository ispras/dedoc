import os

from dedoc.common.exceptions.conversion_exception import ConversionException
from dedoc.converters.concrete_converters.docx_converter import DocxConverter
from tests.units.abstract_converter_test import AbstractConverterTest


class TestDocxConverter(AbstractConverterTest):

    converter = DocxConverter(config={"need_content_analysis": True})
    path = os.path.join(AbstractConverterTest.path, "docx")

    def test_convert_broken(self):
        extension = ".odt"
        filename = "broken"
        with self.assertRaises(ConversionException):
            self._convert(filename=filename, extension=extension, converter=self.converter)

    def test_convert_odt(self):
        filename = "english_doc"
        extension = ".odt"
        self._convert(filename=filename, extension=extension, converter=self.converter)

    def test_convert_doc(self):
        filename = "english_doc"
        extension = ".doc"
        self._convert(filename=filename, extension=extension, converter=self.converter)

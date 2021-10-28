import os

from dedoc.common.exceptions.conversion_exception import ConversionException
from dedoc.converters.concrete_converters.pptx_converter import PptxConverter
from tests.units.abstract_converter_test import AbstractConverterTest


class TestDocxConverter(AbstractConverterTest):

    path = os.path.join(AbstractConverterTest.path, "pptx")
    converter = PptxConverter(config={})

    def test_convert_broken(self):
        extension = ".odp"
        filename = "broken"
        with self.assertRaises(ConversionException):
            self._convert(filename=filename, extension=extension, converter=self.converter)

    def test_convert_odp(self):
        filename = "example"
        extension = ".odp"
        self._convert(filename=filename, extension=extension, converter=self.converter)

    def test_convert_ppt(self):
        filename = "example"
        extension = ".ppt"
        self._convert(filename=filename, extension=extension, converter=self.converter)

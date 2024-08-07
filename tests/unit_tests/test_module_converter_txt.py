import os

from dedoc.converters.concrete_converters.txt_converter import TxtConverter
from tests.unit_tests.abstract_converter_test import AbstractConverterTest


class TestTxtConverter(AbstractConverterTest):
    converter = TxtConverter(config={})

    path = os.path.join(AbstractConverterTest.path, "xml")

    def test_convert_xml(self) -> None:
        extension = ".xml"
        self._convert(filename="simple", extension=extension, converter=self.converter)
        self._convert(filename="with_attributes", extension=extension, converter=self.converter)

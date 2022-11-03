import os

from dedoc import TxtConverter
from tests.units.abstract_converter_test import AbstractConverterTest


class TestTxtConverter(AbstractConverterTest):
    converter = TxtConverter(config={})

    path = os.path.join(AbstractConverterTest.path, "xml")

    def test_convert_xml(self) -> None:
        extension = ".xml"
        self._convert(filename="simple", extension=extension, converter=self.converter)
        self._convert(filename="with_attributes", extension=extension, converter=self.converter)

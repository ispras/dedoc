import os
import shutil
from tempfile import TemporaryDirectory
from unittest import TestCase

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter


class AbstractConverterTest(TestCase):
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

    def setUp(self) -> None:
        """
        Method that runs before AbstractConverterTest testing
        """
        super().setUp()
        self.tmp_dir = TemporaryDirectory()

    def tearDown(self) -> None:
        """
        Method that runs after AbstractConverterTest testing
        """
        super().tearDown()
        self.tmp_dir.cleanup()

    def _convert(self, filename: str, extension: str, converter: AbstractConverter) -> None:
        filename_with_extension = filename + extension
        file = os.path.join(self.path, filename_with_extension)
        tmp_file = os.path.join(self.tmp_dir.name, filename_with_extension)
        self.assertTrue(os.path.isfile(file), f"no such file {file}")
        shutil.copy(file, tmp_file)
        result = converter.convert(file_path=tmp_file)
        self.assertTrue(os.path.isfile(result), f"no such file {result}")

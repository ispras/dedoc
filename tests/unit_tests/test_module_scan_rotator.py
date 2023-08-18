import os
import unittest

import cv2

from dedoc.readers.pdf_reader.pdf_image_reader.scan_rotator import ScanRotator
from tests.test_utils import get_test_config


class TestScanRotator(unittest.TestCase):
    rotator = ScanRotator(config=get_test_config())

    def _get_abs_path(self, file_name: str) -> str:
        data_directory_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        return os.path.join(data_directory_path, "scan_rotator", file_name)

    def test_documents_with_short_lines(self) -> None:
        for i in range(1, 6):
            file_name = f"short_lines-{i}.png"
            img = cv2.imread(self._get_abs_path(file_name))
            image, angle = self.rotator.auto_rotate(img)
            self.assertEqual(0, angle)

import os
import unittest

import cv2
from dedocutils.preprocessing import SkewCorrector


class TestScanRotator(unittest.TestCase):
    skew_corrector = SkewCorrector()

    def _get_abs_path(self, file_name: str) -> str:
        data_directory_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        return os.path.join(data_directory_path, "skew_corrector", file_name)

    def test_documents_with_short_lines(self) -> None:
        for i in range(1, 6):
            file_name = f"short_lines-{i}.png"
            img = cv2.imread(self._get_abs_path(file_name))
            image, angle = self.skew_corrector.preprocess(img)
            angle = angle["orientation_angle"]
            self.assertEqual(0, angle)

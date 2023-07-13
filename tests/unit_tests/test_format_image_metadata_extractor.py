import os
import unittest

from dedoc.metadata_extractors.concrete_metadata_extractors.image_metadata_extractor import ImageMetadataExtractor
from tests.test_utils import get_test_config


class TestImageMetadataExtractor(unittest.TestCase):
    extractor = ImageMetadataExtractor(config=get_test_config())
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    assert os.path.isdir(data_path)

    def test_broken_image_metadata_extraction(self) -> None:
        file = os.path.join(self.data_path, "exif_nan.jpg")
        exif = self.extractor._get_exif(file)
        self.assertIsNone(exif.get("digital_zoom_ratio"))

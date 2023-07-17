import unittest

from dedoc.data_structures.concrete_annotations.spacing_annotation import SpacingAnnotation
from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.pdf_reader.pdf_image_reader.line_metadata_extractor.metadata_extractor import LineMetadataExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.paragraph_extractor.scan_paragraph_classifier_extractor import ScanParagraphClassifierExtractor
from dedoc.readers.pdf_reader.utils.line_object_linker import LineObjectLinker
from tests.test_utils import get_test_config, create_line_by_coordinates


class TestLineObjectLinker(unittest.TestCase):
    config = get_test_config()
    linker = LineObjectLinker(config=config)
    metadata_extractor = LineMetadataExtractor(default_spacing=12, config=config)
    paragraph_extractor = ScanParagraphClassifierExtractor(config=config)

    def _get_spacing(self, line: LineWithLocation) -> int:
        annotations = [annotation for annotation in line.annotations if annotation.name == SpacingAnnotation.name]
        self.assertEqual(1, len(annotations))
        annotation = annotations[0]
        return int(annotation.value)

    def test_line_spacing(self) -> None:
        line1 = create_line_by_coordinates(x_top_left=4, y_top_left=1, height=2, width=9, page=0)
        line2 = create_line_by_coordinates(x_top_left=4, y_top_left=4, height=2, width=9, page=0)
        line3 = create_line_by_coordinates(x_top_left=15, y_top_left=2, height=2, width=7, page=0)
        line4 = create_line_by_coordinates(x_top_left=15, y_top_left=7, height=2, width=7, page=0)
        line5 = create_line_by_coordinates(x_top_left=2, y_top_left=1, height=2, width=9, page=1)
        lines = [line1, line2, line3, line4, line5]
        self.metadata_extractor._LineMetadataExtractor__add_spacing_annotations(lines)  # noqa
        self.assertEqual(self.metadata_extractor.default_spacing, self._get_spacing(line1))
        self.assertEqual(50, self._get_spacing(line2))
        self.assertEqual(self.metadata_extractor.default_spacing, self._get_spacing(line3))
        self.assertEqual(150, self._get_spacing(line4))
        self.assertEqual(self.metadata_extractor.default_spacing, self._get_spacing(line5))

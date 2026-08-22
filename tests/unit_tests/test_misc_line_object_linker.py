import unittest

from dedocutils.data_structures import BBox

from dedoc.data_structures.concrete_annotations.spacing_annotation import SpacingAnnotation
from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.pdf_reader.data_classes.tables.location import Location
from dedoc.readers.pdf_reader.data_classes.tables.scantable import ScanTable
from dedoc.readers.pdf_reader.pdf_image_reader.line_metadata_extractor.metadata_extractor import LineMetadataExtractor
from dedoc.readers.pdf_reader.pdf_image_reader.paragraph_extractor.scan_paragraph_classifier_extractor import ScanParagraphClassifierExtractor
from dedoc.readers.pdf_reader.utils.line_object_linker import LineObjectLinker
from tests.test_utils import create_line_by_coordinates, get_test_config


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

    def _make_line(self, text: str, x: int, y: int, width: int = 80, height: int = 10, page: int = 0) -> LineWithLocation:
        bbox = BBox(x_top_left=x, y_top_left=y, width=width, height=height)
        location = Location(bbox=bbox, page_number=page)
        return LineWithLocation(line=text, metadata=LineMetadata(page_id=page, line_id=0), annotations=[], location=location)

    def _make_table(self, x: int, y: int, width: int = 80, height: int = 40, page: int = 0) -> ScanTable:
        return ScanTable(page_number=page, cells=[], bbox=BBox(x_top_left=x, y_top_left=y, width=width, height=height))

    def test_line_spacing(self) -> None:
        line1 = create_line_by_coordinates(x_top_left=4, y_top_left=1, height=2, width=9, page=0)
        line2 = create_line_by_coordinates(x_top_left=4, y_top_left=4, height=2, width=9, page=0)
        line3 = create_line_by_coordinates(x_top_left=15, y_top_left=2, height=2, width=7, page=0)
        line4 = create_line_by_coordinates(x_top_left=15, y_top_left=7, height=2, width=7, page=0)
        line5 = create_line_by_coordinates(x_top_left=2, y_top_left=1, height=2, width=9, page=1)
        lines = [line1, line2, line3, line4, line5]
        self.metadata_extractor._LineMetadataExtractor__add_spacing_annotations(lines)
        self.assertEqual(self.metadata_extractor.default_spacing, self._get_spacing(line1))
        self.assertEqual(50, self._get_spacing(line2))
        self.assertEqual(self.metadata_extractor.default_spacing, self._get_spacing(line3))
        self.assertEqual(150, self._get_spacing(line4))
        self.assertEqual(self.metadata_extractor.default_spacing, self._get_spacing(line5))

    def test_table_annotation_at_end_when_caption_above(self) -> None:
        """A table linked to the caption above it is anchored at the end of that line."""
        caption = self._make_line("Таблица 1", x=10, y=10)
        table = self._make_table(x=10, y=40)
        lines = self.linker.link_objects(lines=[caption], tables=[table], images=[])

        annotations = [ann for ann in lines[0].annotations if ann.name == TableAnnotation.name]
        self.assertEqual(1, len(annotations))
        self.assertEqual(9, annotations[0].start)
        self.assertEqual(9, annotations[0].end)
        self.assertEqual(table.uid, annotations[0].value)

    def test_table_annotation_at_start_when_line_below(self) -> None:
        """A table linked to the line below it is anchored at the start of that line."""
        line = self._make_line("продолжение", x=10, y=60)
        table = self._make_table(x=10, y=10, height=30)
        lines = self.linker.link_objects(lines=[line], tables=[table], images=[])

        annotations = [ann for ann in lines[0].annotations if ann.name == TableAnnotation.name]
        self.assertEqual(1, len(annotations))
        self.assertEqual(0, annotations[0].start)
        self.assertEqual(11, annotations[0].end)
        self.assertEqual(table.uid, annotations[0].value)

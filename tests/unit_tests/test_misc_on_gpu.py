import os

import cv2
from dedocutils.data_structures import BBox

from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.readers.pdf_reader.data_classes.line_with_location import LineWithLocation
from dedoc.readers.pdf_reader.data_classes.tables.location import Location
from dedoc.readers.pdf_reader.pdf_auto_reader.txtlayer_classifier import TxtlayerClassifier
from dedoc.readers.pdf_reader.pdf_image_reader.columns_orientation_classifier.columns_orientation_classifier import ColumnsOrientationClassifier
from dedoc.readers.pdf_reader.pdf_image_reader.paragraph_extractor.scan_paragraph_classifier_extractor import ScanParagraphClassifierExtractor
from dedoc.structure_extractors.concrete_structure_extractors.law_structure_excractor import LawStructureExtractor
from tests.api_tests.abstract_api_test import AbstractTestApiDocReader
from tests.test_utils import get_test_config


class TestOnGpu(AbstractTestApiDocReader):
    config = dict(on_gpu=True, n_jobs=1)

    def test_line_type_classifier(self) -> None:
        """
        Loads AbstractPickledLineTypeClassifier
        """
        law_extractor = LawStructureExtractor(config=self.config)
        lines = [
            LineWithMeta("     З А К О Н", metadata=LineMetadata(page_id=0, line_id=0)),
            LineWithMeta("\n", metadata=LineMetadata(page_id=0, line_id=1)),
            LineWithMeta("     ГОРОДА МОСКВЫ", metadata=LineMetadata(page_id=0, line_id=2))
        ]
        predictions = law_extractor.classifier.predict(lines)
        self.assertListEqual(predictions, ["header", "header", "cellar"])

    def test_orientation_classifier(self) -> None:
        checkpoint_path = get_test_config()["resources_path"]
        orientation_classifier = ColumnsOrientationClassifier(on_gpu=self.config.get("on_gpu", False), checkpoint_path=checkpoint_path, config=self.config)
        imgs_path = [f"../data/skew_corrector/rotated_{i}.jpg" for i in range(1, 5)]

        for i in range(len(imgs_path)):
            path = os.path.join(os.path.dirname(__file__), imgs_path[i])
            image = cv2.imread(path)
            _, orientation = orientation_classifier.predict(image)
            self.assertEqual(orientation, 0)

    def test_txtlayer_classifier(self) -> None:
        classify_lines = TxtlayerClassifier(config=self.config)
        lines = [LineWithMeta("Line1"), LineWithMeta("Line 2 is a bit longer")]
        self.assertEqual(classify_lines.predict(lines), True)

    def test_scan_paragraph_classifier_extractor(self) -> None:
        classify_lines_with_location = ScanParagraphClassifierExtractor(config=self.config)
        metadata = LineMetadata(page_id=1, line_id=1)
        metadata2 = LineMetadata(page_id=1, line_id=2)
        bbox = BBox(x_top_left=0, y_top_left=0, width=100, height=20)
        bbox2 = BBox(x_top_left=50, y_top_left=50, width=100, height=20)
        location = Location(page_number=1, bbox=bbox)
        location2 = Location(page_number=1, bbox=bbox2)
        lines = [
            LineWithLocation(line="Example line", metadata=metadata, annotations=[], location=location),
            LineWithLocation(line="Example line 2", metadata=metadata2, annotations=[], location=location2)
        ]
        data = classify_lines_with_location.feature_extractor.transform([lines])

        if any((data[col].isna().all() for col in data.columns)):
            labels = ["not_paragraph"] * len(lines)
        else:
            labels = classify_lines_with_location.classifier.predict(data)

        self.assertEqual(labels[0], "paragraph")
        self.assertEqual(labels[1], "paragraph")

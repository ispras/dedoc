from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.readers.pdf_reader.data_classes.page_with_bboxes import PageWithBBox
from dedoc.readers.pdf_reader.pdf_image_reader.line_metadata_extractor.bold_classifier.bold_classifier import BoldClassifier


class FontTypeClassifier:
    def __init__(self) -> None:
        super().__init__()
        self.bold_classifier = BoldClassifier()

    def predict_annotations(self, page: PageWithBBox) -> PageWithBBox:
        if len(page.bboxes) == 0:
            return page

        bboxes = [bbox.bbox for bbox in page.bboxes]
        bold_probabilities = self.bold_classifier.classify(page.image, bboxes)

        for bbox, bold_probability in zip(page.bboxes, bold_probabilities):
            if bold_probability > 0.5:
                bbox.annotations.append(BoldAnnotation(start=0, end=len(bbox.text), value="True"))

        return page

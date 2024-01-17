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

        bboxes = [word.bbox for line in page.bboxes for word in line.words]
        bold_probabilities = self.bold_classifier.classify(page.image, bboxes)

        bbox_id = 0
        for line in page.bboxes:
            current_text = ""

            for word in line.words:
                current_text = current_text + " " if current_text else current_text
                extended_text = current_text + word.text
                if bold_probabilities[bbox_id] > 0.5:
                    line.annotations.append(BoldAnnotation(start=len(current_text), end=len(extended_text), value="True"))
                current_text = extended_text
                bbox_id += 1

        return page

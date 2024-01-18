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
            current_text_len = 0

            for word in line.words:
                current_text_len = current_text_len + 1 if current_text_len > 0 else current_text_len  # add len of " " (space between words)
                extended_text_len = current_text_len + len(word.text)
                if bold_probabilities[bbox_id] > 0.5:
                    line.annotations.append(BoldAnnotation(start=current_text_len, end=extended_text_len, value="True"))
                current_text_len = extended_text_len
                bbox_id += 1

        return page

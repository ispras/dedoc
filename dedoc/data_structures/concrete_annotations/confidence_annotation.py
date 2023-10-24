from dedoc.data_structures.annotation import Annotation


class ConfidenceAnnotation(Annotation):
    """
    Confidence level of some recognized with OCR text inside the line.
    """
    name = "confidence"

    def __init__(self, start: int, end: int, value: str) -> None:
        """
        :param start: start of the text
        :param end: end of the text (not included)
        :param value: confidence level in "percents" (float number from 0 to 1)
        """
        try:
            assert 0.0 <= float(value) <= 1.0
        except ValueError:
            raise ValueError("the value of confidence annotation should be float value")
        except AssertionError:
            raise ValueError("the value of confidence annotation should be in range [0, 1]")
        super().__init__(start=start, end=end, name=ConfidenceAnnotation.name, value=value, is_mergeable=False)

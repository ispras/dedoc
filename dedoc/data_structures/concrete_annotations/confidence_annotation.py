from flask_restx import fields, Api, Model

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
        :param value: confidence level in "percents" (float or integer number from 0 to 100)
        """
        try:
            assert 0.0 <= float(value) <= 100.0
        except ValueError:
            raise ValueError("the value of confidence annotation should be float value")
        except AssertionError:
            raise ValueError("the value of confidence annotation should be in range [0, 100]")
        super().__init__(start=start, end=end, name=ConfidenceAnnotation.name, value=value, is_mergeable=False)

    @staticmethod
    def get_api_dict(api: Api) -> Model:
        return api.model('BoldAnnotation', {
            'start': fields.Integer(description='annotation start index', required=True, example=0),
            'end': fields.Integer(description='annotation end index', required=True, example=4),
            'value': fields.String(description='confidence value', required=True, example="95")
        })

from dedoc.common.exceptions.dedoc_exception import DedocException


class RecognizeException(DedocException):

    def __init__(self, msg: str, msg_api=None):
        super(RecognizeException, self).__init__(msg_api=msg_api, msg=msg)

    def __str__(self) -> str:
        return "RecognizeException({})".format(self.msg)

    @property
    def code(self) -> int:
        return 500

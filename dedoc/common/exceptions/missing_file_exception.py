from dedoc.common.exceptions.dedoc_exception import DedocException


class MissingFileException(DedocException):
    """
    raise if there is no file in post request
    """

    def __init__(self, msg: str, msg_api=None):
        super(MissingFileException, self).__init__(msg_api=msg_api, msg=msg)

    def __str__(self) -> str:
        return "MissingFileException({})".format(self.msg)

    @property
    def code(self) -> int:
        return 400

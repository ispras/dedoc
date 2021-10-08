from dedoc.common.exceptions.dedoc_exception import DedocException


class BadParametersException(DedocException):
    """
    Raise if given parameters are incorrect and can't be handled by the system
    (for example if string provided instead of bool)
    """

    def __init__(self, msg: str, msg_api=None):
        super(BadParametersException, self).__init__(msg=msg, msg_api=msg_api)

    def __str__(self) -> str:
        return "BadParametersException({})".format(self.msg)

    @property
    def code(self) -> int:
        return 400

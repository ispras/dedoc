

class MissingFileException(Exception):
    """
    raise if there is no file in post request
    """

    def __init__(self, msg: str, msg_api=None):
        super(MissingFileException, self).__init__()
        self.msg = msg
        self.msg_api = msg if msg_api is None else msg_api

    def __str__(self) -> str:
        return "MissingFileException({})".format(self.msg)

    @property
    def code(self) -> int:
        return 400

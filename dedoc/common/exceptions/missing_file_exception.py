
class MissingFileException(Exception):
    """
    raise if there is no file in post request
    """

    def __init__(self, msg: str):
        super(MissingFileException, self).__init__()
        self.msg = msg

    def __str__(self) -> str:
        return "MissingFileException({})".format(self.msg)

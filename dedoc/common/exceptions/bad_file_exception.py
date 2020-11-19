
class BadFileFormatException(Exception):
    """
    Raise if given file can't be handled by the system (for example if no reader can read this file)
    """

    def __init__(self, msg: str, msg_api=None):
        super(BadFileFormatException, self).__init__()
        self.msg = msg
        self.msg_api = msg if msg_api is None else msg_api

    def __str__(self) -> str:
        return "BadFileException({})".format(self.msg)

    @property
    def code(self) -> int:
        return 415

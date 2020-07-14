
class BadFileFormatException(Exception):
    """
    Raise if given file can't be handled by system (for example if no one reader can read this file)
    """

    def __init__(self, msg: str):
        super(BadFileFormatException, self).__init__()
        self.msg = msg

    def __str__(self) -> str:
        return "BadFileException({})".format(self.msg)

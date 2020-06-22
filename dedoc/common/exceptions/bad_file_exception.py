
class BadFileFormatException(Exception):

    def __init__(self, msg: str):
        super(BadFileFormatException, self).__init__()
        self.msg = msg

    def __str__(self) -> str:
        return "BadFileException({})".format(self.msg)

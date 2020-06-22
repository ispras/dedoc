
class ConversionException(Exception):

    def __init__(self, msg: str):
        super(ConversionException, self).__init__()
        self.msg = msg

    def __str__(self) -> str:
        return "ConversionException({})".format(self.msg)

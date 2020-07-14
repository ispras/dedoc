
class ConversionException(Exception):
    """
    Raise if conversion of the file ends unsuccessfully or don't finished and converter terminate the process
    of conversion.
    """

    def __init__(self, msg: str):
        super(ConversionException, self).__init__()
        self.msg = msg

    def __str__(self) -> str:
        return "ConversionException({})".format(self.msg)

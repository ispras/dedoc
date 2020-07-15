
class ConversionException(Exception):
    """
    Can be raised if conversion of the file ended unsuccessfully or didn't finish at all
    (converter terminated the process)
    """

    def __init__(self, msg: str):
        super(ConversionException, self).__init__()
        self.msg = msg

    def __str__(self) -> str:
        return "ConversionException({})".format(self.msg)

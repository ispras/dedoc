
class ConversionException(Exception):
    """
    Can be raised if conversion of the file ended unsuccessfully or didn't finish at all
    (converter terminated the process)
    """

    def __init__(self, msg: str, msg_api=None):
        super(ConversionException, self).__init__()
        self.msg = msg
        self.msg_api = msg if msg_api is None else msg_api

    def __str__(self) -> str:
        return "ConversionException({})".format(self.msg)

    @property
    def code(self) -> int:
        return 415

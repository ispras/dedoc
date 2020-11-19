class RecognizeException(Exception):

    def __init__(self, msg: str, msg_api=None):
        super(RecognizeException, self).__init__()
        self.msg = msg
        self.msg_api = msg if msg_api is None else msg_api

    def __str__(self) -> str:
        return "RecognizeException({})".format(self.msg)

    @property
    def code(self) -> int:
        return 500

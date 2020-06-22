class RecognizeException(Exception):

    def __init__(self, msg: str):
        super(RecognizeException, self).__init__()
        self.msg = msg

    def __str__(self) -> str:
        return "RecognizeException({})".format(self.msg)


class JavaNotFoundError(Exception):
    """
    raise if Java not found
    """

    def __init__(self, msg: str) -> None:
        super(JavaNotFoundError, self).__init__()
        self.msg = msg

    def __str__(self) -> str:
        return "JavaNotFoundError({})".format(self.msg)

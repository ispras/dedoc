
class TabbyPdfError(Exception):
    """
    Error from TabbyPDF
    """

    def __init__(self, msg: str) -> None:
        super(TabbyPdfError, self).__init__()
        self.msg = msg

    def __str__(self) -> str:
        return "TabbyPdfError({})".format(self.msg)

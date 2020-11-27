
class StructureExtractorException(Exception):
    """
    Raise if structure extractor can't build structured document from unstructured one.
    """

    def __init__(self, msg: str, msg_api=None):
        super(StructureExtractorException, self).__init__()
        self.msg = msg
        self.msg_api = msg if msg_api is None else msg_api

    def __str__(self) -> str:
        return "StructureExtractorException({})".format(self.msg)

    @property
    def code(self) -> int:
        return 400

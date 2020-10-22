
class StructureExtractorException(Exception):
    """
    Raise if structure extractor can't build structured document from unstructured one.
    """

    def __init__(self, msg: str):
        super(StructureExtractorException, self).__init__()
        self.msg = msg

    def __str__(self) -> str:
        return "StructureExtractorException({})".format(self.msg)

    @property
    def code(self) -> int:
        return 400

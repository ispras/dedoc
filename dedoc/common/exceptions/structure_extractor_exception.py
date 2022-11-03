from typing import Optional

from dedoc.common.exceptions.dedoc_exception import DedocException


class StructureExtractorException(DedocException):
    """
    Raise if structure extractor can't build structured document from unstructured one.
    """

    def __init__(self,
                 msg: str,
                 msg_api: Optional[str] = None,
                 filename: Optional[str] = None,
                 version: Optional[str] = None) -> None:
        super(StructureExtractorException, self).__init__(msg_api=msg_api, msg=msg, filename=filename, version=version)

    def __str__(self) -> str:
        return "StructureExtractorException({})".format(self.msg)

    @property
    def code(self) -> int:
        return 400

from typing import Optional

from dedoc.common.exceptions.dedoc_exception import DedocException


class BadFileFormatException(DedocException):
    """
    Raise if given file can't be handled by the system (for example if no reader can read this file)
    """

    def __init__(self,
                 msg: str,
                 msg_api: Optional[str] = None,
                 filename: Optional[str] = None,
                 version: Optional[str] = None) -> None:
        super(BadFileFormatException, self).__init__(msg_api=msg_api, msg=msg, filename=filename, version=version)

    def __str__(self) -> str:
        return "BadFileException({})".format(self.msg)

    @property
    def code(self) -> int:
        return 415

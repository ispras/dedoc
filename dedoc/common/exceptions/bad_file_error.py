from typing import Optional

from dedoc.common.exceptions.dedoc_error import DedocError


class BadFileFormatError(DedocError):
    """
    Raise if given file can't be handled by the system (for example if no reader can read this file)
    """

    def __init__(self, msg: str, msg_api: Optional[str] = None, filename: Optional[str] = None, version: Optional[str] = None) -> None:
        super(BadFileFormatError, self).__init__(msg_api=msg_api, msg=msg, filename=filename, version=version)

    def __str__(self) -> str:
        return f"BadFileFormatError({self.msg})"

    @property
    def code(self) -> int:
        return 415

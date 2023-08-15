from typing import Optional

from dedoc.common.exceptions.dedoc_error import DedocError


class MissingFileError(DedocError):
    """
    Raise if there is no file in post request
    """

    def __init__(self, msg: str, msg_api: Optional[str] = None, filename: Optional[str] = None, version: Optional[str] = None) -> None:
        super(MissingFileError, self).__init__(msg_api=msg_api, msg=msg, filename=filename, version=version)

    def __str__(self) -> str:
        return f"MissingFileError({self.msg})"

    @property
    def code(self) -> int:
        return 400

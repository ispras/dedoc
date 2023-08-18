from typing import Optional

from dedoc.common.exceptions.dedoc_error import DedocError


class RecognizeError(DedocError):

    def __init__(self, msg: str, msg_api: Optional[str] = None, filename: Optional[str] = None, version: Optional[str] = None) -> None:
        super(RecognizeError, self).__init__(msg_api=msg_api, msg=msg, filename=filename, version=version)

    def __str__(self) -> str:
        return f"RecognizeError({self.msg})"

    @property
    def code(self) -> int:
        return 500

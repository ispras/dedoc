from typing import Optional

from dedoc.common.exceptions.dedoc_error import DedocError


class BadParametersError(DedocError):
    """
    Raise if given parameters are incorrect and can't be handled by the system
    (for example if string provided instead of bool)
    """

    def __init__(self, msg: str, msg_api: Optional[str] = None, filename: Optional[str] = None, version: Optional[str] = None) -> None:
        super(BadParametersError, self).__init__(msg_api=msg_api, msg=msg, filename=filename, version=version)

    def __str__(self) -> str:
        return f"BadParametersError({self.msg})"

    @property
    def code(self) -> int:
        return 400

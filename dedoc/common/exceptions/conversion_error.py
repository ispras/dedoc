from typing import Optional

from dedoc.common.exceptions.dedoc_error import DedocError


class ConversionError(DedocError):
    """
    Can be raised if conversion of the file ended unsuccessfully or didn't finish at all (converter terminated the process)
    """

    def __init__(self, msg: str, msg_api: Optional[str] = None, filename: Optional[str] = None, version: Optional[str] = None) -> None:
        super(ConversionError, self).__init__(msg_api=msg_api, msg=msg, filename=filename, version=version)

    def __str__(self) -> str:
        return f"ConversionError({self.msg})"

    @property
    def code(self) -> int:
        return 415

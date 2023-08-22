from typing import Optional

from dedoc.common.exceptions.dedoc_error import DedocError


class MinioError(DedocError):
    """
    Raise if there is no file in minio
    """

    def __init__(self, msg: str, msg_api: Optional[str] = None, filename: Optional[str] = None, version: Optional[str] = None) -> None:
        super(MinioError, self).__init__(msg_api=msg_api, msg=msg, filename=filename, version=version)

    def __str__(self) -> str:
        return f"MinioError({self.msg})"

    @property
    def code(self) -> int:
        return 404

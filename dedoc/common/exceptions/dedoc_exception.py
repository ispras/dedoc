from typing import Optional

from dedoc.utils.version_utils import get_dedoc_version


class DedocException(Exception):
    def __init__(self,
                 msg: str,
                 msg_api: Optional[str] = None,
                 filename: Optional[str] = None,
                 version: Optional[str] = None,
                 metadata: Optional[dict] = None) -> None:
        super(DedocException, self).__init__()
        self.msg = msg
        self.msg_api = msg if msg_api is None else msg_api
        self.filename = filename
        self.version = version if version is not None else get_dedoc_version()
        self.metadata = metadata

    def __str__(self) -> str:
        return "MissingFileException({})".format(self.msg)

    @property
    def code(self) -> int:
        return 400

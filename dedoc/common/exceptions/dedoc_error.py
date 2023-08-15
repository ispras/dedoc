from typing import Optional

import dedoc


class DedocError(Exception):
    def __init__(self,
                 msg: str,
                 msg_api: Optional[str] = None,
                 filename: Optional[str] = None,
                 version: Optional[str] = None,
                 metadata: Optional[dict] = None) -> None:
        super(DedocError, self).__init__()
        self.msg = msg
        self.msg_api = msg if msg_api is None else msg_api
        self.filename = filename
        self.version = version if version is not None else dedoc.__version__
        self.metadata = metadata

    def __str__(self) -> str:
        return f"DedocError({self.msg})"

    @property
    def code(self) -> int:
        return 400

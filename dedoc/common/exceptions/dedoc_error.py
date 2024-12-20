from typing import Optional

import dedoc.version


class DedocError(Exception):
    def __init__(self,
                 msg: str,
                 msg_api: Optional[str] = None,
                 filename: Optional[str] = None,
                 version: Optional[str] = None,
                 metadata: Optional[dict] = None,
                 code: Optional[int] = None) -> None:
        super(DedocError, self).__init__()
        self.msg = msg
        self.msg_api = msg if msg_api is None else msg_api
        self.filename = filename
        self.version = version if version is not None else dedoc.version.__version__
        self.metadata = metadata
        self.code = 400 if code is None else code

    def __str__(self) -> str:
        return f"DedocError({self.msg})"

    @staticmethod
    def from_dict(error_dict: dict) -> "DedocError":
        return DedocError(
            msg=error_dict.get("msg", ""),
            msg_api=error_dict.get("msg_api", ""),
            filename=error_dict.get("filename", ""),
            version=error_dict.get("version", dedoc.version.__version__),
            metadata=error_dict.get("metadata", {}),
            code=error_dict.get("code", 500)
        )

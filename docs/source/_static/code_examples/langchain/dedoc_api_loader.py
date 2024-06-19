from typing import Optional

from langchain_core.document_loaders import BaseLoader


class DedocAPIFileLoader(BaseLoader):  # напишу код позже, пока это просто плэйсхолдер
    def __init__(  # noqa: FOL005
        self,
        file_path: str,
        split: Optional[str] = "document",
        **kwargs: dict
    ) -> None:
        pass

from abc import ABC, abstractmethod
from typing import List


class BaseAttachmentsExtractor(ABC):

    @abstractmethod
    def can_extract(self, mime: str, filename: str) -> bool:
        pass

    @abstractmethod
    def get_attachments(self, tmpdir: str, filename: str) -> List[List]:
        pass

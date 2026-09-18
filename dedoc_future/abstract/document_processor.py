from abc import ABCMeta, abstractmethod
from typing import Sequence, TypeVar

from tdm import TalismanDocument

from dedoc_future.abstract.config import ImmutableBaseModel
from dedoc_future.abstract.processor import AbstractProcessor

_Config = TypeVar("_Config", bound=ImmutableBaseModel)
_DeployConfig = TypeVar("_DeployConfig", bound=ImmutableBaseModel)


class AbstractDocumentProcessor(
    AbstractProcessor[Sequence[TalismanDocument], Sequence[TalismanDocument], TalismanDocument, _Config, _DeployConfig], metaclass=ABCMeta
):
    @classmethod
    def can_process(cls, data: TalismanDocument, config: _Config) -> bool:
        return True

    @abstractmethod
    def process(self, data: Sequence[TalismanDocument], config: _Config) -> Sequence[TalismanDocument]:
        """
        Process input documents and return changed documents.

        :param data: Sequence of documents to process.
        :param config: Processing configuration.
        :return: Processed sequence of documents.
        """
        pass

from abc import ABC, abstractmethod

from pydantic import BaseModel


class Serializable(ABC):
    """
    Base class for the API schema objects which we later need convert to dict.
    """
    @abstractmethod
    def to_api_schema(self) -> BaseModel:
        """
        Convert class data into the corresponding API schema class.

        :return: API schema class
        """
        pass

from abc import ABC, abstractmethod


class Serializable(ABC):
    """
    Base class for the serializable objects which we need convert to dict.
    """
    @abstractmethod
    def to_dict(self) -> dict:
        """
        Convert class data into dictionary representation.
        Dictionary key should be string and dictionary value should be json serializable.

        :return: dict with all class data.
        """
        pass

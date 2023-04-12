from abc import ABC, abstractmethod


class Serializable(ABC):

    @abstractmethod
    def to_dict(self) -> dict:
        """
        convert class data into dictionary representation. Dictionary key should be string and dictionary value should be json serializable.
        :return: dict with all class data.
        """
        pass

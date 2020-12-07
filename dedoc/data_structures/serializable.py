from abc import ABC, abstractmethod


class Serializable(ABC):

    @abstractmethod
    def to_dict(self, old_version: bool) -> dict:
        """
        convert class data into dictionary representation. Dictionary key should be string and dictionary value should
        be json serializable.
        :param old_version: indicator if old api version is needed
        :return: dict with all class data.
        """
        pass

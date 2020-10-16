from abc import ABC, abstractmethod


class BaseAttachedFile(ABC):
    """
    Abstract class for attached file.
    The class must contain name of attachment on disk for analysis and method get_filename_in_path() and
    original filename for display in meta-information of output
    The class can contain any additional information.
    """

    @abstractmethod
    def get_filename_in_path(self) -> str:
        """
        returns filename for extracting document structure. it is name of exist file in directory of filesystem
        """
        pass

    @abstractmethod
    def get_original_filename(self) -> str:
        """
        returns filename for to display in meta-information of output
        """
        pass

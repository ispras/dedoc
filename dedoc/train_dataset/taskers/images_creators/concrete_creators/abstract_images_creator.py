import zipfile
from abc import ABC, abstractmethod
from typing import List

from dedoc.train_dataset.data_structures.images_archive import ImagesArchive


class AbstractImagesCreator(ABC):

    @abstractmethod
    def add_images(self, page: List[dict], archive: zipfile.ZipFile) -> ImagesArchive:
        """
        take list of line with meta (all lines from one document) and creates images with a bbox around the line
        @param page:
        @param archive: archive where this image creator should put image, named <uid>.jpg
        @return:
        """
        pass

    @abstractmethod
    def can_read(self, page: List[dict]) -> bool:
        """
        return if this creator can handle this document type
        @param page:
        @return:
        """
        pass

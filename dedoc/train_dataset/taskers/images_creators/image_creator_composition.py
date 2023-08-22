import os
import zipfile
from typing import List

from dedoc.train_dataset.data_structures.images_archive import ImagesArchive
from dedoc.train_dataset.exceptions.empty_page_error import EmptyPageError
from dedoc.train_dataset.exceptions.task_creation_error import TaskCreationError
from dedoc.train_dataset.taskers.images_creators.concrete_creators.abstract_images_creator import AbstractImagesCreator


class ImageCreatorComposition:

    def __init__(self, creators: List[AbstractImagesCreator]) -> None:
        self.creators = creators

    def create_images(self, pages: List[List[dict]], tmpdir: str) -> ImagesArchive:
        archive_path = os.path.join(tmpdir, "images.zip")
        with zipfile.ZipFile(archive_path, "w") as archive:
            for page in pages:
                assert len(page) > 0
                if len(pages) == 0:
                    raise EmptyPageError("You try create task with 0 line in document")
                find_handler = False
                for creator in self.creators:
                    if creator.can_read(page):
                        creator.add_images(page=page, archive=archive)
                        find_handler = True
                if not find_handler:
                    raise TaskCreationError(f"No one can handle this task, first line = {pages[0]}")
        return ImagesArchive(archive_path)

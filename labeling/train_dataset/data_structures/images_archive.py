import zipfile
from typing import Optional

from PIL import Image


class ImagesArchive:

    def __init__(self, path: str) -> None:
        self.path = path

    def get_page(self, page_id: int) -> Image.Image:
        with zipfile.ZipFile(self.path) as archive:
            namelist = sorted(archive.namelist())
            image = Image.open(fp=archive.open(namelist[page_id]))
        return image

    def get_page_by_uid(self, uid: str) -> Optional[Image.Image]:
        with zipfile.ZipFile(self.path) as archive:
            if uid not in archive.namelist():
                return None
            image = Image.open(fp=archive.open(uid))
        return image

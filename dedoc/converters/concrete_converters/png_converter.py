import os
from typing import Optional

import cv2
from PIL import Image

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_extensions, converted_mimes


class PNGConverter(AbstractConverter):
    """
    Converts image-like documents into PNG.
    Look to the :class:`~dedoc.converters.AbstractConverter` documentation to get the information about the methods' parameters.
    """
    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)

    def can_convert(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        """
        Checks if the document is image-like, e.g. it has .bmp, .jpg, .tiff, etc. extension.
        """
        return extension.lower() in converted_extensions.image_like_format or mime in converted_mimes.image_like_format

    def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:
        """
        Convert the image-like documents into files with .png extension.
        """
        path_in = os.path.join(tmp_dir, f"{filename}{extension}")
        path_out = os.path.join(tmp_dir, f"{filename}.png")
        if extension in [".hdr", ".pic", ".sr", ".ras", ".j2k"]:
            img = cv2.imread(path_in)
            cv2.imwrite(path_out, img)
        else:
            img = Image.open(path_in)
            img.save(path_out)

        return f"{filename}.png"

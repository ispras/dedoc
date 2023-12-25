import os
from typing import Optional

import cv2
from PIL import Image

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_extensions, converted_mimes
from dedoc.utils.utils import get_mime_extension, splitext_


class PNGConverter(AbstractConverter):
    """
    Converts image-like documents into PNG.
    Look to the :class:`~dedoc.converters.AbstractConverter` documentation to get the information about the methods' parameters.
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)

    def can_convert(self,
                    file_path: Optional[str] = None,
                    extension: Optional[str] = None,
                    mime: Optional[str] = None,
                    parameters: Optional[dict] = None) -> bool:
        """
        Checks if the document is image-like, e.g. it has .bmp, .jpg, .tiff, etc. extension.
        """
        extension, mime = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return extension.lower() in converted_extensions.image_like_format or mime in converted_mimes.image_like_format

    def convert(self, file_path: str, parameters: Optional[dict] = None) -> str:
        """
        Convert the image-like documents into files with .png extension.
        """
        file_dir, file_name = os.path.split(file_path)
        name_wo_ext, extension = splitext_(file_name)
        converted_file_path = os.path.join(file_dir, f"{name_wo_ext}.png")

        if extension in [".hdr", ".pic", ".sr", ".ras", ".j2k"]:
            img = cv2.imread(file_path)
            cv2.imwrite(converted_file_path, img)
        else:
            img = Image.open(file_path)
            img.save(converted_file_path)

        return converted_file_path

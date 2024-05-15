import os
from typing import Optional

import cv2
from PIL import Image, UnidentifiedImageError

from dedoc.common.exceptions.conversion_error import ConversionError
from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_extensions, converted_mimes
from dedoc.utils.utils import splitext_


class PNGConverter(AbstractConverter):
    """
    Converts image-like (.bmp, .jpg, .tiff, etc.) documents into PNG.
    Look to the :class:`~dedoc.converters.AbstractConverter` documentation to get the information about the methods' parameters.
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config, converted_extensions=converted_extensions.image_like_format, converted_mimes=converted_mimes.image_like_format)

    def convert(self, file_path: str, parameters: Optional[dict] = None) -> str:
        """
        Convert the image-like documents into files with .png extension.
        """
        file_dir, file_name = os.path.split(file_path)
        name_wo_ext, extension = splitext_(file_name)
        converted_file_path = os.path.join(file_dir, f"{name_wo_ext}.png")

        if extension.lower() in [".hdr", ".pic", ".sr", ".ras", ".j2k"]:
            img = cv2.imread(file_path)
            cv2.imwrite(converted_file_path, img)
        else:
            try:
                img = Image.open(file_path)
            except UnidentifiedImageError as e:
                raise ConversionError(msg=f"Could not convert file {file_name} ({e})")
            img.save(converted_file_path)

        return converted_file_path

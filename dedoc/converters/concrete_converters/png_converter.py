from typing import Optional

import cv2
from PIL import Image
from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_extensions, converted_mimes


class PNGConverter(AbstractConverter):
    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)

    def can_convert(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        return extension.lower() in converted_extensions.image_like_format or mime in converted_mimes.image_like_format

    def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:
        if extension in ['.hdr', '.pic', '.sr', '.ras']:
            img = cv2.imread("{tmp_dir}/{filename}{extension}".format(
                tmp_dir=tmp_dir, filename=filename, extension=extension
            ))

            cv2.imwrite("{tmp_dir}/{filename}.png".format(
                tmp_dir=tmp_dir, filename=filename
            ), img)
        else:
            img = Image.open("{tmp_dir}/{filename}{extension}".format(
                tmp_dir=tmp_dir, filename=filename, extension=extension
            ))

            img.save("{tmp_dir}/{filename}.png".format(
                tmp_dir=tmp_dir, filename=filename
            ))

        return filename + ".png"

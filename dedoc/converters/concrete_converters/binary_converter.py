from typing import Optional

from dedoc.utils import supported_image_types
from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.converters.concrete_converters.png_converter import PNGConverter


class BinaryConverter(AbstractConverter):
    """
    Converts image-like documents with `mime=application/octet-stream` into PNG.
    Look to the :class:`~dedoc.converters.AbstractConverter` documentation to get the information about the methods' parameters.
    """
    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)
        self.png_converter = PNGConverter(config=config)

    def can_convert(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        """
        Checks if the document is image-like (e.g. it has .bmp, .jpg, .tiff, etc. extension) and has `mime=application/octet-stream`.
        """
        return mime == 'application/octet-stream' and extension in supported_image_types

    def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:
        """
        Convert the image-like and application/octet-stream documents into files with .png extension.
        """
        return self.png_converter.do_convert(tmp_dir, filename, extension)

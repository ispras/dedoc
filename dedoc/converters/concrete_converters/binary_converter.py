from typing import Optional

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.converters.concrete_converters.png_converter import PNGConverter
from dedoc.utils import supported_image_types
from dedoc.utils.utils import get_mime_extension


class BinaryConverter(AbstractConverter):
    """
    Converts image-like documents with `mime=application/octet-stream` into PNG.
    Look to the :class:`~dedoc.converters.AbstractConverter` documentation to get the information about the methods' parameters.
    """
    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)
        self.png_converter = PNGConverter(config=self.config)

    def can_convert(self,
                    file_path: Optional[str] = None,
                    extension: Optional[str] = None,
                    mime: Optional[str] = None,
                    parameters: Optional[dict] = None) -> bool:
        """
        Checks if the document is image-like (e.g. it has .bmp, .jpg, .tiff, etc. extension) and has `mime=application/octet-stream`.
        """
        extension, mime = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return mime == "application/octet-stream" and extension in supported_image_types

    def convert(self, file_path: str, parameters: Optional[dict] = None) -> str:
        """
        Convert the image-like and application/octet-stream documents into files with .png extension.
        """
        return self.png_converter.convert(file_path, parameters=parameters)

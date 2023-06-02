from typing import Optional

from dedoc.utils import supported_image_types
from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.converters.concrete_converters.png_converter import PNGConverter


class BinaryConverter(AbstractConverter):
    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)
        self.png_converter = PNGConverter(config=config)

    def can_convert(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        return mime == 'application/octet-stream' and extension in supported_image_types

    def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:
        return self.png_converter.do_convert(tmp_dir, filename, extension)

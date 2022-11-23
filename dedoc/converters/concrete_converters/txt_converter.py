import os
import shutil
from typing import Optional

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_extensions, converted_mimes


class TxtConverter(AbstractConverter):
    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)

    def can_convert(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        return extension.lower() in converted_extensions.txt_like_format or mime in converted_mimes.txt_like_format

    def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:
        file_path = os.path.join(tmp_dir, f"{filename}{extension}")
        converted_file_name = f"{filename}.txt"
        shutil.copy(file_path, os.path.join(tmp_dir, converted_file_name))
        return converted_file_name

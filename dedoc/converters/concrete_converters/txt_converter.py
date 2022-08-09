import os
from typing import Optional

from bs4 import BeautifulSoup

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_extensions, converted_mimes
from dedoc.utils import get_encoding


class TxtConverter(AbstractConverter):
    def __init__(self, *, config: dict) -> None:
        super().__init__(config=config)

    def can_convert(self, extension: str, mime: str, parameters: Optional[dict] = None) -> bool:
        return extension in converted_extensions.json_like_format or mime in converted_mimes.json_like_format

    def do_convert(self, tmp_dir: str, filename: str, extension: str) -> str:
        file_path = os.path.join(tmp_dir, f"{filename}{extension}")
        encoding = get_encoding(file_path)

        with open(file_path, "r", encoding=encoding) as f:
            xml_content = BeautifulSoup(f, 'xml')

        converted_file_name = f"{filename}.txt"
        with open(os.path.join(tmp_dir, converted_file_name), "w") as f:
            f.write(xml_content.prettify())

        return converted_file_name

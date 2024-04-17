import os
from typing import Optional

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.utils.utils import get_mime_extension, splitext_


class DjvuConverter(AbstractConverter):

    def __init__(self, config: Optional[dict] = None) -> None:
        super().__init__(config=config)

    def can_convert(self,
                    file_path: Optional[str] = None,
                    extension: Optional[str] = None,
                    mime: Optional[str] = None,
                    parameters: Optional[dict] = None) -> bool:
        _, extension = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return extension == ".djvu"

    def convert(self, file_path: str, parameters: Optional[dict] = None) -> str:
        file_dir, file_name = os.path.split(file_path)
        name_wo_ext, _ = splitext_(file_name)
        converted_file_path = os.path.join(file_dir, f"{name_wo_ext}.pdf")
        command = ["ddjvu", "--format=pdf", file_path, converted_file_path]
        self._run_subprocess(command=command, filename=file_name, expected_path=converted_file_path)

        return converted_file_path

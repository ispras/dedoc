import os
import shutil
from typing import Optional

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter
from dedoc.extensions import converted_extensions, converted_mimes
from dedoc.utils.utils import get_mime_extension, splitext_


class TxtConverter(AbstractConverter):
    """
    Converts txt-like documents into TXT by simple renaming.
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
        Checks if the document is txt-like, e.g. it has .xml extension.
        """
        extension, mime = get_mime_extension(file_path=file_path, mime=mime, extension=extension)
        return extension.lower() in converted_extensions.txt_like_format or mime in converted_mimes.txt_like_format

    def convert(self, file_path: str, parameters: Optional[dict] = None) -> str:
        """
        Convert the txt-like documents into files with .txt extension by renaming it.
        """
        file_dir, file_name = os.path.split(file_path)
        name_wo_ext, _ = splitext_(file_name)
        converted_file_path = os.path.join(file_dir, f"{name_wo_ext}.txt")
        shutil.copy(file_path, converted_file_path)

        return converted_file_path

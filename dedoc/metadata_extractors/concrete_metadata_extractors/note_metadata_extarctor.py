import os
import pickle
from typing import Optional

from dedoc.common.exceptions.bad_file_error import BadFileFormatError
from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor


class NoteMetadataExtractor(BaseMetadataExtractor):
    """
    This class is used to extract metadata from documents with extension .note.pickle.
    It expands metadata retrieved by :class:`~dedoc.metadata_extractors.BaseMetadataExtractor`.

    In addition to them, the `author` field can be added to the metadata other fields.
    """

    def __init__(self, *, config: Optional[dict] = None) -> None:
        super().__init__(config=config)

    def can_extract(self,
                    file_path: str,
                    converted_filename: Optional[str] = None,
                    original_filename: Optional[str] = None,
                    parameters: Optional[dict] = None,
                    other_fields: Optional[dict] = None) -> bool:
        """
        Check if the document has .note.pickle extension.
        Look to the :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.can_extract` documentation to get the information about parameters.
        """
        file_dir, file_name, converted_filename, original_filename = self._get_names(file_path, converted_filename, original_filename)
        return converted_filename.lower().endswith(".note.pickle")

    def extract(self,
                file_path: str,
                converted_filename: Optional[str] = None,
                original_filename: Optional[str] = None,
                parameters: Optional[dict] = None,
                other_fields: Optional[dict] = None) -> dict:
        """
        Add the predefined list of metadata for the .note.pickle documents.
        Look to the :meth:`~dedoc.metadata_extractors.AbstractMetadataExtractor.extract` documentation to get the information about parameters.
        """
        file_dir, file_name, converted_filename, original_filename = self._get_names(file_path, converted_filename, original_filename)

        try:
            file_path = os.path.join(file_dir, converted_filename)
            with open(file_path, "rb") as infile:
                note_dict = pickle.load(infile)

            fields = {"author": note_dict["author"]}
            other_fields = {**other_fields, **fields} if other_fields is not None else fields

            meta_info = dict(file_name=original_filename,
                             file_type="note",
                             size=note_dict["size"],
                             access_time=note_dict["modified_time"],
                             created_time=note_dict["created_time"],
                             modified_time=note_dict["modified_time"],
                             other_fields=other_fields)
            return meta_info
        except Exception:
            raise BadFileFormatError(f"Bad note file:\n file_name = {os.path.basename(file_path)}. Seems note-format is broken")

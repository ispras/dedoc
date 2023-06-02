import os
import pickle
from typing import Optional

from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.metadata_extractors.concrete_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor


class NoteMetadataExtractor(BaseMetadataExtractor):

    def __init__(self) -> None:
        super().__init__()

    def can_extract(self,
                    document: UnstructuredDocument,
                    directory: str,
                    filename: str,
                    converted_filename: str,
                    original_filename: str,
                    parameters: Optional[dict] = None,
                    other_fields: Optional[dict] = None) -> bool:
        return filename.lower().endswith(".note.pickle")

    def add_metadata(self,
                     document: UnstructuredDocument,
                     directory: str,
                     filename: str,
                     converted_filename: str,
                     original_filename: str,
                     version: str,
                     parameters: dict = None,
                     other_fields: Optional[dict] = None) -> UnstructuredDocument:

        try:
            file_path = os.path.join(directory, filename)
            with open(file_path, 'rb') as infile:
                note_dict = pickle.load(infile)

            fields = {"author": note_dict['author']}
            other_fields = {**other_fields, **fields} if other_fields is not None else fields

            meta_info = dict(file_name=original_filename,
                             file_type="note",
                             size=note_dict['size'],
                             access_time=note_dict['modified_time'],
                             created_time=note_dict['created_time'],
                             modified_time=note_dict['modified_time'],
                             other_fields=other_fields)
            document.metadata = meta_info
            return document
        except Exception:
            raise BadFileFormatException(f"Bad note file:\n file_name = {os.path.basename(filename)}. Seems note-format is broken")

import os
import pickle
from typing import Optional

from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.data_structures.document_content import DocumentContent
from dedoc.data_structures.document_metadata import DocumentMetadata
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.metadata_extractor.concreat_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor


class NoteMetadataExtractor(BaseMetadataExtractor):

    def __init__(self) -> None:
        super().__init__()

    def can_extract(self,
                    doc: Optional[DocumentContent],
                    directory: str,
                    filename: str,
                    converted_filename: str,
                    original_filename: str,
                    parameters: dict = None) -> bool:
        return filename.endswith(".note.pickle")

    def add_metadata(self,
                     doc: Optional[DocumentContent],
                     directory: Optional[str],
                     filename: Optional[str],
                     converted_filename: Optional[str],
                     original_filename: Optional[str],
                     parameters: dict = None) -> ParsedDocument:
        """
            only for notes and text messages in the document
        """
        try:
            file_path = os.path.join(directory, filename)
            with open(file_path, 'rb') as infile:
                note_dict = pickle.load(infile)

            metadata = DocumentMetadata(
                file_name=original_filename,
                file_type="note",
                size=note_dict['size'],
                access_time=note_dict['modified_time'],
                created_time=note_dict['created_time'],
                modified_time=note_dict['modified_time'],
                other_fields={"author": note_dict['author']}
            )
            parsed_document = ParsedDocument(metadata=metadata, content=doc)
            return parsed_document
        except Exception:
            raise BadFileFormatException("Bad note file:\n file_name = {}. Seems note-format is broken".format(
                os.path.basename(filename)
            ))

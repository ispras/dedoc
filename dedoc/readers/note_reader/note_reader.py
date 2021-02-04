import os
import pickle
from typing import Optional, Tuple

from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.data_structures.unstructured_document import UnstructuredDocument
from dedoc.readers.base_reader import BaseReader
from dedoc.readers.utils.hierarch_level_extractor import HierarchyLevelExtractor


class NoteReader(BaseReader):
    def __init__(self):
        self.hierarchy_level_extractor = HierarchyLevelExtractor()

    def can_read(self,
                 path: str,
                 mime: str,
                 extension: str,
                 document_type: Optional[str],
                 parameters: Optional[dict] = None) -> bool:
        return extension.endswith(".note.pickle")

    def read(self,
             path: str,
             document_type: Optional[str] = None,
             parameters: Optional[dict] = None) -> Tuple[UnstructuredDocument, bool]:

        try:
            with open(path, 'rb') as infile:
                note_dict = pickle.load(infile)

            lines = [LineWithMeta(line=note_dict['content'],
                                  hierarchy_level=None,
                                  annotations=[],
                                  metadata=ParagraphMetadata(line_id=1,
                                                             page_id=1,
                                                             paragraph_type="raw_text",
                                                             predicted_classes=None))]

            lines = self.hierarchy_level_extractor.get_hierarchy_level(lines)
            unstructured = UnstructuredDocument(tables=[], lines=lines)

            return unstructured, False
        except Exception:
            raise BadFileFormatException("Bad note file:\n file_name = {}. Seems note-format is broken".format(
                os.path.basename(path)
            ))

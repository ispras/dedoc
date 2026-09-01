from dataclasses import dataclass
from typing import Optional

from dedoc.data_structures.unstructured_document import UnstructuredDocument


@dataclass
class TxtLayerResult:
    """
    Class for saving information about textual layer correctness of the document chunk.
    - correct - if the document chunk contains correct textual layer or not
    - start - start page of the document chunk (numeration starts with 1)
    - end - end page of the document chunk (numeration starts with 1, end included)
    - document - UnstructuredDocument of document pages[start:end]
    """
    correct: bool
    start: int
    end: Optional[int]
    document: Optional[UnstructuredDocument] = None

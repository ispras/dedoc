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
    - detected_pages - tabby's raw per-page output already produced while detecting the textual layer, covering pages
      [1:detected_last_page]. Handed back to :class:`PdfTabbyReader` so that it extracts only the remaining pages
      instead of extracting these a second time.
    - detected_last_page - last page (numeration starts with 1, included) covered by detected_pages
    """
    correct: bool
    start: int
    end: Optional[int]
    document: Optional[UnstructuredDocument] = None
    detected_pages: Optional[list] = None
    detected_last_page: int = 0

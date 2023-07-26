from typing import Optional

from data_structures import ParsedDocument
from dedoc.config import get_config
from dedoc.configuration_manager import get_manager_config


class DedocPipeline:
    """
    This class allows to run the whole pipeline of the document processing:
    1. Converting
    2. Reading
    3. Metadata extraction
    4. Structure extraction
    5. Output structure construction
    6. Attachments handling
    """

    def __init__(self, config: Optional[dict] = None, manager_config: Optional[dict] = None) -> None:
        config = get_config() if config is None else config
        manager_config = get_manager_config(config) if manager_config is None else manager_config
        self.converter = manager_config.get()


    def parse(self, path: str, parameters: Optional[dict]) -> ParsedDocument:
        pass

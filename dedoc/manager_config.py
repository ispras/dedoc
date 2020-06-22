from dedoc.attachments_extractors.concrete_attach_extractors.excel_attachments_extractor import \
    ExcelAttachmentsExtractor
from dedoc.converters.concrete_converters.docx_converter import DocxConverter
from dedoc.converters.concrete_converters.excel_converter import ExcelConverter
from dedoc.metadata_extractor.basic_metadata_extractor import BasicMetadataExtractor
from dedoc.readers.csv_reader.csv_reader import CSVReader
from dedoc.readers.docx_reader.docx_reader import DocxReader
from dedoc.readers.excel_reader.excel_reader import ExcelReader
from dedoc.readers.json_reader.json_reader import JsonReader
from dedoc.readers.txt_reader.raw_text_reader import RawTextReader
from dedoc.structure_constructor.tree_constructor import TreeConstructor

"""MANAGER SETTINGS"""

__was_called = False

_config = dict(
    converters=[DocxConverter(), ExcelConverter()],

    readers=[DocxReader(),
             ExcelReader(),
             CSVReader(),
             RawTextReader(),
             JsonReader()
             ],

    structure_constructor=TreeConstructor(),

    metadata_extractor=BasicMetadataExtractor(),

    attachments_extractors=[ExcelAttachmentsExtractor()],
)


def get_manager_config() -> dict:
    global __was_called
    __was_called = True
    return _config


def set_manager_config(config: dict):
    if __was_called:
        raise Exception("Config changed after application start, application may be inconsistent")
    global _config
    _config = config

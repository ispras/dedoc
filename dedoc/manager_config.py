__was_called = False


def get_manager_config() -> dict:
    global __was_called
    __was_called = True
    return _config


from dedoc.metadata_extractor.base_metadata_extractor import BaseMetadataExtractor
from dedoc.data_structures.document_metadata import BaseDocumentMetadata
from dedoc.data_structures.paragraph_metadata import BaseParagraphMetadata
from dedoc.attachments_extractors.attachments_extractor import AttachmentsExtractor
from dedoc.attachments_extractors.concrete_attach_extractors.excel_attachments_extractor import \
    ExcelAttachmentsExtractor
from dedoc.attachments_extractors.concrete_attach_extractors.docx_attachments_extractor import \
    DocxAttachmentsExtractor
from dedoc.converters.concrete_converters.docx_converter import DocxConverter
from dedoc.converters.concrete_converters.excel_converter import ExcelConverter
from dedoc.readers.csv_reader.csv_reader import CSVReader
from dedoc.readers.docx_reader.docx_reader import DocxReader
from dedoc.readers.excel_reader.excel_reader import ExcelReader
from dedoc.readers.json_reader.json_reader import JsonReader
from dedoc.readers.txt_reader.raw_text_reader import RawTextReader
from dedoc.structure_constructor.tree_constructor import TreeConstructor

"""MANAGER SETTINGS"""


concrete_attachments_extractors = [ExcelAttachmentsExtractor(), DocxAttachmentsExtractor()]

_config = dict(
    converters=[DocxConverter(), ExcelConverter()],

    readers=[DocxReader(),
             ExcelReader(),
             CSVReader(),
             RawTextReader(),
             JsonReader(),
             ],

    structure_constructor=TreeConstructor(),

    document_metadata_extractor=BaseMetadataExtractor(),

    # Types of metadata structure
    document_metadata=BaseDocumentMetadata,
    paragraph_metadata=BaseParagraphMetadata,

    attachments_extractor=AttachmentsExtractor(extractors=concrete_attachments_extractors)
)


def set_manager_config(config: dict):
    if __was_called:
        raise Exception("Config changed after application start, application may be inconsistent")
    global _config
    _config = config

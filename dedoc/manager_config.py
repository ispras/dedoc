from dedoc.attachments_extractors.attachments_extractor import AttachmentsExtractor
from dedoc.attachments_extractors.concrete_attach_extractors.excel_attachments_extractor import \
    ExcelAttachmentsExtractor
from dedoc.attachments_extractors.concrete_attach_extractors.docx_attachments_extractor import \
    DocxAttachmentsExtractor
from dedoc.converters.concrete_converters.docx_converter import DocxConverter
from dedoc.converters.concrete_converters.excel_converter import ExcelConverter
from dedoc.metadata_extractor.base_metadata_extractor import BaseMetadataExtractor
from dedoc.readers.csv_reader.csv_reader import CSVReader
from dedoc.readers.docx_reader.docx_reader import DocxReader
from dedoc.readers.excel_reader.excel_reader import ExcelReader
from dedoc.readers.json_reader.json_reader import JsonReader
from dedoc.readers.txt_reader.raw_text_reader import RawTextReader
from dedoc.structure_constructor.tree_constructor import TreeConstructor
from structure_constructor.conditional_structure_constructor import ConditionalStructureExtractor
from structure_constructor.linear_constructor import LinearConstructor

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

    structure_constructor=ConditionalStructureExtractor(
        extractors={"linear": LinearConstructor(), "tree": TreeConstructor()},
        default_extractor=LinearConstructor()
    ),

    document_metadata_extractor=BaseMetadataExtractor(),

    attachments_extractor=AttachmentsExtractor(extractors=concrete_attachments_extractors)
)
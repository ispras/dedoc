import logging
import sys

from dedoc.attachments_extractors.attachments_extractor_composition import AttachmentsExtractorComposition
from dedoc.attachments_extractors.concrete_attachments_extractors.docx_attachments_extractor import \
    DocxAttachmentsExtractor
from dedoc.attachments_extractors.concrete_attachments_extractors.excel_attachments_extractor import \
    ExcelAttachmentsExtractor
from dedoc.converters.concrete_converters.docx_converter import DocxConverter
from dedoc.converters.concrete_converters.excel_converter import ExcelConverter
from dedoc.converters.concrete_converters.pptx_converter import PptxConverter
from dedoc.converters.file_converter import FileConverterComposition
from dedoc.metadata_extractor.concreat_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
from dedoc.metadata_extractor.concreat_metadata_extractors.docx_metadata_extractor import DocxMetadataExtractor
from dedoc.metadata_extractor.metadata_extractor_composition import MetadataExtractorComposition
from dedoc.readers.csv_reader.csv_reader import CSVReader
from dedoc.readers.docx_reader.docx_reader import DocxReader
from dedoc.readers.excel_reader.excel_reader import ExcelReader
from dedoc.readers.pptx_reader.pptx_reader import PptxReader
from dedoc.readers.json_reader.json_reader import JsonReader
from dedoc.readers.reader_composition import ReaderComposition
from dedoc.readers.txt_reader.raw_text_reader import RawTextReader
from dedoc.structure_constructor.concreat_structure_constructors.linear_constructor import LinearConstructor
from dedoc.structure_constructor.concreat_structure_constructors.tree_constructor import TreeConstructor
from dedoc.structure_constructor.structure_constructor_composition import StructureConstructorComposition

"""MANAGER SETTINGS"""

concrete_attachments_extractors = [ExcelAttachmentsExtractor(), DocxAttachmentsExtractor()]

logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO,
                    format="%(asctime)s - %(pathname)s - %(levelname)s - %(message)s")

_config = dict(
    converter=FileConverterComposition(converters=[DocxConverter(), ExcelConverter(), PptxConverter()]),

    reader=ReaderComposition(readers=[DocxReader(),
                                      ExcelReader(),
                                      PptxReader(),
                                      CSVReader(),
                                      RawTextReader(),
                                      JsonReader(),
                                      ]),

    structure_constructor=StructureConstructorComposition(
        extractors={"linear": LinearConstructor(), "tree": TreeConstructor()},
        default_extractor=LinearConstructor()
    ),

    document_metadata_extractor=MetadataExtractorComposition(extractors=[
        DocxMetadataExtractor(),
        BaseMetadataExtractor()
    ]),

    attachments_extractor=AttachmentsExtractorComposition(extractors=concrete_attachments_extractors),
    logger=logging.getLogger()
)

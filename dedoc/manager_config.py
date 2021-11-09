from dedoc.attachments_handler.attachments_handler import AttachmentsHandler
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


def get_manager_config(config: dict):
    return dict(
        converter=FileConverterComposition(converters=[DocxConverter(config=config),
                                                       ExcelConverter(config=config),
                                                       PptxConverter(config=config)]),

        reader=ReaderComposition(readers=[DocxReader(config=config),
                                          ExcelReader(),
                                          PptxReader(),
                                          CSVReader(),
                                          RawTextReader(config=config),
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

        attachments_extractor=AttachmentsHandler(config=config)
    )

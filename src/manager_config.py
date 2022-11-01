from src.attachments_handler.attachments_handler import AttachmentsHandler
from src.converters.concrete_converters.docx_converter import DocxConverter
from src.converters.concrete_converters.excel_converter import ExcelConverter
from src.converters.concrete_converters.pdf_converter import PDFConverter
from src.converters.concrete_converters.png_converter import PNGConverter
from src.converters.concrete_converters.txt_converter import TxtConverter
from src.converters.concrete_converters.pptx_converter import PptxConverter
from src.converters.file_converter import FileConverterComposition
from src.metadata_extractor.concreat_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
from src.metadata_extractor.concreat_metadata_extractors.docx_metadata_extractor import DocxMetadataExtractor
from src.metadata_extractor.concreat_metadata_extractors.image_metadata_extractor import ImageMetadataExtractor
from src.metadata_extractor.concreat_metadata_extractors.pdf_metadata_extractor import PdfMetadataExtractor
from src.metadata_extractor.metadata_extractor_composition import MetadataExtractorComposition
from src.readers.archive_reader.archive_reader import ArchiveReader
from src.readers.csv_reader.csv_reader import CSVReader
from src.readers.docx_reader.docx_reader import DocxReader
from src.readers.excel_reader.excel_reader import ExcelReader
from src.readers.json_reader.json_reader import JsonReader
from src.readers.pptx_reader.pptx_reader import PptxReader
from src.readers.reader_composition import ReaderComposition
from src.readers.scanned_reader.pdfscanned_reader.pdf_scan_reader import PdfScanReader
from src.readers.txt_reader.raw_text_reader import RawTextReader
from src.structure_constructor.concreat_structure_constructors.linear_constructor import LinearConstructor
from src.structure_constructor.concreat_structure_constructors.tree_constructor import TreeConstructor
from src.structure_constructor.structure_constructor_composition import StructureConstructorComposition

"""MANAGER SETTINGS"""


def get_manager_config(config: dict) -> dict:
    return dict(
        converter=FileConverterComposition(converters=[DocxConverter(config=config),
                                                       ExcelConverter(config=config),
                                                       PptxConverter(config=config),
                                                       TxtConverter(config=config),
                                                       PDFConverter(config=config),
                                                       PNGConverter(config=config)]),
        reader=ReaderComposition(readers=[DocxReader(config=config),
                                          ExcelReader(config=config),
                                          PptxReader(),
                                          CSVReader(),
                                          RawTextReader(config=config),
                                          JsonReader(),
                                          PdfScanReader(config=config),
                                          ArchiveReader(config=config)]),

        structure_constructor=StructureConstructorComposition(
            extractors={"linear": LinearConstructor(), "tree": TreeConstructor()},
            default_extractor=TreeConstructor()
        ),

        document_metadata_extractor=MetadataExtractorComposition(extractors=[
            DocxMetadataExtractor(),
            PdfMetadataExtractor(config=config),
            ImageMetadataExtractor(config=config),
            BaseMetadataExtractor()
        ]),

        attachments_extractor=AttachmentsHandler(config=config)
    )

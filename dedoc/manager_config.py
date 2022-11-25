import os

from dedoc.attachments_handler.attachments_handler import AttachmentsHandler
from dedoc.converters.concrete_converters.docx_converter import DocxConverter
from dedoc.converters.concrete_converters.excel_converter import ExcelConverter
from dedoc.converters.concrete_converters.pdf_converter import PDFConverter
from dedoc.converters.concrete_converters.png_converter import PNGConverter
from dedoc.converters.concrete_converters.pptx_converter import PptxConverter
from dedoc.converters.concrete_converters.txt_converter import TxtConverter
from dedoc.converters.file_converter import FileConverterComposition
from dedoc.metadata_extractors.concreat_metadata_extractors.base_metadata_extractor import BaseMetadataExtractor
from dedoc.metadata_extractors.concreat_metadata_extractors.docx_metadata_extractor import DocxMetadataExtractor
from dedoc.metadata_extractors.concreat_metadata_extractors.image_metadata_extractor import ImageMetadataExtractor
from dedoc.metadata_extractors.concreat_metadata_extractors.pdf_metadata_extractor import PdfMetadataExtractor
from dedoc.metadata_extractors.metadata_extractor_composition import MetadataExtractorComposition
from dedoc.readers.archive_reader.archive_reader import ArchiveReader
from dedoc.readers.csv_reader.csv_reader import CSVReader
from dedoc.readers.docx_reader.docx_reader import DocxReader
from dedoc.readers.excel_reader.excel_reader import ExcelReader
from dedoc.readers.json_reader.json_reader import JsonReader
from dedoc.readers.pptx_reader.pptx_reader import PptxReader
from dedoc.readers.reader_composition import ReaderComposition
from dedoc.readers.scanned_reader.pdfscanned_reader.pdf_scan_reader import PdfScanReader
from dedoc.readers.txt_reader.raw_text_reader import RawTextReader
from dedoc.structure_constructors.concreat_structure_constructors.linear_constructor import LinearConstructor
from dedoc.structure_constructors.concreat_structure_constructors.tree_constructor import TreeConstructor
from dedoc.structure_constructors.structure_constructor_composition import StructureConstructorComposition
from dedoc.structure_extractors.concrete_structure_extractors.classifying_law_structure_extractor import \
    ClassifyingLawStructureExtractor
from dedoc.structure_extractors.concrete_structure_extractors.default_structure_extractor import \
    DefaultStructureExtractor
from dedoc.structure_extractors.concrete_structure_extractors.diploma_structure_extractor import \
    DiplomaStructureExtractor
from dedoc.structure_extractors.concrete_structure_extractors.foiv_law_structure_extractor import \
    FoivLawStructureExtractor
from dedoc.structure_extractors.concrete_structure_extractors.law_structure_excractor import LawStructureExtractor
from dedoc.structure_extractors.concrete_structure_extractors.tz_structure_extractor import TzStructureExtractor
from dedoc.structure_extractors.structure_extractor_composition import StructureExtractorComposition

"""MANAGER SETTINGS"""


def get_manager_config(config: dict) -> dict:
    converters = [
        DocxConverter(config=config),
        ExcelConverter(config=config),
        PptxConverter(config=config),
        TxtConverter(config=config),
        PDFConverter(config=config),
        PNGConverter(config=config)
    ]
    readers = [
        DocxReader(config=config),
        ExcelReader(config=config),
        PptxReader(),
        CSVReader(),
        RawTextReader(config=config),
        JsonReader(),
        PdfScanReader(config=config),
        ArchiveReader(config=config)
    ]

    metadata_extractors = [
        DocxMetadataExtractor(),
        PdfMetadataExtractor(config=config),
        ImageMetadataExtractor(config=config),
        BaseMetadataExtractor()
    ]

    classifiers_path = os.path.join(os.path.dirname(__file__), "..", "resources", "line_type_classifiers")
    law_extractors = {
        FoivLawStructureExtractor.document_type: FoivLawStructureExtractor(path=os.path.join(classifiers_path, "law_classifier.pkl.gz"),
                                                                           txt_path=os.path.join(classifiers_path, "law_txt_classifier.pkl.gz"),
                                                                           config=config),
        LawStructureExtractor.document_type: LawStructureExtractor(path=os.path.join(classifiers_path, "law_classifier.pkl.gz"),
                                                                   txt_path=os.path.join(classifiers_path, "law_txt_classifier.pkl.gz"),
                                                                   config=config)
    }
    structure_extractors = {
        DefaultStructureExtractor.document_type: DefaultStructureExtractor(),
        DiplomaStructureExtractor.document_type:
            DiplomaStructureExtractor(path=os.path.join(classifiers_path, "diploma_classifier.pkl.gz"), config=config),
        TzStructureExtractor.document_type:
            TzStructureExtractor(path=os.path.join(classifiers_path, "tz_classifier.pkl.gz"),
                                 txt_path=os.path.join(classifiers_path, "tz_classifier_txt.pkl.gz"),
                                 config=config),
        ClassifyingLawStructureExtractor.document_type: ClassifyingLawStructureExtractor(extractors=law_extractors, config=config)
    }

    return dict(
        converter=FileConverterComposition(converters=converters),
        reader=ReaderComposition(readers=readers),
        structure_extractor=StructureExtractorComposition(extractors=structure_extractors, default_key="other"),
        structure_constructor=StructureConstructorComposition(
            extractors={"linear": LinearConstructor(), "tree": TreeConstructor()},
            default_extractor=TreeConstructor()
        ),
        document_metadata_extractor=MetadataExtractorComposition(extractors=metadata_extractors),
        attachments_extractor=AttachmentsHandler(config=config)
    )

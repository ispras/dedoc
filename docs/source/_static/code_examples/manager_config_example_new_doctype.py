from dedoc.attachments_handler import AttachmentsHandler
from dedoc.converters import DocxConverter,ExcelConverter,FileConverterComposition
from dedoc.metadata_extractors import BaseMetadataExtractor,DocxMetadataExtractor,MetadataExtractorComposition
from dedoc.readers import DocxReader,ExcelReader,ReaderComposition
from dedoc.structure_constructors import LinearConstructor,StructureConstructorComposition,TreeConstructor

from pdf_reader import PdfReader
from djvu_converter import DjvuConverter


def get_manager_config(config: dict):
    return dict(
        converter=FileConverterComposition(converters=[DocxConverter(config=config), ExcelConverter(config=config), DjvuConverter(config=config)]),

        reader=ReaderComposition(readers=[DocxReader(config=config),
                                          ExcelReader(),
                                          PdfReader()
                                          ]),

        structure_constructor=StructureConstructorComposition(
            constructors={"linear": LinearConstructor(), "tree": TreeConstructor()},
            default_constructor=LinearConstructor()
        ),

        document_metadata_extractor=MetadataExtractorComposition(extractors=[
            DocxMetadataExtractor(),
            BaseMetadataExtractor()
        ]),

        attachments_extractor=AttachmentsHandler(config=config)
    )

from article_structure_extractor import ArticleStructureExtractor

from dedoc import DedocManager
from dedoc.attachments_handler import AttachmentsHandler
from dedoc.converters import ConverterComposition
from dedoc.metadata_extractors import MetadataExtractorComposition, PdfMetadataExtractor
from dedoc.readers import PdfAutoReader, ReaderComposition
from dedoc.structure_constructors import StructureConstructorComposition, TreeConstructor
from dedoc.structure_extractors import StructureExtractorComposition

manager_config = dict(
    converter=ConverterComposition(converters=[]),
    reader=ReaderComposition(readers=[PdfAutoReader()]),
    structure_extractor=StructureExtractorComposition(extractors={ArticleStructureExtractor.document_type: ArticleStructureExtractor()},
                                                      default_key=ArticleStructureExtractor.document_type),
    structure_constructor=StructureConstructorComposition(constructors={"tree": TreeConstructor()}, default_constructor=TreeConstructor()),
    document_metadata_extractor=MetadataExtractorComposition(extractors=[PdfMetadataExtractor()]),
    attachments_handler=AttachmentsHandler(),
)

manager = DedocManager(manager_config=manager_config)

import os

from djvu_converter import DjvuConverter
from pdf_reader import PdfReader

from dedoc import DedocManager
from dedoc.attachments_handler import AttachmentsHandler
from dedoc.converters import ConverterComposition
from dedoc.metadata_extractors import BaseMetadataExtractor, DocxMetadataExtractor, MetadataExtractorComposition
from dedoc.readers import ReaderComposition
from dedoc.structure_constructors import LinearConstructor, StructureConstructorComposition, TreeConstructor
from dedoc.structure_extractors import DefaultStructureExtractor, StructureExtractorComposition


file_path = "test_dir/The_New_Yorker_Case_Study.djvu"

djvu_converter = DjvuConverter()
pdf_reader = PdfReader()

djvu_converter.can_convert(file_path)  # True
djvu_converter.convert(file_path)  # 'test_dir/The_New_Yorker_Case_Study.pdf'

file_path = "test_dir/pdf_with_attachment.pdf"
pdf_reader.can_read(file_path)  # True
pdf_reader.read(file_path, parameters={"with_attachments": "true"})  # <dedoc.data_structures.UnstructuredDocument>

document = pdf_reader.read(file_path, parameters={"with_attachments": "true"})
list(vars(document))  # ['tables', 'lines', 'attachments', 'warnings', 'metadata']
len(document.attachments)  # 1
len(document.lines)  # 11

"""Adding the implemented handlers to the manager config"""
manager_config = dict(
    converter=ConverterComposition(converters=[DjvuConverter()]),
    reader=ReaderComposition(readers=[PdfReader()]),
    structure_extractor=StructureExtractorComposition(extractors={DefaultStructureExtractor.document_type: DefaultStructureExtractor()}, default_key="other"),
    structure_constructor=StructureConstructorComposition(
        constructors={"linear": LinearConstructor(), "tree": TreeConstructor()},
        default_constructor=LinearConstructor()
    ),
    document_metadata_extractor=MetadataExtractorComposition(extractors=[DocxMetadataExtractor(), BaseMetadataExtractor()]),
    attachments_handler=AttachmentsHandler(),
)

manager = DedocManager(manager_config=manager_config)
result = manager.parse(file_path=file_path, parameters={"with_attachments": "true"})

result  # <dedoc.data_structures.ParsedDocument>
result.to_api_schema().model_dump()  # {'content': {'structure': {'node_id': '0', 'text': '', 'annotations': [], 'metadata': {'paragraph_type': 'root', ...

os.remove("test_dir/The_New_Yorker_Case_Study.pdf")
[os.remove("test_dir/" + file) for file in os.listdir("test_dir/") if file[-4] == "_"]

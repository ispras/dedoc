import mimetypes
import os

from djvu_converter import DjvuConverter
from pdf_reader import PdfReader

from dedoc import DedocManager
from dedoc.attachments_handler import AttachmentsHandler
from dedoc.converters import FileConverterComposition
from dedoc.metadata_extractors import BaseMetadataExtractor, DocxMetadataExtractor, MetadataExtractorComposition
from dedoc.readers import ReaderComposition
from dedoc.structure_constructors import LinearConstructor, StructureConstructorComposition, TreeConstructor
from dedoc.structure_extractors import DefaultStructureExtractor, StructureExtractorComposition


file_dir, file_name = "test_dir", "The_New_Yorker_Case_Study.djvu"
file_path = os.path.join(file_dir, file_name)


djvu_converter = DjvuConverter(config=dict())
pdf_reader = PdfReader()

name_wo_extension, file_extension = os.path.splitext(file_name)
file_mime = mimetypes.guess_type(file_path)[0]

djvu_converter.can_convert(file_extension, file_mime)  # True
djvu_converter.do_convert(file_dir, name_wo_extension, file_extension)  # 'The_New_Yorker_Case_Study.pdf'

file_dir, file_name = "test_dir", "pdf_with_attachment.pdf"
file_path = os.path.join(file_dir, file_name)

name_wo_extension, file_extension = os.path.splitext(file_name)
file_mime = mimetypes.guess_type(file_path)[0]
pdf_reader.can_read(file_path, file_mime, file_extension)  # True

pdf_reader.read(file_path, parameters={"with_attachments": "true"})  # <dedoc.data_structures.UnstructuredDocument>

document = pdf_reader.read(file_path, parameters={"with_attachments": "true"})
list(vars(document))  # ['tables', 'lines', 'attachments', 'warnings', 'metadata']
len(document.attachments)  # 1
len(document.lines)  # 11

"""Adding the implemented handlers to the manager config"""
config = {}
manager_config = dict(
    converter=FileConverterComposition(converters=[DjvuConverter(config=config)]),
    reader=ReaderComposition(readers=[PdfReader()]),
    structure_extractor=StructureExtractorComposition(extractors={DefaultStructureExtractor.document_type: DefaultStructureExtractor()}, default_key="other"),
    structure_constructor=StructureConstructorComposition(
        constructors={"linear": LinearConstructor(), "tree": TreeConstructor()},
        default_constructor=LinearConstructor()
    ),
    document_metadata_extractor=MetadataExtractorComposition(extractors=[DocxMetadataExtractor(), BaseMetadataExtractor()]),
    attachments_handler=AttachmentsHandler(config=config),
)

manager = DedocManager(config=config, manager_config=manager_config)
result = manager.parse(file_path=file_path, parameters={"with_attachments": "true"})

result  # <dedoc.data_structures.ParsedDocument>
result.to_dict()  # OrderedDict([('version', '0.11.2'), ('warnings', []), ('content', OrderedDict([('structure', OrderedDict([('node_id', '0'), ...

os.remove("test_dir/The_New_Yorker_Case_Study.pdf")
[os.remove("test_dir/" + file) for file in os.listdir("test_dir/") if file[-4] == "_"]

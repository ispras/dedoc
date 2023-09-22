import mimetypes
import os

from dedoc import DedocManager
from dedoc.attachments_handler import AttachmentsHandler
from dedoc.converters import DocxConverter, ExcelConverter, FileConverterComposition
from dedoc.metadata_extractors import BaseMetadataExtractor, DocxMetadataExtractor, MetadataExtractorComposition
from dedoc.readers import DocxReader, ExcelReader, ReaderComposition
from dedoc.structure_constructors import LinearConstructor, StructureConstructorComposition, TreeConstructor
from dedoc.structure_extractors import DefaultStructureExtractor, StructureExtractorComposition
from djvu_converter import DjvuConverter
from pdf_reader import PdfReader

djvu_converter = DjvuConverter(config=dict())
pdf_reader = PdfReader()


file_dir, file_name = "test_dir", "example_with_table.djvu"
file_path = os.path.join(file_dir, file_name)

name_wo_extension, file_extension = os.path.splitext(file_name)
file_mime = mimetypes.guess_type(file_path)[0]

djvu_converter.can_convert(file_extension, file_mime)  # True
djvu_converter.do_convert(file_dir, name_wo_extension, file_extension)  # 'example_with_table7.pdf'

file_dir, file_name = "test_dir", "example_with_attachments_depth_1.pdf"
file_path = os.path.join(file_dir, file_name)

name_wo_extension, file_extension = os.path.splitext(file_name)
file_mime = mimetypes.guess_type(file_path)[0]
pdf_reader.can_read(file_path, file_mime, file_extension)  # True

pdf_reader.read(file_path, parameters={"with_attachments": "true"})  # <dedoc.data_structures.UnstructuredDocument>

document = pdf_reader.read(file_path, parameters={"with_attachments": "true"})
list(vars(document))  # ['tables', 'lines', 'attachments', 'warnings', 'metadata']
len(document.attachments)
len(document.lines)

"""Adding the implemented handlers to the manager config"""
config = {"with_attachments": "true"}
manager_config = dict(
        converter=FileConverterComposition(converters=[DocxConverter(config=config), ExcelConverter(config=config), DjvuConverter(config=config)]),

        reader=ReaderComposition(readers=[DocxReader(config=config), ExcelReader(), PdfReader()]),

        structure_constructor=StructureConstructorComposition(
            constructors={"linear": LinearConstructor(), "tree": TreeConstructor()},
            default_constructor=LinearConstructor()
        ),

        document_metadata_extractor=MetadataExtractorComposition(extractors=[DocxMetadataExtractor(), BaseMetadataExtractor()]),
        attachments_extractor=AttachmentsHandler(config=config),
        structure_extractor=StructureExtractorComposition(extractors={
            DefaultStructureExtractor.document_type: DefaultStructureExtractor()}, default_key="other"),
        attachments_handler=AttachmentsHandler(config=config)
    )

manager = DedocManager(config=config, manager_config=manager_config)
result = manager.parse(file_path=file_path, parameters={})

result  # <dedoc.data_structures.ParsedDocument>
result.to_dict()  # OrderedDict([('version', '0.11.2'), ('warnings', []), ('content', OrderedDict([('structure', OrderedDict([('node_id', '0'), ...

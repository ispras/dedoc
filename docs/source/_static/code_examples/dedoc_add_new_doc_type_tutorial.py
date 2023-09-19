from dedoc import DedocManager
from djvu_converter import DjvuConverter
from pdf_reader import PdfReader
import os
import mimetypes

djvu_converter = DjvuConverter(config=dict())
pdf_reader = PdfReader()


file_dir, file_name = "test_dir", "example_with_table7.djvu"
file_path = os.path.join(file_dir, file_name)

name_wo_extension, file_extension = os.path.splitext(file_name)
file_mime = mimetypes.guess_type(file_path)[0]

print(djvu_converter.can_convert(file_extension, file_mime))  # True
print(djvu_converter.do_convert(file_dir, name_wo_extension, file_extension))  # 'example_with_table7.pdf'

file_dir, file_name = "test_dir", "example_with_attachments_depth_1.pdf"
file_path = os.path.join(file_dir, file_name)

name_wo_extension, file_extension = os.path.splitext(file_name)
file_mime = mimetypes.guess_type(file_path)[0]
pdf_reader.can_read(file_path, file_mime, file_extension)  # True

pdf_reader.read(file_path, parameters={"with_attachments": "true"})  # <dedoc.data_structures.UnstructuredDocument>

document = pdf_reader.read(file_path, parameters={"with_attachments": "true"})
print(list(vars(document)))  # ['tables', 'lines', 'attachments', 'warnings', 'metadata']


manager = DedocManager()
result = manager.parse(file_path=file_path, parameters={})

print(result)  # <dedoc.data_structures.ParsedDocument>
print(result.to_dict())  # OrderedDict([('version', ''), ('warnings', []), ('content', OrderedDict([('structure', OrderedDict([('node_id', '0'), ('text', ''), ('annotations', []), ('metadata', OrderedDict([('page_id', 0), ('line_id', 0), ('paragraph_type', 'root'), ('other_fields', {})])), ...


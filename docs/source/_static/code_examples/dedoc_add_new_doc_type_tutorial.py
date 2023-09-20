import mimetypes
import os

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

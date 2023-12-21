# noqa
from dedoc.config import get_config
from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader

# create img reader
# pdf reader can parse image-like formats
img_reader = PdfImageReader(config=get_config())
# and read file example.docx
file_name = "example.jpg"

# we get unstructured file with lines and tables
unstructured_document = img_reader.read(file_path=file_name)

# let's look at the content of unstructured_file, it consists of tables and lines
print(unstructured_document.tables, unstructured_document.lines)

# first of all let's look at the table
table = unstructured_document.tables[0]
# table consists of cells (we assume that table is rectangle)
# so cells is a list of rows and row is a list of cells with metadata
print(table.cells)
# there is also some metadata in the table
print(table.metadata)

# and now let's look at lines. lines is a list of objects of class LineWithMeta
lines = unstructured_document.lines
# let's look at the first line
line = lines[0]
print(line)
# line consists of line (text), metadata, hierarchy level
print(line.line, line.metadata, line.metadata.hierarchy_level)

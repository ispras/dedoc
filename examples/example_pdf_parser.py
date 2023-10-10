# noqa
from dedoc.config import get_config
from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdf_txtlayer_reader import PdfTxtlayerReader
from dedoc.readers.pdf_reader.pdf_image_reader.pdf_image_reader import PdfImageReader

# create pdf text layer reader
pdf_txt_layer_reader = PdfTxtlayerReader(config=get_config())
# and read file example.docx
file_name = "example_with_text_layer.pdf"

# we get unstructured file with lines and tables
unstructured_document = pdf_txt_layer_reader.read(path=file_name, document_type="example")

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
# let's look at first line
line = lines[0]
print(line)
# line consists of line (text), metadata, hierarchy level
print(line.line, line.metadata, line.metadata.hierarchy_level)


# let's now look at the example of parsing pdf document without text layer
# create pdf reader
pdf_image_reader = PdfImageReader(config=get_config())
# and read file example.docx
file_name = "example_without_text_layer.pdf"

# we get unstructured file with lines and tables
unstructured_document = pdf_image_reader.read(path=file_name, document_type="example")

# let's look at the content of unstructured_file, it consists of tables and lines
print(unstructured_document.tables, unstructured_document.lines)

# first of all lets look at the table
table = unstructured_document.tables[0]
# table consists of cells (we assume that table is rectangle)
# so cells is list of rows and row is list of cells with metadata
print(table.cells)
# there is also some metadata in the table
print(table.metadata)

# and now let's look at lines. lines is a list of objects of class LineWithMeta
lines = unstructured_document.lines
# let's look at first line
line = lines[0]
print(line)
# line consists of line (text), metadata, hierarchy level
print(line.line, line.metadata, line.metadata.hierarchy_level)

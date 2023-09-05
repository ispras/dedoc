# noqa
from dedoc.config import get_config
from dedoc.readers.docx_reader.docx_reader import DocxReader

# create docx reader
docx_reader = DocxReader(config=get_config())
# and read file example.docx
file_name = "example.docx"

# we get unstructured file with lines and tables
unstructured_document = docx_reader.read(path=file_name, document_type="example")

# let's look at content of unstructured_file, it consists of tables and lines
print(unstructured_document.tables, unstructured_document.lines)

# first of all lets look at the table
table = unstructured_document.tables[0]
# table consists of cells (we assume that table is rectangle)
# so cells is list of rows and row is list of strings
print(table.cells)
# there is also some metadata in table
print(table.metadata)

# and now lets look at lines. lines it is list of object of class LineWithMeta
lines = unstructured_document.lines
# let's look at first line
line = lines[0]
print(line)
# line consist of line (text), metadata, hierarchy level
print(line.line, line.metadata, line.metadata.hierarchy_level)

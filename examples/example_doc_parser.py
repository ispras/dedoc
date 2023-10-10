# noqa
from dedoc.config import get_config
from dedoc.readers.docx_reader.docx_reader import DocxReader

# create docx reader
docx_reader = DocxReader(config=get_config())
# and read file example.docx
file_name = "example.docx"

# we get unstructured file with lines and tables
unstructured_document = docx_reader.read(path=file_name, document_type="example")

# let's look at the content of unstructured_file, it consists of tables and lines
print(unstructured_document.tables, unstructured_document.lines)

# first of all let's look at the table
table = unstructured_document.tables[0]
# table consists of cells (we assume that table is rectangle)
# cell is a list of rows and row is a list of cells with metadata
for row in table.cells:
    for cell in row:
        print(cell.get_text().replace("\n", "\t") + " ", end="")
    print("\n")

# there is also some metadata in the table
print(table.metadata)

# and now let's look at lines. lines is a list of objects of class LineWithMeta
lines = unstructured_document.lines
# let's look at the first line
line = lines[0]
print(line)
# line consists of line (text), metadata, hierarchy level
print(line.line, line.metadata, line.metadata.hierarchy_level)

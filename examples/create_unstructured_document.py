# noqa
#  in this example we create UnstructuredDocument, let's construct document corresponding to example.docx
from dedoc.data_structures import LineMetadata, Table, UnstructuredDocument
from dedoc.data_structures import TableMetadata
from dedoc.data_structures import LineWithMeta

#  First of all let's create some table, table consists of cells (list of rows, and row is a list of cells with metadata)
from dedoc.data_structures import HierarchyLevel
from dedoc.data_structures.cell_with_meta import CellWithMeta
from dedoc.metadata_extractors import BaseMetadataExtractor


table_cells = [
    ["N", "Second name", "Name", "Organization", "Phone", "Notes"],
    ["1", "Ivanov", "Ivan", "ISP RAS", "8-800"],
]
cells_with_meta = [[CellWithMeta(lines=[LineWithMeta(line=cell_text,
                                                     metadata=LineMetadata(page_id=0, line_id=None),
                                                     annotations=[])]) for cell_text in row] for row in table_cells]
# table also has some metadata, let's assume that our table is on the first page
table_metadata = TableMetadata(page_id=0, uid="table 1")

# let's build table
table = Table(cells=cells_with_meta, metadata=table_metadata)

# Documents also contain some text.
# Logical structure of document may be represented by tree (see example_tree.png)
# but unstructured document consists of flat list of lines with text and metadata
# hierarchy structure hidden in HierarchyLevel attribute of LineWithMeta
# let's build first line, it is document tree root:

# hierarchy level defines position of this line in a document tree.

hierarchy_level = HierarchyLevel(
    # most important parameters of HierarchyLevel is level_1 and level_2
    # hierarchy level compares by tuple (level_1, level_2) lesser -> closer to the root of the tree
    level_1=0,
    level_2=0,
    # can_be_multiline and line_type - some parts of the document (for example title) may take more than one line
    # if can_be_multiline is true then several lines in a row with same level_1, level_2 and line_type will be merged in one tree node
    can_be_multiline=True,
    line_type="header"
)
text = "DOCUMENT TITLE"
metadata = LineMetadata(page_id=0, line_id=1, tag_hierarchy_level=None, hierarchy_level=hierarchy_level, other_fields=None)

# Annotations: one may specify some information about some part of the text, for example that some word written in italic font.
annotations = []

line1 = LineWithMeta(line=text, metadata=metadata, annotations=annotations)

unstructured_document = UnstructuredDocument(tables=[table], lines=[line1], attachments=[])

# I hope you understand some concepts of the LineWithMeta, but you may ask why it need level_1 and level_2
# parameters. Why is only level_1 not enough. Imagine that we have lists like these:
# 1.  1.1.  1.2.1.1. and so on, It may be difficult to restrict the length of the list with
# some pre-set number, so you may define
# HierarchyLevel(1, 1) for 1.
# HierarchyLevel(1, 2) for 1.1.
# HierarchyLevel(1, 4) for 1.2.1.1. and so on
unstructured_document = BaseMetadataExtractor().add_metadata(document=unstructured_document,
                                                             directory="./",
                                                             filename="example.docx",
                                                             converted_filename="example.doc",
                                                             original_filename="example.docx")

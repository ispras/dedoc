#  in this example we create UnstructuredDocument, lets construct document corresponding to example.docx
from dedoc.data_structures.line_with_meta import LineWithMeta
from dedoc.data_structures.paragraph_metadata import ParagraphMetadata
from dedoc.data_structures.table import Table
from dedoc.data_structures.table_metadata import TableMetadata


#  First of all lets create some table, table consist of cells (list of rows, and row is a list of strings
from dedoc.configuration_manager import get_manager_config
from dedoc.structure_parser.heirarchy_level import HierarchyLevel

table_cells = [
    ["N", "Second name", "Name", "Organization", "Phone", "Notes"],
    ["1", "Ivanov", "Ivan", "ISP RAS", "8-800"],
]
# table also has some metadata, lets assume that our table is on first page
table_metadata = TableMetadata(page_id=0)

# finally lets build table
table = Table(cells=table_cells, metadata=table_metadata)

# Documents also contain some text.
# Logical structure of document may be represented by tree (see  example_tree.png)
# but unstructured document consist of flat list of lines with text and metadata
# hierarchy structure hidden in HierarchyLevel attribute of LineWithMeta
# lets build firs line, it is document tree root:
text = "DOCUMENT TITLE"
metadata = ParagraphMetadata(
    paragraph_type="title",
    predicted_classes=None,
    page_id=0,
    line_id=0
)
# hierarchy level define position of this line in document tree.

hierarchy_level = HierarchyLevel(
    # most important parameters of HierarchyLevel is level_1 and level_2
    # hierarchy level compares by tuple (level_1, level_2) lesser -> closer to the root of the tree
    level_1=0,
    level_2=0,
    # can_be_multiline and paragraph_type - some parts of the document (for example title) may take more
    # than one line
    # if can_be_multiline is true than several lines in a row with same level_1, level_2 and paragraph_type
    # will be merged in one tree node
    can_be_multiline=True,
    paragraph_type="title"
)

# Annotations: one may specify some information about some part of the text, for example that some word
# written in italic font.
annotations = []

line1 = LineWithMeta(
    line=text,
    hierarchy_level=hierarchy_level,
    metadata=metadata,
    annotations=annotations
)

# I hope you understand some concepts of the LineWithMeta, but you may ask why it need level_1 and level_2
# parameters. Why is only level_1 not enough. Imagine that we have lists like these:
# 1.  1.1.  1.2.1.1. and so on, It may be difficult to restrict the length of the list with
# some pre-set number, so you may define
# HierarchyLevel(1, 1) for 1.
# HierarchyLevel(1, 2) for 1.1.
# HierarchyLevel(1, 4) for 1.2.1.1. and so on


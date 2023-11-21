from dedoc.data_structures import AttachAnnotation, AttachedFile, BoldAnnotation, CellWithMeta, HierarchyLevel, LineMetadata, LineWithMeta, \
    LinkedTextAnnotation, Table, TableAnnotation, TableMetadata, UnstructuredDocument
from dedoc.structure_constructors import TreeConstructor

text = "Simple text line"
simple_line = LineWithMeta(text)

hierarchy_level = HierarchyLevel(level_1=0, level_2=0, line_type="header", can_be_multiline=True)

metadata = LineMetadata(page_id=0, line_id=1, tag_hierarchy_level=None, hierarchy_level=hierarchy_level, other_fields=None)
annotations = [LinkedTextAnnotation(start=0, end=5, value="Now the line isn't so simple :)"), BoldAnnotation(start=7, end=10, value="True")]

super_line = LineWithMeta(text, metadata=metadata, annotations=annotations)

table_cells = [
    ["N", "Second name", "Name", "Organization", "Phone", "Notes"],
    ["1", "Ivanov", "Ivan", "ISP RAS", "8-800"],
]

cells_with_meta = []
for row in table_cells:
    cells_row = []
    for cell_text in row:
        line_with_meta = LineWithMeta(cell_text, metadata=LineMetadata(page_id=0, line_id=None), annotations=[])
        cell = CellWithMeta(lines=[line_with_meta])  # CellWithMeta contains list of LineWithMeta
        cells_row.append(cell)
    cells_with_meta.append(cells_row)

table_metadata = TableMetadata(page_id=0, uid="table")
table = Table(cells=cells_with_meta, metadata=table_metadata)

table_line_metadata = LineMetadata(
    page_id=0,
    line_id=None,
    hierarchy_level=HierarchyLevel(
        level_1=1,
        level_2=0,
        can_be_multiline=False,
        line_type="raw_text"
    ),
)
table_line_text = "Line with simple table"
table_line = LineWithMeta(table_line_text, metadata=table_line_metadata, annotations=[TableAnnotation(name="table", start=0, end=len(table_line_text))])

table_cells = [["Last name First name Patronymic", "Last name First name Patronymic", "Last name First name Patronymic"],
               ["Ivanov", "Ivan", "Ivanovich"],
               ["Petrov", "Petr", "Petrovich"]]

for row in table_cells:
    cells_row = []
    for cell_text in row:
        line_with_meta = LineWithMeta(cell_text, metadata=LineMetadata(page_id=0, line_id=None), annotations=[])
        cell = CellWithMeta(lines=[line_with_meta])  # CellWithMeta contains list of LineWithMeta
        cells_row.append(cell)
    cells_with_meta.append(cells_row)

cells_with_meta[0][0].colspan = 3
cells_with_meta[0][1].invisible = True
cells_with_meta[0][2].invisible = True

table_metadata = TableMetadata(page_id=0, uid="complicated_table")
complicated_table = Table(cells=cells_with_meta, metadata=table_metadata)

complicated_table_line_metadata = LineMetadata(
    page_id=0,
    line_id=None,
    hierarchy_level=HierarchyLevel(
        level_1=1,
        level_2=0,
        can_be_multiline=False,
        line_type="raw_text"
    ),
)
complicated_table_line_text = "complicated table line"

complicated_table_line = LineWithMeta(complicated_table_line_text, metadata=table_line_metadata,
                                      annotations=[TableAnnotation(complicated_table_line_text, 0, len(complicated_table_line_text))])

attached_file = AttachedFile(original_name="docx_example.png", tmp_file_path="test_dir/docx_example.png", need_content_analysis=False, uid="attached_file")

attached_file_line_metadata = LineMetadata(
    page_id=0,
    line_id=None,
    hierarchy_level=HierarchyLevel(
        level_1=1,
        level_2=0,
        can_be_multiline=False,
        line_type="raw_text"
    ),
)
attached_file_line_text = "Line with attached file"
attached_file_line = LineWithMeta(attached_file_line_text, metadata=attached_file_line_metadata,
                                  annotations=[AttachAnnotation(attach_uid="attached_file", start=0, end=len(attached_file_line_text))])

unstructured_document = UnstructuredDocument(
    tables=[table, complicated_table],
    lines=[super_line, table_line, complicated_table_line, attached_file_line],
    attachments=[attached_file]
)

unstructured_document.metadata = {
    "file_name": "my_document.txt",
    "temporary_file_name": "my_document.txt",
    "file_type": "text/plain",
    "size": 11111,  # in bytes
    "access_time": 1696381364,
    "created_time": 1696316594,
    "modified_time": 1696381364
}

structure_constructor = TreeConstructor()
parsed_document = structure_constructor.structure_document(document=unstructured_document, structure_type="tree")

parsed_document.to_api_schema().model_dump()

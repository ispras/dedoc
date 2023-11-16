from dedoc.data_structures import BoldAnnotation, CellWithMeta, HierarchyLevel, LineMetadata, LineWithMeta, \
    LinkedTextAnnotation, Table, TableMetadata, AttachedFile, UnstructuredDocument

text = "Simple text line"
simple_line = LineWithMeta(text)

hierarchy_level = HierarchyLevel(
    level_1=0,
    level_2=0,
    line_type="header",
    can_be_multiline=True,
)

metadata = LineMetadata(page_id=0, line_id=1, tag_hierarchy_level=None, hierarchy_level=hierarchy_level, other_fields=None)
annotations = [
    LinkedTextAnnotation(0, 5, "Now it isn't so simple :)"),
    BoldAnnotation(7, 10, "True")
]

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
        cell = CellWithMeta(lines=[line_with_meta])
        cells_row.append(cell)
    cells_with_meta.append(cells_row)

table_metadata = TableMetadata(page_id=0, uid="table 1")
table = Table(cells=cells_with_meta, metadata=table_metadata)

attached_file = AttachedFile(original_name="docx_example.png", tmp_file_path="test_dir/docx_example.png", need_content_analysis=True, uid='?')

unstructured_document = UnstructuredDocument(tables=[table], lines=[super_line], attachments=[attached_file])

from dedoc.metadata_extractors import BaseMetadataExtractor
metadata = BaseMetadataExtractor().extract_metadata(directory="./", filename="example.docx", converted_filename="example.doc", original_filename="example.docx")
unstructured_document.metadata = metadata

from dedoc.structure_constructors import TreeConstructor
structure_constructor = TreeConstructor()
parsed_document = structure_constructor.structure_document(document=unstructured_document, structure_type="tree")

print(parsed_document.to_api_schema().model_dump())
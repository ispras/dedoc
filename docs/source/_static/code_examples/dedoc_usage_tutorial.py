from dedoc import DedocManager
from dedoc.attachments_extractors import DocxAttachmentsExtractor
from dedoc.converters import DocxConverter
from dedoc.metadata_extractors import DocxMetadataExtractor
from dedoc.readers import DocxReader
from dedoc.structure_constructors import TreeConstructor
from dedoc.structure_extractors import DefaultStructureExtractor

"""Using converters."""
converter = DocxConverter()
file_path = "test_dir/example.odt"

converter.can_convert(file_path)  # True
converter.convert(file_path)  # 'test_dir/example.docx'

"""Using readers."""
reader = DocxReader()
file_path = "test_dir/example.docx"

reader.can_read(file_path)  # True
reader.read(file_path, parameters={"with_attachments": "true"})  # <dedoc.data_structures.UnstructuredDocument>

document = reader.read(file_path, parameters={"with_attachments": "true"})
# Access and print the values without using 'result' variables or 'print' statements.
list(vars(document))  # ['tables', 'lines', 'attachments', 'warnings', 'metadata']

document.lines[0].line  # Document example
document.lines[0].metadata.tag_hierarchy_level.line_type  # header
document.lines[0].annotations[0]  # Indentation(0:16, 0)
document.lines[0].annotations[3]  # Style(0:16, Title)

document.lines[3].annotations[4]  # Size(0:14, 16.0)
document.lines[3].annotations[5]  # Size(19:26, 16.0)
document.lines[3].annotations[6]  # Bold(0:4, True)
document.lines[3].annotations[7]  # Italic(6:12, True)
document.lines[3].annotations[8]  # Size(14:19, 10.0)

cell = document.tables[0].cells[0][0]
cell  # CellWithMeta(N)
cell.get_text()  # N
cell.rowspan, cell.colspan, cell.invisible  # (1, 1, False)
document.tables[0].metadata.uid  # f2f08354fc2dbcb5ded8885479f498a6
document.tables[0].metadata.page_id  # None
document.tables[0].metadata.rotated_angle  # 0.0
document.tables[1].cells[0][0].invisible  # False
document.tables[1].cells[0][1].invisible  # True
document.tables[1].cells[0][0].colspan  # 2
document.tables[1].cells[0][1].colspan  # 1
document.tables[1].cells[0][0].get_text()  # Table header
document.tables[1].cells[0][1].get_text()  # Table header
document.tables[0].metadata.uid  # f2f08354fc2dbcb5ded8885479f498a6
document.lines[3].line  # Bold, italic, small text.
document.lines[3].annotations[-1]  # Table(0:26, f2f08354fc2dbcb5ded8885479f498a6)

document.attachments[0].uid  # attach_6de4dc06-0b75-11ee-a68a-acde48001122
document.attachments[0].original_name  # image1.png
document.attachments[0].tmp_file_path  # test_dir/1686830947_714.png
document.attachments[0].need_content_analysis  # False
document.attachments[0].uid  # attach_6de4dc06-0b75-11ee-a68a-acde48001122
document.lines[5].line  # More text.
document.lines[5].annotations[-2]  # Attachment(0:10, attach_6de4dc06-0b75-11ee-a68a-acde48001122)

"""Using metadata extractors"""
metadata_extractor = DocxMetadataExtractor()
metadata_extractor.can_extract(file_path)  # True
document.metadata = metadata_extractor.extract(file_path)
document.metadata  # {'file_name': 'example.docx', 'file_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'size': 373795,
# 'access_time': 1686825619, 'created_time': 1686825617, 'modified_time': 1686823541, 'other_fields': {'document_subject': '', 'keywords': '',
# 'category': '', 'comments': '', 'author': '', 'last_modified_by': '', 'created_date': 1568725611, 'modified_date': 1686752726,
# 'last_printed_date': None}}


"""Using attachments extractors"""
attachments_extractor = DocxAttachmentsExtractor()
attachments_extractor.can_extract(file_path)  # True
attachments = attachments_extractor.extract(file_path)
attachments[0]  # <dedoc.data_structures.AttachedFile>


"""Using structure extractors"""
structure_extractor = DefaultStructureExtractor()
document.lines[0].metadata.hierarchy_level  # None
document = structure_extractor.extract_structure(document, {})
document.lines[0].metadata.hierarchy_level  # HierarchyLevel(level_1=1, level_2=1, can_be_multiline=False, line_type=header)


"""Using structure constructors"""
constructor = TreeConstructor()
parsed_document = constructor.structure_document(document)
parsed_document  # <dedoc.data_structures.ParsedDocument>
list(vars(parsed_document))  # ['metadata', 'content', 'attachments', 'version', 'warnings']

list(vars(parsed_document.content))  # ['tables', 'structure', 'warnings']
list(vars(parsed_document.content.structure))  # ['node_id', 'text', 'annotations', 'metadata', 'subparagraphs', 'parent']
parsed_document.content.structure.subparagraphs[0].text  # Document example


"""Run the whole pipeline"""
manager = DedocManager()
result = manager.parse(file_path=file_path, parameters={})

result  # <dedoc.data_structures.ParsedDocument>
result.to_api_schema().model_dump()  # {'content': {'structure': {'node_id': '0', 'text': '', 'annotations': [], 'metadata': {'paragraph_type': 'root', ...

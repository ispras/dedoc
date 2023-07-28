# noqa
"""Using converters."""
from dedoc.converters import DocxConverter

converter = DocxConverter(config={})

import os
import mimetypes

file_dir, file_name = "test_dir", "example.odt"
file_path = os.path.join(file_dir, file_name)

name_wo_extension, file_extension = os.path.splitext(file_name)
file_mime = mimetypes.guess_type(file_path)[0]

converter.can_convert(file_extension, file_mime)  # True
converter.do_convert(file_dir, name_wo_extension, file_extension)  # 'example.docx'


"""Using readers."""
from dedoc.readers import DocxReader

reader = DocxReader(config={})

import os
import mimetypes

file_dir, file_name = "test_dir", "example.docx"
file_path = os.path.join(file_dir, file_name)

name_wo_extension, file_extension = os.path.splitext(file_name)
file_mime = mimetypes.guess_type(file_path)[0]
reader.can_read(file_path, file_mime, file_extension)  # True

reader.read(file_path, parameters={"with_attachments": "true"})  # <dedoc.data_structures.UnstructuredDocument>

document = reader.read(file_path, parameters={"with_attachments": "true"})
print(list(vars(document)))  # ['tables', 'lines', 'attachments', 'warnings', 'metadata']

print(document.lines[0].line)  # Document example
print(document.lines[0].metadata.tag_hierarchy_level.line_type)  # header

print(document.lines[0].annotations[0])  # Indentation(0:16, 0)
print(document.lines[0].annotations[3])  # Style(0:16, Title)

print(document.lines[3].annotations[4])  # Size(0:14, 16.0)
print(document.lines[3].annotations[5])  # Size(19:26, 16.0)
print(document.lines[3].annotations[6])  # Bold(0:4, True)
print(document.lines[3].annotations[7])  # Italic(6:12, True)
print(document.lines[3].annotations[8])  # Size(14:19, 10.0)

print(document.tables[0].cells[0][0])  # N
print(document.tables[0].cells[1][3])  # Cell3
print(document.tables[1].cells[3])  # ['Text 3', 'Text 4']

print(document.tables[0].metadata.uid)  # f2f08354fc2dbcb5ded8885479f498a6
print(document.tables[0].metadata.cell_properties[0][0].colspan)  # 1
print(document.tables[0].metadata.cell_properties[0][0].rowspan)  # 1
print(document.tables[0].metadata.cell_properties[0][0].invisible)  # False

print(document.tables[1].metadata.cell_properties[0][0].invisible)  # False
print(document.tables[1].metadata.cell_properties[0][1].invisible)  # True

print(document.tables[1].metadata.cell_properties[0][0].colspan)  # 2
print(document.tables[1].metadata.cell_properties[0][1].colspan)  # 1

print(document.tables[1].cells[0][0])  # Table header
print(document.tables[1].cells[0][1])  # Table header

print(document.tables[0].metadata.uid)  # f2f08354fc2dbcb5ded8885479f498a6
print(document.lines[3].line)  # Bold, italic, small text.
print(document.lines[3].annotations[-1])  # Table(0:26, f2f08354fc2dbcb5ded8885479f498a6)

print(document.attachments[0].uid)  # attach_6de4dc06-0b75-11ee-a68a-acde48001122
print(document.attachments[0].original_name)  # image1.png
print(document.attachments[0].tmp_file_path)  # test_dir/1686830947_714.png
print(document.attachments[0].need_content_analysis)  # False

print(document.attachments[0].uid)  # attach_6de4dc06-0b75-11ee-a68a-acde48001122
print(document.lines[5].line)  # More text.
print(document.lines[5].annotations[-2])  # Attachment(0:10, attach_6de4dc06-0b75-11ee-a68a-acde48001122)


"""Using metadata extractors"""
from dedoc.metadata_extractors import DocxMetadataExtractor

metadata_extractor = DocxMetadataExtractor()
metadata_extractor.can_extract(document, file_dir, file_name, file_name, file_name)  # True
document = metadata_extractor.add_metadata(document, file_dir, file_name, file_name, file_name)
print(document.metadata)  # {'file_name': 'example.docx', 'file_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'size': 373795, 'access_time': 1686825619, 'created_time': 1686825617, 'modified_time': 1686823541, 'other_fields': {'document_subject': '', 'keywords': '', 'category': '', 'comments': '', 'author': '', 'last_modified_by': '', 'created_date': 1568725611, 'modified_date': 1686752726, 'last_printed_date': None}}


"""Using attachments extractors"""
from dedoc.attachments_extractors import DocxAttachmentsExtractor

attachments_extractor = DocxAttachmentsExtractor()
attachments_extractor.can_extract(file_extension, file_mime)  # True
attachments = attachments_extractor.get_attachments(file_dir, file_name, {})
print(attachments[0])  # <dedoc.data_structures.AttachedFile>


"""Using structure extractors"""
from dedoc.structure_extractors import DefaultStructureExtractor

structure_extractor = DefaultStructureExtractor()
print(document.lines[0].metadata.hierarchy_level)  # None
document = structure_extractor.extract_structure(document, {})
print(document.lines[0].metadata.hierarchy_level)  # HierarchyLevel(level_1=1, level_2=1, can_be_multiline=False, line_type=header)


"""Using structure constructors"""
from dedoc.structure_constructors import TreeConstructor

constructor = TreeConstructor()
parsed_document = constructor.structure_document(document)
print(parsed_document)  # <dedoc.data_structures.ParsedDocument>
print(list(vars(parsed_document)))  # ['metadata', 'content', 'attachments', 'version', 'warnings']

print(list(vars(parsed_document.content)))  # ['tables', 'structure', 'warnings']
print(list(vars(parsed_document.content.structure)))  # ['node_id', 'text', 'annotations', 'metadata', 'subparagraphs', 'parent']
print(parsed_document.content.structure.subparagraphs[0].text)  # Document example


"""Run the whole pipeline"""
from dedoc.manager.dedoc_manager import DedocManager
from dedoc.config import _config as config
from dedoc.manager_config import get_manager_config

manager = DedocManager.from_config("", get_manager_config(config=config), config=config)
result = manager.parse_file(file_path=file_path, parameters={})

print(result)  # <dedoc.data_structures.ParsedDocument>
print(result.to_dict())  # OrderedDict([('version', ''), ('warnings', []), ('content', OrderedDict([('structure', OrderedDict([('node_id', '0'), ('text', ''), ('annotations', []), ('metadata', OrderedDict([('page_id', 0), ('line_id', 0), ('paragraph_type', 'root'), ('other_fields', {})])), ...

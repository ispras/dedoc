import re
from typing import List

import html2text

from dedoc.api.api_utils import json2html
from dedoc.data_structures import BoldAnnotation, HierarchyLevel, LineWithMeta, UnstructuredDocument
from dedoc.metadata_extractors import DocxMetadataExtractor, PdfMetadataExtractor
from dedoc.readers import DocxReader, PdfTabbyReader
from dedoc.structure_constructors import TreeConstructor
from dedoc.structure_extractors import DefaultStructureExtractor
from dedoc.structure_extractors.patterns import DottedListPattern, LetterListPattern, RegexpPattern, TagHeaderPattern, TagListPattern
from dedoc.structure_extractors.patterns.abstract_pattern import AbstractPattern


# example for docx

docx_reader = DocxReader()
docx_metadata_extractor = DocxMetadataExtractor()
structure_extractor = DefaultStructureExtractor()
structure_constructor = TreeConstructor()

docx_file_path = "test_dir/with_tags.docx"

docx_document = docx_reader.read(file_path=docx_file_path)
print("\n\nDocument lines\n")
for document_line in docx_document.lines:
    print(document_line)

patterns = [
    TagHeaderPattern(line_type="custom_header", level_1=1, can_be_multiline=False),
    TagListPattern(line_type="custom_list", level_1=2),
]
docx_document = structure_extractor.extract(document=docx_document, parameters={"patterns": patterns})

docx_document.metadata = docx_metadata_extractor.extract(file_path=docx_file_path)
docx_parsed_document = structure_constructor.construct(document=docx_document).to_api_schema()
html = json2html(
    paragraph=docx_parsed_document.content.structure,
    attachments=docx_parsed_document.attachments,
    tables=docx_parsed_document.content.tables,
    text=""
)
print(f"\n\nDocument tree\n{html2text.html2text(html)}")


def print_document_tree(document: UnstructuredDocument, patterns: List[AbstractPattern]) -> None:
    document = structure_extractor.extract(document=document, parameters={"patterns": patterns})
    parsed_document = structure_constructor.construct(document=document).to_api_schema()
    html = json2html(paragraph=parsed_document.content.structure, attachments=parsed_document.attachments, tables=parsed_document.content.tables, text="")
    print(f"\n\nDocument tree\n{html2text.html2text(html)}")


patterns = [
    TagHeaderPattern(line_type="custom_header", level_1=1, can_be_multiline=False),
    TagListPattern(line_type="custom_list", level_1=2),
    DottedListPattern(line_type="custom_list", level_1=2, can_be_multiline=False),  # for lists like 1.
    LetterListPattern(line_type="custom_list", level_1=3, level_2=1, can_be_multiline=False),  # for lists like a)
    RegexpPattern(regexp=re.compile(r"^header\s+\d+\.\d+"), line_type="custom_header", level_1=1, level_2=2, can_be_multiline=False),
    RegexpPattern(regexp=re.compile(r"^header\s+\d+"), line_type="custom_header", level_1=1, level_2=1, can_be_multiline=False)
]
print_document_tree(document=docx_document, patterns=patterns)

# example for pdf

pdf_reader = PdfTabbyReader()
pdf_metadata_extractor = PdfMetadataExtractor()
pdf_file_path = "test_dir/law.pdf"

pdf_document = pdf_reader.read(file_path=pdf_file_path)
pdf_document.metadata = pdf_metadata_extractor.extract(file_path=pdf_file_path)
print("\n\nDocument lines\n")
for document_line in pdf_document.lines[:10]:
    print(document_line)

patterns = [
    RegexpPattern(regexp=re.compile(r"^part\s+\d+$"), line_type="part", level_1=1, level_2=1, can_be_multiline=False),
    RegexpPattern(regexp=re.compile(r"^chapter\s+\d+$"), line_type="chapter", level_1=1, level_2=2, can_be_multiline=False),
    DottedListPattern(line_type="point", level_1=2, can_be_multiline=False),  # for lists like 1.
    RegexpPattern(regexp=re.compile(r"^\(\d+\)\s"), line_type="item", level_1=3, level_2=1, can_be_multiline=False),   # for lists like (1)
    RegexpPattern(regexp=re.compile(r"^\(\w\)\s"), line_type="sub_item", level_1=3, level_2=2, can_be_multiline=False)    # for lists like (a)
]
print_document_tree(document=pdf_document, patterns=patterns)


print("\n\nDocument lines\n")
for document_line in pdf_document.lines[:10]:
    print(document_line, document_line.annotations)


class SubHeaderPattern(AbstractPattern):
    _name = "sub_header"

    def match(self, line: LineWithMeta) -> bool:
        return self._is_bold(line)

    def get_hierarchy_level(self, line: LineWithMeta) -> HierarchyLevel:
        return HierarchyLevel(line_type=self._line_type, level_1=self._level_1, level_2=self._level_2, can_be_multiline=self._can_be_multiline)

    def _is_bold(self, line: LineWithMeta) -> bool:
        bold_annotations = [annotation for annotation in line.annotations if annotation.name == BoldAnnotation.name and annotation.value == "True"]
        bold_character_number = sum([annotation.end - annotation.start for annotation in bold_annotations])
        return bold_character_number / len(line.line) > 0.5


class TitlePattern(SubHeaderPattern):
    _name = "title"

    def match(self, line: LineWithMeta) -> bool:
        return line.line.isupper() and self._is_bold(line)


patterns = [
    RegexpPattern(regexp=re.compile(r"^part\s+\d+$"), line_type="part", level_1=1, level_2=2, can_be_multiline=False),
    RegexpPattern(regexp=re.compile(r"^chapter\s+\d+$"), line_type="chapter", level_1=1, level_2=3, can_be_multiline=False),
    DottedListPattern(line_type="point", level_1=2, can_be_multiline=False),
    RegexpPattern(regexp=re.compile(r"^\(\d+\)\s"), line_type="item", level_1=3, level_2=1, can_be_multiline=False),
    RegexpPattern(regexp=re.compile(r"^\(\w\)\s"), line_type="sub_item", level_1=3, level_2=2, can_be_multiline=False),
    TitlePattern(line_type="title", level_1=1, level_2=2, can_be_multiline=False),
    SubHeaderPattern(line_type="sub_header", level_1=1, level_2=4, can_be_multiline=True)
]
print_document_tree(document=pdf_document, patterns=patterns)

from collections import defaultdict
from typing import Dict, List

from dedoc.api.schema import LineMetadata
from dedoc.api.schema.annotation import Annotation
from dedoc.api.schema.cell_with_meta import CellWithMeta
from dedoc.api.schema.parsed_document import ParsedDocument
from dedoc.api.schema.table import Table
from dedoc.api.schema.tree_node import TreeNode
from dedoc.data_structures.concrete_annotations.attach_annotation import AttachAnnotation
from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.italic_annotation import ItalicAnnotation
from dedoc.data_structures.concrete_annotations.linked_text_annotation import LinkedTextAnnotation
from dedoc.data_structures.concrete_annotations.reference_annotation import ReferenceAnnotation
from dedoc.data_structures.concrete_annotations.strike_annotation import StrikeAnnotation
from dedoc.data_structures.concrete_annotations.subscript_annotation import SubscriptAnnotation
from dedoc.data_structures.concrete_annotations.superscript_annotation import SuperscriptAnnotation
from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.concrete_annotations.underlined_annotation import UnderlinedAnnotation
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.extensions import converted_mimes, recognized_mimes

_MD_TAGS: Dict[str, tuple] = {
    BoldAnnotation.name: ("**", "**"),
    ItalicAnnotation.name: ("*", "*"),
    StrikeAnnotation.name: ("~~", "~~"),
    SubscriptAnnotation.name: ("<sub>", "</sub>"),
    SuperscriptAnnotation.name: ("<sup>", "</sup>"),
    UnderlinedAnnotation.name: ("<u>", "</u>"),
}

_BOOL_NAMES = {
    BoldAnnotation.name,
    ItalicAnnotation.name,
    StrikeAnnotation.name,
    SubscriptAnnotation.name,
    SuperscriptAnnotation.name,
    UnderlinedAnnotation.name,
}

_SPECIAL_NAMES = {
    TableAnnotation.name,
    ReferenceAnnotation.name,
    AttachAnnotation.name,
    LinkedTextAnnotation.name,
}


class MarkdownRenderer:

    def render(self, document: ParsedDocument) -> str:
        table2uid = {t.metadata.uid: t for t in document.content.tables}
        attach2uid = {a.metadata.uid: a for a in document.attachments}
        md_content = self._walk(document.content.structure, table2uid, attach2uid, depth=0, list_depth=0)

        # handle tables and attachments without links in annotations
        additional_chunks = []
        for table in table2uid.values():
            additional_chunks.append(_render_table(table, table2uid, attach2uid))

        for attach in attach2uid.values():
            additional_chunks.append(_render_attachment(attach))

        if additional_chunks:
            md_content = f"{md_content}\n\n" + "\n\n".join(additional_chunks)
        return f"{md_content}\n"

    def _walk(self, paragraph: TreeNode, table2uid: dict[str, Table], attach2uid: dict[str, ParsedDocument], depth: int, list_depth: int) -> str:
        chunks: List[str] = []
        text = _annotations2md(paragraph, table2uid, attach2uid).strip()

        if text:
            if paragraph.metadata.paragraph_type in (HierarchyLevel.root, HierarchyLevel.header):
                text = f"{'#' * max(1, depth)} {text}\n\n" if depth < 7 else f"**{text}**\n\n"
            elif paragraph.metadata.paragraph_type == HierarchyLevel.list_item:
                text = f"{'  ' * list_depth}- {text}"
            else:
                text = f"\n{text}"

            chunks.append(text)

        list_depth = list_depth + 1 if paragraph.metadata.paragraph_type == HierarchyLevel.list_item else list_depth
        for sub in paragraph.subparagraphs:
            sub_text = self._walk(sub, table2uid, attach2uid, depth=depth + 1, list_depth=list_depth)
            if sub_text.strip():
                chunks.append(sub_text)

        return "\n".join(chunks)


def _annotations2md(paragraph: TreeNode, table2uid: dict[str, Table], attach2uid: dict[str, ParsedDocument]) -> str:
    idx: Dict[int, str] = defaultdict(str)

    for ann in paragraph.annotations:
        name, value = ann.name, ann.value

        is_bool = name in _BOOL_NAMES
        is_special = name in _SPECIAL_NAMES

        if not (is_bool or is_special):
            continue
        if is_bool and value == "False":
            continue

        if name == LinkedTextAnnotation.name:
            idx[ann.end] += f" ({ann.value})"
        elif name == ReferenceAnnotation.name:
            idx[ann.start] += "["
            idx[ann.end] = f"](#{ann.value})" + idx[ann.end]
        elif name == TableAnnotation.name:
            _handle_table(ann, idx, table2uid, attach2uid)
        elif name == AttachAnnotation.name:
            _handle_attach(ann, idx, attach2uid)
        elif is_bool:
            # md tags don't work if tagged text is not stripped
            ann_start = ann.start + (len(paragraph.text[ann.start:]) - len(paragraph.text[ann.start:].lstrip()))
            ann_end = ann.end - (len(paragraph.text[:ann.end]) - len(paragraph.text[:ann.end].rstrip()))
            open_tag, close_tag = _MD_TAGS[ann.name]
            idx[ann_start] += open_tag
            idx[ann_end] = close_tag + idx[ann_end]

    text = paragraph.text.replace("\n", " ")
    for pos, tag in sorted(idx.items(), reverse=True):
        text = text[:pos] + tag + text[pos:]

    return text


def _handle_table(ann: Annotation, idx: Dict[int, str], table2uid: dict[str, Table], attach2uid: dict[str, ParsedDocument]) -> None:
    table = table2uid.pop(ann.value, None)
    block = _render_table(table, table2uid, attach2uid) if table else f"*missing table {ann.value}*"
    idx[ann.end] += f"\n\n{block}\n\n"


def _handle_attach(ann: Annotation, idx: Dict[int, str], attach2uid: dict[str, ParsedDocument]) -> None:
    att = attach2uid.pop(ann.value, None)
    block = _render_attachment(att) if att else f"*missing attachment {ann.value}*"
    idx[ann.end] += f"\n\n{block}\n\n"


def _render_table(table: Table, table2uid: dict[str, Table], attach2uid: dict[str, ParsedDocument]) -> str:
    rows = table.cells
    if not rows:
        return "*empty table*"

    header_cells = _row_cells(rows[0], table2uid, attach2uid)
    ncols = len(header_cells) or 1
    header_cells += [""] * (ncols - len(header_cells))

    body = []
    for row in rows[1:]:
        cells = _row_cells(row, table2uid, attach2uid)
        cells += [""] * (ncols - len(cells))
        body.append("| " + " | ".join(cells[:ncols]) + " |")

    sep = "| " + " | ".join("---" for _ in range(ncols)) + " |"
    out = ["| " + " | ".join(header_cells) + " |", sep, *body]

    if table.metadata.title:
        out.insert(0, f"**{table.metadata.title}**\n")

    return "\n".join(out)


def _row_cells(row: List[CellWithMeta], table2uid: dict[str, Table], attach2uid: dict[str, ParsedDocument]) -> List[str]:
    cells: List[str] = []
    for cell in row:
        if cell.invisible:
            cells.append("")
            continue
        parts = []
        for line in cell.lines:
            node = TreeNode(
                node_id="0",
                text=line.text,
                annotations=line.annotations,
                metadata=LineMetadata(page_id=0, line_id=0, paragraph_type=HierarchyLevel.raw_text),
                subparagraphs=[],
            )
            parts.append(_annotations2md(node, table2uid, attach2uid))
        cell_text = _esc_cell(" ".join(parts))
        cells.append(cell_text)
    return cells


def _render_attachment(att: ParsedDocument) -> str:
    mime = att.metadata.file_type
    fname = att.metadata.file_name
    uri = f"data:{mime};base64,{att.metadata.base64}"
    block = f"![{fname}]({uri})" if _is_image(mime) else f"[{fname}]({uri})"

    inner = ""
    if att.content is not None and att.content.structure is not None:
        inner = MarkdownRenderer().render(att)

    return f"{block}\n\n{inner}" if inner else block


def _is_image(mime: str) -> bool:
    return mime in recognized_mimes.image_like_format.union(converted_mimes.image_like_format)


def _esc_cell(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ").strip()


def json2md(document: ParsedDocument) -> str:
    return MarkdownRenderer().render(document)

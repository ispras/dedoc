from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set

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


@dataclass
class ConverterState:
    uid2table: Dict[str, Table]
    uid2attach: Dict[str, ParsedDocument]
    rendered_tables: Set[str] = field(default_factory=set)
    rendered_attachments: Set[str] = field(default_factory=set)


def json2md(document: ParsedDocument) -> str:
    uid2table = {t.metadata.uid: t for t in document.content.tables}
    uid2attach = {a.metadata.uid: a for a in document.attachments}
    state = ConverterState(uid2table=uid2table, uid2attach=uid2attach)
    md_content = _walk(document.content.structure, state, depth=0, list_depth=0)

    # handle tables and attachments without links in annotations
    additional_chunks = []
    for table_uid, table in state.uid2table.items():
        if table_uid not in state.rendered_tables:
            additional_chunks.append(_render_table(table, state))

    for attach_uid, attach in state.uid2attach.items():
        if attach_uid not in state.rendered_attachments:
            additional_chunks.append(_render_attachment(attach))

    if additional_chunks:
        md_content = f"{md_content}\n\n" + "\n\n".join(additional_chunks)
    return f"{md_content}\n"


def _walk(paragraph: TreeNode, state: ConverterState, depth: int, list_depth: int) -> str:
    chunks: List[str] = []
    text = _annotations2md(paragraph, state).strip()

    if text:
        if paragraph.metadata.paragraph_type in (HierarchyLevel.root, HierarchyLevel.header):
            # 6 is the maximum level of markdown headers
            text = f"{'#' * max(1, depth)} {text}\n\n" if depth < 7 else f"**{text}**\n\n"
        elif paragraph.metadata.paragraph_type == HierarchyLevel.list_item:
            text = f"{'  ' * list_depth}- {text}"
        else:
            text = f"\n{text}"

        chunks.append(text)

    list_depth = list_depth + 1 if paragraph.metadata.paragraph_type == HierarchyLevel.list_item else list_depth
    for sub in paragraph.subparagraphs:
        sub_text = _walk(sub, state, depth=depth + 1, list_depth=list_depth)
        if sub_text.strip():
            chunks.append(sub_text)

    return "\n".join(chunks)


def _annotations2md(paragraph: TreeNode, state: ConverterState) -> str:
    idx: Dict[int, str] = defaultdict(str)

    for ann in paragraph.annotations:
        name, value = ann.name, ann.value

        if name == LinkedTextAnnotation.name:
            idx[ann.end] += f" ({ann.value})"
        elif name == ReferenceAnnotation.name:
            idx[ann.start] += "["
            idx[ann.end] = f"](#{ann.value})" + idx[ann.end]
        elif name == TableAnnotation.name:
            _handle_table(ann, idx, state)
        elif name == AttachAnnotation.name:
            _handle_attach(ann, idx, state)
        elif name in _MD_TAGS and value != "False":
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


def _handle_table(ann: Annotation, idx: Dict[int, str], state: ConverterState) -> None:
    table = state.uid2table.get(ann.value)
    block = _render_table(table, state) if table else f"*missing table {ann.value}*"
    state.rendered_tables.add(ann.value)
    idx[ann.end] += f"\n\n{block}\n\n"


def _handle_attach(ann: Annotation, idx: Dict[int, str], state: ConverterState) -> None:
    att = state.uid2attach.get(ann.value)
    block = _render_attachment(att) if att else f"*missing attachment {ann.value}*"
    state.rendered_attachments.add(ann.value)
    idx[ann.end] += f"\n\n{block}\n\n"


def _render_table(table: Table, state: ConverterState) -> str:
    rows = table.cells
    if not rows:
        return "*empty table*"

    header_cells = _row_cells(rows[0], state)
    ncols = len(header_cells) or 1
    header_cells += [""] * (ncols - len(header_cells))

    body = []
    for row in rows[1:]:
        cells = _row_cells(row, state)
        cells += [""] * (ncols - len(cells))
        body.append("| " + " | ".join(cells[:ncols]) + " |")

    sep = "| " + " | ".join("---" for _ in range(ncols)) + " |"
    out = ["| " + " | ".join(header_cells) + " |", sep, *body]

    if table.metadata.title:
        out.insert(0, f"**{table.metadata.title}**\n")

    return "\n".join(out)


def _row_cells(row: List[CellWithMeta], state: ConverterState) -> List[str]:
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
            parts.append(_annotations2md(node, state))
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
        inner = json2md(att)

    return f"{block}\n\n{inner}" if inner else block


def _is_image(mime: str) -> bool:
    return mime in recognized_mimes.image_like_format.union(converted_mimes.image_like_format)


def _esc_cell(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ").strip()

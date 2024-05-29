from typing import Dict, Iterator, List, Optional, Set

from dedoc.data_structures.concrete_annotations.attach_annotation import AttachAnnotation
from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.italic_annotation import ItalicAnnotation
from dedoc.data_structures.concrete_annotations.reference_annotation import ReferenceAnnotation
from dedoc.data_structures.concrete_annotations.strike_annotation import StrikeAnnotation
from dedoc.data_structures.concrete_annotations.subscript_annotation import SubscriptAnnotation
from dedoc.data_structures.concrete_annotations.superscript_annotation import SuperscriptAnnotation
from dedoc.data_structures.concrete_annotations.table_annotation import TableAnnotation
from dedoc.data_structures.concrete_annotations.underlined_annotation import UnderlinedAnnotation
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.line_metadata import LineMetadata
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.data_structures.table import Table
from dedoc.data_structures.tree_node import TreeNode
from dedoc.extensions import converted_mimes, recognized_mimes


def __prettify_text(text: str) -> Iterator[str]:
    res = []
    for word in text.split():
        if len(word) == 0:
            continue
        res.append(word)
        if sum(map(len, res)) >= 60:
            yield " ".join(res)
            res = []
    if len(res) > 0:
        yield " ".join(res)


def _node2tree(paragraph: TreeNode, depth: int, depths: Set[int] = None) -> str:
    if depths is None:
        depths = set()

    space_symbol = "&nbsp"
    space = [space_symbol] * 4 * (depth - 1) + 4 * ["-"]
    space = "".join(space)
    node_result = []

    node_result.append(f"  {space} {paragraph.metadata.hierarchy_level.line_type}&nbsp{paragraph.node_id} ")
    for text in __prettify_text(paragraph.text):
        space = [space_symbol] * 4 * (depth - 1) + 4 * [space_symbol]
        space = "".join(space)
        node_result.append(f"<p>  {space} {text}  </p>")
    if len(paragraph.subparagraphs) > 0:
        sub_nodes = "\n".join([_node2tree(sub_node, depth=depth + 1, depths=depths.union({depth})) for sub_node in paragraph.subparagraphs])
        return f"""
        <details>
            <summary> <tt> {"".join(node_result)} </tt> </summary>
            {sub_nodes}
        </details>
        """
    else:
        return f"""
                <p>
                     {"".join(node_result)}
                </p>
                """


def json2collapsed_tree(paragraph: TreeNode) -> str:
    result = f"""
    <!DOCTYPE html>
    <html>
     <head>
      <meta charset="utf-8">
      <title>details</title>
     </head>
     <body>
     <tt>
      {_node2tree(paragraph, depth=0)}
      </tt>
     </body>
    </html>
    """
    return result


def json2tree(paragraph: TreeNode) -> str:
    stack = [paragraph]
    nodes = []
    while len(stack) > 0:
        element = stack.pop()
        nodes.append(element)
        stack.extend(element.subparagraphs)
        # stack.reverse()
    nodes.sort(key=lambda node: tuple(map(int, node.node_id.split("."))))
    root, *nodes = nodes
    result = []
    space_symbol = "&nbsp"
    depths = set()
    for node in reversed(nodes):
        node_result = []
        depth = len(node.node_id.split(".")) - 1
        depths.add(depth)
        depths = {d for d in depths if d <= depth}
        space = [space_symbol] * 4 * (depth - 1) + 4 * ["-"]
        space = __add_vertical_line(depths, space)
        node_result.append(f"<p> <tt> <em>  {space} {node.metadata.hierarchy_level.line_type}&nbsp{node.node_id} </em> </tt> </p>")
        for text in __prettify_text(node.text):
            space = [space_symbol] * 4 * (depth - 1) + 4 * [space_symbol]
            space = __add_vertical_line(depths, space)
            node_result.append(f"<p> <tt> {space} {text} </tt> </p>")
        result.extend(reversed(node_result))
    result.append(f"<h3>{root.text}</h3>")
    return "".join(reversed(result))


def __add_vertical_line(depths: Set[int], space: List[str]) -> str:
    for d in depths:
        space[(d - 1) * 4] = "|"
    return "".join(space)


def json2html(text: str,
              paragraph: TreeNode,
              tables: Optional[List[Table]],
              attachments: Optional[List[ParsedDocument]],
              tabs: int = 0,
              table2id: Dict[str, int] = None,
              attach2id: Dict[str, int] = None) -> str:
    tables = [] if tables is None else tables
    attachments = [] if attachments is None else attachments
    table2id = {table.metadata.uid: table_id for table_id, table in enumerate(tables)} if table2id is None else table2id
    attach2id = {attachment.metadata.uid: attachment_id for attachment_id, attachment in enumerate(attachments)} if attach2id is None else attach2id

    ptext = __annotations2html(paragraph=paragraph, table2id=table2id, attach2id=attach2id, tabs=tabs)

    if paragraph.metadata.hierarchy_level.line_type in [HierarchyLevel.header, HierarchyLevel.root]:
        ptext = f"<strong>{ptext.strip()}</strong>"
    elif paragraph.metadata.hierarchy_level.line_type == HierarchyLevel.list_item:
        ptext = f"<em>{ptext.strip()}</em>"
    else:
        ptext = ptext.strip()

    ptext = f'<p> {"&nbsp;" * tabs} {ptext}     <sub> id = {paragraph.node_id} ; type = {paragraph.metadata.hierarchy_level.line_type} </sub></p>'
    if hasattr(paragraph.metadata, "uid"):
        ptext = f'<div id="{paragraph.metadata.uid}">{ptext}</div>'
    text += ptext

    for subparagraph in paragraph.subparagraphs:
        text = json2html(text=text, paragraph=subparagraph, tables=None, attachments=None, tabs=tabs + 4, table2id=table2id, attach2id=attach2id)

    if tables is not None and len(tables) > 0:
        text += "<h3> Tables: </h3>"
        for table in tables:
            text += table2html(table, table2id)
            text += "<p>&nbsp;</p>"

    image_mimes = recognized_mimes.image_like_format.union(converted_mimes.image_like_format)

    if attachments is not None and len(attachments) > 0:
        text += "<h3> Attachments: </h3>"
        for attachment_id, attachment in enumerate(attachments):
            attachment_text = json2html(text="", paragraph=attachment.content.structure, tables=attachment.content.tables, attachments=attachment.attachments)
            attachment_base64 = f'data:{attachment.metadata.file_type};base64,{attachment.metadata.base64}"'
            attachment_link = f'<a href="{attachment_base64}" download="{attachment.metadata.file_name}">{attachment.metadata.file_name}</a>'
            is_image = attachment.metadata.file_type in image_mimes
            attachment_image = f'<img src="{attachment_base64}">' if is_image else ""

            text += f"""<div id="{attachment.metadata.uid}">
                <h4>attachment {attachment_id} ({attachment_link}):</h4>
                {attachment_image}
                {attachment_text}
            </div>"""

    return text


def __value2tag(name: str, value: str) -> str:
    if name == BoldAnnotation.name:
        return "b"

    if name == ItalicAnnotation.name:
        return "i"

    if name == StrikeAnnotation.name:
        return "strike"

    if name == SuperscriptAnnotation.name:
        return "sup"

    if name == SubscriptAnnotation.name:
        return "sub"

    if name == UnderlinedAnnotation.name:
        return "u"

    if name in (AttachAnnotation.name, TableAnnotation.name, ReferenceAnnotation.name):
        return "a"

    if value.startswith("heading "):
        level = value[len("heading "):]
        return "h" + level if level.isdigit() and int(level) < 7 else "strong"

    return value


def __annotations2html(paragraph: TreeNode, table2id: Dict[str, int], attach2id: Dict[str, int], tabs: int = 0) -> str:
    indexes = dict()

    for annotation in paragraph.annotations:
        name = annotation.name
        value = annotation.value

        bool_annotations = [
            BoldAnnotation.name, ItalicAnnotation.name, StrikeAnnotation.name, SubscriptAnnotation.name, SuperscriptAnnotation.name, UnderlinedAnnotation.name
        ]
        check_annotations = bool_annotations + [TableAnnotation.name, ReferenceAnnotation.name, AttachAnnotation.name]
        if name not in check_annotations and not value.startswith("heading "):
            continue
        elif name in bool_annotations and annotation.value == "False":
            continue

        tag = __value2tag(name, value)
        indexes.setdefault(annotation.start, "")
        indexes.setdefault(annotation.end, "")
        if name == TableAnnotation.name:
            indexes[annotation.end] += f' (<{tag} href="#{value}">table {table2id[value]}</{tag}>)'
        elif name == AttachAnnotation.name:
            indexes[annotation.end] += f' (<{tag} href="#{value}">attachment {attach2id[value]}</{tag}>)'
        elif name == ReferenceAnnotation.name:
            indexes[annotation.start] += f'<{tag} href="#{value}">'
            indexes[annotation.end] = f"</{tag}>" + indexes[annotation.end]
        else:
            indexes[annotation.start] += f"<{tag}>"
            indexes[annotation.end] = f"</{tag}>" + indexes[annotation.end]

    insert_tags = sorted([(index, tag) for index, tag in indexes.items()], reverse=True)
    text = paragraph.text

    for index, tag in insert_tags:
        text = text[:index] + tag + text[index:]

    return text.replace("\n", f'<br>{"&nbsp;" * tabs}')


def table2html(table: Table, table2id: Dict[str, int]) -> str:
    uid = table.metadata.uid
    table_title = f" {table.metadata.title}" if table.metadata.title else ""
    text = f"<h4> table {table2id[uid]}:{table_title}</h4>"
    text += f'<table border="1" id={uid} style="border-collapse: collapse; width: 100%;">\n<tbody>\n'
    for row in table.cells:
        text += "<tr>\n"
        for cell in row:
            text += "<td"
            if cell.invisible:
                text += ' style="display: none" '
            cell_node = TreeNode(
                node_id="0",
                text=cell.get_text(),
                annotations=cell.get_annotations(),
                metadata=LineMetadata(page_id=table.metadata.page_id, line_id=0),
                subparagraphs=[],
                parent=None
            )
            text += f' colspan="{cell.colspan}" rowspan="{cell.rowspan}">{__annotations2html(cell_node, {}, {})}</td>\n'

        text += "</tr>\n"
    text += "</tbody>\n</table>"
    return text


def json2txt(paragraph: TreeNode) -> str:
    subparagraphs_text = "\n".join([json2txt(subparagraph) for subparagraph in paragraph.subparagraphs])
    text = f"{paragraph.text}\n{subparagraphs_text}"
    return text

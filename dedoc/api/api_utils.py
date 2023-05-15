from typing import Optional, List, Dict, Iterator, Set

from dedoc.data_structures.concrete_annotations.bold_annotation import BoldAnnotation
from dedoc.data_structures.concrete_annotations.italic_annotation import ItalicAnnotation
from dedoc.data_structures.concrete_annotations.strike_annotation import StrikeAnnotation
from dedoc.data_structures.concrete_annotations.subscript_annotation import SubscriptAnnotation
from dedoc.data_structures.concrete_annotations.superscript_annotation import SuperscriptAnnotation
from dedoc.data_structures.concrete_annotations.underlined_annotation import UnderlinedAnnotation
from dedoc.data_structures.hierarchy_level import HierarchyLevel
from dedoc.data_structures.table import Table
from dedoc.data_structures.tree_node import TreeNode


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


def _node2tree(paragraph: 'TreeNode', depth: int, depths: Set[int] = None) -> str:
    if depths is None:
        depths = set()

    space_symbol = "&nbsp"
    space = [space_symbol] * 4 * (depth - 1) + 4 * ["-"]
    space = "".join(space)
    node_result = []

    node_result.append("  {} {} ".format(
        space, paragraph.metadata.hierarchy_level.line_type + "&nbsp" + paragraph.node_id))
    for text in __prettify_text(paragraph.text):
        space = [space_symbol] * 4 * (depth - 1) + 4 * [space_symbol]
        space = "".join(space)
        node_result.append("<p>  {} {}  </p>".format(space, text))
    if len(paragraph.subparagraphs) > 0:
        sub_nodes = "\n".join([_node2tree(sub_node, depth=depth + 1, depths=depths.union({depth}))
                               for sub_node in paragraph.subparagraphs])
        return """
        <details>
            <summary> <tt> {} </tt> </summary>
            {}
        </details>
        """.format("".join(node_result), sub_nodes)
    else:
        return """
                <p>
                     {}
                </p>
                """.format("".join(node_result))


def json2collapsed_tree(paragraph: 'TreeNode') -> str:
    result = """
    <!DOCTYPE html>
    <html>
     <head>
      <meta charset="utf-8">
      <title>details</title>
     </head>
     <body>
     <tt>
      {}
      </tt>
     </body>
    </html>
    """.format(_node2tree(paragraph, depth=0))
    return result


def json2tree(paragraph: 'TreeNode') -> str:
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
        node_result.append("<p> <tt> <em>  {} {} </em> </tt> </p>".format(
            space, node.metadata.hierarchy_level.line_type + "&nbsp" + node.node_id))
        for text in __prettify_text(node.text):
            space = [space_symbol] * 4 * (depth - 1) + 4 * [space_symbol]
            space = __add_vertical_line(depths, space)
            node_result.append("<p> <tt> {} {} </tt> </p>".format(space, text))
        result.extend(reversed(node_result))
    result.append("<h3>{}</h3>".format(root.text))
    return "".join(reversed(result))


def __add_vertical_line(depths: Set[int], space: List[str]) -> str:
    for d in depths:
        space[(d - 1) * 4] = "|"
    return "".join(space)


def json2html(text: str,
              paragraph: 'TreeNode',
              tables: Optional[List[Table]],
              tabs: int = 0,
              table2id: Dict[str, int] = None) -> str:
    if tables is None:
        tables = []

    if table2id is None:
        table2id = {table.metadata.uid: table_id for table_id, table in enumerate(tables)}

    ptext = __annotations2html(paragraph, table2id)

    if paragraph.metadata.hierarchy_level.line_type in [HierarchyLevel.header, HierarchyLevel.root]:
        ptext = "<strong>{}</strong>".format(ptext.strip())
    elif paragraph.metadata.hierarchy_level.line_type == HierarchyLevel.list_item:
        ptext = "<em>{}</em>".format(ptext.strip())
    else:
        ptext = ptext.strip()

    text += "<p> {tab} {text}     <sub> id = {id} ; type = {type} </sub></p>".format(
        tab="&nbsp;" * tabs,
        text=ptext,
        type=str(paragraph.metadata.hierarchy_level.line_type),
        id=paragraph.node_id
    )

    for subparagraph in paragraph.subparagraphs:
        text = json2html(text=text, paragraph=subparagraph, tables=None, tabs=tabs + 4, table2id=table2id)

    if tables is not None and len(tables) > 0:
        text += "<h3> Tables: </h3>"
        for table in tables:
            text += __table2html(table, table2id)
            text += "<p>&nbsp;</p>"
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

    if value.startswith("heading "):
        level = value[len("heading "):]
        return "h" + level if level.isdigit() and int(level) < 7 else "strong"

    return value


def __annotations2html(paragraph: 'TreeNode', table2id: Dict[str, int]) -> str:
    indexes = dict()

    for annotation in paragraph.annotations:
        name = annotation.name
        value = annotation.value

        bool_annotations = [BoldAnnotation.name,
                            ItalicAnnotation.name,
                            StrikeAnnotation.name,
                            SubscriptAnnotation.name,
                            SuperscriptAnnotation.name,
                            UnderlinedAnnotation.name]
        check_annotations = bool_annotations + ["table"]
        if name not in check_annotations and not value.startswith("heading "):
            continue
        elif name in bool_annotations and annotation.value == "False":
            continue

        tag = __value2tag(name, value)
        indexes.setdefault(annotation.start, "")
        indexes.setdefault(annotation.end, "")
        if name == "table":
            indexes[annotation.start] += '<p> <sub> <a href="#{uid}"> table#{index_table} </a> </sub> </p>' \
                .format(uid=tag, index_table=table2id[tag])
        else:
            indexes[annotation.start] += "<" + tag + ">"
            indexes[annotation.end] = "</" + tag + ">" + indexes[annotation.end]

    insert_tags = sorted([(index, tag) for index, tag in indexes.items()], reverse=True)
    text = paragraph.text

    for index, tag in insert_tags:
        text = text[:index] + tag + text[index:]

    return text.replace("\n", "<br>")


def __table2html(table: Table, table2id: Dict[str, int]) -> str:
    uid = table.metadata.uid
    text = "<h4> table {}:</h4>".format(table2id[uid])
    text += '<table border="1" id={uid} style="border-collapse: collapse; width: 100%;">\n<tbody>\n'.format(
        uid=uid
    )
    cell_properties = table.metadata.cell_properties
    for row_id, row in enumerate(table.cells):
        text += "<tr>\n"
        for col_id, cell in enumerate(row):
            text += "<td"
            if cell_properties:
                prop = cell_properties[row_id][col_id]
                if prop.invisible:
                    text += " style=\"display: none\" "
                text += " colspan=\"{}\" rowspan=\"{}\">{}</td>\n".format(prop.colspan, prop.rowspan, cell)
            else:
                text += f">{cell}</td>\n"
        text += "</tr>\n"
    text += '</tbody>\n</table>'
    return text

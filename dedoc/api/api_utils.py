from typing import Optional, List

from dedoc.data_structures.table import Table
from dedoc.data_structures.tree_node import TreeNode


def json2html(text: str, paragraph: TreeNode, tables: Optional[List[Table]], tabs: int = 0) -> str:

    if paragraph.metadata.paragraph_type in ["header", "root"]:
        ptext = "<strong>{}</strong>".format(paragraph.text.strip())
    elif paragraph.metadata.paragraph_type == "list_item":
        ptext = "<em>{}</em>".format(paragraph.text.strip())
    else:
        ptext = paragraph.text.strip()
    text += "<p> {tab} {text}     <sub> id = {id} ; type = {type} </sub></p>".format(
        tab="&nbsp;" * tabs,
        text=ptext,
        type=str(paragraph.metadata.paragraph_type),
        id=paragraph.node_id
    )

    for subparagraph in paragraph.subparagraphs:
        text = json2html(text=text, paragraph=subparagraph, tables=None, tabs=tabs + 4)

    if tables is not None and len(tables) > 0:
        text += "<h3>Таблицы:</h3>"
        for table in tables:
            text += __table2html(table.cells)
            text += "<p>&nbsp;</p>"
    return text


def __table2html(table: List[List[str]]) -> str:
    text = '<table border="1" style="border-collapse: collapse; width: 100%;">\n<tbody>\n'
    for row in table:
        text += "<tr>\n"
        for col in row:
            text += "<td >{}</td>\n".format(col)
        text += "</tr>\n"
    text += '</tbody>\n</table>'
    return text
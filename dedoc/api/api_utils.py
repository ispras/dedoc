from typing import Optional, List, Dict

from dedoc.data_structures.table import Table


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

    if paragraph.metadata.paragraph_type in ["header", "root"]:
        ptext = "<strong>{}</strong>".format(ptext.strip())
    elif paragraph.metadata.paragraph_type == "list_item":
        ptext = "<em>{}</em>".format(ptext.strip())
    else:
        ptext = ptext.strip()

    text += "<p> {tab} {text}     <sub> id = {id} ; type = {type} </sub></p>".format(
        tab="&nbsp;" * tabs,
        text=ptext,
        type=str(paragraph.metadata.paragraph_type),
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
    if name == "bold":
        return "b"

    if name == "italic":
        return "i"

    if name == "underlined":
        return "u"

    if value.startswith("heading "):
        level = value[len("heading "):]
        return "h" + level if int(level) < 7 else "strong"

    return value


def __annotations2html(paragraph: 'TreeNode', table2id: Dict[str, int]) -> str:
    indexes = dict()

    for annotation in paragraph.annotations:
        name = annotation.name
        value = annotation.value

        if name not in ["bold", "italic", "underlined", "table"] and not value.startswith("heading "):
            continue
        elif name in ["bold", "italic", "underlined"] and annotation.value == "False":
            continue

        tag = __value2tag(name, value)
        indexes.setdefault(annotation.start, "")
        indexes.setdefault(annotation.end, "")
        if name == "table":
            indexes[annotation.start] += '<p> <sub> <a href="#{uid}"> table#{index_table} </a> </sub> </p>'\
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
    for row in table.cells:
        text += "<tr>\n"
        for col in row:
            text += "<td >{}</td>\n".format(col)
        text += "</tr>\n"
    text += '</tbody>\n</table>'
    return text

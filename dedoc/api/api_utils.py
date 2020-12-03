from typing import Optional, List

from dedoc.data_structures.table import Table


def json2html(text: str, paragraph: 'TreeNode', tables: Optional[List[Table]], tabs: int = 0) -> str:
    ptext = __annotations2html(paragraph)

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
        text = json2html(text=text, paragraph=subparagraph, tables=None, tabs=tabs + 4)

    if tables is not None and len(tables) > 0:
        text += "<h3>Таблицы:</h3>"
        for table in tables:
            text += __table2html(table.cells)
            text += "<p>&nbsp;</p>"
    return text


def __value2tag(name: str, value: str) -> str:
    if name == "bold":
        return "b"

    if name == "italic":
        return "i"

    if name == "underlined":
        return "u"

    if value.startswith("style:heading "):
        level = value[14:]
        return "h" + level if int(level) < 7 else "strong"

    return value


def __annotations2html(paragraph: 'TreeNode') -> str:
    indexes = dict()

    for annotation in paragraph.annotations:
        name = annotation.name
        value = annotation.value

        if name not in ["bold", "italic", "underlined"] and not name.startswith("style:heading "):
            continue
        elif name not in ["bold", "italic", "underlined"] and annotation.value == "False":
            continue

        tag = __value2tag(name, value)

        indexes.setdefault(annotation.start, "")
        indexes.setdefault(annotation.end, "")
        indexes[annotation.start] += "<" + tag + ">"
        indexes[annotation.end] = "</" + tag + ">" + indexes[annotation.end]

    insert_tags = sorted([(index, tag) for index, tag in indexes.items()], reverse=True)
    text = paragraph.text

    for index, tag in insert_tags:
        text = text[:index] + tag + text[index:]

    return text.replace("\n", "<br>")


def __table2html(table: List[List[str]]) -> str:
    text = '<table border="1" style="border-collapse: collapse; width: 100%;">\n<tbody>\n'
    for row in table:
        text += "<tr>\n"
        for col in row:
            text += "<td >{}</td>\n".format(col)
        text += "</tr>\n"
    text += '</tbody>\n</table>'
    return text

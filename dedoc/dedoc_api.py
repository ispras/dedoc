import json
import os
from typing import List, Optional

from flask import Flask, request
from flask import Response

import config
from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.common.exceptions.conversion_exception import ConversionException
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.data_structures.table import Table
from dedoc.data_structures.tree_node import TreeNode
from dedoc.dedoc_manager import DocReaderManager

PORT = config.api_port


static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static/")
app = Flask(__name__, static_url_path=static_path)
app.config["MAX_CONTENT_LENGTH"] = config.max_content_length

manager = DocReaderManager()


def __make_response(document_tree: ParsedDocument) -> Response:
    return app.response_class(
        response=json.dumps(obj=document_tree.to_dict(), ensure_ascii=False, indent=2),
        status=200,
        mimetype='application/json'
    )


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        try:
            # check if the post request has the file part
            file = request.files['file']

            parameters = {k: v for k, v in request.values.items()}
            document_tree = manager.parse_file(file, parameters=parameters)
            if not request.values.get("return_html", False):
                return __make_response(document_tree)
            else:
                return __add_texts(text="", paragraph=document_tree.content.structure,
                                   tables=document_tree.content.tables,
                                   tabs=0)
        except (BadFileFormatException, ConversionException) as err:
            print(err)
            file = request.files['file']
            return app.response_class(response="Unsupported file format for {}".format(file.filename), status=415)
        except Exception as e:
            print("exception on file {}".format(file))
            print(e)
            raise e

    return app.send_static_file("form_input.html")


@app.route('/', methods=['GET'])
def get_info():
    path = "info.html"
    return app.send_static_file(path)


@app.route('/favicon.ico', methods=['GET'])
def get_favicon():
    return app.send_static_file("favicon.ico")


def get_file(file: str):
    return app.send_static_file(file)


def __table2html(table: List[List[str]]) -> str:
    text = '<table border="1" style="border-collapse: collapse; width: 100%;">\n<tbody>\n'
    for row in table:
        text += "<tr>\n"
        for col in row:
            text += "<td >{}</td>\n".format(col)
        text += "</tr>\n"
    text += '</tbody>\n</table>'
    return text


def __add_texts(text: str, paragraph: TreeNode, tables: Optional[List[Table]], tabs: int = 0) -> str:

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
        text = __add_texts(text=text, paragraph=subparagraph, tables=None, tabs=tabs + 4)

    if tables is not None and len(tables) > 0:
        text += "<h3>Таблицы:</h3>"
        for table in tables:
            text += __table2html(table.cells)
            text += "<p>&nbsp;</p>"
    return text


def __handle_request():
    file = request.values["fname"]
    path = os.path.join(static_path, file)

    document_tree = manager.parse_existing_file(path=path, parameters=request.values)
    return document_tree


@app.route('/results_file', methods=['GET'])
def send_json():
    document_tree = __handle_request()
    return __make_response(document_tree)


@app.route('/results_file_html', methods=['GET'])
def send_html():
    document_tree = __handle_request()
    text_res = __add_texts("", document_tree.content.structure, document_tree.content.tables, 0)
    return text_res


@app.route('/example_file', methods=['GET'])
def send_example_file():
    path = request.values["fname"]
    return app.send_static_file(path)


@app.route('/exampletable_jpg', methods=['GET'])
def send_jpg():
    path = "exampletable.jpg"
    return app.send_static_file(path)


@app.route('/exampletable_json', methods=['GET'])
def parse_jpg():
    path = os.path.join(static_path, "exampletable.jpg")
    document_tree = manager.parse_existing_file(path=path, parameters={})
    tables = document_tree.content.tables
    return app.response_class(
        response=json.dumps(obj=tables, ensure_ascii=False, indent=2),
        status=200,
        mimetype='application/json'
    )


def run_api():
    app.run(host='0.0.0.0', port=PORT)


if __name__ == "__main__":
    run_api()


import json
import os

from flask import Flask, request
from flask import Response
from flask import send_file

from dedoc.api.api_utils import json2html
from dedoc.config import get_config
from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.common.exceptions.conversion_exception import ConversionException
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.manager.dedoc_manager import DedocManager

config = get_config()

PORT = config["api_port"]

static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static/")
static_files_dirs = config.get("static_files_dirs")

app = Flask(__name__, static_url_path=config.get("static_path", static_path))
app.config["MAX_CONTENT_LENGTH"] = config["max_content_length"]

external_static_files_path = config.get("external_static_files_path")
if external_static_files_path is not None and not os.path.isdir(external_static_files_path):
    raise Exception("Could not find directory {}, probably config is incorrect".format(external_static_files_path))

favicon_path = config.get("favicon_path")
if favicon_path is not None and not os.path.isfile(favicon_path):
    raise Exception("Could not find file {}, probably config is incorrect".format(favicon_path))

manager = DedocManager()


def __make_response(document_tree: ParsedDocument) -> Response:
    return app.response_class(
        response=json.dumps(obj=document_tree.to_dict(), ensure_ascii=False, indent=2),
        status=200,
        mimetype='application/json'
    )


@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        try:
            # check if the post request has the file part

            parameters = {k: v for k, v in request.values.items()}
            document_tree = manager.parse_file(file, parameters=parameters)
            if not request.values.get("return_html", False):
                return __make_response(document_tree)
            else:
                return json2html(text="", paragraph=document_tree.content.structure,
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


@app.route('/', methods=['GET'])
def get_info():
    key = "start_page_path"
    if key not in config:
        path = "info.html"
        return app.send_static_file(path)
    else:
        info_path = os.path.abspath(config[key])
        return send_file(info_path)


def __handle_request(path: str):

    document_tree = manager.parse_existing_file(path=path, parameters=request.values)
    return document_tree


@app.route('/results_file', methods=['GET'])
def send_json():
    path = __get_static_file_path()
    document_tree = __handle_request(path)
    return __make_response(document_tree)


@app.route('/results_file_html', methods=['GET'])
def send_html():
    path = __get_static_file_path()
    document_tree = __handle_request(path)
    text_res = json2html("", document_tree.content.structure, document_tree.content.tables, 0)
    return text_res


@app.route('/static_file', methods=['GET'])
def send_example_file():
    path = __get_static_file_path()
    as_attachment = request.values.get("as_attachment") == "true"
    return send_file(path, as_attachment=as_attachment)


def __get_static_file_path():
    file = request.values["fname"]
    directory_name = request.values.get("directory")
    directory = static_files_dirs[directory_name] if directory_name is not None else static_path
    return os.path.join(directory, file)


def run_api():
    app.run(host='0.0.0.0', port=PORT)

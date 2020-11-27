import importlib
import os

from flask import Flask, request
from flask import send_file

from flask_restplus import Resource, Api

from dedoc.api.swagger_api_utils import get_command_keep_models
from dedoc.common.exceptions.structure_extractor_exception import StructureExtractorException
from dedoc.api.api_utils import json2html
from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.common.exceptions.conversion_exception import ConversionException
from dedoc.common.exceptions.missing_file_exception import MissingFileException
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.manager.dedoc_manager import DedocManager

from dedoc.api import app, config, static_files_dirs, PORT, static_path

module_api_args = importlib.import_module(config['import_path_init_api_args'])


@app.route('/', methods=['GET'])
def get_info():
    """
    Root URL '/' is need start with simple Flask before rest-plus.API otherwise you will get 404 Error. It is bug of rest-plus lib.
    """
    key = "start_page_path"
    if key not in config:
        path = "html_eng/info.html"
        return app.send_static_file(path)
    else:
        info_path = os.path.abspath(config[key])
        return send_file(info_path)


api = Api(app, doc='/swagger/', description=get_command_keep_models())


@api.route('/upload')
@api.expect(module_api_args.init_args(api))
class UploadFile(Resource):
    @api.marshal_with(ParsedDocument.get_api_dict(api), skip_none=True)
    def post(self):
        if request.method == 'POST':
            if 'file' not in request.files or request.files['file'] is None or request.files['file'].filename == "":
                raise MissingFileException("Error: Missing content in request file parameter")

            # check if the post request has the file part
            parameters = {k: v for k, v in request.values.items()}
            document_tree = manager.parse_file(request.files['file'], parameters=parameters)
            if request.values.get("return_html", "False").lower() == "false":
                return document_tree
            else:
                return json2html(text="", paragraph=document_tree.content.structure,
                                 tables=document_tree.content.tables,
                                 tabs=0)


@api.route('/static_file')
@api.doc(False)
class SendExampleFile(Resource):
    def get(self):
        path = _get_static_file_path()
        as_attachment = request.values.get("as_attachment") == "true"
        return send_file(path, as_attachment=as_attachment)


@api.route('/results_file')
@api.doc(False)
class SendJson(Resource):
    @api.marshal_with(ParsedDocument.get_api_dict(api), skip_none=True)
    def get(self):
        path = _get_static_file_path()
        document_tree = _handle_request(path)
        return document_tree


@api.route('/results_file_html')
@api.doc(False)
class SendHtml(Resource):

    def get(self):
        path = _get_static_file_path()
        document_tree = _handle_request(path)
        text_res = json2html("", document_tree.content.structure, document_tree.content.tables, 0)
        return text_res


# ==================== Declare API exceptions =======================

@api.errorhandler(MissingFileException)
def handle_missing_file_exception(error):
    return {'message': error.msg_api}, error.code


@api.errorhandler(BadFileFormatException)
def handle_bad_file_format_exception(error):
    return {'message': error.msg_api}, error.code


@api.errorhandler(ConversionException)
def handle_conversion_exception(error):
    return {'message': error.msg_api}, error.code


@api.errorhandler(StructureExtractorException)
def handle_structure_extractor_exception(error):
    return {'message': error.msg_api}, error.code


@api.errorhandler(Exception)
def handle_exception(error):
    return {'message': str(error)}, 500


manager = DedocManager.from_config()


# ==================== Utils API functions =======================


def _get_static_file_path():
    file = request.values["fname"]
    directory_name = request.values.get("directory")
    directory = static_files_dirs[directory_name] if directory_name is not None else static_path
    return os.path.abspath(os.path.join(directory, file))


def _handle_request(path: str):
    document_tree = manager.parse_existing_file(path=path, parameters=request.values)
    return document_tree


# ==================== Public functions =======================


def get_api() -> Flask:
    """
    Function is used for adding additional routing handlers
    :return: Flask Application
    """
    return app


def run_api(app: Flask):
    app.run(host='0.0.0.0', port=PORT)

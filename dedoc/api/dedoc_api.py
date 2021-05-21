import importlib
import json
import os
from functools import wraps

from flask import Flask, request, Request
from flask import send_file
from flask_restx import Resource, Api, Model
from werkzeug.local import LocalProxy

from dedoc.api.swagger_api_utils import get_command_keep_models
from dedoc.common.exceptions.structure_extractor_exception import StructureExtractorException
from dedoc.api.api_utils import json2html, json2tree
from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.common.exceptions.conversion_exception import ConversionException
from dedoc.common.exceptions.missing_file_exception import MissingFileException
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.manager.dedoc_thread_manager import DedocThreadedManager

from dedoc.api.init_api import app, config, static_files_dirs, PORT, static_path

module_api_args = importlib.import_module(config['import_path_init_api_args'])
logger = config["logger"]


@app.route('/', methods=['GET'])
def get_info():
    """
    Root URL '/' is need start with simple Flask before rest-plus.API otherwise you will get 404 Error.
    It is bug of rest-plus lib.
    """
    key = "start_page_path"
    if key not in config:
        path = "html_eng/info.html"
        return app.send_static_file(path)
    else:
        info_path = os.path.abspath(config[key])
        return send_file(info_path)


@app.route('/version', methods=['GET'])
def get_version():
    return manager.version


api = Api(app, doc='/swagger/', description=get_command_keep_models())


def marshal_with_wrapper(model: Model, request_post: LocalProxy, **other):
    """
    Response marshalling with json indent=2 for json and outputs html for return_html==True
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            if str(request_post.values.get("return_format", "json")).lower() == "json":
                func2 = api.marshal_with(model, **other)(func)
                ob = func2(*args, **kwargs)
                return app.response_class(
                    response=json.dumps(obj=ob, ensure_ascii=False, indent=2),
                    status=200,
                    mimetype='application/json')
            else:
                return app.response_class(
                    response=func(*args, **kwargs),
                    status=200,
                    mimetype='text/html;charset=utf-8')

        return wrapper

    return decorator


def _get_parameters(request: Request):
    return {k: v for k, v in request.values.items()}


@api.route('/upload')
@api.expect(module_api_args.init_args(api))
class UploadFile(Resource):
    @api.doc('parsed document', model=ParsedDocument.get_api_dict(api))
    @marshal_with_wrapper(ParsedDocument.get_api_dict(api), request, skip_none=True)
    def post(self):
        if request.method == 'POST':
            if 'file' not in request.files or request.files['file'] is None or request.files['file'].filename == "":
                raise MissingFileException("Error: Missing content in request_post file parameter")
            # check if the post request_post has the file part
            parameters = _get_parameters(request)
            file = request.files['file']
            logger.info("Get file {} with parameters {}".format(file.name, parameters))
            document_tree = manager.parse_file(file, parameters=parameters)
            if str(parameters.get("return_format", "json")).lower() == "html":
                return json2html(text="", paragraph=document_tree.content.structure,
                                 tables=document_tree.content.tables,
                                 tabs=0)
            elif str(parameters.get("return_format", "json")).lower() == "tree":
                return json2tree(paragraph=document_tree.content.structure)
            else:
                logger.info("Send result. File {} with parameters {}".format(file.filename, parameters))
                return document_tree


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
    @marshal_with_wrapper(ParsedDocument.get_api_dict(api), request, skip_none=True)
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
        return app.response_class(
            response=text_res,
            status=200,
            mimetype='text/html;charset=utf-8')


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


version_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "VERSION"))
manager = DedocThreadedManager.from_config(config=config, version=open(version_file_path).read())


# ==================== Utils API functions =======================


def _get_static_file_path():
    file = request.values["fname"]
    directory_name = request.values.get("directory")
    directory = static_files_dirs[
        directory_name] if directory_name is not None and directory_name in static_files_dirs else static_path
    return os.path.abspath(os.path.join(directory, file))


def _handle_request(path: str):
    parameters = _get_parameters(request)
    document_tree = manager.parse_existing_file(path=path, parameters=parameters)
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

import importlib.metadata
import json
import os
from functools import wraps
from typing import List, Tuple, Callable, Any

import ujson
from flask import Flask, request, Request, Response
from flask import send_file
from flask_restx import Resource, Api, Model
from werkzeug.local import LocalProxy

from dedoc.api.api_utils import json2html, json2tree, json2collapsed_tree
from dedoc.api.init_api import app, config, static_files_dirs, PORT, static_path
from dedoc.api.swagger_api_utils import get_command_keep_models
from dedoc.common.exceptions.dedoc_exception import DedocException
from dedoc.common.exceptions.missing_file_exception import MissingFileException
from dedoc.data_structures.parsed_document import ParsedDocument
from dedoc.manager.dedoc_thread_manager import DedocThreadedManager

module_api_args = importlib.import_module(config['import_path_init_api_args'])
logger = config["logger"]


@app.route('/', methods=['GET'])
def get_info() -> Response:
    """
    Root URL '/' is need start with simple Flask before rest-plus. API otherwise you will get 404 Error.
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
def get_version() -> str:
    return manager.version


api = Api(app, doc='/swagger/', description=get_command_keep_models())


def marshal_with_wrapper(model: Model,
                         request_post: LocalProxy,
                         default_serializer: str = "json",
                         **other: Any) -> Callable:
    """
    Response marshalling with json indent=2 for json and outputs html for return_html==True
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Response:

            serializer = str(request_post.values.get("return_format", default_serializer)).lower()
            if serializer in ("html", "tree", "collapsed_tree"):
                return app.response_class(
                    response=func(*args, **kwargs),
                    status=200,
                    mimetype='text/html;charset=utf-8')
            else:
                return app.response_class(
                    response=func(*args, **kwargs),
                    status=200,
                    mimetype='application/json')

        return wrapper

    return decorator


def _get_parameters(request: Request) -> dict:
    return {k: v for k, v in request.values.items()}


params_parser = module_api_args.init_args(api)


def check_on_unnecessary(request: Request, from_parser: dict) -> List[str]:
    params = _get_parameters(request)
    warning = []
    for param in params.keys():
        if param not in from_parser.keys():
            warning.append("parameter \"{}\" is not supported".format(param))
            logger.warning("parameter \"{}\" is not supported".format(param))

    return warning


@api.route('/upload')
@api.expect(params_parser)
class UploadFile(Resource):
    @api.doc('parsed document', model=ParsedDocument.get_api_dict(api))
    @marshal_with_wrapper(ParsedDocument.get_api_dict(api), request, skip_none=True)
    def post(self) -> str:
        if request.method == 'POST':
            if 'file' not in request.files or request.files['file'] is None or request.files['file'].filename == "":
                raise MissingFileException("Error: Missing content in request_post file parameter",
                                           version=manager.version)
            # check if the post request_post has the file part
            parameters = params_parser.parse_args()
            file = parameters['file']
            del parameters['file']

            logger.info("Get file {} with parameters {}".format(file.filename, parameters))
            warnings = check_on_unnecessary(request, dict(parameters))
            document_tree = manager.parse_file(file, parameters=dict(parameters))
            document_tree.warnings.extend(warnings)
            return_format = str(parameters.get("return_format", "json")).lower()
            if return_format == "html":
                return json2html(text="", paragraph=document_tree.content.structure, tables=document_tree.content.tables, tabs=0)
            elif return_format == "tree":
                return json2tree(paragraph=document_tree.content.structure)
            elif return_format in ("ujson", "json"):
                return ujson.dumps(document_tree.to_dict())
            elif return_format == "collapsed_tree":
                return json2collapsed_tree(paragraph=document_tree.content.structure)
            else:
                logger.info("Send result. File {} with parameters {}".format(file.filename, parameters))
                return json.dumps(document_tree.to_dict(), ensure_ascii=False, indent=2)


@api.route('/static_file')
@api.doc(False)
class SendExampleFile(Resource):
    def get(self) -> Response:
        path = _get_static_file_path()
        as_attachment = request.values.get("as_attachment") == "true"
        return send_file(path, as_attachment=as_attachment)


@api.route('/results_file')
@api.doc(False)
class SendJson(Resource):
    @marshal_with_wrapper(ParsedDocument.get_api_dict(api), request, default_serializer="pretty_json", skip_none=True)
    def get(self) -> ParsedDocument:
        path = _get_static_file_path()
        document_tree = _handle_request(path)
        return document_tree


@api.route('/results_file_html')
@api.doc(False)
class SendHtml(Resource):

    def get(self) -> Response:
        path = _get_static_file_path()
        document_tree = _handle_request(path)
        text_res = json2html("", document_tree.content.structure, document_tree.content.tables, 0)
        return app.response_class(
            response=text_res,
            status=200,
            mimetype='text/html;charset=utf-8')


# ==================== Declare API exceptions =======================

@api.errorhandler(DedocException)
def handle_missing_file_exception(error: DedocException) -> Tuple[dict, int]:
    result = {"message": error.msg_api}
    if error.filename:
        result["file_name"] = error.filename
    if error.version:
        result["dedoc_version"] = error.version
    if error.metadata:
        result["metadata"] = error.metadata
    return result, error.code


version_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "VERSION"))
version = open(version_file_path).read().strip() if os.path.isfile(version_file_path) else importlib.metadata.version("dedoc")
manager = DedocThreadedManager.from_config(config=config, version=version)


# ==================== Utils API functions =======================


def _get_static_file_path() -> str:
    file = request.values["fname"]
    directory_name = request.values.get("directory")
    directory = static_files_dirs[
        directory_name] if directory_name is not None and directory_name in static_files_dirs else static_path
    return os.path.abspath(os.path.join(directory, file))


def _handle_request(path: str) -> ParsedDocument:
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


def run_api(app: Flask) -> None:
    app.run(host='0.0.0.0', port=PORT)

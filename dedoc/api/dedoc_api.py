import importlib
import os

import uvicorn
from fastapi import Response, FastAPI, Request, Depends, UploadFile, File
from fastapi.responses import UJSONResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse

from dedoc.api.api_args import QueryParameters
from dedoc.api.api_utils import json2html, json2tree, json2collapsed_tree
from dedoc.common.exceptions.dedoc_exception import DedocException
from dedoc.common.exceptions.missing_file_exception import MissingFileException
from dedoc.config import get_config
from dedoc.manager.dedoc_thread_manager import DedocThreadedManager

config = get_config()
PORT = config["api_port"]
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static/")
static_files_dirs = config.get("static_files_dirs")

app = FastAPI()
app.mount('/static', StaticFiles(directory=config.get("static_path", static_path)), name="static")

module_api_args = importlib.import_module(config['import_path_init_api_args'])
logger = config["logger"]
version_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "VERSION"))
manager = DedocThreadedManager.from_config(config=config, version=open(version_file_path).read().strip())


@app.get("/")
def get_info() -> Response:
    """
    Root URL '/' is need start with simple Flask before rest-plus. API otherwise you will get 404 Error.
    It is bug of rest-plus lib.
    """
    return FileResponse(os.path.join(static_path, 'html_eng/info.html'))


@app.get('/static_file')
def get_static_file(request: Request) -> Response:
    path = _get_static_file_path(request)
    # TODO check as_attachment
    as_attachment = request.query_params.get("as_attachment") == "true"  # noqa
    return FileResponse(path)


@app.get('/version')
def get_version() -> Response:
    return PlainTextResponse(manager.version)


def _get_static_file_path(request: Request) -> str:
    file = request.query_params.get("fname")
    directory_name = request.query_params.get("directory")
    directory = static_files_dirs[
        directory_name] if directory_name is not None and directory_name in static_files_dirs else static_path
    return os.path.abspath(os.path.join(directory, file))


@app.post('/upload')
async def upload(file: UploadFile = File(...), query_params: QueryParameters = Depends()) -> Response:
    parameters = query_params.dict(by_alias=True)

    if not file or file.filename == "":
        raise MissingFileException("Error: Missing content in request_post file parameter", version=manager.version)
    # check if the post request_post has the file part

    logger.info("Get file {} with parameters {}".format(file.filename, parameters))
    warnings = []
    document_tree = manager.parse_file(file, parameters=dict(parameters))
    document_tree.warnings.extend(warnings)
    return_format = str(parameters.get("return_format", "json")).lower()
    if return_format == "html":
        html_content = json2html(text="", paragraph=document_tree.content.structure, tables=document_tree.content.tables, tabs=0)
        return HTMLResponse(content=html_content, status_code=200)
    elif return_format == "tree":
        html_content = json2tree(paragraph=document_tree.content.structure)
        return HTMLResponse(content=html_content, status_code=200)
    elif return_format == "ujson":
        return UJSONResponse(content=document_tree.to_dict(), status_code=200)
    elif str(parameters.get("return_format", "json")).lower() == "collapsed_tree":
        html_content = json2collapsed_tree(paragraph=document_tree.content.structure)
        return HTMLResponse(content=html_content, status_code=200)
    else:
        logger.info("Send result. File {} with parameters {}".format(file.filename, parameters))
        return ORJSONResponse(content=document_tree.to_dict(), status_code=200)


@app.exception_handler(DedocException)
async def exception_handler(request: Request, exc: DedocException) -> Response:
    result = {"message": exc.msg}
    if exc.filename:
        result["file_name"] = exc.filename
    if exc.version:
        result["dedoc_version"] = exc.version
    if exc.metadata:
        result["metadata"] = exc.metadata
    return JSONResponse(
        status_code=exc.code,
        content=result,
    )


def get_api() -> FastAPI:
    return app


def run_api(app: FastAPI) -> None:
    uvicorn.run(app=app, host="0.0.0.0", port=int(PORT))

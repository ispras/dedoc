import importlib
import os
import tempfile

import uvicorn
from fastapi import Depends, FastAPI, File, Request, Response, UploadFile
from fastapi.responses import ORJSONResponse, UJSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse

import dedoc
from dedoc.api.api_args import QueryParameters
from dedoc.api.api_utils import json2collapsed_tree, json2html, json2tree, json2txt
from dedoc.common.exceptions.dedoc_error import DedocError
from dedoc.common.exceptions.missing_file_error import MissingFileError
from dedoc.config import get_config
from dedoc.dedoc_manager import DedocManager
from dedoc.utils.utils import save_upload_file

config = get_config()
PORT = config["api_port"]
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static/")
static_files_dirs = config.get("static_files_dirs")

app = FastAPI()
app.mount("/static", StaticFiles(directory=config.get("static_path", static_path)), name="static")

module_api_args = importlib.import_module(config["import_path_init_api_args"])
logger = config["logger"]
manager = DedocManager(config=config)


@app.get("/")
def get_info() -> Response:
    """
    Root URL "/" is need start with simple Flask before rest-plus. API otherwise you will get 404 Error.
    It is bug of rest-plus lib.
    """
    return FileResponse(os.path.join(static_path, "html_eng/info.html"))


@app.get("/static_file")
def get_static_file(request: Request) -> Response:
    path = _get_static_file_path(request)
    # TODO check as_attachment
    as_attachment = request.query_params.get("as_attachment") == "true"  # noqa
    return FileResponse(path)


@app.get("/version")
def get_version() -> Response:
    return PlainTextResponse(dedoc.__version__)


def _get_static_file_path(request: Request) -> str:
    file = request.query_params.get("fname")
    directory_name = request.query_params.get("directory")
    directory = static_files_dirs[directory_name] if directory_name is not None and directory_name in static_files_dirs else static_path
    return os.path.abspath(os.path.join(directory, file))


@app.post("/upload")
async def upload(file: UploadFile = File(...), query_params: QueryParameters = Depends()) -> Response:  # noqa
    parameters = query_params.dict(by_alias=True)

    if not file or file.filename == "":
        raise MissingFileError("Error: Missing content in request_post file parameter", version=dedoc.__version__)
    # check if the post request_post has the file part

    logger.info(f"Get file {file.filename} with parameters {parameters}")
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = save_upload_file(file, tmpdir)
        document_tree = manager.parse(file_path, parameters=dict(parameters))

    return_format = str(parameters.get("return_format", "json")).lower()
    if return_format == "html":
        html_content = json2html(text="", paragraph=document_tree.content.structure, tables=document_tree.content.tables, tabs=0)
        return HTMLResponse(content=html_content, status_code=200)
    elif return_format == "plain_text":
        txt_content = json2txt(paragraph=document_tree.content.structure)
        return PlainTextResponse(content=txt_content, status_code=200)
    elif return_format == "tree":
        html_content = json2tree(paragraph=document_tree.content.structure)
        return HTMLResponse(content=html_content, status_code=200)
    elif return_format == "ujson":
        return UJSONResponse(content=document_tree.to_dict(), status_code=200)
    elif str(parameters.get("return_format", "json")).lower() == "collapsed_tree":
        html_content = json2collapsed_tree(paragraph=document_tree.content.structure)
        return HTMLResponse(content=html_content, status_code=200)
    else:
        logger.info(f"Send result. File {file.filename} with parameters {parameters}")
        return ORJSONResponse(content=document_tree.to_dict(), status_code=200)


@app.exception_handler(DedocError)
async def exception_handler(request: Request, exc: DedocError) -> Response:
    result = {"message": exc.msg}
    if exc.filename:
        result["file_name"] = exc.filename
    if exc.version:
        result["dedoc_version"] = exc.version
    if exc.metadata:
        result["metadata"] = exc.metadata
    return JSONResponse(status_code=exc.code, content=result)


def get_api() -> FastAPI:
    return app


def run_api(app: FastAPI) -> None:
    uvicorn.run(app=app, host="0.0.0.0", port=int(PORT))

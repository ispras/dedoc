import logging
import os
import shutil

import uvicorn
from fastapi import FastAPI, Response, Request, UploadFile, File, Depends
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, HTMLResponse
from starlette.templating import Jinja2Templates

from dedoc.api.dedoc_api import _get_static_file_path
from dedoc.api.train_dataset.api_args import TrainDatasetParameters
from dedoc.api.train_dataset.async_archive_handler import AsyncHandler
from dedoc.config import get_config
from dedoc.manager.dedoc_thread_manager import DedocThreadedManager
from dedoc.train_dataset.taskers.concrete_taskers.filtered_line_label_tasker import FilteredLineLabelTasker
from dedoc.train_dataset.taskers.concrete_taskers.header_footer_tasker import HeaderFooterTasker
from dedoc.train_dataset.taskers.concrete_taskers.line_label_tasker import LineLabelTasker
from dedoc.train_dataset.taskers.concrete_taskers.table_tasker import TableTasker
from dedoc.train_dataset.taskers.tasker import Tasker
from dedoc.train_dataset.train_dataset_utils import get_path_original_documents
from dedoc.utils.utils import calculate_file_hash

config = get_config()
PORT = config["api_port"]

static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
static_files_dirs = config.get("static_files_dirs")

logger = config.get("logger", logging.getLogger())

app = FastAPI()
app.mount('/static', StaticFiles(directory=static_path), name="static")
templates = Jinja2Templates(directory=os.path.join(static_path, "train_dataset"))

version_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "VERSION"))
manager = DedocThreadedManager.from_config(config=config, version=open(version_file_path).read().strip())


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
UPLOAD_FOLDER = os.path.join(config["resources_path"], "tasks")
train_resources_path = os.path.join(project_root, "resources", "train_dataset")

path2lines = os.path.join(config["intermediate_data_path"], "lines.jsonlines")
boxes_path = os.path.join(config["intermediate_data_path"], "bboxes.jsonlines")
progress_bar = {}

label2label_law = {
    "part": "item",
    "section": "item",
    "subsection": "item",
    "chapter": "item",
    "paragraph": "item",
    "article": "item",
    "articlePart": "item",
    "item": "item",
    "subitem": "item",
    "cellar": "cellar",
    "application": "application",
    "root": "title"
}
label2label_tz = {
    "root": "title",
    "toc": "toc",
    "toc_item": "toc",
    "item": "item",
    "part": "part",
    "raw_text": "raw_text"
}
label2label_diploma = {
    "root": "title",
    "toc": "toc",
    "toc_item": "toc",
    "item": "raw_text",
    "part": "named_item",
    "raw_text": "raw_text"
}

taskers = {
    "law_classifier": LineLabelTasker(
        path2bboxes=boxes_path,
        path2lines=path2lines,
        path2docs=get_path_original_documents(config),
        manifest_path=os.path.join(train_resources_path, "law", "manifest.pdf"),
        config_path=os.path.join(train_resources_path, "law", "config.json"),
        tmp_dir=UPLOAD_FOLDER,
        progress_bar=progress_bar,
        item2label=lambda t: label2label_law.get(t['_metadata']['hierarchy_level']['line_type'], "raw_text"),
        config=config),
    "paragraph_classifier": LineLabelTasker(
        path2bboxes=boxes_path,
        path2lines=path2lines,
        path2docs=get_path_original_documents(config),
        manifest_path=os.path.join(train_resources_path, "paragraph", "manifest.pdf"),
        config_path=os.path.join(train_resources_path, "paragraph", "config.json"),
        tmp_dir=UPLOAD_FOLDER,
        progress_bar=progress_bar,
        item2label=lambda t: "not_paragraph",
        config=config),
    "tz_classifier": LineLabelTasker(
        path2bboxes=boxes_path,
        path2lines=path2lines,
        path2docs=get_path_original_documents(config),
        manifest_path=os.path.join(train_resources_path, "tz", "manifest.pdf"),
        config_path=os.path.join(train_resources_path, "tz", "config.json"),
        tmp_dir=UPLOAD_FOLDER,
        progress_bar=progress_bar,
        item2label=lambda t: label2label_tz.get(t['_metadata']['hierarchy_level']['line_type'], "raw_text"),
        config=config),
    "diploma_classifier": FilteredLineLabelTasker(
        path2bboxes=boxes_path,
        path2lines=path2lines,
        path2docs=get_path_original_documents(config),
        manifest_path=os.path.join(train_resources_path, "diploma", "manifest.pdf"),
        config_path=os.path.join(train_resources_path, "diploma", "config.json"),
        tmp_dir=UPLOAD_FOLDER,
        progress_bar=progress_bar,
        item2label=lambda t: label2label_diploma.get(t['_metadata']['hierarchy_level']['line_type'], "raw_text"),
        config=config),
    "header_classifier": HeaderFooterTasker(
        path2bboxes=boxes_path,
        path2lines=path2lines,
        path2docs=get_path_original_documents(config),
        manifest_path=os.path.join(train_resources_path, "header", "manifest.pdf"),
        config_path=os.path.join(train_resources_path, "header", "config.json"),
        tmp_dir=UPLOAD_FOLDER,
        progress_bar=progress_bar,
        item2label=lambda t: "text",
        config=config),
    "tables_classifier": TableTasker()
}

tasker = Tasker(boxes_label_path=os.path.join(config["intermediate_data_path"], "bboxes.jsonlines"),
                line_info_path=os.path.join(config["intermediate_data_path"], "lines.jsonlines"),
                images_path=get_path_original_documents(config),
                save_path=UPLOAD_FOLDER,
                concrete_taskers=taskers,
                progress_bar=progress_bar,
                config=config)
handler = AsyncHandler(tasker=tasker, manager=manager, config=config)


@app.get('/')
def get_info() -> Response:
    """
    Returns the main page for the labeling mode.
    """
    return FileResponse(os.path.join(static_path, 'train_dataset/info_labeling_mode.html'))


@app.get("/handle_archive")
def handle_archive() -> Response:
    """
    Returns the page for running the whole pipeline of task making.
    """
    return FileResponse(os.path.join(static_path, 'train_dataset/form_input_archive.html'))


@app.post('/upload_archive')
def upload_archive(file: UploadFile = File(...), query_params: TrainDatasetParameters = Depends()) -> Response:
    """
    Run the whole pipeline of task making.
    """
    clear()
    parameters = query_params.dict(by_alias=True)
    uid = handler.handle(file=file, parameters=parameters)
    return HTMLResponse(
        f'Successfully handle file. UID=<p><a href="/get_result_archive/?uid={uid}">get_result_archive/?uid={uid}</a></p>',
        status_code=201
    )


@app.get('/get_result_archive')
def get_result_archive(request: Request, uid: str) -> Response:
    """
    Get the archive with the result tasks.
    """
    if handler.is_ready(uid):
        path = handler.get_results(uid)
        file = os.path.basename(path)
        path_out = os.path.join(UPLOAD_FOLDER, file)
        shutil.move(handler.get_results(uid), path_out)
        hash_sum = calculate_file_hash(path=path_out)
        logger.info("md5sum {}".format(hash_sum))
        return templates.TemplateResponse("download.html", dict(request=request, value=file, cnt_per_one=1, hash_sum=hash_sum, filename=file))
    else:
        response = "<h2>Ещё не готово</h2>"
        for line in handler.get_progress(uid).split("\n"):
            response += "<p> {} </p>".format(line)
        return HTMLResponse(response, status_code=202)


@app.get('/info_classifiers')
def get_classifiers_info() -> Response:
    return FileResponse(os.path.join(static_path, "train_dataset/refit_classifier.html"))


@app.get('/static_file')
def get_static_file(request: Request) -> Response:
    path = _get_static_file_path(request)
    return FileResponse(path)


@app.get('/return-file/{filename}')
def return_files(filename: str) -> Response:
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    return FileResponse(file_path)


@app.get('/clear')
def clear() -> Response:
    shutil.rmtree(config["intermediate_data_path"])
    os.makedirs(config["intermediate_data_path"])
    shutil.rmtree(UPLOAD_FOLDER)
    os.makedirs(UPLOAD_FOLDER)
    return HTMLResponse("<h2>Successfully clear files</h2>", status_code=201)


def run_special_api() -> None:
    uvicorn.run(app=app, host="0.0.0.0", port=int(PORT))

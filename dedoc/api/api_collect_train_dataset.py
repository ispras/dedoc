import logging
import os
import shutil
from typing import Union

from dedoc.common.exceptions.bad_file_exception import BadFileFormatException
from dedoc.common.exceptions.conversion_exception import ConversionException
from dedoc.config import Configuration
from dedoc.manager.dedoc_thread_manager import DedocThreadedManager
from flask import Flask, request, render_template, send_file, Response

from dedoc.train_dataset.train_dataset_utils import get_path_original_documents
from dedoc.utils.utils import calculate_file_hash
from dedoc.api.async_archive_handler import AsyncHandler
from dedoc.train_dataset.taskers.concrete_taskers.filtered_line_label_tasker import FilteredLineLabelTasker
from dedoc.train_dataset.taskers.concrete_taskers.header_footer_tasker import HeaderFooterTasker
from dedoc.train_dataset.taskers.concrete_taskers.line_label_tasker import LineLabelTasker
from dedoc.train_dataset.taskers.concrete_taskers.table_tasker import TableTasker
from dedoc.train_dataset.taskers.tasker import Tasker

config = Configuration.getInstance().getConfig()

logger = config.get("logger", logging.getLogger())
PORT = config["api_port"]

docs_path = os.path.join(os.path.dirname(__file__), "..", "..", "online_docs")
docs_path = os.path.abspath(docs_path)

app = Flask(__name__, static_folder=docs_path, template_folder=docs_path)

version_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "VERSION"))
manager = DedocThreadedManager.from_config(config=config, version=open(version_file_path).read().strip())

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOAD_FOLDER = "/tmp/tasks"

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
        manifest_path=os.path.join(project_root, "resources/train_dataset/law/manifest.pdf"),
        config_path=os.path.join(project_root, "resources/train_dataset/law/config.json"),
        tmp_dir=UPLOAD_FOLDER,
        progress_bar=progress_bar,
        item2label=lambda t: label2label_law.get(t['_metadata']['hierarchy_level']['line_type'], "raw_text"),
        config=config),
    "paragraph_classifier": LineLabelTasker(
        path2bboxes=boxes_path,
        path2lines=path2lines,
        path2docs=get_path_original_documents(config),
        manifest_path=os.path.join(project_root, "resources/train_dataset/paragraph/manifest.pdf"),
        config_path=os.path.join(project_root, "resources/train_dataset/paragraph/config.json"),
        tmp_dir=UPLOAD_FOLDER,
        progress_bar=progress_bar,
        item2label=lambda t: "not_paragraph",
        config=config),
    "tz_classifier": LineLabelTasker(
        path2bboxes=boxes_path,
        path2lines=path2lines,
        path2docs=get_path_original_documents(config),
        manifest_path=os.path.join(project_root, "resources/train_dataset/tz/manifest.pdf"),
        config_path=os.path.join(project_root, "resources/train_dataset/tz/config.json"),
        tmp_dir=UPLOAD_FOLDER,
        progress_bar=progress_bar,
        item2label=lambda t: label2label_tz.get(t['_metadata']['hierarchy_level']['line_type'], "raw_text"),
        config=config),
    "diploma_classifier": FilteredLineLabelTasker(
        path2bboxes=boxes_path,
        path2lines=path2lines,
        path2docs=get_path_original_documents(config),
        manifest_path=os.path.join(project_root, "resources/train_dataset/diploma/manifest.pdf"),
        config_path=os.path.join(project_root, "resources/train_dataset/diploma/config.json"),
        tmp_dir=UPLOAD_FOLDER,
        progress_bar=progress_bar,
        item2label=lambda t: label2label_diploma.get(t['_metadata']['hierarchy_level']['line_type'], "raw_text"),
        config=config),
    "header_classifier": HeaderFooterTasker(
        path2bboxes=boxes_path,
        path2lines=path2lines,
        path2docs=get_path_original_documents(config),
        manifest_path=os.path.join(project_root, "resources/train_dataset/header/manifest.pdf"),
        config_path=os.path.join(project_root, "resources/train_dataset/header/config.json"),
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


@app.route('/handle_archive', methods=['GET'])
def handle_archive() -> Response:
    path = "form_input_archive.html"
    return app.send_static_file(filename=path)


@app.route('/get_result_archive/', methods=['GET'])
def get_result_archive() -> Response:
    uid = request.args.get("uid")
    if handler.is_ready(uid):
        path = handler.get_results(uid)
        file = os.path.basename(path)
        path_out = os.path.join(UPLOAD_FOLDER, file)
        shutil.move(handler.get_results(uid), path_out)
        hash_sum = calculate_file_hash(path=path_out)
        logger.info("md5sum {}".format(hash_sum))
        return render_template('download.html', value=file, cnt_per_one=1, hash_sum=hash_sum, filename=file)
    else:
        response = "<h2>Ещё не готово</h2>"
        for line in handler.get_progress(uid).split("\n"):
            response += "<p> {} </p>".format(line)
        return app.response_class(
            response=response,
            status=202
        )


@app.route('/upload_archive', methods=['POST'])
def upload_archive() -> Response:
    clear()
    file = request.files['file']
    parameters = {k: v for k, v in request.values.items()}
    uid = handler.handle(file=file, parameters=parameters)
    # _ = manager.parse_file(file, parameters=parameters)
    return app.response_class(
        response='Successfully handle file. UID=<p><a href="/get_result_archive/?uid={uid}">get_result_archive/'
                 '?uid={uid}</a></p>'  # noqa
                 "".format(uid=uid),
        status=201
    )


@app.route('/', methods=['GET'])
def get_info() -> Response:
    path = "info_labeling_mode.html"
    return app.send_static_file(filename=path)


@app.route('/upload', methods=['GET'])
def get_upload_form() -> Response:
    path = "form_input.html"
    return app.send_static_file(filename=path)


@app.route('/create_tasks', methods=['GET'])
def get_created_tasks() -> Response:
    path = "creating_tasks_for_labeling.html"
    return app.send_static_file(filename=path)


@app.route('/info_classifiers', methods=['GET'])
def get_classifiers_info() -> Response:
    path = "refit_classifier.html"
    return app.send_static_file(filename=path)


@app.route('/icon', methods=['GET'])
def get_icon() -> Response:
    path = "law_example.png"
    return app.send_static_file(path)


@app.route('/style', methods=['GET'])
def get_css() -> Response:
    path = "styles.css"
    return app.send_static_file(path)


@app.route('/return-file/<filename>', methods=['GET'])
def return_files_tut(filename: str) -> Response:
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(file_path, as_attachment=True, attachment_filename='')


@app.route('/wget-file/<filename>', methods=['GET'])
def return_files_wget(filename: str) -> Response:
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(file_path, as_attachment=False, attachment_filename=filename)


@app.route('/clear', methods=['GET'])
def clear() -> Response:
    shutil.rmtree(config["intermediate_data_path"])
    os.makedirs(config["intermediate_data_path"])
    shutil.rmtree(UPLOAD_FOLDER)
    os.makedirs(UPLOAD_FOLDER)
    return app.response_class(
        response="Successfully clear files",
        status=201
    )


@app.route('/upload', methods=['POST'])
def upload_file() -> Response:
    if request.method == 'POST':
        try:
            # check if the post request has the file part
            file = request.files['file']

            parameters = {k: v for k, v in request.values.items()}
            _ = manager.parse_file(file, parameters=parameters)
            return app.response_class(
                response="Successfully handle file {}".format(file.filename),
                status=201
            )

        except (BadFileFormatException, ConversionException) as err:
            print(err)  # noqa
            file = request.files['file']
            return app.response_class(response="Unsupported file format for {}".format(file.filename), status=415)
        except Exception as e:
            print("exception on file {}".format(file))  # noqa
            print(e)  # noqa
            raise e

    return app.send_static_file("form_input.html")


@app.route('/create_tasks', methods=['POST'])
def create_tasks() -> Union[str, Response]:
    if request.method == 'POST':
        try:
            parameters = {k: v for k, v in request.values.items()}
            res_pathname, cnt_per_one = tasker.create_tasks(type_of_task=parameters.get("classifier_type"),
                                                            count_tasks=int(parameters.get("count_tasks")))
            file_name = os.path.split(res_pathname)[-1]
            if parameters.get("automated_mode", "false").lower() == "true":
                return "/return-file/{}".format(file_name)
            hash_sum = calculate_file_hash(path=res_pathname)
            logger.info("md5sum {}".format(hash_sum))
            return render_template('download.html', value=file_name, cnt_per_one=cnt_per_one, hash_sum=hash_sum)

        except Exception as e:
            print(e)  # noqa
            raise e


def run_special_api() -> None:
    app.run(host="0.0.0.0", port=1231)

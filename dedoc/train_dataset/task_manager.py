import json
import os
import shutil
import time
import zipfile
from tempfile import TemporaryDirectory
from typing import Dict, Union

from flask import Flask, request, send_file, Response

app = Flask(__name__, static_folder=os.path.dirname(__file__))

tasks = sorted([task for task in os.listdir(".") if task.endswith("zip") and task.startswith("task_")])
results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "results"))
os.makedirs(results_dir, exist_ok=True)

with open("formInput.html") as file:
    form_input = file.read()

with open("formResult.html") as file:
    form_results = file.read()


@app.route('/', methods=['GET'])
def get_info() -> str:
    if len(tasks) > 0:
        return form_input.format(tasks_left=len(tasks))
    else:
        return """<h1 style="color: #5e9ca0;">Размечать нечего</h1>
        <h2> <a href="get_results">Получить результаты</a> </h2>"""


@app.route('/upload', methods=['POST'])
def upload() -> Union[str, Response]:
    parameters = {k: v for k, v in request.values.items()}
    name = parameters.get("name", "Инкогнито")
    if len(tasks) == 0:
        return '<h1 style="color: #5e9ca0;">Размечать нечего</h1>'
    else:
        task = tasks.pop()
        with open("task_manager.log", "a") as file_log:
            file_log.write("{} take task {}\n".format(name, task))
        return send_file(task, as_attachment=True, attachment_filename=task)


@app.route('/upload_results', methods=['POST', "GET"])
def upload_results() -> Response:
    if request.method == "POST":
        file = request.files['file']
        with TemporaryDirectory() as tmp_dir:
            name = file.filename
            path_out = os.path.join(tmp_dir, name)
            file.save(path_out)
            if name.endswith(".json"):
                cnt = ""
                _save_result_file(path_out, name)
            elif name.endswith(".zip"):
                with zipfile.ZipFile(path_out) as archive:
                    name_list = archive.namelist()
                    cnt = len(name_list)
                    for file_name in name_list:
                        path_out = os.path.join(tmp_dir, file_name)
                        archive.extract(member=file_name, path=tmp_dir)
                        _save_result_file(path_out, file_name)
        return '<h1> Результат получен {} </h1>'.format(cnt)
    if request.method == "GET":
        return form_results


def _save_result_file(path: str, name: str) -> None:
    path_out = os.path.abspath(os.path.join(results_dir, name))
    shutil.copy(path, path_out)
    with open("task_manager.log", "a") as file_log:
        file_log.write("save file in {}\n".format(path_out))


@app.route('/get_results', methods=["GET"])
def get_results() -> Response:
    with TemporaryDirectory() as tmp_dir:
        archive_name = "results_{}.zip".format(int(time.time()))
        archive_path = os.path.join(tmp_dir, archive_name)
        with zipfile.ZipFile(archive_path, "w") as archive:
            labeled = _merge_labeled()
            archive.writestr("labeled.json", json.dumps(labeled, indent=4, ensure_ascii=False).encode("utf-8"))
            original_documents_set = {os.path.basename(d["data"]["original_document"]) for d in labeled.values()}

            with zipfile.ZipFile("original_documents.zip") as original_documents:
                files = [file for file in original_documents.namelist() if file in original_documents_set]
                for file in files:
                    with original_documents.open(file) as f_in:
                        archive.writestr("original_documents/{}".format(file), f_in.read())

            archive.write("task_manager.log")
        return send_file(archive_path, as_attachment=True, attachment_filename=archive_name)


def _merge_labeled() -> Dict[str, dict]:
    labeled = {}
    task_id = 0
    for file in os.listdir(results_dir):
        with open(os.path.join(results_dir, file)) as task_file:
            tasks = json.load(task_file)
        for task in tasks.values():
            task["id"] = task_id
            labeled[str(task_id)] = task
            task_id += 1
    return labeled


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000)

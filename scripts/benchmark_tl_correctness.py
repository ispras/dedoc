import json
import os
import zipfile
from collections import OrderedDict, namedtuple
from time import time

import numpy as np
import requests
import wget
from Cryptodome.Random.random import shuffle
from sklearn.metrics import accuracy_score, balanced_accuracy_score, precision_recall_fscore_support
from tqdm import tqdm

from dedoc.config import get_config
from dedoc.utils.utils import send_file

path_result = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources", "benchmarks"))
os.makedirs(path_result, exist_ok=True)
path_result = os.path.join(path_result, "benchmarks_tl_correctness.txt")

"""
Experiments are available -> https://github.com/alexander1999-hub/txt_layer_correctness/tree/main :
    * generating synthetic incorrect text
    * compare different classification models
    * compare different input textual feature: TF-IDF and custom features
    * compare on real data of correct/incorrect texts with GT using Levenstein (available on Confluence -> dataset page)
Here (in this script) we calculate an accuracy of selected model (XGboost on custom features) on real data without GT. Data are pdfs with textual layer)
"""

host = "http://localhost:1231"
param_dist_errors = namedtuple("Param", ("total_file_size", "total_incorrect_files", "failed"))


def send_request_mineru(file_path: str, url: str) -> dict:
    """
    send file `file_name` in post request with `data` as parameters. Expects that response return code
    `expected_code`

    :param file_name: name of file (should lie  src/tests/data folder
    :param data: parameter dictionary (here you can put language for example)
    :param expected_code: expected http response code. 200 for normal request
    :return: result from json
    """
    data = {"parse_method": "auto", "is_json_md_dump": True}
    file_name = file_path.split("/")[-1]

    with open(file_path, "rb") as file:
        files = {"pdf_file": (file_name, file)}
        r = requests.post(url, files=files, data=data)

        if r.status_code != 200:
            return r.content.decode()
        else:
            return json.loads(r.content.decode())


def errors_param_for_text_layer(path_base: str, tl_type: str, tl_path: str, parameters: dict) -> namedtuple:
    failed = []
    total_incorrect_files = 0
    directory = os.path.join(path_base, tl_path)
    files_list = [file_name for file_name in os.listdir(directory) if file_name.endswith(".pdf")]
    total_file_size = len(files_list)
    print(f"Files: {files_list}\nFiles number: {total_file_size}")
    for file in tqdm(files_list):
        file_path = os.path.join(directory, file)
        r = send_file(host=host, file_name=file, file_path=file_path, parameters=parameters)

        found = False  # found error of classifier
        for warning in r["warnings"]:
            if warning.find(tl_type) != -1:
                found = True
                break

        if found:
            total_incorrect_files += 1  # count, where label != predict
            failed.append(file)         # file, where classifier failed
    return param_dist_errors(total_file_size, total_incorrect_files, failed)


def download_dataset(data_dir: str) -> str:
    benchmark_data_dir = os.path.join(data_dir, "data_with_text_layer")
    if not os.path.isdir(benchmark_data_dir):
        path_out = os.path.join(data_dir, "data_with_text_layer.zip")
        wget.download("https://at.ispras.ru/owncloud/index.php/s/axacSYXf7YCLcbb/download", path_out)
        with zipfile.ZipFile(path_out, "r") as zip_ref:
            zip_ref.extractall(data_dir)
        os.remove(path_out)
        print(f"Benchmark data downloaded to {benchmark_data_dir}")
    else:
        print(f"Use cached benchmark data from {benchmark_data_dir}")

    assert os.path.isdir(benchmark_data_dir)

    return benchmark_data_dir


def evaluation_dedoc() -> None:
    data_dir = os.path.join(get_config()["intermediate_data_path"], "text_layer_correctness_data")
    os.makedirs(data_dir, exist_ok=True)

    benchmark_data_dir = download_dataset(data_dir)

    result = OrderedDict()
    result["version"] = requests.get(f"{host}/version").text
    parameters = dict(pdf_with_text_layer="auto", pages="1:1")
    result_item = OrderedDict()

    incorrect_tl_result = errors_param_for_text_layer(benchmark_data_dir, " incorrect ", "data_correct_text_layer", parameters)
    result_item["percentage_of_guessed_correct_tl"] = 1 - incorrect_tl_result.total_incorrect_files / incorrect_tl_result.total_file_size
    result_item["list_of_file_with_incorrect_tl"] = incorrect_tl_result.failed

    correct_tl_result = errors_param_for_text_layer(benchmark_data_dir, " correct ", "data_incorrect_text_layer", parameters)
    result_item["percentage_of_guessed_incorrect_tl"] = 1 - correct_tl_result.total_incorrect_files / correct_tl_result.total_file_size
    result_item["list_of_file_with_correct_tl"] = correct_tl_result.failed
    result["guessing_the_correctness_of_the_text"] = result_item

    with open(path_result, "w") as file_out:
        json.dump(obj=result, fp=file_out, indent=4, ensure_ascii=False)
    print(f"Save result in {path_result}")


def get_metrics(max_eval_pdf: int = 10000, with_shuffle: bool = False) -> None:
    data_dir = os.path.join(get_config()["intermediate_data_path"], "text_layer_correctness_data")
    os.makedirs(data_dir, exist_ok=True)

    data_dir = download_dataset(data_dir)

    folder = os.path.join(data_dir, "data_correct_text_layer")
    correct_files = np.array([os.path.join(folder, file_name) for file_name in os.listdir(folder) if file_name.endswith(".pdf")])
    folder = os.path.join(data_dir, "data_incorrect_text_layer")
    incorrect_files = np.array([os.path.join(folder, file_name) for file_name in os.listdir(folder) if file_name.endswith(".pdf")])

    files = np.append(correct_files, incorrect_files)

    labels = np.empty(files.size)
    labels[:correct_files.size] = 0  # "correct"
    labels[correct_files.size:] = 1  # "incorrect"

    failed_corrected_pdfs = []
    failed_incorrected_pdfs = []

    # run pipeline for prediction
    predicts = np.empty(files.size)
    parameters = dict(pdf_with_text_layer="auto", pages="1:1")
    times_correct, times_incorrect = [], []

    if with_shuffle:
        shuffle(files)
    count = min(max_eval_pdf, len(files))

    for i, file_path in enumerate(tqdm(files[:count])):
        file_name = file_path.split("/")[-1]

        time_b = time()
        r = send_file(host=host, file_name=file_name, file_path=file_path, parameters=parameters)
        time_eval = time() - time_b

        if labels[i] == 0:
            times_correct.append(time_eval)
        else:
            times_incorrect.append(time_eval)

        predicts[i] = 3  # "failed" not handling
        for warning in r["warnings"]:
            if "has incorrect textual layer" in warning:
                predicts[i] = 1  # "incorrect"
            if "has a correct textual layer" in warning:
                predicts[i] = 0  # "correct"

        if predicts[i] != labels[i]:
            failed_corrected_pdfs.append(file_name) if labels[i] == 0 else failed_incorrected_pdfs.append(file_name)

    labels, predicts = labels[:count], predicts[:count]

    b_accuracy = balanced_accuracy_score(labels, predicts)
    accuracy = accuracy_score(labels, predicts)
    w_avg = precision_recall_fscore_support(labels, predicts, average="weighted")
    avg = precision_recall_fscore_support(labels, predicts, average=None, labels=[0, 1])

    output = f"--- Balanced Accuracy --- = {b_accuracy}\n"
    output += f"--- Accuracy --- = {accuracy}\n"
    output += f"--- Weighted --- Precision = {w_avg[0]}, Recall={w_avg[1]}, F1={w_avg[2]}\n"
    output += f"--- Class corrected --- : Precision = {avg[0][0]}, Recall={avg[1][0]}, F1={avg[2][0]}\n"
    output += f"--- Class incorrected --- : Precision = {avg[0][1]}, Recall={avg[1][1]}, F1={avg[2][1]}\n"

    output += f"--- AVG Time corrected pdfs --- = {np.array(times_correct).mean()}\n"
    output += f"--- AVG Time incorrected pdfs --- = {np.array(times_incorrect).mean()}\n"
    output += f"--- AVG Time all pdfs --- = {np.array(times_correct + times_incorrect).mean()}\n"

    output += "--- Failed corrected pdfs --- : \n" + '\n'.join(failed_corrected_pdfs)  # noqa
    output += "--- Failed incorrected pdfs --- : \n" + '\n'.join(failed_incorrected_pdfs)  # noqa

    print(output)
    with open(path_result, "w") as file_out:
        file_out.write(output)
    print(f"Save result in {path_result}")


if __name__ == "__main__":
    # evaluation_dedoc()
    get_metrics(max_eval_pdf=50, with_shuffle=True)

import os
import zipfile
from time import time

import numpy as np
import requests
import wget
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


def get_metrics(max_eval_pdf: int = 10000) -> None:
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

    output = f"Version = {requests.get(host + '/version').text}\n\n"

    output += f"--- Balanced Accuracy --- = {b_accuracy}\n"
    output += f"--- Accuracy --- = {accuracy}\n"
    output += f"--- Weighted --- Precision = {w_avg[0]}, Recall={w_avg[1]}, F1={w_avg[2]}\n"
    output += f"--- Class corrected --- : Precision = {avg[0][0]}, Recall={avg[1][0]}, F1={avg[2][0]}\n"
    output += f"--- Class incorrected --- : Precision = {avg[0][1]}, Recall={avg[1][1]}, F1={avg[2][1]}\n"

    output += f"--- AVG Time corrected pdfs --- = {np.mean(times_correct)}\n"
    output += f"--- AVG Time incorrected pdfs --- = {np.mean(times_incorrect)}\n"
    output += f"--- AVG Time all pdfs --- = {np.mean(times_correct + times_incorrect)}\n"

    output += "\n\n--- Failed corrected pdfs --- : \n" + '\n'.join(failed_corrected_pdfs)  # noqa
    output += "\n\n--- Failed incorrected pdfs --- : \n" + '\n'.join(failed_incorrected_pdfs)  # noqa

    print(output)
    with open(path_result, "w") as file_out:
        file_out.write(output)
    print(f"Save result in {path_result}")


if __name__ == "__main__":
    get_metrics()

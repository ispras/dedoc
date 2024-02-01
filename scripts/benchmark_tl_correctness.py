import json
import os
import zipfile
from collections import OrderedDict, namedtuple

import requests
import wget
from tqdm import tqdm

from dedoc.config import get_config
from dedoc.utils.utils import send_file

path_result = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources", "benchmarks"))
os.makedirs(path_result, exist_ok=True)
path_result = os.path.join(path_result, "benchmarks_tl_correctness.json")

host = "http://localhost:1231"
param_dist_errors = namedtuple("Param", ("total_file_size", "total_incorrect_files", "failed"))


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

        found = False
        for warning in r["warnings"]:
            if warning.find(tl_type) != -1:
                found = True
                break

        if found:
            total_incorrect_files += 1
            failed.append(file)
    return param_dist_errors(total_file_size, total_incorrect_files, failed)


if __name__ == "__main__":
    data_dir = os.path.join(get_config()["intermediate_data_path"], "text_layer_correctness_data")
    os.makedirs(data_dir, exist_ok=True)
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

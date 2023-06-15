import json
import os
import zipfile
from collections import OrderedDict, namedtuple
from tempfile import TemporaryDirectory

import requests
import wget
from tqdm import tqdm

from dedoc.utils.utils import send_file

path_result = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "benchmarks")
path_result = os.path.abspath(path_result)
os.makedirs(path_result, exist_ok=True)
path_result = os.path.join(path_result, "benchmarks_tl_correctness.json")

host = "http://localhost:1231"
param_dist_errors = namedtuple('Param', ('total_file_size', 'total_incorrect_files', 'failed'))


def errors_param_for_text_layer(path_base: str, tl_type: str, tl_path: str, parameters: dict) -> namedtuple:
    failed = []
    total_incorrect_files = 0
    directory = os.path.join(path_base, tl_path)
    files_list = os.listdir(directory)
    total_file_size = len(files_list)
    print(files_list)
    print(total_file_size)
    for file in tqdm(files_list):
        file_path = os.path.join(directory, file)
        r = send_file(host=host, file_name=file, file_path=file_path, parameters=parameters)
        if r["warnings"][-1].find(tl_type) != -1:
            total_incorrect_files += 1
            failed.append(file)
    return param_dist_errors(total_file_size, total_incorrect_files, failed)


def main() -> None:
    with TemporaryDirectory() as path_base:
        path_out = os.path.join(path_base, "data_with_text_layer.zip")
        wget.download("https://at.ispras.ru/owncloud/index.php/s/BvABW6mx9wKWqPp/download", path_out)
        with zipfile.ZipFile(path_out, 'r') as zip_ref:
            zip_ref.extractall(path_base)
        directory = os.path.join(path_base, 'data_with_text_layer')
        print(directory)
        result = OrderedDict()
        result["version"] = requests.get("{}/version".format(host)).text
        parameters = dict(pdf_with_text_layer="auto", pages="0:1")
        result_item = OrderedDict()
        incorrect_tl_result = errors_param_for_text_layer(directory, 'incorrect', 'data_correct_text_layer',
                                                          parameters)
        result_item["percentage_of_guessed_correct_tl"] = 1 - incorrect_tl_result.total_incorrect_files / \
            incorrect_tl_result.total_file_size
        result_item["list_of_file_with_incorrect_tl"] = incorrect_tl_result.failed
        correct_tl_result = errors_param_for_text_layer(directory, 'correct', 'data_incorrect_text_layer',
                                                        parameters)
        result_item["percentage_of_guessed_incorrect_tl"] = 1 - correct_tl_result.total_incorrect_files / \
            correct_tl_result.total_file_size
        result_item["list_of_file_with_correct_tl"] = correct_tl_result.failed
        result["guessing_the_correctness_of_the_text"] = result_item

        with open(path_result, "w") as file_out:
            json.dump(obj=result, fp=file_out, indent=4, ensure_ascii=False)
        print("save result in" + path_result)


main()

import json
import os
import zipfile
from collections import OrderedDict, namedtuple
from tempfile import TemporaryDirectory

import requests
import wget
from tqdm import tqdm

from dedoc.utils.utils import send_file

path_result = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "benchmarks"))
os.makedirs(path_result, exist_ok=True)
path_result = os.path.join(path_result, "benchmarks_tl_correctness.json")

host = "http://localhost:1231"
param_dist_errors = namedtuple('Param', ('total_file_size', 'total_incorrect_files', 'failed'))


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
    # with TemporaryDirectory() as path_base:
    #     path_out = os.path.join(path_base, "data_with_text_layer.zip")
    #     wget.download("https://at.ispras.ru/owncloud/index.php/s/BvABW6mx9wKWqPp/download", path_out)
    #     with zipfile.ZipFile(path_out, 'r') as zip_ref:
    #         zip_ref.extractall(path_base)
    directory = os.path.join("train", 'data_with_text_layer')

    result = OrderedDict()
    result["version"] = requests.get(f"{host}/version").text
    parameters = dict(pdf_with_text_layer="auto", pages="1:1")
    result_item = OrderedDict()

    incorrect_tl_result = errors_param_for_text_layer(directory, ' incorrect ', 'data_correct_text_layer', parameters)
    result_item["percentage_of_guessed_correct_tl"] = 1 - incorrect_tl_result.total_incorrect_files / incorrect_tl_result.total_file_size
    result_item["list_of_file_with_incorrect_tl"] = incorrect_tl_result.failed

    correct_tl_result = errors_param_for_text_layer(directory, ' correct ', 'data_incorrect_text_layer', parameters)
    result_item["percentage_of_guessed_incorrect_tl"] = 1 - correct_tl_result.total_incorrect_files / correct_tl_result.total_file_size
    result_item["list_of_file_with_correct_tl"] = correct_tl_result.failed
    result["guessing_the_correctness_of_the_text"] = result_item

    with open(path_result, "w") as file_out:
        json.dump(obj=result, fp=file_out, indent=4, ensure_ascii=False)
    print("save result in" + path_result)

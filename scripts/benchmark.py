import os
import time
import zipfile
from collections import OrderedDict, namedtuple
from tempfile import TemporaryDirectory
from typing import List

import numpy as np
import requests
import wget
from texttable import Texttable
from tqdm import tqdm

from dedoc.readers.pdf_reader.pdf_txtlayer_reader.pdfminer_reader.pdfminer_extractor import PdfminerExtractor
from dedoc.utils.utils import send_file

path_result = os.path.join(os.path.dirname(__file__), "..", "resources", "benchmarks")
path_result = os.path.abspath(path_result)
os.makedirs(path_result, exist_ok=True)
path_result = os.path.join(path_result, "time_benchmark.txt")

Task = namedtuple("Task", ("directory", "name", "parameters", "func_page_count"))

host = "http://localhost:1231"
data_url = "https://at.ispras.ru/owncloud/index.php/s/bEozaxZALrUyFzM/download"


def get_pdf_page_count(path: str) -> int:
    with open(path, "rb") as fp:
        pages = len(list(PdfminerExtractor.get_pages(fp)))
        return pages if pages > 0 else 1


def get_none_page_count(path: str) -> int:
    return 1


def get_cpu_performance() -> float:
    start = time.time()
    for _ in range(50000):
        m1 = np.random.uniform((5000, 5000))
        m2 = np.random.uniform((5000, 5000))
        _ = np.matmul(m1, m2)
    return 1 / (time.time() - start)


def get_times(spend_page_times: List, total_size: int, total_time: int, total_files: int, cpu_performance: float = 1.0) -> List[float]:
    total_time = total_time * cpu_performance
    throughput = total_size / total_time
    mean_time_on_file = total_time / total_files
    mean_time_cpu_on_page = sum(spend_page_times) / len(spend_page_times) * cpu_performance

    return [total_time, throughput, mean_time_on_file, mean_time_cpu_on_page]


cpu_performance = get_cpu_performance()
print(f'"cpu_performance" = {cpu_performance}')

with TemporaryDirectory() as path_base:
    path_out = os.path.join(path_base, "dataset.zip")
    wget.download(data_url, path_out)
    with zipfile.ZipFile(path_out, "r") as zip_ref:
        zip_ref.extractall(path_base)
    print(path_base)

    failed = []
    result = OrderedDict()
    result["version"] = requests.get(f"{host}/version").text
    result["cpu_performance"] = cpu_performance
    tasks = [
        Task("images", "images", {}, get_none_page_count),
        Task("htmls", "law_html", {"document_type": "law"}, get_none_page_count),
        Task("htmls", "other_html", {}, get_none_page_count),
        Task("txt", "txt", {}, get_none_page_count),
        Task("pdf_text_layer", "pdf_text_layer_true", {"pdf_with_text_layer": "true"}, get_pdf_page_count),
        Task("pdf_text_layer", "pdf_text_layer_auto", {"pdf_with_text_layer": "auto"}, get_pdf_page_count),
        Task("pdf_text_layer", "pdf_text_layer_auto_tabby", {"pdf_with_text_layer": "auto_tabby"}, get_pdf_page_count),
        Task("pdf_text_layer", "pdf_text_layer_false", {"pdf_with_text_layer": "false"}, get_pdf_page_count),
        Task("pdf_text_layer", "pdf_text_layer_tabby", {"pdf_with_text_layer": "tabby"}, get_pdf_page_count),
        Task("docx", "docx", {}, get_none_page_count),
        Task("pdf", "pdf", {"pdf_with_text_layer": "false"}, get_pdf_page_count),
        Task("pdf_tables", "pdf_tables", {}, get_pdf_page_count)
    ]
    print(tasks)
    table_benchmark = Texttable()
    header = [
        ["Dataset", "total_file_size", "total_files", "total_pages", # noqa
         "|||||||||||||||||||||||||", "|||||||||raw_time||||||", "|||||||||||||||||||||||||", "|||||||||||||||||||||||||",  # noqa
         "=========================", "====independent_cpu====", "=========================", "========================="],  # noqa
        ["", "", "", "", "total_time", "throughput", "mean_time_on_file ", "mean_time_cpu_on_page",  # noqa
         "total_time", "throughput", "mean_time_on_file", "mean_time_cpu_on_page"]]  # noqa
    table_benchmark.header(header[0])
    table_benchmark.add_row(header[1])
    table_benchmark.set_cols_width([25 for _ in header[0]])
    for directory, name, parameters, page_func in tasks:
        total_size = 0
        total_time = 0
        total_files = 0
        total_pages = 0
        files_info = []
        spend_page_times = []
        directory = os.path.join(path_base, directory)

        for file in tqdm(os.listdir(directory), desc=name):
            file_path = os.path.join(directory, file)
            file_size = os.path.getsize(file_path)
            total_size += file_size
            time_start = time.time()
            send_file(host=host, file_name=file, file_path=file_path, parameters=parameters)
            time_finish = time.time()
            spend_file_time = time_finish - time_start
            pages = page_func(file_path)
            spend_page_times.append(spend_file_time / pages)
            total_time += spend_file_time
            total_pages += pages
            files_info.append({"file": file, "size": file_size, "time_per_file": spend_file_time, "time_per_page": spend_page_times[-1]})
            total_files += 0

        result_item = [name, total_size, len(files_info), total_pages]
        result_item.extend(get_times(spend_page_times, total_size, total_time, len(files_info)))
        result_item.extend(get_times(spend_page_times, total_size, total_time, len(files_info), cpu_performance))

        table_benchmark.add_row(result_item)
        with open(path_result, "w") as file_out:
            file_out.write(f"cpu_performance={cpu_performance}")
            file_out.write("\nTable 1 - benchmarks\n")
            file_out.write(table_benchmark.draw())
        print(f"save result in {path_result}")

    print(failed)

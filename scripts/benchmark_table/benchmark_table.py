import os
import zipfile
from pathlib import Path
import json
import pprint

import numpy as np
import wget

from dedoc.api.api_utils import table2html
from dedoc.config import get_config
from dedoc.readers import PdfImageReader
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_recognizer import TableRecognizer
from scripts.benchmark_table.metric import TEDS
from tests.test_utils import get_test_config

path_result = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "benchmarks")
path_result = os.path.abspath(path_result)
os.makedirs(path_result, exist_ok=True)
path_result = os.path.join(path_result, "table_benchmark.json")

URL = "https://at.ispras.ru/owncloud/index.php/s/Xaf4OyHj6xN2RHH/download"

table_recognizer = TableRecognizer(config=get_test_config())
image_reader = PdfImageReader(config=get_test_config())
teds = TEDS()


def call_metric(pred_json: dict, true_json: dict) -> dict:
    scores = teds.batch_evaluate(pred_json, true_json)
    pp = pprint.PrettyPrinter()
    pp.pprint(scores)

    return scores


def get_tables(image_path: str) -> str:
    document = image_reader.read(image_path)

    for table in document.tables:
        table.metadata.uid = "test_id"
    table2id = {"test_id": 0}
    html_tables = [table2html(table, table2id) for table in document.tables]

    # TODO: while works with one table in an image
    return html_tables[0]


def make_predict_json(data_path: Path) -> dict:
    predict_json = {}
    for filename in os.listdir(data_path):
        print(filename)
        file_path = str(data_path / filename)

        predict_json[filename] = {"html": "<html><body>" + get_tables(file_path) + "</body></html>"}

    return predict_json


def download_dataset(data_dir: Path) -> None:

    if not os.path.isdir(data_dir):
        data_dir.mkdir(parents=True)
        pdfs_zip_path = str(data_dir / "benchmark_table_data.zip")
        wget.download(URL, pdfs_zip_path)

        with zipfile.ZipFile(pdfs_zip_path, 'r') as zip_ref:
            zip_ref.extractall(data_dir)
        os.remove(pdfs_zip_path)

        print(f"Benchmark data downloaded to {data_dir}")
    else:
        print(f"Use cached benchmark data from {data_dir}")


def prediction(path_pred: Path, path_images: Path) -> dict:
    pred_json = make_predict_json(path_images)
    with open(path_pred, "w") as fd:
        json.dump(pred_json, fd, indent=2, ensure_ascii=False)

    return pred_json


if __name__ == "__main__":
    data_dir = Path(get_config()["intermediate_data_path"]) / "benchmark_table_data"
    path_images = data_dir / "images"
    path_gt = data_dir / "gt.json"
    path_pred = data_dir / "pred.json"
    download_dataset(data_dir)

    with open(path_gt, "r") as fp:
        gt_json = json.load(fp)
    '''
    Creating base html (based on method predictions for future labeling)
    path_images = data_dir / "images_tmp"
    pred_json = prediction("gt_tmp.json", path_images)
    '''
    pred_json = prediction(path_pred, path_images)   
    scores = call_metric(pred_json=pred_json, true_json=gt_json)

    result = dict()
    result["mean"] = np.mean([score for score in scores.values()])
    result["images"] = scores

    # save benchmarks
    with open(path_result, "w") as fd:
        json.dump(result, fd, indent=2, ensure_ascii=False)








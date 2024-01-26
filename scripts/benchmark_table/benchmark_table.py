import zipfile
from pathlib import Path
import json
import pprint
from typing import Optional, List

import numpy as np
import wget

from dedoc.api.api_utils import table2html
from dedoc.config import get_config
from dedoc.readers import PdfImageReader
from dedoc.readers.pdf_reader.pdf_image_reader.table_recognizer.table_recognizer import TableRecognizer
from scripts.benchmark_table.metric import TEDS

path_result = Path(__file__).parent / ".." / ".." / "resources" / "benchmarks"
path_result.absolute().mkdir(parents=True, exist_ok=True)

table_recognizer = TableRecognizer(config=get_config())
image_reader = PdfImageReader(config=get_config())


def call_metric(pred_json: dict, true_json: dict, structure_only: bool = False, ignore_nodes: Optional[List] = None) -> dict:
    teds = TEDS(structure_only=structure_only, ignore_nodes=ignore_nodes)
    scores = teds.batch_evaluate(pred_json, true_json)
    pp = pprint.PrettyPrinter()
    pp.pprint(scores)

    return scores


def get_tables(image_path: Path) -> str:
    document = image_reader.read(str(image_path))

    for table in document.tables:
        table.metadata.uid = "test_id"
    table2id = {"test_id": 0}
    html_tables = [table2html(table, table2id) for table in document.tables]

    # TODO: while works with one table in an image
    return html_tables[0]


def make_predict_json(data_path: Path) -> dict:
    predict_json = {}
    for pathname in Path.iterdir(data_path):
        print(pathname)

        predict_json[pathname.name] = {"html": "<html><body>" + get_tables(pathname) + "</body></html>"}

    return predict_json


def download_dataset(data_dir: Path, name_zip: str, url: str) -> None:
    if Path.exists(data_dir):
        print(f"Use cached benchmark data from {data_dir}")
        return

    data_dir.mkdir(parents=True, exist_ok=True)
    pdfs_zip_path = data_dir / name_zip
    wget.download(url, str(data_dir))

    with zipfile.ZipFile(pdfs_zip_path, 'r') as zip_ref:
        zip_ref.extractall(data_dir)
    pdfs_zip_path.unlink()

    print(f"Benchmark data downloaded to {data_dir}")


def prediction(path_pred: Path, path_images: Path) -> dict:
    pred_json = make_predict_json(path_images)
    with path_pred.open("w") as fd:
        json.dump(pred_json, fd, indent=2, ensure_ascii=False)

    return pred_json


def benchmark_on_our_data():
    data_dir = Path(get_config()["intermediate_data_path"]) / "benchmark_table_data"
    path_images = data_dir / "images"
    path_gt = data_dir / "gt.json"
    path_pred = data_dir / "pred.json"
    download_dataset(data_dir,
                     name_zip="benchmark_table_data.zip",
                     url="https://at.ispras.ru/owncloud/index.php/s/Xaf4OyHj6xN2RHH/download")

    mode_metric_structure_only = False

    with open(path_gt, "r") as fp:
        gt_json = json.load(fp)
    '''
    Creating base html (based on method predictions for future labeling)
    path_images = data_dir / "images_tmp"
    pred_json = prediction("gt_tmp.json", path_images)
    '''
    pred_json = prediction(path_pred, path_images)
    scores = call_metric(pred_json=pred_json, true_json=gt_json, structure_only=mode_metric_structure_only)

    result = dict()
    result["mode_metric_structure_only"] = mode_metric_structure_only
    result["mean"] = np.mean([score for score in scores.values()])
    result["images"] = scores

    # save benchmarks
    file_result = path_result / "table_benchmark.json"
    with file_result.open("w") as fd:
        json.dump(result, fd, indent=2, ensure_ascii=False)


def benchmark_on_generated_table():
    """
    Generated data from https://github.com/hassan-mahmood/TIES_DataGeneration
    Article generation information https://arxiv.org/pdf/1905.13391.pdf
    Note: generate the 1st table tape category
    Note: don't use header table tag <th>, replacing on <td> tag
    Note: all generated data (four categories) you can download from 
    TODO: some tables have a low quality. Should to trace the reason.
    All generated data (all categories) we can download from https://at.ispras.ru/owncloud/index.php/s/cjpCIR7I0G4JzZU
    """

    data_dir = Path(get_config()["intermediate_data_path"]) / "visualizeimgs" / "category1"
    path_images = data_dir / "img_500"
    path_gt = data_dir / "html_500"
    download_dataset(data_dir,
                     name_zip="benchmark_table_data_generated_500_tables_category_1.zip",
                     url="https://at.ispras.ru/owncloud/index.php/s/gItWxupnF2pve6B/download")
    mode_metric_structure_only = True

    # make common ground-truth file
    common_gt_json = {}
    for pathname in Path.iterdir(path_gt):
        image_name = pathname.name.split(".")[0] + '.png'
        with open(pathname, "r") as fp:
            table_html = fp.read()
            # exclude header tags
            table_html = table_html.replace("<th ", "<td ")
            table_html = table_html.replace("</th>", "</td>")

        common_gt_json[image_name] = {"html": table_html}

    file_common_gt = data_dir / "common_gt.json"
    with file_common_gt.open("w") as fd:
        json.dump(common_gt_json, fd, indent=2, ensure_ascii=False)

    # calculate metrics
    path_pred = data_dir / "pred.json"

    pred_json = prediction(path_pred, path_images)
    scores = call_metric(pred_json=pred_json, true_json=common_gt_json,
                         structure_only=mode_metric_structure_only,
                         ignore_nodes=['span', 'style', 'head', 'h4'])

    result = dict()
    result["mode_metric_structure_only"] = mode_metric_structure_only
    result["mean"] = np.mean([score for score in scores.values()])
    result["images"] = scores

    # save benchmarks
    file_result = path_result / "table_benchmark_on_generated_data.json"
    with file_result.open("w") as fd:
        json.dump(result, fd, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # benchmark_on_our_data()
    benchmark_on_generated_table()
